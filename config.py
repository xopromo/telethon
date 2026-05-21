import os
from dotenv import load_dotenv

load_dotenv()

# Telegram configuration
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')

# AI Provider configuration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower()  # gemini, mistral, cerebras

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Mistral API
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')

# Cerebras API
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY', '')

# System prompt for AI
SYSTEM_PROMPT = """You are a helpful AI assistant integrated into Telegram.
You help the user with various tasks including:
- Answering questions
- Writing and editing text
- Analysis and explanations
- Coding help
- And more

Keep responses concise for Telegram (max 4096 characters).
Be direct and helpful."""
