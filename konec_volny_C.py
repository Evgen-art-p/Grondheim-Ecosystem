#!/usr/bin/env python3
# konec_volny_C.py
# ─────────────────────────────────────────────────────────────
# ИНСТРУМЕНТ: найти КОНЕЦ ВОЛНЫ C — там, где он реально есть.
#
# НЕ пробой ноги A (C_CONFIRMED — это НАЧАЛО развязки, рано).
# НЕ разворотный бар/ромб (одна свеча слепая, стреляет на теле волны).
#
# КОНЕЦ ВОЛНЫ C = бар, на котором волна поставила свой ИСТИННЫЙ
# экстремум (самый низ для C-вниз / самый верх для C-вверх) И после
# которого пасть Аллигатора начала схлопываться (импульс выдохся).
# Это точка входа В ТРЕНД по Котину: коррекция кончилась, дальше
# рынок бежит в импульсе 1-2-3.
#
# КАК ОН ЕГО НАХОДИТ (честно, без магии):
#   1. zigzag_core доводит волну до фазы подтверждённой C и ведёт
#      бегущий экстремум leg["extreme"] — самый низ/верх, куда волна
#      дошла.
#   2. Пока пасть открыта в сторону C и цена делает новый экстремум —
#      волна ещё идёт, конец НЕ ставим.
#   3. Как только пасть переплелась (перестала быть открытой в сторону
#      C) — волна кончилась. КОНЕЦ_C ставится на том баре, где стоял
#      истинный экстремум (не на баре схлопывания, а на баре самого
#      низа/верха — возвращаемся к нему).
#
# Итог: одна метка ромбом на КАЖДОМ реальном конце волны C по всей
# истории. Свеча-экстремум подсвечена. Открываешь MT5 на той же дате —
# и проверяешь глазами: там ли настоящий конец коррекции.
#
# ЗАПУСК (из корня репо; CSV можно указать коротким путём — сам найдёт
# в папке Биржа, чтобы не печатать кириллицу в PowerShell):
#   py konec_volny_C.py test_data/EURUSDH4.csv EURUSD --start 2015.09.01 --end 2015.12.15 --out konec.png
#
# Можно без картинки, просто список дат концов волны:
#   py konec_volny_C.py test_data/EURUSDH4.csv EURUSD --list
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"
if not _BIRZHA.exists():
    # вдруг запускают уже из папки Биржа
    _BIRZHA = _ROOT
sys.path.insert(0, str(_BIRZHA))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from williams_core import read_mt5_csv, _smma_series, detect_fractals, fractal_outside_jaw  # noqa: E402

_TEST_POINT = {
    "XAUUSD": 0.01, "XAGUSD": 0.001,
    "EURUSD": 0.00001, "GBPUSD": 0.00001, "USDJPY": 0.001,
    "AUDUSD": 0.00001, "USDCHF": 0.00001, "USDCAD": 0.00001,
    "BTCUSD": 0.01, "ETHUSD": 0.01,
}

# состояния
ISCHU_A, VEDU_A = "ИЩУ_A", "ВЕДУ_A"
ZHDU_B, VEDU_B = "ЖДУ_B", "ВЕДУ_B"
ZHDU_C, VEDU_C = "ЖДУ_C", "ВЕДУ_C"
VEDU_CONF = "ВЕДУ_ПОДТВ_C"
_OPP = {"BULL": "BEAR", "BEAR": "BULL"}


def _series(bars, point):
    med = [(b["high"] + b["low"]) / 2 for b in bars]
    jaw = _smma_series(med, 13)
    teeth = _smma_series(med, 8)
    lips = _smma_series(med, 5)
    n = len(bars)
    thr = 50 * point if point else 0.0005
    bo = [0] * n
    for i in range(n):
        j, t, l = jaw[i], teeth[i], lips[i]
        if j is None or t is None or l is None:
            bo[i] = 0
            continue
        spread = max(abs(j - t), abs(t - l), abs(j - l))
        bo[i] = 0 if spread < thr else (bo[i - 1] + 1 if i > 0 else 1)
    fr = detect_fractals(bars)
    up = {}
    dn = {}
    for f in fr["all_up"]:
        idx = f["bar_index"]
        up[idx] = (f["price"], jaw[idx] is not None and fractal_outside_jaw(f["price"], jaw[idx], "LONG"))
    for f in fr["all_down"]:
        idx = f["bar_index"]
        dn[idx] = (f["price"], jaw[idx] is not None and fractal_outside_jaw(f["price"], jaw[idx], "SHORT"))
    return jaw, teeth, lips, bo, up, dn


