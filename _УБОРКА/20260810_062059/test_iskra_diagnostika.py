#!/usr/bin/env python3
# test_iskra_diagnostika.py — рядом с test_idivergence_bar.py
# ─────────────────────────────────────────────────────────────
# ИСКРА ПОД ТЕМИ ЖЕ ПРОВЕРКАМИ, ЧТО ПОХОРОНИЛИ СНАЙПЕР (01.08.2026).
#
# Формулу НЕ трогает и НЕ переписывает: импортирует find_divergence_bars
# и backtest прямо из test_idivergence_bar.py. Одно место правды — на
# острове дублирование логики уже давало 5990 ложных сигналов.
#
# Что проверяет и почему:
#
#   1. ШИРИНА РИСКА. risk = размах сигнального бара, величина плавающая.
#      Узкий бар → крохотный риск → та же победа считается как +8R
#      вместо +0.8R. Ровно этот механизм 01.08 похоронил Блок Пустых
#      Цен: там весь плюс сидел в сделках с самым тесным стопом (61%,
#      83%, 128% итога на трёх инструментах), а такой стоп в терминале
#      сносится первым же движением — бэктест на барах путь цены
#      внутри бара не видит и «сохраняет» то, что в жизни бы снесло.
#      Разрез по терцилям риск/ATR отвечает, здорова Искра или нет.
#
#   2. ПРОТЯЖКА ПОРОГА. Отбрасываем сделки с риском тоньше порога и
#      двигаем порог. Здорово: PF плавно едет, плюс держится широко.
#      Больно: PF растёт тем выше, чем тоньше допустимый риск — значит
#      меряем разрешение бара, а не рынок.
#      (Фильтрация постфактум законна: сделки Искры НЕ перекрываются,
#      выброс одной не меняет остальные.)
#
#   3. РАСПРЕДЕЛЕНИЕ ПО ВРЕМЕНИ. Толстый хвост (плюс размазан) или
#      везение на одном окне. Город уже различал: боевая формула —
#      концентрация 17-58%, фрактал-триггер Брута — 128-339% из одного
#      окна, в бой не пущен.
#
#   4. ЗНАЧИМОСТЬ. Средний R и его стандартная ошибка. Летопись даёт
#      суммы в R, но ни разу не отвечала на вопрос «а отличается ли
#      это от нуля». Для золота H4 после спреда там +63.37R на 2407
#      сделках — надо посмотреть, сколько это сигм.
#
# ВАЖНО про спред: летопись считала спред только на золоте. Здесь
# --spread обязателен к применению на КАЖДОМ инструменте, иначе
# сравнение нечестное. И помни известную недоделку самого движка:
# у ШОРТА стоп срабатывает с опозданием на спред (закрытие шорта —
# покупка по ASK, а код сверяет с бидовым хаем). То есть короткие
# сделки здесь всё ещё чуть добрее к нам, чем жизнь.
#
# ЗАПУСК (из того же места, откуда гоняешь test_idivergence_bar.py):
#   py test_iskra_diagnostika.py Биржа/test_data/XAUUSDH4.csv --spread 16
#   py test_iskra_diagnostika.py Биржа/test_data/EURUSDH1.csv --spread 2
#   py test_iskra_diagnostika.py Биржа/test_data/SP500Daily.csv --spread 50
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

from williams_core import read_mt5_csv                      # noqa: E402
from test_idivergence_bar import (                          # noqa: E402
    find_divergence_bars, backtest, guess_symbol_and_point,
)

OKON = 6
POROGI = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]


def naiti_csv(imya: str):
    """Ищет CSV по ГОЛОМУ имени, чтобы в команде не пришлось писать путь
    с кириллицей (терминал Шефа кириллицу в путях глотает). Сначала —
    как дали, потом обход всех папок под корнем."""
    kak_dali = Path(imya)
    if kak_dali.exists():
        return kak_dali
    if not imya.lower().endswith(".csv"):
        imya = imya + ".csv"
    nizhnee = imya.lower()
    tochnye, pokhozhie = [], []
    for p in _ROOT.rglob("*.csv"):
        if p.name.lower() == nizhnee:
            tochnye.append(p)
        elif p.stem.lower().startswith(nizhnee[:-4]):
            pokhozhie.append(p)
    naidennoe = tochnye or pokhozhie
    return naidennoe[0] if naidennoe else None


