# Instagram Video Integration Plan

## ✅ Тест пройден: yt-dlp работает!

### Метаданные успешно получены:
```
- Title: Video by alex_ponyatov
- Duration: 120.3s  
- Uploader: Александр Понятов
```

---

## 📋 Требования для локального использования

### 1. Установка yt-dlp
```bash
pip install yt-dlp
```

### 2. Аутентификация в Instagram
yt-dlp может использовать сохранённые cookies из браузера:

```bash
# Option A: Chrome cookies (автоматически)
yt-dlp --cookies-from-browser chrome "https://www.instagram.com/p/..."

# Option B: Cookies из файла
yt-dlp --cookies "cookies.txt" "https://www.instagram.com/p/..."

# Option C: Username + Password (не рекомендуется)
yt-dlp -u your_username -p your_password "https://www.instagram.com/p/..."
```

**Best practice**: Используй Chrome cookies (автоматически читаются из профиля)

---

## 🔧 Интеграция с Telethon agents

### Вариант 1: Добавить в content_agent.py

```python
from instagram_downloader import InstagramDownloader

async def process_instagram_link(url: str, client: TelegramClient):
    """Скачать видео с Инстаграма и опубликовать в Saved Messages"""
    
    downloader = InstagramDownloader(output_dir="/tmp/instagram_downloads")
    
    # Получить метаданные
    info = downloader.get_info(url)
    if not info:
        print(f"❌ Не удалось получить информацию: {url}")
        return
    
    # Скачать видео
    file_path = downloader.download_reel(url)
    if not file_path:
        print(f"❌ Не удалось скачать: {url}")
        return
    
    # Отправить в Saved Messages
    message = f"""
**{info.get('title', 'Instagram Video')}**

Duration: {info.get('duration', 'unknown')}s
By: {info.get('uploader', 'unknown')}

Source: {url}
"""
    
    await client.send_file("me", file_path, caption=message)
    print(f"✅ Загружено в Saved Messages: {info.get('title')}")
```

### Вариант 2: Отдельный агент instagram_agent.py

Создай новый агент, который:
- Следит за каналом в Telegram (где делятся Instagram ссылками)
- Скачивает видео через yt-dlp
- Обрабатывает через AI (переписывает описание)
- Публикует в Saved Messages

```python
# instagram_agent.py
async def main():
    async with TelegramClient('session', api_id, api_hash) as client:
        # Слушать новые сообщения в канале
        async for message in client.iter_messages(INSTAGRAM_CHANNEL):
            if "instagram.com" in message.text:
                await process_instagram_link(message.text, client)
```

---

## ⚙️ Конфигурация

Добавить в `.env`:
```env
# Instagram
INSTAGRAM_COOKIES_PATH=/path/to/cookies.txt
INSTAGRAM_OUTPUT_DIR=/tmp/instagram_downloads
```

Добавить в `config.py`:
```python
INSTAGRAM_COOKIES_PATH = os.getenv("INSTAGRAM_COOKIES_PATH", "")
INSTAGRAM_OUTPUT_DIR = os.getenv("INSTAGRAM_OUTPUT_DIR", "/tmp/instagram_downloads")
```

---

## ⚠️ Риски и ограничения

| Risk | Решение |
|------|---------|
| Instagram может заблокировать аккаунт | Используй отдельный аккаунт, не лупи слишком часто |
| Требуется аутентификация | Автоматическая работа с Chrome cookies |
| 2FA может помешать | Отключи на время инициального скрейпинга |
| Вес видео → GitHub Actions | Не сохраняй видео в repo, только metadata + ссылку |
| Terms of Service | Для личного использования ок, для распространения — проверить лицензию |

---

## 🚀 Быстрый старт (локально)

1. Убедись, что ты залогинен в Chrome/Firefox с Instagram
2. Запусти скрипт:

```bash
python instagram_downloader.py
```

3. Если сработало → готово интегрировать в agenty!

---

## Альтернативные подходы (если yt-dlp зависнет)

### instagrapi
```bash
pip install instagrapi
```

```python
from instagrapi import Client

client = Client()
client.login(username, password)
media = client.media_info(media_id)
video_url = media.video_url
```

**Pro:** Более надёжна, есть куча функций
**Con:** Требует real Instagram account (ban risk выше)

### instagram-scraper
```bash
pip install instagram-scraper
```

**Pro:** Быстра
**Con:** Часто ломается (Instagram меняет структуру)

---

## Рекомендация

✅ **Используй yt-dlp** — самый стабильный и поддерживаемый проект
- Регулярно обновляется (реагирует на изменения Instagram)
- Большое сообщество
- Работает через реальный браузер (меньше риск блокировки)
