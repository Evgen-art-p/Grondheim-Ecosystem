# -*- coding: utf-8 -*-
"""
СЧЁТЧИК v3: своя территория (VASYA_SVOY_RAZVOROT_V1)

НОЛЬ LLM-ВЫЗОВОВ. Совет не будится.

ЧТО БЫЛО НЕ ТАК В v2: пасть мерилась на РОДИТЕЛЬСКОМ этаже (Искры).
Ошибка того же рода, что путаница компаса и точки — смешение двух
масштабов там, где нужен один. «У каждого своя территория» (Шеф):
опора §6.3 — локальное свойство ЕГО ЖЕ волны. Разворотный бар и
Аллигатор, от которого он отбивается, — ОБА на этаже Василия.

Связь с Искрой остаётся только через НАСЛЕДОВАНИЕ этажа (step_down)
— она даёт ему территорию, но не судит его пасть.

ЧТО СЧИТАЕТ на каждом (актив × этаж-территория):
  · сколько раз нашёлся bdb_dir
  · из них — сколько сформировалось внутри ЕГО ЖЕ пасти
    (bdb_price между min/max его же jaw/teeth/lips на том же срезе)

ЗАПУСК: из корня репо
    python schetchik_vasya3.py               # всё, шаг 20
    python schetchik_vasya3.py 50 EURUSD      # один актив, шаг 50
"""
import contextlib
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
BIRZHA = REPO / "Биржа"
TEST_DATA = BIRZHA / "test_data"

TF_ORDER = ["MN1", "W1", "D1", "H12", "H8", "H4", "H1", "M30", "M15", "M10", "M5"]
WORD_TO_TF = {"Monthly": "MN1", "Weekly": "W1", "Daily": "D1", "Hourly": "H1"}

SLICE_BARS = 400
MIN_BARS = 60


def _scan_folder():
    found = {}
    if not TEST_DATA.exists():
        return found
    for p in sorted(TEST_DATA.glob("*.csv")):
        stem, tf, sym = p.stem, None, None
        for word, code in WORD_TO_TF.items():
            if stem.endswith(word):
                tf, sym = code, stem[: -len(word)]
                break
        if tf is None:
            m = re.match(r"^([A-Za-z]+)_?([A-Za-z]\d+)$", stem)
            if m:
                sym, tf = m.group(1), m.group(2).upper()
        if tf and sym:
            found.setdefault(sym.upper(), {})[tf] = p
    return found


def _point_for(bars):
    dec = 0
    for b in bars[:200]:
        for v in (b["open"], b["high"], b["low"], b["close"]):
            s = f"{v!r}"
            if "." in s:
                dec = max(dec, len(s.split(".")[1].rstrip("0")))
    return 10 ** (-(min(dec, 5) or 2))


def _in_own_mouth(price, alligator):
    jaw, teeth, lips = alligator.get("jaw"), alligator.get("teeth"), alligator.get("lips")
    vals = [v for v in (jaw, teeth, lips) if v is not None]
    if len(vals) < 3 or price is None:
        return None
    return min(vals) <= price <= max(vals)


def _run_one(path: Path, symbol: str, tf: str, step: int) -> dict:
    from williams_core import read_mt5_csv, build_market_data

    try:
        bars = read_mt5_csv(str(path))
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    if not bars or len(bars) < MIN_BARS + step:
        return {"error": f"мало баров ({len(bars) if bars else 0})"}

    point = _point_for(bars)
    total = len(bars)
    checks = hits = in_mouth = outside = unknown = 0
    examples = []

    i = max(MIN_BARS, SLICE_BARS)
    while i <= total:
        window = bars[max(0, i - SLICE_BARS): i]
        checks += 1
        try:
            md = build_market_data(window, symbol=symbol, timeframe=tf, point=point)
        except Exception:
            i += step
            continue
        if not md:
            i += step
            continue
        wf = md.get("wave_form", {}) or {}
        d = wf.get("bdb_dir")
        if d:
            hits += 1
            m = _in_own_mouth(wf.get("bdb_price"), md.get("alligator", {}) or {})
            if m is True:
                in_mouth += 1
            elif m is False:
                outside += 1
            else:
                unknown += 1
            if len(examples) < 2:
                a = md.get("alligator", {})
                examples.append(
                    f"{md.get('bar_time')} {d} @ {wf.get('bdb_price')} "
                    f"(пасть: {a.get('jaw')}/{a.get('teeth')}/{a.get('lips')}) "
                    f"{'В ПАСТИ' if m else 'снаружи' if m is False else '?'}")
        i += step

    return {"total": total, "checks": checks, "hits": hits,
            "in_mouth": in_mouth, "outside": outside, "unknown": unknown,
            "examples": examples}


def main() -> int:
    step, only_symbol = 20, None
    if len(sys.argv) > 1:
        try:
            step = int(sys.argv[1])
        except ValueError:
            only_symbol = sys.argv[1].upper()
    if len(sys.argv) > 2:
        only_symbol = sys.argv[2].upper()

    if str(BIRZHA) not in sys.path:
        sys.path.insert(0, str(BIRZHA))
    found = _scan_folder()
    if not found:
        print(f"✗ в {TEST_DATA} не найдено CSV")
        return 1

    print("═" * 74)
    print(f"  СВОЯ ТЕРРИТОРИЯ · разворот и пасть на ОДНОМ этаже · "
          f"шаг {step} · 0 LLM-вызовов")
    print("═" * 74)

    g = {"checks": 0, "hits": 0, "in_mouth": 0, "outside": 0, "unknown": 0}

    for sym in sorted(found):
        if only_symbol and sym != only_symbol:
            continue
        tfs = found[sym]
        order = [t for t in TF_ORDER if t in tfs] + \
                [t for t in sorted(tfs) if t not in TF_ORDER]
        print(f"\n  ▌{sym}")
        print(f"  {'этаж':6} {'замеров':>8} {'развор.':>8} {'частота':>10} "
              f"{'в пасти':>9} {'снаружи':>9}")
        print("  " + "─" * 66)
        for tf in order:
            with contextlib.redirect_stdout(io.StringIO()):
                r = _run_one(tfs[tf], sym, tf, step)
            if r.get("error"):
                print(f"  {tf:6} {r['error']}")
                continue
            freq = f"1 / {r['checks'] // r['hits']}" if r["hits"] else "—"
            pm = f"{100 * r['in_mouth'] / r['hits']:.0f}%" if r["hits"] else "—"
            po = f"{100 * r['outside'] / r['hits']:.0f}%" if r["hits"] else "—"
            print(f"  {tf:6} {r['checks']:>8} {r['hits']:>8} {freq:>10} "
                  f"{pm:>9} {po:>9}")
            for ex in r["examples"][:1]:
                print(f"         {ex}")
            for k in g:
                g[k] += r.get(k, 0)

    print("\n" + "═" * 74)
    h, c = g["hits"], g["checks"]
    if not c:
        print("  ничего не померено")
        return 1
    print(f"  ИТОГО: {c} замеров, {h} разворотных баров")
    if h:
        print(f"  опора §6.3 (пасть СВОЕГО этажа): "
              f"в пасти {g['in_mouth']} ({100 * g['in_mouth'] / h:.0f}%), "
              f"снаружи {g['outside']} ({100 * g['outside'] / h:.0f}%)")
    print("═" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
