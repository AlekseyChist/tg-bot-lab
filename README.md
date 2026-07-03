# 🚴 Avala Segment Bot

*бот показывает время участников чата на Strava-сегменте Avala*

## 🧠 Фишка: «облачный мозг + локальные руки»

Этот проект использует **гибридный подход**:

- **Claude (облако)** — проектирует, дробит задачу на подзадачи и пишет спеки-промпты в `orchestrator/prompts/`
- **Локальная модель qwen3-coder** — генерирует весь код через `orchestrator/gen.py` (мост к Ollama)
- **Claude** — лишь запускает тесты и корректирует спеки

> 💰 Платный AI используется только для планирования. Генерация кода бесплатна на локальной GPU.

## 🎯 Команды

| Команда     | Что делает                               |
|-------------|------------------------------------------|
| `/link`     | Привязать свой Strava (один раз)         |
| `/board`    | Показать таблицу времён всех привязанных |
| `/badges`   | Установить бейджи с временем рядом с именами |
| `/unlink`   | Отвязать Strava                          |
| `/help`     | Справка                                  |

## ⚠️ Важное про Strava API

Официальный API лидербордов сегментов Strava **удалили в 2020 году** — получить «время всех разом» нельзя.

Поэтому каждый участник один раз привязывает свой аккаунт Strava через OAuth, а бот берёт его личный рекорд (PR) из поля `athlete_segment_stats.pr_elapsed_time`.

> 📌 Достаточно прав scope=`read`.

## 🏗 Архитектура

| Файл                     | Роль                                           |
|--------------------------|------------------------------------------------|
| `bot/logic.py`           | Чистые функции (формат времени, таблица, бейдж) |
| `bot/strava.py`          | Async-клиент Strava (OAuth, refresh, PR на сегменте) |
| `bot/storage.py`         | JSON-хранилище токенов                         |
| `bot/oauth_server.py`    | aiohttp ловит OAuth-callback                   |
| `bot/handlers.py`        | Команды aiogram                                |
| `bot/main.py`            | Запуск: polling + OAuth-сервер                 |
| `orchestrator/gen.py`    | Мост к локальной qwen (Ollama)                 |

> 🧠 Принцип: чистая логика отделена от I/O, поэтому её можно тестировать без токенов.

## 🚀 Запуск

```bash
python -m venv .venv
# Активация виртуального окружения:
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Заполнить: BOT_TOKEN (от @BotFather),
# STRAVA_CLIENT_ID и STRAVA_CLIENT_SECRET (strava.com/settings/api)

python -m bot.main
```

> 🌐 Для привязки друзей нужен публичный адрес для OAuth-callback (например, туннель `cloudflared` к `localhost:8000`). Его домен нужно вписать в **Authorization Callback Domain** в настройках Strava.

## 🧪 Тесты

```bash
pytest -q
```

> 26 тестов, чистая логика проверяется без токенов.

## 🔒 Секреты

Токены и ключи хранятся только в `.env` (и `bot/data/` с токенами).  
Все эти файлы находятся в `.gitignore`, поэтому **не попадают в репозиторий**.

## 🛠 Стек

- Python
- aiogram 3.x
- aiohttp
- python-dotenv
- Ollama + qwen3-coder (локальная генерация кода)
