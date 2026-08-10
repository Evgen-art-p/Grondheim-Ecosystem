#!/usr/bin/env python3
# test_fractal_trigger.py
# ─────────────────────────────────────────────────────────────
# ФРАКТАЛ-ТРИГГЕР ДЛЯ БРУТА (§4/§6.1 канона, гл.11 Trading Chaos II
# изд., подтверждено дважды независимыми источниками — см.
# ИСКРА_ПЕРЕДЕЛКА_СПЕК.md правки 21-23). Собирает воедино все находки
# сессии 22.07. Не трогает старый код репы — отдельный файл.
#
# ЧТО СЧИТАЕТ (по шагам, честно, без ИИ внутри):
#
#   1. ФРАКТАЛ-ТРИГГЕР — момент ПОДТВЕРЖДЕНИЯ истинного фрактала вне
#      пасти (не момент пробоя, как в старом _hans_breakout). Фрактал
#      с центром на баре c впервые известен на баре c+lookback —
#      именно этот бар и есть момент триггера. Фильтр: фрактал-пик
#      выше сырой (без сдвига) Челюсти, фрактал-дно ниже неё.
#
#   2. ЖИВАЯ ТОЧКА — честная симуляция боевой `proverit_tochku`
#      (hooks.py): рождается на разворотнике Necron (том же, что
#      Искра), питается повторным сигналом той же стороны с GREEN/
#      SQUAT (compute_mfi), умирает на структурном сломе (close
#      против направления) или 3 бара TWR-нейтрали подряд.
#      Фрактал-триггер принимается ТОЛЬКО если совпадает по стороне
#      с живой точкой на этом баре — иначе отбрасывается (правка 22:
#      голый фрактал без этого условия — шум, ~0R).
#
#   3. НАСТОЯЩАЯ ВОЛНА 1 — спуск по лесенке ТФ (M5→M10→M15→M30→H1...),
#      ищем МЛАДШИЙ ТФ, на котором отрезок «рождение точки → фрактал»
#      реально укладывается в 100-140 баров (канон §3 — не формула,
#      ориентир масштаба чтения волны). Требует CSV с младшими ТФ
#      того же символа рядом (test_data/СИМВОЛТФ.csv). Если файлов
#      нет — предупреждает и пропускает этот фильтр (правка 22:
#      без него результат грубее, но не нулевой).
#
#   4. ВХОД/СТОП — механика sFractalStopOrders.mq4 (Necron, 2010):
#      Buy/Sell Stop на уровне фрактала, стоп — на ближайшем ранее
#      подтверждённом противоположном фрактале. Ордер НЕ обрывается
#      искусственно на следующем сигнале — висит до исполнения или
#      до --max-wait баров (по умолчанию 500, правка 23: обрывать
#      рано — терять большую часть преимущества, конспект Локи по
#      New Trading Dimensions подтвердился честным тестом).
#
# СИМВОЛ/POINT — угадываются по имени файла, как у test_idivergence_bar.py.
#
# ЗАПУСК — любой из вариантов:
#   py test_fractal_trigger.py Биржа/test_data/XAUUSDH4.csv
#   py test_fractal_trigger.py Биржа/test_data/GBPUSDH1.csv \
#       --start 2020.01.01 --end 2026.01.01 --spread 2.0 --max-wait 300
#   py test_fractal_trigger.py Биржа/test_data/XAUUSDH4.csv --wave1-scale
#       (включить спуск по ТФ — правка 24: ЭКСПЕРИМЕНТАЛЬНО, вместе
#       с долгим ожиданием портит результат на EURUSD, портит выборку;
#       по умолчанию ВЫКЛЮЧЕН)
# ─────────────────────────────────────────────────────────────

import sys
import bisect
from pathlib import Path
from datetime import datetime

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"
if not _BIRZHA.exists():
    _BIRZHA = _ROOT
sys.path.insert(0, str(_BIRZHA))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from williams_core import read_mt5_csv, _smma_series, detect_fractals, compute_mfi  # noqa: E402
from test_idivergence_bar import find_divergence_bars, guess_symbol_and_point  # noqa: E402

_TF_LADDER = ["M5", "M10", "M15", "M30", "H1", "H4", "H8", "H12", "D1", "Daily"]
_WAVE1_MIN, _WAVE1_MAX = 100, 140   # ориентир масштаба чтения волны, канон §3


# ═══════════════════════════════════════════════════════════
# 1. ФРАКТАЛ-ТРИГГЕР — момент подтверждения, не пробоя
# ═══════════════════════════════════════════════════════════

