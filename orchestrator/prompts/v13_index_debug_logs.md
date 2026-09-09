Ниже — ТЕКУЩЕЕ содержимое файла `api/index.py`. Внеси РОВНО ЭТИ изменения и выведи
файл ЦЕЛИКОМ (всё остальное — включая проверку секрета вебхука, ветку
`/api/exchange_token` с `render_page_html`, ветку "health / всё остальное" —
оставь БУКВАЛЬНО без изменений):

1) В импорты добавь `import io` и `import logging` (рядом с `import json`).

2) Замени тело `_process_update`, чтобы функция:
   - на время своей работы вешала временный `logging.Handler`, который пишет
     форматированные записи (включая traceback исключений) в `io.StringIO()`,
     на корневой логгер (`logging.getLogger()`), уровень `logging.DEBUG`;
   - в `finally` снимала этот хендлер (`logger.removeHandler(...)`);
   - возвращала `str | None`: если было наше собственное исключение — его
     `traceback.format_exc()`; ИНАЧЕ, если хендлер поймал хоть один log-рекорд
     уровня `WARNING` и выше — содержимое `StringIO` (`getvalue()`); иначе `None`.

БЫЛО:
```python
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
```

СТАЛО (используй именно такую структуру):
```python
async def _process_update(data: dict) -> str | None:
    bot = Bot(config.BOT_TOKEN)
    store = TokenStore()
    pending = PendingStore()
    http = aiohttp.ClientSession()

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
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
```

3) `import traceback` уже есть в импортах — оставь как есть, если он уже был
   добавлен в предыдущей версии файла (см. ниже, в приведённом оригинале он уже есть).

4) Ветка `/api/telegram` в `app()` — оставь ТОЧНО как в приведённом оригинале ниже
   (уже пишет `error_text` в тело ответа с префиксом `"ERROR:\n"`, код всегда 200) —
   БЕЗ изменений, кроме того что `_process_update` теперь может возвращать текст
   логов, а не только traceback — сама эта ветка не меняется.

ПОЛНЫЙ ТЕКУЩИЙ ФАЙЛ (оригинал, за основу — бери именно эту версию, в ней уже
есть предыдущая диагностическая правка с `error_text`):

```python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import traceback
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
    try:
        update = Update.model_validate(data)
        await dp.feed_update(bot, update, store=store, http=http, pending=pending)
        return None
    except Exception:
        return traceback.format_exc()
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
    path = scope.get("path", "")
    method = scope.get("method", "GET")

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
        if error_text:
            body = ("ERROR:\n" + error_text).encode("utf-8")
            await _send(send, 200, "text/plain; charset=utf-8", body)
        else:
            await _send(send, 200, "text/plain; charset=utf-8", b"ok")
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
```

Выведи ТОЛЬКО итоговый код файла целиком в одном ```python блоке — без пояснений до/после.
