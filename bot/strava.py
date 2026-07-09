"""
Strava API client.

Note: Strava removed the segment leaderboard API in 2020, so we fetch each
athlete's personal record (PR) separately using their own OAuth token.
"""
from __future__ import annotations

import base64
import time
from typing import Optional

import aiohttp
from bot import config


TOKEN_URL = "https://www.strava.com/oauth/token"
REVOKE_URL = "https://www.strava.com/oauth/revoke"
API_BASE = "https://www.strava.com/api/v3"


def authorize_url(state: str) -> str:
    """Build the Strava authorize URL."""
    import urllib.parse

    params = {
        "client_id": config.STRAVA_CLIENT_ID,
        "redirect_uri": config.redirect_uri(),
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": config.STRAVA_SCOPE,
        "state": state,
    }
    querystring = urllib.parse.urlencode(params)
    return f"https://www.strava.com/oauth/authorize?{querystring}"


async def _post_token(session: aiohttp.ClientSession, data: dict) -> dict:
    """Post form data to the token endpoint and return JSON response."""
    data["client_id"] = config.STRAVA_CLIENT_ID
    data["client_secret"] = config.STRAVA_CLIENT_SECRET

    async with session.post(TOKEN_URL, data=data) as resp:
        body = await resp.text()
        if resp.status != 200:
            raise RuntimeError(f"Strava token error {resp.status}: {body}")
        return await resp.json()


async def exchange_code(session: aiohttp.ClientSession, code: str) -> dict:
    """Exchange an authorization code for tokens."""
    return await _post_token(session, {"code": code, "grant_type": "authorization_code"})


async def refresh(session: aiohttp.ClientSession, refresh_token: str) -> dict:
    """Refresh an access token using a refresh token."""
    return await _post_token(
        session, {"grant_type": "refresh_token", "refresh_token": refresh_token}
    )


async def revoke_token(
    session: aiohttp.ClientSession,
    token: str,
    token_type_hint: str = "refresh_token",
) -> bool:
    """
    Revoke a user's Strava authorization via the RFC 7009 revoke endpoint.

    Revoking either the refresh or access token invalidates ALL tokens for that
    athlete and removes the app from their Strava settings. Prefer passing the
    refresh_token (it is always present in the stored record even when the access
    token is expired), with token_type_hint="refresh_token".
    """
    if not token:
        return False

    creds = f"{config.STRAVA_CLIENT_ID}:{config.STRAVA_CLIENT_SECRET}"
    b64 = base64.b64encode(creds.encode()).decode()
    headers = {"Authorization": f"Basic {b64}"}

    body = {"token": token, "token_type_hint": token_type_hint}

    try:
        async with session.post(REVOKE_URL, data=body, headers=headers) as resp:
            return resp.status == 200
    except Exception:
        return False


async def valid_access_token(
    session: aiohttp.ClientSession,
    store,
    tg_id: int,
    record: dict,
) -> Optional[str]:
    """Return a valid access token, refreshing if necessary."""
    now = int(time.time())
    expires_at = record.get("expires_at", 0)

    if expires_at - 60 > now:
        return record.get("access_token")

    try:
        response = await refresh(session, record["refresh_token"])
    except Exception:
        return None

    record["access_token"] = response["access_token"]
    record["refresh_token"] = response["refresh_token"]
    record["expires_at"] = int(time.time()) + response["expires_in"]

    await store.set(tg_id, record)

    return record["access_token"]


async def segment_pr_seconds(
    session: aiohttp.ClientSession, access_token: str, segment_id: int
) -> Optional[int]:
    """Fetch the personal record time in seconds for a segment."""
    url = f"{API_BASE}/segments/{segment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return None

        data = await resp.json()
        stats = data.get("athlete_segment_stats") or {}
        pr = stats.get("pr_elapsed_time")

        if pr:
            return int(pr)
        return None
