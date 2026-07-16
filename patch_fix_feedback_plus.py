# -*- coding: utf-8 -*-
"""
patch_fix_feedback_plus.py
════════════════════════════════════════════════════════════════════
ФИКС МОЕГО БАГА: висячий унарный + в user_msg трёх мозгов

Ошибка из прогона:
  run_brut/run_avan/run_cons: bad operand type for unary +: 'str'

ПРИЧИНА (мой косяк в patch_disciplina_pyramidy.py): при вставке блока
обратной связи получилось:
    user_msg = (
        # коммент
        + ((f"⛔ ОБРАТНАЯ СВЯЗЬ..." ...) if ... else "")
        + "=== НАКРЫТЫЙ СТОЛ ..."
Первый операнд отсутствует → Python читает "+(...)" как УНАРНЫЙ плюс
перед строкой → падение. Все три трейдера мертвы, прогон холостой.

ЛЕЧЕНИЕ: убрать ВЕДУЩИЙ "+" — блock feedback становится первым
операндом конкатенации. Логика та же, синтаксис чинится.

ИДЕМПОТЕНТЕН (проверяет наличие битого паттерна). Бэкап — по файлу.
Запуск из корня Grondheim-Ecosystem:
    python patch_fix_feedback_plus.py
"""
import io
import sys
from pathlib import Path

SLOTS = ("A06", "A07", "A08")


def find_brain(aid):
    cands = [
        Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / aid / "мозг.py",
        Path("Биржа") / "цеха" / "торговый_хаос" / "слоты" / aid / "мозг.py",
    ]
    for c in cands:
        if c.exists():
            return c
    return None


BROKEN = (
    '    user_msg = (\n'
    '        # DISCIPLINA_PYRAMIDY_V1: если по прошлому ведению был укол — показать\n'
    '        # его трейдеру ОТДЕЛЬНОЙ строкой, чтобы увидел и сделал вывод.\n'
    '        + ((f"⛔ ОБРАТНАЯ СВЯЗЬ ПО ВЕДЕНИЮ (прошлый бар): "\n'
)

FIXED = (
    '    user_msg = (\n'
    '        # DISCIPLINA_PYRAMIDY_V1: если по прошлому ведению был укол — показать\n'
    '        # его трейдеру ОТДЕЛЬНОЙ строкой (fix: без ведущего + — первый операнд).\n'
    '        ((f"⛔ ОБРАТНАЯ СВЯЗЬ ПО ВЕДЕНИЮ (прошлый бар): "\n'
)


def main():
    fixed_any = False
    for aid in SLOTS:
        path = find_brain(aid)
        if not path:
            print(f"[ПАТЧ] ⚠️  {aid}: мозг.py не найден — пропуск")
            continue
        src = path.read_text(encoding="utf-8")

        if BROKEN not in src:
            if FIXED in src:
                print(f"[ПАТЧ] ✓ {aid}: уже починен")
            else:
                print(f"[ПАТЧ] ⚠️  {aid}: битый паттерн не найден "
                      f"(структура иная?) — проверь вручную")
            continue

        bak = path.with_suffix(".py.bak_fixplus")
        if not bak.exists():
            bak.write_text(src, encoding="utf-8")
        src = src.replace(BROKEN, FIXED, 1)
        path.write_text(src, encoding="utf-8")
        print(f"[ПАТЧ] ✓ {aid}: висячий + убран, синтаксис починен")
        fixed_any = True

    if fixed_any:
        print("[ПАТЧ] ✅ Трейдеры оживут. Прогоняй заново.")
    else:
        print("[ПАТЧ] ✓ Чинить нечего (или уже починено).")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
