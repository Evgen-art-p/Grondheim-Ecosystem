# -*- coding: utf-8 -*-
"""
patch_otlozhka_spread.py
════════════════════════════════════════════════════════════════════
ДЕЛО 1 (канон Вильямса + поправка на спред) — ВСЕ ВХОДЫ ОТЛОЖКОЙ

Заменяет прошлую версию (patch_vklyuchit_otlozhku.py) — та ставила
развилку «если рынок уже на цене → вход по рынку (OPEN)». Шеф отверг:
по системе НИКТО не входит по рынку. Всегда отложенный ордер, ждёт
пробоя. Не зацепил — не туда, не входим.

КАНОН (Bill Williams, Trading Chaos):
  • вход ВСЕГДА Buy Stop / Sell Stop, отложкой (не по рынку);
  • у каждого трейдера СВОЯ точка отсчёта (он сам считает entry):
      Брут §6.1 — пробой фрактала за пастью;
      Аван §6.2 — конец волны C, разворотный бар;
      Консерватор §6.3 — откат волны 2, приседающий разворотный.
    Мы НЕ трогаем их расчёт entry — только оформляем отложку и
    добавляем поправку на спред.

ПОПРАВКА НА СПРЕД (шеф, XAUUSD — проверено терминалом):
  point = 0.01 (размер тика).  пункт = 0.10 = 10 тиков (цена тика).
  спред = md["mfi"]["spread"] × point  — ЖИВОЙ, из бара терминала.

  График рисуется по Bid. Покупка и стоп-выше исполняются по Ask
  (Bid + спред) — они дойдут до уровня РАНЬШЕ, чем Bid-график покажет.
  Значит их надо отодвинуть на спред. Продажа — по Bid (=график),
  спред не мешает, там просто запас от прокола.

    LONG  (Buy Stop, по Ask):
        entry = high + 2×спред          (без тика — спред сам зазор)
        stop  снизу, по Bid — не трогаем (как трейдер посчитал)

    SHORT (Sell Stop, по Bid):
        entry = low − 3 пункта (−0.30)  (запас от ложного прокола)
        stop  СВЕРХУ, по Ask → stop + 2×спред  (чтоб не выбило раньше)

ЧТО ДЕЛАЕТ ПАТЧ:
  1. Ставит хелпер _otlozhka_entry_stop(order, chain): считает
     entry/stop с поправкой на спред по стороне сделки.
  2. В рождении позиции: entry/stop берутся из хелпера, статус ВСЕГДА
     PENDING (opened_at не ставится — его даст _aktivirovat_ordera
     в миг реального пробоя). Никакого OPEN по рынку.

ИДЕМПОТЕНТЕН (маркер OTLOZHKA_SPREAD_V1). Бэкап — один раз.
Запуск из корня проекта:  python patch_otlozhka_spread.py
"""
import io
import sys
from pathlib import Path

MARKER = "OTLOZHKA_SPREAD_V1"
PUNKT_ZOLOTO = 0.10   # цена тика XAUUSD = 1 пункт (из терминала: 0.1)


