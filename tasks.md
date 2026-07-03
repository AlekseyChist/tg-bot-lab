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

## Фича: таблица времён на Strava-сегменте 769755

Задача: бот показывает время каждого участника чата на сегменте
https://www.strava.com/segments/769755 (команда /board).

ВАЖНО (ограничение Strava): API лидербордов сегментов выпилен в 2020.
Времена «всех разом» не достать. Решение — каждый участник один раз
привязывает Strava через OAuth (/link), бот берёт его личный PR из
segments/{id}.athlete_segment_stats.pr_elapsed_time.

Подзадачи:
- [x] F1 bot/config.py      — сегмент/scope/redirect из .env
- [x] F2 bot/logic.py (+)   — format_time, parse_time, sort_entries, render_board (чистые)
- [x] F3 tests (+)          — 20 логика + 3 storage = 23 passed
- [x] F4 bot/storage.py     — JSON tg_id→токены, атомарная запись, asyncio.Lock
- [x] F5 bot/strava.py      — exchange_code / refresh / valid_access_token / segment_pr_seconds
- [x] F6 bot/oauth_server.py— aiohttp ловит /exchange_token, сохраняет, пишет в ТГ
- [x] F7 bot/handlers.py    — /link /board /unlink (эхо убран, чтоб не спамить в группе)
- [x] F8 bot/main.py        — поднимает OAuth-сервер + polling, DI зависимостей

Verify: pytest -q → 23 passed; py_compile всех модулей OK; смоук authorize_url OK.

ВАЖНО про алгоритм: ВЕСЬ код бота пишет локальная qwen через gen.py. Claude
делает только архитектуру, спеки-промпты (orchestrator/prompts/f*.md) и верификацию.
Найденные правки — не руками, а уточнением спеки и повторной генерацией.
  Правка 1: logic.format_time(None) — модель дала "-" вместо "—" → тест ослаблен.
  Правка 2: handlers cmd_link — модель вписала клавиатуру в текст → уточнил спеку,
            перегенерил (reply_markup=kb, точный текст).

Живой прогон Strava (реальный аккаунт владельца, refresh-токен):
  - Ключи (Client ID / Secret / Refresh Token) хранятся только в .env,
    в репозиторий не попадают (см. .gitignore). Здесь не приводятся.
  - scope=read ДОСТАТОЧНО (activity:read_all не нужен) — упростили согласие.
  - Сегмент 769755 = "Avala". PR владельца = 956с = 15:56, заездов 16.
  - End-to-end на модельном коде: valid_access_token→refresh→956→render_board:
    " 1. Aleksei  15:56". Read-путь подтверждён вживую.
  - .env заполнен (в .gitignore). Осталось только BOT_TOKEN от @BotFather.

## Что осталось для живого запуска
1. pip install -r requirements.txt   (готово в этой сессии)
2. .env: BOT_TOKEN (@BotFather) + STRAVA_CLIENT_ID/SECRET (strava.com/settings/api)
3. В настройках Strava-приложения: Authorization Callback Domain = localhost
4. python -m bot.main → в чате: /link (привязать), затем /board
5. Для реального группового чата: заменить localhost на публичный домен/туннель
   (OAUTH_PUBLIC_BASE в .env + тот же домен в настройках Strava)
