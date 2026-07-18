# -*- coding: utf-8 -*-
"""
ВОРОНКА: где теряются кандидаты в detect_divergent_bar

НОЛЬ LLM-ВЫЗОВОВ. Тот же приём, что 18.07 с компасом (замер показал:
15 честных точек без компаса против 2 с ним — и компас разжали).
Здесь то же самое, но для bdb_strong.

ФОРМУЛА (williams_core.py):
    bdb_candidate = bull_candidate or bear_candidate   # lower_low+upper_close
                                                        # (или зеркально BEAR)
    bdb_strong = bdb_candidate and is_peak and ao_diver

    angulation_ok СЧИТАЕТСЯ, но в bdb_strong НЕ ВХОДИТ (закомментирован
    как затвор — "оставлен как факт, что он врал"). Значит реальных
    ворот два: is_peak (резинка Джастин на пике) и ao_diver (дивер AO
    на этом самом баре).

ЧТО ДЕЛАЕТ: идёт по КАЖДОМУ бару (не с шагом!) на одном срезе истории
и считает, сколько раз выполняется каждое условие по отдельности и
в комбинации — воронка сверху вниз.

ЗАПУСК:
    python voronka_bdb.py                       # XAUUSD H4, 5000 баров
    python voronka_bdb.py XAUUSD H1 5000
    python voronka_bdb.py EURUSD D1 3000
"""
import contextlib
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
BIRZHA = REPO / "Биржа"
TEST_DATA = BIRZHA / "test_data"

WORD_TO_TF = {"MN1": "Monthly", "W1": "Weekly", "D1": "Daily", "H1": "Hourly"}


def _find_csv(symbol: str, tf: str) -> Path:
    word = WORD_TO_TF.get(tf)
    candidates = []
    if word:
        candidates.append(TEST_DATA / f"{symbol}{word}.csv")
    candidates.append(TEST_DATA / f"{symbol}{tf}.csv")
    candidates.append(TEST_DATA / f"{symbol}_{tf}.csv")
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{symbol} {tf} не найден в {TEST_DATA}")


def _point_for(bars):
    dec = 0
    for b in bars[:200]:
        for v in (b["open"], b["high"], b["low"], b["close"]):
            s = f"{v!r}"
            if "." in s:
                dec = max(dec, len(s.split(".")[1].rstrip("0")))
    return 10 ** (-(min(dec, 5) or 2))


def main() -> int:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
    tf = sys.argv[2] if len(sys.argv) > 2 else "H4"
    n_bars = int(sys.argv[3]) if len(sys.argv) > 3 else 5000

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

    bars = all_bars[-n_bars:] if len(all_bars) > n_bars else all_bars
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

    total = 0
    n_candidate = 0
    n_peak = 0
    n_diver = 0
    n_peak_and_diver = 0
    n_strong = 0
    n_angulation_ok = 0   # справочно — уже не затвор

    examples_candidate_only = []   # кандидат есть, strong нет — где теряем

    # идём по КАЖДОМУ бару окна, отдавая только историю ДО него
    start = max(40, 60)
    for i in range(start, len(bars) + 1):
        window = bars[:i]
        w_teeth = teeth_series[:i]
        w_lips = lips_series[:i] if lips_series else None
        w_ao = ao_series[:i]

        total += 1
        try:
            db = detect_divergent_bar(window, w_ao, w_teeth,
                                      point=point, lips_series=w_lips)
        except Exception:
            continue

        cand = db.get("bdb_candidate")
        peak = db.get("is_peak")
        diver = db.get("ao_divergence")
        strong = db.get("bdb_strong")
        ang_ok = db.get("angulation_ok")

        if cand:
            n_candidate += 1
            if peak:
                n_peak += 1
            if diver:
                n_diver += 1
            if peak and diver:
                n_peak_and_diver += 1
            if ang_ok:
                n_angulation_ok += 1
            if strong:
                n_strong += 1
            elif len(examples_candidate_only) < 5:
                reasons = []
                if not peak:
                    reasons.append(f"is_peak=False (tension={db.get('tension_ratio')})")
                if not diver:
                    reasons.append("ao_divergence=False")
                examples_candidate_only.append(
                    f"{window[-1]['date']} {db.get('direction')} — "
                    f"{', '.join(reasons) if reasons else '?'}")

    print("═" * 72)
    print(f"  ВОРОНКА detect_divergent_bar · {symbol} {tf} · {len(bars)} баров")
    print("═" * 72)
    print(f"  всего замеров (каждый бар)      : {total}")
    print(f"  bdb_candidate (lower_low+upper_close"
          f" или зеркально)     : {n_candidate:>6}  "
          f"({100*n_candidate/total:.1f}%)")
    if n_candidate:
        print(f"    ├─ из них is_peak=True (резинка на пике)   : "
              f"{n_peak:>6}  ({100*n_peak/n_candidate:.1f}% от кандидатов)")
        print(f"    ├─ из них ao_divergence=True                : "
              f"{n_diver:>6}  ({100*n_diver/n_candidate:.1f}% от кандидатов)")
        print(f"    ├─ оба разом (is_peak AND ao_divergence)    : "
              f"{n_peak_and_diver:>6}  ({100*n_peak_and_diver/n_candidate:.1f}% от кандидатов)")
        print(f"    ├─ angulation_ok (справочно, НЕ затвор)     : "
              f"{n_angulation_ok:>6}  ({100*n_angulation_ok/n_candidate:.1f}% от кандидатов)")
        print(f"    └─ bdb_strong (итог: cand AND peak AND diver): "
              f"{n_strong:>6}  ({100*n_strong/n_candidate:.1f}% от кандидатов, "
              f"{100*n_strong/total:.2f}% от всех баров)")
    print()
    if examples_candidate_only:
        print("  ПОЧЕМУ ТЕРЯЮТСЯ (кандидат есть, strong — нет), примеры:")
        for ex in examples_candidate_only:
            print(f"    · {ex}")
    print("═" * 72)
    if n_candidate and n_peak_and_diver == 0:
        print("  ⚠️  is_peak и ao_divergence НИКОГДА не совпадают одновременно —")
        print("      это структурный, не статистический ноль. Смотреть, не")
        print("      противоречат ли они друг другу по построению (одна из")
        print("      формул гасит другую).")
    elif n_candidate and n_strong / n_candidate < 0.05:
        worse = "is_peak" if n_peak < n_diver else "ao_divergence"
        print(f"  → узкое место — {worse}: он режет сильнее второго условия.")
    print("═" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
