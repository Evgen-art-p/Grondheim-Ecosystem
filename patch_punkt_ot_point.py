# -*- coding: utf-8 -*-
"""
patch_punkt_ot_point.py
════════════════════════════════════════════════════════════════════
ФИКС: «3 пункта» для SHORT считать от POINT инструмента, не константой

БАГ (нашли на тесте GBPUSD): punkt = 0.10 захардкожен в двух местах —
рождение SHORT-заявки и переезд SHORT. 0.10 верно ТОЛЬКО для золота
(пункт = 10 тиков = 10 × 0.01). Для GBPUSD point=1e-05, пункт=0.0001,
а код вычитал 3 × 0.10 = 0.30 — это 3000 пунктов, Sell Stop улетал в
бездну, заявка на фунте была бракованной.

ПРАВИЛЬНО (подтверждено терминалом золота: цена тика = 10 × point):
    пункт = 10 * point   → золото 10×0.01=0.10 (как было),
                            фунт   10×1e-05=0.0001 (верно теперь).

ЛЕЧЕНИЕ: в обоих местах заменить  punkt = 0.10  на
    punkt = 10 * (point or 0.01)
где point берём из market_data (он там есть — _spread_price его читает).

ИДЕМПОТЕНТЕН (маркер PUNKT_OT_POINT_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_punkt_ot_point.py
"""
import io
import sys
from pathlib import Path

MARKER = "PUNKT_OT_POINT_V1"


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
    n = 0

    # Место 1: рождение заявки в _otlozhka_entry_stop
    old1 = '    punkt = 0.10  # XAUUSD: 1 пункт = цена тика = 0.10'
    new1 = ('    punkt = 10 * float(point or 0.01)  # ' + MARKER
            + ': пункт = 10×point (любой инструмент)')
    if old1 in src:
        src = src.replace(old1, new1, 1)
        n += 1
        print("[ПАТЧ] ✓ рождение SHORT: punkt от point")
    else:
        print("[ПАТЧ] ⚠️  якорь рождения (punkt=0.10 с комментом) не найден")

    # Место 2: переезд заявки в _pereezd_zayavki (там punkt = 0.10 без коммента)
    old2 = ('    sp = (float(sp_pts) * float(point)) if sp_pts is not None else 0.0\n'
            '    punkt = 0.10\n')
    new2 = ('    sp = (float(sp_pts) * float(point)) if sp_pts is not None else 0.0\n'
            '    punkt = 10 * float(point or 0.01)  # ' + MARKER
            + ': пункт = 10×point\n')
    if old2 in src:
        src = src.replace(old2, new2, 1)
        n += 1
        print("[ПАТЧ] ✓ переезд SHORT: punkt от point")
    else:
        print("[ПАТЧ] ⚠️  якорь переезда (punkt=0.10) не найден")

    if n == 0:
        print("[ПАТЧ] ✗ ни один якорь не совпал — останов")
        sys.exit(2)

    bak = path.with_suffix(".py.bak_punkt")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✅ Готово (мест: {n}). Теперь «3 пункта» верны на любом")
    print("[ПАТЧ]    инструменте: золото 0.30, фунт 0.0003, и т.д.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
