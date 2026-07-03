Create `bot/handlers.py` for aiogram version 3.x (NOT 2.x). Follow the aiogram 3.x
API EXACTLY as shown below. Do not use `@dp.message_handler` (that is 2.x).

Use these exact imports and patterns:

    from aiogram import Router, F
    from aiogram.filters import Command, CommandStart
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    )
    from bot import logic

    router = Router()

Requirements:
1. A helper `_kb() -> InlineKeyboardMarkup` that builds an inline keyboard from
   `logic.keyboard()` (list of (label, callback_data)), one button per row:
       rows = [[InlineKeyboardButton(text=label, callback_data=data)]
               for label, data in logic.keyboard()]
       return InlineKeyboardMarkup(inline_keyboard=rows)

2. `@router.message(CommandStart())` -> async def cmd_start(message: Message) -> None:
   answers logic.start_text() with reply_markup=_kb()

3. `@router.message(Command("help"))` -> async def cmd_help(message: Message) -> None:
   answers logic.help_text()

4. `@router.callback_query(F.data.startswith("btn:"))` ->
   async def on_button(callback: CallbackQuery) -> None:
       await callback.message.answer(logic.on_button(callback.data))
       await callback.answer()

5. `@router.message(F.text)` -> async def echo(message: Message) -> None:
   answers logic.echo_text(message.text)

Every handler is `async` and uses `await message.answer(...)`.
Type hints on all functions. Output ONLY the module in one ```python block.
