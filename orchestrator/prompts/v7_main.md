Напиши целиком файл `bot/main.py` — ЛОКАЛЬНЫЙ запуск бота в polling-режиме
(для разработки на своей машине; на Vercel этот файл не используется).
Обновление: `pending` теперь `PendingStore` из bot.storage (а не пустой dict),
и перед polling нужно снять вебхук, чтобы не конфликтовал с getUpdates.

ОБЯЗАТЕЛЬНО: файл ДОЛЖЕН начинаться с блока импортов (все строки ниже), и только
ПОТОМ идёт `async def main()`. Не пропускай импорты.

Импорты: `import asyncio, importlib, logging`, `import aiohttp`,
`from aiogram import Bot, Dispatcher`, `from dotenv import load_dotenv`,
`from bot import config, oauth_server`, `from bot.handlers import router`,
`from bot.storage import TokenStore, PendingStore`.

```
async def main() -> None:
    load_dotenv()
    importlib.reload(config)   # config читает env при импорте, до load_dotenv
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в .env")
    bot = Bot(config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    store = TokenStore()
    pending = PendingStore()
    http = aiohttp.ClientSession()
    app = oauth_server.build_app(store=store, http=http, pending=pending, bot=bot)
    runner = await oauth_server.start(app)
    logging.info("segment=%s redirect_uri=%s", config.SEGMENT_ID, config.redirect_uri())
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        # зависимости инжектятся в хэндлеры по имени параметра
        await dp.start_polling(bot, store=store, http=http, pending=pending)
    finally:
        await runner.cleanup()
        await http.close()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

Выведи ТОЛЬКО код файла целиком в одном ```python блоке.
