# -*- coding: utf-8 -*-
"""
proverka_pozicii.py
────────────────────────────────────────────────────────────────────
ЧТО РЕАЛЬНО ЛЕЖИТ В ПОЗИЦИИ.

Ищем обрыв: заряд Ильи двинулся (суд ТРЕЙДЕРА сработал), а у Веры
черновиков нет (суд СЕНСОРОВ молчал). Судья сенсоров начинается с:

    stol = pos.get("стол_входа") or {}
    if not stol or pnl_r is None:
        return          # ← тихо выходит, если слепка нет

Значит либо слепка нет в позиции, либо он пустой. Смотрим глазами.

Имя ASCII: PowerShell ест букву «Б» при вставке. Файл ищем сами.
Ничего не пишет.  Из КОРНЯ репы:  python proverka_pozicii.py
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("=" * 70)
    print("ЧТО В ПОЗИЦИИ — есть ли слепок стола входа")
    print("=" * 70)

    # ищем файл сами, не набирая «Б»
    kandidaty = list(ROOT.rglob("trading_state.json"))
    if not kandidaty:
        print("!! trading_state.json нигде не найден под корнем репы.")
        return 1

    for f in kandidaty:
        print(f"\nФАЙЛ: {f.relative_to(ROOT)}")
        print("-" * 70)
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  не читается: {e}")
            continue

        pos_list = d.get("positions", []) or []
        print(f"позиций: {len(pos_list)}")

        if not pos_list:
            print("  (пусто — позиции могли быть очищены после закрытия)")
            # покажем, какие вообще ключи есть в state
            print(f"  ключи state: {list(d.keys())}")
            continue

        for i, p in enumerate(pos_list, 1):
            print(f"\n  ── позиция #{i} ──")
            print(f"  ключи: {list(p.keys())}")
            stol = p.get("стол_входа")
            if stol is None:
                print("  !! СЛЕПКА «стол_входа» НЕТ — судья сенсоров молчит")
                print("     → позиция открывалась кодом БЕЗ патча SUD_SENSOROV_V2,")
                print("       либо врезка в _persist_trading_state не отработала.")
            elif not stol:
                print("  !! слепок «стол_входа» ПУСТ: {}")
                print("     → tstate в момент сборки не содержал показаний сенсоров.")
            else:
                print("  OK слепок «стол_входа» есть:")
                for k, v in stol.items():
                    print(f"     {k}: {v}")
            print("\n  полная позиция:")
            print("  " + json.dumps(p, ensure_ascii=False, indent=1).replace("\n", "\n  "))

    # заодно: смотрим на журнал pnl — были ли закрытия
    print("\n" + "=" * 70)
    pnl = list(ROOT.rglob("trading_pnl.jsonl"))
    for f in pnl:
        lines = [l for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        print(f"ЖУРНАЛ {f.relative_to(ROOT)}: записей {len(lines)}")
        for l in lines[-3:]:
            try:
                r = json.loads(l)
                print(f"  · {r.get('trader')} {r.get('pnl_r')}R "
                      f"{r.get('close_reason','')} {r.get('closed_at','')}")
            except Exception:
                print(f"  · {l[:80]}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
