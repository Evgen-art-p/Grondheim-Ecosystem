#!/usr/bin/env python3
# test_idivergence_bar.py
# ─────────────────────────────────────────────────────────────
# Точная формула из iDivergenceBar.mq4 (Necron, 2010) — НЕ трогает
# старый код репы, отдельный тестовый скрипт (правка Шефа 21.07).
#
# Аллигатор 13/8/5 СО СМЕЩЕНИЕМ (+8/+5/+3 — как MT4 iAlligator
# возвращает уже отображаемое, сдвинутое значение линии).
#
# SELL-бар: high[i] > high[i-1]  И  close[i] < середины бара
#           И  low[i] > up   (весь бар ВЫШЕ всех трёх линий разом)
# BUY-бар:  low[i]  < low[i-1]   И  close[i] > середины бара
#           И  high[i] < dn  (весь бар НИЖЕ всех трёх линий разом)
#   up = max(lips,teeth,jaw)   dn = min(lips,teeth,jaw)
#
# Вход/стоп — по КАНОН_ВХОДА §6.2 (Единая_торговая_система.txt):
#   BUY:  entry = high[i]+1pt (Buy Stop, пробой)   stop = low[i]-1pt
#   SELL: entry = low[i]-1pt  (Sell Stop, пробой)   stop = high[i]+1pt
# Ордер — ОТЛОЖЕННЫЙ: ждём, пока цена реально дойдёт до entry, иначе
# сделка не считается взятой. Держим до стопа или до следующего
# противоположного сигнала (флип), как в прошлых прогонах.
#
# ЗАПУСК:
#   py test_idivergence_bar.py Биржа/test_data/XAUUSDH4.csv XAUUSD 0.01
#   py test_idivergence_bar.py Биржа/test_data/EURUSDH1.csv EURUSD 0.00001 \
#       --start 2010.01.01 --end 2017.12.31
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path
from datetime import datetime

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"
if not _BIRZHA.exists():
    _BIRZHA = _ROOT
sys.path.insert(0, str(_BIRZHA))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from williams_core import read_mt5_csv, _smma_series  # noqa: E402


def shifted(series: list, shift: int) -> list:
    """Значение линии на баре i = сырой SMMA на баре (i-shift) — имитация
    отображаемого (смещённого вперёд) значения MT4 iAlligator."""
    n = len(series)
    out = [None] * n
    for i in range(n):
        j = i - shift
        if j >= 0:
            out[i] = series[j]
    return out


def find_divergence_bars(bars: list) -> list:
    n = len(bars)
    medians = [(b["high"] + b["low"]) / 2 for b in bars]
    jaw_raw = _smma_series(medians, 13)
    teeth_raw = _smma_series(medians, 8)
    lips_raw = _smma_series(medians, 5)

    jaw = shifted(jaw_raw, 8)
    teeth = shifted(teeth_raw, 5)
    lips = shifted(lips_raw, 3)

    events = []
    for i in range(1, n):
        j, t, l = jaw[i], teeth[i], lips[i]
        if j is None or t is None or l is None:
            continue
        up = max(l, t, j)
        dn = min(l, t, j)
        b, p = bars[i], bars[i - 1]
        mid = (b["high"] + b["low"]) / 2

        if b["high"] > p["high"] and b["close"] < mid and b["low"] > up:
            events.append({"bar_index": i, "date": b["date"], "side": "SELL"})
        elif b["low"] < p["low"] and b["close"] > mid and b["high"] < dn:
            events.append({"bar_index": i, "date": b["date"], "side": "BUY"})

    return events


def backtest(bars: list, events: list, point: float) -> list:
    n = len(bars)
    trades = []
    for k, e in enumerate(events):
        i = e["bar_index"]
        side = e["side"]
        if side == "BUY":
            entry_level = bars[i]["high"] + point
            stop_level = bars[i]["low"] - point
        else:
            entry_level = bars[i]["low"] - point
            stop_level = bars[i]["high"] + point

        risk = abs(entry_level - stop_level)
        if risk <= 0:
            continue

        next_i = events[k + 1]["bar_index"] if k + 1 < len(events) else n - 1

        # ждём заполнения отложенного ордера
        fill_i = None
        for j in range(i + 1, min(next_i, n)):
            if side == "BUY" and bars[j]["high"] >= entry_level:
                fill_i = j
                break
            if side == "SELL" and bars[j]["low"] <= entry_level:
                fill_i = j
                break
        if fill_i is None:
            continue  # ордер не сработал до следующего сигнала — сделка не взята

        exit_price = None
        exit_reason = None
        for j in range(fill_i, min(next_i, n)):
            if side == "BUY" and bars[j]["low"] <= stop_level:
                exit_price = stop_level
                exit_reason = "STOP"
                break
            if side == "SELL" and bars[j]["high"] >= stop_level:
                exit_price = stop_level
                exit_reason = "STOP"
                break
        if exit_price is None:
            exit_i = min(next_i, n - 1)
            exit_price = bars[exit_i]["close"]
            exit_reason = "FLIP"

        pnl = (exit_price - entry_level) if side == "BUY" else (entry_level - exit_price)
        r = pnl / risk
        trades.append({"date": bars[fill_i]["date"], "side": side,
                       "entry": entry_level, "stop": stop_level,
                       "exit": exit_price, "reason": exit_reason, "r": r})
    return trades


def main():
    args = sys.argv[1:]
    csv_path, symbol, point = args[0], args[1], float(args[2])

    def opt(name, d=None):
        return args[args.index(name) + 1] if name in args else d

    full = csv_path
    if not Path(full).is_absolute() and not Path(full).exists():
        full = str(_BIRZHA / csv_path)
    bars = read_mt5_csv(full)

    start = opt("--start")
    end = opt("--end")

    def pd(d):
        return datetime.strptime(d.replace(".", "-")[:10], "%Y-%m-%d")

    events = find_divergence_bars(bars)
    if start or end:
        s = pd(start) if start else None
        en = pd(end) if end else None
        events = [e for e in events if (not s or pd(e["date"]) >= s) and (not en or pd(e["date"]) <= en)]

    print(f"{symbol}: баров={len(bars)}  дивергентных баров найдено={len(events)}")

    trades = backtest(bars, events, point)
    if not trades:
        print("  -> сделок не взято")
        return

    wins = sum(1 for t in trades if t["r"] > 0)
    total = sum(t["r"] for t in trades)
    big = [t for t in trades if t["r"] > 5]
    print(f"  -> сигналов={len(events)}  взято сделок={len(trades)} "
          f"(остальные — ордер не заполнился до следующего сигнала)")
    print(f"  -> винрейт={100*wins/len(trades):.0f}%  суммарно={total:+.2f}R  "
          f"средний={total/len(trades):+.2f}R")
    print(f"  -> крупных побед (R>5): {len(big)}")
    for t in big:
        print(f"       {t['date']}  {t['side']}  R={t['r']:+.2f}")


if __name__ == "__main__":
    main()