def find_fractal_triggers(bars: list, lookback: int = 2) -> list:
    n = len(bars)
    medians = [(b["high"] + b["low"]) / 2 for b in bars]
    jaw_series = _smma_series(medians, 13)   # сырая Челюсть, без сдвига

    fr = detect_fractals(bars, lookback=lookback)
    events = []
    for f in fr["all_up"]:
        ci = f["bar_index"] + lookback
        if ci >= n or jaw_series[ci] is None:
            continue
        if f["price"] > jaw_series[ci]:
            events.append({"bar_index": ci, "date": bars[ci]["date"], "side": "LONG",
                           "fractal_price": f["price"], "fractal_bar": f["bar_index"]})
    for f in fr["all_down"]:
        ci = f["bar_index"] + lookback
        if ci >= n or jaw_series[ci] is None:
            continue
        if f["price"] < jaw_series[ci]:
            events.append({"bar_index": ci, "date": bars[ci]["date"], "side": "SHORT",
                           "fractal_price": f["price"], "fractal_bar": f["bar_index"]})
    events.sort(key=lambda e: e["bar_index"])
    return events


# ═══════════════════════════════════════════════════════════
# 2. ЖИВАЯ ТОЧКА — честная симуляция proverit_tochku (hooks.py)
# ═══════════════════════════════════════════════════════════

def _rolling_sma(closes: list, period: int) -> list:
    n = len(closes)
    out = [None] * n
    s = 0.0
    for i in range(n):
        s += closes[i]
        if i >= period:
            s -= closes[i - period]
        if i >= period - 1:
            out[i] = s / period
    return out


def simulate_tochka(bars: list, necron_events: list):
    """Возвращает (tochka_dir_at, tochka_birth_at) — по одному значению
    на каждый бар: направление живой точки (или None) и бар её рождения."""
    n = len(bars)
    closes = [b["close"] for b in bars]
    tide = _rolling_sma(closes, 5)
    wave = _rolling_sma(closes, 13)
    ripple = _rolling_sma(closes, 34)

    necron_by_bar = {e["bar_index"]: e for e in necron_events}
    alive = False
    zp = None
    direction = None
    neutral_count = 0
    cur_birth = None
    tochka_dir_at = [None] * n
    tochka_birth_at = [None] * n

    for i in range(n):
        ev = necron_by_bar.get(i)
        if ev is not None and not alive:
            alive = True
            direction = "BULL" if ev["side"] == "BUY" else "BEAR"
            zp = bars[i]["low"] if ev["side"] == "BUY" else bars[i]["high"]
            neutral_count = 0
            cur_birth = i
        elif alive:
            fed = False
            if ev is not None:
                ev_dir = "BULL" if ev["side"] == "BUY" else "BEAR"
                if ev_dir == direction and i >= 1:
                    mfi = compute_mfi(bars[i], bars[i - 1], point=None)
                    if mfi["type"] in ("GREEN", "SQUAT"):
                        new_zp = min(zp, bars[i]["low"]) if direction == "BULL" else max(zp, bars[i]["high"])
                        if new_zp != zp:
                            zp = new_zp
                            fed = True
            if not fed:
                close = bars[i]["close"]
                broken = (direction == "BULL" and close < zp) or (direction == "BEAR" and close > zp)
                if broken:
                    alive = False; direction = None; zp = None; neutral_count = 0; cur_birth = None
                else:
                    if tide[i] is not None and wave[i] is not None and ripple[i] is not None:
                        lo, hi = min(wave[i], ripple[i]), max(wave[i], ripple[i])
                        if lo <= tide[i] <= hi:
                            neutral_count += 1
                            if neutral_count >= 3:
                                alive = False; direction = None; zp = None; neutral_count = 0; cur_birth = None
                        else:
                            neutral_count = 0
        tochka_dir_at[i] = direction if alive else None
        tochka_birth_at[i] = cur_birth if alive else None

    return tochka_dir_at, tochka_birth_at


# ═══════════════════════════════════════════════════════════
# 3. НАСТОЯЩАЯ ВОЛНА 1 — спуск по лесенке ТФ
# ═══════════════════════════════════════════════════════════

def _parse_dt(d: str) -> datetime:
    parts = d.split(" ")
    datepart = parts[0].replace(".", "-")
    timepart = parts[1] if len(parts) > 1 else "00:00"
    return datetime.strptime(f"{datepart} {timepart}", "%Y-%m-%d %H:%M")


