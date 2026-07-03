Напиши целиком файл `bot/storage.py`. Асинхронное хранилище токенов и OAuth-state
с двумя бэкендами: файловый JSON (локалка/тесты) и Upstash Redis (Vercel).

Импорты: `import asyncio, json, os`, `from typing import Dict, Optional`, `from bot import config`.
НЕ импортируй upstash на уровне модуля — только лениво внутри методов Redis-ветки
(`from upstash_redis.asyncio import Redis`), чтобы файловый режим и тесты работали
без установленного пакета.

=== class TokenStore ===
Публичный async-интерфейс НЕ меняется (на него завязаны тесты):
`set(tg_id: int, record: dict) -> None`, `get(tg_id: int) -> Optional[dict]`,
`delete(tg_id: int) -> bool`, `all() -> Dict[str, dict]`.

Конструктор: `def __init__(self, path: str = None)`.
Выбор бэкенда:
- Если `path` передан ЯВНО (не None) → всегда файловый бэкенд по этому пути.
- Иначе если `config.use_redis()` → Redis-бэкенд.
- Иначе файловый бэкенд по `config.TOKENS_PATH`.
Запомни выбор в `self._use_redis: bool`. Для файлового режима сохрани `self.path`
и `self._lock = asyncio.Lock()`.

Файловый бэкенд — точно как раньше:
- `_load()`: если файла нет → `{}`; читать JSON; при `json.JSONDecodeError` → `{}`.
- `_save(data)`: `os.makedirs(os.path.dirname(self.path), exist_ok=True)`, писать во
  временный `f"{self.path}.tmp"` (`ensure_ascii=False, indent=2, separators=(',', ': ')`),
  затем `os.replace(tmp, self.path)`.
- `set/get/delete/all` под `async with self._lock`, ключи — `str(tg_id)`.
  `delete` возвращает True если ключ был, иначе False. `all()` возвращает весь dict.

Redis-бэкенд — один хэш с именем `"strava:tokens"`, поле = `str(tg_id)`, значение = JSON-строка record.
Клиент создавай лениво: приватный метод `_redis()` возвращает
`Redis(url=config.UPSTASH_REDIS_REST_URL, token=config.UPSTASH_REDIS_REST_TOKEN)`.
API upstash (async, всё await):
- `set`:  `await r.hset("strava:tokens", str(tg_id), json.dumps(record, ensure_ascii=False))`
- `get`:  `v = await r.hget("strava:tokens", str(tg_id))`; вернуть `json.loads(v)` если v, иначе None.
- `delete`: `n = await r.hdel("strava:tokens", str(tg_id))`; вернуть `bool(n)`.
- `all`:  `raw = await r.hgetall("strava:tokens")`; вернуть `{k: json.loads(val) for k, val in (raw or {}).items()}`.
  (hgetall возвращает dict полей→строк; значения парсь через json.loads.)

Внутри set/get/delete/all делай `if self._use_redis:` ветку Redis, `else:` файловую.

=== class PendingStore ===
Хранит временный OAuth-state между командой /link и callback'ом Strava.
Интерфейс:
- `async def set(self, state: str, data: dict, ttl: int = 600) -> None`
- `async def pop(self, state: str) -> Optional[dict]`  (вернуть данные и удалить; None если нет)

Конструктор `__init__(self)`: `self._use_redis = config.use_redis()`.
Для НЕ-redis режима держи process-local словарь: используй атрибут КЛАССА
`_mem: Dict[str, dict] = {}` (общий на процесс, чтобы разные экземпляры видели одно —
нужно для локального polling, где /link и callback в одном процессе).

Redis-бэкенд, ключ `f"pending:{state}"`:
- `set`: `await r.set(f"pending:{state}", json.dumps(data, ensure_ascii=False), ex=ttl)`
- `pop`: `v = await r.getdel(f"pending:{state}")`; вернуть `json.loads(v)` если v, иначе None.
Клиент — тем же способом (`Redis(url=..., token=...)`).

Не-redis `set`: `PendingStore._mem[state] = data` (ttl игнорируй).
Не-redis `pop`: `PendingStore._mem.pop(state, None)`.

Выведи ТОЛЬКО код файла целиком в одном ```python блоке.
