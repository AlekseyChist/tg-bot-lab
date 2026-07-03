Напиши целиком файл `api/telegram.py` — serverless-функция Vercel (Python runtime),
принимающая вебхук Telegram. Формат Vercel: класс `handler(BaseHTTPRequestHandler)`.

В начале файла обеспечь импорт пакета `bot` (функция лежит в api/, а пакет — в корне репо):
```
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

Импорты:
`import json, asyncio`, `from http.server import BaseHTTPRequestHandler`, `import aiohttp`,
`from aiogram import Bot, Dispatcher`, `from aiogram.types import Update`,
`from bot import config`, `from bot.handlers import router`,
`from bot.storage import TokenStore, PendingStore`.

Корутина обработки одного апдейта (строим всё заново на каждый вызов — serverless):
```
async def _process(data: dict) -> None:
    bot = Bot(config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
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

Класс:
```
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if config.TELEGRAM_WEBHOOK_SECRET and secret != config.TELEGRAM_WEBHOOK_SECRET:
            self.send_response(403)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
            asyncio.run(_process(data))
        except Exception:
            import traceback
            traceback.print_exc()
        # Всегда 200 — чтобы Telegram не заваливал ретраями.
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ok")
```

Никакого dotenv (на Vercel переменные окружения заданы в проекте). Выведи ТОЛЬКО
код файла целиком в одном ```python блоке.
