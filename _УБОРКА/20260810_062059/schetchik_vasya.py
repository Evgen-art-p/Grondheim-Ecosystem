# -*- coding: utf-8 -*-
"""
СЧЁТЧИК: живой ли глаз Василия (VASYA_SVOY_RAZVOROT_V1)

НОЛЬ LLM-ВЫЗОВОВ. Совет не будится. Чистая геометрия по CSV из
Биржа/test_data — тот же аппарат, что читает Василий в бою
(read_ao_wave_form через build_market_data), прогнанный по истории.

СЛЕПОТА К АКТИВУ И ЭТАЖУ (Закон Картриджа): скрипт НЕ знает заранее
ни одного тикера и ни одного ТФ. Что лежит в папке — то и меряет.

ЧТО СЧИТАЕТ на каждом (актив × этаж):
  · сколько баров пройдено
  · сколько раз нашёлся разворотный бар (bdb_dir не None)
  · частота: раз в сколько баров в среднем
  · ОПОРА §6.3: где именно сформировался разворот —
      В ПАСТИ  — цена бара внутри [min(jaw,teeth,lips), max(...)]
      СНАРУЖИ  — вне пасти
    Канон §6.3: надёжность даёт опора в Пасти (или на уровне волны 4).
    Если почти всё снаружи — это ещё не системный удар, а просто
    разворот где-то. Число покажет правду, а не спор.

БЕЗ ЗАГЛЯДЫВАНИЯ В БУДУЩЕЕ: на каждом шаге ядру отдаётся срез
bars[:i], последний бар среза — «сейчас». Ровно так же, как в бою.

ЗАПУСК: из корня репо
    python schetchik_vasya.py                 # всё, что в папке, шаг 20
    python schetchik_vasya.py 5               # шаг 5 (точнее, дольше)
    python schetchik_vasya.py 20 XAUUSD       # только один актив

Шаг — через сколько баров делать замер. Шаг 1 = каждый бар (очень
долго на 94k баров). Шаг 20 — быстрая разведка формы.
"""
import re
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parent
BIRZHA = REPO / "Биржа"
TEST_DATA = BIRZHA / "test_data"

# Лесенка Шефа — порядок для вывода. Файлы, которых нет, просто пропустятся.
TF_ORDER = ["MN1", "W1", "D1", "H12", "H8", "H4", "H1", "M30", "M15", "M10", "M5"]
# MT5 пишет старшие ТФ словом — мостик как в feed_source
WORD_TO_TF = {"Monthly": "MN1", "Weekly": "W1", "Daily": "D1", "Hourly": "H1"}

# Сколько баров отдаём ядру на каждом замере. Окно читалки 120 (§3),
# но izmerit_volnovuyu_strukturu смотрит глубже по полному ряду.
SLICE_BARS = 400
MIN_BARS = 60


def _scan_folder():
    """Что лежит в папке -> {symbol: {tf: path}}. Ничего не хардкодим."""
    found = {}
    if not TEST_DATA.exists():
        return found
    for p in sorted(TEST_DATA.glob("*.csv")):
        stem = p.stem
        tf = None
        sym = None
        for word, code in WORD_TO_TF.items():
            if stem.endswith(word):
                tf, sym = code, stem[: -len(word)]
                break
        if tf is None:
            m = re.match(r"^([A-Za-z]+)_?([A-Za-z]\d+)$", stem)
            if m:
                sym, tf = m.group(1), m.group(2).upper()
        if not tf or not sym:
            continue
        found.setdefault(sym.upper(), {})[tf] = p
    return found


def _point_for(bars):
    """
    Шаг цены из самих данных — ядро слепо к тикеру, и мы тоже.
    Смотрим, сколько знаков после точки реально используется.
    """
    dec = 0
    for b in bars[:200]:
        for v in (b["open"], b["high"], b["low"], b["close"]):
            s = f"{v!r}"
            if "." in s:
                dec = max(dec, len(s.split(".")[1].rstrip("0")))
    dec = min(dec, 5) or 2
    return 10 ** (-dec)


