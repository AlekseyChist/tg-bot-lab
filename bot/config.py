from __future__ import annotations
import os


def _int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value and value.strip():
        return int(value)
    return default


BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")
SEGMENT_ID = _int("SEGMENT_ID", 769755)
SEGMENT_NAME = os.environ.get("SEGMENT_NAME", "Avala")
STRAVA_SCOPE = os.environ.get("STRAVA_SCOPE", "read,activity:read_all")
TOKENS_PATH = os.environ.get("TOKENS_PATH", "bot/data/tokens.json")
OAUTH_HOST = os.environ.get("OAUTH_HOST", "localhost")
OAUTH_PORT = _int("OAUTH_PORT", 8000)
OAUTH_PUBLIC_BASE = os.environ.get("OAUTH_PUBLIC_BASE", f"http://{OAUTH_HOST}:{OAUTH_PORT}")
REDIRECT_PATH = "/api/exchange_token"
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL", "")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN", "")


def redirect_uri() -> str:
    base = OAUTH_PUBLIC_BASE.rstrip("/")
    return base + REDIRECT_PATH


def use_redis() -> bool:
    return bool(UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)
