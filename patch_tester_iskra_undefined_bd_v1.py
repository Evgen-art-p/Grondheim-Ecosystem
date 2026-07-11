# -*- coding: utf-8 -*-
"""
patch_tester_iskra_undefined_bd_v1.py
─────────────────────────────────────────────────────────────
ПОЧИНКА ИСКРЫ · Биржа/tester_express.py · _on_council_event

ДИАГНОЗ (найдено чтением кода, подтверждено поведением: А01 не
показывалась НИКОГДА, с самого первого прогона — А02 всегда
появлялась сразу):

  В блоке aid == "A01" внутри _on_council_event есть строка:
      out(f"🎯 бар {i} ({bd}) — ИСКРА: {_t1}")
  Переменная `bd` НИГДЕ не определена во всей функции run_tester —
  ни разу не присвоена. Это NameError на ровном месте.

  Тот же undefined `bd` есть и во второй строке — в ветке
  "council_idle" (сообщение про "спуск не нашёл точку").

  Крах происходит ДО строки _emit_report("A01", narrative, _t1,
  result=r) — то есть отчёт Искры никогда не успевает уйти в кабинет.
  А исключение молча глотается ЧУЖИМ try/except в council.py:
      def _emit(ev):
          if on_event:
              try:
                  on_event(ev)
              except Exception:
                  pass
  Отсюда полная тишина — ни в чате, ни в консоли, ни в окне отчёта:
  ошибка есть, но её никто не видит.

  Для A02-A09 такой переменной в их блоках нет — они работали всегда.

ЛЕЧЕНИЕ:
  `bd` заменена на настоящую дату текущего бара — bars_all[i]["date"]
  — вычисляется один раз в начале итерации кандидата (там же, где
  задаётся state["cursor"] = i), используется в обоих местах, где
  раньше был undefined `bd`.

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_tester_iskra_undefined_bd_v1.py

Идемпотентно: маркер TESTER_ISKRA_BD_FIX_V1 — повторный запуск
скажет "уже пропатчено" и ничего не тронет второй раз.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "tester_express.py"
MARKER = "# TESTER_ISKRA_BD_FIX_V1 — маркер идемпотентности"

# ── 1. Определяем bd рядом с cursor (один раз на кандидата) ────
OLD_CURSOR = '''            state["cursor"] = i
            scanned += 1
            _emit(f"кандидат {idx+1}/{len(candidates)} · бар {i}")'''

NEW_CURSOR = '''            state["cursor"] = i
            bd = bars_all[i].get("date", "?")   # TESTER_ISKRA_BD_FIX_V1: было undefined
            scanned += 1
            _emit(f"кандидат {idx+1}/{len(candidates)} · бар {i}")'''

# ── 2. council_idle сообщение — bd теперь определена ────────────
OLD_IDLE_MSG = '''                    _msg = (f"кандидат {idx+1}/{len(candidates)} ({bd}, {side}): "
                            f"спуск не нашёл точку (компас={_d.get('compass')})")'''

NEW_IDLE_MSG = '''                    _msg = (f"кандидат {idx+1}/{len(candidates)} ({bd}, {side}): "
                            f"спуск не нашёл точку (компас={_d.get('compass')})")  # TESTER_ISKRA_BD_FIX_V1'''

# ── 3. Заголовок Искры — bd теперь определена ───────────────────
OLD_A01_MSG = '''                    out(f"🎯 бар {i} ({bd}) — ИСКРА: {_t1}")'''

NEW_A01_MSG = '''                    out(f"🎯 бар {i} ({bd}) — ИСКРА: {_t1}")  # TESTER_ISKRA_BD_FIX_V1'''


def _patch():
    if not TARGET.exists():
        print(f"[ПАТЧ] ❌ Не найден {TARGET} — запусти из корня репо.")
        raise SystemExit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ tester_express.py уже пропатчен (TESTER_ISKRA_BD_FIX_V1) — пропускаю.")
        return False

    changed = 0
    for label, old, new in (
        ("bd = bars_all[i]['date'] (определение)", OLD_CURSOR, NEW_CURSOR),
        ("council_idle сообщение (bd теперь существует)", OLD_IDLE_MSG, NEW_IDLE_MSG),
        ("заголовок Искры (bd теперь существует)", OLD_A01_MSG, NEW_A01_MSG),
    ):
        if old in src:
            src = src.replace(old, new)
            changed += 1
            print(f"[ПАТЧ] 🔧 {label}")
        elif new in src:
            print(f"[ПАТЧ] ↺ {label} — уже на месте")
        else:
            print(f"[ПАТЧ] ⚠️  {label} — блок не совпал, проверь вручную")

    if changed == 0:
        print("[ПАТЧ] ⚠️  ничего не изменилось.")
        return False

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] 💾 tester_express.py сохранён (изменений: {changed}).")
    return True


def main():
    print("═" * 62)
    print("  ПОЧИНКА ИСКРЫ · TESTER_ISKRA_BD_FIX_V1")
    print("═" * 62)
    _patch()
    print("═" * 62)
    print("  ✅ ГОТОВО. Перезапусти студию, прогони ТЕСТЕР ещё раз —")
    print("     Искра (A01) теперь должна появиться в чате и в окне")
    print("     отчёта ПЕРВОЙ, до Моржа.")
    print("═" * 62)


if __name__ == "__main__":
    main()
