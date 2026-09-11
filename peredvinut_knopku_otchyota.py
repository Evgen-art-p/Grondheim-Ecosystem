# -*- coding: utf-8 -*-
# KNOPKA_OTCHYOTA_K_OCHISTKE_V1
"""
КНОПКА «ОТЧЁТ» ПЕРЕЕЗЖАЕТ К «ОЧИСТИТЬ»

Я поставил её на место кнопки «← Брат» — в отдельный ряд справа. А
там она перекрывается кнопками тестера, когда тот открыт: ровно та
же беда, из-за которой убрали и «← Брат», и надпись «БИРЖА · СОВЕТ».

Слово Шефа: пусть встанет после «ОЧИСТИТЬ», к ним в ряд.

ЧТО ДЕЛАЕТ ПАТЧ. Переносит кнопку в общую панель, сразу за
«ОЧИСТИТЬ», и убирает пустой ряд, который для неё заводился. Вид
кнопки тот же, что у соседей: тот же размер, те же отступы.

ТРЕБУЕТ: STRANICA_OTCHYOTA_V1 (кнопка должна уже существовать).

БЕЗОПАСНОСТЬ: .bak_knopka, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

КУДА КЛАСТЬ ЭТОТ ФАЙЛ: в корень репы, рядом с main.py — как все
патчи. Оттуда же и запускать.

    python peredvinut_knopku_otchyota.py --suho
    python peredvinut_knopku_otchyota.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KNOPKA_OTCHYOTA_K_OCHISTKE_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

# 1. ставим кнопку в ряд, сразу за ОЧИСТИТЬ
STAROE_RYAD = '''                        _clean_btn.on("click", lambda: _ochistit_istoriyu())
                        with _clean_btn:
                            ui.html("🧹 ОЧИСТИТЬ")'''

NOVOE_RYAD = '''                        _clean_btn.on("click", lambda: _ochistit_istoriyu())
                        with _clean_btn:
                            ui.html("🧹 ОЧИСТИТЬ")
                        # KNOPKA_OTCHYOTA_K_OCHISTKE_V1: отчёт — сюда же.
                        # Справа в своём ряду его перекрывали кнопки
                        # тестера, как раньше «← Брат» и надпись Биржи.
                        _otchyot_btn = ui.element("div").style(
                            "display:flex;align-items:center;"
                            "padding:6px 14px;border-radius:7px;"
                            "font-size:12px;font-weight:700;cursor:pointer;"
                            "background:rgba(99,130,255,0.08);"
                            "color:rgba(150,175,255,0.85);"
                            "border:1px solid rgba(99,130,255,0.3);")
                        _otchyot_btn.on("click", lambda: ui.navigate.to(
                            f"/otchyot/{tseh_id}", new_tab=True))
                        with _otchyot_btn:
                            ui.html("📄 ОТЧЁТ")'''

# 2. убираем прежний ряд справа
STAROE_STARYY = '''                    # STRANICA_OTCHYOTA_V1: на её место — отчёт прогона.
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
NOVOE_STARYY = '''                    # KNOPKA_OTCHYOTA_K_OCHISTKE_V1: кнопка отчёта
                    # переехала в общий ряд, к «ОЧИСТИТЬ».
'''


def main():
    print()
    print("КНОПКА ОТЧЁТА — К ОЧИСТИТЬ"
          + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()
    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")
    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if "STRANICA_OTCHYOTA_V1" not in txt:
        print("!! сперва podklyuchit_stranicu_otchyota.py")
        return

    novy = txt
    for imya, st, nv in (("кнопка в ряд", STAROE_RYAD, NOVOE_RYAD),
                         ("прежний ряд убран", STAROE_STARYY, NOVOE_STARYY)):
        if novy.count(st) != 1:
            print(f"  ОТКАЗ на «{imya}» — якорь встречается "
                  f"{novy.count(st)} раз(а), файл не тронут")
            return
        novy = novy.replace(st, nv, 1)
        print(f"  {imya}: сделано")

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_knopka"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_knopka")
    print("Отчёт теперь рядом с ОЧИСТИТЬ, тестер его не перекроет.")
    print()


if __name__ == "__main__":
    main()
