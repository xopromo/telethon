# Instagram Agent — Полная документация

## Описание

**instagram_agent.py** — отдельный агент, который:
1. Мониторит указанный Telegram канал на наличие Instagram ссылок
2. Скачивает видео через yt-dlp
3. Переписывает описание через AI (Mistral → Gemini → Cerebras)
4. Публикует видео + переписанное описание в Saved Messages
5. Отслеживает обработанные ссылки (не обрабатывает дважды)

---

## Установка зависимостей

```bash
pip install yt-dlp telethon mistralai google-generativeai
```

Убедись, что установлены все API ключи в `.env`:
```env
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_PHONE=+1234567890
SESSION_NAME=telegram_session

MISTRAL_API_KEY=your_key
GEMINI_API_KEY=your_key
CEREBRAS_API_KEY=your_key
```

---

## Конфигурация

### Основные параметры (в коде)

| Параметр | Значение | Описание |
|----------|----------|---------|
| `INSTAGRAM_SOURCE_CHANNEL` | `"instagram"` | Канал/username для мониторинга. Измени на свой канал! |
| `INSTAGRAM_OUTPUT_DIR` | `/tmp/instagram_downloads` | Директория для скачанных видео |
| `MAX_VIDEO_SIZE_MB` | 2000 | Максимальный размер видео (лимит Telegram 4GB) |
| `PROCESSED_INSTAGRAM_FILE` | `processed_instagram.json` | Файл для отслеживания обработанных ссылок |

### Измени INSTAGRAM_SOURCE_CHANNEL

```python
# Вариант 1: По username канала
INSTAGRAM_SOURCE_CHANNEL = "your_channel_username"

# Вариант 2: По ID канала
INSTAGRAM_SOURCE_CHANNEL = 1234567890

# Вариант 3: По полной ссылке
INSTAGRAM_SOURCE_CHANNEL = "https://t.me/your_channel"
```

---

## Использование

### 1️⃣ Быстрый старт: скачать одно видео по ссылке

```bash
python instagram_agent.py "https://www.instagram.com/p/DYpsm93IVGM/"
```

Вывод:
```
Processing: https://www.instagram.com/p/DYpsm93IVGM/
✅ Got Instagram info: Video by alex_ponyatov
✅ AI rewrite done
✅ Downloaded: /tmp/instagram_downloads/video.mp4 (125.3MB)
✅ Published to Saved Messages
✅ Video processed and saved to Saved Messages
```

**Видео сразу отправится в Saved Messages!**

### 2️⃣ Мониторить канал: процессить все новые ссылки

Сначала настрой канал:
```python
# instagram_agent.py
INSTAGRAM_SOURCE_CHANNEL = "your_channel_name"  # или ID
```

Затем запусти без аргументов:
```bash
python instagram_agent.py
```

Вывод:
```
📡 Channel monitoring mode: your_channel_name
✅ Found channel: Your Channel
Processing: https://www.instagram.com/p/DYpsm93IVGM/
✅ Got Instagram info: Video by alex_ponyatov
...
✅ Finished. Processed 5 new videos
```

### 2️⃣ Запланированный запуск (GitHub Actions)

Создай `.github/workflows/instagram-agent.yml`:

```yaml
name: Instagram Agent

on:
  schedule:
    # Каждые 6 часов
    - cron: '0 */6 * * *'
  workflow_dispatch:

jobs:
  instagram:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install yt-dlp telethon mistralai google-generativeai python-dotenv
      
      - name: Run Instagram Agent
        env:
          TELEGRAM_API_ID: ${{ secrets.TELEGRAM_API_ID }}
          TELEGRAM_API_HASH: ${{ secrets.TELEGRAM_API_HASH }}
          TELEGRAM_PHONE: ${{ secrets.TELEGRAM_PHONE }}
          SESSION_NAME: instagram_session
          MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          CEREBRAS_API_KEY: ${{ secrets.CEREBRAS_API_KEY }}
        run: python instagram_agent.py
      
      - name: Commit and push changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "Instagram Agent"
          git add processed_instagram.json
          git commit -m "Update Instagram Agent state" --allow-empty
          git push
```

---

## Архитектура

### Поток обработки

```
Telegram Channel
    ↓
Extract Instagram URLs
    ↓
Check if already processed
    ↓
Get video metadata (yt-dlp)
    ↓
Rewrite description (AI)
    ↓
Download video (yt-dlp + browser cookies)
    ↓
Publish to Saved Messages
    ↓
Mark as processed
```

### AI Реwrite

Агент использует AIProviderChain с fallback порядком:
1. **Mistral** (основной)
2. **Gemini** (если Mistral не ответил)
3. **Cerebras** (если оба выше не ответили)

На каждый запрос система:
- Отправляет оригинальное описание видео
- AI переписывает его для публикации
- Если AI вернёт "SKIP" → видео пропускается (реклама или невалидный контент)
- Результат очищается от emoji, хештегов, t.me ссылок

### Дедупликация

Все обработанные Instagram URL сохраняются в `processed_instagram.json`:

