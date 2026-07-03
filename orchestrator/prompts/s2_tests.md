Create a pytest test module `tests/test_logic.py` for a module `bot.logic`.

The module under test has these functions:
  start_text() -> str
  help_text() -> str
  echo_text(text: str) -> str
  keyboard() -> list[tuple[str, str]]
  on_button(data: str) -> str

Write tests asserting EXACTLY these behaviors:

- test_start_text: "Привет" in start_text(); "/help" in start_text()
- test_help_text: "/start" in help_text(); "/help" in help_text();
  "эхо" in help_text().lower()   # case-insensitive on purpose
- test_echo_normal: echo_text("hi") == "Ты написал: hi"
- test_echo_empty: echo_text("") == "Пустое сообщение."
- test_echo_whitespace: echo_text("   ") == "Пустое сообщение."
- test_keyboard: keyboard() == [("Привет","btn:hello"),("Помощь","btn:help"),("О боте","btn:about")]
- test_button_hello: on_button("btn:hello") == "Привет! Рад тебя видеть."
- test_button_help: on_button("btn:help") == help_text()
- test_button_about: on_button("btn:about") == "Я тестовый бот. Собран локально на qwen3-coder."
- test_button_unknown: on_button("btn:zzz") == "Неизвестная кнопка."

Import with `from bot import logic`. Use plain `assert`. No fixtures needed.
The file must start with a UTF-8 friendly module (Russian strings are used).
Output ONLY the test module in a single ```python block.
