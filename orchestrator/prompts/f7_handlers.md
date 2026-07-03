Write `bot/handlers.py`: thin aiogram 3.x handlers. Type hints. aiogram 3 syntax
only (Router, filters), no aiogram 2.x legacy.

Imports:
    import asyncio
    import html
    import logging
    import secrets
    import aiohttp
    from aiogram import Router, F
    from aiogram.filters import Command, CommandStart
    from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
    from bot import config, logic, strava
    from bot.storage import TokenStore

module: router = Router()
module: log = logging.getLogger(__name__)

Helper coroutine for auto-deleting a bot message after a delay:
    async def _autodelete(msg: Message, delay: int = 5) -> None:
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except Exception:
            pass

def _display_name(msg: Message) -> str:
    u = msg.from_user; if u.username return "@" + u.username else return u.full_name.

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    answer logic.start_text() + "\n\n" + logic.help_text().

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    answer logic.help_text().

@router.message(Command("link"))
async def cmd_link(message: Message, pending: dict) -> None:
    if not config.STRAVA_CLIENT_ID: answer that Strava app is not configured; return.
    state = secrets.token_urlsafe(16)
    pending[state] = {"tg_id": message.from_user.id, "name": _display_name(message),
                      "chat_id": message.chat.id}
    url = strava.authorize_url(state)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Привязать Strava", url=url)]])
    # убрать саму команду /link из чата:
    try: await message.delete() except Exception: pass
    # отправить сообщение с кнопкой и ЗАПОМНИТЬ его id, чтобы удалить после привязки:
    prompt = await message.answer(
        f"Нажми кнопку и разреши доступ. Возьмём только твой результат на сегменте {config.SEGMENT_ID}.",
        reply_markup=kb,
    )
    pending[state]["prompt_message_id"] = prompt.message_id
    # страховка: если человек так и не нажмёт — снять кнопку через 120с
    asyncio.create_task(_autodelete(prompt, 120))
    IMPORTANT: the keyboard goes ONLY in the reply_markup argument. NEVER put the
    keyboard object inside the text string (no f"{kb}"). Note pending[state] was
    already created above with tg_id/name/chat_id; here we just add prompt_message_id.

@router.message(Command("unlink"))
async def cmd_unlink(message: Message, store: TokenStore) -> None:
    removed = await store.delete(message.from_user.id)
    answer "Strava отвязана." if removed else "У тебя нет привязки."

@router.message(Command("board"))
async def cmd_board(message: Message, store: TokenStore, http: aiohttp.ClientSession) -> None:
    users = await store.all()
    if not users: answer logic.render_board([], config.SEGMENT_ID); return
    placeholder = await message.answer("⏳ Считаю времена…")
    define inner: async def one(tg_id_str: str, record: dict) -> dict:
        token = await strava.valid_access_token(http, store, int(tg_id_str), record)
        seconds = None; if token: seconds = await strava.segment_pr_seconds(http, token, config.SEGMENT_ID)
        return {"name": record.get("name", "?"), "seconds": seconds}
    entries = await asyncio.gather(*(one(k, v) for k, v in users.items()))
    board = logic.render_board(list(entries), config.SEGMENT_ID)
    await placeholder.edit_text(f"<pre>{html.escape(board)}</pre>", parse_mode="HTML")

@router.message(Command("badges"))
async def cmd_badges(message: Message, store: TokenStore, http: aiohttp.ClientSession) -> None:
    Set each linked member's Strava time as their admin custom-title badge next to
    their name. Works ONLY in a supergroup.
    - if message.chat.type != "supergroup":
        await message.answer("Работает только в супергруппе. Сделай бота админом с правом «Назначать администраторов» — обычная группа станет супергруппой сама.")
        return
    - users = await store.all()
    - if not users: await message.answer("Пока никто не привязал Strava. /link"); return
    - bot = message.bot ; chat_id = message.chat.id ; results = []  (list of str)
    - for tg_id_str, record in users.items():
        tg_id = int(tg_id_str) ; name = record.get("name", "?")
        token = await strava.valid_access_token(http, store, tg_id, record)
        seconds = await strava.segment_pr_seconds(http, token, config.SEGMENT_ID) if token else None
        badge = logic.badge_text(config.SEGMENT_NAME, seconds)
        if badge is None:
            results.append(f"{name}: нет PR"); continue
        try:
            # делаем «почти пустым» админом: всё False, кроме can_invite_users,
            # иначе Telegram снимает админку и title поставить нельзя.
            await bot.promote_chat_member(chat_id, tg_id, is_anonymous=False,
                can_manage_chat=False, can_change_info=False, can_delete_messages=False,
                can_invite_users=True, can_restrict_members=False, can_pin_messages=False,
                can_promote_members=False, can_manage_video_chats=False)
            await bot.set_chat_administrator_custom_title(chat_id, tg_id, badge)
            results.append(f"{name}: {badge}")
        except Exception as e:
            results.append(f"{name}: ошибка ({e})")
    - # полный отчёт — только в лог сервера, НЕ в чат:
      log.info("badges: %s", "; ".join(results))
    - # убрать саму команду /badges из чата:
      try: await message.delete() except Exception: pass
    - # короткое подтверждение, самоудаляется через 5с:
      m = await message.answer("✅ Бейджи обновлены")
      asyncio.create_task(_autodelete(m, 5))

Service-message cleaner — keep the chat free of "вошёл/вышел/закрепил" spam:
@router.message(F.new_chat_members | F.left_chat_member | F.pinned_message
                | F.new_chat_title | F.new_chat_photo | F.delete_chat_photo)
async def clean_service(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass
IMPORTANT: this handler must be registered AFTER all the command handlers, and it
only matches those service-message fields — it must NOT touch normal text messages.

Do NOT add an echo handler and do NOT add any callback_query handler.
