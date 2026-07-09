# -*- coding: utf-8 -*-
# patch_tester_express_soul_ignore.py — TESTER_EXPRESS_SOUL_IGNORE_V1
# ─────────────────────────────────────────────────────────────
# Закрывает reportMissingImports на "studio.grondheim_memory".
#
# ЭТО НЕ БАГ — в отличие от девяти *_live.py из прошлого патча,
# studio.grondheim_memory НЕ ДОЛЖЕН резолвиться в этом репозитории.
# Это душа агентов из старого мира (-2), для торговых агентов её
# сюда никто и не переносил — это явно написано в комментарии тремя
# строками ниже, try/except уже ловит отсутствие и подставляет
# честную заглушку (_NoSoulShim), плюс печатает в лог, что учится
# без неё. Рантайм полностью безопасен уже сейчас.
#
# Pylance не умеет отличить "модуль пропал по ошибке" от "модуля
# здесь и не должно быть, это намеренный кросс-репо fallback" —
# он статически не видит соседний репозиторий вообще. Чинить
# нечего: правильный ответ — сказать чекеру явно, что это ожидаемо.
# `# type: ignore[import]` здесь не прячет проблему, а документирует
# то, что уже написано в комментарии кода прямо под этой строкой.
#
# ЗАПУСК из корня:  python patch_tester_express_soul_ignore.py
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TESTER_EXPRESS_SOUL_IGNORE_V1"
ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "tester_express.py"

OLD = "        import studio.grondheim_memory as _gm"
NEW = "        import studio.grondheim_memory as _gm  # type: ignore[import]  # TESTER_EXPRESS_SOUL_IGNORE_V1: намеренно — см. except ниже"

EOF_MARKER = "\n# TESTER_EXPRESS_SOUL_IGNORE_V1 — маркер идемпотентности\n"


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print("• маркер уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    n = text.count(OLD)
    print(f"  {'✓' if n == 1 else '✗'} якорь [import studio.grondheim_memory]: найден {n} раз (нужно 1)")
    if n != 1:
        print("✗ якорь не сошёлся — файл отличается от ожидаемого. Ничего не режу.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_name(TARGET.name + f".bak_{ts}")
    shutil.copy2(TARGET, bak)
    print(f"• бэкап: {bak.name}")

    text = text.replace(OLD, NEW, 1) + EOF_MARKER
    TARGET.write_text(text, encoding="utf-8")
    print("• правка внесена")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}\n  Файл откатан из бэкапа.")
        sys.exit(1)

    print()
    print("  ГОТОВО: Pylance больше не подсвечивает намеренный fallback.")
    print("  Рантайм не менялся ни на символ — только комментарий для чекера.")
    print("═" * 62)


if __name__ == "__main__":
    main()
