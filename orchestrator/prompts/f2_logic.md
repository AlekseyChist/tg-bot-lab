Write a Python module `bot/logic.py`. PURE functions only — no imports from
telegram/aiogram/strava, no I/O. Use type hints. Keep it exactly to this spec.

Imports: `from typing import List, Optional, Tuple`

Functions:

1) start_text() -> str
   Return a greeting string that contains the substring "Привет" and "/help".

2) help_text() -> str
   Return a multiline string listing commands. MUST contain the substrings
   "/link", "/board", "/help".

3) echo_text(text: str) -> str
   If text is empty or only whitespace -> return "Пустое сообщение."
   Otherwise return "Ты написал: " + text

4) keyboard() -> List[Tuple[str, str]]
   Return exactly:
   [("Привет", "btn:hello"), ("Помощь", "btn:help"), ("О боте", "btn:about")]

5) on_button(data: str) -> str
   "btn:hello" -> "Привет! Рад тебя видеть."
   "btn:help"  -> help_text()
   "btn:about" -> "Я тестовый бот. Собран локально на qwen3-coder."
   anything else -> "Неизвестная кнопка."

6) format_time(seconds: Optional[int]) -> str
   None or negative -> "—"
   Else format seconds as "M:SS", or "H:MM:SS" when there are whole hours.
   Examples: 252 -> "4:12" ; 65 -> "1:05" ; 3661 -> "1:01:01"

7) parse_time(text: str) -> Optional[int]
   Parse "M:SS" / "H:MM:SS" / plain seconds into total seconds.
   "4:12" -> 252 ; "1:01:01" -> 3661 ; "252" -> 252
   Return None for empty string, non-digit parts, or more than 3 colon-parts.

8) sort_entries(entries: List[dict]) -> List[dict]
   Each entry is {"name": str, "seconds": int | None}.
   Return a NEW sorted list (do not mutate input): by seconds ascending;
   entries whose seconds is None go LAST.

9) render_board(entries: List[dict], segment_id: int) -> str
   Header line: f"🏆 Сегмент {segment_id} — таблица времён"
   If entries is empty: return header + "\n" + a hint containing "/link".
   Else: sort with sort_entries, pad names to equal width with ljust, and
   build lines. Ranked entries (with a time) start at 1:
     f"{rank:>2}. {name}  {format_time(sec)}"
   Entries without a PR (seconds is None) get no rank and the text "нет PR",
   placed after ranked ones. Join all lines with "\n".

10) badge_text(segment_name: str, seconds: Optional[int], max_len: int = 16) -> Optional[str]
    Build the short admin-title badge shown next to a member's name.
    If seconds is None -> return None (no PR means no badge).
    Otherwise text = f"{segment_name} {format_time(seconds)}".
    If len(text) > max_len -> return text[:max_len] (Telegram custom_title cap).
    Else return text.
    Example: badge_text("Avala", 956) -> "Avala 15:56"
