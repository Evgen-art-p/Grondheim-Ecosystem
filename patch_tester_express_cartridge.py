# -*- coding: utf-8 -*-
# patch_tester_express_cartridge.py — TESTER_EXPRESS_CARTRIDGE_V1
# ─────────────────────────────────────────────────────────────
# НЕ типизация — реальный порт. tester_express.py всё ещё дёргает
# iskra_live.py/morj_live.py/panikyor_live.py/hans_live.py/
# arkhiv_live.py/brut_live.py/avan_live.py/cons_live.py/
# executor_live.py — плоские файлы старого мира (-2). Их больше нет:
# Шеф переименовал их в мозг.py по Закону Картриджа, каждый теперь
# живёт в GRONDHEIM_CITY/Биржа/цеха/{цех}/слоты/{слот}/мозг.py.
# ui_torg.py это уже умеет читать через _slot_brain(). tester_express.py —
# ещё нет: 8 из 9 импортов вообще без try/except, тестер рухнет
# ModuleNotFoundError'ом на первом же прогоне после Искры.
#
# ЧТО ДЕЛАЕТ ПАТЧ:
#   1. Добавляет _REPO и собственный _slot_brain() — тот же механизм,
#      что в ui_torg.py (Закон Фрактала: источник свой, труба та же).
#      tester_express.py — отдельный CLI-скрипт, не тянет чужой модуль
#      ради одной функции.
#   2. Меняет 9 точек входа (маппинг ceh_id/слот — из ROSTER_SPEC
#      ui_torg.py, порядок 1:1 совпадает с порядком импортов здесь):
#        run_iskra    → торговый_хаос / A01
#        run_morj     → торговый_хаос / A02
#        run_panikyor → торговый_хаос / A03
#        run_hans     → торговый_хаос / A04
#        run_arkhiv   → контора       / архивариус
#        run_brut     → торговый_хаос / A06
#        run_avan     → торговый_хаос / A07
#        run_cons     → торговый_хаос / A08
#        run_executor → контора       / исполнитель
#
# ПОВЕДЕНИЕ ПРИ СБОЕ НЕ МЕНЯЕТСЯ: весь блок (строки ~316-570) сидит
# в одном try/finally БЕЗ except — если мозг не в слоте, исключение
# как и раньше падает наверх после finally, прогон обрывается. Патч
# просто меняет ModuleNotFoundError на честный RuntimeError с именем
# слота — тот же приём, что уже стоит в ui_torg.py (_slot_brain там же).
#
# Ни одна формула/вызов run_iskra(...)/run_morj(...)/... не меняется —
# меняется только ОТКУДА берётся функция.
#
# ЗАПУСК из корня:  python patch_tester_express_cartridge.py
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TESTER_EXPRESS_CARTRIDGE_V1"
ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "tester_express.py"

# ── 0. импорт importlib.util + _REPO + _slot_brain, сразу после _HERE ──
OLD_HEADER = '''import sys
import argparse
from pathlib import Path
from datetime import datetime

_HERE = Path(__file__).resolve().parent'''

NEW_HEADER = '''import sys
import argparse
import importlib.util
from pathlib import Path
from datetime import datetime

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent   # TESTER_EXPRESS_CARTRIDGE_V1: корень репо, для поиска мозгов
_BRAIN_CACHE: dict = {}


def _slot_brain(ceh_id: str, slot: str):
    """TESTER_EXPRESS_CARTRIDGE_V1: Закон Картриджа для кода — тот же
    механизм, что в ui_torg.py (_slot_brain). Мозг слота живёт в
    GRONDHEIM_CITY/Биржа/цеха/{ceh_id}/слоты/{slot}/мозг.py — не
    захардкожен списком имён, цех сам говорит, что там лежит. Нет
    файла — честная вакансия (None), не ошибка. Кэш на процесс."""
    key = (ceh_id, slot)
    if key in _BRAIN_CACHE:
        return _BRAIN_CACHE[key]
    brain_path = (_REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh_id
                 / "слоты" / slot / "мозг.py")
    if not brain_path.exists():
        _BRAIN_CACHE[key] = None
        return None
    spec = importlib.util.spec_from_file_location(
        f"_brain_{ceh_id}_{slot}", brain_path)
    if spec is None or spec.loader is None:
        _BRAIN_CACHE[key] = None
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _BRAIN_CACHE[key] = mod
    return mod'''

# ── 1. Искра (внутри "Сита 1", единственный вызов run_iskra ниже по коду) ──
OLD_1 = '''    try:
        from iskra_live import run_iskra'''
NEW_1 = '''    try:
        _b_a01 = _slot_brain("торговый_хаос", "A01")
        if _b_a01 is None:
            raise RuntimeError("мозг A01 (Искра) ещё не в слоте")
        run_iskra = _b_a01.run_iskra'''

# ── 2. Морж ──
OLD_2 = '''            from morj_live import run_morj
            rm = run_morj(symbol=symbol, timeframe=timeframe)'''
NEW_2 = '''            _b_a02 = _slot_brain("торговый_хаос", "A02")
            if _b_a02 is None:
                raise RuntimeError("мозг A02 (Морж) ещё не в слоте")
            rm = _b_a02.run_morj(symbol=symbol, timeframe=timeframe)'''

