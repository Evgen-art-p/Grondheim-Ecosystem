# -*- coding: utf-8 -*-
"""
patch_brat_chat_viewer_shrink.py

Запускать из КОРНЯ репозитория:
    python patch_brat_chat_viewer_shrink.py

Что делает:
  Уменьшает высоту чата и поля с просевом (chat-log/viewer) на
  33% от высоты кнопки ГОРОД (.brat-gate).

  Технически: chat-log/viewer лежат в .split-view внутри
  .stage-content (flex:1 — забирает весь остаток высоты стейджа).
  Уменьшить их высоту на N px = увеличить padding-bottom у
  .stage-content на те же N px (сейчас 90px). Кнопку и toolbar
  не трогает вообще.

  Высоту кнопки берёт из реального CSS-правила .brat-gate
  (min-height) — какая бы она сейчас ни была, а не захардкоженное
  число.

Бэкап: Брат/ui_brat.py.bak_before_chat_viewer_shrink
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

    gate_match = re.search(r'\.brat-gate\s*\{(.*?)\}', text, re.DOTALL)
    if not gate_match:
        print("Патч НЕ применён — не нашёл CSS-правило .brat-gate.")
        sys.exit(2)
    height_match = re.search(r'min-height\s*:\s*(\d+)\s*px', gate_match.group(1))
    if not height_match:
        print("Патч НЕ применён — не нашёл min-height внутри .brat-gate.")
        sys.exit(3)
    button_height = int(height_match.group(1))
    delta = round(button_height * 0.33)
    if delta < 1:
        delta = 1

    old_marker = "padding-top:0 !important; padding-bottom:90px;"
    count = text.count(old_marker)
    if count == 0:
        print("Патч НЕ применён — не нашёл 'padding-bottom:90px;' у stage-content.")
        idx = text.find("stage-content")
        if idx != -1:
            print("\nВот что реально стоит рядом со stage-content:\n")
            print(text[idx:idx + 300])
        sys.exit(4)
    if count > 1:
        print(f"Патч НЕ применён — маркер встречается {count} раз (ожидался 1).")
        sys.exit(5)

    old_bottom = 90
    new_bottom = old_bottom + delta
    new_marker = f"padding-top:0 !important; padding-bottom:{new_bottom}px;"

    new_text = text.replace(old_marker, new_marker, 1)

    backup = TARGET.with_name(TARGET.name + ".bak_before_chat_viewer_shrink")
    backup.write_text(text, encoding="utf-8")
    TARGET.write_text(new_text, encoding="utf-8")

    print(f"Высота кнопки (.brat-gate min-height): {button_height}px")
    print(f"33% от неё: {delta}px")
    print(f"padding-bottom у stage-content: {old_bottom}px → {new_bottom}px")
    print(f"(чат и просев стали ниже ровно на {delta}px)")
    print(f"\nБэкап сохранён: {backup}")
    print(f"Патч применён: {TARGET}")


if __name__ == "__main__":
    main()
