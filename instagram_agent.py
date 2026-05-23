#!/usr/bin/env python3
"""
Instagram Agent (manual run or scheduled):
- Monitors a Telegram channel for Instagram links
- Downloads videos using yt-dlp
- Rewrites descriptions via AI
- Publishes to Saved Messages with original link
"""
import asyncio
import logging
import os
import json
import re
from pathlib import Path
from typing import Optional
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from instagram_downloader import InstagramDownloader
from ai_providers import AIProviderChain, AdaptiveDelay
from config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    SESSION_NAME,
    GEMINI_API_KEY,
    MISTRAL_API_KEY,
    CEREBRAS_API_KEY,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Configuration
INSTAGRAM_SOURCE_CHANNEL = "instagram"  # Channel/username to monitor for Instagram links
INSTAGRAM_OUTPUT_DIR = "/tmp/instagram_downloads"
PROCESSED_INSTAGRAM_FILE = "processed_instagram.json"
MAX_VIDEO_SIZE_MB = 2000  # Telegram limit is 4GB, but be conservative

# AI Prompt
INSTAGRAM_REWRITE_PROMPT = """Ты — редактор моего канала в Telegram.

Перепиши это описание Instagram видео для публикации:
- Сохрани суть и основные факты
- Сделай текст интересным и энергичным
- Пиши на русском языке
- Максимум 500 символов
- Без эмодзи, хештегов, t.me ссылок
- Оставь внешние ссылки если они важны
- Если это очевидная реклама — ответь только: SKIP

Оригинальное описание:
{text}"""

# ── Text cleanup ───────────────────────────────────────────────────────────────

EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "♀-♂"
    "☀-⭕"
    "‍"
    "⏏"
    "⏩"
    "⌚"
    "️"
    "〰"
    "]+"
)


