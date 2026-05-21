import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import User
from anthropic import Anthropic
from config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    SESSION_NAME,
    ANTHROPIC_API_KEY,
    SYSTEM_PROMPT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramAIAgent:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
        self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation_history = {}  # Store conversation context per user

    async def start(self):
        """Start the Telegram client and connect"""
        logger.info("Starting Telegram AI Agent...")

        await self.client.start(phone=TELEGRAM_PHONE)
        me = await self.client.get_me()
        logger.info(f"✅ Connected as {me.first_name} (@{me.username})")

        # Set up message handler
        @self.client.on(events.NewMessage)
        async def handle_message(event):
            await self.process_message(event)

        logger.info("📱 Listening for messages...")
        await self.client.run_until_disconnected()

    async def process_message(self, event):
        """Process incoming messages"""
        # Ignore messages from bots and channel messages
        if event.from_id is None:
            return

        sender = await event.get_sender()
        sender_id = event.sender_id
        message_text = event.text

        # Get user identifier
        user_identifier = f"user_{sender_id}"

        # Don't process empty messages
        if not message_text or not message_text.strip():
            return

        logger.info(f"📨 Message from {sender.first_name}: {message_text[:50]}...")

        # Show typing indicator
        async with self.client.action(event.chat_id, 'typing'):
            # Get response from Claude
            response = await self.get_ai_response(message_text, user_identifier)

            # Send response
            try:
                await event.reply(response)
                logger.info(f"✅ Reply sent to {sender.first_name}")
            except Exception as e:
                logger.error(f"Error sending reply: {e}")
                await event.reply("Sorry, there was an error processing your request.")

    async def get_ai_response(self, user_message: str, user_id: str) -> str:
        """Get response from Claude AI with conversation history"""

        # Initialize conversation history for new users
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        # Add user message to history
        self.conversation_history[user_id].append({
            "role": "user",
            "content": user_message
        })

        # Keep only last 10 messages for context
        messages = self.conversation_history[user_id][-10:]

        try:
            response = self.anthropic_client.messages.create(
                model="claude-opus-4-7",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages
            )

            assistant_message = response.content[0].text

            # Add assistant response to history
            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    async def stop(self):
        """Stop the agent gracefully"""
        logger.info("Stopping Telegram AI Agent...")
        await self.client.disconnect()


async def main():
    """Main entry point"""
    agent = TelegramAIAgent()

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        await agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
