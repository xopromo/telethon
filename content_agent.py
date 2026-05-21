"""
Content Agent: monitors subscribed channels, rewrites posts via AI, sends to Saved Messages
"""
import asyncio
import logging
import os
import json
import re
from telethon import TelegramClient
from telethon.tl.types import Channel, MessageMediaPhoto, MessageMediaDocument
from ai_providers import AIProviderChain, AdaptiveDelay
from config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    SESSION_NAME,
    PROVIDER_PRIORITY,
    GEMINI_API_KEY,
    MISTRAL_API_KEY,
    CEREBRAS_API_KEY,
)

PROCESSED_IDS_FILE = "processed_ids.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

REWRITE_PROMPT = """Ты — редактор Telegram-канала про нейросети и технологии.

Перепиши этот пост для моего канала. Требования:
- Сохрани суть и факты
- Сделай текст живым и интересным
- Пиши на русском языке
- Максимум 800 символов
- Не упоминай источник
- Не используй эмодзи вообще
- Не пиши вступления типа "Вот переписанный пост:"
- Начинай сразу с контента
- Ссылки: оставь только внешние источники (новости, исследования, сайты) — убери все ссылки на Telegram-каналы (t.me/...)
- Если пост — реклама или вакансия, пропусти его (ответь только словом: SKIP)

Оригинальный пост:
{text}"""


# Regex to strip emoji unicode characters
EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002500-\U00002BEF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "♀-♂"
    "☀-⭕"
    "‍⏏⏩⌚️〰"
    "]+",
    flags=re.UNICODE,
)

# Regex to strip t.me links (channel links)
TG_LINK_RE = re.compile(r"https?://t\.me/\S+|@\w{5,}", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Remove emoji and Telegram channel links from text"""
    text = EMOJI_RE.sub("", text)
    text = TG_LINK_RE.sub("", text)
    # Clean up extra whitespace/newlines left after removals
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()

POSTS_PER_CHANNEL = 3
CHANNELS_LIMIT = 10


class ContentAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        # Gemini first — more stable and free, Mistral last to avoid rate limits
        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }
        # Original priority: mistral → gemini → cerebras
        priority = ["mistral", "gemini", "cerebras"]
        providers_config = [(p, api_key_map[p]) for p in priority]
        self.ai = AIProviderChain(providers_config, "")

    def load_processed_ids(self) -> dict:
        """Load already processed post IDs from file"""
        try:
            with open(PROCESSED_IDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_processed_ids(self, ids: dict):
        """Save processed post IDs to file"""
        with open(PROCESSED_IDS_FILE, "w") as f:
            json.dump(ids, f, indent=2)

    def is_processed(self, ids: dict, channel_id: int, message_id: int) -> bool:
        return str(message_id) in ids.get(str(channel_id), [])

    def mark_processed(self, ids: dict, channel_id: int, message_id: int):
        key = str(channel_id)
        if key not in ids:
            ids[key] = []
        if str(message_id) not in ids[key]:
            ids[key].append(str(message_id))
        # Keep only last 100 IDs per channel to avoid file bloat
        ids[key] = ids[key][-100:]

    async def run(self):
        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name}")

        processed_ids = self.load_processed_ids()
        channels = await self.get_subscribed_channels()
        logger.info(f"📋 Processing {len(channels)} channels")

        delay = AdaptiveDelay(initial=3.0, min_delay=3.0, max_delay=120.0)
        processed = 0

        for channel in channels:
            posts = await self.get_recent_posts(channel)
            for post_text, post_message in posts:
                # Skip already processed posts
                if self.is_processed(processed_ids, channel.id, post_message.id):
                    logger.info(f"⏭️ Already seen: [{channel.title}] msg#{post_message.id}")
                    continue

                rewritten = await self.rewrite_post(post_text, channel.title, delay)
                if rewritten and rewritten.strip() != "SKIP":
                    await self.send_to_saved(rewritten, channel.title, post_message)
                    self.mark_processed(processed_ids, channel.id, post_message.id)
                    processed += 1
                elif rewritten and rewritten.strip() == "SKIP":
                    logger.info(f"⏭️ Skipped ad/vacancy from {channel.title}")
                    self.mark_processed(processed_ids, channel.id, post_message.id)

                await delay.wait()

        self.save_processed_ids(processed_ids)
        logger.info(f"✨ Done! Sent {processed} new posts to Saved Messages")
        await self.client.disconnect()

    async def get_subscribed_channels(self) -> list:
        """Get first N channels from subscriptions"""
        channels = []
        async for dialog in self.client.iter_dialogs():
            if len(channels) >= CHANNELS_LIMIT:
                break
            if isinstance(dialog.entity, Channel) and not dialog.entity.megagroup:
                channels.append(dialog.entity)
                logger.info(f"  📢 {dialog.entity.title}")
        return channels

    async def get_recent_posts(self, channel) -> list:
        """Get recent text posts (with message object for media)"""
        posts = []
        try:
            async for message in self.client.iter_messages(channel, limit=POSTS_PER_CHANNEL):
                # Skip: too short, forwarded, no text
                if not message.text or len(message.text) < 100:
                    continue
                if message.fwd_from:
                    continue
                posts.append((message.text, message))
        except Exception as e:
            logger.warning(f"⚠️ Could not read {channel.title}: {e}")
        return posts

    async def rewrite_post(self, text: str, source_title: str, delay: AdaptiveDelay) -> str | None:
        """Rewrite post via AI, return None on error"""
        try:
            logger.info(f"🤖 Rewriting from {source_title}...")
            prompt = REWRITE_PROMPT.format(text=text[:2000])
            response = await self.ai.get_response(prompt, [], delay=delay)
            return clean_text(response)
        except Exception as e:
            logger.error(f"All providers failed for {source_title}: {e}")
            return None

    async def send_to_saved(self, rewritten: str, source_title: str, original_message):
        """Send two posts to Saved Messages: rewritten (with media) + original text"""
        try:
            has_media = original_message.media and isinstance(
                original_message.media, (MessageMediaPhoto, MessageMediaDocument)
            )

            # --- Post 1: rewritten version (with media if any) ---
            post1_text = f"[ {source_title} ]\n\n{rewritten}"

            if has_media:
                media_file = await self.client.download_media(original_message.media)
                if media_file:
                    await self.client.send_file("me", media_file, caption=post1_text)
                    try:
                        os.remove(media_file)
                    except Exception:
                        pass
                else:
                    await self.client.send_message("me", post1_text)
            else:
                await self.client.send_message("me", post1_text)

            # --- Post 2: original text for reference ---
            original_text = original_message.text or ""
            post2_text = f"ОРИГИНАЛ [ {source_title} ]\n\n{original_text}"
            await self.client.send_message("me", post2_text, link_preview=True)

            logger.info(f"✅ Sent 2 posts to Saved Messages (rewritten + original)")

        except Exception as e:
            logger.error(f"Send error: {e}")


async def main():
    agent = ContentAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
