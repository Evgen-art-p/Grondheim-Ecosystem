# -*- coding: utf-8 -*-
"""
patch_otkat_treylinga.py
════════════════════════════════════════════════════════════════════
ОТКАТ МОЕЙ ОШИБКИ: TRAILING_NE_V_UBYTOK_V1 — ЛОКА ПРАВА

Я поставил диагноз неверно. Настоящая причина -1.0R на подтянутом
стопе (GBPUSD, Брут SHORT) была НЕ в том, что трейлинг «лезет в
убыток» — а в том, что у СТАРОЙ позиции без stop_initial fallback
брал ТЕКУЩИЙ (уже подтянутый) стоп и как цену выхода, и как знаменатель
риска: risk = stop_r - entry, где stop_r == exit_price. Это
математически ВСЕГДА даёт ровно -1.0, какой бы трейлинг ни был —
тавтология, не баг трейлинга.

Эта причина уже вылечена РАНЬШЕ тем же днём: STOP_INITIAL_R_V1 (риск
считается от ПЕРВОГО стопа) + чистка старого trading_state.json.
Мой ДОПОЛНИТЕЛЬНЫЙ запрет «не двигать стоп в зону убытка входа» лечил
ПРИЗРАК и реально ВРЕДИТ: он блокирует законное сокращение риска
(например: подтянуть стоп с -1.0R до -0.05R — это ЗАЩИТА, даже если
формально ещё не breakeven). Любое движение стопа НАВСТРЕЧУ цене уже
проверено условием `novy <= old` (LONG) / `novy >= old` (SHORT) —
этого достаточно, монотонное сокращение риска гарантировано.

ЛЕЧЕНИЕ: убрать guard `if novy < entry` (LONG) / `if novy > entry`
(SHORT), вернуть трейлинг к исходной логике «двигать всегда навстречу
цене», без ограничения по зоне входа.

ИДЕМПОТЕНТЕН (проверяет отсутствие/наличие маркера). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_otkat_treylinga.py
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

    if MARKER not in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже отсутствует — идемпотентно (нечего откатывать)")
        return

    orig = src
    n = 0

    long_broken = (
        '            novy = teeth\n'
        '            # ' + MARKER + ': Зубы ниже входа → стоп в убыток, не тянем\n'
        '            if novy < entry:\n'
        '                continue\n'
        '            if novy <= old:          # только в защиту\n'
        '                continue\n'
    )
    long_fixed = (
        '            novy = teeth\n'
        '            if novy <= old:          # только в защиту\n'
        '                continue\n'
    )
    if long_broken in src:
        src = src.replace(long_broken, long_fixed, 1)
        n += 1
        print("[ПАТЧ] ✓ LONG: guard убран, трейлинг снова движется навстречу цене")
    else:
        print("[ПАТЧ] ⚠️  LONG-блок не найден (изменён вручную?)")

    short_broken = (
        '            novy = teeth\n'
        '            # ' + MARKER + ': Зубы выше входа → стоп в убыток, не тянем\n'
        '            if novy > entry:\n'
        '                continue\n'
        '            if novy >= old:\n'
        '                continue\n'
    )
    short_fixed = (
        '            novy = teeth\n'
        '            if novy >= old:\n'
        '                continue\n'
    )
    if short_broken in src:
        src = src.replace(short_broken, short_fixed, 1)
        n += 1
        print("[ПАТЧ] ✓ SHORT: guard убран, трейлинг снова движется навстречу цене")
    else:
        print("[ПАТЧ] ⚠️  SHORT-блок не найден (изменён вручную?)")

    if n == 0:
        print("[ПАТЧ] ✗ ни один блок не совпал — останов")
        sys.exit(2)

    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ откат ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_otkat_treylinga")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✅ Откат выполнен (веток: {n}). Трейлинг снова тянет стоп")
    print("[ПАТЧ]    навстречу цене всегда — от -1.0R к -0.5R, -0.2R и дальше.")
    print("[ПАТЧ]    Защита от ЗАВЫШЕННОГО риска (novy<=old/novy>=old) осталась.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
