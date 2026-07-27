# -*- coding: utf-8 -*-
"""
patch_brat_stage_up_to_header.py

Запускать из КОРНЯ репозитория:
    python patch_brat_stage_up_to_header.py

Что делает:
  Сейчас .app-container задаёт единый "gap: 20px" — это расстояние
  ОДИНАКОВО что между колонками (лево/центр/право), что между
  хедером и рядом контента под ним. Из-за этого над центральным
  контейнером (ГОРОД + чат + просев) висит пустой зазор в 20px.

  Патч разносит gap на два отдельных значения:
    - column-gap: 20px   (между лево/центр/право — как было)
    - row-gap:    8px    (между хедером и рядом контента — меньше)

  Итог: центральный контейнер (и левая/правая колонки вместе с ним,
  они все в одной строке грида) поднимается ближе к хедеру, зазор
  почти исчезает, высота стейджа увеличивается на разницу (20-8=12px
  дополнительной высоты сверху).

  Ищет короткую однострочную сигнатуру "gap: 20px;" — устойчиво
  к отступам. Если не найдёт или найдёт больше одного совпадения —
  ничего не меняет и показывает, что реально в файле.

Бэкап: Брат/ui_brat.py.bak_before_stage_up
"""

import sys
from pathlib import Path

TARGET = Path("Брат") / "ui_brat.py"

OLD = "gap: 20px;"
NEW = "column-gap: 20px;\n  row-gap: 8px;"


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН файл: {TARGET.resolve()}")
        print("Запусти скрипт из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    count = text.count(OLD)
    if count == 0:
        print("Патч НЕ применён — не нашёл 'gap: 20px;' в файле.")
        idx = text.find(".app-container")
        if idx != -1:
            print("\nВот что реально стоит в .app-container (для сверки):\n")
            print(text[idx:idx + 500])
        print("\nФайл не тронут.")
        sys.exit(2)
    if count > 1:
        print(f"Патч НЕ применён — 'gap: 20px;' встречается {count} раз "
              f"(ожидался 1) — не рискую менять не тот.")
        print("Файл не тронут.")
        sys.exit(3)

    new_text = text.replace(OLD, NEW, 1)

    backup = TARGET.with_name(TARGET.name + ".bak_before_stage_up")
    backup.write_text(text, encoding="utf-8")
    TARGET.write_text(new_text, encoding="utf-8")

    print(f"Бэкап сохранён: {backup}")
    print(f"Патч применён: {TARGET}")
    print("Центральный контейнер (и лево/право вместе с ним) поднялся")
    print("ближе к хедеру — вертикальный зазор 20px → 8px.")


if __name__ == "__main__":
    main()