# ── 3. Паникёр ──
OLD_3 = '''            from panikyor_live import run_panikyor
            rp = run_panikyor(symbol=symbol, timeframe=timeframe)'''
NEW_3 = '''            _b_a03 = _slot_brain("торговый_хаос", "A03")
            if _b_a03 is None:
                raise RuntimeError("мозг A03 (Паникёр) ещё не в слоте")
            rp = _b_a03.run_panikyor(symbol=symbol, timeframe=timeframe)'''

# ── 4. Ганс ──
OLD_4 = '''            from hans_live import run_hans
            rh = run_hans(symbol=symbol, timeframe=timeframe)'''
NEW_4 = '''            _b_a04 = _slot_brain("торговый_хаос", "A04")
            if _b_a04 is None:
                raise RuntimeError("мозг A04 (Ганс) ещё не в слоте")
            rh = _b_a04.run_hans(symbol=symbol, timeframe=timeframe)'''

# ── 5. Архивариус ──
OLD_5 = '''            from arkhiv_live import run_arkhiv
            ra = run_arkhiv()'''
NEW_5 = '''            _b_a05 = _slot_brain("контора", "архивариус")
            if _b_a05 is None:
                raise RuntimeError("мозг архивариуса ещё не в слоте")
            ra = _b_a05.run_arkhiv()'''

# ── 6. Брут ──
OLD_6 = '''            from brut_live import run_brut
            rb = run_brut(symbol=symbol, timeframe=timeframe)'''
NEW_6 = '''            _b_a06 = _slot_brain("торговый_хаос", "A06")
            if _b_a06 is None:
                raise RuntimeError("мозг A06 (Брут) ещё не в слоте")
            rb = _b_a06.run_brut(symbol=symbol, timeframe=timeframe)'''

# ── 7. Авантюрист ──
OLD_7 = '''            from avan_live import run_avan
            rav = run_avan(symbol=symbol, timeframe=timeframe)'''
NEW_7 = '''            _b_a07 = _slot_brain("торговый_хаос", "A07")
            if _b_a07 is None:
                raise RuntimeError("мозг A07 (Авантюрист) ещё не в слоте")
            rav = _b_a07.run_avan(symbol=symbol, timeframe=timeframe)'''

# ── 8. Консерватор ──
OLD_8 = '''            from cons_live import run_cons
            rco = run_cons(symbol=symbol, timeframe=timeframe)'''
NEW_8 = '''            _b_a08 = _slot_brain("торговый_хаос", "A08")
            if _b_a08 is None:
                raise RuntimeError("мозг A08 (Консерватор) ещё не в слоте")
            rco = _b_a08.run_cons(symbol=symbol, timeframe=timeframe)'''

# ── 9. Исполнитель ──
OLD_9 = '''            from executor_live import run_executor
            rex = run_executor(symbol=symbol, timeframe=timeframe)'''
NEW_9 = '''            _b_a09 = _slot_brain("контора", "исполнитель")
            if _b_a09 is None:
                raise RuntimeError("мозг исполнителя ещё не в слоте")
            rex = _b_a09.run_executor(symbol=symbol, timeframe=timeframe)'''

EOF_MARKER = "\n# TESTER_EXPRESS_CARTRIDGE_V1 — маркер идемпотентности\n"

BLOCKS = [
    ("шапка: _REPO + _slot_brain",   OLD_HEADER, NEW_HEADER),
    ("A01 Искра",                     OLD_1, NEW_1),
    ("A02 Морж",                      OLD_2, NEW_2),
    ("A03 Паникёр",                   OLD_3, NEW_3),
    ("A04 Ганс",                      OLD_4, NEW_4),
    ("A05 Архивариус",                OLD_5, NEW_5),
    ("A06 Брут",                      OLD_6, NEW_6),
    ("A07 Авантюрист",                OLD_7, NEW_7),
    ("A08 Консерватор",               OLD_8, NEW_8),
    ("A09 Исполнитель",               OLD_9, NEW_9),
]


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: порт 9 агентов на Закон Картриджа")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print("• маркер уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    ok = True
    for label, old, _new in BLOCKS:
        n = text.count(old)
        status = "✓" if n == 1 else "✗"
        print(f"  {status} якорь [{label}]: найден {n} раз (нужно ровно 1)")
        if n != 1:
            ok = False
    if not ok:
        print("✗ якоря не сошлись — файл отличается от ожидаемого. Ничего не режу.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_name(TARGET.name + f".bak_{ts}")
    shutil.copy2(TARGET, bak)
    print(f"• бэкап: {bak.name}")

    for _label, old, new in BLOCKS:
        text = text.replace(old, new, 1)
    text += EOF_MARKER

    TARGET.write_text(text, encoding="utf-8")
    print("• правки внесены (10 блоков)")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}\n  Файл откатан из бэкапа.")
        sys.exit(1)

    print()
    print("  ГОТОВО: все 9 агентов Совета грузятся из мозг.py по Закону")
    print("  Картриджа, как в ui_torg.py. Поведение при сбое то же самое")
    print("  (loud crash через finally) — только сообщение теперь честное:")
    print("  \"мозг A0X ещё не в слоте\", а не ModuleNotFoundError в пустоту.")
    print("═" * 62)


if __name__ == "__main__":
    main()
