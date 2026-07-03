Напиши целиком файл `bot/config.py` — модуль конфигурации Telegram-бота, читающий
настройки из переменных окружения. Только стандартная библиотека (`os`).

Требования (точно, ничего лишнего):

Вверху: `from __future__ import annotations` и `import os`.

Приватный помощник:
```
def _int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value and value.strip():
        return int(value)
    return default
```

Константы уровня модуля (читаются из окружения при импорте):
- `BOT_TOKEN = os.environ.get("BOT_TOKEN", "")`
- `STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", "")`
- `STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")`
- `SEGMENT_ID = _int("SEGMENT_ID", 769755)`
- `SEGMENT_NAME = os.environ.get("SEGMENT_NAME", "Avala")`
- `STRAVA_SCOPE = os.environ.get("STRAVA_SCOPE", "read,activity:read_all")`
- `TOKENS_PATH = os.environ.get("TOKENS_PATH", "bot/data/tokens.json")` — файловый фолбэк.
- `OAUTH_HOST = os.environ.get("OAUTH_HOST", "localhost")` — только для локального polling-сервера.
- `OAUTH_PORT = _int("OAUTH_PORT", 8000)` — только для локального polling-сервера.
- `OAUTH_PUBLIC_BASE = os.environ.get("OAUTH_PUBLIC_BASE", f"http://{OAUTH_HOST}:{OAUTH_PORT}")`
- `REDIRECT_PATH = "/api/exchange_token"`  — ВАЖНО: именно этот путь (Vercel-функция).
- `TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")`
- `UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "")`
- `UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")`

Функции:
```
def redirect_uri() -> str:
    base = OAUTH_PUBLIC_BASE.rstrip("/")
    return base + REDIRECT_PATH

def use_redis() -> bool:
    return bool(UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)
```

Никаких классов, никакого I/O, никакого logging. Выведи ТОЛЬКО код файла целиком в одном ```python блоке.
