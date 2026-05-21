"""
Content Agent: monitors subscribed channels, rewrites posts via AI, sends to Saved Messages
"""
import asyncio
import logging
import os
from telethon import TelegramClient
from telethon.tl.types import Channel, MessageMediaPhoto, MessageMediaDocument
from ai_providers import AIProviderChain
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

REWRITE_PROMPT = """Ты — редактор Telegram-канала про нейросети и технологии.

Перепиши этот пост для моего канала. Требования:
- Сохрани суть и факты
- Сделай текст живым и интересным
- Пиши на русском языке
- Максимум 800 символов
- Не упоминай источник
- Не пиши вступления типа "Вот переписанный пост:"
- Начинай сразу с контента
- Если пост — реклама или вакансия, пропусти его (ответь только словом: SKIP)

Оригинальный пост:
{text}"""

POSTS_PER_CHANNEL = 3
CHANNELS_LIMIT = 10
AI_DELAY = 5  # seconds between AI requests to avoid rate limits


class ContentAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        # Gemini first — more stable and free, Mistral last to avoid rate limits
        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }
        # Override priority: gemini → cerebras → mistral
        priority = ["gemini", "cerebras", "mistral"]
        providers_config = [(p, api_key_map[p]) for p in priority]
        self.ai = AIProviderChain(providers_config, "")

    async def run(self):
        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name}")

        channels = await self.get_subscribed_channels()
        logger.info(f"📋 Processing {len(channels)} channels")

        processed = 0
        for channel in channels:
            posts = await self.get_recent_posts(channel)
            for post_text, post_message in posts:
                rewritten = await self.rewrite_post(post_text, channel.title)
                if rewritten and rewritten != "SKIP":
                    await self.send_to_saved(rewritten, channel.title, post_message)
                    processed += 1
                elif rewritten == "SKIP":
                    logger.info(f"⏭️ Skipped ad/vacancy post from {channel.title}")
                await asyncio.sleep(AI_DELAY)  # pause between AI requests

        logger.info(f"✨ Done! Sent {processed} posts to Saved Messages")
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

    async def rewrite_post(self, text: str, source_title: str) -> str | None:
        """Rewrite post via AI, return None on error"""
        try:
            logger.info(f"🤖 Rewriting from {source_title}...")
            prompt = REWRITE_PROMPT.format(text=text[:2000])
            response = await self.ai.get_response(prompt, [])

            # If AI returned an error message — skip this post
            if response.startswith("Sorry") or response.startswith("Error") or "All providers" in response:
                logger.warning(f"❌ AI error for post from {source_title}: {response[:80]}")
                return None

            return response.strip()
        except Exception as e:
            logger.error(f"Rewrite error: {e}")
            return None

    async def send_to_saved(self, text: str, source_title: str, original_message):
        """Send rewritten post + original media to Saved Messages"""
        try:
            header = f"📌 {source_title}\n\n"
            full_text = header + text

            has_media = original_message.media and isinstance(
                original_message.media, (MessageMediaPhoto, MessageMediaDocument)
            )

            if has_media:
                # Download media and send with rewritten caption
                media_file = await self.client.download_media(original_message.media)
                if media_file:
                    await self.client.send_file("me", media_file, caption=full_text)
                    # Clean up temp file
                    try:
                        os.remove(media_file)
                    except Exception:
                        pass
                    logger.info(f"✅ Sent with media to Saved Messages")
                    return

            # Text only
            await self.client.send_message("me", full_text)
            logger.info(f"✅ Sent text to Saved Messages")

        except Exception as e:
            logger.error(f"Send error: {e}")


async def main():
    agent = ContentAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
