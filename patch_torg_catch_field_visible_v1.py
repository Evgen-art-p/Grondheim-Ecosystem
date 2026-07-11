# -*- coding: utf-8 -*-
"""
patch_torg_catch_field_visible_v1.py
────────────────────────────────────────────────────────────────────
ЧИНИТ: поле «ловить: N» в режиме ТЕСТЕР рисуется схлопнутым — числа
не видно (при этом значение в state доходит: тестер честно ловит N).

ДВА ВЕРОЯТНЫХ ВИНОВНИКА В ТЕКУЩЕМ ВИДЖЕТЕ:
  1) format="%d" — в этой связке NiceGUI/Quasar форматтер на float-
     значении (1.0) может отрисовать ПУСТО, хотя модель = 1. Отсюда
     «число читается, но глазом пусто».
  2) props("dense borderless") + width:60px — коробка без рамки схло-
     пывается, спиннер/паддинги съедают ширину, значение клипается.

ЛЕЧЕНИЕ (только сам ui.number, привязку _on_bars_change НЕ трогаю):
  • убираю format="%d" (пусть показывает целое как есть);
  • borderless → outlined — видимая коробка, как в старой студии;
  • input-style — гарантированно красит и центрирует само число;
  • ширину 60 → 78, чтобы значение и спиннер помещались.

Идемпотентно. Маркер CATCH_FIELD_VISIBLE_V1. Бэкап рядом (.bak).
Запуск из КОРНЯ репы (Windows/PowerShell):
    python patch_torg_catch_field_visible_v1.py
"""
from __future__ import annotations
import sys
from pathlib import Path

MARKER = "CATCH_FIELD_VISIBLE_V1"
TARGET = Path("Биржа") / "ui_torg.py"

OLD = (
    '                            _bi = ui.number(\n'
    '                                value=1, min=1, max=999, format="%d",\n'
    '                                on_change=_on_bars_change,   # штатный API NiceGUI, не сырое quasar-событие\n'
    '                            ).props("dense borderless").style(\n'
    '                                "width:60px;font-family:JetBrains Mono;font-size:12px;color:rgba(0,204,255,0.9);")\n'
)

NEW = (
    '                            _bi = ui.number(\n'
    '                                value=1, min=1, max=999,\n'
    '                                on_change=_on_bars_change,   # штатный API NiceGUI, не сырое quasar-событие\n'
    '                            ).props(  # ' + MARKER + ': видимая коробка + гарантированная отрисовка числа\n'
    "                                'dense outlined '\n"
    "                                'input-style=\"color:rgba(0,204,255,0.95);'\n"
    "                                'font-family:JetBrains Mono;font-size:13px;'\n"
    "                                'text-align:center;padding:0 2px;\"'\n"
    '                            ).style("width:78px;")\n'
)


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти из КОРНЯ репы (там, где папка «Биржа»).")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if OLD not in src:
        print("✗ не нашёл ожидаемый блок ui.number поля «ловить».")
        print("  Либо код уже правился вручную, либо не применён "
              "patch_torg_bars_input_onchange_v1. Проверь виджет _bi в "
              "Биржа/ui_torg.py.")
        return 2

    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")
    else:
        print(f"• бэкап уже был: {bak} (не перезаписываю)")

    TARGET.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"✓ {TARGET}: поле «ловить» теперь видимая коробка, число рисуется.")
    print(f"  Маркер идемпотентности: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
