"""
Scheduled mode for GitHub Actions - check messages every hour
"""
import asyncio
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events
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
    SYSTEM_PROMPT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScheduledTelegramAIAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
        self.conversation_history = {}

        # Initialize AI provider chain
        api_key_map = {
            "mistral": MISTRAL_API_KEY,
            "gemini": GEMINI_API_KEY,
            "cerebras": CEREBRAS_API_KEY,
        }

        providers_config = [
            (provider, api_key_map.get(provider))
            for provider in PROVIDER_PRIORITY
        ]

        self.ai_provider = AIProviderChain(providers_config, SYSTEM_PROMPT)
        self.last_check_time = datetime.now() - timedelta(hours=1)

    async def check_and_respond(self):
        """Check for new messages and respond"""
        logger.info("🔍 Checking for new messages...")

        try:
            await self.client.start(phone=TELEGRAM_PHONE)
            me = await self.client.get_me()
            logger.info(f"✅ Connected as {me.first_name}")

            # Get all dialogs (conversations)
            processed_count = 0

            async for dialog in self.client.iter_dialogs():
                # Get recent messages
                async for message in self.client.iter_messages(dialog, limit=5):
                    # Check if message is recent and from user
                    if message.date < self.last_check_time:
                        continue

                    if message.out:  # Skip own messages
                        continue

                    if not message.text or not message.text.strip():
                        continue

                    sender = await message.get_sender()
                    sender_id = message.sender_id

                    logger.info(f"📨 Found message from {sender.first_name if sender else 'Unknown'}: {message.text[:50]}...")

                    # Get AI response
                    user_identifier = f"user_{sender_id}"
                    response = await self.get_ai_response(message.text, user_identifier)

                    # Reply to message
                    try:
                        await message.reply(response)
                        logger.info(f"✅ Replied to {sender.first_name if sender else 'Unknown'}")
                        processed_count += 1
                    except Exception as e:
                        logger.error(f"Error replying: {e}")

            logger.info(f"✨ Processed {processed_count} messages")
            self.last_check_time = datetime.now()

        except Exception as e:
            logger.error(f"Error checking messages: {e}")
        finally:
            await self.client.disconnect()

    async def get_ai_response(self, user_message: str, user_id: str) -> str:
        """Get response from AI with conversation history"""

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        self.conversation_history[user_id].append({
            "role": "user",
            "content": user_message
        })

        messages = self.conversation_history[user_id][-10:]

        try:
            assistant_message = await self.ai_provider.get_response(user_message, messages)

            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            logger.error(f"Error calling AI provider: {e}")
            return f"Sorry, I encountered an error: {str(e)}"


async def main():
    """Main entry point for scheduled execution"""
    agent = ScheduledTelegramAIAgent()

    try:
        await agent.check_and_respond()
        logger.info("✅ Check completed successfully")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
