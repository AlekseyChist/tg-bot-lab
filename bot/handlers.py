from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)
from bot import logic

router = Router()

def _kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=data)]
            for label, data in logic.keyboard()]
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(logic.start_text(), reply_markup=_kb())

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(logic.help_text())

@router.callback_query(F.data.startswith("btn:"))
async def on_button(callback: CallbackQuery) -> None:
    await callback.message.answer(logic.on_button(callback.data))
    await callback.answer()

@router.message(F.text)
async def echo(message: Message) -> None:
    await message.answer(logic.echo_text(message.text))
