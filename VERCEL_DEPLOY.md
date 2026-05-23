# 🚀 Развертывание на Vercel

## За 5 минут сделай свой сервер!

### Шаг 1: Открой Vercel
1. Открой https://vercel.com
2. Нажми **Sign up**
3. Выбери **GitHub** (login с GitHub)
4. Авторизуйся

### Шаг 2: Импортируй репо
1. Нажми **Add New** → **Project**
2. Выбери твой репо: `xopromo/telethon`
3. Нажми **Import**

### Шаг 3: Добавь GitHub Token
1. Перед деплоем → **Environment Variables**
2. Name: `GITHUB_TOKEN`
3. Value: Твой GitHub Personal Access Token
   - Как получить token:
     - https://github.com/settings/tokens
     - **Generate new token (classic)**
     - Выбери scope: `repo`, `public_repo`
     - Скопируй token
4. Нажми **Add**

### Шаг 4: Развернись
1. Нажми **Deploy**
2. Подожди 2-3 минуты
3. ✅ Готово!

---

## Что получишь

```
https://xxxxxx.vercel.app

Твой сайт будет работать на этом URL!
```

---

## Как обновить?

```bash
git push origin <branch>
```

Vercel автоматически:
1. Видит push
2. Пересобирает проект
3. Развертывает новую версию

За 1 минуту всё готово!

---

## Если что-то не работает

### Ошибка: "GITHUB_TOKEN not found"
- Проверь что добавил Environment Variable
- Перепроверь имя: `GITHUB_TOKEN` (точно)
- Пересоберись: Settings → Redeploy

### Ошибка: "API not found"
- Проверь что `api/create-issue.js` есть в репо
- Пусти `git push` заново

### Медленно загружается
- Это нормально для первого запуска
- Потом будет быстро

---

## Тестирование

После деплоя:

1. Обнови GitHub Pages сайт:
   - `https://xopromo.github.io/telethon/`

2. Вставь Instagram ссылку

3. Нажми "Скачать"

4. ✅ Issue должна создаться автоматически!

---

**Готово!** 🎉