def _in_mouth(price, jaw, teeth, lips):
    """Опора §6.3: бар сформировался внутри Пасти Аллигатора?"""
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
    checks = 0
    hits = 0
    in_mouth = 0
    outside = 0
    unknown = 0
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
            allig = md.get("alligator", {}) or {}
            m = _in_mouth(wf.get("bdb_price"), allig.get("jaw"),
                          allig.get("teeth"), allig.get("lips"))
            if m is True:
                in_mouth += 1
            elif m is False:
                outside += 1
            else:
                unknown += 1
            if len(examples) < 3:
                examples.append(
                    f"{md.get('bar_time')} {d} @ {wf.get('bdb_price')} "
                    f"{'в пасти' if m else 'снаружи' if m is False else '?'}")
        i += step

    return {"total": total, "checks": checks, "hits": hits,
            "in_mouth": in_mouth, "outside": outside, "unknown": unknown,
            "examples": examples, "point": point}


def main() -> int:
    step = 20
    only_symbol = None
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

    # тише в консоли — ядро любит печатать
    import io, contextlib

    print("═" * 74)
    print(f"  ГЛАЗ ВАСИЛИЯ ПО ИСТОРИИ · шаг замера {step} баров · 0 LLM-вызовов")
    print(f"  папка: {TEST_DATA}")
    print("═" * 74)

    grand = OrderedDict()
    for sym in sorted(found):
        if only_symbol and sym != only_symbol:
            continue
        tfs = found[sym]
        order = [t for t in TF_ORDER if t in tfs] + \
                [t for t in sorted(tfs) if t not in TF_ORDER]
        print(f"\n  ▌{sym}")
        print(f"  {'этаж':6} {'баров':>8} {'замеров':>8} {'развор.':>8} "
              f"{'частота':>10} {'в пасти':>9} {'снаружи':>9}")
        print("  " + "─" * 70)
        for tf in order:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                r = _run_one(tfs[tf], sym, tf, step)
            if r.get("error"):
                print(f"  {tf:6} {'—':>8} {r['error']}")
                continue
            freq = (f"1 / {r['checks'] // r['hits']}" if r["hits"] else "—")
            pct_m = (f"{100 * r['in_mouth'] / r['hits']:.0f}%" if r["hits"] else "—")
            pct_o = (f"{100 * r['outside'] / r['hits']:.0f}%" if r["hits"] else "—")
            print(f"  {tf:6} {r['total']:>8} {r['checks']:>8} {r['hits']:>8} "
                  f"{freq:>10} {pct_m:>9} {pct_o:>9}")
            grand.setdefault("hits", 0)
            grand["hits"] += r["hits"]
            grand.setdefault("checks", 0)
            grand["checks"] += r["checks"]
            grand.setdefault("in_mouth", 0)
            grand["in_mouth"] += r["in_mouth"]
            grand.setdefault("outside", 0)
            grand["outside"] += r["outside"]
            for ex in r["examples"][:1]:
                print(f"         пример: {ex}")

    print("\n" + "═" * 74)
    h = grand.get("hits", 0)
    c = grand.get("checks", 0)
    if not c:
        print("  ничего не померено")
        return 1
    print(f"  ИТОГО: {c} замеров, {h} разворотных баров "
          f"({100 * h / c:.1f}% замеров)")
    if h:
        print(f"  опора §6.3: в пасти {grand['in_mouth']} "
              f"({100 * grand['in_mouth'] / h:.0f}%), "
              f"снаружи {grand['outside']} "
              f"({100 * grand['outside'] / h:.0f}%)")
        print()
        if grand["in_mouth"] * 2 < h:
            print("  ⚠️  большинство разворотов НЕ в пасти — по §6.3 это ещё")
            print("      не системный удар. Опора нужна как отдельный факт,")
            print("      иначе Василий входит на любом развороте подряд.")
        else:
            print("  ✓ опора набирается — геометрия ложится в канон §6.3.")
    else:
        print("  ⚠️  НИ ОДНОГО разворотного бара за всю историю на всех этажах.")
        print("      Глаз мёртв — смотреть detect_divergent_bar (bdb_strong).")
    print("═" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
