В файле `bot/logic.py` есть функция `help_text()`. Сейчас она перечисляет не все
команды бота. Обнови ТОЛЬКО эту функцию (весь остальной файл `bot/logic.py`
оставь БЕЗ ИЗМЕНЕНИЙ — ни одной другой строки).

Полный список команд бота (взято из `bot/handlers.py`):
- `/link` — привязать Strava аккаунт (в группе бот шлёт ссылку в личку)
- `/unlink` — отвязать свой Strava-аккаунт (с отзывом токена на стороне Strava)
- `/board` — показать таблицу результатов (личные рекорды на сегменте)
- `/badges` — обновить бейджи (кастомные титулы) участников с их временем;
  работает только в супергруппе
- `/revoke_all` — отозвать и удалить ВСЕ привязки Strava; только для администратора
- `/help` — показать список команд

БЫЛО:
```python
def help_text() -> str:
    return """Доступные команды:
/link — привязать Strava аккаунт
/board — показать таблицу результатов
/help — показать эту справку"""
```

СТАЛО (сохрани именно такой стиль — тройные кавычки, без экранирования,
одна команда на строку, тире после команды через пробел):
```python
def help_text() -> str:
    return """Доступные команды:
/link — привязать Strava аккаунт
/unlink — отвязать свой Strava-аккаунт
/board — показать таблицу результатов
/badges — обновить бейджи участников (только в супергруппе)
/revoke_all — отозвать все привязки (только для администратора)
/help — показать эту справку"""
```

ПОЛНЫЙ ТЕКУЩИЙ ФАЙЛ `bot/logic.py` (за основу — измени только тело `help_text()`,
всё остальное скопируй буквально как есть, посимвольно, включая пустые строки):

```python
from typing import List, Optional, Tuple

def start_text() -> str:
    return "Привет! Напиши /help для списка команд."

def help_text() -> str:
    return """Доступные команды:
/link — привязать Strava аккаунт
/board — показать таблицу результатов
/help — показать эту справку"""

def echo_text(text: str) -> str:
    if not text or text.isspace():
        return "Пустое сообщение."
    return f"Ты написал: {text}"

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

def format_time(seconds: Optional[int]) -> str:
    if seconds is None or seconds < 0:
        return "—"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def parse_time(text: str) -> Optional[int]:
    if not text:
        return None
    
    parts = text.split(":")
    
    if len(parts) > 3:
        return None
    
    try:
        if len(parts) == 1:
            return int(parts[0])
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:  # 3 parts
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return None

def sort_entries(entries: List[dict]) -> List[dict]:
    def sort_key(entry):
        sec = entry["seconds"]
        return (sec is None, sec if sec is not None else float('inf'))
    
    return sorted(entries, key=sort_key)

def render_board(entries: List[dict], segment_id: int) -> str:
    header = f"🏆 Сегмент {segment_id} — таблица времён"
    
    if not entries:
        return f"{header}\nНет данных. Напиши /link чтобы начать."
    
    sorted_entries = sort_entries(entries)
    
    # Find max name length for padding
    max_name_len = max(len(entry["name"]) for entry in sorted_entries)
    
    lines = [header]
    rank = 1
    
    for entry in sorted_entries:
        name = entry["name"]
        sec = entry["seconds"]
        
        if sec is not None:
            lines.append(f"{rank:>2}. {name:<{max_name_len}}  {format_time(sec)}")
            rank += 1
        else:
            lines.append(f"   {name:<{max_name_len}}  нет PR")
    
    return "\n".join(lines)

def badge_text(segment_name: str, seconds: Optional[int], max_len: int = 16) -> Optional[str]:
    if seconds is None:
        return None
    
    text = f"{segment_name} {format_time(seconds)}"
    
    if len(text) > max_len:
        return text[:max_len]
    
    return text
```

Выведи ТОЛЬКО итоговый код ВСЕГО файла `bot/logic.py` целиком в одном ```python
блоке (со всеми остальными функциями без единого изменения, как они есть).
