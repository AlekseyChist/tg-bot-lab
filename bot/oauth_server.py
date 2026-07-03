from __future__ import annotations
import asyncio
import logging
import aiohttp
from aiohttp import web
from bot import config, strava

log = logging.getLogger(__name__)

async def _delete_later(bot, chat_id, message_id, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def _page(title: str, body: str) -> web.Response:
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<h2>{title}</h2>
<p>{body}</p>
<p>Можно закрыть вкладку и вернуться в Telegram.</p>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")

def build_app(*, store, http: aiohttp.ClientSession, pending: dict, bot) -> web.Application:
    async def exchange(request):
        error = request.query.get("error")
        code = request.query.get("code")
        state = request.query.get("state", "")
        
        if error or not code:
            return _page("Не удалось привязать", f"Ошибка: {error or 'не получен код'}")
            
        pend = pending.pop(state, None)
        if not pend:
            return _page("Ссылка устарела", "Запусти привязку заново командой /link")
            
        try:
            tok = await strava.exchange_code(http, code)
        except Exception as e:
            log.exception("Ошибка при обмене кода на токены")
            return _page("Ошибка Strava", str(e))
            
        athlete = tok.get("athlete") or {}
        record = {
            "athlete_id": athlete.get("id"),
            "name": pend["name"],
            "access_token": tok["access_token"],
            "refresh_token": tok["refresh_token"],
            "expires_at": tok["expires_at"],
        }
        
        await store.set(pend["tg_id"], record)
        
        # убрать из чата сообщение-приглашение с кнопкой (если знаем его id):
        pmid = pend.get("prompt_message_id")
        if pmid:
            try:
                await bot.delete_message(pend["chat_id"], pmid)
            except Exception:
                pass
                
        # подтверждение в чат, самоудаляется через 8с, чтобы не засорять:
        try:
            msg = await bot.send_message(pend["chat_id"],
                f"✅ {pend['name']} привязал(а) Strava. Жми /board.")
            asyncio.create_task(_delete_later(bot, pend["chat_id"], msg.message_id, 8))
        except Exception:
            pass
            
        return _page("Готово ✅", "Strava успешно привязана.")
        
    app = web.Application()
    app.router.add_get(config.REDIRECT_PATH, exchange)
    return app

async def start(app: web.Application):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.OAUTH_HOST, config.OAUTH_PORT)
    await site.start()
    log.info("OAuth сервер запущен на %s:%d", config.OAUTH_HOST, config.OAUTH_PORT)
    return runner
