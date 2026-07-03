Напиши файл README.md для проекта «Avala Segment Bot» (репозиторий tg-bot-lab).
На русском, красиво, с эмодзи в заголовках и таблицами.

Проект: Telegram-бот, который показывает время каждого участника чата на
Strava-сегменте №769755 «Avala» — прямо рядом с именем.

Обязательные разделы (именно в таком порядке):

1. Заголовок «# 🚴 Avala Segment Bot» и под ним одна строка-описание курсивом:
   бот показывает время участников чата на Strava-сегменте Avala.

2. ## 🧠 Фишка: «облачный мозг + локальные руки»
   Опиши подход: Claude (облако) только проектирует, дробит задачу на подзадачи
   и пишет спеки-промпты в orchestrator/prompts/; весь код пишет локальная модель
   qwen3-coder на своей видеокарте (RTX 4090) через orchestrator/gen.py (мост к
   Ollama). Claude лишь гоняет тесты и правит спеки. Платный AI — только на
   планирование, генерация кода бесплатна на локальной GPU.

3. ## 🎯 Команды — таблица из двух колонок (Команда | Что делает):
   - /link — привязать свой Strava (один раз, через OAuth)
   - /board — таблица времён всех привязанных участников
   - /badges — повесить время каждому как бейдж рядом с именем (custom title)
   - /unlink — отвязать Strava
   - /help — справка

4. ## ⚠️ Важное про Strava API
   Официальный API лидербордов сегментов Strava убрала в 2020 — «время всех
   разом» получить нельзя. Поэтому каждый участник один раз привязывает свой
   Strava (OAuth), а бот берёт его личный рекорд (PR) из поля
   athlete_segment_stats.pr_elapsed_time. Достаточно прав scope=read.

5. ## 🏗 Архитектура — таблица (Файл | Роль):
   - bot/logic.py — чистые функции (формат времени, таблица, бейдж), тестируются офлайн
   - bot/strava.py — async-клиент Strava (OAuth, refresh, PR на сегменте)
   - bot/storage.py — JSON-хранилище токенов
   - bot/oauth_server.py — aiohttp ловит OAuth-callback
   - bot/handlers.py — команды aiogram
   - bot/main.py — запуск: polling + OAuth-сервер
   - orchestrator/gen.py — мост к локальной qwen (Ollama)
   Отдельно упомяни принцип: чистая логика отделена от I/O, поэтому её можно
   тестировать без токенов.

6. ## 🚀 Запуск — блок ```bash с шагами:
   python -m venv .venv и активация (Windows: .venv\Scripts\activate)
   pip install -r requirements.txt
   cp .env.example .env  и заполнить: BOT_TOKEN (от @BotFather),
   STRAVA_CLIENT_ID и STRAVA_CLIENT_SECRET (strava.com/settings/api)
   python -m bot.main
   После блока — короткое примечание: для привязки друзей нужен публичный адрес
   для OAuth-callback (например, туннель cloudflared к localhost:8000), а его
   домен надо вписать в Authorization Callback Domain в настройках Strava.

7. ## 🧪 Тесты — блок ```bash с `pytest -q` и строка: «26 тестов, чистая логика
   проверяется без токенов».

8. ## 🔒 Секреты — короткий абзац: токены и ключи лежат только в .env (и
   bot/data/ с токенами), всё это в .gitignore и в репозиторий не попадает.

9. ## 🛠 Стек — маркированный список: Python, aiogram 3.x, aiohttp,
   python-dotenv, Ollama + qwen3-coder (локальная генерация кода).
