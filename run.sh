#!/bin/bash

# Instagram Agent — One-click launcher for Mac/Linux

echo "🚀 Instagram Agent Launcher"
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python не найден. Установи Python 3.8+ и попробуй снова."
    exit 1
fi

# Install dependencies silently
echo "📦 Проверяю зависимости..."
pip install -q yt-dlp telethon mistralai google-generativeai python-dotenv 2>/dev/null

# Ask for Instagram URL
echo ""
read -p "🔗 Введи Instagram ссылку (или Enter для мониторинга канала): " INSTAGRAM_URL

# Run agent
echo ""
if [ -z "$INSTAGRAM_URL" ]; then
    echo "📡 Запускаю мониторинг канала..."
    python3 instagram_agent.py
else
    echo "📌 Скачиваю видео..."
    python3 instagram_agent.py "$INSTAGRAM_URL"
fi