def load_lower_tf_dates(symbol: str, working_tf: str) -> dict:
    """Грузит даты (не все поля — экономим память) младших ТФ того же
    символа, если файлы есть рядом в test_data. Честно пропускает то,
    чего нет."""
    if working_tf not in _TF_LADDER:
        return {}
    idx = _TF_LADDER.index(working_tf)
    out = {}
    for tf in _TF_LADDER[:idx]:
        path = _BIRZHA / "test_data" / f"{symbol}{tf}.csv"
        if not path.exists():
            continue
        try:
            tb = read_mt5_csv(str(path))
            out[tf] = [_parse_dt(b["date"]) for b in tb]
        except Exception:
            continue
    return out


def filter_real_wave1(bars: list, events_with_birth: list, tf_dates: dict) -> list:
    """events_with_birth: [(event, birth_bar_index), ...]. Возвращает
    только те event, где на КАКОМ-ТО младшем ТФ отрезок рождение->
    триггер укладывается в _WAVE1_MIN.._WAVE1_MAX баров."""
    if not tf_dates:
        return [e for e, _ in events_with_birth]   # фильтр недоступен — пропускаем честно

    out = []
    for e, bb in events_with_birth:
        t_start = _parse_dt(bars[bb]["date"])
        t_end = _parse_dt(bars[e["bar_index"]]["date"])
        for tf, dates in tf_dates.items():
            lo = bisect.bisect_left(dates, t_start)
            hi = bisect.bisect_right(dates, t_end)
            if _WAVE1_MIN <= hi - lo <= _WAVE1_MAX:
                out.append(e)
                break
    return out


# ═══════════════════════════════════════════════════════════
# 4. ВХОД/СТОП — sFractalStopOrders.mq4, долгое ожидание (правка 23)
# ═══════════════════════════════════════════════════════════

def backtest(bars: list, events: list, point: float, spread: float = 0.0,
            max_wait: int = 500) -> list:
    n = len(bars)
    fr = detect_fractals(bars, lookback=2)
    all_confirm = []
    for f in fr["all_up"]:
        ci = f["bar_index"] + 2
        if ci < n:
            all_confirm.append((ci, "up", f["price"]))
    for f in fr["all_down"]:
        ci = f["bar_index"] + 2
        if ci < n:
            all_confirm.append((ci, "down", f["price"]))
    all_confirm.sort(key=lambda x: x[0])

    ptr = 0
    known_up, known_down = [], []
    trades = []

    for e in events:
        i = e["bar_index"]
        side = e["side"]

        while ptr < len(all_confirm) and all_confirm[ptr][0] <= i:
            ci, typ, price = all_confirm[ptr]
            (known_up if typ == "up" else known_down).append((ci, price))
            ptr += 1

        if side == "LONG":
            entry_level = e["fractal_price"] + point
            if not known_down:
                continue
            stop_level = known_down[-1][1]
            real_entry = entry_level + spread
        else:
            entry_level = e["fractal_price"] - point
            if not known_up:
                continue
            stop_level = known_up[-1][1]
            real_entry = entry_level - spread

        risk = abs(real_entry - stop_level)
        if risk <= 0:
            continue

        limit = min(i + 1 + max_wait, n)
        fill_i = None
        for j in range(i + 1, limit):
            if side == "LONG" and bars[j]["high"] >= entry_level:
                fill_i = j; break
            if side == "SHORT" and bars[j]["low"] <= entry_level:
                fill_i = j; break
        if fill_i is None:
            continue

        exit_price = None
        exit_reason = None
        for j in range(fill_i, limit):
            if side == "LONG" and bars[j]["low"] <= stop_level:
                exit_price = stop_level; exit_reason = "STOP"; break
            if side == "SHORT" and bars[j]["high"] >= stop_level:
                exit_price = stop_level; exit_reason = "STOP"; break
        if exit_price is None:
            exit_i = min(limit - 1, n - 1)
            exit_price = bars[exit_i]["close"]
            exit_price = exit_price - spread if side == "LONG" else exit_price + spread
            exit_reason = "MAX_WAIT"

        pnl = (exit_price - real_entry) if side == "LONG" else (real_entry - exit_price)
        r = pnl / risk
        trades.append({"date": bars[fill_i]["date"], "side": side, "r": r, "reason": exit_reason})

    return trades


