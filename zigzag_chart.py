#!/usr/bin/env python3
# zigzag_chart.py
# ─────────────────────────────────────────────────────────────
# КАРТИНКА ДЛЯ СВЕРКИ — рисует настоящие свечи из CSV + метки автомата
# ног зигзага (zigzag_core.on_bar_md), теми же честными скользящими
# окнами, что видит живой Совет/тестер (без забегания вперёд). Чтобы
# сверить глазами с MT5/TradingView: открой тот же символ/ТФ на тех
# же датах и сравни, где автомат поставил метки.
#
# Метки на графике:
#   A▲/A▼   — старт ноги A (треугольник вверх/вниз по стороне)
#   A close — закрытие ноги A (х)
#   B▲/B▼   — старт ноги B
#   B close — закрытие ноги B
#   C attempt — начало попытки C (пунктирный треугольник)
#   C CONFIRMED — крупная звезда, цена пробила ногу A
#   C discarded — крестик, структура стёрта (не архивирована)
#
# ЗАПУСК (из корня репо, рядом с count_triggers.py):
#   python zigzag_chart.py test_data/EURUSDH4.csv EURUSD \
#       --start 2009.12.01 --end 2010.03.15 \
#       --out zigzag_check.png
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"
if not _BIRZHA.exists():
    print(f"ОШИБКА: не нашёл папку Биржа рядом с этим файлом ({_BIRZHA})")
    sys.exit(1)
sys.path.insert(0, str(_BIRZHA))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from williams_core import read_mt5_csv, build_market_data  # noqa: E402
from zigzag_core import ZigzagTracker, on_bar_md  # noqa: E402

_TEST_POINT = {
    "XAUUSD": 0.01,   "XAGUSD": 0.001,
    "EURUSD": 0.00001, "GBPUSD": 0.00001, "USDJPY": 0.001,
    "AUDUSD": 0.00001, "USDCHF": 0.00001, "USDCAD": 0.00001,
    "BTCUSD": 0.01,   "ETHUSD": 0.01,
}

_MARKERS = {
    "LEG_A_START":  dict(sym="^", size=90, offset=1),
    "LEG_A_CLOSE":  dict(sym="x", size=70, offset=0),
    "LEG_B_START":  dict(sym="^", size=90, offset=1),
    "LEG_B_CLOSE":  dict(sym="x", size=70, offset=0),
    "C_ATTEMPT_START": dict(sym="^", size=90, offset=1),
    "C_CONFIRMED":  dict(sym="*", size=260, offset=1),
    "C_DISCARDED":  dict(sym="x", size=90, offset=0),
    "CYCLE_ARCHIVED": dict(sym="s", size=60, offset=0),
    "РАЗВОРОТ_НА_C": dict(sym="D", size=170, offset=1),
}


