#!/usr/bin/env python3
# test_iskra_ekstremum.py — рядом с test_idivergence_bar.py
# ─────────────────────────────────────────────────────────────
# ПРОВЕРКА ГИПОТЕЗЫ ШЕФА (01.08): "цена ходит резко ИЗ пасти, потом
# ОБРАТНО в пасть, и на экстремумах — Искра. Прибыль анализ делаем
# исходя из того, где это произошло."
#
# Переведено в измеримое БЕЗ визуальной оценки "пасть узкая/широкая":
# у каждого бара Necron уже есть готовое число — насколько бар
# высунулся ЗА линии Аллигатора в момент сигнала:
#   SELL: low[i] - up      (up = max(губы,зубы,челюсть))
#   BUY:  dn - high[i]     (dn = min(губы,зубы,челюсть))
# Нормируем на ATR, чтобы сравнивать разные инструменты и эпохи.
#
# Гипотеза: чем дальше бар высунулся за пасть, тем ближе он к
# настоящему истощению движения ("экстремум"), тем сильнее сигнал.
# Мелкое касание линии — вероятно шум внутри тренда, не разворот.
#
# НЕ переопределяет формулу сигнала — find_divergence_bars и backtest
# импортируются из test_idivergence_bar.py как есть, одно место
# правды. Этот скрипт только довешивает метрику "дистанция за пасть"
# на уже найденные сигналы и режет результат по ней.
#
# Никакого забегания вперёд: дистанция считается на самом баре
# сигнала, тем же способом, каким её видит формула в момент решения.
#
# ЗАПУСК (имя csv — голое, без пути и без кириллицы в команде):
#   py test_iskra_ekstremum.py XAUUSDH4 --spread 16
#   py test_iskra_ekstremum.py EURUSDH1 --spread 2
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"
if not _BIRZHA.exists():
    _BIRZHA = _ROOT
