import argparse
import json
import sys
from urllib import request, error
import os
from dotenv import load_dotenv

def _call(token: str, method: str, params: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(params).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))

def main():
    load_dotenv()
    
    token = os.environ.get("BOT_TOKEN")
    base = os.environ.get("OAUTH_PUBLIC_BASE", "").rstrip("/")
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    
    if not token:
        print("Error: BOT_TOKEN is not set", file=sys.stderr)
        return 2
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()
    
    if args.delete:
        res = _call(token, "deleteWebhook", {"drop_pending_updates": False})
    else:
        hook_url = base + "/api/telegram"
        params = {
            "url": hook_url,
            "allowed_updates": ["message", "callback_query", "my_chat_member"]
        }
        if secret:
            params["secret_token"] = secret
        res = _call(token, "setWebhook", params)
    
    print(json.dumps(res, ensure_ascii=False, indent=2))
    
    info = _call(token, "getWebhookInfo", {})
    print(json.dumps(info, ensure_ascii=False, indent=2))
    
    return 0 if res.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
