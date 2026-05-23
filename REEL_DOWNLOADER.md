# 🎬 Instagram Reel Downloader

Веб-приложение для скачивания Instagram reels с ограничением 2 в сутки.

## Как использовать

### Для пользователя:
1. Открой: https://xopromo.github.io/telethon/
2. Вставь ссылку на Instagram reel
3. Нажми "Скачать"
4. Видео появится в артефактах GitHub Actions

### Лимиты:
- **2 скачивания в сутки** на все пользователи
- Лимит обновляется каждый день в 00:00 UTC
- Логируется в `rate_limiter.json`

### Для админа (без лимита):
Запусти workflow вручную с правом на push:
```bash
git push <branch>
# Лимит не будет проверяться
```

## Файлы

- `docs/index.html` — веб-форма (GitHub Pages)
- `rate_limiter.json` — логирование скачиваний
- `check_reel_limit.py` — проверка лимита
- `.github/workflows/download-reel.yml` — workflow для скачивания

## Требования

- `yt-dlp` (установляется в workflow автоматически)
- GitHub Pages включен в репо

## Как включить GitHub Pages

1. Открыть Settings → Pages
2. Source: Deploy from a branch
3. Branch: main / docs folder
4. Нажать Save

Готово! Сайт будет доступен по ссылке: `https://<username>.github.io/<repo>/`
