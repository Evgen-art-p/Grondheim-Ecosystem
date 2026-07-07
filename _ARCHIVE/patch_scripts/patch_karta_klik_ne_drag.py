# -*- coding: utf-8 -*-
"""
PATCH: КАРТА · КЛИК НЕ ГЛОТАЕТСЯ ПЕРЕТАСКИВАНИЕМ — точка жителя
исключена из drag-логики карты, как здания.
Маркер: KARTA_KLIK_NE_DRAG_V1

НАЙДЕННАЯ ПРИЧИНА (не гадание — сверено с самим JS): pointerdown на
viewport запускает перетаскивание карты для ЛЮБОГО клика, КРОМЕ клика
по `.grond-sector` (зданию) — та строка написана явно:

    if(e.target.closest('.grond-sector')) return;

Точка жителя (`.grond-zhitel` / `.grond-zhitel--active`) под это
исключение не попадала. Клик по ней сначала ловил pointerdown → карта
захватывала указатель (setPointerCapture) как начало перетаскивания →
клик до onclick не долетал. Ровно та защита, что уже стоит для зданий,
для точек жителей просто забыли поставить.

ЧТО МЕНЯЕМ: одна строка — исключение расширяется на точки жителей,
той же логикой, что уже работает для зданий.

Идемпотентен: если исключение уже включает grond-zhitel — не трогает.

Запуск из корня репо:  python patch_karta_klik_ne_drag.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
TARGET = REPO / "ГОРОД" / "ui_grondheim.py"

ANCHOR = "    if(e.target.closest('.grond-sector')) return;"
INSERT = "    if(e.target.closest('.grond-sector, .grond-zhitel, .grond-zhitel--active')) return;"


def install():
    print("═══ PATCH KARTA_KLIK_NE_DRAG_V1 — клик не глотается перетаскиванием ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "grond-zhitel, .grond-zhitel--active" in src and ANCHOR not in src:
        print("  ○ уже накатано — не трогаю")
        return True

    if ANCHOR not in src:
        print("  ✖ якорь не найден — строка pointerdown-исключения выглядит "
              "иначе. Покажи текущий JS-блок, поправлю точечно.")
        return False

    src = src.replace(ANCHOR, INSERT)

    try:
        ast.parse(src)  # файл всё ещё .py, JS внутри строки — но пусть Python не сломался
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ pointerdown теперь пропускает клик и по точкам жителей")
    print("  ✔ синтаксис чист")
    print("\n  Обнови /grondheim (полная перезагрузка страницы, не просто")
    print("  клик — JS уже был загружен старым в браузере) — клик по точке")
    print("  теперь долетает до onclick, а не ловится перетаскиванием.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