```json
{
  "urls": [
    "https://www.instagram.com/p/DYpsm93IVGM/",
    "https://www.instagram.com/p/DXabcd12EF/"
  ]
}
```

При каждом запуске агент проверяет этот файл и пропускает уже обработанные URL.

---

## Требования к yt-dlp

### Аутентификация в Instagram

yt-dlp нужны cookies для доступа к видео. Есть несколько способов:

#### ✅ Best: Chrome/Firefox cookies (автоматически)
```bash
# yt-dlp автоматически прочитает cookies из браузера
yt-dlp --cookies-from-browser chrome "https://www.instagram.com/p/..."
```

Убедись, что:
- Ты залогинен в Instagram в Chrome/Firefox
- Нет 2FA или отключена
- Cookies сохранены

#### Альтернатива: Cookies файл

Экспортируй cookies из браузера (расширение EditThisCookie) в `cookies.txt`:

```python
# В instagram_downloader.py добавь:
result = subprocess.run([
    "yt-dlp",
    "--cookies", "cookies.txt",
    "-o", output_template,
    url,
])
```

#### ⚠️ Не рекомендуется: Username + Password
```python
result = subprocess.run([
    "yt-dlp",
    "-u", "your_username",
    "-p", "your_password",
    url,
])
```

---

## Вывод в Saved Messages

Каждый опубликованный видео выглядит так:

```
[Переписанное AI описание видео]

Duration: 120s
By: Alex Ponyatov

[Ссылка на оригинальный Instagram пост]
```

Видео файл загружается непосредственно в Telegram (не через ссылку).

---

## Обработка ошибок

| Ошибка | Решение |
|--------|---------|
| `Unable to download webpage` | Проверь yt-dlp cookies (Chrome/Firefox) |
| `403 Forbidden` | Instagram заблокировала доступ → перелогинься в браузер |
| `Instagram locked behind login` | Нужна real Instagram account (yt-dlp требует) |
| `Connection timeout` | Проверь интернет или задай больший timeout |
| `Video size > 2GB` | Агент пропустит видео автоматически |

---

## Примеры использования

### CLI примеры

```bash
# Скачать одно видео
python instagram_agent.py "https://www.instagram.com/p/DYpsm93IVGM/"

# Скачать Reel
python instagram_agent.py "https://www.instagram.com/reel/ABC123/"

# Мониторить канал (все новые ссылки за последние 100 постов)
python instagram_agent.py

# С логированием
python instagram_agent.py "https://www.instagram.com/p/..." 2>&1 | tee download.log
```

### Примеры настройки

### Вариант 1: Мониторить приватный канал
```python
INSTAGRAM_SOURCE_CHANNEL = -1001234567890  # ID приватного канала
```

### Вариант 2: Разные папки для разных источников
```python
def get_output_dir(channel_name: str) -> str:
    return f"/tmp/instagram_{channel_name}"
```

### Вариант 3: Лимит по времени
```python
# Обработать только посты за последние 24 часа
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(hours=24)

async for message in client.iter_messages(entity, limit=200):
    if message.date < cutoff:
        break
```

---

## Performance

**Типичные значения:**
- Получение метаданных: 2-5 сек
- AI rewrite: 5-10 сек  
- Скачивание видео (150MB): 30-60 сек
- Загрузка в Telegram: 10-20 сек

**Всего на одно видео: ~2-3 минуты**

---

## Tips & Tricks

1. **Тестируй локально сначала**
   ```bash
   python instagram_agent.py
   ```

2. **Смотри логи**
   ```bash
   python instagram_agent.py 2>&1 | tee instagram.log
   ```

3. **Проверь yt-dlp версию**
   ```bash
   yt-dlp -U  # Обновить до последней
   ```

4. **Отключи 2FA в Instagram на время инициального скрейпинга**
   Instagram может требовать подтверждение при новом access

5. **Запусти в отдельной сессии**
   ```bash
   nohup python instagram_agent.py > instagram.log 2>&1 &
   ```

---

## Логирование

Агент логирует все события:
- `✅ Got Instagram info` — метаданные получены
- `✅ AI rewrite done` — описание переписано
- `✅ Downloaded` — видео скачано
- `✅ Published to Saved Messages` — опубликовано
- `⏭️ Already processed` — уже обработано ранее
- `⏭️ Skipped by AI filter` — AI отклонила (реклама)
- `❌ Failed to get info/download/publish` — ошибка

---

## Лицензирование и Terms of Service

⚠️ **Важно:** Instagram Terms of Service запрещают автоматизированный скрейпинг.

**Рекомендуемый подход:**
- Используй для личного использования
- Не массово публикуй чужой контент
- Уважай авторские права
- Дай credit источнику (ссылка на оригинал всегда рядом)

---

## Интеграция с другими агентами

Если хочешь, чтобы Instagram видео обрабатывались как обычные посты:

```python
# content_agent.py
from instagram_downloader import InstagramDownloader

async def process_instagram_message(message):
    urls = extract_instagram_urls(message.text)
    for url in urls:
        await instagram_agent.process_instagram_url(url, ...)
```

Или используй Instagram Agent как отдельный процесс (рекомендуется).
