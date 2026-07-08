# -*- coding: utf-8 -*-
"""
PATCH: СТОЛ ЦЕХА — устанавливает /torg/{tseh_id}, стол Совета Биржи.
Маркер: TORG_STOL_V2

Проверено ЖИВЬЮ (не только синтаксисом) — поднят настоящий NiceGUI-сервер,
реальные HTTP-запросы:
  • страница /torg/торговый_хаос → 200, 0 ошибок в логе
  • пузырёк Веры (занятый слот) → class=[occupied, active], аватар нашёлся
  • 8 вакантных пузырьков → class=[vacant], без аватара
  • статика аватарки (/torg-static-.../avatar.png) → 200, отдаётся реально
  • несуществующий цех (/torg/нет_такого) → честный "не найден", не падение

ЧТО ДЕЛАЕТ:
  1. Копирует ui_torg.py в Биржа/ (рядом с cartridge_registry.py, kalibrovka.py)
  2. main.py: добавляет "Биржа" в список папок sys.path (как Брат/жители/ГОРОД)
  3. main.py: регистрирует /torg/{tseh_id} и /torg (по умолчанию торговый_хаос)

ЧЕСТНОСТЬ ЭТОЙ ВЕРСИИ: кнопка РЫНОК зовёт Калибровку (реальный работающий
механизм) — не полный старый Совет (там был Вильямс+LLM+ордера). Полю ввода
"скажи..." пока не с кем говорить — живой чат с резидентом это отдельный,
следующий камень (нужен run_slot + промпты слотов). Layout/визуал — один
в один со старым /exchange (пузырьки-переключатели, стол чат+вьюер+аватар).

Идемпотентен: файл/маршрут уже стоят → пропускает.
Требует: patch_birzha_baza.py и patch_kalibrovka.py уже накатаны.

Запуск из корня репо:  python patch_torg_stol.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
HERE = Path(__file__).resolve().parent
MARKER = "TORG_STOL_V2"


def _load_source(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


MAIN_ANCHOR_PATH = '''for _sub in ("Брат", "жители", "ГОРОД"):'''
MAIN_INSERT_PATH = '''for _sub in ("Брат", "жители", "ГОРОД", "Биржа"):'''

MAIN_ANCHOR_ROUTE = '''if __name__ in {"__main__", "__mp_main__"}:'''
MAIN_INSERT_ROUTE = '''# ── СТОЛ ЦЕХА — Совет Биржи (Закон Пары: слот -> резидент) ── TORG_STOL_V2
# Клик по пузырьку переключает активного; РЫНОК зовёт Калибровку.
from ui_torg import page_torg

@ui.page("/torg/{tseh_id}")
def _torg(tseh_id: str = "торговый_хаос"):
    page_torg(tseh_id)

@ui.page("/torg")
def _torg0():
    page_torg()


if __name__ in {"__main__", "__mp_main__"}:'''


def install():
    print(f"═══ PATCH {MARKER} — стол цеха /torg ═══")
    print(f"репо: {REPO}")

    # 1. ui_torg.py в Биржа/
    birzha_dir = REPO / "Биржа"
    if not birzha_dir.exists():
        print("  ✖ нет папки Биржа/ — накати сначала patch_birzha_baza.py")
        return False
    dst = birzha_dir / "ui_torg.py"
    if dst.exists():
        print("  ○ ui_torg.py уже стоит — не трогаю")
    else:
        dst.write_text(_load_source("ui_torg.py"), encoding="utf-8")
        print("  ✔ создан: Биржа/ui_torg.py")
        try:
            ast.parse(dst.read_text(encoding="utf-8"))
            print("  ✔ синтаксис ui_torg.py чист")
        except SyntaxError as e:
            print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
            return False

    # 2. main.py — путь + маршрут
    main_path = REPO / "main.py"
    if not main_path.exists():
        print("  ✖ main.py не найден в корне")
        return False
    src = main_path.read_text(encoding="utf-8")

    if MARKER in src:
        print("  ○ main.py уже пропатчен (маркер найден) — не трогаю")
        return True

    if MAIN_ANCHOR_PATH not in src or MAIN_ANCHOR_ROUTE not in src:
        print("  ✖ якоря в main.py не найдены — файл менялся, останавливаюсь. "
              "Покажи текущий main.py.")
        return False

    src = src.replace(MAIN_ANCHOR_PATH, MAIN_INSERT_PATH)
    src = src.replace(MAIN_ANCHOR_ROUTE, MAIN_INSERT_ROUTE)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ (main.py): {e}")
        return False

    main_path.write_text(src, encoding="utf-8")
    print("  ✔ main.py: добавлена папка 'Биржа' в sys.path")
    print("  ✔ main.py: маршрут /torg/{tseh_id} зарегистрирован")

    print("\n═══ ИТОГ ═══")
    print("  Открой http://localhost:8080/torg/торговый_хаос")
    print("  Пузырьки — реальный состав цеха (resolve_para), не список в коде.")
    print("  Кнопка РЫНОК — реальная Калибровка (режим+план по сессии).")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
