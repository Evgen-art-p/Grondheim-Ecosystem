# -*- coding: utf-8 -*-
# PRIBORY_V_MOZG_V1
"""
В СТОЛ ТРЕЙДЕРА ЛОЖАТСЯ ПРИБОРЫ, А НЕ ВЫВОДЫ.

    python patch_pribory_v_mozg.py --suho
    python patch_pribory_v_mozg.py

Запускать из КОРНЯ репо, после postavit_stol_i_glaz.py.

ЗАЧЕМ (слово Шефа 07.08)
    «То, что ты посчитал код готовый, он не будет работать.»

    И верно: код находил разворотный бар, считал согласие с водой,
    объявлял фрактал действительным — а трейдеру оставалось кивнуть.
    Выбирать нечего, смотреть незачем. Бот с характером.

ЧТО МЕНЯЕТСЯ
    Блок «sensors» в столе был набором ВЫВОДОВ. Теперь на его месте
    блок «приборы» — голые показания: где линии Аллигатора и в каком
    они порядке, спит ли пасть, какое значение у AO и растёт ли оно,
    где ОБА последних фрактала, какое окно объёма, какое натяжение.

    Что всё это значит, говорит трейдер, глядя на кадр.

ЧТО НЕ МЕНЯЕТСЯ
    Дневник, ведение позиции, вердикт, блок «market», характер роли —
    не тронуты. Меняется одна вставка на мозг.
"""
import argparse, ast, py_compile, shutil, sys
from pathlib import Path

MARKER = "PRIBORY_V_MOZG_V1"
CEHA = Path("GRONDHEIM_CITY") / "Биржа" / "цеха"

A_OLD = '''        "sensors": {
            "iskra":  {k: table["iskra"].get(k) for k in
                       ("t1_status", "zero_point_price", "trend_direction",
                        "dlina", "struktura_chitaetsya")},
            "morj":   {k: table["morj"].get(k) for k in
                       ("morj_status", "wave_1_validated", "tension_peak")},
            "panic":  {k: table["panic"].get(k) for k in
                       ("panic_phase", "crowd_sentiment")},
            "hans":   {k: table["hans"].get(k) for k in
                       ("fractal_valid", "fractal_side", "fractal_price")},
            "arkhiv": table.get("arkhiv", {}),
        },
'''

A_NEW = '''        # PRIBORY_V_MOZG_V1: здесь были ВЫВОДЫ сенсоров — «бар найден»,
        # «согласен с водой», «фрактал действителен». Их больше нет:
        # код не решает за трейдера. Теперь голые показания приборов, а
        # что они значат — говорит он сам, глядя на кадр.
        "приборы": table.get("приборы", {}),
        "arkhiv": table.get("arkhiv", {}),
'''


def pravit(mozg: Path, suho: bool) -> str:
    src = mozg.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже"
    if src.count(A_OLD) != 1:
        return "мимо"
    novyy = src.replace(A_OLD, A_NEW, 1)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        return f"ошибка: {e}"
    if suho:
        return "ок"
    bak = mozg.with_suffix(".py.bak_pribory")
    if not bak.exists():
        shutil.copy2(mozg, bak)
    mozg.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(mozg), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, mozg)
        return f"ошибка: py_compile — {e}"
    return "ок"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()
    if not CEHA.exists():
        print("✗ это не корень репо")
        return 1
    print("ПРИБОРЫ ВМЕСТО ВЫВОДОВ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print()
    itogo = {"ок": 0, "уже": 0, "мимо": 0}
    for mozg in sorted(CEHA.glob("*/слоты/*/мозг.py")):
        r = pravit(mozg, a.suho)
        if r.startswith("ошибка"):
            print(f"  ✗ {mozg.parent.name}: {r}")
            return 1
        itogo[r] = itogo.get(r, 0) + 1
        if r != "мимо":
            print(f"  {'·' if r == 'ок' else '='} {mozg.parent.name} — {r}")
    print(f"\n✓ поправлено {itogo['ок']}, уже стояло {itogo['уже']}, "
          f"без этой строки {itogo['мимо']}")
    if not a.suho:
        print("\n  Рядом с каждым мозгом лежит .bak_pribory.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
