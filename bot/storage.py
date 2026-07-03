import asyncio
import json
import os
from typing import Dict, Optional
from bot import config

class TokenStore:
    def __init__(self, path: str = None):
        self.path = path or config.TOKENS_PATH
        self._lock = asyncio.Lock()

    def _load(self) -> Dict[str, dict]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save(self, data) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        os.replace(tmp_path, self.path)

    async def set(self, tg_id: int, record: dict) -> None:
        async with self._lock:
            data = self._load()
            data[str(tg_id)] = record
            self._save(data)

    async def get(self, tg_id: int) -> Optional[dict]:
        async with self._lock:
            data = self._load()
            return data.get(str(tg_id))

    async def delete(self, tg_id: int) -> bool:
        async with self._lock:
            data = self._load()
            if str(tg_id) in data:
                data.pop(str(tg_id))
                self._save(data)
                return True
            return False

    async def all(self) -> Dict[str, dict]:
        async with self._lock:
            return self._load()
