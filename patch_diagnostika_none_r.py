# -*- coding: utf-8 -*-
"""
patch_diagnostika_none_r.py
════════════════════════════════════════════════════════════════════
СТРАХОВКА: диагностика, если pnl_r снова станет None

Если когда-нибудь риск (risk = entry - stop_r для LONG / stop_r - entry
для SHORT) окажется ≤ 0 — раньше это молча превращалось в pnl_r=None
и прочерк в отчёте, без единой зацепки ПОЧЕМУ. Расследование каждый раз
занимало полчаса реконструкции по обрывкам лога (см. историю с GBPUSD
и EURUSD None-R сегодня).

ЛЕЧЕНИЕ: перед строкой `pnl_r = round(...) if risk > 0 else None`
вставляем print, который печатает ВСЁ нужное для диагноза ЗА ОДИН
взгляд в консоль:
  • direction, entry, stop (текущий), stop_initial (сырое значение
    из pos, ДО fallback — покажет, отсутствует ли поле вообще);
  • risk (посчитанный) — само число, которое обнулило R;
  • trailed / dolivok / entry_fractal_idx — история позиции, если есть
    (подскажет: старая позиция без stop_initial? был долив? был
    переезд заявки?).

Печатает ТОЛЬКО когда risk <= 0 (аварийный случай) — в норме молчит,
лог не засоряет.

ИДЕМПОТЕНТЕН (маркер DIAGNOSTIKA_NONE_R_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_diagnostika_none_r.py
"""
import io
import sys
from pathlib import Path

MARKER = "DIAGNOSTIKA_NONE_R_V1"


def find_hooks() -> Path:
    for p in (Path("Биржа") / "hooks.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "hooks.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден hooks.py — запусти из корня")
    sys.exit(1)


def main():
    path = find_hooks()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src

    anchor = '        pnl_r     = round(pnl_price / risk, 4) if risk > 0 else None\n'
    if anchor not in src:
        print("[ПАТЧ] ✗ якорь расчёта pnl_r не найден — файл изменён?")
        sys.exit(2)

    inject = (
        '        if risk <= 0:\n'
        '            # ' + MARKER + ': риск обнулился — печатаем ВСЁ для\n'
        '            # диагноза за один взгляд, не полчаса реконструкции.\n'
        '            print(\n'
        '                f"[МАЯК] ⚠️  RISK<=0 → pnl_r=None. Разбор:\\n"\n'
        '                f"  trader={pos.get(\'trader\')} dir={direction} "\n'
        '                f"entry={entry} stop(текущий)={stop}\\n"\n'
        '                f"  stop_initial(сырое из pos)={pos.get(\'stop_initial\')}"\n'
        '                f" (None → поля НЕТ, позиция СТАРАЯ, без патча)\\n"\n'
        '                f"  stop_r(использован)={stop_r}  risk={risk}\\n"\n'
        '                f"  entry_avg={pos.get(\'entry_avg\')} "\n'
        '                f"lot_base={pos.get(\'lot_base\')} lot={pos.get(\'lot\')}\\n"\n'
        '                f"  trailed={pos.get(\'trailed\')} "\n'
        '                f"dolivok={pos.get(\'dolivok\')} "\n'
        '                f"entry_fractal_idx={pos.get(\'entry_fractal_idx\')} "\n'
        '                f"(если есть — была активна отложка/переезд)"\n'
        '            )\n'
        + anchor
    )
    src = src.replace(anchor, inject, 1)

    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ правка ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_diagnostika_none_r")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Страховка поставлена.")
    print("[ПАТЧ]    Если risk<=0 повторится — консоль сразу покажет, откуда")
    print("[ПАТЧ]    (старая позиция без stop_initial? долив? переезд?).")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
