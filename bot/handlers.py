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

router = Router()
log = logging.getLogger(__name__)

async def _autodelete(msg: Message, delay: int = 5) -> None:
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

def _display_name(msg: Message) -> str:
    u = msg.from_user
    if u.username:
        return "@" + u.username
    else:
        return u.full_name

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(logic.start_text() + "\n\n" + logic.help_text())

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(logic.help_text())

@router.message(Command("link"))
async def cmd_link(message: Message, pending: dict) -> None:
    if not config.STRAVA_CLIENT_ID:
        await message.answer("Приложение Strava не настроено.")
        return
    state = secrets.token_urlsafe(16)
    pending[state] = {"tg_id": message.from_user.id, "name": _display_name(message),
                      "chat_id": message.chat.id}
    url = strava.authorize_url(state)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Привязать Strava", url=url)]])
    try:
        await message.delete()
    except Exception:
        pass
    prompt = await message.answer(
        f"Нажми кнопку и разреши доступ. Возьмём только твой результат на сегменте {config.SEGMENT_ID}.",
        reply_markup=kb,
    )
    pending[state]["prompt_message_id"] = prompt.message_id
    asyncio.create_task(_autodelete(prompt, 120))

@router.message(Command("unlink"))
async def cmd_unlink(message: Message, store: TokenStore) -> None:
    removed = await store.delete(message.from_user.id)
    await message.answer("Strava отвязана." if removed else "У тебя нет привязки.")

@router.message(Command("board"))
async def cmd_board(message: Message, store: TokenStore, http: aiohttp.ClientSession) -> None:
    users = await store.all()
    if not users:
        await message.answer(logic.render_board([], config.SEGMENT_ID))
        return
    placeholder = await message.answer("⏳ Считаю времена…")
    async def one(tg_id_str: str, record: dict) -> dict:
        token = await strava.valid_access_token(http, store, int(tg_id_str), record)
        seconds = None
        if token:
            seconds = await strava.segment_pr_seconds(http, token, config.SEGMENT_ID)
        return {"name": record.get("name", "?"), "seconds": seconds}
    entries = await asyncio.gather(*(one(k, v) for k, v in users.items()))
    board = logic.render_board(list(entries), config.SEGMENT_ID)
    await placeholder.edit_text(f"<pre>{html.escape(board)}</pre>", parse_mode="HTML")

@router.message(Command("badges"))
async def cmd_badges(message: Message, store: TokenStore, http: aiohttp.ClientSession) -> None:
    if message.chat.type != "supergroup":
        await message.answer("Работает только в супергруппе. Сделай бота админом с правом «Назначать администраторов» — обычная группа станет супергруппой сама.")
        return
    users = await store.all()
    if not users:
        await message.answer("Пока никто не привязал Strava. /link")
        return
    bot = message.bot
    chat_id = message.chat.id
    results = []
    for tg_id_str, record in users.items():
        tg_id = int(tg_id_str)
        name = record.get("name", "?")
        token = await strava.valid_access_token(http, store, tg_id, record)
        seconds = await strava.segment_pr_seconds(http, token, config.SEGMENT_ID) if token else None
        badge = logic.badge_text(config.SEGMENT_NAME, seconds)
        if badge is None:
            results.append(f"{name}: нет PR")
            continue
        try:
            await bot.promote_chat_member(chat_id, tg_id, is_anonymous=False,
                can_manage_chat=False, can_change_info=False, can_delete_messages=False,
                can_invite_users=True, can_restrict_members=False, can_pin_messages=False,
                can_promote_members=False, can_manage_video_chats=False)
            await bot.set_chat_administrator_custom_title(chat_id, tg_id, badge)
            results.append(f"{name}: {badge}")
        except Exception as e:
            results.append(f"{name}: ошибка ({e})")
    log.info("badges: %s", "; ".join(results))
    try:
        await message.delete()
    except Exception:
        pass
    m = await message.answer("✅ Бейджи обновлены")
    asyncio.create_task(_autodelete(m, 5))

@router.message(F.new_chat_members | F.left_chat_member | F.pinned_message
                | F.new_chat_title | F.new_chat_photo | F.delete_chat_photo)
async def clean_service(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass
