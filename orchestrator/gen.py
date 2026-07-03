#!/usr/bin/env python3
"""Bridge: dispatch a single subtask to the local Ollama coding model.

Это "локальные руки" в связке "облачный мозг (Claude) + локальная видяха".
Claude формирует system+task, зовёт этот скрипт, получает чистый код.

Стандартная библиотека only — чтобы сам оркестратор не тянул зависимостей.

Примеры:
    python gen.py --task "Write add(a,b)" --out ../bot/x.py
    python gen.py --system-file sys.txt --task-file t.md --out ../bot/handlers.py
    echo "..." | python gen.py --stdin --out out.py

Код вынимается из ```fenced``` блоков. Если блоков нет — печатается сырой ответ
(и НЕ пишется в файл, чтобы не затереть цель мусором).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3-coder-8k:latest"

# Жёсткая рамка для кодера: только код, без болтовни, без выдумок.
DEFAULT_SYSTEM = (
    "You are a precise Python code generator. "
    "Output ONLY the requested code inside a single ```python fenced block. "
    "No explanations, no prose before or after. "
    "Follow the spec exactly; do not invent extra features. "
    "Use type hints. Keep imports minimal and correct."
)

FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str | None:
    """Вынуть код из fenced-блоков. Склеить, если их несколько. None если нет."""
    blocks = FENCE_RE.findall(text)
    if not blocks:
        return None
    return "\n\n".join(b.strip("\n") for b in blocks).strip() + "\n"


def call_ollama(model: str, system: str, task: str, num_predict: int,
                temperature: float, keep_alive: str, timeout: int) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": task},
        ],
        "stream": False,
        "keep_alive": keep_alive,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Dispatch one subtask to local Ollama.")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--task", help="Task text (inline).")
    ap.add_argument("--task-file", help="Read task from file.")
    ap.add_argument("--stdin", action="store_true", help="Read task from stdin.")
    ap.add_argument("--system", help="Override system prompt (inline).")
    ap.add_argument("--system-file", help="Read system prompt from file.")
    ap.add_argument("--out", help="Write extracted code to this file.")
    ap.add_argument("--num-predict", type=int, default=2048)
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--keep-alive", default="15m", help="Keep model warm in VRAM.")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--raw", action="store_true", help="Print raw model reply too.")
    args = ap.parse_args()

    # --- собрать task ---
    if args.stdin:
        task = sys.stdin.read()
    elif args.task_file:
        with open(args.task_file, encoding="utf-8") as f:
            task = f.read()
    elif args.task:
        task = args.task
    else:
        ap.error("need --task, --task-file or --stdin")

    # --- собрать system ---
    if args.system_file:
        with open(args.system_file, encoding="utf-8") as f:
            system = f.read()
    elif args.system:
        system = args.system
    else:
        system = DEFAULT_SYSTEM

    t0 = time.monotonic()
    try:
        data = call_ollama(
            args.model, system, task, args.num_predict,
            args.temperature, args.keep_alive, args.timeout,
        )
    except Exception as e:  # noqa: BLE001 - CLI boundary
        print(f"[gen] ОШИБКА вызова Ollama: {e}", file=sys.stderr)
        return 2
    wall = time.monotonic() - t0

    reply = data.get("message", {}).get("content", "")
    ntok = data.get("eval_count", 0)
    gen_s = data.get("eval_duration", 0) / 1e9
    tps = (ntok / gen_s) if gen_s else 0.0
    print(
        f"[gen] model={args.model} wall={wall:.1f}s gen={gen_s:.1f}s "
        f"tokens={ntok} ~{tps:.0f} tok/s",
        file=sys.stderr,
    )

    if args.raw or not args.out:
        print(reply)

    code = extract_code(reply)
    if code is None:
        print("[gen] ВНИМАНИЕ: в ответе нет ```fenced``` блока — файл не записан.",
              file=sys.stderr)
        return 1

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        print(f"[gen] записано {len(code)} байт → {args.out}", file=sys.stderr)
    else:
        print(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
