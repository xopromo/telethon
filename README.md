# Telegram AI Agent

Personal AI assistant for Telegram powered by Claude API and Telethon library.

## Setup

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Create a new application to get `API_ID` and `API_HASH`
3. Have your phone number ready

### 2. Get Claude API Key

1. Go to https://console.anthropic.com
2. Create an API key
3. Copy it

### 3. Configure

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your editor
```

Example `.env`:
```
TELEGRAM_API_ID=123456789
TELEGRAM_API_HASH=abcdef123456...
TELEGRAM_PHONE=+1234567890
ANTHROPIC_API_KEY=sk-ant-...
BOT_USERNAME=yourname
SESSION_NAME=telegram_session
```

### 4. Run

```bash
python agent.py
```

First run will ask you to confirm your Telegram login (you'll receive a code via SMS).

## Features

✅ Real-time message processing  
✅ Conversation context memory  
✅ Claude AI responses  
✅ Typing indicator while processing  
✅ Error handling  

## Usage

Just send any message to your account and the AI will respond!

## Notes

- The agent only responds to messages sent directly to your account
- Conversation history is kept per user for context
- Responses are limited to 4096 characters (Telegram limit)
