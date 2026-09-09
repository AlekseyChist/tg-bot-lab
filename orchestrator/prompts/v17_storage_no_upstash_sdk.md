Найден баг: пакет `upstash-redis` (`from upstash_redis.asyncio import Redis`) внутри
себя использует `httpx` с `anyio`-бэкендом для TCP-соединений, а в серверлесс-рантайме
Vercel (Python) это падает с `httpcore.ConnectError: [Errno 16] Device or resource busy`
при любой попытке достучаться до Upstash — то есть Redis вообще не работает в проде,
хотя переменные окружения (`UPSTASH_REDIS_REST_URL/TOKEN`) выставлены верно.
Остальной проект (Telegram Bot API, Strava API) успешно ходит в сеть через `aiohttp`
— значит именно `aiohttp` в этом рантайме работает нормально, а `httpx` — нет.

РЕШЕНИЕ: полностью убрать зависимость от пакета `upstash-redis` и его клиента,
и обращаться к Upstash REST API напрямую через `aiohttp` (тот же способ, что уже
используется в `bot/strava.py`).

Upstash REST API поддерживает выполнение ОДНОЙ команды через POST на базовый URL
с телом — JSON-массивом самой команды, и заголовком `Authorization: Bearer <token>`:
```
POST {UPSTASH_REDIS_REST_URL}
Authorization: Bearer {UPSTASH_REDIS_REST_TOKEN}
Content-Type: application/json
Body: ["HSET", "key", "field", "value"]
```
Ответ: JSON вида `{"result": ...}` (для HGETALL результат — плоский список
`["field1", "value1", "field2", "value2", ...]`, для отсутствующего ключа при GET/GETDEL —
`{"result": null}`).

Перепиши файл `bot/storage.py` ЦЕЛИКОМ. Структура и публичный интерфейс классов
`TokenStore` и `PendingStore` (сигнатуры методов, поведение файлового fallback,
формат данных) должны остаться ТЕ ЖЕ, что и сейчас — меняется ТОЛЬКО то, как
класс обращается к Redis (через `aiohttp` вместо пакета `upstash_redis`).

ТЕКУЩИЙ файл (для справки, что нужно сохранить 1:1 кроме Redis-части):

```python
import asyncio
import json
import os
from typing import Dict, Optional

from bot import config


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
            r = await self._redis()
            await r.hset("strava:tokens", str(tg_id), json.dumps(record, ensure_ascii=False))
        else:
            async with self._lock:
                data = self._load()
                data[str(tg_id)] = record
                self._save(data)

    async def get(self, tg_id: int) -> Optional[dict]:
        if self._use_redis:
            r = await self._redis()
            v = await r.hget("strava:tokens", str(tg_id))
            return json.loads(v) if v else None
        else:
            async with self._lock:
                data = self._load()
                return data.get(str(tg_id))

    async def delete(self, tg_id: int) -> bool:
        if self._use_redis:
            r = await self._redis()
            n = await r.hdel("strava:tokens", str(tg_id))
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
            r = await self._redis()
            raw = await r.hgetall("strava:tokens")
            return {k: json.loads(val) for k, val in (raw or {}).items()}
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
            json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        os.replace(tmp_path, self.path)

    async def _redis(self):
        from upstash_redis.asyncio import Redis
        return Redis(url=config.UPSTASH_REDIS_REST_URL, token=config.UPSTASH_REDIS_REST_TOKEN)


class PendingStore:
    _mem: Dict[str, dict] = {}

    def __init__(self):
        self._use_redis = config.use_redis()

    async def set(self, state: str, data: dict, ttl: int = 600) -> None:
        if self._use_redis:
            r = await self._redis()
            await r.set(f"pending:{state}", json.dumps(data, ensure_ascii=False), ex=ttl)
        else:
            self._mem[state] = data

    async def pop(self, state: str) -> Optional[dict]:
        if self._use_redis:
            r = await self._redis()
            v = await r.getdel(f"pending:{state}")
            return json.loads(v) if v else None
        else:
            return self._mem.pop(state, None)

    async def _redis(self):
        from upstash_redis.asyncio import Redis
        return Redis(url=config.UPSTASH_REDIS_REST_URL, token=config.UPSTASH_REDIS_REST_TOKEN)
```

Требуемые изменения:

1) В импортах добавь `import aiohttp` (вместо ленивого `from upstash_redis.asyncio import Redis`
   внутри `_redis()` — этого импорта и метода `_redis()` в обоих классах больше НЕ должно быть).

2) Добавь МОДУЛЬНУЮ (не метод класса) асинхронную функцию-хелпер:
```python
async def _upstash(cmd: list):
    headers = {"Authorization": f"Bearer {config.UPSTASH_REDIS_REST_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(config.UPSTASH_REDIS_REST_URL, json=cmd, headers=headers) as resp:
            data = await resp.json()
            return data.get("result")
```
   Раздели её от классов пустыми строками, размести СРАЗУ ПОСЛЕ импортов, ДО класса `TokenStore`.

3) В `TokenStore`:
   - `set`: вместо `r = await self._redis(); await r.hset(...)` — 
     `await _upstash(["HSET", "strava:tokens", str(tg_id), json.dumps(record, ensure_ascii=False)])`.
   - `get`: вместо `r.hget(...)` —
     `v = await _upstash(["HGET", "strava:tokens", str(tg_id)])`, затем та же логика
     `return json.loads(v) if v else None`.
   - `delete`: вместо `r.hdel(...)` —
     `n = await _upstash(["HDEL", "strava:tokens", str(tg_id)])`, затем `return bool(n)`.
   - `all`: вместо `r.hgetall(...)` (который в старом клиенте возвращал dict) —
     `raw = await _upstash(["HGETALL", "strava:tokens"])` возвращает ПЛОСКИЙ список
     `[field1, value1, field2, value2, ...]` (или `None`/`[]` если пусто). Собери словарь
     вручную:
     ```python
     result: Dict[str, dict] = {}
     if raw:
         for i in range(0, len(raw), 2):
             result[raw[i]] = json.loads(raw[i + 1])
     return result
     ```
   - Метод `_redis()` УДАЛИ полностью.
   - `_load`/`_save` и файловый fallback — БЕЗ изменений.

4) В `PendingStore`:
   - `set`: вместо `r = await self._redis(); await r.set(..., ex=ttl)` —
     `await _upstash(["SET", f"pending:{state}", json.dumps(data, ensure_ascii=False), "EX", str(ttl)])`.
   - `pop`: вместо `r = await self._redis(); v = await r.getdel(...)` —
     `v = await _upstash(["GETDEL", f"pending:{state}"])`, затем та же логика
     `return json.loads(v) if v else None`.
   - Метод `_redis()` УДАЛИ полностью.
   - `_mem`-fallback — БЕЗ изменений.

Выведи ТОЛЬКО итоговый код файла `bot/storage.py` целиком в одном ```python блоке.
