# -*- coding: utf-8 -*-
# STRANICA_OTCHYOTA_V1
"""
ПОДКЛЮЧИТЬ СТРАНИЦУ ОТЧЁТА

Ставит на место модуль `Биржа/ui_otchyot.py` (его надо положить
рядом с этим патчем) и делает две вещи:

 1. `main.py` — регистрирует страницы:
        /otchyot                 · последний прогон
        /otchyot/{ceh}           · последний прогон этого цеха
        /otchyot/{ceh}/{папка}   · конкретный прогон

 2. `Биржа/ui_torg.py` — кнопка «📄 ОТЧЁТ» в шапке кабинета, на
    освободившееся место кнопки «← Брат».

Страница ничего не пересчитывает: читает `места.jsonl` и подпапку
`кадры`, которые отчёт уже пишет сам.

БЕЗОПАСНОСТЬ: .bak_otchyot, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python podklyuchit_stranicu_otchyota.py --suho
    python podklyuchit_stranicu_otchyota.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "STRANICA_OTCHYOTA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
MAIN = _REPO / "main.py"
TORG = _REPO / "Биржа" / "ui_torg.py"
MODUL_SYUDA = _REPO / "Биржа" / "ui_otchyot.py"
MODUL_OTSYUDA = _REPO / "ui_otchyot.py"

STAROE_MAIN = '''@ui.page("/torg")
def _torg0():
    page_torg()'''

NOVOE_MAIN = '''@ui.page("/torg")
def _torg0():
    page_torg()


# ── STRANICA_OTCHYOTA_V1: отчёт прогона — кадр и разбор рядом ──
# В консоли никто разбираться не будет, в папках тем более. Здесь
# каждое место видно глазами: кадр того бара и что он про него сказал.
from ui_otchyot import page_otchyot

@ui.page("/otchyot")
def _otchyot0():
    page_otchyot()

@ui.page("/otchyot/{ceh}")
def _otchyot1(ceh: str = "торговый_хаос"):
    page_otchyot(ceh)

@ui.page("/otchyot/{ceh}/{papka}")
def _otchyot2(ceh: str = "торговый_хаос", papka: str = ""):
    page_otchyot(ceh, papka)'''

STAROE_TORG = '''                    # UBRAT_KNOPKU_BRAT_V1: кнопка «← Брат» убрана по
                    # слову Шефа — не использовалась и жалась к
                    # «ОЧИСТИТЬ». К Брату ходим через город.
'''

NOVOE_TORG = '''                    # UBRAT_KNOPKU_BRAT_V1: кнопка «← Брат» убрана по
                    # слову Шефа — не использовалась и жалась к
                    # «ОЧИСТИТЬ». К Брату ходим через город.
                    # STRANICA_OTCHYOTA_V1: на её место — отчёт прогона.
                    with ui.row().style("gap:8px; justify-content:flex-end;"):
                        ui.button(
                            "📄 ОТЧЁТ",
                            on_click=lambda: ui.navigate.to(
                                f"/otchyot/{tseh_id}", new_tab=True)
                        ).props("flat").style(
                            "padding:6px 14px; border-radius:8px; "
                            "font-size:12px; "
                            "background:rgba(99,130,255,0.08); "
                            "border:1px solid rgba(99,130,255,0.25); "
                            "color:rgba(180,190,220,0.8);")
'''


def main():
    print()
    print("СТРАНИЦА ОТЧЁТА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    print("1. МОДУЛЬ Биржа/ui_otchyot.py:")
    if not MODUL_OTSYUDA.exists() and not MODUL_SYUDA.exists():
        print("  !! положи ui_otchyot.py рядом с патчем — без него никак")
        return
    if MODUL_OTSYUDA.exists():
        if not SUHO:
            MODUL_SYUDA.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(MODUL_OTSYUDA, MODUL_SYUDA)
        print(f"  {'лёг бы' if SUHO else 'положен'} в Биржа/")
    else:
        print("  уже на месте")

    vsego = 0
    print()
    print("2. MAIN — страницы зарегистрированы:")
    if not MAIN.exists():
        print("  main.py: файла нет")
    else:
        txt = MAIN.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  main.py: уже стоит")
        elif txt.count(STAROE_MAIN) != 1:
            print(f"  main.py: ОТКАЗ — якорь встречается "
                  f"{txt.count(STAROE_MAIN)} раз(а)")
        else:
            novy = txt.replace(STAROE_MAIN, NOVOE_MAIN, 1)
            try:
                ast.parse(novy)
                if not SUHO:
                    shutil.copy2(MAIN, MAIN.with_suffix(".py.bak_otchyot"))
                    MAIN.write_text(novy, encoding="utf-8")
                print(f"  main.py: {'готов' if SUHO else 'поправлен'}")
                vsego += 1
            except SyntaxError as e:
                print(f"  main.py: ОТКАЗ — синтаксис сломан ({e})")

    print()
    print("3. КАБИНЕТ — кнопка «ОТЧЁТ»:")
    if not TORG.exists():
        print("  ui_torg.py: файла нет")
    else:
        txt = TORG.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  ui_torg.py: уже стоит")
        elif txt.count(STAROE_TORG) != 1:
            print("  ui_torg.py: ОТКАЗ — сперва ubrat_knopku_brat.py")
        else:
            novy = txt.replace(STAROE_TORG, NOVOE_TORG, 1)
            try:
                ast.parse(novy)
                if not SUHO:
                    shutil.copy2(TORG, TORG.with_suffix(".py.bak_otchyot"))
                    TORG.write_text(novy, encoding="utf-8")
                print(f"  ui_torg.py: {'готов' if SUHO else 'поправлен'}")
                vsego += 1
            except SyntaxError as e:
                print(f"  ui_torg.py: ОТКАЗ — синтаксис сломан ({e})")

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_otchyot")
    print("Кнопка «ОТЧЁТ» в шапке кабинета, рядом с ОЧИСТИТЬ.")
    print()


if __name__ == "__main__":
    main()
