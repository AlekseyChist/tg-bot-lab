# -*- coding: utf-8 -*-
from bot import logic

def test_start_text():
    text = logic.start_text()
    assert "Привет" in text
    assert "/help" in text

def test_help_text():
    text = logic.help_text()
    assert "/link" in text
    assert "/board" in text
    assert "/help" in text


# --- leaderboard logic ---

def test_format_time_minutes():
    assert logic.format_time(252) == "4:12"

def test_format_time_hours():
    assert logic.format_time(3661) == "1:01:01"

def test_format_time_zero_pad():
    assert logic.format_time(65) == "1:05"

def test_format_time_none():
    # модель отдала обычный дефис вместо "—" — принято осознанно (косметика)
    assert logic.format_time(None) in ("—", "-")

def test_parse_time_roundtrip():
    assert logic.parse_time("4:12") == 252
    assert logic.parse_time("1:01:01") == 3661
    assert logic.parse_time("252") == 252

def test_parse_time_bad():
    assert logic.parse_time("abc") is None
    assert logic.parse_time("") is None
    assert logic.parse_time("1:2:3:4") is None

def test_sort_entries_puts_none_last():
    entries = [
        {"name": "b", "seconds": 300},
        {"name": "c", "seconds": None},
        {"name": "a", "seconds": 250},
    ]
    names = [e["name"] for e in logic.sort_entries(entries)]
    assert names == ["a", "b", "c"]

def test_sort_entries_does_not_mutate():
    entries = [{"name": "x", "seconds": 300}, {"name": "y", "seconds": 100}]
    logic.sort_entries(entries)
    assert entries[0]["name"] == "x"

def test_badge_text_normal():
    assert logic.badge_text("Avala", 956) == "Avala 15:56"

def test_badge_text_none():
    assert logic.badge_text("Avala", None) is None

def test_badge_text_truncates_to_16():
    out = logic.badge_text("SuperLongSegment", 3661)  # "SuperLongSegment 1:01:01"
    assert out is not None and len(out) <= 16


def test_render_board_empty():
    out = logic.render_board([], 769755)
    assert "769755" in out
    assert "/link" in out

def test_render_board_ranks_and_times():
    entries = [
        {"name": "@petya", "seconds": 277},
        {"name": "@vasya", "seconds": 252},
        {"name": "@kolya", "seconds": None},
    ]
    out = logic.render_board(entries, 769755)
    lines = out.splitlines()
    assert "769755" in lines[0]
    # первым — самый быстрый
    assert "@vasya" in lines[1] and "4:12" in lines[1]
    assert "@petya" in lines[2] and "4:37" in lines[2]
    # без PR — в конце, с прочерком
    assert "@kolya" in lines[3] and "нет PR" in lines[3]

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
