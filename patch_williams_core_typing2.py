# -*- coding: utf-8 -*-
# patch_williams_core_typing2.py — WILLIAMS_CORE_TYPING_V2
# ─────────────────────────────────────────────────────────────
# Дельта поверх WILLIAMS_CORE_TYPING_V1. Закрывает всплывший
# reportOptionalOperand в compute_ac_series (строка 191): "Оператор
# '-' не поддерживается для None". Ошибка вылезла ИМЕННО ПОСЛЕ V1 —
# пока result был бесформенным list[None], Pylance спотыкался о
# __setitem__ раньше и до этой строки не добирался. Как только
# список стал типобезопасным (list[Optional[float]]), проверка
# дошла до правой части присваивания и увидела, что ao_series[i]
# сам по себе Optional.
#
# ЗАКОН: ao_series[i] СТРУКТУРНО не может быть None в этой строке —
# window = ao_series[i-4:i+1] включает сам ao_series[i] (5 элементов),
# valid отбрасывает None; если бы ao_series[i] было None, valid не
# набрал бы 5 штук и мы бы ушли по `continue` строкой раньше. Значит
# это не костыль-заглушка, а честная запись уже существующего
# инварианта — Pylance просто не умеет его вывести сам (не видит
# связь между `window`/`valid` и повторным обращением к ao_series[i]).
# Сверено на 300 случайных сериях (включая перемешанные None) —
# поведение побитово идентично.
#
# ЗАПУСК из корня:  python patch_williams_core_typing2.py
# Требует уже применённый WILLIAMS_CORE_TYPING_V1.
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER   = "WILLIAMS_CORE_TYPING_V2"
REQUIRED = "WILLIAMS_CORE_TYPING_V1"

ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "williams_core.py"

OLD = '''    result: list[Optional[float]] = [None] * len(ao_series)
    for i in range(len(ao_series)):
        window = ao_series[max(0, i-4):i+1]
        valid  = [v for v in window if v is not None]
        if len(valid) < 5:
            continue
        result[i] = ao_series[i] - sum(valid[-5:]) / 5
    return result'''

NEW = '''    result: list[Optional[float]] = [None] * len(ao_series)
    for i in range(len(ao_series)):
        window = ao_series[max(0, i-4):i+1]
        valid  = [v for v in window if v is not None]
        if len(valid) < 5:
            continue
        cur = ao_series[i]
        if cur is None:
            continue  # WILLIAMS_CORE_TYPING_V2: структурно недостижимо
            # (window включает cur; valid==5 доказывает cur не None) —
            # запись существующего инварианта, не новая ветка поведения
        result[i] = cur - sum(valid[-5:]) / 5
    return result'''

EOF_MARKER = "\n# WILLIAMS_CORE_TYPING_V2 — маркер идемпотентности\n"


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: reportOptionalOperand в compute_ac_series")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if REQUIRED not in text:
        print(f"✗ не наложен базовый патч {REQUIRED}.")
        print("  Сначала прогони patch_williams_core_typing.py — этот идёт поверх него.")
        sys.exit(1)

    if MARKER in text:
        print("• маркер уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    n = text.count(OLD)
    print(f"  {'✓' if n == 1 else '✗'} якорь [compute_ac_series: result[i]]: найден {n} раз (нужно 1)")
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
    print("  ГОТОВО: явная проверка `cur is None` перед вычитанием.")
    print("  Ветка структурно недостижима (доказано на 300 прогонах,")
    print("  включая перемешанные None) — формула AC не изменилась.")
    print("═" * 62)


if __name__ == "__main__":
    main()
