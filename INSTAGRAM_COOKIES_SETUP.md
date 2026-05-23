# 🍪 Как добавить Instagram Cookies для yt-dlp

## Проблема

yt-dlp нуждается в cookies для доступа к Instagram видео. Без них выдаёт ошибку:
```
Skipped (no metadata)
```

## ✅ Решение: Используй приложение "Get cookies.txt"

### Вариант 1: С приложением "Get cookies.txt" (рекомендуется)

1. **Открой приложение "Get cookies.txt"** (у тебя уже есть!)
2. **Убедись что ты залогинен в Instagram** в браузере
3. **Нажми "Export All Cookies"** (синяя кнопка)
4. **Выбери формат: Netscape** (как на скрине)
5. **Скопируй всё содержимое** (Ctrl+A → Ctrl+C)
6. **Открой файл** `instagram_cookies.txt` в репо на GitHub
7. **Удали старое содержимое** (строки с примером)
8. **Вставь скопированное** (Ctrl+V)
9. **Commit и push**

### Вариант 2: С расширением EditThisCookie (если нет приложения)

Если не хочешь использовать приложение:
1. Установи [EditThisCookie для Chrome](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
2. Нажми иконку → Export
3. Скопируй JSON
4. В репо обнови `instagram_cookies.txt` вручную с нужными полями

---

## Как использовать

После добавления cookies:

1. **GitHub Actions автоматически будет использовать `instagram_cookies.txt`**
2. **yt-dlp сможет скачивать видео**
3. **AI переписывать описания**
4. **Отправлять в Telegram**

---

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

---

## ⚠️ Важно

- **Cookies содержат твою сессию** — не делись с кем-то и не пусти в публичный репо
- **Cookies истекают** — если перестанет работать, обнови их
- **2FA может помешать** — если у тебя включена 2FA, отключи её временно для экспорта
- **Формат Netscape** — обязательно используй этот формат (txt, не json)

---

## Если не работает

### Ошибка: "Cookies file too small"
- Убедись что скопировал весь текст из приложения
- Файл должен быть больше 100 байт

### Ошибка: "Invalid cookies format"
- Убедись что используешь формат **Netscape**
- Должно быть несколько строк типа: `.instagram.com	TRUE	/	TRUE	...`

### Ошибка: "429 Rate limit"
- Instagram блокирует — подожди 1-24 часа
- Проверь что cookies ещё свежие
- Попробуй отключить 2FA и заново залогиниться

### Ошибка: "Login page barrier"
- Нужно перезалогиниться на Instagram
- Экспортируй cookies снова через приложение

---

## 🔄 Обновление cookies

Если cookies истекли (перестало работать):
1. Открой Instagram в браузере → залогинься заново
2. Экспортируй cookies через приложение "Get cookies.txt"
3. Обнови `instagram_cookies.txt` в репо
4. Попробуй запустить workflow снова

---

**Готово?** Запусти workflow и видео должно скачаться! 🚀
