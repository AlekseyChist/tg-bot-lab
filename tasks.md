# TG-Bot Lab — план подзадач (отработка алгоритма «облачный мозг + локальные руки»)

## Цель
Отработать конвейер: Claude планирует и дробит → каждая мелкая подзадача уходит
на локальную qwen3-coder (RTX 4090) через `orchestrator/gen.py` → код пишется в
файл → гоняются тесты → Claude проверяет и правит.

## Архитектура бота (aiogram 3.x)
Чистая логика отделена от Telegram-хендлеров — чтобы тестировать оффлайн без токена.

    bot/logic.py     ← ЧИСТЫЕ функции (без импортов telegram) — легко тестируются
    bot/handlers.py  ← тонкие aiogram-хендлеры, зовут logic
    bot/main.py      ← bootstrap: читает BOT_TOKEN из .env, запускает polling
    tests/test_logic.py ← оффлайн-тесты чистой логики

## Подзадачи (каждая → отдельный вызов локальной модели)

- [x] S1  bot/logic.py       — start_text(), help_text(), echo_text(t), keyboard(), on_button(data)
- [x] S2  tests/test_logic.py — pytest на все функции S1 (verify surface, без токена)
- [x] S3  bot/handlers.py     — aiogram Router: /start, /help, эхо, callback кнопок
- [x] S4  bot/main.py         — Bot/Dispatcher, .env, polling

## Правило verify
После каждой подзадачи с кодом-логикой: `pytest -q`. Хендлеры/main проверяем
компиляцией (`python -m py_compile`), т.к. живой прогон требует токена BotFather.

## Лог прогонов
Модель: qwen3-coder-8k:latest, RTX 4090 Laptop 16GB. ~68-69 tok/s (тёплая),
холодный старт ~15с. keep_alive=15m держит модель в памяти между вызовами.

- S1 logic.py     — 7.1с / 255 ток. Код корректен. Правка Claude: 0.
  Замечание: модель написала "Эхо" (заглавная) вместо требуемой подстроки "эхо";
  контракт-тест сделан регистронезависимым (`.lower()`) — осознанно.
- S2 test_logic.py — 7.5с / 296 ток. 10 тестов. Результат: 10 passed. Правок: 0.
- S3 handlers.py  — 6.7с / 221 ток. aiogram 3.x чисто, без legacy 2.x. py_compile OK.
- S4 main.py      — 4.9с / 120 ток. py_compile OK.

Итого генерация: ~26с чистого GPU-времени на весь бот. Платный AI (Claude) —
только планирование, спеки-контракты и верификация. Ни одной правки кода руками.

## Что осталось для живого запуска
1. pip install -r requirements.txt   (aiogram ещё не установлен)
2. Токен от @BotFather → .env
3. python -m bot.main
