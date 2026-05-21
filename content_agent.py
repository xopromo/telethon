"""
Content Agent: monitors AI/tech channels, rewrites posts, sends to Saved Messages
"""
import asyncio
import logging
import os
from telethon import TelegramClient
from telethon.tl.types import Channel
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

REWRITE_PROMPT = """You are a Telegram content editor.

Rewrite the following post for my personal channel. Rules:
- Keep the core idea and facts
- Make it more engaging and concise
- Write in Russian
- Keep it under 1000 characters
- Do NOT add emojis excessively (max 2-3)
- Do NOT mention the original source
- Start directly with the content, no intro like "Here is..." or "Rewritten:"

Original post:
{text}"""

POSTS_PER_CHANNEL = 3  # How many recent posts to take from each channel
CHANNELS_LIMIT = 10    # How many channels to monitor


class ContentAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }
        providers_config = [
            (provider, api_key_map.get(provider))
            for provider in PROVIDER_PRIORITY
        ]
        self.ai = AIProviderChain(providers_config, "")

    async def run(self):
        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name}")

        # Get user's channel subscriptions
        channels = await self.get_subscribed_channels()
        logger.info(f"📋 Found {len(channels)} channels to process")

        processed = 0
        for channel in channels:
            posts = await self.get_recent_posts(channel)
            for post in posts:
                rewritten = await self.rewrite_post(post, channel.title)
                if rewritten:
                    await self.send_to_saved(rewritten, channel.title)
                    processed += 1
                    await asyncio.sleep(2)  # avoid flood limits

        logger.info(f"✨ Done! Sent {processed} posts to Saved Messages")
        await self.client.disconnect()

    async def get_subscribed_channels(self) -> list:
        """Get first 10 channels from user's subscriptions"""
        channels = []

        async for dialog in self.client.iter_dialogs():
            if len(channels) >= CHANNELS_LIMIT:
                break
            # Only channels (not groups, not private chats)
            if isinstance(dialog.entity, Channel) and not dialog.entity.megagroup:
                channels.append(dialog.entity)
                logger.info(f"  📢 {dialog.entity.title}")

        return channels

    async def get_recent_posts(self, channel) -> list:
        """Get recent text posts from a channel"""
        posts = []
        try:
            async for message in self.client.iter_messages(channel, limit=POSTS_PER_CHANNEL):
                # Only text posts (skip media-only, ads, forwarded)
                if message.text and len(message.text) > 100 and not message.fwd_from:
                    posts.append(message.text)
        except Exception as e:
            logger.warning(f"⚠️ Could not read {channel.title}: {e}")
        return posts

    async def rewrite_post(self, text: str, source_title: str) -> str | None:
        """Rewrite a post using AI"""
        try:
            logger.info(f"🤖 Rewriting post from {source_title}...")
            prompt = REWRITE_PROMPT.format(text=text[:2000])
            response = await self.ai.get_response(prompt, [])
            return response
        except Exception as e:
            logger.error(f"Error rewriting: {e}")
            return None

    async def send_to_saved(self, text: str, source_title: str):
        """Send rewritten post to Saved Messages"""
        try:
            header = f"📌 На основе: {source_title}\n\n"
            await self.client.send_message("me", header + text)
            logger.info(f"✅ Sent to Saved Messages")
        except Exception as e:
            logger.error(f"Error sending: {e}")


async def main():
    agent = ContentAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
