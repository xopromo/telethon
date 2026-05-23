# 📥 Скачай Instagram видео в один клик через GitHub!

## 🎯 Как пользоваться

### 1️⃣ Открой GitHub репо
[Перейди сюда](https://github.com/xopromo/telethon)

### 2️⃣ Нажми на "Actions"
![screenshot: Actions tab at top](https://imgur.com/placeholder.png)

### 3️⃣ Выбери "📥 Download Instagram Video"
Слева в списке workflows найди "Download Instagram Video"

### 4️⃣ Нажми "Run workflow"
Зелёная кнопка справа

### 5️⃣ Введи Instagram ссылку
```
https://www.instagram.com/p/DYpsm93IVGM/
```

### 6️⃣ Нажми ещё раз "Run workflow"

### 7️⃣ Жди 2-5 минут ⏳
Видео загружается в Telegram Saved Messages автоматически!

---

## ✅ Результат

Видео появится в **Saved Messages** с:
- 🎬 Видеофайлом
- 📝 Описанием переписанным AI
- 🔗 Ссылкой на оригинальный пост

---

## 🔍 Как проверить статус

1. Открой вкладку "Actions" на GitHub
2. Нажми на последний запуск (самый верхний)
3. Смотри логи: ✅ зелёный = успех, ❌ красный = ошибка

---

## ⚠️ Требования

Для работы нужны GitHub Secrets (админ уже должен их добавить):
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_PHONE`
- `MISTRAL_API_KEY`
- `GEMINI_API_KEY`
- `CEREBRAS_API_KEY`

> Если что-то не работает → попроси админа проверить Secrets

---

## 🚀 Примеры ссылок

```
✅ Работает:
https://www.instagram.com/p/DYpsm93IVGM/
https://www.instagram.com/reel/ABC123DEF/
https://instagram.com/p/XYZ789/

❌ Не работает:
instagram.com (слишком общая)
https://www.instagram.com/username/ (профиль, не пост)
```

---

## 🎉 Вот и всё!

Нет паузы на установку, нет терминала, просто:
1. Нажал Actions
2. Ввел ссылку
3. Готово!

**GitHub сделает все сам!** 🤖
