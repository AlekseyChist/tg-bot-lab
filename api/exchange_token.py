import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import aiohttp
from aiogram import Bot
from bot import config, oauth_server
from bot.storage import TokenStore, PendingStore

async def _run(query: dict) -> tuple:
    bot = Bot(config.BOT_TOKEN)
    store = TokenStore()
    pending = PendingStore()
    http = aiohttp.ClientSession()
    try:
        return await oauth_server.process_exchange(query, store=store, http=http, pending=pending, bot=bot)
    finally:
        await http.close()
        await bot.session.close()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = parse_qs(urlparse(self.path).query)
        query = {k: v[0] for k, v in parsed.items()}
        try:
            title, body = asyncio.run(_run(query))
        except Exception as e:
            import traceback
            traceback.print_exc()
            title, body = "Ошибка", str(e)
        page = oauth_server.render_page_html(title, body)
        payload = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
