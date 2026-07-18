# -*- coding: utf-8 -*-
"""
СЧЁТЧИК v2: глаз Василия НА ЕГО МАСШТАБЕ (VASYA_SVOY_RAZVOROT_V1)

НОЛЬ LLM-ВЫЗОВОВ. Совет не будится. Чистая геометрия по CSV.

ЧТО БЫЛО НЕ ТАК В v1: разворот и пасть мерились на ОДНОМ этаже —
этаже Искры. Это бессмыслица: на масштабе Искры васина точка не его
вообще. Отсюда «0% в пасти» на всех этажах — цифра ни о чём.

КАК ПРАВИЛЬНО (фрактальность):
  · РАЗВОРОТ  — с ДОЧЕРНЕГО этажа (step_down от этажа Искры), где
    васина волна растянута на 100-140 баров (§3) и имеет СВОИ диверы,
    СВОЮ ангуляцию, СВОЙ отрыв от СВОЕГО Аллигатора. Ровно то, что
    делает _read_vasya_wave в бою.
  · ПАСТЬ     — с РОДИТЕЛЬСКОГО этажа (этаж Искры). То, что на H1
    выглядит отрывом от линий, на H4 — отскок внутри пасти. Один бар,
    два масштаба, два описания.
  · СИНХРОН   — оба этажа режутся по ОДНОЙ дате (bisect по bars[i].date),
    старший не заглядывает в будущее младшего.

СЛЕПОТА К АКТИВУ И ЭТАЖУ (Закон Картриджа): что лежит в папке — то и
меряем. Ни одного тикера и ни одного ТФ в коде.

ЗАПУСК: из корня репо
    python schetchik_vasya2.py                # всё, шаг 20
    python schetchik_vasya2.py 50             # реже замеры, быстрее
    python schetchik_vasya2.py 20 XAUUSD      # один актив
"""
import bisect
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

SLICE_BARS = 400      # сколько баров отдаём ядру на замер
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


def _in_mouth(price, jaw, teeth, lips):
    vals = [v for v in (jaw, teeth, lips) if v is not None]
    if len(vals) < 3 or price is None:
        return None
    return min(vals) <= price <= max(vals)


