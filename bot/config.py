from __future__ import annotations
import os

def _int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value and value.strip():
        return int(value)
    return default

BOT_TOKEN            = os.environ.get("BOT_TOKEN", "")
STRAVA_CLIENT_ID     = os.environ.get("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")
SEGMENT_ID           = _int("SEGMENT_ID", 769755)
SEGMENT_NAME         = os.environ.get("SEGMENT_NAME", "Avala")
OAUTH_HOST           = os.environ.get("OAUTH_HOST", "localhost")
OAUTH_PORT           = _int("OAUTH_PORT", 8000)
OAUTH_PUBLIC_BASE    = os.environ.get("OAUTH_PUBLIC_BASE", f"http://{OAUTH_HOST}:{OAUTH_PORT}")
REDIRECT_PATH        = "/exchange_token"
STRAVA_SCOPE         = os.environ.get("STRAVA_SCOPE", "read,activity:read_all")
TOKENS_PATH          = os.environ.get("TOKENS_PATH", "bot/data/tokens.json")

def redirect_uri() -> str:
    base = OAUTH_PUBLIC_BASE.rstrip("/")
    return base + REDIRECT_PATH
