"""
Small async Strava API client using aiohttp.

Note: Strava removed the segment leaderboard API in 2020, so we fetch each
athlete's personal record (PR) separately using their own OAuth token.
"""
from __future__ import annotations

import time
from typing import Optional
import aiohttp
from bot import config


TOKEN_URL = "https://www.strava.com/oauth/token"
DEAUTHORIZE_URL = "https://www.strava.com/oauth/deauthorize"
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

    async with session.post(TOKEN_URL, data=data) as response:
        body = await response.json()
        if response.status != 200:
            raise RuntimeError(f"Strava token error {response.status}: {body}")
        return body


async def exchange_code(session: aiohttp.ClientSession, code: str) -> dict:
    """Exchange an authorization code for tokens."""
    return await _post_token(session, {"code": code, "grant_type": "authorization_code"})


async def refresh(session: aiohttp.ClientSession, refresh_token: str) -> dict:
    """Refresh an access token using a refresh token."""
    return await _post_token(
        session, {"grant_type": "refresh_token", "refresh_token": refresh_token}
    )


async def revoke_token(session: aiohttp.ClientSession, access_token: str) -> bool:
    """
    Deauthorize the athlete on Strava. This invalidates ALL of that athlete's
    refresh/access tokens and removes the app from their Strava settings.

    IMPORTANT: Strava's deauthorize endpoint requires a *valid, non-expired
    ACCESS token* — a refresh token or an expired access token does NOT work.
    Callers must first obtain a fresh access token via valid_access_token()
    (which refreshes when needed) and pass it here.

    We use POST DEAUTHORIZE_URL with Bearer auth. (This legacy endpoint is
    supported through 2027-06-01; migrating to POST /oauth/revoke later is a
    known follow-up, but /deauthorize is the simplest reliably-working method.)
    """
    if not access_token:
        return False

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with session.post(DEAUTHORIZE_URL, headers=headers) as response:
            return response.status == 200
    except Exception:
        return False


async def valid_access_token(
    session: aiohttp.ClientSession, store, tg_id: int, record: dict
) -> Optional[str]:
    """
    Ensure we have a valid access token. Refresh if necessary.
    Returns the access token or None on failure.
    """
    now = int(time.time())
    expires_at = record.get("expires_at", 0)

    # If token is still valid (with 60s buffer), return it
    if expires_at - 60 > now:
        return record.get("access_token")

    # Otherwise, try to refresh
    try:
        new_tokens = await refresh(session, record["refresh_token"])
    except Exception:
        return None

    # Update the record with new tokens
    record["access_token"] = new_tokens.get("access_token")
    record["refresh_token"] = new_tokens.get("refresh_token")
    record["expires_at"] = now + new_tokens.get("expires_in", 0)

    await store.set(tg_id, record)

    return record.get("access_token")


async def segment_pr_seconds(
    session: aiohttp.ClientSession, access_token: str, segment_id: int
) -> Optional[int]:
    """
    Fetch the personal record (PR) elapsed time for a segment.
    Returns seconds as int, or None if not found/error.
    """
    url = f"{API_BASE}/segments/{segment_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            return None

        data = await response.json()
        stats = data.get("athlete_segment_stats") or {}
        pr = stats.get("pr_elapsed_time")

        if pr:
            return int(pr)
        return None
