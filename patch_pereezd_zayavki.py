# -*- coding: utf-8 -*-
"""
patch_pereezd_zayavki.py  (ДЕЛО 1б)
════════════════════════════════════════════════════════════════════
СНЯТИЕ/ПЕРЕЕЗД ЗАЯВКИ ПО ВИЛЬЯМСУ — не по счётчику баров, по СТРУКТУРЕ

КАНОН (Bill Williams): отложенная заявка живёт, пока:
  • не сработает (рынок пробил) — активируется;
  • не появится НОВЫЙ фрактал в ту же сторону — тогда старая заявка
    неактуальна, СТРУКТУРА СДВИНУЛАСЬ: заявку ПЕРЕВЫСТАВИТЬ от нового
    фрактала (± спред), стоп — под новый противоположный фрактал (§8);
  • цена не вернётся к старту сигнального фрактала — тогда сигнал
    отменён, заявку снять совсем.

БЫЛО: _aktivirovat_ordera снимал заявку тупо по ORDER_EXPIRE_BARS=10.
Это брокерская логика (day-order), НЕ Вильямс.

СТАЛО: на каждом баре для PENDING (после проверки «пробил»):
  1. Новый фрактал ПО ТРЕНДУ (сместился last_up для LONG / last_down
     для SHORT дальше в сторону сделки) → ПЕРЕЕЗД: entry от нового
     фрактала + спред, стоп от нового противоположного фрактала.
     Заявка остаётся PENDING на новом уровне.
  2. Цена вернулась к старту (LONG: close < стартовый уровень сигнала /
     SHORT: close > стартовый) → снять совсем.
  3. Счётчик баров EXPIRE остаётся КРАЙНЕЙ страховкой (фракталы могли
     замереть) — но теперь это подстраховка, не основной механизм.

Заявка помнит при рождении: entry_fractal_price (от какого фрактала),
entry_fractal_idx (bar_index — чтоб не «переезжать» на тот же самый),
signal_start (противоположный фрактал на миг рождения — старт сигнала).

Спред-поправка при переезде — та же, что при рождении:
  LONG entry = fractal_price + 2*спред ; стоп = opp_fractal (низ)
  SHORT entry = fractal_price - 3 пункта ; стоп = opp_fractal + 2*спред

ИДЕМПОТЕНТЕН (маркер PEREEZD_ZAYAVKI_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_pereezd_zayavki.py
"""
import io
import sys
from pathlib import Path

MARKER = "PEREEZD_ZAYAVKI_V1"