def atr_ryad(bars, period=14):
    """ATR простым сглаживанием — самодостаточно, без зависимостей."""
    n = len(bars)
    out = [None] * n
    tr = [None] * n
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


def svodka(rr):
    if not rr:
        return None
    n = len(rr)
    pobed = [x for x in rr if x > 0]
    ubytki = [x for x in rr if x <= 0]
    plyus = sum(pobed)
    minus = -sum(ubytki)
    sred = sum(rr) / n
    disp = sum((x - sred) ** 2 for x in rr) / (n - 1) if n > 1 else 0.0
    sko = disp ** 0.5
    se = sko / (n ** 0.5) if n else 0.0
    return {"n": n, "winrate": 100 * len(pobed) / n, "summa": sum(rr),
            "pf": (plyus / minus) if minus > 0 else None,
            "sred": sred, "se": se, "sigm": (sred / se) if se > 0 else 0.0}


def stroka(imya, rr, shirina=24):
    s = svodka(rr)
    if not s:
        return f"{imya:<{shirina}} {'—':>7}"
    pf = f"{s['pf']:.2f}" if s["pf"] is not None else "∞"
    return (f"{imya:<{shirina}} {s['n']:>7} {s['winrate']:>7.1f}% "
            f"{s['summa']:>9.2f} {pf:>6} {s['sred']:>+8.3f} {s['sigm']:>7.1f}σ")