def find_hooks() -> Path:
    for p in (Path("Биржа") / "hooks.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "hooks.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден hooks.py — запусти из КОРНЯ проекта")
    sys.exit(1)


HELPER = '''
# ''' + MARKER + ''': отложка + поправка на спред ────────────────────
def _spread_price(chain: dict) -> float:
    """Живой спред В ЦЕНЕ из бара терминала. spread приходит в пунктах
    (целое из MT5), point — размер тика. spread_price = spread × point."""
    md = chain.get("market_data", {}) or {}
    point = md.get("point") or 0.01
    spread_pts = (md.get("mfi", {}) or {}).get("spread")
    if spread_pts is None:
        spread_pts = 0.0
    return float(spread_pts) * float(point)


def _otlozhka_entry_stop(order: dict, chain: dict):
    """Возвращает (entry, stop) с поправкой на спред по стороне сделки.
    Трейдер сам посчитал сырой entry/stop от СВОЕГО бара (фрактал /
    разворотный / приседающий) — мы только добавляем зазор на спред.

    LONG  (Buy Stop, по Ask):  entry = high + 2×спред; стоп снизу — как есть.
    SHORT (Sell Stop, по Bid): entry = low − 3 пункта;  стоп сверху + 2×спред.

    Если сырых чисел нет — возвращаем как пришло (не выдумываем).
    """
    d = (order.get("direction") or "").upper()
    entry = order.get("entry")
    stop = order.get("stop")
    md = chain.get("market_data", {}) or {}
    price = md.get("price", {}) or {}
    high = price.get("high")
    low = price.get("low")
    sp = _spread_price(chain)
    punkt = 0.10  # XAUUSD: 1 пункт = цена тика = 0.10

    if d == "LONG":
        # Buy Stop над баром, покупка по Ask → +2 спреда (без тика)
        if high is not None:
            entry = round(high + 2 * sp, 6)
        # стоп снизу закрывается по Bid — спред не мешает, оставляем
    elif d == "SHORT":
        # Sell Stop под баром, продажа по Bid → запас 3 пункта вниз
        if low is not None:
            entry = round(low - 3 * punkt, 6)
        # стоп СВЕРХУ закрывается по Ask → +2 спреда, чтоб не выбило раньше
        if stop is not None:
            stop = round(stop + 2 * sp, 6)

    return entry, stop


'''


def main():
    path = find_hooks()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — нечего делать (идемпотентно)")
        return

    orig = src

    # ── Якорь рождения позиции: жёсткий OPEN ──────────────────
    anchor = (
        '            "entry":     order.get("entry"),\n'
        '            "stop":      order.get("stop"),\n'
        '            "tp":        order.get("tp"),\n'
        '            "lot":       order.get("lot"),\n'
        '            "status":    "OPEN",\n'
        '            "mode":      order.get("status"),       # PAPER | LIVE\n'
        '            "opened_at": bar_time,\n'
    )
    if anchor not in src:
        print("[ПАТЧ] ✗ якорь рождения позиции не найден — файл изменён?")
        sys.exit(2)

    zamena = (
        '            # ' + MARKER + ': ВСЕГДА отложка. entry/stop с поправкой\n'
        '            # на спред (LONG +2спреда по Ask; SHORT −3 пункта, стоп\n'
        '            # сверху +2спреда). Статус PENDING — ждём пробоя, НИКОГДА\n'
        '            # не входим по рынку. opened_at поставит _aktivirovat_ordera\n'
        '            # в миг реального пробоя.\n'
        '            **dict(zip(("entry", "stop"),\n'
        '                      _otlozhka_entry_stop(order, chain))),\n'
        '            "tp":        order.get("tp"),\n'
        '            "lot":       order.get("lot"),\n'
        '            "status":    "PENDING",\n'
        '            "_ждёт_баров": 0,\n'
        '            "mode":      order.get("status"),       # PAPER | LIVE\n'
    )
    src = src.replace(anchor, zamena, 1)

    # ── Вставляем хелперы перед функцией рождения позиции ─────
    for def_anchor in ("def _apply_trading_results(", "def _settle_positions("):
        if def_anchor in src:
            src = src.replace(def_anchor, HELPER + def_anchor, 1)
            break
    else:
        print("[ПАТЧ] ✗ не нашёл, куда вставить хелпер — останов")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_otlozhka_spread")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Отложка+спред включены.")
    print("[ПАТЧ]    Все входы — PENDING (Buy/Sell Stop), ждут пробоя.")
    print("[ПАТЧ]    LONG: high+2спреда · SHORT: low−0.30, стоп+2спреда.")
    print("[ПАТЧ]    Никто не входит по рынку. В логе: 📌 ЗАЯВКА → ⚡ АКТИВИРОВАН.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
