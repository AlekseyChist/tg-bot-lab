Напиши целиком файл `scripts/set_webhook.py` — одноразовая утилита, регистрирующая
(или удаляющая) вебхук Telegram, чтобы Telegram слал апдейты на Vercel-функцию.
Только стандартная библиотека + python-dotenv для чтения .env. НЕ использовать aiohttp.

Импорты: `import argparse, json, sys`, `from urllib import request, error`,
`import os`, `from dotenv import load_dotenv`.

Логика:
- `load_dotenv()` в начале main.
- Читать из окружения: `BOT_TOKEN`, `OAUTH_PUBLIC_BASE`, `TELEGRAM_WEBHOOK_SECRET`.
- Если нет `BOT_TOKEN` → печать ошибки в stderr и `return 2`.
- CLI: `argparse` с флагом `--delete` (action="store_true").

Помощник вызова Telegram API (стандартный urllib, POST form-urlencoded или JSON):
```
def _call(token: str, method: str, params: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(params).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))
```

main():
- собрать `token`, `base = OAUTH_PUBLIC_BASE.rstrip("/")`, `secret = TELEGRAM_WEBHOOK_SECRET`.
- если `args.delete`:
    `res = _call(token, "deleteWebhook", {"drop_pending_updates": False})`
  иначе:
    `hook_url = base + "/api/telegram"`
    `params = {"url": hook_url, "allowed_updates": ["message", "callback_query", "my_chat_member"]}`
    если secret: `params["secret_token"] = secret`
    `res = _call(token, "setWebhook", params)`
- напечатать `json.dumps(res, ensure_ascii=False, indent=2)`.
- дополнительно вызвать `getWebhookInfo` и тоже напечатать, чтобы видеть итоговое состояние:
    `info = _call(token, "getWebhookInfo", {})`; `print(json.dumps(info, ensure_ascii=False, indent=2))`
- вернуть 0 если `res.get("ok")` иначе 1.

В конце:
```
if __name__ == "__main__":
    raise SystemExit(main())
```

Выведи ТОЛЬКО код файла целиком в одном ```python блоке.
