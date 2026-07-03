Create a Python module `bot/logic.py` with PURE functions only.
Do NOT import aiogram, telegram, or anything network-related. Stdlib only.

Implement EXACTLY these functions with these EXACT contracts (Russian reply texts):

1. start_text() -> str
   Return a welcome message. Must contain the words "Привет" and "/help".

2. help_text() -> str
   Return a help message listing commands. Must contain the substrings
   "/start" and "/help" and "эхо".

3. echo_text(text: str) -> str
   Return the string:  "Ты написал: " + text
   If text is empty or only whitespace, return exactly: "Пустое сообщение."

4. keyboard() -> list[tuple[str, str]]
   Return a fixed list of (label, callback_data) pairs, EXACTLY:
   [("Привет", "btn:hello"), ("Помощь", "btn:help"), ("О боте", "btn:about")]

5. on_button(data: str) -> str
   Map callback_data to a reply:
     "btn:hello" -> "Привет! Рад тебя видеть."
     "btn:help"  -> help_text()
     "btn:about" -> "Я тестовый бот. Собран локально на qwen3-coder."
   For any other value return: "Неизвестная кнопка."

Requirements: type hints on every function. No global side effects, no prints.
Output ONLY the module code in a single ```python block.
