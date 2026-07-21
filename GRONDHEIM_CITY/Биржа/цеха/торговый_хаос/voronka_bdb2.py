# -*- coding: utf-8 -*-
"""
ВОРОНКА v2: СОБЫТИЯ, не бары (detect_divergent_bar)

НОЛЬ LLM-ВЫЗОВОВ.

ЧТО БЫЛО НЕ ТАК В v1: bdb_strong — состояние, которое может держаться
True несколько баров подряд (пока не отойдёт is_peak/ao_divergence).
v1 считал КАЖДЫЙ такой бар отдельной находкой — отсюда 45-172 находки
в год при ожидаемых 10-15 (Шеф, по опыту).

ЧТО СЧИТАЕТ ТЕПЕРЬ: только МОМЕНТ РОЖДЕНИЯ сигнала — переход
False → True на баре i относительно бара i-1 (по направлению
BULL/BEAR отдельно: смена направления тоже считается новым событием).
Плюс частота в год — из интервала между первой и последней датой.

ЗАПУСК:
    python voronka_bdb2.py                    # XAUUSD H4, вся история
    python voronka_bdb2.py EURUSD H1
    python voronka_bdb2.py EURUSD H4 20000     # последние 20000 баров
"""
import contextlib
import io
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]   # PERENOS_V_TSEH_V1: файл теперь в цеха/торговый_хаос/
BIRZHA = REPO / "Биржа"
TEST_DATA = BIRZHA / "test_data"
WORD_TO_TF = {"MN1": "Monthly", "W1": "Weekly", "D1": "Daily", "H1": "Hourly"}


def _find_csv(symbol, tf):
    word = WORD_TO_TF.get(tf)
    cands = []
    if word:
        cands.append(TEST_DATA / f"{symbol}{word}.csv")
    cands.append(TEST_DATA / f"{symbol}{tf}.csv")
    cands.append(TEST_DATA / f"{symbol}_{tf}.csv")
    for c in cands:
        if c.exists():
            return c
    raise FileNotFoundError(f"{symbol} {tf} не найден")


def _point_for(bars):
    dec = 0
    for b in bars[:200]:
        for v in (b["open"], b["high"], b["low"], b["close"]):
            s = f"{v!r}"
            if "." in s:
                dec = max(dec, len(s.split(".")[1].rstrip("0")))
    return 10 ** (-(min(dec, 5) or 2))


def _parse_date(s):
    s = s.strip()
    for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def main() -> int:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
    tf = sys.argv[2] if len(sys.argv) > 2 else "H4"
    n_bars = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if str(BIRZHA) not in sys.path:
        sys.path.insert(0, str(BIRZHA))
    from williams_core import (
        read_mt5_csv, compute_alligator, compute_ao_series,
        detect_divergent_bar,
    )

    path = _find_csv(symbol, tf)
    with contextlib.redirect_stdout(io.StringIO()):
        all_bars = read_mt5_csv(str(path))
    if not all_bars:
        print(f"✗ пусто: {path}")
        return 1

    bars = all_bars[-n_bars:] if n_bars else all_bars
    if len(bars) < 60:
        print(f"✗ мало баров: {len(bars)}")
        return 1

    point = _point_for(bars)
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    alligator = compute_alligator(highs, lows, point=point)
    ao_series = compute_ao_series(highs, lows)
    teeth_series = alligator.get("teeth_series")
    lips_series = alligator.get("lips_series")

    prev_strong_dir = None   # None / "BULL" / "BEAR" — что было ИСТИННЫМ на прошлом баре
    events = []               # список новорождённых событий

    start = 60
    for i in range(start, len(bars) + 1):
        window = bars[:i]
        w_teeth = teeth_series[:i]
        w_lips = lips_series[:i] if lips_series else None
        w_ao = ao_series[:i]
        try:
            db = detect_divergent_bar(window, w_ao, w_teeth,
                                      point=point, lips_series=w_lips)
        except Exception:
            continue

        cur_dir = db.get("direction") if db.get("bdb_strong") else None

        # СОБЫТИЕ = переход "не было True в эту сторону" -> "стало True"
        if cur_dir is not None and cur_dir != prev_strong_dir:
            events.append({"date": window[-1]["date"], "dir": cur_dir,
                           "price": window[-1]["low"] if cur_dir == "BULL"
                                    else window[-1]["high"]})
        prev_strong_dir = cur_dir

    total_bars = len(bars) - start + 1
    d0 = _parse_date(bars[start - 1]["date"])
    d1 = _parse_date(bars[-1]["date"])
    years = ((d1 - d0).days / 365.25) if (d0 and d1) else None

    print("═" * 74)
    print(f"  ВОРОНКА v2 (СОБЫТИЯ) · {symbol} {tf} · {len(bars)} баров")
    print("═" * 74)
    print(f"  диапазон дат           : {bars[start-1]['date']} → {bars[-1]['date']}")
    if years:
        print(f"  это примерно            : {years:.1f} лет")
    print(f"  баров прогнано          : {total_bars}")
    print(f"  СОБЫТИЙ (рождений сигнала): {len(events)}")
    if years and years > 0:
        print(f"  ЧАСТОТА                 : {len(events) / years:.1f} событий/год")
    print()
    if events:
        print("  первые 10 событий:")
        for e in events[:10]:
            print(f"    · {e['date']}  {e['dir']}  @ {e['price']}")
        if len(events) > 10:
            print(f"    ... и ещё {len(events) - 10}")
    print("═" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
