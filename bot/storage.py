import asyncio
import json
import os
from typing import Dict, Optional

import aiohttp

from bot import config


async def _upstash(cmd: list):
    headers = {"Authorization": f"Bearer {config.UPSTASH_REDIS_REST_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            config.UPSTASH_REDIS_REST_URL, json=cmd, headers=headers
        ) as resp:
            data = await resp.json()
            return data.get("result")


class TokenStore:
    def __init__(self, path: str = None):
        if path is not None:
            self._use_redis = False
            self.path = path
            self._lock = asyncio.Lock()
        elif config.use_redis():
            self._use_redis = True
        else:
            self._use_redis = False
            self.path = config.TOKENS_PATH
            self._lock = asyncio.Lock()

    async def set(self, tg_id: int, record: dict) -> None:
        if self._use_redis:
            await _upstash(
                [
                    "HSET",
                    "strava:tokens",
                    str(tg_id),
                    json.dumps(record, ensure_ascii=False),
                ]
            )
        else:
            async with self._lock:
                data = self._load()
                data[str(tg_id)] = record
                self._save(data)

    async def get(self, tg_id: int) -> Optional[dict]:
        if self._use_redis:
            v = await _upstash(
                ["HGET", "strava:tokens", str(tg_id)]
            )
            return json.loads(v) if v else None
        else:
            async with self._lock:
                data = self._load()
                return data.get(str(tg_id))

    async def delete(self, tg_id: int) -> bool:
        if self._use_redis:
            n = await _upstash(
                ["HDEL", "strava:tokens", str(tg_id)]
            )
            return bool(n)
        else:
            async with self._lock:
                data = self._load()
                if str(tg_id) in data:
                    del data[str(tg_id)]
                    self._save(data)
                    return True
                return False

    async def all(self) -> Dict[str, dict]:
        if self._use_redis:
            raw = await _upstash(["HGETALL", "strava:tokens"])
            result: Dict[str, dict] = {}
            if raw:
                for i in range(0, len(raw), 2):
                    result[raw[i]] = json.loads(raw[i + 1])
            return result
        else:
            async with self._lock:
                return self._load()

    def _load(self) -> Dict[str, dict]:
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data: Dict[str, dict]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, separators=(",", ": "))
        os.replace(tmp_path, self.path)


class PendingStore:
    _mem: Dict[str, dict] = {}

    def __init__(self):
        self._use_redis = config.use_redis()

    async def set(self, state: str, data: dict, ttl: int = 600) -> None:
        if self._use_redis:
            await _upstash(
                [
                    "SET",
                    f"pending:{state}",
                    json.dumps(data, ensure_ascii=False),
                    "EX",
                    str(ttl),
                ]
            )
        else:
            self._mem[state] = data

    async def pop(self, state: str) -> Optional[dict]:
        if self._use_redis:
            v = await _upstash(["GETDEL", f"pending:{state}"])
            return json.loads(v) if v else None
        else:
            return self._mem.pop(state, None)