def find_hooks() -> Path:
    for p in (Path("Биржа") / "hooks.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "hooks.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден hooks.py — запусти из корня")
    sys.exit(1)


HELPER = '''
# ''' + MARKER + ''': переезд заявки за новым фракталом (Вильямс) ──────
def _pereezd_zayavki(pos, md):
    """Проверяет PENDING-заявку против текущей структуры фракталов.
    Возвращает:
      "MOVED"   — переехала на новый фрактал (pos обновлён на месте);
      "CANCEL"  — цена вернулась к старту, сигнал мёртв (снять);
      None      — ничего, ждём дальше.
    Спред-поправка та же, что при рождении.
    """
    d = (pos.get("direction") or "").upper()
    fr = md.get("fractals", {}) or {}
    price = md.get("price", {}) or {}
    close = price.get("close")
    point = md.get("point") or 0.01
    sp_pts = (md.get("mfi", {}) or {}).get("spread")
    sp = (float(sp_pts) * float(point)) if sp_pts is not None else 0.0
    punkt = 0.10

    if close is None:
        return None

    if d == "LONG":
        up = fr.get("last_up") or {}
        down = fr.get("last_down") or {}
        up_px = up.get("price") if isinstance(up, dict) else None
        up_idx = up.get("bar_index") if isinstance(up, dict) else None
        down_px = down.get("price") if isinstance(down, dict) else None

        # 2. возврат к старту сигнала — снять
        start = pos.get("signal_start")
        if start is not None and close < start:
            return "CANCEL"

        # 1. новый ВЕРХНИЙ фрактал (другой bar_index) ВЫШЕ прежнего → переезд
        old_idx = pos.get("entry_fractal_idx")
        old_px = pos.get("entry_fractal_price")
        if (up_px is not None and up_idx is not None
                and up_idx != old_idx
                and (old_px is None or up_px > old_px)):
            pos["entry"] = round(up_px + 2 * sp, 6)          # Buy Stop + спред
            if down_px is not None:
                pos["stop"] = round(down_px, 6)              # под новый низ
                pos["stop_initial"] = pos["stop"]            # R от новой опоры
                pos["signal_start"] = down_px                # новый старт сигнала
            pos["entry_fractal_price"] = up_px
            pos["entry_fractal_idx"] = up_idx
            pos["_ждёт_баров"] = 0                            # счётчик сброшен
            return "MOVED"

    elif d == "SHORT":
        up = fr.get("last_up") or {}
        down = fr.get("last_down") or {}
        down_px = down.get("price") if isinstance(down, dict) else None
        down_idx = down.get("bar_index") if isinstance(down, dict) else None
        up_px = up.get("price") if isinstance(up, dict) else None

        start = pos.get("signal_start")
        if start is not None and close > start:
            return "CANCEL"

        old_idx = pos.get("entry_fractal_idx")
        old_px = pos.get("entry_fractal_price")
        if (down_px is not None and down_idx is not None
                and down_idx != old_idx
                and (old_px is None or down_px < old_px)):
            pos["entry"] = round(down_px - 3 * punkt, 6)     # Sell Stop − 3 пункта
            if up_px is not None:
                pos["stop"] = round(up_px + 2 * sp, 6)       # над новым верхом
                pos["stop_initial"] = pos["stop"]
                pos["signal_start"] = up_px
            pos["entry_fractal_price"] = down_px
            pos["entry_fractal_idx"] = down_idx
            pos["_ждёт_баров"] = 0
            return "MOVED"

    return None


'''


def main():
    path = find_hooks()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src

    # 1. helper перед _aktivirovat_ordera
    def_anchor = "def _aktivirovat_ordera("
    if def_anchor not in src:
        print("[ПАТЧ] ✗ _aktivirovat_ordera не найдена")
        sys.exit(2)
    src = src.replace(def_anchor, HELPER + def_anchor, 1)

    # 2. вклиниваем проверку переезда ПЕРЕД счётчиком баров.
    #    Якорь — блок счётчика "не сработал".
    anchor = (
        '        # не сработал — считаем, сколько ждёт\n'
        '        zhdyot = pos.get("_ждёт_баров", 0) + 1\n'
    )
    if anchor not in src:
        print("[ПАТЧ] ✗ якорь счётчика баров не найден")
        sys.exit(3)
    inject = (
        '        # ' + MARKER + ': не пробил — сверяем со СТРУКТУРОЙ (Вильямс).\n'
        '        _pz = _pereezd_zayavki(pos, md)\n'
        '        if _pz == "CANCEL":\n'
        '            print(f"[ОРДЕР] 🚫 {pos.get(\'trader\')} {d} @ {entry} ОТМЕНЁН "\n'
        '                  f"— цена вернулась к старту сигнала (Вильямс)")\n'
        '            dirty = True\n'
        '            continue          # снять заявку совсем\n'
        '        if _pz == "MOVED":\n'
        '            print(f"[ОРДЕР] 🔄 {pos.get(\'trader\')} {d} ПЕРЕЕХАЛ @ "\n'
        '                  f"{pos.get(\'entry\')} — новый фрактал по тренду, стоп "\n'
        '                  f"{pos.get(\'stop\')} (Вильямс §8)")\n'
        '            dirty = True\n'
        '            ostalis.append(pos)\n'
        '            continue          # PENDING на новом уровне\n'
        '\n'
        '        # не сработал — считаем, сколько ждёт\n'
        '        zhdyot = pos.get("_ждёт_баров", 0) + 1\n'
    )
    src = src.replace(anchor, inject, 1)

    # 3. при рождении PENDING запоминаем фрактал-старт. Якорь — _ждёт_баров:0
    birth_anchor = '            "_ждёт_баров": 0,\n'
    if birth_anchor in src:
        birth_inject = (
            '            "_ждёт_баров": 0,\n'
            '            # ' + MARKER + ': заявка помнит, ОТ КАКОГО фрактала родилась,\n'
            '            # и старт сигнала (противоположный фрактал) — для переезда/снятия.\n'
            '            **_zapomnit_fraktal_starta(order, chain),\n'
        )
        src = src.replace(birth_anchor, birth_inject, 1)

        # helper запоминания — рядом с _pereezd
        remember = (
            'def _zapomnit_fraktal_starta(order, chain):\n'
            '    """При рождении PENDING: запоминаем фрактал входа и старт\n'
            '    сигнала (противоположный фрактал) — опоры для переезда."""\n'
            '    d = (order.get("direction") or "").upper()\n'
            '    md = chain.get("market_data", {}) or {}\n'
            '    fr = md.get("fractals", {}) or {}\n'
            '    up = fr.get("last_up") or {}\n'
            '    down = fr.get("last_down") or {}\n'
            '    if d == "LONG":\n'
            '        f = up if isinstance(up, dict) else {}\n'
            '        opp = down if isinstance(down, dict) else {}\n'
            '    else:\n'
            '        f = down if isinstance(down, dict) else {}\n'
            '        opp = up if isinstance(up, dict) else {}\n'
            '    return {\n'
            '        "entry_fractal_price": f.get("price"),\n'
            '        "entry_fractal_idx":   f.get("bar_index"),\n'
            '        "signal_start":        opp.get("price"),\n'
            '    }\n'
            '\n'
            '\n'
            'def _aktivirovat_ordera('
        )
        src = src.replace("def _aktivirovat_ordera(", remember, 1)
        print("[ПАТЧ] ✓ рождение помнит фрактал-старт")
    else:
        print("[ПАТЧ] ⚠️  якорь рождения PENDING не найден — переезд будет "
              "работать, но без стартовой памяти (первый фрактал не запомнен)")

    bak = path.with_suffix(".py.bak_pereezd")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Дело 1б: заявка снимается/переезжает по СТРУКТУРЕ.")
    print("[ПАТЧ]    Новый фрактал по тренду → переезд (🔄). Возврат к")
    print("[ПАТЧ]    старту → отмена (🚫). Счётчик баров — крайняя страховка.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