def _run_pair(child_path, parent_path, symbol, child_tf, parent_tf, step):
    """
    Разворот с child_tf, пасть с parent_tf, синхронно по дате.
    Возвращает статистику или {"error": ...}.
    """
    from williams_core import read_mt5_csv, build_market_data

    try:
        cb = read_mt5_csv(str(child_path))
        pb = read_mt5_csv(str(parent_path))
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    if not cb or len(cb) < MIN_BARS + step:
        return {"error": f"мало баров на {child_tf}"}
    if not pb or len(pb) < MIN_BARS:
        return {"error": f"мало баров на {parent_tf}"}

    c_point = _point_for(cb)
    p_point = _point_for(pb)
    p_dates = [b["date"] for b in pb]

    checks = hits = in_mouth = outside = unknown = 0
    examples = []

    i = max(MIN_BARS, SLICE_BARS)
    while i <= len(cb):
        checks += 1
        c_window = cb[max(0, i - SLICE_BARS): i]
        now = c_window[-1]["date"]
        try:
            c_md = build_market_data(c_window, symbol=symbol,
                                     timeframe=child_tf, point=c_point)
        except Exception:
            i += step
            continue
        if not c_md:
            i += step
            continue

        wf = c_md.get("wave_form", {}) or {}
        d = wf.get("bdb_dir")
        if d:
            hits += 1
            # ── родительский этаж на ТУ ЖЕ дату, без будущего ──
            j = bisect.bisect_right(p_dates, now)
            m = None
            if j >= MIN_BARS:
                p_window = pb[max(0, j - SLICE_BARS): j]
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        p_md = build_market_data(p_window, symbol=symbol,
                                                 timeframe=parent_tf,
                                                 point=p_point)
                except Exception:
                    p_md = None
                if p_md:
                    a = p_md.get("alligator", {}) or {}
                    m = _in_mouth(wf.get("bdb_price"), a.get("jaw"),
                                  a.get("teeth"), a.get("lips"))
            if m is True:
                in_mouth += 1
            elif m is False:
                outside += 1
            else:
                unknown += 1
            if len(examples) < 2:
                examples.append(
                    f"{now} {d} @ {wf.get('bdb_price')} → пасть {parent_tf}: "
                    f"{'ДА' if m else 'нет' if m is False else '?'}")
        i += step

    return {"total": len(cb), "checks": checks, "hits": hits,
            "in_mouth": in_mouth, "outside": outside,
            "unknown": unknown, "examples": examples}


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
    try:
        from mt5_feed import step_down
    except Exception as e:
        print(f"✗ лесенка не поднялась: {e}")
        return 1

    found = _scan_folder()
    if not found:
        print(f"✗ в {TEST_DATA} не найдено CSV")
        return 1

    print("═" * 78)
    print(f"  ГЛАЗ ВАСИЛИЯ НА ЕГО МАСШТАБЕ · шаг {step} · 0 LLM-вызовов")
    print("  разворот — с дочернего этажа · пасть — с родительского · синхронно")
    print("═" * 78)

    g = {"checks": 0, "hits": 0, "in_mouth": 0, "outside": 0, "unknown": 0}

    for sym in sorted(found):
        if only_symbol and sym != only_symbol:
            continue
        tfs = found[sym]
        order = [t for t in TF_ORDER if t in tfs]
        print(f"\n  ▌{sym}")
        print(f"  {'Искра':6} {'Вася':6} {'замеров':>8} {'развор.':>8} "
              f"{'частота':>10} {'в пасти':>9} {'снаружи':>9}")
        print("  " + "─" * 74)
        for parent_tf in order:
            child_tf = step_down(parent_tf)
            if not child_tf or child_tf not in tfs:
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                r = _run_pair(tfs[child_tf], tfs[parent_tf],
                              sym, child_tf, parent_tf, step)
            if r.get("error"):
                print(f"  {parent_tf:6} {child_tf:6} {r['error']}")
                continue
            freq = f"1 / {r['checks'] // r['hits']}" if r["hits"] else "—"
            pm = f"{100 * r['in_mouth'] / r['hits']:.0f}%" if r["hits"] else "—"
            po = f"{100 * r['outside'] / r['hits']:.0f}%" if r["hits"] else "—"
            print(f"  {parent_tf:6} {child_tf:6} {r['checks']:>8} {r['hits']:>8} "
                  f"{freq:>10} {pm:>9} {po:>9}")
            for ex in r["examples"][:1]:
                print(f"         {ex}")
            for k in g:
                g[k] += r.get(k, 0)

    print("\n" + "═" * 78)
    h, c = g["hits"], g["checks"]
    if not c:
        print("  ничего не померено")
        return 1
    print(f"  ИТОГО: {c} замеров, {h} разворотных баров на масштабе Василия")
    if h:
        print(f"  опора §6.3 (пасть родительского этажа): "
              f"в пасти {g['in_mouth']} ({100 * g['in_mouth'] / h:.0f}%), "
              f"снаружи {g['outside']} ({100 * g['outside'] / h:.0f}%), "
              f"неизвестно {g['unknown']}")
        print()
        if g["in_mouth"] * 2 >= h:
            print("  ✓ большинство васиных разворотов ложится в пасть старшего —")
            print("    это и есть §6.3: отрыв на своём этаже = опора на верхнем.")
        elif g["in_mouth"]:
            print("  ○ опора набирается частично. Смотреть, чем отличаются те,")
            print("    что попали в пасть — возможно, там и живёт настоящий §6.3.")
        else:
            print("  ⚠️  ни один не попал в пасть старшего. Либо опора меряется")
            print("      не пастью, либо этаж Василия выбран не тот.")
    else:
        print("  ⚠️  на масштабе Василия разворотов не найдено вовсе.")
    print("═" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
