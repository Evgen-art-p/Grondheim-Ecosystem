# -*- coding: utf-8 -*-
"""
patch_paket_pyramida.py
════════════════════════════════════════════════════════════════════
ПИРАМИДА КАК ОДИН ПАКЕТ — ЧЕСТНЫЙ УЧЁТ (вариант А, канон шефа)

Пакет живёт одним телом: средневзвешенная цена входа, общий стоп,
полный объём. R меряется от ПЕРВОНАЧАЛЬНОГО риска первой ноги — того
риска, что был принят на входе. Долив по тренду → средняя растёт
медленнее цены → при выходе пакет отдаёт кратно больше R. Плюс не
обрезан — в этом вся суть пирамиды.

БОЛЕЗНЬ: _settle_positions считал pnl_r от входа ПЕРВОЙ ноги и БЕЗ
учёта лота. Долил объём — а R как у одиночной сделки. Сила пирамиды
(множитель прибыли на тренде) терялась в статистике.

ЛЕЧЕНИЕ — три точки:

  1. РОЖДЕНИЕ (hooks.py): позиция заводит поля пакета:
       entry_avg = entry (средняя = вход первой ноги)
       lot_base  = lot   (объём первой ноги)
       (risk0 берём при закрытии из stop_initial — он неизменен)

  2. ADD (tester_express.py, _primenit_vedenie): при доливе
       entry_avg = (entry_avg*lot + entry_new*add_lot)/(lot+add_lot)
       lot       += add_lot
     entry_new — текущая цена (close бара долива).

  3. ЗАКРЫТИЕ (hooks.py, _settle_positions): считаем ПО ПАКЕТУ:
       ea   = entry_avg (fallback entry — старые позиции)
       risk0 = |entry_первой − stop_initial|   (первонач. риск, от entry!)
       pnl_price = (exit − ea)  для LONG / (ea − exit) для SHORT
       pnl_lots  = pnl_price * (lot / lot_base)   ← множитель объёма пакета
       pnl_r     = pnl_lots / risk0
     Одиночная сделка (без доливов): lot==lot_base, ea==entry →
     формула = старая, ничего не меняется. Пирамида → R растёт честно.

ВАЖНО: risk0 считается от entry ПЕРВОЙ ноги и stop_initial — оба
неизменны с рождения. entry_avg для pnl, entry(перв.) для risk. Так R
= «во сколько раз пакет отбил первоначально принятый риск».

ИДЕМПОТЕНТЕН (маркер PAKET_PYRAMIDA_V1). Бэкапы — по одному на файл.
Запуск из корня Grondheim-Ecosystem:
    python patch_paket_pyramida.py
"""
import io
import sys
from pathlib import Path

MARKER = "PAKET_PYRAMIDA_V1"


def find(name):
    for base in (Path("Биржа"), Path("GRONDHEIM_CITY") / "Биржа"):
        p = base / name
        if p.exists():
            return p
    print(f"[ПАТЧ] ✗ не найден Биржа/{name} — запусти из корня")
    sys.exit(1)


