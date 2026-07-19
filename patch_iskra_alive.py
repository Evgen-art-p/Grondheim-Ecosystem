#!/usr/bin/env python3
# patch_iskra_alive.py
# ─────────────────────────────────────────────────────────────
# ISKRA_ALIVE_V1 · 20.07
#
# TOCHKA_ZHIVA_V1 (patch_tochka_zhiva.py) добавил в trading_state
# схему поля "alive"/"rodilas_na_bare", но никто их не выставлял в
# True — proverit_tochku() всегда видела "точки нет". Этот патч
# закрывает дыру: в момент, когда t1_status становится DETECTED
# (спуск реально нашёл точку c), Искра зажигает alive=True и
# метит rodilas_na_bare датой рождения. Когда DETECTED уходит
# (NOT_FOUND) — alive гасится тоже, честно, без ожидания следующего
# бара proverit_tochku.
#
# ЗАВИСИМОСТЬ: применить ПОСЛЕ patch_tochka_zhiva.py (нужна схема
# полей в trading_state, иначе не критично — setdefault отработает,
# но порядок логичнее в эту сторону).
#
# ИДЕМПОТЕНТНОСТЬ: маркер ISKRA_ALIVE_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = (Path(__file__).resolve().parent / "GRONDHEIM_CITY" / "Биржа"
          / "цеха" / "торговый_хаос" / "слоты" / "A01" / "мозг.py")
MARKER = "ISKRA_ALIVE_V1"


ANCHOR = '''    tstate["iskra"]["found_timeframe"] = (
        signal.get("found_timeframe") or signal.get("timeframe")
    )
    save_trading_state(tstate)'''

REPLACEMENT = '''    tstate["iskra"]["found_timeframe"] = (
        signal.get("found_timeframe") or signal.get("timeframe")
    )
    # ''' + MARKER + ''': точка c родилась — зажигаем alive. Если статус
    # ушёл обратно в NOT_FOUND — гасим сразу, честно (не ждём, пока
    # proverit_tochku поймает слом на следующем баре в тестере/совете).
    _t1 = signal.get("t1_status", "NOT_FOUND")
    if _t1 == "DETECTED":
        tstate["iskra"]["alive"] = True
        tstate["iskra"]["rodilas_na_bare"] = (md or {}).get("bar_time")
    elif _t1 == "NOT_FOUND":
        tstate["iskra"]["alive"] = False
    save_trading_state(tstate)'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    if ANCHOR not in src:
        raise SystemExit("❌ якорь не найден — файл разошёлся "
                          "с ожидаемым, патч НЕ применён")

    src = src.replace(ANCHOR, REPLACEMENT, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_alive")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
