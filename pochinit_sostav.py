# -*- coding: utf-8 -*-
# POCHINIT_SOSTAV_V1
"""
ПОЧИНКА: кабинет падал на `state` до его создания.

ЧТО СЛОМАЛОСЬ (моя ошибка в nastroit_birzhu.py)
    В `page_torg` порядок такой: сперва собирается `roster`, и только
    ПОСЛЕ этого создаётся `state`. А я вписал выбор активного участника
    сразу за сборкой состава — то есть обратился к `state` раньше, чем
    он появился:

        UnboundLocalError: cannot access local variable 'state'

ПОЧИНКА
    Убираю ту вставку и беру первого участника прямо внутри `state` —
    состав к этому моменту уже собран строкой выше, так что и городить
    ничего не нужно.

Запускать из КОРНЯ репо:
    python pochinit_sostav.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "POCHINIT_SOSTAV_V1"
TARGET = Path("Биржа") / "ui_torg.py"
BAK = Path("Биржа") / "ui_torg.py.bak_pochinit_sostav"

A1_OLD = '''    roster = _build_roster(static_prefix)
    # SOSTAV_S_DISKA_V1: активным встаёт первый, кто есть на диске.
    # Пусто в квартале — остаётся пустая строка, кабинет не падает.
    if roster and not state.get("active_agent"):
        state["active_agent"] = roster[0]["old_id"]
'''

A1_NEW = '''    roster = _build_roster(static_prefix)
'''

A2_OLD = '''        # SOSTAV_S_DISKA_V1: кто активен вначале — решается при сборке
        # состава (первый из тех, кто реально есть на диске).
        "active_agent": "",
'''

A2_NEW = '''        # POCHINIT_SOSTAV_V1: активным встаёт первый, кто реально есть
        # на диске. Состав собран строкой выше, поэтому берём прямо
        # здесь — раньше это стояло ДО создания state и роняло кабинет.
        # Пусто в квартале — пустая строка, и ничего не падает.
        "active_agent": (roster[0]["old_id"] if roster else ""),
'''


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — починено, ничего не делаю")
        return 0
    if "SOSTAV_S_DISKA_V1" not in src:
        print("✗ в кабинете нет состава с диска — сначала nastroit_birzhu.py")
        return 1

    novyy = src
    for imya, old, new in (("лишняя вставка после сборки состава", A1_OLD, A1_NEW),
                           ("первый активный внутри state", A2_OLD, A2_NEW)):
        n = novyy.count(old)
        if n != 1:
            print(f"✗ «{imya}»: найдено {n} раз (нужно 1). "
                  f"Файл не тот — ничего не менял.")
            return 1
        novyy = novyy.replace(old, new, 1)
        print(f"  · {imya} — ок")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK.name}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print("\n  Перезапусти кабинет — должен подняться.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
