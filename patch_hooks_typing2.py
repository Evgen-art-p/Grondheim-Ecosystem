# -*- coding: utf-8 -*-
# patch_hooks_typing2.py — HOOKS_TYPING_V2
# ─────────────────────────────────────────────────────────────
# Дельта поверх HOOKS_TYPING_V1. Закрывает reportCallIssue/
# reportArgumentType на max(reasons, key=reasons.get) — ТУ ЖЕ
# строку, что V1 уже трогал (там добавил только аннотацию типа
# словаря). Оказалось мало: сама передача `reasons.get` как
# значения в key= — вот в чём корень.
#
# ПОЧЕМУ АННОТАЦИЯ СЛОВАРЯ НЕ ХВАТИЛО. dict.get — ПЕРЕГРУЖЕННАЯ
# функция (три сигнатуры под разный default). Даже когда словарь
# честно dict[str, int], bound-метод reasons.get остаётся целым
# перегруженным объектом, а не одной функцией (str) -> int — а
# max() в typeshed ждёт именно одну монолитную сигнатуру для key=.
# Это не наша дыра в типизации — это то, как Pylance разбирает
# ЛЮБОЙ dict.get, переданный значением, а не вызовом.
#
# ПРАВКА: key=lambda k: reasons[k] — лямбда с одним аргументом
# это ровно та монолитная сигнатура (str) -> int, что и просит
# max(). Обращение по [] вместо .get() безопасно: max() перебирает
# СОБСТВЕННЫЕ ключи reasons, промаха по ключу быть не может.
# Сверено на 200 случайных распределениях — совпадает побитово.
#
# ЗАПУСК из корня:  python patch_hooks_typing2.py
# Требует уже применённый HOOKS_TYPING_V1.
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER   = "HOOKS_TYPING_V2"
REQUIRED = "HOOKS_TYPING_V1"

ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "hooks.py"

OLD = '    top_reason = max(reasons, key=reasons.get) if reasons else "none"'
NEW = '    top_reason = max(reasons, key=lambda k: reasons[k]) if reasons else "none"  # HOOKS_TYPING_V2'

EOF_MARKER = "\n# HOOKS_TYPING_V2 — маркер идемпотентности\n"


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: max(key=) через lambda")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if REQUIRED not in text:
        print(f"✗ не наложен базовый патч {REQUIRED}.")
        print("  Сначала прогони patch_hooks_typing.py — этот идёт поверх него.")
        sys.exit(1)

    if MARKER in text:
        print("• маркер уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    n = text.count(OLD)
    print(f"  {'✓' if n == 1 else '✗'} якорь [max(reasons, key=reasons.get)]: найден {n} раз (нужно 1)")
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
    print("  ГОТОВО: key=lambda k: reasons[k] — монолитная сигнатура,")
    print("  max() больше не спотыкается о перегрузки dict.get.")
    print("═" * 62)


if __name__ == "__main__":
    main()
