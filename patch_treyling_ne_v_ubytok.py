# -*- coding: utf-8 -*-
"""
patch_treyling_ne_v_ubytok.py
════════════════════════════════════════════════════════════════════
ТРЕЙЛИНГ НЕ ДВИГАЕТ СТОП В УБЫТОЧНУЮ ЗОНУ (канон)

БОЛЕЗНЬ (лог GBPUSD, Брут SHORT):
  вход 1.46942, стоп 1.47579 → трейлинг подтянул к Зубам 1.469757.
  Но Зубы ВЫШЕ входа шорта → стоп в зоне УБЫТКА. Цена пошла ПРОТИВ
  позиции (вверх), Зубы оказались над входом, трейлинг послушно
  потянул стоп туда. H бара выбил → −1.0R.
  По Вильямсу трейлинг за Зубы защищает ПРОФИТ — имеет смысл, только
  когда цена идёт В СТОРОНУ позиции и Зубы запирают прибыль. Когда
  цена против — стоп трогать НЕЛЬЗЯ, ждём исходный.

ДИАГНОЗ: защита «цена под/над Зубами» есть, но неполная — она не
проверяет, что сами Зубы в ПРОФИТ-зоне относительно входа.

ЛЕЧЕНИЕ (одно условие в каждую ветку, сразу после novy = teeth):
  LONG:  if novy < entry: continue   # Зубы ниже входа — не запираем убыток
  SHORT: if novy > entry: continue   # Зубы выше входа — не запираем убыток
Трейлинг сработает ТОЛЬКО когда реально защищает (стоп в безубыток
или профит). Против-позиционное движение оставит ИСХОДНЫЙ стоп —
сделка выживет или честно умрёт −1R по своему настоящему стопу.

ИДЕМПОТЕНТЕН (маркер TRAILING_NE_V_UBYTOK_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_treyling_ne_v_ubytok.py
"""
import io
import sys
from pathlib import Path

MARKER = "TRAILING_NE_V_UBYTOK_V1"


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

    # LONG-ветка: после novy = teeth (первое вхождение в LONG)
    long_old = (
        '            novy = teeth\n'
        '            if novy <= old:          # только в защиту\n'
        '                continue\n'
    )
    long_new = (
        '            novy = teeth\n'
        '            # ' + MARKER + ': Зубы ниже входа → стоп в убыток, не тянем\n'
        '            if novy < entry:\n'
        '                continue\n'
        '            if novy <= old:          # только в защиту\n'
        '                continue\n'
    )
    if long_old in src:
        src = src.replace(long_old, long_new, 1)
        n += 1
        print("[ПАТЧ] ✓ LONG: стоп не тянется ниже входа")
    else:
        print("[ПАТЧ] ⚠️  LONG-якорь не найден")

    # SHORT-ветка
    short_old = (
        '            novy = teeth\n'
        '            if novy >= old:\n'
        '                continue\n'
    )
    short_new = (
        '            novy = teeth\n'
        '            # ' + MARKER + ': Зубы выше входа → стоп в убыток, не тянем\n'
        '            if novy > entry:\n'
        '                continue\n'
        '            if novy >= old:\n'
        '                continue\n'
    )
    if short_old in src:
        src = src.replace(short_old, short_new, 1)
        n += 1
        print("[ПАТЧ] ✓ SHORT: стоп не тянется выше входа")
    else:
        print("[ПАТЧ] ⚠️  SHORT-якорь не найден")

    if n == 0:
        print("[ПАТЧ] ✗ ни один якорь не совпал — останов")
        sys.exit(2)

    # проверка синтаксиса до записи
    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ правка ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_treyling_ubytok")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✅ Готово (веток: {n}). Трейлинг больше не фиксирует убыток.")
    print("[ПАТЧ]    Стоп тянется только в безубыток/профит. Против позиции —")
    print("[ПАТЧ]    исходный стоп держится, сделка выживает или честно −1R.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
