Write `bot/oauth_server.py`: a tiny aiohttp web server that catches the Strava
OAuth redirect. Type hints. Short module docstring in Russian explaining that
Strava redirects the user's browser to {OAUTH_PUBLIC_BASE}/exchange_token with a
`code` and our `state`; we swap the code for tokens, save the link and DM the user.

Imports:
    from __future__ import annotations
    import asyncio
    import logging
    import aiohttp
    from aiohttp import web
    from bot import config, strava

module: log = logging.getLogger(__name__)

Helper coroutine to delete a message after a delay (for auto-cleaning chat):
    async def _delete_later(bot, chat_id, message_id, delay: int) -> None:
        await asyncio.sleep(delay)
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            pass

def _page(title: str, body: str) -> web.Response:
    return web.Response with a tiny utf-8 HTML page showing title and body and a
    line telling the user they can close the tab and return to Telegram.
    content_type="text/html".

def build_app(*, store, http: aiohttp.ClientSession, pending: dict, bot) -> web.Application:
    Define an inner coroutine `async def exchange(request):`
      - error = request.query.get("error"); code = request.query.get("code");
        state = request.query.get("state", "")
      - if error or not code: return _page("Не удалось привязать", ...).
      - pend = pending.pop(state, None); if not pend: return _page("Ссылка устарела",
        "Запусти привязку заново командой /link").
      - try tok = await strava.exchange_code(http, code) except Exception as e:
        log.exception(...) and return _page("Ошибка Strava", str(e)).
      - athlete = tok.get("athlete") or {}. Build record = {
          "athlete_id": athlete.get("id"),
          "name": pend["name"],
          "access_token": tok["access_token"],
          "refresh_token": tok["refresh_token"],
          "expires_at": tok["expires_at"],
        }
      - await store.set(pend["tg_id"], record)
      - # убрать из чата сообщение-приглашение с кнопкой (если знаем его id):
        pmid = pend.get("prompt_message_id")
        if pmid:
            try: await bot.delete_message(pend["chat_id"], pmid) except Exception: pass
      - # подтверждение в чат, самоудаляется через 8с, чтобы не засорять:
        try:
            msg = await bot.send_message(pend["chat_id"],
                f"✅ {pend['name']} привязал(а) Strava. Жми /board.")
            asyncio.create_task(_delete_later(bot, pend["chat_id"], msg.message_id, 8))
        except Exception: pass
        (send to pend["chat_id"] — the chat where /link was used; works in a group,
        and in a private chat chat_id == the user id)
      - return _page("Готово ✅", "Strava успешно привязана.")
    Then: app = web.Application(); app.router.add_get(config.REDIRECT_PATH, exchange);
    return app.

async def start(app: web.Application):
    runner = web.AppRunner(app); await runner.setup();
    site = web.TCPSite(runner, config.OAUTH_HOST, config.OAUTH_PORT); await site.start();
    log.info(...); return runner.
