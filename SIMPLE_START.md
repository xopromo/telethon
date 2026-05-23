# 🎬 Скачай видео с Instagram в 1 клик!

## На твоём компьютере (самый простой способ)

```bash
python download.py
```

Всё! Скрипт спросит ссылку → видео загрузится в Saved Messages.

---

## Требования (одноразово)

```bash
pip install yt-dlp telethon mistralai google-generativeai python-dotenv
```

---

## GitHub Actions (ещё проще, но медленнее)

1. Открой → **Actions** → **Download Instagram Video**
2. Нажми **Run workflow**
3. Введи Instagram ссылку
4. Ждёшь 2-5 минут → видео в Saved Messages ✅

---

## Как это работает?

```
Ты вводишь ссылку
    ↓
yt-dlp скачивает видео с Instagram
    ↓
AI переписывает описание
    ↓
Отправляется в Telegram Saved Messages
    ↓
✅ Готово!
```

---

## Что нужно один раз настроить?

1. **.env файл** (заполни свои ключи):
   ```env
   TELEGRAM_API_ID=your_id
   TELEGRAM_API_HASH=your_hash
   TELEGRAM_PHONE=+1234567890
   MISTRAL_API_KEY=your_key
   GEMINI_API_KEY=your_key
   CEREBRAS_API_KEY=your_key
   ```

2. **SESSION_BASE64** (если на GitHub Actions):
   - Есть уже, генерируется автоматически

---

## Примеры

```bash
# Локально
python download.py
> 🔗 Вставь Instagram ссылку:
> https://www.instagram.com/p/DYpsm93IVGM/
✅ Video скачан и отправлен в Telegram!

# Или напрямую
python instagram_agent.py "https://www.instagram.com/p/DYpsm93IVGM/"
```

---

**Всё просто? Готово! 🚀**
