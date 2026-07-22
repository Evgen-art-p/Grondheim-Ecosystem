#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"
sys.path.insert(0, str(_BIRZHA))

from williams_core import read_mt5_csv, _smma_series

def shifted(series, shift):
    n = len(series)
    out = [None] * n
    for i in range(n):
        j = i - shift
        if j >= 0:
            out[i] = series[j]
    return out

def calc_ao(bars, fast=5, slow=34):
    n = len(bars)
    medians = [(b["high"] + b["low"]) / 2 for b in bars]
    
    def smma(data, period):
        result = [None] * len(data)
        if len(data) < period:
            return result
        result[period-1] = sum(data[:period]) / period
        for i in range(period, len(data)):
            result[i] = (result[i-1] * (period-1) + data[i]) / period
        return result
    
    sma_fast = smma(medians, fast)
    sma_slow = smma(medians, slow)
    
    ao = [None] * n
    for i in range(n):
        if sma_fast[i] is not None and sma_slow[i] is not None:
            ao[i] = sma_fast[i] - sma_slow[i]
    return ao

def find_simple_divergence(bars, ao, lookback=20):
    """Упрощенная дивергенция: цена новый экстремум, а AO не подтверждает"""
    n = len(bars)
    divergences = [False] * n
    
    for i in range(lookback, n):
        if ao[i] is None:
            continue
        
        start = max(0, i - lookback)
        
        # Собираем значения AO в окне
        ao_values = [ao[j] for j in range(start, i) if ao[j] is not None]
        if not ao_values:
            continue
        
        # Медвежья: цена выше, чем за lookback, а AO не выше
        max_price = max(bars[j]["high"] for j in range(start, i))
        max_ao = max(ao_values)
        
        if bars[i]["high"] > max_price and ao[i] < max_ao * 0.95:
            divergences[i] = True
        
        # Бычья: цена ниже, чем за lookback, а AO не ниже
        min_price = min(bars[j]["low"] for j in range(start, i))
        min_ao = min(ao_values)
        
        if bars[i]["low"] < min_price and ao[i] > min_ao * 1.05:
            divergences[i] = True
    
    return divergences

def find_divergence_bars(bars):
    n = len(bars)
    
    medians = [(b["high"] + b["low"]) / 2 for b in bars]
    jaw_raw = _smma_series(medians, 13)
    teeth_raw = _smma_series(medians, 8)
    lips_raw = _smma_series(medians, 5)
    
    jaw = shifted(jaw_raw, 8)
    teeth = shifted(teeth_raw, 5)
    lips = shifted(lips_raw, 3)
    
    ao = calc_ao(bars)
    divergences = find_simple_divergence(bars, ao)
    
    events = []
    for i in range(1, n):
        j, t, l = jaw[i], teeth[i], lips[i]
        if j is None or t is None or l is None:
            continue
        up = max(l, t, j)
        dn = min(l, t, j)
        b = bars[i]
        p = bars[i-1]
        mid = (b["high"] + b["low"]) / 2
        
        is_sell = b["high"] > p["high"] and b["close"] < mid and b["low"] > up
        is_buy = b["low"] < p["low"] and b["close"] > mid and b["high"] < dn
        
        if is_sell and divergences[i]:
            events.append({"bar_index": i, "date": b["date"], "side": "SELL"})
        elif is_buy and divergences[i]:
            events.append({"bar_index": i, "date": b["date"], "side": "BUY"})
    return events

def backtest(bars, events, point, spread_pips):
    n = len(bars)
    trades = []
    spread_cost = spread_pips * point
    
    for k, e in enumerate(events):
        i = e["bar_index"]
        side = e["side"]
        
        fill_i = i + 1
        if fill_i >= n:
            continue
        
        entry_price = bars[fill_i]["open"]
        
        if side == "BUY":
            stop_level = bars[i]["low"] - point
            entry_with_spread = entry_price + spread_cost
        else:
            stop_level = bars[i]["high"] + point
            entry_with_spread = entry_price - spread_cost
        
        risk = abs(entry_with_spread - stop_level)
        if risk <= 0:
            continue
        
        next_i = events[k+1]["bar_index"] if k+1 < len(events) else n-1
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
            if next_i < n:
                exit_price = bars[next_i]["open"]
                exit_reason = "FLIP"
            else:
                exit_price = bars[-1]["close"]
                exit_reason = "END"
        
        if side == "BUY":
            pnl = exit_price - entry_with_spread
        else:
            pnl = entry_with_spread - exit_price
        
        r = pnl / risk
        trades.append({
            "date": bars[fill_i]["date"],
            "side": side,
            "r": r,
            "exit_reason": exit_reason
        })
    
    return trades

def main():
    args = sys.argv[1:]
    if len(args) < 3:
        print("Использование: python proverit_canon_v6.py CSV SYMBOL LOT [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--spread SPREAD]")
        return
    
    csv_path = args[0]
    symbol = args[1]
    point = float(args[2])
    
    spread_pips = 0
    if "--spread" in args:
        spread_pips = float(args[args.index("--spread") + 1])
    
    start = None
    end = None
    if "--start" in args:
        start = args[args.index("--start") + 1]
    if "--end" in args:
        end = args[args.index("--end") + 1]
    
    full = Path(csv_path)
    if not full.is_absolute() and not full.exists():
        if (_ROOT / csv_path).exists():
            full = _ROOT / csv_path
        elif (_BIRZHA / "test_data" / csv_path).exists():
            full = _BIRZHA / "test_data" / csv_path
        elif (_BIRZHA / csv_path).exists():
            full = _BIRZHA / csv_path
    
    if not full.exists():
        print(f"❌ CSV не найден: {csv_path}")
        return
    
    bars = read_mt5_csv(str(full))
    
    def pd(d):
        return datetime.strptime(d.replace(".", "-")[:10], "%Y-%m-%d")
    
    events = find_divergence_bars(bars)
    
    if start or end:
        s = pd(start) if start else None
        en = pd(end) if end else None
        events = [e for e in events if (not s or pd(e["date"]) >= s) and (not en or pd(e["date"]) <= en)]
    
    print(f"{symbol}: баров={len(bars)}  сигналов с дивергенцией={len(events)}")
    trades = backtest(bars, events, point, spread_pips)
    
    if not trades:
        print("  -> сделок не взято")
        return
    
    wins = sum(1 for t in trades if t["r"] > 0)
    total = sum(t["r"] for t in trades)
    stops = sum(1 for t in trades if t["exit_reason"] == "STOP")
    flips = sum(1 for t in trades if t["exit_reason"] == "FLIP")
    
    print(f"  -> взято сделок={len(trades)}")
    print(f"  -> винрейт={100*wins/len(trades):.0f}%")
    print(f"  -> суммарно={total:+.2f}R")
    print(f"  -> средний={total/len(trades):+.2f}R")
    print(f"  -> по стопу: {stops}, по флипу: {flips}")
    print(f"  -> крупных побед (R>5): {sum(1 for t in trades if t['r'] > 5)}")
    
    if trades:
        print("\n  Последние 5 сделок:")
        for t in trades[-5:]:
            print(f"    {t['date']} {t['side']} R={t['r']:+.2f} ({t['exit_reason']})")

if __name__ == "__main__":
    main()