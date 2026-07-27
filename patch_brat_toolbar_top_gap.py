# -*- coding: utf-8 -*-
"""
patch_brat_toolbar_top_gap.py

Запускать из КОРНЯ репозитория:
    python patch_brat_toolbar_top_gap.py

Что делает:
  Сейчас сверху над кнопкой ГОРОД практически нет отступа (поле
  выровнено по align-items:end, паддинг сверху минимальный).
  Патч добавляет отступ сверху = 20% от высоты самой кнопки (.brat-gate).

  Кнопки НЕ трогает вообще (ни цвет, ни рамку, ни высоту кнопки —
  только padding-top у поля stage-toolbar, где кнопка сидит).

  Как считает: сам находит текущую высоту кнопки (min-height
  в CSS-правиле .brat-gate) — какая бы она сейчас ни была (34px,
  45px или другая, если до этого гулял другой патч), берёт 20% от
  неё и подставляет как padding-top у stage-toolbar. Никаких
  захардкоженных чисел — подстраивается под реальный файл.

Бэкап: Брат/ui_brat.py.bak_before_toolbar_top_gap
"""

import re
import sys
from pathlib import Path

TARGET = Path("Брат") / "ui_brat.py"


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН файл: {TARGET.resolve()}")
        print("Запусти скрипт из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    # 1) находим текущую высоту кнопки в .brat-gate
    gate_match = re.search(r'\.brat-gate\s*\{(.*?)\}', text, re.DOTALL)
    if not gate_match:
        print("Патч НЕ применён — не нашёл CSS-правило .brat-gate.")
        sys.exit(2)
    height_match = re.search(r'min-height\s*:\s*(\d+)\s*px', gate_match.group(1))
    if not height_match:
        print("Патч НЕ применён — не нашёл min-height внутри .brat-gate:")
        print(gate_match.group(0))
        sys.exit(3)
    button_height = int(height_match.group(1))
    new_top = round(button_height * 0.2)
    if new_top < 1:
        new_top = 1

    # 2) находим блок stage-toolbar Брата (маркер — align-items:end, уникален
    #    для этого конкретного inline-style, во всём файле встречается 1 раз)
    marker = "align-items:end !important;"
    if text.count(marker) != 1:
        print(f"Патч НЕ применён — маркер 'align-items:end !important;' "
              f"встречается {text.count(marker)} раз (ожидался 1).")
        sys.exit(4)
    marker_idx = text.find(marker)
    window = text[marker_idx: marker_idx + 400]

    pad_match = re.search(r'padding\s*:\s*(\d+)px\s+(\d+px)\s+(\d+px)\s*!important;', window)
    if not pad_match:
        print("Патч НЕ применён — не нашёл 'padding:Npx ... !important;' "
              "рядом с align-items:end. Вот что там реально стоит:\n")
        print(window)
        sys.exit(5)

    old_padding_full = pad_match.group(0)
    right_part = pad_match.group(2)
    bottom_part = pad_match.group(3)
    new_padding_full = f"padding:{new_top}px {right_part} {bottom_part} !important;"

    new_text = text[:marker_idx] + window.replace(old_padding_full, new_padding_full, 1) + text[marker_idx + 400:]

    backup = TARGET.with_name(TARGET.name + ".bak_before_toolbar_top_gap")
    backup.write_text(text, encoding="utf-8")
    TARGET.write_text(new_text, encoding="utf-8")

    print(f"Высота кнопки (.brat-gate min-height): {button_height}px")
    print(f"Новый отступ сверху (20% от высоты кнопки): {new_top}px")
    print(f"Было: {old_padding_full}")
    print(f"Стало: {new_padding_full}")
    print(f"\nБэкап сохранён: {backup}")
    print(f"Патч применён: {TARGET}")


if __name__ == "__main__":
    main()