def _parse_date(d):
    return datetime.strptime(d.replace(".", "-")[:10], "%Y-%m-%d")


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print("Использование: python zigzag_chart.py <csv> <symbol> "
              "--start YYYY.MM.DD --end YYYY.MM.DD [--out файл.png] [--point X]")
        sys.exit(1)
    csv_path, symbol = args[0], args[1]

    def _opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    start = _opt("--start")
    end = _opt("--end")
    out = _opt("--out", "zigzag_check.png")
    point_override = _opt("--point")

    point = float(point_override) if point_override else _TEST_POINT.get(symbol.upper())
    if point is None:
        print(f"⚠️  point для {symbol} неизвестен — укажи --point")
        sys.exit(1)

    full_path = csv_path
    if not Path(full_path).is_absolute() and not Path(full_path).exists():
        full_path = str(_BIRZHA / csv_path)
    bars = read_mt5_csv(full_path)
    if not bars:
        print(f"CSV не прочитан: {full_path}")
        sys.exit(1)

    if not start or not end:
        print("Укажи --start и --end (YYYY.MM.DD)")
        sys.exit(1)

    # индексы диапазона показа + запас истории СЛЕВА для разгона
    # индикаторов (SMMA34/AO нужно ~150 баров warmup)
    show_lo = next((i for i, b in enumerate(bars) if b["date"][:10].replace(".", "-") >= start.replace(".", "-")), 0)
    show_hi = next((i for i, b in enumerate(bars) if b["date"][:10].replace(".", "-") > end.replace(".", "-")), len(bars)) - 1
    warmup_lo = max(0, show_lo - 250)

    print(f"Диапазон показа: бары {show_lo}-{show_hi} "
          f"({bars[show_lo]['date']} → {bars[show_hi]['date']})")
    print(f"Гоняю автомат честным скользящим окном от бара {warmup_lo}...")

    state = ZigzagTracker.novoye_sostoyanie()
    events = []   # (bar_index, event_dict)
    for i in range(warmup_lo, show_hi + 1):
        window = bars[max(0, i - 199):i + 1]
        md = build_market_data(window, symbol=symbol, timeframe="H?", point=point)
        if not md:
            continue
        ev = on_bar_md(state, md)
        if ev and i >= show_lo:
            events.append((i, ev))

    print(f"Событий в окне показа: {len(events)}")
    for i, ev in events:
        print(f"  бар {i} {bars[i]['date']}: {ev['event']}")

    # ── рисуем свечи ──
    show_bars = bars[show_lo:show_hi + 1]
    dates = [_parse_date(b["date"]) for b in show_bars]

    fig, ax = plt.subplots(figsize=(max(14, len(show_bars) * 0.06), 8), dpi=140)

    for x, b in zip(dates, show_bars):
        color = "#2e7d32" if b["close"] >= b["open"] else "#c62828"
        ax.plot([x, x], [b["low"], b["high"]], color=color, linewidth=0.8, zorder=2)
        ax.plot([x, x], [b["open"], b["close"]], color=color, linewidth=3.2, zorder=3)

    y_lo = min(b["low"] for b in show_bars)
    y_hi = max(b["high"] for b in show_bars)
    y_span = y_hi - y_lo

    for i, ev in events:
        b = bars[i]
        x = _parse_date(b["date"])
        kind = ev["event"]
        m = _MARKERS.get(kind, dict(sym="o", size=60, offset=0))
        if kind == "РАЗВОРОТ_НА_C":
            # BUY-разворот ставим ПОД баром, SELL — НАД баром
            is_buy = ev.get("signal") == "BUY"
            y = (b["low"] - y_span * 0.05) if is_buy else (b["high"] + y_span * 0.05)
            col = "#00c853" if is_buy else "#d50000"
        else:
            y = (b["high"] + y_span * 0.03) if kind in ("LEG_A_START", "LEG_B_START",
                                                        "C_ATTEMPT_START", "C_CONFIRMED") \
                else (b["low"] - y_span * 0.03)
            col = ("#1565c0" if "A_" in kind else
                  "#6a1b9a" if "B_" in kind else
                  "#e65100" if kind.startswith("C_ATTEMPT") else
                  "#2e7d32" if kind == "C_CONFIRMED" else
                  "#b71c1c" if kind == "C_DISCARDED" else "#757575")
        ax.scatter([x], [y], marker=m["sym"], s=m["size"], zorder=6, color=col)
        label = f"{kind} {ev.get('signal','')}" if kind == "РАЗВОРОТ_НА_C" else kind
        ax.annotate(label, (x, y), fontsize=6, rotation=60,
                   textcoords="offset points", xytext=(0, 6 if y > b["high"] else -12),
                   ha="left")

    ax.set_title(f"{symbol} — автомат ног A-B-C ({bars[show_lo]['date']} → "
                f"{bars[show_hi]['date']})\nсвеча = реальный бар CSV, "
                f"метки = события zigzag_core (честное скользящее окно)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out)
    print(f"\nГотово: {out}")


if __name__ == "__main__":
    main()