def clean_text(text: str) -> str:
    """Remove emoji, hashtags, @mentions, and t.me links"""
    text = EMOJI_RE.sub(" ", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"@[a-zA-Z0-9_]{5,}", "", text)
    text = re.sub(r"https?://t\.me/\S+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def load_processed_instagram() -> dict:
    """Load processed Instagram URLs"""
    if os.path.exists(PROCESSED_INSTAGRAM_FILE):
        with open(PROCESSED_INSTAGRAM_FILE) as f:
            return json.load(f)
    return {"urls": []}


def save_processed_instagram(data: dict):
    """Save processed Instagram URLs"""
    with open(PROCESSED_INSTAGRAM_FILE, "w") as f:
        json.dump(data, f, indent=2)


def extract_instagram_urls(text: str) -> list[str]:
    """Extract Instagram URLs from text"""
    if not text:
        return []
    pattern = r"https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_/-]+"
    return re.findall(pattern, text)


async def get_instagram_info(url: str, downloader: InstagramDownloader) -> Optional[dict]:
    """Get Instagram video metadata"""
    try:
        info = downloader.get_info(url)
        if info:
            logger.info(f"✅ Got Instagram info: {info.get('title', 'Unknown')}")
            return info
    except Exception as e:
        logger.error(f"❌ Failed to get info for {url}: {e}")
    return None


async def rewrite_instagram_description(
    title: str, uploader: str, ai_chain: AIProviderChain
) -> Optional[str]:
    """Rewrite Instagram video description via AI"""
    input_text = f"{title} (by {uploader})"
    prompt = INSTAGRAM_REWRITE_PROMPT.format(text=input_text)

    try:
        result = await ai_chain.call(prompt)
        if result and result.upper() != "SKIP":
            logger.info(f"✅ AI rewrite done")
            return clean_text(result)
        elif result and result.upper() == "SKIP":
            logger.info("⏭️ Skipped by AI (likely ad)")
            return None
    except Exception as e:
        logger.error(f"❌ AI rewrite failed: {e}")
    return None


async def download_instagram_video(url: str, downloader: InstagramDownloader) -> Optional[str]:
    """Download Instagram video, return file path or None"""
    try:
        file_path = downloader.download_reel(url)
        if file_path and os.path.exists(file_path):
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > MAX_VIDEO_SIZE_MB:
                logger.warning(f"⚠️ Video too large ({file_size_mb:.0f}MB), skipping")
                return None
            logger.info(f"✅ Downloaded: {file_path} ({file_size_mb:.1f}MB)")
            return file_path
    except Exception as e:
        logger.error(f"❌ Download failed for {url}: {e}")
    return None


async def process_instagram_url(
    url: str,
    client: TelegramClient,
    ai_chain: AIProviderChain,
    downloader: InstagramDownloader,
) -> bool:
    """Process single Instagram URL: download → rewrite → publish"""
    logger.info(f"Processing: {url}")

    # Get metadata
    info = await get_instagram_info(url, downloader)
    if not info:
        logger.warning(f"⏭️ Skipped (no metadata): {url}")
        return False

    title = info.get("title", "Instagram Video")
    uploader = info.get("uploader", "Unknown")
    duration = info.get("duration", 0)

    # Rewrite description
    rewritten = await rewrite_instagram_description(title, uploader, ai_chain)
    if not rewritten:
        logger.warning(f"⏭️ Skipped by AI filter")
        return False

    # Download video
    video_path = await download_instagram_video(url, downloader)
    if not video_path:
        logger.warning(f"⏭️ Failed to download video")
        return False

    # Publish to Saved Messages
    try:
        caption = f"""<b>{rewritten}</b>

Duration: {duration:.0f}s
By: {uploader}

<a href="{url}">Original Instagram post</a>"""

        await client.send_file("me", video_path, caption=caption, parse_mode="html")
        logger.info(f"✅ Published to Saved Messages")

        # Cleanup
        os.remove(video_path)
        return True

    except Exception as e:
        logger.error(f"❌ Failed to publish: {e}")
        return False


async def main(url: Optional[str] = None):
    """Main agent: process single URL or monitor channel"""
    logger.info("🚀 Instagram Agent starting...")

    # Initialize
    downloader = InstagramDownloader(output_dir=INSTAGRAM_OUTPUT_DIR)
    ai_chain = AIProviderChain(
        api_keys={
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        },
        delay=AdaptiveDelay(initial_delay=1.0),
    )

    processed = load_processed_instagram()
    processed_urls = set(processed.get("urls", []))

    async with TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
        await client.start(phone=TELEGRAM_PHONE)
        logger.info("✅ Connected to Telegram")

        # Mode 1: Process single URL from user
        if url:
            logger.info(f"📌 Single URL mode: {url}")
            success = await process_instagram_url(url, client, ai_chain, downloader)
            if success:
                processed_urls.add(url)
                processed["urls"] = list(processed_urls)
                save_processed_instagram(processed)
                logger.info("✅ Video processed and saved to Saved Messages")
            else:
                logger.error("❌ Failed to process video")
            return

        # Mode 2: Monitor channel for Instagram links
        logger.info(f"📡 Channel monitoring mode: {INSTAGRAM_SOURCE_CHANNEL}")

        # Get source channel
        try:
            entity = await client.get_entity(INSTAGRAM_SOURCE_CHANNEL)
            logger.info(f"✅ Found channel: {entity.title if hasattr(entity, 'title') else INSTAGRAM_SOURCE_CHANNEL}")
        except Exception as e:
            logger.error(f"❌ Channel not found: {INSTAGRAM_SOURCE_CHANNEL} ({e})")
            return

        # Fetch recent messages
        count = 0
        async for message in client.iter_messages(entity, limit=100):
            if not message.text:
                continue

            urls = extract_instagram_urls(message.text)
            for url in urls:
                if url in processed_urls:
                    logger.info(f"⏭️ Already processed: {url}")
                    continue

                success = await process_instagram_url(url, client, ai_chain, downloader)
                if success:
                    count += 1
                    processed_urls.add(url)

        # Save state
        processed["urls"] = list(processed_urls)
        save_processed_instagram(processed)

        logger.info(f"✅ Finished. Processed {count} new videos")


if __name__ == "__main__":
    import sys

    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
        # Validate it's an Instagram URL
        if not extract_instagram_urls(url):
            print("❌ Invalid Instagram URL. Usage:")
            print("  python instagram_agent.py                                    # Monitor channel")
            print("  python instagram_agent.py https://www.instagram.com/p/ABC123  # Download single URL")
            sys.exit(1)

    asyncio.run(main(url=url))
