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
   - bot/storage.py — хранилище токенов: Upstash Redis (прод) или JSON-файл (локальный фолбэк)
   - bot/oauth_server.py — обработка OAuth-callback Strava
   - bot/handlers.py — команды aiogram
   - bot/main.py — локальный запуск: polling + OAuth-сервер
   - api/index.py — единый ASGI-entrypoint для Vercel (вебхук Telegram + OAuth-callback)
   - scripts/set_webhook.py — регистрация вебхука Telegram на публичный адрес
   - orchestrator/gen.py — мост к локальной qwen (Ollama)
   Отдельно упомяни принцип: чистая логика отделена от I/O, поэтому её можно
   тестировать без токенов.

6. ## 🚀 Запуск локально (polling) — блок ```bash с шагами:
   python -m venv .venv и активация (Windows: .venv\Scripts\activate)
   pip install -r requirements.txt
   cp .env.example .env  и заполнить: BOT_TOKEN (от @BotFather),
   STRAVA_CLIENT_ID и STRAVA_CLIENT_SECRET (strava.com/settings/api)
   python -m bot.main
   После блока — короткое примечание: локально бот работает, пока включён ПК;
   для привязки друзей нужен публичный адрес для OAuth-callback (туннель
   cloudflared к localhost:8000), а его домен — в Authorization Callback Domain
   в настройках Strava. Без Upstash хранилище падает на файл bot/data/tokens.json.

7. ## ☁️ Хостинг на Vercel (webhook, всегда онлайн)
   Опиши, что в проде бот живёт на Vercel в режиме вебхука и не зависит от ПК.
   Маркированным списком по шагам:
   - Задеплоить проект на Vercel (api/index.py — точка входа, см. vercel.json).
   - В переменных окружения проекта на Vercel задать: BOT_TOKEN,
     STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, OAUTH_PUBLIC_BASE
     (публичный https-адрес приложения, например https://<app>.vercel.app).
   - Подключить хранилище Upstash Redis через Vercel Marketplace — оно создаёт
     переменные KV_REST_API_URL/KV_REST_API_TOKEN, которые config.py читает
     автоматически (нужно, т.к. у serverless нет постоянного диска).
   - В strava.com/settings/api вписать Authorization Callback Domain =
     домен приложения на Vercel (без https:// и без /).
   - Зарегистрировать вебхук: локально с заполненными BOT_TOKEN и
     OAUTH_PUBLIC_BASE запустить `python scripts/set_webhook.py`.
   После шагов — примечание: env-переменные применяются только после нового
   деплоя (`vercel --prod`).

8. ## 🧪 Тесты — блок ```bash с `pytest -q` и строка: «26 тестов, чистая логика
   проверяется без токенов».

9. ## 🔒 Секреты — короткий абзац: локально токены и ключи лежат только в .env
   (и bot/data/ с токенами) — всё в .gitignore и в репозиторий не попадает;
   в проде секреты хранятся в переменных окружения Vercel. В коде секретов нет.

10. ## 🛠 Стек — маркированный список: Python, aiogram 3.x, aiohttp,
    python-dotenv, Upstash Redis (upstash-redis), Vercel (serverless webhook),
    Ollama + qwen3-coder (локальная генерация кода).
