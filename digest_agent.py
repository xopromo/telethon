"""
Digest Agent: collects posts from last 24h, groups by topic via AI,
writes mini-articles for groups with 3+ posts
"""
import asyncio
import logging
import json
import re
import hashlib
import os
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.tl.types import Channel
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

PROCESSED_TOPICS_FILE = "processed_topics.json"
ALL_SEEN_POSTS_FILE = "all_seen_posts.json"  # Global deduplication
CHANNELS_LIMIT = 10
LOOKBACK_HOURS = 24
MIN_POSTS_FOR_DIGEST = 3

GROUPING_PROMPT = """У меня есть посты из разных Telegram-каналов за последние 24 часа.
Сгруппируй их по теме — одна тема это один инфоповод или событие.

Посты:
{posts_list}

Верни ТОЛЬКО валидный JSON без пояснений, в формате:
{{
  "название темы кратко": [1, 3, 7],
  "другая тема": [2, 5],
  ...
}}

Правила:
- Группируй только если посты реально об одном событии/инфоповоде
- Одиночные посты не включай (только группы от 2+)
- Название темы — 3-6 слов на русском"""

ARTICLE_PROMPT = """Ты — редактор Telegram-канала про нейросети и технологии.

Напиши мини-статью (обзор) на основе этих {count} постов об одной теме.

Посты:
{posts_text}

Требования:
- Объедини факты из всех постов в связный текст
- Пиши на русском языке
- Максимум 1500 символов
- Не используй эмодзи
- Не используй хештеги
- Сохрани важные внешние ссылки (не t.me)
- Убери ссылки на Telegram-каналы
- Начинай сразу с сути, без вступлений типа "Вот статья:"
- Структура: факты → контекст → вывод"""

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


def topic_hash(topic_name: str) -> str:
    """Hash of topic name + current day — allows same topic next day"""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return hashlib.md5(f"{topic_name}:{day}".encode()).hexdigest()[:12]


class DigestAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }
        providers_config = [(p, api_key_map[p]) for p in ["mistral", "gemini", "cerebras"]]
        self.ai = AIProviderChain(providers_config, "")
        self.delay = AdaptiveDelay(initial=5.0, min_delay=3.0, max_delay=120.0)

    def load_processed_topics(self) -> dict:
        try:
            with open(PROCESSED_TOPICS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_processed_topics(self, topics: dict):
        with open(PROCESSED_TOPICS_FILE, "w") as f:
            json.dump(topics, f, indent=2, ensure_ascii=False)

    def load_all_seen_posts(self) -> dict:
        try:
            with open(ALL_SEEN_POSTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_all_seen_posts(self, posts: dict):
        with open(ALL_SEEN_POSTS_FILE, "w") as f:
            json.dump(posts, f, indent=2)

    def sentence_hashes(self, text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip().lower() for s in sentences if len(s.strip()) >= 30][:3]
        return [hashlib.md5(s.encode()).hexdigest()[:8] for s in sentences]

    def seen_similar_post(self, seen_posts: dict, channel_id: int, text: str) -> bool:
        new_hashes = set(self.sentence_hashes(text))
        if not new_hashes:
            return False
        for channel_data in seen_posts.values():
            for stored_hashes in channel_data.values():
                if isinstance(stored_hashes, list):
                    if new_hashes & set(stored_hashes):
                        return True
        return False

    def record_post(self, seen_posts: dict, channel_id: int, message_id: int, text: str):
        channel_key = str(channel_id)
        if channel_key not in seen_posts:
            seen_posts[channel_key] = {}
        seen_posts[channel_key][str(message_id)] = self.sentence_hashes(text)
        seen_posts[channel_key] = dict(list(seen_posts[channel_key].items())[-300:])

    async def run(self):
        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name}")

        processed_topics = self.load_processed_topics()
        seen_posts = self.load_all_seen_posts()
        since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

        # Step 1: collect all posts from last 24h
        all_posts = await self.collect_posts(since, seen_posts)
        logger.info(f"📦 Collected {len(all_posts)} posts total")

        if len(all_posts) < MIN_POSTS_FOR_DIGEST:
            logger.info("Not enough posts for digest")
            await self.client.disconnect()
            return

        # Step 2: group posts by topic via AI
        groups = await self.group_by_topic(all_posts)
        logger.info(f"🗂 Found {len(groups)} topic groups")

        # Step 3: write articles for groups with enough posts
        articles_sent = 0
        for topic_name, indices in groups.items():
            posts_in_group = [all_posts[i] for i in indices if i < len(all_posts)]

            if len(posts_in_group) < MIN_POSTS_FOR_DIGEST:
                logger.info(f"⏭ Skipping '{topic_name}' — only {len(posts_in_group)} posts")
                continue

            t_hash = topic_hash(topic_name)
            if t_hash in processed_topics:
                logger.info(f"⏭ Already covered today: '{topic_name}'")
                continue

            article = await self.write_article(topic_name, posts_in_group)
            if article:
                await self.send_digest(article, topic_name, posts_in_group)
                processed_topics[t_hash] = {
                    "topic": topic_name,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "posts_count": len(posts_in_group),
                }
                articles_sent += 1
                await self.delay.wait()

        self.save_processed_topics(processed_topics)
        self.save_all_seen_posts(seen_posts)
        logger.info(f"✨ Digest done! Sent {articles_sent} articles")
        await self.client.disconnect()

    async def collect_posts(self, since: datetime, seen_posts: dict) -> list:
        """Collect posts from subscribed channels since given time"""
        all_posts = []
        channels_found = 0

        async for dialog in self.client.iter_dialogs():
            if channels_found >= CHANNELS_LIMIT:
                break
            if not (isinstance(dialog.entity, Channel) and not dialog.entity.megagroup):
                continue

            channel = dialog.entity
            channels_found += 1

            try:
                async for message in self.client.iter_messages(channel, limit=20):
                    if message.date < since:
                        break
                    if not message.text or len(message.text) < 100:
                        continue
                    if message.fwd_from:
                        continue

                    # Skip if similar post seen before
                    if self.seen_similar_post(seen_posts, channel.id, message.text):
                        logger.info(f"⏭ Duplicate skipped in {channel.title}")
                        continue

                    all_posts.append({
                        "text": message.text,
                        "channel": channel.title,
                        "date": message.date.isoformat(),
                    })

                    # Record that we've seen this
                    self.record_post(seen_posts, channel.id, message.id, message.text)
            except Exception as e:
                logger.warning(f"⚠️ Could not read {channel.title}: {e}")

        return all_posts

    async def group_by_topic(self, posts: list) -> dict:
        """Ask AI to group posts by topic, return {topic: [indices]}"""
        posts_list = "\n".join(
            f"{i+1}. [{p['channel']}] {p['text'][:120].strip()}"
            for i, p in enumerate(posts)
        )

        prompt = GROUPING_PROMPT.format(posts_list=posts_list)

        try:
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in grouping response")
                return {}

            raw = json.loads(json_match.group())
            # Convert to 0-based indices
            return {
                topic: [i - 1 for i in indices if isinstance(i, int)]
                for topic, indices in raw.items()
            }
        except Exception as e:
            logger.error(f"Grouping failed: {e}")
            return {}

    async def write_article(self, topic_name: str, posts: list) -> str | None:
        """Generate mini-article from grouped posts"""
        posts_text = "\n\n---\n\n".join(
            f"Канал: {p['channel']}\n{p['text'][:800]}"
            for p in posts
        )

        prompt = ARTICLE_PROMPT.format(
            count=len(posts),
            posts_text=posts_text,
        )

        try:
            logger.info(f"✍️ Writing article: '{topic_name}' ({len(posts)} posts)")
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            return clean_text(response)
        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            return None

    async def send_digest(self, article: str, topic_name: str, posts: list):
        """Send article + sources to Saved Messages"""
        try:
            # Post 1: article
            channels = ", ".join(dict.fromkeys(p["channel"] for p in posts))
            header = f"ДАЙДЖЕСТ: {topic_name}\nИсточники: {channels}\n\n"
            await self.client.send_message("me", header + article)

            # Post 2: original posts for reference
            originals = "\n\n---\n\n".join(
                f"[ {p['channel']} ]\n{p['text'][:500]}"
                for p in posts
            )
            await self.client.send_message("me", f"ОРИГИНАЛЫ ({len(posts)} поста)\n\n{originals}")

            logger.info(f"✅ Sent digest: '{topic_name}'")
        except Exception as e:
            logger.error(f"Send error: {e}")


async def main():
    agent = DigestAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
