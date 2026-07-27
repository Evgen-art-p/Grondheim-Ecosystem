# -*- coding: utf-8 -*-
"""
patch_brat_toolbar_height.py

Запускать из КОРНЯ репозитория:
    python patch_brat_toolbar_height.py

Что делает:
  Поле с кнопкой ГОРОД (stage-toolbar) в кабинете Брата — сейчас
  "height:auto" (высота по контенту, ~46px: кнопка 34px + паддинги
  6+6px). Раз чат и поле с просевом (chat-log/viewer) — flex:1 и
  просто забирают весь остаток высоты stage-monitor, то любое
  увеличение фиксированной высоты toolbar автоматически отъедает
  место именно у них — отдельно их трогать не нужно.

    1) height: auto → 55px  (~46px * 1.2 ≈ 55px, +20%)
    2) padding-top: 6px → 7px  (6 * 1.2 = 7.2 ≈ 7px, +20%) —
       расстояние от верхнего края кнопки до верха поля.
       Кнопка внутри выровнена по align-items:end (прижата к низу),
       поэтому весь прирост высоты поля (п.1) тоже ложится сверху,
       над кнопкой — оба увеличения складываются визуально.

  Ищет короткие однострочные фрагменты (не многострочный блок целиком)
  — устойчивее к разнице в отступах/переносах строк между версиями
  файла. Если что-то не найдено — ничего не меняет, печатает, что
  именно не нашёл, и показывает окружение "stage-toolbar" для сверки.

Бэкап: Брат/ui_brat.py.bak_before_toolbar_height
"""

import sys
from pathlib import Path

TARGET = Path("Брат") / "ui_brat.py"

REPLACEMENTS = [
    (
        "align-items:end !important; height:auto !important;",
        "align-items:end !important; height:55px !important;",
        "height: auto → 55px",
    ),
    (
        "padding:6px 12px 6px !important;",
        "padding:7px 12px 6px !important;",
        "padding-top: 6px → 7px",
    ),
]


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН файл: {TARGET.resolve()}")
        print("Запусти скрипт из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")
    original = text

    if "stage-toolbar" not in text:
        print("Патч НЕ применён — в файле вообще нет 'stage-toolbar'.")
        print("Файл не тронут. Проверь, тот ли это ui_brat.py.")
        sys.exit(2)

    missing = []
    new_text = text
    for old, new, label in REPLACEMENTS:
        count = new_text.count(old)
        if count == 0:
            missing.append(label)
            continue
        if count > 1:
            missing.append(f"{label} — найдено {count} совпадений (ожидалось 1), пропущено")
            continue
        new_text = new_text.replace(old, new, 1)

    if missing:
        print("Патч НЕ применён полностью — не нашёл ожидаемый текст:")
        for m in missing:
            print(f"  - {m}")
        idx = text.find("stage-toolbar")
        snippet = text[max(0, idx - 30):idx + 400]
        print("\nВот что реально стоит в файле вокруг stage-toolbar (для сверки):\n")
        print(snippet)
        print("\nФайл НЕ изменён.")
        sys.exit(3)

    backup = TARGET.with_name(TARGET.name + ".bak_before_toolbar_height")
    backup.write_text(original, encoding="utf-8")
    TARGET.write_text(new_text, encoding="utf-8")

    print(f"Бэкап сохранён: {backup}")
    print(f"Патч применён: {TARGET}")
    print("Поле с кнопкой ГОРОД теперь выше на ~20% (за счёт чата и просева),")
    print("и отступ сверху над кнопкой тоже увеличен на ~20%.")


if __name__ == "__main__":
    main()
