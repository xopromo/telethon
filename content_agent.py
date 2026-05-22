"""
Content Agent (manual run):
- Collects latest posts from subscribed channels
- Groups similar posts → mini-digest (2+ posts on same topic)
- Single posts → rewrite as usual
"""
import asyncio
import logging
import os
import json
import re
import hashlib
from telethon import TelegramClient
from telethon.tl.types import Channel, MessageMediaPhoto, MessageMediaDocument
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

PROCESSED_IDS_FILE = "processed_ids.json"
ALL_SEEN_POSTS_FILE = "all_seen_posts.json"  # Global deduplication

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

POSTS_PER_CHANNEL = 3
CHANNELS_LIMIT = 20

# ── Prompts ────────────────────────────────────────────────────────────────────

GROUPING_PROMPT = """Вот свежие посты из разных Telegram-каналов.
Найди посты, которые пишут об ОДНОМ И ТОМ ЖЕ конкретном событии, релизе или анонсе.

Посты:
{posts_list}

Верни ТОЛЬКО валидный JSON без пояснений:
{{
  "название темы": [1, 4],
  "другая тема": [2, 7, 9],
  ...
}}

Правила:
- Группируй ТОЛЬКО если посты описывают буквально одно и то же: один и тот же продукт, одну и ту же функцию, одно и то же объявление
- "Оба про ИИ" или "оба про нейросети" — это НЕ повод объединять
- Одиночные посты не включай (только группы 2+)
- Если сомневаешься — не группируй
- Название темы — 3-6 слов на русском
- Если нет подходящих групп — верни пустой объект {{}}"""

REWRITE_PROMPT_TEMPLATE = """Ты — редактор моего Telegram-канала. Канал о: {channel_topic}.

Перепиши этот пост для канала:
- Сохрани суть и факты
- Сделай текст живым и интересным
- Пиши на русском языке
- Максимум 800 символов
- Не упоминай источник
- Без эмодзи, хештегов
- Оставь внешние ссылки (не t.me)
- Начинай сразу с контента
- Если реклама или вакансия — ответь только: SKIP

Пост:
{{text}}"""

MINI_DIGEST_PROMPT_TEMPLATE = """Ты — редактор моего Telegram-канала. Канал о: {channel_topic}.

Проверь, действительно ли эти посты об одном и том же событии в рамках темы канала, и если да — напиши один короткий пост.

Тема: {{topic}}

Посты:
{{posts_text}}

Требования:
- Сначала убедись, что все посты об одном конкретном событии/продукте/анонсе
- Если посты о РАЗНЫХ вещах — ответь только: SKIP
- Объедини факты из постов об одном событии, убери повторы
- Пиши на русском языке
- Максимум 600 символов — это быстрая новость, не статья
- Без эмодзи, хештегов
- Оставь важные внешние ссылки (не t.me)
- Начинай сразу с сути"""

# ── Text cleanup ───────────────────────────────────────────────────────────────

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


# ── Agent ──────────────────────────────────────────────────────────────────────

class ContentAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }
        providers_config = [(p, api_key_map[p]) for p in ["mistral", "gemini", "cerebras"]]
        self.ai = AIProviderChain(providers_config, "")
        self.delay = AdaptiveDelay(initial=3.0, min_delay=3.0, max_delay=120.0)

    # ── Persistence ────────────────────────────────────────────────────────────

    def load_processed_ids(self) -> dict:
        try:
            with open(PROCESSED_IDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_processed_ids(self, ids: dict):
        with open(PROCESSED_IDS_FILE, "w") as f:
            json.dump(ids, f, indent=2)

    def is_processed(self, ids, channel_id, message_id) -> bool:
        return str(message_id) in ids.get(str(channel_id), [])

    def mark_processed(self, ids, channel_id, message_id):
        key = str(channel_id)
        if key not in ids:
            ids[key] = []
        if str(message_id) not in ids[key]:
            ids[key].append(str(message_id))
        ids[key] = ids[key][-100:]

    def load_all_seen_posts(self) -> dict:
        """Load global deduplication database"""
        try:
            with open(ALL_SEEN_POSTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_all_seen_posts(self, posts: dict):
        """Save global deduplication database"""
        with open(ALL_SEEN_POSTS_FILE, "w") as f:
            json.dump(posts, f, indent=2)

    def sentence_hashes(self, text: str) -> list[str]:
        """Hash first 3 sentences individually.
        Even if title is changed, sentences 2-3 will match."""
        # Split by sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        # Take first 3 non-empty sentences, min 30 chars to skip tiny fragments
        sentences = [s.strip().lower() for s in sentences if len(s.strip()) >= 30][:3]
        return [hashlib.md5(s.encode()).hexdigest()[:8] for s in sentences]

    def count_matching_sentences(self, seen_posts: dict, text: str) -> int:
        """Count how many sentence hashes of text match any previously seen post"""
        new_hashes = set(self.sentence_hashes(text))
        if not new_hashes:
            return 0
        max_matches = 0
        for channel_data in seen_posts.values():
            for stored_hashes in channel_data.values():
                if isinstance(stored_hashes, list):
                    matches = len(new_hashes & set(stored_hashes))
                    if matches > max_matches:
                        max_matches = matches
        return max_matches

    def record_post(self, seen_posts: dict, channel_id: int, message_id: int, text: str):
        """Store sentence hashes for this post"""
        channel_key = str(channel_id)
        if channel_key not in seen_posts:
            seen_posts[channel_key] = {}

        seen_posts[channel_key][str(message_id)] = self.sentence_hashes(text)

        # Keep last 300 posts per channel
        seen_posts[channel_key] = dict(list(seen_posts[channel_key].items())[-300:])

    # ── Channel topic detection ────────────────────────────────────────────────

    async def detect_channel_topic(self, channel, sample_messages: list) -> str:
        """Detect channel topic from sample messages"""
        sample_text = "\n".join(
            f"- {m.text[:100].strip()}"
            for m in sample_messages[:10]
            if m.text
        )
        if not sample_text:
            return "General"

        prompt = f"""Посмотри на эти посты из канала "{channel.title}" и определи основную тематику в 1-2 словах.

Посты:
{sample_text}

Ответь только тему (2-3 слова на русском), без объяснений."""

        try:
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            topic = response.strip().strip('"').strip("'")[:50]
            return topic if topic else "General"
        except Exception as e:
            logger.warning(f"Topic detection failed for {channel.title}: {e}")
            return "General"

    # ── Main flow ──────────────────────────────────────────────────────────────

    async def run(self):
        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name}")

        processed_ids = self.load_processed_ids()
        seen_posts = self.load_all_seen_posts()

        offset = processed_ids.get("_channel_offset", 0)
        logger.info(f"🔄 Channel offset: {offset}")

        # Step 1: collect all fresh posts
        all_posts, next_offset = await self.collect_posts(processed_ids, seen_posts, offset)
        logger.info(f"📦 Collected {len(all_posts)} new posts")

        if not all_posts:
            logger.info("No new posts to process")
            await self.client.disconnect()
            return

        # Step 2: group similar posts via AI (single request)
        groups = {}
        if len(all_posts) >= 2:
            groups = await self.group_by_topic(all_posts)
            logger.info(f"🗂 Found {len(groups)} topic groups")

        # Step 3: figure out which posts are in a group
        grouped_indices = set()
        for indices in groups.values():
            if len(indices) >= 2:
                grouped_indices.update(indices)

        sent = 0

        # Step 4a: send mini-digests for grouped posts
        for topic, indices in groups.items():
            posts_in_group = [all_posts[i] for i in indices if i < len(all_posts)]
            if len(posts_in_group) < 2:
                continue

            result = await self.make_mini_digest(topic, posts_in_group)
            if result and result.strip().upper() != "SKIP":
                await self.send_mini_digest(result, topic, posts_in_group)
                for i in indices:
                    if i < len(all_posts):
                        p = all_posts[i]
                        self.mark_processed(processed_ids, p["channel_id"], p["message_id"])
                sent += 1
            elif result and result.strip().upper() == "SKIP":
                logger.info(f"⏭ Mini-digest skipped (unrelated posts): '{topic}'")
                grouped_indices -= set(indices)  # release back to solo rewrite
            await self.delay.wait()

        # Step 4b: rewrite single posts as usual
        for i, post in enumerate(all_posts):
            if i in grouped_indices:
                continue  # already handled above

            result = await self.rewrite_post(post)
            if result and result.strip() != "SKIP":
                await self.send_post(result, post)
                self.mark_processed(processed_ids, post["channel_id"], post["message_id"])
                sent += 1
            elif result == "SKIP":
                self.mark_processed(processed_ids, post["channel_id"], post["message_id"])

            await self.delay.wait()

        processed_ids["_channel_offset"] = next_offset
        self.save_processed_ids(processed_ids)
        self.save_all_seen_posts(seen_posts)
        logger.info(f"✨ Done! Sent {sent} items to Saved Messages")
        await self.client.disconnect()

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_posts(self, processed_ids: dict, seen_posts: dict, offset: int = 0) -> tuple[list, int]:
        posts = []
        channels_found = 0
        channels_skipped = 0

        async for dialog in self.client.iter_dialogs():
            if channels_found >= CHANNELS_LIMIT:
                break
            if not (isinstance(dialog.entity, Channel) and not dialog.entity.megagroup):
                continue

            # Skip channels before offset for rotation
            if channels_skipped < offset:
                channels_skipped += 1
                continue

            channel = dialog.entity
            channels_found += 1
            logger.info(f"  📢 {channel.title}")

            # Detect channel topic on first encounter
            channel_key = str(channel.id)
            if "_topics" not in processed_ids:
                processed_ids["_topics"] = {}
            if channel_key not in processed_ids["_topics"]:
                # Collect sample messages for topic detection
                sample_msgs = []
                async for msg in self.client.iter_messages(channel, limit=20):
                    if msg.text:
                        sample_msgs.append(msg)
                channel_topic = await self.detect_channel_topic(channel, sample_msgs)
                processed_ids["_topics"][channel_key] = channel_topic
                logger.info(f"🏷 Topic: {channel_topic}")
            else:
                channel_topic = processed_ids["_topics"][channel_key]

            try:
                async for message in self.client.iter_messages(channel, limit=POSTS_PER_CHANNEL):
                    if not message.text or len(message.text) < 100:
                        continue
                    if message.fwd_from:
                        continue

                    # Skip if already processed
                    if self.is_processed(processed_ids, channel.id, message.id):
                        continue

                    # Dedup: 2+ sentence matches = exact duplicate, skip
                    # 1 sentence match = partial, allow but flag for grouping only
                    match_count = self.count_matching_sentences(seen_posts, message.text)
                    if match_count >= 2:
                        logger.info(f"⏭ Exact duplicate skipped in {channel.title}")
                        continue

                    posts.append({
                        "text": message.text,
                        "channel": channel.title,
                        "channel_id": channel.id,
                        "message_id": message.id,
                        "message_obj": message,
                        "partial": match_count == 1,
                        "channel_topic": channel_topic,
                    })

                    self.record_post(seen_posts, channel.id, message.id, message.text)
            except Exception as e:
                logger.warning(f"⚠️ Could not read {channel.title}: {e}")

        # Next run starts after the channels we just processed; reset when exhausted
        next_offset = offset + channels_found if channels_found >= CHANNELS_LIMIT else 0
        logger.info(f"🔄 Next offset will be: {next_offset}")
        return posts, next_offset

    # ── Group ──────────────────────────────────────────────────────────────────

    async def group_by_topic(self, posts: list) -> dict:
        posts_list = "\n".join(
            f"{i+1}. [{p['channel']}] {p['text'][:120].strip()}"
            for i, p in enumerate(posts)
        )
        prompt = GROUPING_PROMPT.format(posts_list=posts_list)

        try:
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                return {}
            raw = json.loads(json_match.group())
            return {
                topic: [i - 1 for i in indices if isinstance(i, int)]
                for topic, indices in raw.items()
                if len(indices) >= 2
            }
        except Exception as e:
            logger.error(f"Grouping failed: {e}")
            return {}

    # ── Generate ───────────────────────────────────────────────────────────────

    async def make_mini_digest(self, topic: str, posts: list) -> str | None:
        posts_text = "\n\n---\n\n".join(
            f"Канал: {p['channel']}\n{p['text'][:600]}"
            for p in posts
        )
        channel_topic = posts[0].get("channel_topic", "General") if posts else "General"
        mini_digest_prompt = MINI_DIGEST_PROMPT_TEMPLATE.format(channel_topic=channel_topic)
        prompt = mini_digest_prompt.format(topic=topic, posts_text=posts_text)
        try:
            logger.info(f"📰 Mini-digest: '{topic}' ({len(posts)} posts)")
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            return clean_text(response)
        except Exception as e:
            logger.error(f"Mini-digest failed: {e}")
            return None

    async def rewrite_post(self, post: dict) -> str | None:
        channel_topic = post.get("channel_topic", "General")
        rewrite_prompt = REWRITE_PROMPT_TEMPLATE.format(channel_topic=channel_topic)
        prompt = rewrite_prompt.format(text=post["text"][:2000])
        try:
            logger.info(f"✏️ Rewriting from {post['channel']}")
            response = await self.ai.get_response(prompt, [], delay=self.delay)
            return clean_text(response)
        except Exception as e:
            logger.error(f"Rewrite failed: {e}")
            return None

    # ── Send ───────────────────────────────────────────────────────────────────

    async def send_post(self, text: str, post: dict):
        """Single rewritten post + original"""
        try:
            message_obj = post["message_obj"]
            has_media = message_obj.media and isinstance(
                message_obj.media, (MessageMediaPhoto, MessageMediaDocument)
            )

            header = f"[ {post['channel']} ]\n\n"
            full_text = header + text

            if has_media:
                media_file = await self.client.download_media(message_obj.media)
                if media_file:
                    await self.client.send_file("me", media_file, caption=full_text)
                    try:
                        os.remove(media_file)
                    except Exception:
                        pass
                    return

            await self.client.send_message("me", full_text)

            # Original for reference
            await self.client.send_message(
                "me",
                f"ОРИГИНАЛ [ {post['channel']} ]\n\n{post['text']}",
                link_preview=True,
            )
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def send_mini_digest(self, text: str, topic: str, posts: list):
        """Mini-digest post + originals"""
        try:
            channels = ", ".join(dict.fromkeys(p["channel"] for p in posts))
            header = f"МИНИ-ДАЙДЖЕСТ: {topic}\n{channels}\n\n"
            await self.client.send_message("me", header + text)

            # Originals for reference
            originals = "\n\n---\n\n".join(
                f"[ {p['channel']} ]\n{p['text'][:400]}"
                for p in posts
            )
            await self.client.send_message(
                "me",
                f"ОРИГИНАЛЫ ({len(posts)} поста)\n\n{originals}",
                link_preview=True,
            )
            logger.info(f"✅ Sent mini-digest: '{topic}'")
        except Exception as e:
            logger.error(f"Send mini-digest error: {e}")


async def main():
    agent = ContentAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
