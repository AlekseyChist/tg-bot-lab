Напиши целиком файл `bot/handlers.py` — команды aiogram 3.x для Strava-сегмент-бота.
Это ОБНОВЛЕНИЕ существующего файла: логика та же, меняется ТОЛЬКО тип зависимости
`pending` — теперь это объект `PendingStore` (из bot.storage) с async-методами, а не
обычный dict.

ОБЯЗАТЕЛЬНО начни файл со ВСЕХ импортов ниже (не пропусти `import aiohttp` — он
нужен для аннотаций `aiohttp.ClientSession`, файл БЕЗ `from __future__ import annotations`).

Импорты (все, каждый строкой): `import asyncio`, `import html`, `import logging`,
`import secrets`, `import aiohttp`,
`from aiogram import Router, F`,
`from aiogram.filters import Command, CommandStart`,
`from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton`,
`from bot import config, logic, strava`,
`from bot.storage import TokenStore, PendingStore`.

`router = Router()`, `log = logging.getLogger(__name__)`.

Вспомогательные (без изменений):
- `async def _autodelete(msg: Message, delay: int = 5) -> None`: `await asyncio.sleep(delay)`,
  затем `try: await msg.delete() except Exception: pass`.
- `def _display_name(msg: Message) -> str`: если `msg.from_user.username` → `"@"+username`,
  иначе `msg.from_user.full_name`.

Зависимости в хэндлеры aiogram инжектит ПО ИМЕНИ параметра: `store: TokenStore`,
`http: aiohttp.ClientSession`, `pending: PendingStore`.

Хэндлеры:

1) `@router.message(CommandStart())` `cmd_start(message)`:
   `await message.answer(logic.start_text() + "\n\n" + logic.help_text())`

2) `@router.message(Command("help"))` `cmd_help(message)`:
   `await message.answer(logic.help_text())`

3) `@router.message(Command("link"))` `cmd_link(message: Message, pending: PendingStore)`:
   ЦЕЛЬ ИЗМЕНЕНИЯ: в группе каждый должен получать СВОЮ ссылку в ЛИЧКУ, чтобы люди
   не тыкали в чужую кнопку. В личном чате — поведение как раньше.
   - если не `config.STRAVA_CLIENT_ID` → `await message.answer("Приложение Strava не настроено.")`, return.
   - `state = secrets.token_urlsafe(16)`
   - `name = _display_name(message)`
   - `url = strava.authorize_url(state)`
   - `kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Привязать Strava", url=url)]])`
   - `text = f"Нажми кнопку и разреши доступ. Возьмём только твой результат на сегменте {config.SEGMENT_ID}."`
   - `pend = {"tg_id": message.from_user.id, "name": name}`
   - Если чат приватный (`message.chat.type == "private"`):
       - `prompt = await message.answer(text, reply_markup=kb)`
       - `pend["chat_id"] = message.chat.id`
   - Иначе (группа/супергруппа) — отправляем кнопку в ЛС пользователю:
       - в `try` попытаться: `prompt = await message.bot.send_message(message.from_user.id, text, reply_markup=kb)`
       - `except Exception:` (бот не может писать в ЛС — юзер не нажимал Start):
           - `me = await message.bot.me()`
           - `start_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🤖 Открыть бота", url=f"https://t.me/{me.username}?start=link")]])`
           - `warn = await message.answer(f"{name}, чтобы привязать Strava — открой меня в личке (кнопка ниже), нажми Start и отправь /link там.", reply_markup=start_kb)`
           - `asyncio.create_task(_autodelete(warn, 30))`
           - `try: await message.delete() except Exception: pass`
           - `return`
       - `pend["chat_id"] = message.from_user.id`  (чат для колбэка — личка)
       - удалить исходную команду в группе: `try: await message.delete() except Exception: pass`
       - краткое уведомление в группе: `note = await message.answer(f"📩 {name}, отправил тебе ссылку в личку.")` и `asyncio.create_task(_autodelete(note, 8))`
   - Общий хвост (для обоих веток, где `prompt` создан):
       - `pend["prompt_message_id"] = prompt.message_id`
       - `await pending.set(state, pend, ttl=600)`
       - `asyncio.create_task(_autodelete(prompt, 120))`

4) `@router.message(Command("unlink"))` `cmd_unlink(message, store: TokenStore)`:
   `removed = await store.delete(message.from_user.id)`;
   `await message.answer("Strava отвязана." if removed else "У тебя нет привязки.")`

5) `@router.message(Command("board"))` `cmd_board(message, store: TokenStore, http: aiohttp.ClientSession)`:
   - `users = await store.all()`
   - если пусто → `await message.answer(logic.render_board([], config.SEGMENT_ID))`, return.
   - `placeholder = await message.answer("⏳ Считаю времена…")`
   - вложенная `async def one(tg_id_str, record)`:
       `token = await strava.valid_access_token(http, store, int(tg_id_str), record)`;
       `seconds = await strava.segment_pr_seconds(http, token, config.SEGMENT_ID) if token else None`;
       вернуть `{"name": record.get("name", "?"), "seconds": seconds}`
   - `entries = await asyncio.gather(*(one(k, v) for k, v in users.items()))`
   - `board = logic.render_board(list(entries), config.SEGMENT_ID)`
   - `await placeholder.edit_text(f"<pre>{html.escape(board)}</pre>", parse_mode="HTML")`

6) `@router.message(Command("badges"))` `cmd_badges(message, store: TokenStore, http: aiohttp.ClientSession)`:
   - если `message.chat.type != "supergroup"` → `await message.answer("Работает только в супергруппе. Сделай бота админом с правом «Назначать администраторов» — обычная группа станет супергруппой сама.")`, return.
   - `users = await store.all()`; если пусто → `await message.answer("Пока никто не привязал Strava. /link")`, return.
   - `bot = message.bot`, `chat_id = message.chat.id`, `results = []`
   - для каждого `tg_id_str, record` в `users.items()`:
       `tg_id = int(tg_id_str)`, `name = record.get("name", "?")`,
       `token = await strava.valid_access_token(http, store, tg_id, record)`,
       `seconds = await strava.segment_pr_seconds(http, token, config.SEGMENT_ID) if token else None`,
       `badge = logic.badge_text(config.SEGMENT_NAME, seconds)`,
       если `badge is None` → `results.append(f"{name}: нет PR")`, continue.
       try:
         `await bot.promote_chat_member(chat_id, tg_id, is_anonymous=False, can_manage_chat=False, can_change_info=False, can_delete_messages=False, can_invite_users=True, can_restrict_members=False, can_pin_messages=False, can_promote_members=False, can_manage_video_chats=False)`
         `await bot.set_chat_administrator_custom_title(chat_id, tg_id, badge)`
         `results.append(f"{name}: {badge}")`
       except Exception as e: `results.append(f"{name}: ошибка ({e})")`
   - `log.info("badges: %s", "; ".join(results))`
   - `try: await message.delete() except Exception: pass`
   - `m = await message.answer("✅ Бейджи обновлены")`; `asyncio.create_task(_autodelete(m, 5))`

7) `@router.message(F.new_chat_members | F.left_chat_member | F.pinned_message | F.new_chat_title | F.new_chat_photo | F.delete_chat_photo)` `clean_service(message)`:
   `try: await message.delete() except Exception: pass`

Выведи ТОЛЬКО код файла целиком в одном ```python блоке.