def patch_hooks():
    path = find("hooks.py")
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("[ПАТЧ] ✓ hooks.py уже пропатчен")
        return
    orig = src

    # — A. РОЖДЕНИЕ: добавить entry_avg/lot_base после "lot": order.get("lot"),
    a_old = '            "lot":       order.get("lot"),\n'
    a_new = (
        '            "lot":       order.get("lot"),\n'
        '            # ' + MARKER + ': поля ПАКЕТА пирамиды. entry_avg —\n'
        '            # средневзвешенная цена входа (растёт при ADD). lot_base —\n'
        '            # объём первой ноги (для множителя R). Одиночная сделка:\n'
        '            # entry_avg==entry, lot==lot_base → расчёт как раньше.\n'
        '            **dict(zip(("entry_avg", "lot_base"),\n'
        '                      (lambda es: (es[0], order.get("lot")))(\n'
        '                          _otlozhka_entry_stop(order, chain)))),\n'
    )
    if a_old not in src:
        print("[ПАТЧ] ✗ hooks: якорь рождения (lot) не найден")
        sys.exit(2)
    src = src.replace(a_old, a_new, 1)

    # — B. ЗАКРЫТИЕ: пакетный расчёт pnl_r
    b_old = (
        '        stop_r = pos.get("stop_initial", stop)  # fallback для старых позиций\n'
        '        if direction == "LONG":\n'
        '            risk      = entry - stop_r\n'
        '            pnl_price = round(exit_price - entry, 6)\n'
        '        else:  # SHORT\n'
        '            risk      = stop_r - entry\n'
        '            pnl_price = round(entry - exit_price, 6)\n'
        '        pnl_r     = round(pnl_price / risk, 4) if risk > 0 else None\n'
    )
    b_new = (
        '        # ' + MARKER + ': ПАКЕТНЫЙ расчёт пирамиды (вариант А).\n'
        '        # risk0 — первоначальный риск ПЕРВОЙ ноги (entry vs stop_initial),\n'
        '        # неизменен. pnl — от СРЕДНЕЙ цены пакета × множитель объёма\n'
        '        # (lot/lot_base). Одиночная сделка: ea==entry, lot==lot_base →\n'
        '        # формула вырождается в старую, ничего не меняется.\n'
        '        stop_r    = pos.get("stop_initial", stop)  # первый стоп (неизменен)\n'
        '        ea        = pos.get("entry_avg", entry)    # средняя цена пакета\n'
        '        lot_base  = pos.get("lot_base") or pos.get("lot") or 1.0\n'
        '        lot_full  = pos.get("lot") or lot_base\n'
        '        try:\n'
        '            mult = float(lot_full) / float(lot_base) if lot_base else 1.0\n'
        '        except (TypeError, ZeroDivisionError):\n'
        '            mult = 1.0\n'
        '        if direction == "LONG":\n'
        '            risk      = entry - stop_r          # риск от ПЕРВОЙ ноги\n'
        '            pnl_price = round((exit_price - ea) * mult, 6)\n'
        '        else:  # SHORT\n'
        '            risk      = stop_r - entry\n'
        '            pnl_price = round((ea - exit_price) * mult, 6)\n'
        '        pnl_r     = round(pnl_price / risk, 4) if risk > 0 else None\n'
    )
    if b_old not in src:
        print("[ПАТЧ] ✗ hooks: якорь расчёта pnl_r не найден")
        sys.exit(3)
    src = src.replace(b_old, b_new, 1)

    bak = path.with_suffix(".py.bak_paket")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ hooks.py: рождение (entry_avg/lot_base) + пакетный R")


def patch_tester():
    path = find("tester_express.py")
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("[ПАТЧ] ✓ tester_express.py уже пропатчен")
        return
    orig = src

    # ADD: после наращивания лота обновить среднюю. Якорь — строка лота.
    old = '                p["lot"] = round(float(p.get("lot") or 0.0) + al, 4)\n'
    new = (
        '                # ' + MARKER + ': средневзвешенная цена ПАКЕТА.\n'
        '                # entry_new = close бара долива (текущая цена входа ноги).\n'
        '                _lot_old = float(p.get("lot") or 0.0)\n'
        '                _ea_old = float(p.get("entry_avg", p.get("entry") or 0.0))\n'
        '                _entry_new = float(close) if close is not None else _ea_old\n'
        '                _lot_new = _lot_old + al\n'
        '                if _lot_new > 0:\n'
        '                    p["entry_avg"] = round(\n'
        '                        (_ea_old * _lot_old + _entry_new * al) / _lot_new, 6)\n'
        '                p["lot"] = round(_lot_new, 4)\n'
    )
    if old not in src:
        print("[ПАТЧ] ✗ tester: якорь ADD (lot) не найден — примени "
              "patch_most_vedeniya.py сначала")
        sys.exit(4)
    src = src.replace(old, new, 1)

    bak = path.with_suffix(".py.bak_paket")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ tester_express.py: ADD обновляет entry_avg пакета")


def main():
    patch_hooks()
    patch_tester()
    print("[ПАТЧ] ✅ Пирамида-пакет достроена.")
    print("[ПАТЧ]    Долив растит объём и среднюю; R считается от")
    print("[ПАТЧ]    первоначального риска × множитель пакета. Плюс не обрезан.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
