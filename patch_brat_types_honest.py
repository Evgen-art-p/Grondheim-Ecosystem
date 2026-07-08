# -*- coding: utf-8 -*-
"""
PATCH: ui_brat · ЧЕСТНЫЕ ТИПЫ — та же болезнь, что в ui_zhitel, x3.
Маркер: BRAT_TYPES_HONEST_V1

НАЙДЕНО: 19 ошибок Pylance — но это ОДНА болезнь в трёх словарях, не 19
разных проблем. Ровно то же, что чинили в ui_zhitel.py:

    refs = {"chat": None, "viewer": None, "input": None, "files": None}
    pick = {"zhitel": None, "tip": None}          (в do_naznachit_rol)
    pick = {"zhitel": None, "lokacia": None}       (в do_propiska)

Каждый словарь стартует значениями None → pyright решает "здесь ВСЕГДА
None" → потом ругается на всё, что туда реально кладём (Element, str,
Input, dict-объект жителя). Код при этом абсолютно рабочий — врёт
только вывод типа при создании словаря.

ЛЕЧЕНИЕ: аннотировать каждый словарь как dict — "значения любые", не
"значения None". Не подавление — честное объявление того, чем словарь
и так является по факту использования.

Идемпотентен. Запуск из корня репо:  python patch_brat_types_honest.py
"""
import sys
import io
import ast
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Брат" / "ui_brat.py"

FIXES = [
    (
        '    refs  = {"chat": None, "viewer": None, "input": None, "files": None}',
        '    refs: dict = {"chat": None, "viewer": None, "input": None, "files": None}',
    ),
    (
        '        pick = {"zhitel": None, "tip": None}',
        '        pick: dict = {"zhitel": None, "tip": None}',
    ),
    (
        '        pick = {"zhitel": None, "lokacia": None}',
        '        pick: dict = {"zhitel": None, "lokacia": None}',
    ),
]


def install():
    print("═══ PATCH BRAT_TYPES_HONEST_V1 — честные типы ui_brat ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "BRAT_TYPES_HONEST_V1" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    done, missed = 0, []
    for old, new in FIXES:
        if new in src:
            done += 1
            continue
        if old not in src:
            missed.append(old.strip()[:50])
            continue
        src = src.replace(old, new, 1)
        done += 1

    if missed:
        for m in missed:
            print(f"  ✖ якорь не найден: {m}...")
        print("  ✖ файл отличается от ожидаемого — останавливаюсь.")
        return False

    src += "\n# BRAT_TYPES_HONEST_V1 — маркер идемпотентности\n"

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print(f"  ✔ применено правок: {done} (из 3 словарей)")
    print("  ✔ синтаксис чист")
    print("\n  Проверь: pyright Брат/ui_brat.py")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
