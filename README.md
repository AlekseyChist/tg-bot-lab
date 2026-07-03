# TG-Bot Lab

Песочница для отработки алгоритма **«облачный мозг (Claude) + локальные руки (qwen3-coder на RTX 4090)»**.

## Идея
Claude не пишет код бота сам — он **дробит задачу на мелкие подзадачи** и
**диспетчеризует** каждую на локальную модель через `orchestrator/gen.py`, затем
принимает результат, гоняет тесты и правит. Платный AI тратится только на
планирование и контроль качества; генерация кода — бесплатно на видяхе.

## Как устроено
- `orchestrator/gen.py` — мост к Ollama (`http://localhost:11434`). Stdlib only.
- `tasks.md` — план дробления на подзадачи + лог прогонов.
- `bot/` — генерируемый код бота (aiogram 3.x). Логика отделена от хендлеров.
- `tests/` — оффлайн-тесты чистой логики (без токена Telegram).

## Запуск конвейера (пример одной подзадачи)
```bash
python orchestrator/gen.py \
  --task-file orchestrator/prompts/s1_logic.md \
  --out bot/logic.py
pytest -q
```

## Запуск самого бота
```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env    # вставить токен от @BotFather
python -m bot.main
```
