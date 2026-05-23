@echo off
REM Instagram Agent — One-click launcher for Windows

echo.
echo 🚀 Instagram Agent Launcher
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установи Python 3.8+ и попробуй снова.
    pause
    exit /b 1
)

REM Install dependencies silently
echo 📦 Проверяю зависимости...
pip install -q yt-dlp telethon mistralai google-generativeai python-dotenv >nul 2>&1

REM Ask for Instagram URL
echo.
set /p INSTAGRAM_URL="🔗 Введи Instagram ссылку (или Enter для мониторинга канала): "

REM Run agent
echo.
if "%INSTAGRAM_URL%"=="" (
    echo 📡 Запускаю мониторинг канала...
    python instagram_agent.py
) else (
    echo 📌 Скачиваю видео...
    python instagram_agent.py "%INSTAGRAM_URL%"
)

pause
