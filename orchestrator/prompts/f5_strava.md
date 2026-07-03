Write `bot/strava.py`: a small async Strava API client using aiohttp. Type hints.

Note in a short module docstring: Strava removed the segment leaderboard API in
2020, so we fetch each athlete's personal record (PR) separately using their own
OAuth token.

Imports:
    from __future__ import annotations
    import time
    from typing import Optional
    import aiohttp
    from bot import config

Constants:
    TOKEN_URL = "https://www.strava.com/oauth/token"
    API_BASE  = "https://www.strava.com/api/v3"

Functions:

def authorize_url(state: str) -> str:
    build the Strava authorize URL. Use urllib.parse.urlencode on these params:
    client_id=config.STRAVA_CLIENT_ID, redirect_uri=config.redirect_uri(),
    response_type="code", approval_prompt="auto", scope=config.STRAVA_SCOPE,
    state=state. Return f"https://www.strava.com/oauth/authorize?{querystring}".

async def _post_token(session: aiohttp.ClientSession, data: dict) -> dict:
    merge client_id=config.STRAVA_CLIENT_ID and client_secret=config.STRAVA_CLIENT_SECRET
    into data, POST form data to TOKEN_URL, read json; if status != 200 raise
    RuntimeError(f"Strava token error {status}: {body}"), else return the json.

async def exchange_code(session, code: str) -> dict:
    return await _post_token(session, {"code": code, "grant_type": "authorization_code"})

async def refresh(session, refresh_token: str) -> dict:
    return await _post_token(session, {"grant_type": "refresh_token",
                                       "refresh_token": refresh_token})

async def valid_access_token(session, store, tg_id: int, record: dict) -> Optional[str]:
    now = int(time.time()). If record.get("expires_at", 0) - 60 > now: return
    record.get("access_token"). Otherwise try refresh(session, record["refresh_token"])
    inside try/except -> on any exception return None. On success update record's
    access_token, refresh_token, expires_at from the response, `await store.set(tg_id, record)`,
    and return the new access_token.

async def segment_pr_seconds(session, access_token: str, segment_id: int) -> Optional[int]:
    GET f"{API_BASE}/segments/{segment_id}" with header
    Authorization: f"Bearer {access_token}". If status != 200 return None.
    Read json, take data.get("athlete_segment_stats") or {}, then
    stats.get("pr_elapsed_time"); return int(pr) if truthy else None.
