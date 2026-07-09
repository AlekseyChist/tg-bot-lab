Write `bot/strava.py`: a small async Strava API client using aiohttp. Type hints.

Note in a short module docstring: Strava removed the segment leaderboard API in
2020, so we fetch each athlete's personal record (PR) separately using their own
OAuth token.

Imports:
    from __future__ import annotations
    import base64
    import time
    from typing import Optional
    import aiohttp
    from bot import config

Constants:
    TOKEN_URL  = "https://www.strava.com/oauth/token"
    REVOKE_URL = "https://www.strava.com/oauth/revoke"
    API_BASE   = "https://www.strava.com/api/v3"

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

async def revoke_token(session, token: str, token_type_hint: str = "refresh_token") -> bool:
    Revoke a user's Strava authorization via the RFC 7009 revoke endpoint
    (POST REVOKE_URL, effective for Strava since 2026-06-01). Revoking either
    the refresh or access token invalidates ALL tokens for that athlete and
    removes the app from their Strava settings. Prefer passing the refresh_token
    (it is always present in the stored record even when the access token is
    expired), with token_type_hint="refresh_token".

    - if token is falsy: return False (nothing to revoke).
    - build HTTP Basic Auth from config.STRAVA_CLIENT_ID and
      config.STRAVA_CLIENT_SECRET:
        creds = f"{config.STRAVA_CLIENT_ID}:{config.STRAVA_CLIENT_SECRET}"
        b64 = base64.b64encode(creds.encode()).decode()
        headers = {"Authorization": f"Basic {b64}"}
    - form body: {"token": token, "token_type_hint": token_type_hint}
    - POST REVOKE_URL with data=body and headers=headers, inside try/except.
      On any exception return False.
    - Strava returns HTTP 200 with an empty body whether or not the token was
      found, so: return response.status == 200.

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
