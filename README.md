# Telegram AI Agent

Personal AI assistant for Telegram powered by free AI providers (Gemini, Mistral, or Cerebras) and Telethon library.

## Supported AI Providers

- **Google Gemini** (free) - Most capable, good for general tasks
- **Mistral** (free tier) - Fast and reliable
- **Cerebras** (free) - Very fast inference

## Setup

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Create a new application to get `API_ID` and `API_HASH`
3. Have your phone number ready

### 2. Get AI API Key (Choose One)

**Option A: Google Gemini (Recommended)**
- Go to https://ai.google.dev
- Click "Get API Key"
- Create new API key (free tier available)

**Option B: Mistral**
- Go to https://console.mistral.ai
- Sign up and get API key
- Free tier includes 2 million tokens

**Option C: Cerebras**
- Go to https://cloud.cerebras.ai
- Sign up and get API key
- Completely free

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

# Choose one provider: gemini, mistral, or cerebras
AI_PROVIDER=gemini

# Set only the API key for your chosen provider
GEMINI_API_KEY=sk-...
MISTRAL_API_KEY=your_mistral_key
CEREBRAS_API_KEY=your_cerebras_key

BOT_USERNAME=yourname
SESSION_NAME=telegram_session
```

### 4. Run

```bash
python agent.py
```

First run will ask you to confirm your Telegram login (you'll receive a code via SMS).

## Features

✅ Multiple free AI providers (Gemini, Mistral, Cerebras)  
✅ Real-time message processing  
✅ Conversation context memory  
✅ Typing indicator while processing  
✅ Error handling  

## Usage

Just send any message to your account and the AI will respond!

## Switching Providers

To switch AI providers, just change `AI_PROVIDER` in `.env` and restart the agent:

```bash
AI_PROVIDER=mistral  # Switch to Mistral
python agent.py
```

## API Costs

- **Gemini**: Free (generous free tier)
- **Mistral**: Free tier (2M tokens/month), then paid
- **Cerebras**: Free to use
