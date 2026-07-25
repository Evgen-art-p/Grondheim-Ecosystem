# -*- coding: utf-8 -*-
# PATCH_AKADEMIA_GATE_V1 — клик по Замку Сов ведёт в кабинет Академии
"""
Правит ГОРОД/ui_grondheim.py: добавляет 0008_OWL_CASTLE в LOCATION_GATES,
тем же швом, что уже открыт для Биржи (0014_EXCHANGE -> /torg).

После патча клик по Замку Сов на карте /grondheim ведёт на /akademia,
а не в честный паспорт места (ui_lokacia.py) — ровно как у Биржи.

Идемпотентно: если строка уже стоит — молчит и выходит.
Бэкап перед правкой, ast.parse после — не сошлось, файл не пишется.

Запуск ИЗ КОРНЯ РЕПО:
    python patch_akademia_gate_v1.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "ГОРОД" / "ui_grondheim.py"

ANCHOR = '''LOCATION_GATES = {
    "0014_EXCHANGE": "/torg",   # Биржа -> стол Совета (ui_torg.py)
}'''

REPLACEMENT = '''LOCATION_GATES = {
    "0014_EXCHANGE": "/torg",       # Биржа -> стол Совета (ui_torg.py)
    "0008_OWL_CASTLE": "/akademia", # Замок Сов -> кабинет Академии (ui_akademia.py)
}'''


def main():
    print("═══ PATCH_AKADEMIA_GATE_V1 ═══")
    print(f"корень: {ROOT}\n")

    if not TARGET.exists():
        print(f"✗ {TARGET} не найден. Запускай ИЗ КОРНЯ репо.")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if '"0008_OWL_CASTLE"' in src:
        print("= врата уже открыты — 0008_OWL_CASTLE уже в LOCATION_GATES")
        return True

    if ANCHOR not in src:
        print("✗ якорь LOCATION_GATES не найден в ожидаемом виде.")
        print("  Похоже, файл менялся — правь руками одну строку:")
        print('  "0008_OWL_CASTLE": "/akademia",')
        return False

    novyy = src.replace(ANCHOR, REPLACEMENT, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки файл не парсится: {e}")
        print("ФАЙЛ НЕ ЗАПИСАН — ничего не сломано.")
        return False

    bak = TARGET.with_suffix(".py.bak_akademia_gate")
    shutil.copy2(TARGET, bak)
    TARGET.write_text(novyy, encoding="utf-8")
    print(f"✓ бэкап: {bak.name}")
    print("✓ врата открыты: клик по Замку Сов -> /akademia")
    return True


if __name__ == "__main__":
    ok = main()
    print()
    if ok:
        print("✅ ГОТОВО. Запускай python main.py и кликай на Замок Сов на карте /grondheim")
    else:
        print("❌ Не докатилось — смотри сообщения выше.")
    print("`шесть·проверено·до·корня`")
