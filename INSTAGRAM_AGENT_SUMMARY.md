# Instagram Agent — Quick Start

✅ **Новый отдельный агент для скачивания Instagram видео**

## Что это делает

```
Telegram Channel → Instagram Links → yt-dlp → AI Rewrite → Saved Messages
```

1. Мониторит указанный Telegram канал на Instagram ссылки
2. Скачивает видео через **yt-dlp** (работает с реальным браузером)
3. Переписывает описание через **AIProviderChain** (Mistral → Gemini → Cerebras)
4. Публикует в **Saved Messages** с оригинальной ссылкой
5. Отслеживает обработанные URL в `processed_instagram.json` (no duplicates)

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `instagram_agent.py` | Основной агент (async, Telethon + yt-dlp + AI) |
| `instagram_downloader.py` | Утилита для работы с yt-dlp |
| `.github/workflows/instagram-agent.yml` | GitHub Actions (каждые 6 часов) |
| `INSTAGRAM_AGENT_USAGE.md` | Подробная документация |

---

## 2 режима работы

### 📌 Режим 1: Скачать одно видео по ссылке (быстро!)

```bash
python instagram_agent.py https://www.instagram.com/p/DYpsm93IVGM/
```

Результат:
```
Processing: https://www.instagram.com/p/DYpsm93IVGM/
✅ Got Instagram info: Video by alex_ponyatov
✅ AI rewrite done
✅ Downloaded: /tmp/instagram_downloads/video.mp4 (125.3MB)
✅ Published to Saved Messages
✅ Video processed and saved to Saved Messages
```

Видео сразу отправится в Saved Messages с переписанным описанием!

### 📡 Режим 2: Мониторить Telegram канал (автоматический)

Сначала выбери источник в `instagram_agent.py`:
```python
INSTAGRAM_SOURCE_CHANNEL = "your_channel_name"  # или ID канала
```

Затем запусти без аргументов:
```bash
# Ручной запуск (процессит последние 100 сообщений)
python instagram_agent.py

# Или через GitHub Actions (каждые 6 часов)
# Просто push — workflow запустится автоматически
```

---

## Требования

- ✅ Залогинен в Instagram в Chrome/Firefox
- ✅ Нет 2FA или отключена
- ✅ Установлен yt-dlp: `pip install yt-dlp`

---

## Архитектура

```
┌─────────────────────────────────────┐
│     Telegram Channel                │
│  (Instagram links in messages)      │
└────────┬────────────────────────────┘
         │
         ├─→ Extract URLs from messages
         │
         ├─→ Check processed_instagram.json
         │   (skip if already done)
         │
         ├─→ yt-dlp:
         │   ├─ Get metadata (title, duration, uploader)
         │   └─ Download video (using Chrome cookies)
         │
         ├─→ AIProviderChain:
         │   ├─ Mistral (primary)
         │   ├─ Gemini (failover)
         │   └─ Cerebras (last resort)
         │   → Rewrite description
         │
         ├─→ Cleanup text:
         │   ├─ Remove emoji
         │   ├─ Remove hashtags
         │   └─ Remove t.me links
         │
         ├─→ Telegram Client:
         │   └─ Send video + caption to Saved Messages
         │
         └─→ Save URL to processed_instagram.json
```

---

## Примеры вывода

### Логи (консоль)

```
Processing: https://www.instagram.com/p/DYpsm93IVGM/
✅ Got Instagram info: Video by alex_ponyatov
✅ AI rewrite done
✅ Downloaded: /tmp/instagram_downloads/video.mp4 (125.3MB)
✅ Published to Saved Messages
✅ Finished. Processed 5 new videos
```

### Результат в Saved Messages

```
[Переписанное AI описание видео]

Duration: 120s
By: Alex Ponyatov

[Ссылка на оригинальный Instagram пост]
[Видео файл]
```

---

## Конфигурация

### Обязательно измени

```python
# instagram_agent.py
INSTAGRAM_SOURCE_CHANNEL = "your_channel_name"
```

### Опционально

```python
# Максимальный размер видео (лимит Telegram 4GB)
MAX_VIDEO_SIZE_MB = 2000

# Директория для скачанных видео
INSTAGRAM_OUTPUT_DIR = "/tmp/instagram_downloads"

# Файл для отслеживания обработанных URL
PROCESSED_INSTAGRAM_FILE = "processed_instagram.json"
```

---

## GitHub Actions setup

Уже создан `.github/workflows/instagram-agent.yml`:
- ✅ Runs every 6 hours (cron)
- ✅ Manual trigger via `workflow_dispatch`
- ✅ Auto-commits state to repo

Просто push → все работает!

---

## Требования к среде

```bash
# Installation
pip install yt-dlp telethon mistralai google-generativeai python-dotenv

# .env file
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_PHONE=...
SESSION_NAME=telegram_session

MISTRAL_API_KEY=...
GEMINI_API_KEY=...
CEREBRAS_API_KEY=...
```

---

## Отличие от других агентов

| Агент | Источник | Обработка | Вывод |
|-------|----------|-----------|-------|
| **content_agent** | Telegram каналы | Текст → AI | Переписанный текст |
| **digest_agent** | Telegram каналы | 24h → группировка → AI | Статьи |
| **insights_agent** | История канала | Фильтр → AI insights | Insights group |
| **instagram_agent** | **Instagram ссылки** | **Видео → yt-dlp → AI** | **Видео + описание** |

---

## Трабл-шутинг

**yt-dlp не может скачать видео?**
- Проверь, залогинен ли ты в Instagram в Chrome/Firefox
- Попробуй отключить 2FA
- Обнови yt-dlp: `pip install --upgrade yt-dlp`

**AI не переписывает описание?**
- Проверь API ключи в .env
- Посмотри логи (может быть rate limit)

**GitHub Actions не работает?**
- Проверь secrets в GitHub (TELEGRAM_API_ID, MISTRAL_API_KEY и т.д.)
- Посмотри workflow logs в GitHub Actions tab

---

## Next Steps

1. ✅ Установи зависимости
2. ✅ Добавь INSTAGRAM_SOURCE_CHANNEL в instagram_agent.py
3. ✅ Запусти локально: `python instagram_agent.py`
4. ✅ Push в repo → GitHub Actions поднимет автоматически
5. ✅ Проверь Saved Messages на результат

---

## Больше информации

See `INSTAGRAM_AGENT_USAGE.md` for:
- Detailed authentication methods
- Performance tuning
- Advanced configuration
- Integration with other agents
- Licensing & ToS considerations
