"""
Insights Agent: reads posts from a channel/topic in batches (newest → oldest),
filters valuable insights using AI, publishes to a private group.

Usage:
    python insights_agent.py --channel VelesCommunityRu --topic "Pro трейдинг"
    python insights_agent.py --channel VelesCommunityRu --topic "Pro трейдинг" --batch 500
"""
import asyncio
import argparse
import json
import os
import re
import logging
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.tl.functions.channels import CreateChannelRequest
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INSIGHTS_STATE_FILE = "insights_state.json"
DEFAULT_BATCH = 1000
FILTER_CHUNK = 50  # posts per AI filtering call

BATCH_FILTER_PROMPT = """Ты — эксперт по трейдингу криптовалют. Вот {n} сообщений из трейдингового сообщества.

Сообщения:
{posts_list}

Выбери только сообщения с реально ценными инсайтами или стратегиями.
Верни ТОЛЬКО валидный JSON-список номеров: [1, 7, 23]
Если ценных нет — верни: []

Ценно:
- Конкретная торговая стратегия или тактика с деталями
- Технический анализ с объяснением логики
- Практический опыт: что сработало и почему
- Нестандартный инсайт, находка или наблюдение о рынке

Не ценно:
- Общие слова ("крипта растёт", "HODL")
- Вопросы без ответа, флуд, смол-ток
- Реклама, ссылки на сторонние сервисы
- Простые реакции и приветствия"""

INSIGHT_PROMPT = """Ты — эксперт по трейдингу. Напиши краткий инсайт на основе этого поста из трейдингового сообщества.

Пост:
{text}

Требования:
- Выдели главную идею, стратегию или находку
- Объясни практическую ценность
- Пиши на русском языке, 2-4 предложения
- Без эмодзи и хештегов
- Начинай сразу с сути"""


