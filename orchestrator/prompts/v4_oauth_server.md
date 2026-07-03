Напиши целиком файл `bot/oauth_server.py`. Он обслуживает Strava OAuth-callback.
Ядро вынесено в переиспользуемую корутину `process_exchange`, которую зовут ОБА:
локальный aiohttp-сервер (polling-режим) и Vercel-функция `api/exchange_token.py`.

Импорты: `from __future__ import annotations`, `import asyncio, logging`, `import aiohttp`,
`from aiohttp import web`, `from bot import config, strava`.
`log = logging.getLogger(__name__)`.

1) Помощник авто-удаления сообщения (как было):
```
async def _delete_later(bot, chat_id, message_id, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass
```

2) Рендер HTML-страницы как СТРОКИ (используется и локально, и в Vercel-функции):
```
def render_page_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<h2>{title}</h2>
<p>{body}</p>
<p>Можно закрыть вкладку и вернуться в Telegram.</p>
</body>
</html>"""
```

3) Ядро обмена — принимает query как обычный dict (плоские строковые значения),
   возвращает кортеж `(title: str, body: str)`. НИКАКИХ web.Response внутри.
```
async def process_exchange(query: dict, *, store, http: aiohttp.ClientSession, pending, bot) -> tuple[str, str]:
```
Логика:
- `error = query.get("error")`, `code = query.get("code")`, `state = query.get("state", "")`
- если `error` или нет `code` → вернуть `("Не удалось привязать", f"Ошибка: {error or 'не получен код'}")`
- `pend = await pending.pop(state)`  (ВНИМАНИЕ: pending — это PendingStore, метод async!)
- если не `pend` → вернуть `("Ссылка устарела", "Запусти привязку заново командой /link")`
- try: `tok = await strava.exchange_code(http, code)`
  except Exception as e: `log.exception("Ошибка при обмене кода на токены")`; вернуть `("Ошибка Strava", str(e))`
- `athlete = tok.get("athlete") or {}`
- собрать record:
  `{"athlete_id": athlete.get("id"), "name": pend["name"], "access_token": tok["access_token"], "refresh_token": tok["refresh_token"], "expires_at": tok["expires_at"]}`
- `await store.set(pend["tg_id"], record)`
- удалить сообщение-приглашение, если знаем id:
  `pmid = pend.get("prompt_message_id")`; если pmid: `try: await bot.delete_message(pend["chat_id"], pmid) except Exception: pass`
- отправить подтверждение и запланировать его авто-удаление:
  ```
  try:
      msg = await bot.send_message(pend["chat_id"], f"✅ {pend['name']} привязал(а) Strava. Жми /board.")
      asyncio.create_task(_delete_later(bot, pend["chat_id"], msg.message_id, 8))
  except Exception:
      pass
  ```
- вернуть `("Готово ✅", "Strava успешно привязана.")`

4) Локальный aiohttp-обработчик и приложение (для polling-режима bot.main):
```
def build_app(*, store, http: aiohttp.ClientSession, pending, bot) -> web.Application:
    async def exchange(request):
        query = dict(request.query)
        title, body = await process_exchange(query, store=store, http=http, pending=pending, bot=bot)
        return web.Response(text=render_page_html(title, body), content_type="text/html")
    app = web.Application()
    app.router.add_get(config.REDIRECT_PATH, exchange)
    return app
```

5) Запуск локального сервера (как было):
```
async def start(app: web.Application):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.OAUTH_HOST, config.OAUTH_PORT)
    await site.start()
    log.info("OAuth сервер запущен на %s:%d", config.OAUTH_HOST, config.OAUTH_PORT)
    return runner
```

Выведи ТОЛЬКО код файла целиком в одном ```python блоке.
