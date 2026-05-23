# 🍪 Как добавить Instagram Cookies для yt-dlp

## Проблема

yt-dlp нуждается в cookies для доступа к Instagram видео. Без них выдаёт ошибку:
```
Skipped (no metadata)
```

## Решение: Экспортируй cookies из Chrome

### Шаг 1: Установи расширение

👉 [EditThisCookie для Chrome](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)

### Шаг 2: Экспортируй cookies

1. **Открой Chrome**
2. **Зайди на Instagram** (убедись что залогинен)
3. **Нажми на иконку EditThisCookie** (вверху справа браузера)
4. **Нажми кнопку Export** (внизу popup'а)
5. **Скопируй весь JSON** что выпадет

Должно выглядеть примерно так:
```json
[
  {
    "domain": ".instagram.com",
    "name": "sessionid",
    "value": "your-very-long-session-id-here...",
    "path": "/",
    ...
  },
  {
    "domain": ".instagram.com", 
    "name": "csrftoken",
    "value": "your-csrf-token...",
    ...
  },
  ...
]
```

### Шаг 3: Добавь в репо

1. **Открой** `instagram_cookies.json` в репо на GitHub
2. **Replace весь контент** на скопированный JSON
3. **Commit и push**

## Как использовать

После добавления cookies:

1. GitHub Actions автоматически будет использовать `instagram_cookies.json`
2. yt-dlp сможет скачивать видео
3. AI переписывать описания
4. Отправлять в Telegram

## Проверка что работает

Запусти workflow:
1. **Actions → Download Instagram Video**
2. **Введи Instagram ссылку**
3. **Run workflow**

Если в логах видишь:
```
✅ Got Instagram info: Video by ...
✅ AI rewrite done
✅ Downloaded: ...
✅ Published to Saved Messages
```

Значит всё работает! 🎉

## ⚠️ Важно

- **Cookies содержат твою сессию** — не делись с кем-то
- **Cookies истекают** — если перестанет работать, обнови их
- **2FA может помешать** — если у тебя включена 2FA, отключи её временно
- **Не пиши cookies прямо в код** — всегда используй `instagram_cookies.json` файл

## Если не работает

### Ошибка: "Cookies file not found"
- Убедись что `instagram_cookies.json` в корне репо
- Проверь что файл не пустой

### Ошибка: "Invalid cookies format"
- Убедись что скопировал JSON целиком (это список `[...]`)
- Проверь что нет ошибок синтаксиса

### Ошибка: "429 Rate limit"
- Instagram блокирует — подожди 1-24 часа
- Проверь что cookies ещё свежие
- Попробуй отключить 2FA и заново залогиниться

### Ошибка: "Login page barrier"
- Нужно перезалогиниться на Instagram
- Экспортируй cookies снова

## 🔄 Обновление cookies

Если cookies истекли (перестало работать):
1. Открой Instagram в Chrome → залогинься заново
2. Экспортируй cookies через EditThisCookie
3. Обнови `instagram_cookies.json` в репо
4. Попробуй запустить workflow снова

---

**Готово?** Теперь видео должно скачиваться! 🚀
