# -*- coding: utf-8 -*-
"""
PATCH: КАРТА · КЛИК ПО ЖИТЕЛЮ — точка ведёт в живую карточку.
Маркер: KARTA_KLIK_ZHITEL_V1

ЗАМЫСЕЛ (сверено со старым кабинетом, studio/cabinet/ui_cabinet.py):
клик по точке-агенту на карте старого города → cabSelectAgent(id,dept)
→ emitEvent('cab-agent-select') → select_agent() → открывает панель
агента В ТЕКУЩЕМ СОСТОЯНИИ (chat, DNA, стресс — что есть, то и видно).

НОВЫЙ ГОРОД устроен страницами, не панелями (клик по локации уже
делает ui.navigate.to(f"/lokacia/{id}") — тот же принцип, другой
механизм отображения). У жителя уже есть готовая живая карточка —
/zhitel/{zid} (жители/ui_zhitel.py): чат, DNA, фон по прописке/маске.
Это и есть "агент в активном состоянии" нового города — просто другой
маршрут. Патч соединяет точку с этим маршрутом, ничего не выдумывая
нового.

ЧТО ДЕЛАЕТ:
  1. JS: window.grondOpenZhitel(zid) — параллельно grondOpen, тот же
     механизм emitEvent, другой канал ('grond-zhitel-open').
  2. Точка получает onclick + cursor:pointer (сейчас кликать нельзя
     было — только hover-подсказка).
  3. Python: ui.on("grond-zhitel-open", ...) → ui.navigate.to(f"/zhitel/{zid}")

Идемпотентен: если "grondOpenZhitel" уже есть — не трогает файл.
Требует: patch_karta_zhiteli.py уже накатан (иначе нет функции точек).

Запуск из корня репо:  python patch_karta_klik_zhitel.py
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

# ── Якорь 1: JS-функция открытия локации → добавляем рядом функцию для жителя
ANCHOR_JS = "  window.grondOpen = function(locId){ emitEvent('grond-open', locId); };"
INSERT_JS = (ANCHOR_JS +
            "\n  window.grondOpenZhitel = function(zid){ emitEvent('grond-zhitel-open', zid); };")

# ── Якорь 2: разметка точки — добавляем onclick, точка становится кликабельной
ANCHOR_TOCHKA = '''            points += (
                '<div class="%s" title="%s" '
                'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;"></div>'
                % (cls, title, px, py, dot, dot)
            )'''
INSERT_TOCHKA = '''            points += (
                '<div class="%s" title="%s" '
                'onclick="window.grondOpenZhitel && window.grondOpenZhitel(\\'%s\\')" '
                'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;"></div>'
                % (cls, title, _esc(z["id"]), px, py, dot, dot)
            )'''

# ── Якорь 3: обработчик открытия локации — добавляем обработчик жителя рядом
ANCHOR_ON_OPEN = '''    def on_open(e):
        loc_id = e.args
        if loc_id:
            # клик по локации -> открыть её страницу (ui_lokacia.py)
            ui.navigate.to(f"/lokacia/{loc_id}")

    ui.on("grond-open", on_open)'''
INSERT_ON_OPEN = '''    def on_open(e):
        loc_id = e.args
        if loc_id:
            # клик по локации -> открыть её страницу (ui_lokacia.py)
            ui.navigate.to(f"/lokacia/{loc_id}")

    def on_open_zhitel(e):
        zid = e.args
        if zid:
            # клик по жителю -> живая карточка (ui_zhitel.py), в текущем
            # состоянии — та же логика, что select_agent() в старом
            # кабинете, только страницей, не панелью
            ui.navigate.to(f"/zhitel/{zid}")

    ui.on("grond-open", on_open)
    ui.on("grond-zhitel-open", on_open_zhitel)'''

# ── Якорь 4: cursor у точки — сейчас default (не намекает на клик)
ANCHOR_CSS_1 = '''.grond-zhitel{
  position: absolute; border-radius: 50%; z-index: 3; box-sizing: border-box;
  background: rgba(80,250,123,0.85);
  border: 1px solid rgba(80,250,123,0.5);
  transition: transform 0.15s, box-shadow 0.15s;
}'''
INSERT_CSS_1 = '''.grond-zhitel{
  position: absolute; border-radius: 50%; z-index: 3; box-sizing: border-box;
  background: rgba(80,250,123,0.85);
  border: 1px solid rgba(80,250,123,0.5);
  transition: transform 0.15s, box-shadow 0.15s;
  cursor: pointer;
}'''
ANCHOR_CSS_2 = '''.grond-zhitel--active{
  position: absolute; border-radius: 50%; z-index: 4; box-sizing: border-box;
  background: rgba(201,168,76,0.85);
  border: 1px solid rgba(201,168,76,0.6);
  animation: grondPulseWalk 1.5s infinite;
}'''
INSERT_CSS_2 = '''.grond-zhitel--active{
  position: absolute; border-radius: 50%; z-index: 4; box-sizing: border-box;
  background: rgba(201,168,76,0.85);
  border: 1px solid rgba(201,168,76,0.6);
  animation: grondPulseWalk 1.5s infinite;
  cursor: pointer;
}'''


def install():
    print("═══ PATCH KARTA_KLIK_ZHITEL_V1 — клик по жителю ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "grondOpenZhitel" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    if "_tochki_zhitelej_html" not in src:
        print("  ✖ patch_karta_zhiteli.py ещё не накатан — сначала он")
        return False

    anchors = [
        ("JS-функция", ANCHOR_JS), ("разметка точки", ANCHOR_TOCHKA),
        ("обработчик открытия", ANCHOR_ON_OPEN),
    ]
    for name, a in anchors:
        if a not in src:
            print(f"  ✖ якорь «{name}» не найден — файл менялся руками, "
                  f"останавливаюсь. Покажи текущий файл, поправлю точечно.")
            return False

    src = src.replace(ANCHOR_JS, INSERT_JS)
    src = src.replace(ANCHOR_TOCHKA, INSERT_TOCHKA)
    src = src.replace(ANCHOR_ON_OPEN, INSERT_ON_OPEN)
    # CSS-курсор — необязательные якоря (могут отличаться после patch_karta_cvet.py
    # или не быть накатаны вовсе); правим если найдены, не падаем если нет.
    if ANCHOR_CSS_1 in src:
        src = src.replace(ANCHOR_CSS_1, INSERT_CSS_1)
    if ANCHOR_CSS_2 in src:
        src = src.replace(ANCHOR_CSS_2, INSERT_CSS_2)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ точка кликабельна -> /zhitel/{id} (живая карточка)")
    print("  ✔ синтаксис чист")
    print("\n  Клик по любой точке жителя открывает его карточку —")
    print("  чат, якоря, DNA, фон по текущей прописке/маске.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
