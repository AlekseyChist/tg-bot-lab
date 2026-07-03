Write a Python module `bot/storage.py`: a small async JSON store mapping a
Telegram user id to their Strava token record. Use type hints.

Imports:
    import asyncio
    import json
    import os
    from typing import Dict, Optional
    from bot import config

Class TokenStore:
  __init__(self, path: str = None): store self.path = path or config.TOKENS_PATH ;
      create an asyncio.Lock() as self._lock.

  Private sync helpers (NOT async):
    _load(self) -> Dict[str, dict]:
        if the file does not exist -> return {} .
        Otherwise open it utf-8 and json.load; if json is broken (JSONDecodeError)
        return {} instead of raising.
    _save(self, data) -> None:
        make sure the parent directory exists (os.makedirs(..., exist_ok=True));
        write to a temp file "<path>.tmp" then os.replace it onto self.path
        (atomic). Use ensure_ascii=False, indent=2, newline="\n".

  Async methods — EACH must take `async with self._lock:` around its body:
    async set(self, tg_id: int, record: dict) -> None:
        load, set data[str(tg_id)] = record, save.
    async get(self, tg_id: int) -> Optional[dict]:
        load and return data.get(str(tg_id)).
    async delete(self, tg_id: int) -> bool:
        load, pop str(tg_id); if it existed -> save and return True, else False.
    async all(self) -> Dict[str, dict]:
        load and return the whole dict.

Keys in the JSON file are the string form of tg_id.
