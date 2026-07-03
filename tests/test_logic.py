# -*- coding: utf-8 -*-
from bot import logic

def test_start_text():
    text = logic.start_text()
    assert "Привет" in text
    assert "/help" in text

def test_help_text():
    text = logic.help_text()
    assert "/start" in text
    assert "/help" in text
    assert "эхо" in text.lower()

def test_echo_normal():
    assert logic.echo_text("hi") == "Ты написал: hi"

def test_echo_empty():
    assert logic.echo_text("") == "Пустое сообщение."

def test_echo_whitespace():
    assert logic.echo_text("   ") == "Пустое сообщение."

def test_keyboard():
    assert logic.keyboard() == [("Привет","btn:hello"),("Помощь","btn:help"),("О боте","btn:about")]

def test_button_hello():
    assert logic.on_button("btn:hello") == "Привет! Рад тебя видеть."

def test_button_help():
    assert logic.on_button("btn:help") == logic.help_text()

def test_button_about():
    assert logic.on_button("btn:about") == "Я тестовый бот. Собран локально на qwen3-coder."

def test_button_unknown():
    assert logic.on_button("btn:zzz") == "Неизвестная кнопка."
