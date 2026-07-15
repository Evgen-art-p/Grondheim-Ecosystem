# -*- coding: utf-8 -*-
"""
patch_otlozhka_spread.py  (v2 — под ЖИВОЙ main)
════════════════════════════════════════════════════════════════════
ДЕЛО 1 — ВСЕ ВХОДЫ ОТЛОЖКОЙ (канон Вильямса) + ПОПРАВКА НА СПРЕД

Адаптирован под текущий hooks.py на main, где уже влиты
STOP_INITIAL_R_V1 (stop_initial), entry_bias и слепок стола.
Рождение позиции сейчас: status="OPEN", opened_at=bar_time.

ДЕЛАЕТ:
  1. entry/stop/stop_initial берутся с ПОПРАВКОЙ НА СПРЕД:
       LONG  (Buy Stop, по Ask):  entry = high + 2×спред
                                  стоп снизу — как трейдер посчитал
       SHORT (Sell Stop, по Bid): entry = low − 3 пункта (−0.30)
                                  стоп сверху → stop + 2×спред (по Ask)
     stop_initial = спред-поправленный стоп (R от реального стопа заявки).
  2. status: "OPEN" → "PENDING" (+ "_ждёт_баров": 0).
     opened_at из рождения УБРАН — его ставит _aktivirovat_ordera
     в миг реального пробоя (~строка 568). Никто не входит по рынку.

  Логику отсчёта entry у трёх трейдеров (Брут/Аван/Консерватор) НЕ
  трогаем — они сами считают сырой entry/stop от своего бара.

Спред живой: md["mfi"]["spread"] × md["point"]. XAUUSD: point=0.01,
пункт=0.10 (цена тика). Проверено терминалом шефа.

ИДЕМПОТЕНТЕН (маркер OTLOZHKA_SPREAD_V2). Бэкап — один раз.
Запуск из корня:  python patch_otlozhka_spread.py
"""
import io
import sys
from pathlib import Path

MARKER = "OTLOZHKA_SPREAD_V2"


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
    """Живой спред В ЦЕНЕ из бара терминала.
    spread приходит в пунктах (целое из MT5), point — размер тика."""
    md = chain.get("market_data", {}) or {}
    point = md.get("point") or 0.01
    spread_pts = (md.get("mfi", {}) or {}).get("spread")
    if spread_pts is None:
        spread_pts = 0.0
    return float(spread_pts) * float(point)


def _otlozhka_entry_stop(order: dict, chain: dict):
    """(entry, stop) с поправкой на спред по стороне сделки.
    Трейдер посчитал сырой entry/stop от СВОЕГО бара — добавляем зазор.

    LONG  (Buy Stop, по Ask):  entry = high + 2*спред; стоп снизу — как есть.
    SHORT (Sell Stop, по Bid): entry = low - 3 пункта; стоп сверху + 2*спред.
    Нет сырых чисел — возвращаем как пришло (не выдумываем).
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
        if high is not None:
            entry = round(high + 2 * sp, 6)      # Buy Stop над баром, по Ask
        # стоп снизу по Bid — спред не мешает
    elif d == "SHORT":
        if low is not None:
            entry = round(low - 3 * punkt, 6)    # Sell Stop, запас 3 пункта
        if stop is not None:
            stop = round(stop + 2 * sp, 6)       # стоп сверху по Ask
    return entry, stop


'''


def main():
    path = find_hooks()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — нечего делать (идемпотентно)")
        return

    orig = src

    # ── Якорь 1: entry/stop/stop_initial в рождении позиции ──────
    anchor_es = (
        '            "entry":     order.get("entry"),\n'
        '            "stop":      order.get("stop"),\n'
        '            # STOP_INITIAL_R_V1: ПЕРВЫЙ стоп — неизменная мера риска R.\n'
        '            # Трейлинг/СЕЙФ перетирают "stop"; этот помнит вход.\n'
        '            "stop_initial": order.get("stop"),\n'
    )
    if anchor_es not in src:
        print("[ПАТЧ] ✗ якорь entry/stop не найден — покажи строки 940-955")
        sys.exit(2)

    zamena_es = (
        '            # ' + MARKER + ': entry/stop с поправкой на спред.\n'
        '            # LONG: high+2спреда (по Ask). SHORT: low-0.30, стоп+2спреда.\n'
        '            # stop_initial = спред-поправленный стоп (R от реального стопа).\n'
        '            **dict(zip(("entry", "stop", "stop_initial"),\n'
        '                      (lambda es: (es[0], es[1], es[1]))(\n'
        '                          _otlozhka_entry_stop(order, chain)))),\n'
    )
    src = src.replace(anchor_es, zamena_es, 1)

    # ── Якорь 2: status OPEN + opened_at → PENDING, без opened_at ──
    anchor_st = (
        '            "status":    "OPEN",\n'
        '            "mode":      order.get("status"),       # PAPER | LIVE\n'
        '            "opened_at": bar_time,\n'
    )
    if anchor_st not in src:
        print("[ПАТЧ] ✗ якорь status/opened_at не найден")
        sys.exit(3)

    zamena_st = (
        '            # ' + MARKER + ': ВСЕГДА отложка. Ждём пробоя, никто не\n'
        '            # входит по рынку. opened_at поставит _aktivirovat_ordera\n'
        '            # в миг реального пробоя (время ИСТИННОГО входа).\n'
        '            "status":    "PENDING",\n'
        '            "_ждёт_баров": 0,\n'
        '            "mode":      order.get("status"),       # PAPER | LIVE\n'
    )
    src = src.replace(anchor_st, zamena_st, 1)

    # ── Вставляем хелперы перед функцией рождения позиции ─────
    for def_anchor in ("def _apply_trading_results(", "def _settle_positions("):
        if def_anchor in src:
            src = src.replace(def_anchor, HELPER + def_anchor, 1)
            break
    else:
        print("[ПАТЧ] ✗ не нашёл, куда вставить хелпер — останов")
        sys.exit(4)

    bak = path.with_suffix(".py.bak_otlozhka_spread")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Отложка+спред включены (v2, под живой main).")
    print("[ПАТЧ]    Все входы — PENDING, ждут пробоя.")
    print("[ПАТЧ]    LONG: high+2спреда · SHORT: low-0.30, стоп+2спреда.")
    print("[ПАТЧ]    В логе: 📌 ЗАЯВКА → ⚡ АКТИВИРОВАН → 🔒 СЕЙФ.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
