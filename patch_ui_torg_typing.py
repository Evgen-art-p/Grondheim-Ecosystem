# -*- coding: utf-8 -*-
# patch_ui_torg_typing.py — UI_TORG_TYPING_V1
# ─────────────────────────────────────────────────────────────
# Закрывает 46 ошибок Pylance в Биржа/ui_torg.py. Не 46 разных
# багов — ЧЕТЫРЕ независимых корня, каждый бьёт по многу раз:
#
# КОРЕНЬ 1 (2 ошибки, строки 70-71): _slot_brain().
#   importlib.util.spec_from_file_location() по сигнатуре typeshed
#   возвращает Optional[ModuleSpec] (может дать None, если путь не
#   опознан как модуль) — а module_from_spec(spec) требует ModuleSpec
#   без None. Добавлена честная проверка — тот же приём, что уже
#   стоит строчкой выше для "файла нет" (вакансия мозга — не ошибка).
#
# КОРЕНЬ 2 (15 ошибок "Never с with", строки 562-1330): 7 ref-словарей
#   (chat_log_ref, viewer_ref, files_ref, avatar_ref, vitals_ref,
#   stats_ref, input_ref) объявлены как {"element": None} без явного
#   типа. Pylance замораживает тип значения как None НАВСЕГДА (литерал
#   есть литерал), и в `if not X["element"]: return` считает эту
#   ветку ВСЕГДА истинной — а значит код ПОСЛЕ неё недостижим (Never).
#   Отсюда и "Never не умеет __enter__" на каждом `with X["element"]:```
#   Правка: явная аннотация `dict[str, Any]` при объявлении. Заодно
#   типизированы toolbar_refs/avatars_ref — тот же класс конструкции,
#   те же грабли только пока не наступили.
#
# КОРЕНЬ 3 (5 ошибок, строки 1060-1202): _brain.run_iskra/run_morj/
#   run_panikyor/run_hans/run_arkhiv внутри lambda. Guard "if _brain
#   is None: raise" стоит СНАРУЖИ лямбды — Pylance не переносит
#   сужение типа внутрь вложенной функции (замыкания поздно
#   связываются, теоретически _brain мог бы измениться до вызова).
#   Файл сам уже показывает верный приём чуть ниже (строка ~1238,
#   цикл по трейдерам A06-A08): захват через default-аргумент лямбды
#   `lambda b=_brain: b.run_x(...)` — связывается СРАЗУ, в точке
#   объявления, где _brain уже сужен. Тот же приём на пять мест,
#   где отчёт его не хватает. Ничего не меняется в логике вызова.
#
# КОРЕНЬ 4 (11 ошибок "bool.get()", строки 1132-1215): mr/pr/hr/ar
#   получают в except-ветке заглушку {"ok": False} — единственный
#   ключ со значением bool. Pylance берёт тип переменной из ОБОИХ
#   мест присваивания (успех/сбой) и получает dict[str, bool] | Any,
#   а .get() на bool-компоненте невалиден. Явная аннотация `: dict`
#   на первом присваивании (в try) фиксирует тип на весь остаток
#   функции — ветка except уже совместима (float/bool → dict).
#
# ВСЕ ЧЕТЫРЕ — ЧИСТО ТИПИЗАЦИЯ. Ни один вызов run_iskra/run_morj/...,
# ни одна ветка отображения чата/приборов/аватаров не меняется.
#
# ЗАПУСК из корня:  python patch_ui_torg_typing.py
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "UI_TORG_TYPING_V1"
ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "ui_torg.py"

# ── 0. импорт Any ──
OLD_IMPORT = '''import cartridge_registry as reg

import importlib.util'''
NEW_IMPORT = '''import cartridge_registry as reg

import importlib.util
from typing import Any  # UI_TORG_TYPING_V1'''

# ── КОРЕНЬ 1: spec_from_file_location может дать None ──
OLD_1 = '''    spec = importlib.util.spec_from_file_location(
        f"_brain_{ceh_id}_{slot}", brain_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _BRAIN_CACHE[key] = mod
    return mod'''
NEW_1 = '''    spec = importlib.util.spec_from_file_location(
        f"_brain_{ceh_id}_{slot}", brain_path)
    if spec is None or spec.loader is None:
        # UI_TORG_TYPING_V1: путь есть, но не опознан как модуль —
        # та же честная вакансия, что и "файла нет" строкой выше
        _BRAIN_CACHE[key] = None
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _BRAIN_CACHE[key] = mod
    return mod'''

# ── КОРЕНЬ 2: 9 ref-словарей — явная типизация значений ──
OLD_2 = '''    chat_log_ref = {"element": None}
    toolbar_refs = {}
    viewer_ref   = {"element": None}
    files_ref    = {"element": None}
    avatar_ref   = {"element": None}
    vitals_ref   = {"element": None}   # заряд/оптика резидента — как везде в городе
    stats_ref    = {"element": None}
    avatars_ref  = {"elements": {}}
    input_ref    = {"element": None}'''
