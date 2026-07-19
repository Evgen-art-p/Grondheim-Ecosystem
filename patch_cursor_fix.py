#!/usr/bin/env python3
# patch_cursor_fix.py
# ─────────────────────────────────────────────────────────────
# CURSOR_FIX_V1 · 20.07 (срочный, найден на живом прогоне XAUUSD H4)
#
# БАГ (мой, из SITO_SLIYANIE_V1): слияние Сита-1/Сита-2 убрало строку
# state["cursor"] = i, которая раньше жила внутри цикла Сита-2. Эта
# переменная — не косметика: её читает "честный кран" (_fake_fetch/
# _fake_pull/_multi_step_down), которым подменяется pull_bars() на
# время теста. Когда Искра ВНУТРИ СЕБЯ зовёт pull_bars(symbol, tf)
# (её собственный спуск по лесенке, ISKRA_V2_DESCENT), она получает
# честный срез истории НЕ ПО ТЕКУЩЕМУ БАРУ, а по state["cursor"] —
# а тот со времён патча слияния сит НИКОГДА не обновлялся и оставался
# на значении warmup (самый первый бар прогона).
#
# СЛЕДСТВИЕ: Искра на КАЖДОМ кандидате видела одни и те же (самые
# древние) бары — отсюда десятки подряд честных "NOT_FOUND": не
# потому что там реально нечего искать, а потому что ей физически
# показывали не тот момент времени. Дешёвое сито (build_market_data
# напрямую на window) эту переменную не использует и потому находило
# кандидатов правильно — расхождение между "сито нашло" и "Искра не
# нашла" было СИМПТОМОМ этого бага, не пластиком архитектуры.
#
# ПАТЧ: возвращает state["cursor"] = i на каждом баре слитого цикла,
# в начале итерации — до любых обращений к _fake_fetch.
#
# ЗАВИСИМОСТЬ: применить ПОСЛЕ patch_sito_sliyanie.py.
#
# ИДЕМПОТЕНТНОСТЬ: маркер CURSOR_FIX_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Биржа" / "tester_express.py"
MARKER = "CURSOR_FIX_V1"


ANCHOR = '''        for i in range(warmup, total):
            if _stop_requested():   # TESTER_HANDLES_V1: кнопка СТОП биржи
                out(f"⏸ СТОП по команде Шефа — прошёл бар {i} из {total}.")
                break

            # ── ведение: на КАЖДОМ баре, не только между кандидатами ──'''

REPLACEMENT = '''        for i in range(warmup, total):
            if _stop_requested():   # TESTER_HANDLES_V1: кнопка СТОП биржи
                out(f"⏸ СТОП по команде Шефа — прошёл бар {i} из {total}.")
                break

            # ''' + MARKER + ''': "честный кран" (_fake_fetch/_fake_pull/
            # _multi_step_down) режет историю ПО ЭТОЙ переменной, не по
            # аргументам вызова. Без неё Искра внутри себя (её собственный
            # pull_bars при спуске по лесенке) видела бы всегда один и тот
            # же (самый первый) момент истории — потерялась при слиянии
            # Сита-1/Сита-2, возвращаю на каждом баре.
            state["cursor"] = i

            # ── ведение: на КАЖДОМ баре, не только между кандидатами ──'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    if ANCHOR not in src:
        raise SystemExit("❌ якорь не найден — файл разошёлся "
                          "с ожидаемым (наложен ли уже patch_sito_sliyanie.py?), "
                          "патч НЕ применён")

    src = src.replace(ANCHOR, REPLACEMENT, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_cursor")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