sys.path.insert(0, str(_BIRZHA))
sys.path.insert(0, str(_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from williams_core import read_mt5_csv, _smma_series           # noqa: E402
from test_idivergence_bar import (                              # noqa: E402
    find_divergence_bars, backtest, guess_symbol_and_point, shifted,
)

OKON = 6


def naiti_csv(imya: str):
    p = Path(imya)
    if p.exists():
        return p
    if not imya.lower().endswith(".csv"):
        imya = imya + ".csv"
    nizhnee = imya.lower()
    tochnye, pokhozhie = [], []
    for f in _ROOT.rglob("*.csv"):
        if f.name.lower() == nizhnee:
            tochnye.append(f)
        elif f.stem.lower().startswith(nizhnee[:-4]):
            pokhozhie.append(f)
    naidennoe = tochnye or pokhozhie
    return naidennoe[0] if naidennoe else None


def atr_ryad(bars, period=14):
    n = len(bars)
    out, tr = [None] * n, [None] * n
    for i in range(1, n):
        pc = bars[i - 1]["close"]
        tr[i] = max(bars[i]["high"] - bars[i]["low"],
                    abs(bars[i]["high"] - pc), abs(bars[i]["low"] - pc))
    summa = 0.0
    for i in range(1, n):
        if tr[i] is None:
            continue
        if i < period:
            summa += tr[i]
            if i == period - 1:
                out[i] = summa / (period - 1)
            continue
        prev = out[i - 1]
        out[i] = tr[i] if prev is None else (prev * (period - 1) + tr[i]) / period
    return out


def linii_alligatora(bars):
    """Те же смещённые линии, что внутри find_divergence_bars — не
    трогаем формулу сигнала, только пересчитываем линии для метрики."""
    medians = [(b["high"] + b["low"]) / 2 for b in bars]
    jaw = shifted(_smma_series(medians, 13), 8)
    teeth = shifted(_smma_series(medians, 8), 5)
    lips = shifted(_smma_series(medians, 5), 3)
    return jaw, teeth, lips


def svodka(rr):
    if not rr:
        return None
    n = len(rr)
    pobed = [x for x in rr if x > 0]
    ubytki = [x for x in rr if x <= 0]
    plyus, minus = sum(pobed), -sum(ubytki)
    sred = sum(rr) / n
    disp = sum((x - sred) ** 2 for x in rr) / (n - 1) if n > 1 else 0.0
    se = (disp ** 0.5) / (n ** 0.5) if n > 1 else 0.0
    return {"n": n, "winrate": 100 * len(pobed) / n, "summa": sum(rr),
            "pf": (plyus / minus) if minus > 0 else None,
            "sred": sred, "sigm": (sred / se) if se > 0 else 0.0}


def stroka(imya, rr, shirina=24):
    s = svodka(rr)
    if not s:
        return f"{imya:<{shirina}} {'—':>7}"
    pf = f"{s['pf']:.2f}" if s["pf"] is not None else "∞"
    return (f"{imya:<{shirina}} {s['n']:>7} {s['winrate']:>7.1f}% "
            f"{s['summa']:>9.2f} {pf:>6} {s['sred']:>+8.3f} {s['sigm']:>7.1f}σ")


def okna_stroka(sdelki, granitsy):
    if not sdelki:
        return "—"
    itog = sum(t["r"] for t in sdelki)
    summy = []
    for k in range(OKON):
        nach, kon = granitsy[k], granitsy[k + 1]
        v = [t for t in sdelki if (nach <= t["date"] < kon)] if k < OKON - 1 \
            else [t for t in sdelki if nach <= t["date"] <= kon]
        summy.append(sum(x["r"] for x in v))
    plyus = sum(1 for s in summy if s > 0)
    if itog <= 0:
        return f"{plyus}/{OKON} окон+"
    return f"{plyus}/{OKON} окон+, лучшее {max(summy) / itog * 100:.0f}%"


def main():
    args = sys.argv[1:]
    if not args:
        print("py test_iskra_ekstremum.py <csv> [--point ...] [--spread пункты]")
        sys.exit(0)

    def opt(name, d=None):
        return args[args.index(name) + 1] if name in args else d

    csv_path = args[0]
    symbol, point = guess_symbol_and_point(csv_path)
    if opt("--point"):
        point = float(opt("--point"))
    if point is None:
        print("Не угадал point — передай --point 0.01")
        sys.exit(1)

    spread_p = float(opt("--spread", 0) or 0)
    spread = spread_p * point

    full = naiti_csv(csv_path)
    if full is None:
        print(f"Не нашёл «{csv_path}».")
        sys.exit(1)

    bars = read_mt5_csv(str(full))
    if not bars:
        print("Не прочитал бары.")
        sys.exit(1)

    atr = atr_ryad(bars)
    jaw, teeth, lips = linii_alligatora(bars)

    events = find_divergence_bars(bars)
    sdelki = backtest(bars, events, point, spread)

    po_date_i = {}
    for i, b in enumerate(bars):
        po_date_i.setdefault(b["date"], i)

    # довешиваем метрику "дистанция за пасть в ATR" на каждую сделку —
    # берём бар СИГНАЛА (не бар входа), это тот момент, когда формула
    # решала, "экстремум это или нет"
    signal_i_by_date = {}
    for e in events:
        # сделка датируется баром ЗАПОЛНЕНИЯ ордера (в backtest), а не
        # баром сигнала — сопоставляем через ближайший сигнал не позже
        pass

    # проще и без риска рассинхрона: пересобираем сделки вручную из
    # backtest-совместимого прохода events -> ищем дистанцию на баре
    # самого сигнала (e['bar_index']), затем сшиваем с trades по order:
    # backtest сохраняет порядок events -> trades 1:в:1 по возможности,
    # но часть events не даёт сделки (ордер не заполнился). Сшиваем по
    # bar_index диапазону между сигналом и датой филла.
    events_by_index = {e["bar_index"]: e for e in events}
    dist_atr_by_signal_i = {}
    for i, e in events_by_index.items():
        j, t, l = jaw[i], teeth[i], lips[i]
        a = atr[i]
        if None in (j, t, l, a) or a <= 0:
            continue
        up, dn = max(l, t, j), min(l, t, j)
        b = bars[i]
        if e["side"] == "SELL":
            dist = (b["low"] - up) / a
        else:
            dist = (dn - b["high"]) / a
        dist_atr_by_signal_i[i] = dist

    # сшивка sdelki <-> дистанция: находим ближайший ПРЕДШЕСТВУЮЩИЙ
    # сигнал того же side для даты филла (fill_i >= signal_i всегда)
    events_sorted = sorted(events, key=lambda e: e["bar_index"])
    for t in sdelki:
        fill_date = t["date"]
        fill_i = po_date_i.get(fill_date)
        if fill_i is None:
            continue
        kandidat = None
        for e in events_sorted:
            if e["bar_index"] > fill_i:
                break
            if e["side"] == t["side"]:
                kandidat = e
        if kandidat is not None and kandidat["bar_index"] in dist_atr_by_signal_i:
            t["dist_atr"] = dist_atr_by_signal_i[kandidat["bar_index"]]

    n = len(bars)
    granitsy = [bars[min(n - 1, k * n // OKON)]["date"] for k in range(OKON)] + [bars[-1]["date"]]

    print(f"\n{'═' * 78}")
    print(f"ИСКРА · НА ЭКСТРЕМУМАХ ЛИ СРАБАТЫВАЕТ  ·  {Path(csv_path).name}")
    print(f"{symbol or '?'} · point={point} · спред={spread_p}п · сделок={len(sdelki)}")
    print(f"{'═' * 78}")

    zag = (f"\n{'':<24} {'Сделок':>7} {'Винрейт':>8} {'Сумма R':>9} "
           f"{'PF':>6} {'Сред R':>8} {'Значим':>8}")

    s_ok = [t for t in sdelki if t.get("dist_atr") is not None]
    if len(s_ok) < 9:
        print("\nСделок с метрикой мало для разреза.")
        return

    print(zag)
    print("-" * 78)
    print(stroka("ВСЕ СДЕЛКИ", [t["r"] for t in s_ok]))

    print(f"\n{'─' * 78}")
    print("РАЗРЕЗ ПО ГЛУБИНЕ ВЫСОВЫВАНИЯ ЗА ПАСТЬ АЛЛИГАТОРА (в ATR)")
    print(f"{'─' * 78}")
    print("Гипотеза Шефа: чем дальше бар высунулся за линии в момент")
    print("сигнала, тем ближе к настоящему экстремуму движения.\n")

    s_ok.sort(key=lambda t: t["dist_atr"])
    k = len(s_ok) // 3
    gruppy = [("у самой пасти (мелко)", s_ok[:k]),
              ("средне", s_ok[k:2 * k]),
              ("далеко за пастью", s_ok[2 * k:])]

    print(zag)
    print("-" * 78)
    for imya, g in gruppy:
        print(stroka(imya, [t["r"] for t in g]))

    print()
    itog = sum(t["r"] for t in s_ok)
    for imya, g in gruppy:
        summa = sum(t["r"] for t in g)
        dolya = (summa / itog * 100) if itog else 0.0
        print(f"   {imya:<22} дистанция {g[0]['dist_atr']:.2f}–{g[-1]['dist_atr']:.2f} ATR"
              f"   даёт {dolya:>6.0f}% итога   {okna_stroka(g, granitsy)}")

    print("\nЧитать так:")
    print("  · Прибыль растёт от 'у пасти' к 'далеко' — гипотеза Шефа")
    print("    подтверждается: глубокое высовывание = настоящий экстремум.")
    print("  · Плюс сидит в 'у самой пасти' — наоборот, срабатывания у")
    print("    линии сильнее, чем на далёких выбросах.")
    print("  · Ровно по центру, без перекоса — метрика не различает.\n")


if __name__ == "__main__":
    main()
