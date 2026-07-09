# -*- coding: utf-8 -*-
# patch_global_anchor_typing.py — GLOBAL_ANCHOR_TYPING_V1
# ─────────────────────────────────────────────────────────────
# Закрывает неявный Optional в global_trend() — тот самый параметр,
# который williams_core.py уже дёргает как as_of_date. Optional уже
# импортирован в файле (для senior_timeframe), просто эту сигнатуру
# пропустили. Чисто типизация, тело функции не меняется — там уже
# стоит `if as_of_date and sbars:`, то есть None и так обрабатывался
# по факту, просто сигнатура не признавалась в этом.
#
# ЗАПУСК из корня:  python patch_global_anchor_typing.py
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "GLOBAL_ANCHOR_TYPING_V1"
ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "global_anchor.py"

OLD = '''def global_trend(symbol: str, working_tf: str,
                 as_of_date: str = None) -> dict:'''
NEW = '''def global_trend(symbol: str, working_tf: str,
                 as_of_date: Optional[str] = None) -> dict:'''

EOF_MARKER = "\n# GLOBAL_ANCHOR_TYPING_V1 — маркер идемпотентности\n"


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
    print(f"  {'✓' if n == 1 else '✗'} якорь [global_trend: as_of_date]: найден {n} раз (нужно 1)")
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

    print("\n  ГОТОВО: as_of_date теперь Optional[str], как тело функции и предполагало.")
    print("═" * 62)


if __name__ == "__main__":
    main()
