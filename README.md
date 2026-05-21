# Telegram AI Agent

Personal AI assistant for Telegram with automatic failover between multiple free AI providers.

## AI Provider Fallback System

Agent tries providers in order, automatically switching if one fails:

1. **Mistral** (primary) - Fast and reliable
2. **Google Gemini** (fallback #1) - Most capable
3. **Cerebras** (fallback #2) - Very fast inference

**Example:** If Mistral is down, automatically switches to Gemini. If Gemini fails too, tries Cerebras.

## Two Deployment Options

### Option A: GitHub Actions (FREE MVP) ⭐
Runs every hour automatically, 24/7 for free!

### Option B: Local Machine
Run on your computer when you're online.

---

## Setup for GitHub Actions (Recommended)

### 1. Fork Repository
1. Go to https://github.com/xopromo/telethon
2. Click **Fork** button (top right)
3. This creates your own copy

### 2. Add GitHub Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these secrets:

```
TELEGRAM_API_ID = 94575
TELEGRAM_API_HASH = a3406de8d12d27ecc61ff27eabe69fff
TELEGRAM_PHONE = +79552230812
MISTRAL_API_KEY = 1Xl3lcBIS5TTV0bkHEvmhTwnIM6AJ3VY
GEMINI_API_KEY = AIzaSyDemJMre4p3BFlWyiXCc9aK_XdVnOcOagk
CEREBRAS_API_KEY = csk-wn5mpv6jp5yy5phkc65xfwwt8t8rrthxrfxd4trcfttx5hck
```

### 3. Enable Actions

1. Go to **Actions** tab
2. Click **I understand my workflows, go ahead and enable them**

### 4. It's Running!

Agent now checks for messages **every hour** automatically! 🤖

Check logs: **Actions** tab → Latest workflow run

---

## Alternative: Local Setup

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

### 3. Configure Telegram

Edit `.env` file and add:
```
TELEGRAM_API_ID=123456789
TELEGRAM_API_HASH=abcdef123456hash
TELEGRAM_PHONE=+1234567890
BOT_USERNAME=yourname
```

API keys already added (Mistral, Gemini, Cerebras).

### 4. Install & Run

```bash
pip install -r requirements.txt
python agent.py
```

First run will ask you to confirm your Telegram login (you'll receive a code via SMS).

## Features

✅ **Automatic Failover** - If one provider fails, automatically tries next  
✅ **3 Free AI Providers** - Mistral, Gemini, Cerebras  
✅ **Real-time Processing** - Responds instantly to Telegram messages  
✅ **Context Memory** - Remembers conversation history  
✅ **Resilient** - No single point of failure  

## How It Works

### GitHub Actions Mode (Scheduled)
```
Every hour:
  ↓
Run agent_scheduled.py
  ↓
Check for new messages
  ↓
For each message:
    Try Mistral → Gemini → Cerebras
    ↓
    Send reply
    ↓
Exit
```

### Local Mode (Always Listening)
```
Message received (real-time)
  ↓
Try Mistral API
  ├─ Success? → Send response ✅
  ├─ Fail? → Try Gemini
  │   ├─ Success? → Send response ✅
  │   ├─ Fail? → Try Cerebras
  │   │   ├─ Success? → Send response ✅
  │   │   └─ Fail? → "All providers down" ❌
```

## Usage

Just send any message in Telegram and the agent will respond!

Monitor logs to see which provider is being used:
```
🤖 Trying mistral...
✅ mistral succeeded
```

## API Costs

- **Mistral**: Free tier (2M tokens/month)
- **Gemini**: Free (generous limits)
- **Cerebras**: Completely free