def okna_stroka(sdelki, daty_granits):
    if not sdelki:
        return "—"
    itog = sum(t["r"] for t in sdelki)
    summy = []
    for k in range(OKON):
        nach, kon = daty_granits[k], daty_granits[k + 1]
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
        print("py test_iskra_diagnostika.py <csv> [--point ...] [--spread пункты]")
        print("\nСпред указывать ОБЯЗАТЕЛЬНО — летопись считала его только")
        print("на золоте, остальные цифры валовые и потому несравнимы.")
        sys.exit(1)

    def opt(name, d=None):
        return args[args.index(name) + 1] if name in args else d

    csv_path = args[0]
    symbol, point = guess_symbol_and_point(csv_path)
    if opt("--point"):
        point = float(opt("--point"))
    if point is None:
        print("Не угадал point по имени файла — передай --point 0.01")
        sys.exit(1)

    spread_p = float(opt("--spread", 0) or 0)
    spread = spread_p * point

    full = naiti_csv(csv_path)
    if full is None:
        print(f"\nНе нашёл файл «{csv_path}» нигде под {_ROOT}.")
        nashlos = sorted(p.name for p in _ROOT.rglob("*.csv"))[:25]
        if nashlos:
            print("Вот какие CSV лежат рядом — возьми имя отсюда:")
            for imya in nashlos:
                print(f"   {imya}")
        sys.exit(1)

    bars = read_mt5_csv(str(full))
    if not bars:
        print(f"Не прочитал бары: {full}")
        sys.exit(1)

    atr = atr_ryad(bars)
    po_date = {}
    for i, b in enumerate(bars):
        po_date.setdefault(b["date"], i)

    events = find_divergence_bars(bars)
    sdelki = backtest(bars, events, point, spread)

    # риск каждой сделки в единицах ATR — то, чего движок не считал
    for t in sdelki:
        i = po_date.get(t["date"])
        a = atr[i] if (i is not None and i < len(atr)) else None
        risk = abs(t["entry"] - t["stop"])
        t["risk_atr"] = (risk / a) if (a and a > 0) else None

    n = len(bars)
    granitsy = [bars[min(n - 1, k * n // OKON)]["date"] for k in range(OKON)] + [bars[-1]["date"]]

    print(f"\n{'═' * 78}")
    print(f"ИСКРА · ДИАГНОСТИКА  ·  {Path(csv_path).name}")
    print(f"{symbol or '?'} · point={point} · спред={spread_p}п · баров={len(bars)}")
    print(f"сигналов={len(events)} · взято сделок={len(sdelki)}")
    if spread_p == 0:
        print("\n⚠ СПРЕД НЕ УКАЗАН. Числа валовые, сравнивать с другими")
        print("  инструментами нельзя. Перезапусти с --spread.")
    print(f"{'═' * 78}")

    if not sdelki:
        print("\nСделок нет.")
        return

    zag = (f"\n{'':<24} {'Сделок':>7} {'Винрейт':>8} {'Сумма R':>9} "
           f"{'PF':>6} {'Сред R':>8} {'Значим':>8}")

    print(zag)
    print("-" * 78)
    print(stroka("ВСЕ СДЕЛКИ", [t["r"] for t in sdelki]))
    print(f"\n   Распределение: {okna_stroka(sdelki, granitsy)}")
    print("   'Значим' — на сколько стандартных ошибок средний R отстоит")
    print("   от нуля. Меньше 2σ — от случайности не отличается.")

    # ── 1. разрез по ширине риска ─────────────────────────
    s_atr = [t for t in sdelki if t["risk_atr"] is not None]
    print(f"\n{'─' * 78}")
    print("1. ГДЕ СИДИТ ПРИБЫЛЬ — РАЗРЕЗ ПО ШИРИНЕ РИСКА")
    print(f"{'─' * 78}")
    if len(s_atr) < 9:
        print("   Сделок мало для разреза.")
    else:
        s_atr.sort(key=lambda t: t["risk_atr"])
        k = len(s_atr) // 3
        gruppy = [("узкий риск", s_atr[:k]),
                  ("средний", s_atr[k:2 * k]),
                  ("широкий риск", s_atr[2 * k:])]
        print(zag)
        print("-" * 78)
        itog = sum(t["r"] for t in s_atr)
        for imya, g in gruppy:
            print(stroka(imya, [t["r"] for t in g]))
        print()
        for imya, g in gruppy:
            summa = sum(t["r"] for t in g)
            dolya = (summa / itog * 100) if itog else 0.0
            print(f"   {imya:<14} риск {g[0]['risk_atr']:.2f}–{g[-1]['risk_atr']:.2f} ATR"
                  f"   даёт {dolya:>6.0f}% итога   {okna_stroka(g, granitsy)}")
        print("\n   Плюс во всех трёх — Искра живёт сама.")
        print("   Весь плюс в узких — то же, что убило БПЦ.")

    # ── 2. протяжка порога минимального риска ─────────────
    print(f"\n{'─' * 78}")
    print("2. ПРОТЯЖКА ПОРОГА МИНИМАЛЬНОГО РИСКА")
    print(f"{'─' * 78}")
    print(zag)
    print("-" * 78)
    for p in POROGI:
        g = [t for t in s_atr if t["risk_atr"] >= p]
        if not g:
            continue
        print(stroka(f"риск ≥ {p:.2f} ATR", [t["r"] for t in g])
              + f"   {okna_stroka(g, granitsy)}")
    print("\n   PF плавно едет, плюс держится широко — порог не решает.")
    print("   PF тем выше, чем тоньше допустимый риск — меряем не рынок,")
    print("   а разрешение бара. Именно так выглядел БПЦ 01.08.")

    # ── 3. окна ───────────────────────────────────────────
    print(f"\n{'─' * 78}")
    print("3. РАСПРЕДЕЛЕНИЕ ПО ИСТОРИИ")
    print(f"{'─' * 78}")
    itog = sum(t["r"] for t in sdelki)
    print(f"   {'Окно':<26} {'Сделок':>7} {'Сумма R':>10} {'Доля':>8}")
    for k in range(OKON):
        nach, kon = granitsy[k], granitsy[k + 1]
        v = [t for t in sdelki if (nach <= t["date"] < kon)] if k < OKON - 1 \
            else [t for t in sdelki if nach <= t["date"] <= kon]
        s = sum(x["r"] for x in v)
        dolya = (s / itog * 100) if itog else 0.0
        print(f"   {nach[:10]}–{kon[:10]:<13} {len(v):>7} {s:>10.2f} {dolya:>7.0f}%")
    print()


if __name__ == "__main__":
    main()