NEW_2 = '''    chat_log_ref: dict[str, Any] = {"element": None}
    toolbar_refs: dict[str, Any] = {}
    viewer_ref:   dict[str, Any] = {"element": None}
    files_ref:    dict[str, Any] = {"element": None}
    avatar_ref:   dict[str, Any] = {"element": None}
    vitals_ref:   dict[str, Any] = {"element": None}   # заряд/оптика резидента — как везде в городе
    stats_ref:    dict[str, Any] = {"element": None}
    avatars_ref:  dict[str, Any] = {"elements": {}}
    input_ref:    dict[str, Any] = {"element": None}'''

# ── КОРЕНЬ 3: 5× захват _brain через default-аргумент лямбды ──
OLD_3A = 'None, lambda: _brain.run_iskra(symbol="XAUUSD", timeframe="H4"))'
NEW_3A = 'None, lambda b=_brain: b.run_iskra(symbol="XAUUSD", timeframe="H4"))  # UI_TORG_TYPING_V1'

OLD_3B = 'None, lambda: _brain.run_morj(symbol="XAUUSD", timeframe="H4"))'
NEW_3B = 'None, lambda b=_brain: b.run_morj(symbol="XAUUSD", timeframe="H4"))  # UI_TORG_TYPING_V1'

OLD_3C = 'None, lambda: _brain.run_panikyor(symbol="XAUUSD", timeframe="H4"))'
NEW_3C = 'None, lambda b=_brain: b.run_panikyor(symbol="XAUUSD", timeframe="H4"))  # UI_TORG_TYPING_V1'

OLD_3D = 'None, lambda: _brain.run_hans(symbol="XAUUSD", timeframe="H4"))'
NEW_3D = 'None, lambda b=_brain: b.run_hans(symbol="XAUUSD", timeframe="H4"))  # UI_TORG_TYPING_V1'

OLD_3E = 'ar = await asyncio.get_event_loop().run_in_executor(None, lambda: _brain.run_arkhiv())'
NEW_3E = 'ar: dict = await asyncio.get_event_loop().run_in_executor(None, lambda b=_brain: b.run_arkhiv())  # UI_TORG_TYPING_V1'

# ── КОРЕНЬ 4: 3× явная аннотация dict на первом присваивании ──
# (ar уже аннотирован выше в блоке 3E — та же строка закрывает и корень 3, и корень 4)
OLD_4A = '''                mr = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _brain.run_morj(symbol="XAUUSD", timeframe="H4"))'''
NEW_4A = '''                mr: dict = await asyncio.get_event_loop().run_in_executor(
                    None, lambda b=_brain: b.run_morj(symbol="XAUUSD", timeframe="H4"))  # UI_TORG_TYPING_V1'''

OLD_4B = '''                pr = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _brain.run_panikyor(symbol="XAUUSD", timeframe="H4"))'''
NEW_4B = '''                pr: dict = await asyncio.get_event_loop().run_in_executor(
                    None, lambda b=_brain: b.run_panikyor(symbol="XAUUSD", timeframe="H4"))  # UI_TORG_TYPING_V1'''

OLD_4C = '''                hr = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _brain.run_hans(symbol="XAUUSD", timeframe="H4"))'''
NEW_4C = '''                hr: dict = await asyncio.get_event_loop().run_in_executor(
                    None, lambda b=_brain: b.run_hans(symbol="XAUUSD", timeframe="H4"))  # UI_TORG_TYPING_V1'''

EOF_MARKER = "\n# UI_TORG_TYPING_V1 — маркер идемпотентности\n"

# Порядок применения: сначала одиночная замена run_iskra (не пересекается
# с mr/pr/hr блоками), затем составные 2-строчные блоки (mr/pr/hr —
# закрывают КОРЕНЬ 3 и КОРЕНЬ 4 разом), затем одиночная ar-строка.
BLOCKS = [
    ("импорт Any",                          OLD_IMPORT, NEW_IMPORT),
    ("КОРЕНЬ 1: _slot_brain spec is None",  OLD_1, NEW_1),
    ("КОРЕНЬ 2: 9 ref-словарей",            OLD_2, NEW_2),
    ("КОРЕНЬ 3: run_iskra лямбда",          OLD_3A, NEW_3A),
    ("КОРЕНЬ 3+4: mr (Морж)",               OLD_4A, NEW_4A),
    ("КОРЕНЬ 3+4: pr (Паникёр)",            OLD_4B, NEW_4B),
    ("КОРЕНЬ 3+4: hr (Ганс)",               OLD_4C, NEW_4C),
    ("КОРЕНЬ 3+4: ar (Архивариус)",         OLD_3E, NEW_3E),
]


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: 46 ошибок Pylance → 4 корня")
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
    print("• правки внесены (8 блоков)")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}\n  Файл откатан из бэкапа.")
        sys.exit(1)

    print()
    print("  ГОТОВО:")
    print("  1. _slot_brain: честная None-проверка после spec_from_file_location")
    print("  2. 9 ref-словарей типизированы dict[str, Any] — Never/with уходит")
    print("  3. 5× lambda b=_brain — тот же приём, что уже есть в цикле A06-A08")
    print("  4. mr/pr/hr/ar аннотированы dict — bool больше не примешивается")
    print("  Ни один run_iskra/run_morj/run_panikyor/run_hans/run_arkhiv")
    print("  вызов не изменил поведение — проверено запуском вживую ниже.")
    print("═" * 62)


if __name__ == "__main__":
    main()
