"""
Group Agent: hourly collection from a specific group
- Collects latest posts from "банк по нейросетям"
- Rewrites each post via AI
- Preserves media
- Publishes to Saved Messages
"""
import asyncio
import logging
import os
import json
import re
import hashlib
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
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

GROUP_NAME = "банк по нейросетям"
PROCESSED_GROUP_IDS_FILE = "processed_group_ids.json"
GROUP_SEEN_POSTS_FILE = "group_seen_posts.json"
POSTS_PER_RUN = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

REWRITE_PROMPT = """Ты — куратор подборки постов про нейросети и AI.

Перепиши этот пост для сохранения в базу знаний:
- Сохрани суть, факты и основную идею
- Улучши читаемость и структуру
- Пиши на русском языке
- Максимум 1000 символов
- Не упоминай источник
- Без эмодзи, хештегов
- Оставь важные внешние ссылки (не t.me)
- Начинай сразу с контента
- Если реклама или спам — ответь только: SKIP

Пост:
{text}"""

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
    "]+",
    flags=re.UNICODE,
)
TG_LINK_RE = re.compile(r"https?://t\.me/\S+|@\w{5,}", re.IGNORECASE)
HASHTAG_RE = re.compile(r"#\w+", re.UNICODE)


def clean_text(text: str) -> str:
    text = EMOJI_RE.sub("", text)
    text = TG_LINK_RE.sub("", text)
    text = HASHTAG_RE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def sentence_hashes(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip().lower() for s in sentences if len(s.strip()) >= 30][:3]
    return [hashlib.md5(s.encode()).hexdigest()[:8] for s in sentences]


class GroupAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }
        providers_config = [(p, api_key_map[p]) for p in ["mistral", "gemini", "cerebras"]]
        self.ai = AIProviderChain(providers_config, "")
        self.delay = AdaptiveDelay(initial=3.0, min_delay=2.0, max_delay=60.0)

    def load_processed_ids(self) -> dict:
        try:
            with open(PROCESSED_GROUP_IDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_processed_ids(self, data: dict):
        with open(PROCESSED_GROUP_IDS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_seen_posts(self) -> dict:
        try:
            with open(GROUP_SEEN_POSTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_seen_posts(self, data: dict):
        with open(GROUP_SEEN_POSTS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def is_processed(self, processed_ids: dict, message_id: int) -> bool:
        return str(message_id) in processed_ids.get("ids", {})

    def mark_processed(self, processed_ids: dict, message_id: int):
        if "ids" not in processed_ids:
            processed_ids["ids"] = {}
        processed_ids["ids"][str(message_id)] = True
        # Keep only last 100 message IDs
        if len(processed_ids["ids"]) > 100:
            processed_ids["ids"] = dict(list(processed_ids["ids"].items())[-100:])

    def count_matching_sentences(self, seen_posts: dict, text: str) -> int:
        new_hashes = set(sentence_hashes(text))
        if not new_hashes:
            return 0
        max_matches = 0
        for stored_hashes in seen_posts.values():
            if isinstance(stored_hashes, list):
                matches = len(new_hashes & set(stored_hashes))
                if matches > max_matches:
                    max_matches = matches
        return max_matches

    def record_post(self, seen_posts: dict, message_id: int, text: str):
        seen_posts[str(message_id)] = sentence_hashes(text)
        # Keep only last 200
        if len(seen_posts) > 200:
            seen_posts = dict(list(seen_posts.items())[-200:])

    async def rewrite_post(self, text: str) -> str | None:
        prompt = REWRITE_PROMPT.format(text=text[:2000])
        try:
            logger.info("✏️ Rewriting post from group...")
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            return clean_text(response)
        except Exception as e:
            logger.error(f"Rewrite failed: {e}")
            return None

    async def send_post(self, text: str, original_text: str, message_obj):
        """Send rewritten post + original + media"""
        try:
            has_media = message_obj.media and isinstance(
                message_obj.media, (MessageMediaPhoto, MessageMediaDocument)
            )

            header = f"📚 НЕЙРОСЕТИ БАНК\n\n"
            full_text = header + text

            if has_media:
                media_file = await self.client.download_media(message_obj.media)
                if media_file:
                    await self.client.send_file("me", media_file, caption=full_text)
                    try:
                        os.remove(media_file)
                    except Exception:
                        pass
                    await self.client.send_message(
                        "me",
                        f"ОРИГИНАЛ:\n\n{original_text[:500]}",
                        link_preview=True,
                    )
                    logger.info(f"✅ Sent with media")
                    return

            await self.client.send_message("me", full_text)
            await self.client.send_message(
                "me",
                f"ОРИГИНАЛ:\n\n{original_text[:500]}",
                link_preview=True,
            )
            logger.info(f"✅ Sent (text only)")
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def run(self):
        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name}")

        processed_ids = self.load_processed_ids()
        seen_posts = self.load_seen_posts()

        # Find the group
        group = None
        async for dialog in self.client.iter_dialogs():
            if GROUP_NAME.lower() in dialog.name.lower():
                group = dialog.entity
                logger.info(f"📢 Found group: {dialog.name}")
                break

        if not group:
            logger.error(f"Group '{GROUP_NAME}' not found")
            await self.client.disconnect()
            return

        # Collect recent posts
        posts = []
        short_posts = 0
        duplicates = 0

        async for message in self.client.iter_messages(group, limit=POSTS_PER_RUN):
            if not message.text or len(message.text) < 100:
                short_posts += 1
                continue

            if self.is_processed(processed_ids, message.id):
                continue

            # Dedup check
            match_count = self.count_matching_sentences(seen_posts, message.text)
            if match_count >= 2:
                duplicates += 1
                continue

            posts.append({
                "text": message.text,
                "message_id": message.id,
                "message_obj": message,
                "partial": match_count == 1,
            })

            self.record_post(seen_posts, message.id, message.text)

        logger.info(f"📦 Collected {len(posts)} new posts (skipped: {short_posts} short, {duplicates} duplicates)")

        if not posts:
            logger.info("No new posts to process")
            self.save_processed_ids(processed_ids)
            self.save_seen_posts(seen_posts)
            await self.client.disconnect()
            return

        # Rewrite and publish
        sent = 0
        for post in posts:
            # Skip partial matches (only publish if grouped, but we're not grouping here)
            # Actually, let's publish them too since they're less common
            result = await self.rewrite_post(post["text"])
            if result and result.strip() != "SKIP":
                await self.send_post(result, post["text"], post["message_obj"])
                self.mark_processed(processed_ids, post["message_id"])
                sent += 1
            elif result == "SKIP":
                self.mark_processed(processed_ids, post["message_id"])
                logger.info("⏭ Post skipped (spam/ad)")
            else:
                self.mark_processed(processed_ids, post["message_id"])

            await self.delay.wait()

        self.save_processed_ids(processed_ids)
        self.save_seen_posts(seen_posts)
        logger.info(f"✨ Done! Published {sent} posts")
        await self.client.disconnect()


async def main():
    agent = GroupAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
