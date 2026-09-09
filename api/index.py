import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import traceback
import io
import logging
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


async def _process_update(data: dict) -> str | None:
    bot = Bot(config.BOT_TOKEN)
    store = TokenStore()
    pending = PendingStore()
    http = aiohttp.ClientSession()

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    try:
        update = Update.model_validate(data)
        await dp.feed_update(bot, update, store=store, http=http, pending=pending)
        captured = log_stream.getvalue()
        return captured if captured else None
    except Exception:
        return traceback.format_exc()
    finally:
        root_logger.removeHandler(handler)
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
    path = scope.get("path", "")
    method = scope.get("method", "GET")

    qs = scope.get("query_string", b"").decode("utf-8")
    if "showscope" in qs:
        info = f"path={path!r} method={method!r} qs={qs!r} raw_path={scope.get('raw_path')!r} root_path={scope.get('root_path')!r} keys={list(scope.keys())!r}"
        await _send(send, 200, "text/plain; charset=utf-8", info.encode("utf-8"))
        return

    if path == "/api/telegram" and method == "POST":
        secret = _header(scope, "x-telegram-bot-api-secret-token")
        if config.TELEGRAM_WEBHOOK_SECRET and secret != config.TELEGRAM_WEBHOOK_SECRET:
            await _send(send, 403, "text/plain; charset=utf-8", b"forbidden")
            return
        raw = await _read_body(receive)
        error_text = None
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
            error_text = await _process_update(data)
        except Exception:
            error_text = traceback.format_exc()
        marker = f"DEBUG-V15 raw_len={len(raw)} path={path!r}\n"
        body = (marker + "ERROR/LOG:\n" + (error_text or "(nothing captured)")).encode("utf-8")
        await _send(send, 200, "text/plain; charset=utf-8", body)
        return

    if path == "/api/exchange_token" and method == "GET":
        raw_qs = scope.get("query_string", b"").decode("utf-8")
        parsed = parse_qs(raw_qs)
        query = {k: v[0] for k, v in parsed.items()}
        try:
            title, body = await _handle_exchange(query)
        except Exception as e:
            import traceback
            traceback.print_exc()
            title, body = "Ошибка", str(e)
        page = oauth_server.render_page_html(title, body).encode("utf-8")
        await _send(send, 200, "text/html; charset=utf-8", page)
        return

    # health / всё остальное
    await _send(send, 200, "text/plain; charset=utf-8", b"ok")
