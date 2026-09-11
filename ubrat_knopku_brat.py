# -*- coding: utf-8 -*-
# UBRAT_KNOPKU_BRAT_V1
"""
КНОПКА «← БРАТ» УХОДИТ ИЗ КАБИНЕТА БИРЖИ

Слово Шефа 11.09: она там не используется — в главный кабинет
возвращает кнопка «← Город», а эта просто занимает место рядом с
«ОЧИСТИТЬ» и наезжает на него взглядом.

ЧТО ДЕЛАЕТ ПАТЧ. Убирает кнопку и пустой ряд, в котором она одна и
стояла. Ничего больше не трогает: «← Город» на месте, переход к
Брату остаётся через город.

БЕЗОПАСНОСТЬ: .bak_brat, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python ubrat_knopku_brat.py --suho
    python ubrat_knopku_brat.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "UBRAT_KNOPKU_BRAT_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

STAROE = '''                    with ui.row().style("gap:8px; justify-content:flex-end;"):
                        ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat", new_tab=True)).props("flat").style(
                            "padding:6px 14px; border-radius:8px; font-size:12px; "
                            "background:rgba(99,130,255,0.08); border:1px solid rgba(99,130,255,0.25); "
                            "color:rgba(180,190,220,0.8);")
'''

NOVOE = '''                    # UBRAT_KNOPKU_BRAT_V1: кнопка «← Брат» убрана по
                    # слову Шефа — не использовалась и жалась к
                    # «ОЧИСТИТЬ». К Брату ходим через город.
'''


def main():
    print()
    print("УБРАТЬ КНОПКУ «БРАТ»" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()
    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")
    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if txt.count(STAROE) != 1:
        print(f"!! якорь встречается {txt.count(STAROE)} раз(а) — не трогаю")
        return
    novy = txt.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    print("  кнопка и пустой ряд — убраны")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_brat"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_brat")
    print()


if __name__ == "__main__":
    main()
