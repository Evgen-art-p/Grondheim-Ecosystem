# -*- coding: utf-8 -*-
"""
ochistit_pozicii.py — разовая чистка залежавшихся открытых позиций.

Стирает ТОЛЬКО массив positions в trading_state.json (старые сделки,
родившиеся до патча stop_initial — они дают NoneR на подтянутом стопе).
Память Искры, history_dna и всё остальное — НЕ трогает.

Делает бэкап перед чисткой. Запуск из корня проекта:
    python ochistit_pozicii.py
"""
import io
import json
import sys
from pathlib import Path

STATE = Path("GRONDHEIM_CITY") / "Биржа" / "данные" / "trading_state.json"


def main():
    if not STATE.exists():
        print(f"[ЧИСТКА] не найден {STATE}")
        # покажем, где вообще лежат trading_state.json
        found = list(Path(".").rglob("trading_state.json"))
        if found:
            print("[ЧИСТКА] нашёл рядом:")
            for f in found:
                print("   ", f)
            print("[ЧИСТКА] поправь путь STATE в скрипте на нужный")
        sys.exit(1)

    d = json.loads(STATE.read_text(encoding="utf-8"))
    n = len(d.get("positions", []) or [])

    if n == 0:
        print("[ЧИСТКА] позиций и так нет — чистить нечего")
        return

    # бэкап
    bak = STATE.with_suffix(".json.bak_ochistka")
    bak.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    d["positions"] = []
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ЧИСТКА] OK: стёрто позиций {n}. Память Искры и history_dna целы.")
    print(f"[ЧИСТКА] бэкап: {bak.name}")
    print("[ЧИСТКА] теперь гоняй тестер — новые сделки пойдут со stop_initial.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
