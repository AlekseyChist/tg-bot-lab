from typing import List, Tuple

def start_text() -> str:
    return "Привет! Напиши /help чтобы увидеть доступные команды."

def help_text() -> str:
    return "Доступные команды:\n/start - начать\n/help - помощь\nЭхо: просто напиши что-нибудь"

def echo_text(text: str) -> str:
    if not text or text.isspace():
        return "Пустое сообщение."
    return "Ты написал: " + text

def keyboard() -> List[Tuple[str, str]]:
    return [("Привет", "btn:hello"), ("Помощь", "btn:help"), ("О боте", "btn:about")]

def on_button(data: str) -> str:
    if data == "btn:hello":
        return "Привет! Рад тебя видеть."
    elif data == "btn:help":
        return help_text()
    elif data == "btn:about":
        return "Я тестовый бот. Собран локально на qwen3-coder."
    else:
        return "Неизвестная кнопка."
