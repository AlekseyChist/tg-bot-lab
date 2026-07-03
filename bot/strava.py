from __future__ import annotations
import time
from typing import Optional
import aiohttp
from bot import config
from urllib.parse import urlencode

TOKEN_URL = "https://www.strava.com/oauth/token"
API_BASE  = "https://www.strava.com/api/v3"

def authorize_url(state: str) -> str:
    params = {
        "client_id": config.STRAVA_CLIENT_ID,
        "redirect_uri": config.redirect_uri(),
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": config.STRAVA_SCOPE,
        "state": state
    }
    querystring = urlencode(params)
    return f"https://www.strava.com/oauth/authorize?{querystring}"

async def _post_token(session: aiohttp.ClientSession, data: dict) -> dict:
    data["client_id"] = config.STRAVA_CLIENT_ID
    data["client_secret"] = config.STRAVA_CLIENT_SECRET
    async with session.post(TOKEN_URL, data=data) as response:
        body = await response.text()
        if response.status != 200:
            raise RuntimeError(f"Strava token error {response.status}: {body}")
        return await response.json()

async def exchange_code(session: aiohttp.ClientSession, code: str) -> dict:
    return await _post_token(session, {"code": code, "grant_type": "authorization_code"})

async def refresh(session: aiohttp.ClientSession, refresh_token: str) -> dict:
    return await _post_token(session, {"grant_type": "refresh_token",
                                       "refresh_token": refresh_token})

async def valid_access_token(session: aiohttp.ClientSession, store, tg_id: int, record: dict) -> Optional[str]:
    now = int(time.time())
    if record.get("expires_at", 0) - 60 > now:
        return record.get("access_token")
    
    try:
        response = await refresh(session, record["refresh_token"])
    except Exception:
        return None
    
    record["access_token"] = response["access_token"]
    record["refresh_token"] = response["refresh_token"]
    record["expires_at"] = now + response["expires_in"]
    await store.set(tg_id, record)
    return record["access_token"]

async def segment_pr_seconds(session: aiohttp.ClientSession, access_token: str, segment_id: int) -> Optional[int]:
    url = f"{API_BASE}/segments/{segment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            return None
        data = await response.json()
        stats = data.get("athlete_segment_stats", {})
        pr = stats.get("pr_elapsed_time")
        return int(pr) if pr else None