class InsightsAgent:
    def __init__(self, channel: str, topic: str | None, batch: int, topic_id: int | None = None):
        self.channel_arg = channel
        self.topic_arg = topic
        self.batch = batch
        self.topic_id_override = topic_id

        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }
        providers_config = [(p, api_key_map[p]) for p in ["mistral", "gemini", "cerebras"]]
        self.ai = AIProviderChain(providers_config, "")
        self.delay = AdaptiveDelay(initial=3.0, min_delay=3.0, max_delay=120.0)

    def load_state(self) -> dict:
        try:
            with open(INSIGHTS_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_state(self, state: dict):
        with open(INSIGHTS_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    async def get_or_create_output_group(self, state: dict) -> int:
        """Create a private megagroup for insights if not yet created."""
        if "output_group_id" in state and state["output_group_id"]:
            return state["output_group_id"]

        logger.info("Creating private group 'Insights Feed'...")
        result = await self.client(CreateChannelRequest(
            title="Insights Feed",
            about="AI-отфильтрованные инсайты из трейдинговых каналов",
            megagroup=True,
        ))
        group = result.chats[0]
        group_id = int(f"-100{group.id}")
        state["output_group_id"] = group_id
        logger.info(f"✅ Group created: {group.title} (ID: {group_id})")
        return group_id

    async def find_topic_id(self, channel, topic_name: str) -> int | None:
        """Find topic ID by name. Tries API call first, falls back to scanning service messages."""
        # Method 1: GetForumTopicsRequest (available in newer Telethon builds)
        try:
            from telethon.tl.functions.channels import GetForumTopicsRequest
            result = await self.client(GetForumTopicsRequest(
                channel=channel,
                q="",
                offset_date=0,
                offset_id=0,
                offset_topic=0,
                limit=100,
            ))
            topics = result.topics
            for t in topics:
                if t.title.lower() == topic_name.lower():
                    return t.id
            for t in topics:
                if topic_name.lower() in t.title.lower():
                    logger.info(f"📌 Partial match via API: '{t.title}'")
                    return t.id
        except Exception as e:
            logger.info(f"GetForumTopicsRequest unavailable ({e}), scanning messages...")

        # Method 2: scan recent service messages for MessageActionTopicCreate
        try:
            from telethon.tl.types import MessageActionTopicCreate
            async for msg in self.client.iter_messages(channel, limit=2000):
                action = getattr(msg, "action", None)
                if isinstance(action, MessageActionTopicCreate):
                    if topic_name.lower() in action.title.lower():
                        logger.info(f"📌 Found topic via scan: '{action.title}' → ID {msg.id}")
                        return msg.id
        except Exception as e:
            logger.warning(f"Topic scan failed: {e}")

        return None

    async def collect_batch(self, channel, topic_id: int | None, cursor_id: int, freeze_id: int) -> list:
        """Collect up to self.batch posts going backwards from cursor_id."""
        posts = []
        kwargs = {
            "limit": self.batch * 3,  # fetch more to compensate for short/media-only messages
            "offset_id": cursor_id,
            "reverse": False,
        }
        if topic_id:
            kwargs["reply_to"] = topic_id

        async for msg in self.client.iter_messages(channel, **kwargs):
            # Ignore posts newer than freeze point (new posts that appeared during run)
            if msg.id >= freeze_id:
                continue
            if not msg.text or len(msg.text) < 50:
                continue

            posts.append({
                "id": msg.id,
                "text": msg.text,
                "date": msg.date.isoformat()[:10],
                "media": msg.media,
                "link": f"https://t.me/{self.channel_arg}/{msg.id}",
            })

            if len(posts) >= self.batch:
                break

        return posts

    async def filter_valuable(self, posts: list) -> list:
        """Send chunk of posts to AI, return only the valuable ones."""
        valuable = []
        for i in range(0, len(posts), FILTER_CHUNK):
            chunk = posts[i:i + FILTER_CHUNK]
            posts_list = "\n".join(
                f"{j + 1}. {p['text'][:200].strip()}"
                for j, p in enumerate(chunk)
            )
            prompt = BATCH_FILTER_PROMPT.format(n=len(chunk), posts_list=posts_list)
            try:
                response = await self.ai.get_response(prompt, [], delay=self.delay)
                match = re.search(r"\[.*?\]", response, re.DOTALL)
                if match:
                    indices = json.loads(match.group())
                    for idx in indices:
                        if isinstance(idx, int) and 1 <= idx <= len(chunk):
                            valuable.append(chunk[idx - 1])
            except Exception as e:
                logger.error(f"Filter chunk failed: {e}")
            await self.delay.wait()

        return valuable

    async def generate_insight(self, post: dict) -> str | None:
        prompt = INSIGHT_PROMPT.format(text=post["text"][:2000])
        try:
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            return response.strip()
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return None

    async def publish_insight(self, insight: str, post: dict, output_group_id: int):
        try:
            body = f"ИНСАЙТ ({post['date']})\n\n{insight}"
            footer = f"\n\n— {post['link']}"
            full_text = body + footer

            media = post["media"]
            if media and isinstance(media, (MessageMediaPhoto, MessageMediaDocument)):
                media_file = await self.client.download_media(media)
                if media_file:
                    await self.client.send_file(output_group_id, media_file, caption=full_text)
                    try:
                        os.remove(media_file)
                    except Exception:
                        pass
                    await self.client.send_message(
                        output_group_id,
                        f"ОРИГИНАЛ:\n{post['text'][:800]}",
                        link_preview=False,
                    )
                    return

            await self.client.send_message(output_group_id, full_text, link_preview=False)
            await self.client.send_message(
                output_group_id,
                f"ОРИГИНАЛ:\n{post['text'][:800]}",
                link_preview=False,
            )
            logger.info(f"✅ Published insight for post {post['id']}")
        except Exception as e:
            logger.error(f"Publish error: {e}")

    async def run(self):
        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name}")

        state = self.load_state()
        channel_key = self.channel_arg.lower()
        if channel_key not in state:
            state[channel_key] = {}
        ch = state[channel_key]

        channel = await self.client.get_entity(self.channel_arg)
        logger.info(f"📢 Channel: {channel.title}")

        # Resolve topic
        topic_id = None
        if self.topic_id_override:
            topic_id = self.topic_id_override
            ch["topic_id"] = topic_id
            logger.info(f"📌 Topic ID (manual): {topic_id}")
        elif self.topic_arg:
            topic_id = ch.get("topic_id")
            if not topic_id:
                topic_id = await self.find_topic_id(channel, self.topic_arg)
                if topic_id:
                    ch["topic_id"] = topic_id
                    logger.info(f"📌 Topic '{self.topic_arg}' → ID {topic_id}")
                else:
                    logger.error(f"Topic '{self.topic_arg}' not found. Use --topic-id to specify manually.")
                    await self.client.disconnect()
                    return

        # Set freeze point once per channel — everything newer is ignored
        if "freeze_id" not in ch:
            kwargs = {"limit": 1}
            if topic_id:
                kwargs["reply_to"] = topic_id
            async for msg in self.client.iter_messages(channel, **kwargs):
                ch["freeze_id"] = msg.id
                ch["cursor_id"] = msg.id
                ch["total_processed"] = 0
                ch["total_published"] = 0
            logger.info(f"🧊 Freeze point: ID {ch['freeze_id']}")

        freeze_id = ch["freeze_id"]
        cursor_id = ch.get("cursor_id", freeze_id)

        if cursor_id <= 0:
            logger.info("✅ All historical posts processed. Reset cursor_id to re-run.")
            await self.client.disconnect()
            return

        output_group_id = await self.get_or_create_output_group(state)

        logger.info(f"📖 Batch of {self.batch} posts before ID {cursor_id}...")
        posts = await self.collect_batch(channel, topic_id, cursor_id, freeze_id)

        if not posts:
            ch["cursor_id"] = 0
            state[channel_key] = ch
            self.save_state(state)
            logger.info("No more posts. History exhausted.")
            await self.client.disconnect()
            return

        oldest_id = min(p["id"] for p in posts)
        ch["cursor_id"] = oldest_id - 1
        ch["total_processed"] = ch.get("total_processed", 0) + len(posts)

        logger.info(f"📦 Got {len(posts)} posts (IDs {oldest_id}–{max(p['id'] for p in posts)})")

        valuable = await self.filter_valuable(posts)
        logger.info(f"⭐ {len(valuable)} valuable out of {len(posts)}")

        published = 0
        for post in valuable:
            insight = await self.generate_insight(post)
            if insight:
                await self.publish_insight(insight, post, output_group_id)
                published += 1
            await self.delay.wait()

        ch["total_published"] = ch.get("total_published", 0) + published
        state[channel_key] = ch
        self.save_state(state)

        logger.info(
            f"✨ Done! Published {published} insights | "
            f"Total: {ch['total_processed']} read, {ch['total_published']} published | "
            f"Next cursor: {ch['cursor_id']}"
        )
        await self.client.disconnect()


async def main():
    parser = argparse.ArgumentParser(
        description="Extract valuable insights from a Telegram channel/topic"
    )
    parser.add_argument("--channel", required=True, help="Channel username (e.g. VelesCommunityRu)")
    parser.add_argument("--topic", default=None, help="Topic name in forum channel")
    parser.add_argument("--topic-id", type=int, default=None, help="Topic ID (manual override if auto-detection fails)")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH, help="Posts per run (default 1000)")
    args = parser.parse_args()

    channel = args.channel.strip().replace("https://t.me/", "").strip("/")
    agent = InsightsAgent(channel=channel, topic=args.topic, batch=args.batch, topic_id=args.topic_id)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