def _dir(jaw_i, teeth_i, lips_i):
    if jaw_i is None or teeth_i is None or lips_i is None:
        return None
    return "BULL" if lips_i > teeth_i else "BEAR"


def _leg_dir(kind):  # UP-фрактал (вершина) -> нога вниз
    return "BEAR" if kind == "UP" else "BULL"


def find_konec_C(bars, point):
    """
    Возвращает список концов волны C:
      {bar_index, date, c_dir, signal, extreme_price}
    signal = BUY  для C-вниз (конец падения -> вход вверх по тренду)
    signal = SELL для C-вверх
    """
    jaw, teeth, lips, bo, up, dn = _series(bars, point)
    n = len(bars)

    phase = ISCHU_A
    a = b = c = None
    # для конца C: помним, на каком баре стоял истинный экстремум волны
    c_ext_idx = None
    out = []

    for i in range(n):
        sleeping = (bo[i] == 0)
        di = _dir(jaw[i], teeth[i], lips[i])

        if phase == ISCHU_A:
            for kind, m in (("UP", up), ("DOWN", dn)):
                if i in m:
                    nd = _leg_dir(kind)
                    price, outside = m[i]
                    if not sleeping and di == nd and outside:
                        a = {"extreme": price, "dir": nd}
                        phase = VEDU_A
                        break

        elif phase == VEDU_A:
            if not sleeping and di == a["dir"]:
                a["extreme"] = min(a["extreme"], bars[i]["low"]) if a["dir"] == "BEAR" else max(a["extreme"], bars[i]["high"])
            else:
                phase = ZHDU_B

        elif phase == ZHDU_B:
            nd = _OPP[a["dir"]]
            m = up if nd == "BEAR" else dn
            if i in m and not sleeping and di == nd and m[i][1]:
                b = {"extreme": m[i][0], "dir": nd}
                phase = VEDU_B

        elif phase == VEDU_B:
            if not sleeping and di == b["dir"]:
                b["extreme"] = min(b["extreme"], bars[i]["low"]) if b["dir"] == "BEAR" else max(b["extreme"], bars[i]["high"])
            else:
                phase = ZHDU_C

        elif phase == ZHDU_C:
            nd = a["dir"]
            m = up if nd == "BEAR" else dn
            if i in m and not sleeping and di == nd and m[i][1]:
                c = {"extreme": m[i][0], "dir": nd}
                c_ext_idx = i
                phase = VEDU_C

        elif phase == VEDU_C:
            # ждём пробоя ноги A ценой
            broke = (bars[i]["low"] < a["extreme"]) if c["dir"] == "BEAR" else (bars[i]["high"] > a["extreme"])
            if broke:
                # обновим экстремум и запомним бар
                if c["dir"] == "BEAR":
                    if bars[i]["low"] < c["extreme"]:
                        c["extreme"] = bars[i]["low"]; c_ext_idx = i
                else:
                    if bars[i]["high"] > c["extreme"]:
                        c["extreme"] = bars[i]["high"]; c_ext_idx = i
                phase = VEDU_CONF
            elif sleeping or di != c["dir"]:
                # пасть переплелась ДО пробоя — структура стёрта
                phase = ISCHU_A
                a = b = c = None
                c_ext_idx = None

        elif phase == VEDU_CONF:
            # ВОЛНА C ИДЁТ. Пока пасть открыта в сторону C и цена
            # делает новый экстремум — ведём экстремум, помним его бар.
            zhiva = (not sleeping and di == c["dir"])
            if zhiva:
                if c["dir"] == "BEAR":
                    if bars[i]["low"] < c["extreme"]:
                        c["extreme"] = bars[i]["low"]; c_ext_idx = i
                else:
                    if bars[i]["high"] > c["extreme"]:
                        c["extreme"] = bars[i]["high"]; c_ext_idx = i
            else:
                # ПАСТЬ ПЕРЕПЛЕЛАСЬ = ВОЛНА C КОНЧИЛАСЬ.
                # КОНЕЦ_C ставим на баре истинного экстремума.
                out.append({
                    "bar_index": c_ext_idx,
                    "date": bars[c_ext_idx]["date"],
                    "c_dir": c["dir"],
                    "signal": "BUY" if c["dir"] == "BEAR" else "SELL",
                    "extreme_price": c["extreme"],
                })
                phase = ISCHU_A
                a = b = c = None
                c_ext_idx = None

    return out


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print("py konec_volny_C.py <csv> <symbol> [--start YYYY.MM.DD --end YYYY.MM.DD] [--out файл.png] [--list]")
        sys.exit(1)
    csv_path, symbol = args[0], args[1]

    def opt(name, d=None):
        return args[args.index(name) + 1] if name in args else d

    point = _TEST_POINT.get(symbol.upper())
    if point is None:
        print(f"point для {symbol} неизвестен — допиши в _TEST_POINT")
        sys.exit(1)

    full = csv_path
    if not Path(full).is_absolute() and not Path(full).exists():
        full = str(_BIRZHA / csv_path)
    bars = read_mt5_csv(full)
    if not bars:
        print(f"CSV не прочитан: {full}")
        sys.exit(1)

    ends = find_konec_C(bars, point)
    print(f"Найдено концов волны C за всю историю: {len(ends)}")

    start = opt("--start")
    end = opt("--end")

    def in_win(d):
        dd = d[:10].replace(".", "-")
        if start and dd < start.replace(".", "-"):
            return False
        if end and dd > end.replace(".", "-"):
            return False
        return True

    shown = [e for e in ends if in_win(e["date"])]
    print(f"В окне показа: {len(shown)}")
    for e in shown:
        print(f"  {e['date']}  КОНЕЦ C  {e['signal']:4}  экстремум={e['extreme_price']:.5f}")

    if "--list" in args or "--out" not in args:
        return

    # ── картинка ──
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import datetime

    def pd(d):
        return datetime.strptime(d.replace(".", "-")[:10], "%Y-%m-%d")

    lo = next((i for i, b in enumerate(bars) if in_win(b["date"])), 0)
    hi = len(bars) - 1 - next((k for k, b in enumerate(reversed(bars)) if in_win(b["date"])), 0)
    sb = bars[lo:hi + 1]
    dts = [pd(b["date"]) for b in sb]

    fig, ax = plt.subplots(figsize=(max(14, len(sb) * 0.07), 8), dpi=140)
    for x, b in zip(dts, sb):
        col = "#2e7d32" if b["close"] >= b["open"] else "#c62828"
        ax.plot([x, x], [b["low"], b["high"]], color=col, lw=0.8, zorder=2)
        ax.plot([x, x], [b["open"], b["close"]], color=col, lw=3.2, zorder=3)

    ylo = min(b["low"] for b in sb)
    yhi = max(b["high"] for b in sb)
    span = yhi - ylo
    for e in shown:
        b = bars[e["bar_index"]]
        x = pd(b["date"])
        is_buy = e["signal"] == "BUY"
        y = (b["low"] - span * 0.05) if is_buy else (b["high"] + span * 0.05)
        ax.scatter([x], [y], marker="D", s=200, zorder=6,
                  color="#00c853" if is_buy else "#d50000",
                  edgecolors="black", linewidths=0.7)
        ax.annotate(f"КОНЕЦ C {e['signal']}", (x, y), fontsize=7, rotation=45,
                   textcoords="offset points", xytext=(0, -14 if is_buy else 6))

    ax.set_title(f"{symbol} — КОНЕЦ ВОЛНЫ C (истинный экстремум коррекции)\n"
                f"{sb[0]['date']} → {sb[-1]['date']}  •  ромб = вход в тренд по Котину")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    out = opt("--out", "konec.png")
    fig.savefig(out)
    print(f"\nГотово: {out}")


if __name__ == "__main__":
    main()
