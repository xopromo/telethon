# 🎬 Instagram Video Downloader

Скачивай видео с Instagram прямо в Telegram Saved Messages!

---

## 3️⃣ Способа запуска

### 1️⃣ **GitHub Actions** (самый простой!) 🌟

Без установки, без кода, просто нажимаешь на GitHub:

```
GitHub → Actions → "Download Instagram Video" → 
Ввести ссылку → Run → Готово в Saved Messages
```

📖 Детали: [GITHUB_QUICKSTART.md](GITHUB_QUICKSTART.md)

---

### 2️⃣ **Один клик на своём компьютере**

Для Mac/Linux:
```bash
bash run.sh
```

Для Windows:
```
Двойной клик на run.bat
```

📖 Детали: [QUICKSTART.md](QUICKSTART.md)

---

### 3️⃣ **Командная строка** (для продвинутых)

```bash
python instagram_agent.py "https://www.instagram.com/p/ABC123/"
```

📖 Детали: [INSTAGRAM_AGENT_USAGE.md](INSTAGRAM_AGENT_USAGE.md)

---

## 🎯 Рекомендация

| Вариант | Кому | Сложность |
|---------|------|-----------|
| **GitHub Actions** | Новичкам, без установки | ⭐ Легко |
| **run.sh / run.bat** | Дома на компьютере | ⭐⭐ Средне |
| **Командная строка** | Разработчикам | ⭐⭐⭐ Сложно |

---

## ✨ Что делает

1. Скачивает видео с Instagram
2. Переписывает описание через AI
3. Отправляет в Telegram Saved Messages

**Всё автоматически!**

---

## 🚀 Быстрый старт

### Если у тебя есть GitHub:
1. Открой [Actions](https://github.com/xopromo/telethon/actions)
2. Нажми "Download Instagram Video"
3. Введи ссылку
4. **Готово!** 🎉

### Если хочешь локально:
1. Скачай [репо](https://github.com/xopromo/telethon)
2. Запусти `run.sh` (Mac/Linux) или `run.bat` (Windows)
3. Введи ссылку
4. **Готово!** 🎉

---

## 📋 Требования

- Instagram аккаунт (залогинен в браузере)
- Telegram аккаунт (с API ключами)
- AI API ключи (Mistral, Gemini, Cerebras)

---

## 🆘 Помощь

- GitHub Actions не работает? → проверь Secrets в Settings
- Локальный запуск не работает? → посмотри QUICKSTART.md
- Более подробно? → смотри INSTAGRAM_AGENT_USAGE.md

---

**Выбирай способ и начинай! 🚀**
