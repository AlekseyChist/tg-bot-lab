import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from urllib.parse import parse_qs
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from bot import config, oauth_server
from bot.handlers import router
from bot.storage import TokenStore, PendingStore


async def _read_body(receive) -> bytes:
    body = b""
    more = True
    while more:
        msg = await receive()
        body += msg.get("body", b"")
        more = msg.get("more_body", False)
    return body


async def _send(send, status: int, content_type: str, body: bytes) -> None:
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", content_type.encode("utf-8")),
            (b"content-length", str(len(body)).encode("utf-8")),
        ],
    })
    await send({"type": "http.response.body", "body": body})


def _header(scope, name: str) -> str:
    target = name.lower().encode("utf-8")
    for k, v in scope.get("headers", []):
        if k == target:
            return v.decode("utf-8")
    return ""


dp = Dispatcher()
dp.include_router(router)


async def _process_update(data: dict) -> None:
    bot = Bot(config.BOT_TOKEN)
    store = TokenStore()
    pending = PendingStore()
    http = aiohttp.ClientSession()
    try:
        update = Update.model_validate(data)
        await dp.feed_update(bot, update, store=store, http=http, pending=pending)
    finally:
        await http.close()
        await bot.session.close()


async def _handle_exchange(query: dict):
    bot = Bot(config.BOT_TOKEN)
    store = TokenStore()
    pending = PendingStore()
    http = aiohttp.ClientSession()
    try:
        return await oauth_server.process_exchange(query, store=store, http=http, pending=pending, bot=bot)
    finally:
        await http.close()
        await bot.session.close()


async def app(scope, receive, send) -> None:
    if scope["type"] != "http":
        return
    method = scope.get("method", "GET")
    raw_qs = scope.get("query_string", b"").decode("utf-8")
    parsed = parse_qs(raw_qs)
    route = parsed.get("_route", [""])[0]

    if route == "_debug_board":
        from bot import strava
        store = TokenStore()
        http = aiohttp.ClientSession()
        try:
            users = await store.all()
            out = [f"users={list(users.keys())!r}"]
            for tg_id_str, record in users.items():
                out.append(f"--- tg_id={tg_id_str} record={record!r}")
                token = await strava.valid_access_token(http, store, int(tg_id_str), record)
                out.append(f"token_ok={bool(token)!r}")
                if token:
                    url = f"{strava.API_BASE}/segments/{config.SEGMENT_ID}"
                    headers = {"Authorization": f"Bearer {token}"}
                    async with http.get(url, headers=headers) as resp:
                        raw_body = await resp.text()
                        out.append(f"segment_status={resp.status} body={raw_body[:2000]}")
            info = "\n".join(out)
        except Exception:
            import traceback
            info = traceback.format_exc()
        finally:
            await http.close()
        await _send(send, 200, "text/plain; charset=utf-8", info.encode("utf-8"))
        return

    if route == "telegram" and method == "POST":
        secret = _header(scope, "x-telegram-bot-api-secret-token")
        if config.TELEGRAM_WEBHOOK_SECRET and secret != config.TELEGRAM_WEBHOOK_SECRET:
            await _send(send, 403, "text/plain; charset=utf-8", b"forbidden")
            return
        raw = await _read_body(receive)
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
            await _process_update(data)
        except Exception:
            import traceback
            traceback.print_exc()
        await _send(send, 200, "text/plain; charset=utf-8", b"ok")
        return

    if route == "exchange_token" and method == "GET":
        query = {k: v[0] for k, v in parsed.items() if k != "_route"}
        try:
            title, body = await _handle_exchange(query)
        except Exception as e:
            import traceback
            traceback.print_exc()
            title, body = "Ошибка", str(e)
        page = oauth_server.render_page_html(title, body).encode("utf-8")
        await _send(send, 200, "text/html; charset=utf-8", page)
        return

    await _send(send, 200, "text/plain; charset=utf-8", b"ok")