# ═══════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    if not args:
        print("py test_fractal_trigger.py <csv> [символ] [point] [--start ...] "
             "[--end ...] [--spread пункты] [--max-wait баров] "
             "[--wave1-scale] [--symbol ...] [--point ...] [--tf ...]")
        sys.exit(1)

    def opt(name, d=None):
        return args[args.index(name) + 1] if name in args else d

    csv_path = args[0]
    rest = args[1:]
    pos_symbol = rest[0] if rest and not rest[0].startswith("--") else None
    pos_point = None
    if pos_symbol is not None and len(rest) > 1 and not rest[1].startswith("--"):
        pos_point = rest[1]

    symbol = opt("--symbol", pos_symbol)
    point_arg = opt("--point", pos_point)
    guessed_symbol, guessed_point = guess_symbol_and_point(csv_path)
    if symbol is None:
        symbol = guessed_symbol or "?"
    point = float(point_arg) if point_arg is not None else guessed_point
    if point is None:
        print(f"Не смог угадать point по имени файла «{csv_path}» — передай --point явно.")
        sys.exit(1)

    # рабочий ТФ — угадываем по хвосту имени файла (после символа)
    working_tf = opt("--tf")
    if working_tf is None:
        stem = Path(csv_path).stem.upper()
        sym_prefix = symbol.upper() if symbol != "?" else ""
        working_tf = stem[len(sym_prefix):] if stem.startswith(sym_prefix) else None
        if working_tf == "DAILY":
            working_tf = "D1"

    full = csv_path
    if not Path(full).is_absolute() and not Path(full).exists():
        full = str(_BIRZHA / csv_path)
    bars = read_mt5_csv(full)

    spread = float(opt("--spread", 0) or 0) * point
    max_wait = int(opt("--max-wait", 500))
    use_wave1_scale = "--wave1-scale" in args   # ВЫКЛ по умолчанию — правка 24:
                                                    # вместе с долгим ожиданием (правка 23)
                                                    # портит результат на EURUSD (+49.74R
                                                    # -> -44.57R), хотя каждый порознь честно
                                                    # работал. Включай явно для эксперимента.
    skip_wave1_scale = not use_wave1_scale

    start = opt("--start")
    end = opt("--end")

    def pd(d):
        return datetime.strptime(d.replace(".", "-")[:10], "%Y-%m-%d")

    necron = find_divergence_bars(bars)
    tochka_dir, tochka_birth = simulate_tochka(bars, necron)
    fractal_events = find_fractal_triggers(bars)

    aligned = []
    for e in fractal_events:
        i = e["bar_index"]
        want = "BULL" if e["side"] == "LONG" else "BEAR"
        if tochka_dir[i] == want:
            aligned.append((e, tochka_birth[i]))

    print(f"{symbol} (point={point}, ТФ={working_tf or '?'}): баров={len(bars)}  "
         f"фрактал-триггеров={len(fractal_events)}  совпали с живой точкой={len(aligned)}")

    if skip_wave1_scale:
        events = [e for e, _ in aligned]
        print("  (спуск по ТФ выключен по умолчанию — правка 24, "
             "добавь --wave1-scale для эксперимента)")
    else:
        tf_dates = load_lower_tf_dates(symbol, working_tf) if working_tf else {}
        if not tf_dates:
            print(f"  ПРЕДУПРЕЖДЕНИЕ: нет CSV младших ТФ для {symbol} рядом в test_data/ — "
                 f"фильтр «настоящая волна 1» пропущен, результат грубее (правка 22).")
            events = [e for e, _ in aligned]
        else:
            events = filter_real_wave1(bars, aligned, tf_dates)
            print(f"  из них с настоящей волной 1 (100-140 баров на младшем ТФ): {len(events)}")

    if start or end:
        s = pd(start) if start else None
        en = pd(end) if end else None
        events = [e for e in events if (not s or pd(e["date"]) >= s) and (not en or pd(e["date"]) <= en)]
        print(f"  в заданном диапазоне дат: {len(events)}")

    trades = backtest(bars, events, point, spread, max_wait)
    if not trades:
        print("  -> сделок не взято")
        return

    wins = sum(1 for t in trades if t["r"] > 0)
    total = sum(t["r"] for t in trades)
    big = [t for t in trades if t["r"] > 5]
    print(f"  -> сделок={len(trades)}  винрейт={100*wins/len(trades):.0f}%  "
         f"суммарно={total:+.2f}R  средний={total/len(trades):+.2f}R")
    print(f"  -> крупных побед (R>5): {len(big)}")
    for t in big[:20]:
        print(f"       {t['date']}  {t['side']}  R={t['r']:+.2f}  ({t['reason']})")


if __name__ == "__main__":
    main()
