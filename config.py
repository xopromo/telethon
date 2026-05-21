import os
from dotenv import load_dotenv

load_dotenv()

# Telegram configuration
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')

# API Keys
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', 'Mistral_key_here')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'Gemini_key_here')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY', 'Cerebras_key_here')

# Provider fallback order: try providers in this order, fallback to next if one fails
PROVIDER_PRIORITY = ['mistral', 'gemini', 'cerebras']

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
