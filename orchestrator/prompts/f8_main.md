Write `bot/main.py`: bootstrap for an aiogram 3.x bot plus the OAuth callback
server. Type hints.

Imports:
    import asyncio
    import importlib
    import logging
    import aiohttp
    from aiogram import Bot, Dispatcher
    from dotenv import load_dotenv
    from bot import config, oauth_server
    from bot.handlers import router
    from bot.storage import TokenStore

async def main() -> None:
    load_dotenv()
    importlib.reload(config)   # config read env at import time, before load_dotenv
    if not config.BOT_TOKEN: raise RuntimeError("BOT_TOKEN не задан в .env")
    bot = Bot(config.BOT_TOKEN)
    dp = Dispatcher(); dp.include_router(router)
    store = TokenStore()
    pending: dict = {}
    http = aiohttp.ClientSession()
    app = oauth_server.build_app(store=store, http=http, pending=pending, bot=bot)
    runner = await oauth_server.start(app)
    logging.info("segment=%s redirect_uri=%s", config.SEGMENT_ID, config.redirect_uri())
    try:
        # dependencies are injected into handlers by parameter name
        await dp.start_polling(bot, store=store, http=http, pending=pending)
    finally:
        await runner.cleanup()
        await http.close()
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
