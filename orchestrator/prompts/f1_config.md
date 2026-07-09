Write `bot/config.py`. Reads all settings from environment variables (a .env is
loaded elsewhere before this module is reloaded). No secrets hardcoded.

Start with: `from __future__ import annotations` and `import os`.

Helper:
    def _int(name: str, default: int) -> int:
        read os.environ.get(name); if it is set and non-blank return int(it),
        else return default.

Module-level variables (all via os.environ.get with the given defaults):
    BOT_TOKEN            = env "BOT_TOKEN", default ""
    STRAVA_CLIENT_ID     = env "STRAVA_CLIENT_ID", default ""
    STRAVA_CLIENT_SECRET = env "STRAVA_CLIENT_SECRET", default ""
    SEGMENT_ID           = _int("SEGMENT_ID", 769755)
    SEGMENT_NAME         = env "SEGMENT_NAME", default "Avala"
    STRAVA_SCOPE         = env "STRAVA_SCOPE", default "read,activity:read_all"
    TOKENS_PATH          = env "TOKENS_PATH", default "bot/data/tokens.json"
    OAUTH_HOST           = env "OAUTH_HOST", default "localhost"
    OAUTH_PORT           = _int("OAUTH_PORT", 8000)
    OAUTH_PUBLIC_BASE    = env "OAUTH_PUBLIC_BASE", default
                           f"http://{OAUTH_HOST}:{OAUTH_PORT}"
    REDIRECT_PATH        = "/api/exchange_token"   (a plain constant)
    TELEGRAM_WEBHOOK_SECRET = env "TELEGRAM_WEBHOOK_SECRET", default ""
    ADMIN_ID             = _int("ADMIN_ID", 0)
        # Telegram user id разрешённого администратора. 0 = админ не задан,
        # значит админские команды (например /revoke_all) должны отказывать всем.
    UPSTASH_REDIS_REST_URL   = env "UPSTASH_REDIS_REST_URL" OR env "KV_REST_API_URL",
                               default "" (try the first, fall back to the second)
    UPSTASH_REDIS_REST_TOKEN = env "UPSTASH_REDIS_REST_TOKEN" OR env "KV_REST_API_TOKEN",
                               default "" (same fallback pattern)

Functions:
    def redirect_uri() -> str:
        return OAUTH_PUBLIC_BASE with any trailing "/" removed, + REDIRECT_PATH

    def use_redis() -> bool:
        return True only if BOTH UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN
        are non-empty.
