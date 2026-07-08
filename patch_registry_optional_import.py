# -*- coding: utf-8 -*-
"""
Патч: Брат/ui_registry.py — reportMissingImports на строках 381 и 397.

ПРИЧИНА — НЕ БАГ, А НАМЕРЕННО ОПЦИОНАЛЬНЫЙ ИМПОРТ:
  `studio.modules_registry` — модуль СТАРОГО репо (-2). В новом городе
  (Grondheim-Ecosystem) его сознательно нет — это прямо написано в
  комментариях кода:
      "Цеха для селекта рождения. Новый город: studio/ нет — fallback."
      "Новый город — старого studio/ нет. Отдаём встроенный список."
  Импорт обёрнут в try/except Exception именно для этого — рабочий
  страховочный механизм на переходный период, не забытый долг.

  Pylance не смотрит внутрь try/except — он всегда статически ищет
  модуль на диске и ругается, даже если код готов к его отсутствию.
  Чинить тут нечего в логике: это единственный честный случай, когда
  правильный ответ — explicit pyright-ignore, а не правка кода,
  потому что мы ДОКУМЕНТИРУЕМ намеренно опциональную зависимость,
  а не прячем реальную проблему.

Правка: добавляет `# pyright: ignore[reportMissingImports]` на обе
строки импорта. Идемпотентен: повторный запуск ничего не меняет.
"""
import sys
import py_compile
import shutil
from pathlib import Path
from datetime import datetime

TARGET = Path("Брат/ui_registry.py")

PAIRS = [
    (
        "        from studio.modules_registry import list_cartridges",
        "        from studio.modules_registry import list_cartridges  # pyright: ignore[reportMissingImports]",
    ),
    (
        "        from studio.modules_registry import get_cartridge",
        "        from studio.modules_registry import get_cartridge  # pyright: ignore[reportMissingImports]",
    ),
]


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН: {TARGET} (запусти из корня Grondheim-Ecosystem)")
        sys.exit(1)

    src = TARGET.read_text(encoding="utf-8")

    if "pyright: ignore[reportMissingImports]" in src:
        print("Уже применено — идемпотентность держит, ничего не меняю.")
        return

    for old, new in PAIRS:
        if old not in src:
            print(f"НЕ НАЙДЕН ожидаемый фрагмент: {old!r}")
            print("Файл изменился с момента диагностики — ничего не трогаю.")
            sys.exit(1)

    backup = TARGET.with_suffix(f".py.bak_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(TARGET, backup)
    print(f"Бэкап: {backup}")

    new_src = src
    for old, new in PAIRS:
        new_src = new_src.replace(old, new)
    TARGET.write_text(new_src, encoding="utf-8")

    py_compile.compile(str(TARGET), doraise=True)
    print("Синтаксис цел (py_compile прошёл).")
    print("Готово: обе строки импорта помечены как намеренно опциональные (pyright-ignore).")


if __name__ == "__main__":
    main()
