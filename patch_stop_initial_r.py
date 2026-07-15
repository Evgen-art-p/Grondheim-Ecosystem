# -*- coding: utf-8 -*-
"""
patch_stop_initial_r.py — ЛЕЧЕНИЕ БОЛЕЗНИ "R от подтянутого стопа"

Болезнь:
    _settle_positions считал risk = |entry - stop| от ТЕКУЩЕГО стопа.
    После СЕЙФа (трейлинг) стоп проезжает за вход → risk отрицательный
    → pnl_r = None → судья выходит, черновик не пишется, прибыльная
    сделка выпадает из отчёта. Теряем именно те сделки, где сейф сработал.

Лечение (две руки):
    1. Позиция при РОЖДЕНИИ запоминает свой ПЕРВЫЙ стоп: stop_initial.
       Трейлинг перетирает pos["stop"] — но stop_initial неизменен.
    2. _settle_positions считает risk от stop_initial (fallback на stop
       для старых уже открытых позиций без этого поля).

Идемпотентен: повторный запуск ничего не делает (маркеры проверяются).
Запуск из корня проекта:  python patch_stop_initial_r.py
"""
import io
import sys
from pathlib import Path

HOOKS = Path("Биржа") / "hooks.py"

MARKER = "STOP_INITIAL_R_V1"


def main():
    if not HOOKS.exists():
        print(f"[ПАТЧ] ✗ не найден {HOOKS} — запусти из корня проекта")
        sys.exit(1)

    src = HOOKS.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — нечего делать (идемпотентно)")
        return

    orig = src
    changes = 0

    # ── РУКА 1: позиция запоминает первый стоп при рождении ──────────
    # Якорь — строка создания позиции. Вставляем stop_initial сразу
    # после "stop": order.get("stop"),
    anchor_birth = '            "stop":      order.get("stop"),\n'
    inject_birth = (
        anchor_birth
        + '            # ' + MARKER + ': ПЕРВЫЙ стоп — неизменная мера риска R.\n'
        + '            # Трейлинг/СЕЙФ перетирают "stop"; этот помнит вход.\n'
        + '            "stop_initial": order.get("stop"),\n'
    )
    if anchor_birth in src and "stop_initial" not in src:
        src = src.replace(anchor_birth, inject_birth, 1)
        changes += 1
        print('[ПАТЧ] ✓ РУКА 1: позиция запоминает stop_initial при рождении')
    else:
        print('[ПАТЧ] ⚠️  РУКА 1: якорь рождения не найден (или уже есть stop_initial) — пропуск')

    # ── РУКА 1.5: самопочинка — уже открытые позиции без stop_initial ──
    # Шеф не обязан лазить в консоль и проверять trailed вручную.
    # Трейлинг видит каждую OPEN-позицию КАЖДЫЙ бар — вот там и чиним
    # молча, автоматически, один раз на позицию, навсегда.
    # Честно: если сейф УЖЕ сработал ДО патча, истинный первый стоп
    # нигде не логировался отдельно — его неоткуда восстановить.
    # Самопочинка берёт стоп таким, какой он есть в момент первой
    # встречи после патча — это лучшее, что вообще возможно, и это
    # происходит САМО, без ручной проверки.
    anchor_trail = (
        '        old = pos.get("stop")\n'
        '        entry = pos.get("entry")\n'
        '        if old is None or entry is None:\n'
        '            continue\n'
    )
    inject_trail = (
        '        old = pos.get("stop")\n'
        '        entry = pos.get("entry")\n'
        '        if old is None or entry is None:\n'
        '            continue\n'
        '        # ' + MARKER + ': самопочинка — если позиция открыта ДО патча\n'
        '        # и ещё не имеет stop_initial, фиксируем его молча ОДИН раз.\n'
        '        if "stop_initial" not in pos:\n'
        '            pos["stop_initial"] = old\n'
        '            dirty = True\n'
    )
    if anchor_trail in src:
        src = src.replace(anchor_trail, inject_trail, 1)
        changes += 1
        print('[ПАТЧ] ✓ РУКА 1.5: самопочинка уже открытых позиций (без ручной проверки)')
    else:
        print('[ПАТЧ] ⚠️  РУКА 1.5: якорь трейлинга не найден — пропуск (не критично)')

    # ── РУКА 2: risk от stop_initial в _settle_positions ────────────
    # Было:
    #   if direction == "LONG":
    #       risk      = entry - stop
    #       pnl_price = round(exit_price - entry, 6)
    #   else:  # SHORT
    #       risk      = stop - entry
    #       pnl_price = round(entry - exit_price, 6)
    anchor_risk = (
        '        if direction == "LONG":\n'
        '            risk      = entry - stop\n'
        '            pnl_price = round(exit_price - entry, 6)\n'
        '        else:  # SHORT\n'
        '            risk      = stop - entry\n'
        '            pnl_price = round(entry - exit_price, 6)\n'
    )
    inject_risk = (
        '        # ' + MARKER + ': R считается от ПЕРВОГО стопа, а не текущего.\n'
        '        # Трейлинг двигает стоп в прибыль → |entry-stop| текущего\n'
        '        # уходил в минус → risk<0 → pnl_r=None. R — мера риска НА ВХОДЕ.\n'
        '        stop_r = pos.get("stop_initial", stop)  # fallback для старых позиций\n'
        '        if direction == "LONG":\n'
        '            risk      = entry - stop_r\n'
        '            pnl_price = round(exit_price - entry, 6)\n'
        '        else:  # SHORT\n'
        '            risk      = stop_r - entry\n'
        '            pnl_price = round(entry - exit_price, 6)\n'
    )
    if anchor_risk in src:
        src = src.replace(anchor_risk, inject_risk, 1)
        changes += 1
        print('[ПАТЧ] ✓ РУКА 2: risk в _settle_positions считается от stop_initial')
    else:
        print('[ПАТЧ] ✗ РУКА 2: якорь расчёта risk НЕ НАЙДЕН — файл изменён? останов')
        sys.exit(2)

    if changes == 0:
        print('[ПАТЧ] ⚠️  ничего не изменено')
        return

    # бэкап + запись
    bak = HOOKS.with_suffix('.py.bak_stop_initial')
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f'[ПАТЧ] 💾 бэкап: {bak.name}')

    HOOKS.write_text(src, encoding="utf-8")
    print(f'[ПАТЧ] ✅ применено рук: {changes}. Болезнь вылечена.')
    print('[ПАТЧ]    Теперь сделка со сработавшим сейфом получит честный +R')
    print('[ПАТЧ]    и попадёт в отчёт, а судья запишет черновик.')


if __name__ == "__main__":
    # ensure utf-8 stdout on Windows/PowerShell
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
