#!/usr/bin/env python3
# count_triggers.py
# ─────────────────────────────────────────────────────────────
# Бесплатный (без LLM, ноль долларов) подсчёт: сколько раз за ВСЮ
# историю сработал бы каждый из трёх триггеров Совета:
#   А — свежий спуск ядра (то, что раньше называлось "кандидат")
#   Б — фрактал Ганса на живой точке
#   В — Большой палец Авантюриста на живой точке
#
# Это ОЦЕНКА СВЕРХУ для триггера А (ядро грубее живой Искры — она
# своим голосом часть кандидатов отсеет, как видно на реальных
# прогонах). А вот Б и В — уже настоящие: они вообще не спрашивают
# Искру, просто ждут живую точку. Если по ним нули на всей истории —
# это честный факт про данные, не повод чинить код.
#
# НИКАКОГО trading_state.json не трогает (точка живёт в памяти этого
# скрипта, не на диске) — реальный прогон тестера этим не заденет.
#
# ЗАПУСК (из корня репо):
#   python count_triggers.py test_data/XAUUSDH4.csv XAUUSD H4
#   python count_triggers.py test_data/XAUUSDH4.csv XAUUSD H4 --warmup 100
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"

if not _BIRZHA.exists():
    print(f"ОШИБКА: не нашёл папку Биржа рядом с этим файлом ({_BIRZHA})")
    sys.exit(1)

sys.path.insert(0, str(_BIRZHA))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from williams_core import read_mt5_csv, build_market_data  # noqa: E402
from hooks import _hans_breakout  # noqa: E402


_TEST_POINT = {
    "XAUUSD": 0.01,   "XAGUSD": 0.001,
    "EURUSD": 0.00001, "GBPUSD": 0.00001, "USDJPY": 0.001,
    "AUDUSD": 0.00001, "USDCHF": 0.00001, "USDCAD": 0.00001,
    "BTCUSD": 0.01,   "ETHUSD": 0.01,
}

_HANS_TO_BULL_BEAR = {"LONG": "BULL", "SHORT": "BEAR"}   # TRIGGERS_SINHRON_V1


_HANS_TO_BULL_BEAR = {"LONG": "BULL", "SHORT": "BEAR"}  # TRIGGERS_SINHRON_V1
_TWR_NEUTRAL_KILL_BARS = 3   # KALIBROVKA_POROGA_V1: синхронно с hooks.py


def _proverit_tochku_lokalno(md: dict, tochka: dict) -> dict:
    """Та же логика, что TOCHKA_ZHIVA_V1 (hooks.proverit_tochku), но
    БЕЗ файла на диске — состояние живёт в переданном словаре tochka.
    Ничего не пишет в trading_state.json, ни разу не зовёт модель."""
    if not tochka.get("alive"):
        return {"alive": False, "reason": "точки нет", "changed": False}
    zp = tochka.get("zero_point_price")
    napr = tochka.get("trend_direction")
    if zp is None or napr not in ("BULL", "BEAR"):
        return {"alive": False, "reason": "точки нет", "changed": False}

    price = md.get("price", {}) or {}
    low = price.get("low")
    high = price.get("high")
    close = price.get("close")   # KALIBROVKA_POROGA_V1: слом — строго по close
    twr = md.get("twr", {}) or {}
    db = md.get("divergent_bar", {}) or {}
    mfi_type = (md.get("mfi", {}) or {}).get("type")

    # подпитка той же стороной — проверяется первой (см. TOCHKA_ZHIVA_V1)
    if db.get("direction") == napr and mfi_type in ("GREEN", "SQUAT"):
        novaya_zp = None
        if napr == "BULL" and low is not None:
            novaya_zp = min(zp, low)
        elif napr == "BEAR" and high is not None:
            novaya_zp = max(zp, high)
        if novaya_zp is not None and novaya_zp != zp:
            tochka["zero_point_price"] = novaya_zp
            return {"alive": True, "reason": f"подпитка {mfi_type}", "changed": True}

    # KALIBROVKA_POROGA_V1: слом строго по close — тень не считается
    slomana = False
    if napr == "BULL" and close is not None and close < zp:
        slomana = True
    elif napr == "BEAR" and close is not None and close > zp:
        slomana = True
    if slomana:
        tochka["alive"] = False
        tochka["neutral_bars_count"] = 0
        return {"alive": False, "reason": "структурный слом (close)", "changed": True}

    # KALIBROVKA_POROGA_V1: TWR требует _TWR_NEUTRAL_KILL_BARS баров подряд
    if twr.get("neutral") is True:
        n = int(tochka.get("neutral_bars_count", 0) or 0) + 1
        tochka["neutral_bars_count"] = n
        if n >= _TWR_NEUTRAL_KILL_BARS:
            tochka["alive"] = False
            tochka["neutral_bars_count"] = 0
            return {"alive": False, "reason": f"TWR угас ({n} бар подряд)", "changed": True}
        return {"alive": True, "reason": f"TWR нейтрален {n}/{_TWR_NEUTRAL_KILL_BARS}",
                "changed": False}
    else:
        if tochka.get("neutral_bars_count"):
            tochka["neutral_bars_count"] = 0

    return {"alive": True, "reason": "жива", "changed": False}


def main():
    args = sys.argv[1:]
    if len(args) < 3:
        print("Использование: python count_triggers.py <csv> <symbol> <tf> [--warmup N]")
        print("Пример:        python count_triggers.py test_data/XAUUSDH4.csv XAUUSD H4")
        sys.exit(1)

    csv_path, symbol, tf = args[0], args[1], args[2]
    warmup = 60
    if "--warmup" in args:
        idx = args.index("--warmup")
        warmup = int(args[idx + 1])

    point = _TEST_POINT.get(symbol.upper())
    if point is None:
        print(f"⚠️  point для {symbol} неизвестен этому счётчику — "
              f"допиши его в _TEST_POINT внутри файла.")
        sys.exit(1)

    full_path = csv_path
    if not Path(full_path).is_absolute() and not Path(full_path).exists():
        full_path = str(_BIRZHA / csv_path)

    bars_all = read_mt5_csv(full_path)
    if not bars_all:
        print(f"CSV не прочитан или пуст: {full_path}")
        sys.exit(1)

    total = len(bars_all)
    print(f"Считаю {symbol} {tf}: {total - warmup} баров ({bars_all[warmup]['date']} "
          f"→ {bars_all[-1]['date']}). Чистая математика — ни одного вызова модели.")
    print("")

    tochka = {"alive": False}
    cnt_a = cnt_b = cnt_c = 0
    cnt_alive_bars = 0
    cnt_smert_slom = 0   # DIAGNOSTIKA_PRICHINA_V1: структурный слом
    cnt_smert_twr  = 0   # DIAGNOSTIKA_PRICHINA_V1: TWR угас
    cnt_podpitka   = 0   # DIAGNOSTIKA_PRICHINA_V1: подпитка (для контекста)
    _prev_strong_side = None   # DEDUP_V1: для перехода "родился" (False→True)

    for i in range(warmup, total):
        end = i + 1
        start = max(0, end - 120)
        window = bars_all[start:end]
        md = build_market_data(window, symbol=symbol, timeframe=tf, point=point)
        if not md:
            continue

        db = md.get("divergent_bar", {}) or {}
        wf = md.get("wave_form", {}) or {}
        strong = db.get("bdb_strong") or wf.get("bdb_dir")
        side = db.get("direction") or wf.get("bdb_dir")

        # DEDUP_V1: одна и та же волна может держать "strong" истинным
        # НЕСКОЛЬКО баров подряд (цена ходит рядом с разворотом) — без
        # этого одна реальная точка засчиталась бы много раз. Считаем
        # только МОМЕНТ РОЖДЕНИЯ: переход с "не было" на "есть" (или
        # смену стороны — новая волна пошла в другую сторону).
        is_new_birth = bool(strong) and (side != _prev_strong_side)
        _prev_strong_side = side if strong else None

        if is_new_birth:
            # Триггер А (оценка сверху — ядро грубее живой Искры)
            cnt_a += 1
            price = md.get("price", {}) or {}
            zp = price.get("low") if side == "BULL" else price.get("high")
            tochka = {"alive": True, "zero_point_price": zp, "trend_direction": side,
                      "neutral_bars_count": 0}
            continue   # родившаяся точка на этом же баре не проверяется на смерть

        if strong:
            continue   # та же волна продолжается — уже посчитана, пропускаем

        rez = _proverit_tochku_lokalno(md, tochka)
        if not rez.get("alive"):
            if rez.get("changed"):   # DIAGNOSTIKA_PRICHINA_V1: точка ТОЛЬКО ЧТО умерла
                if "слом" in rez.get("reason", ""):
                    cnt_smert_slom += 1
                elif "TWR" in rez.get("reason", ""):
                    cnt_smert_twr += 1
            continue

        if rez.get("changed") and "подпитка" in rez.get("reason", ""):
            cnt_podpitka += 1   # DIAGNOSTIKA_PRICHINA_V1

        cnt_alive_bars += 1   # DIAGNOSTIKA_ZHIVA_V1

        # TRIGGERS_SINHRON_V1: пробой/палец засчитывается только В ТУ
        # ЖЕ сторону, что и живая точка — иначе это чужая волна.
        _napr_tochki = tochka.get("trend_direction")

        hd = _hans_breakout(md, window)
        if hd is not None and _HANS_TO_BULL_BEAR.get(hd) == _napr_tochki:
            cnt_b += 1
            continue

        thumb = md.get("thumb_trade", {}) or {}
        if thumb.get("triggered") and thumb.get("direction") == _napr_tochki:
            cnt_c += 1

    total_wake = cnt_a + cnt_b + cnt_c
    print("═" * 60)
    print(f"  Баров проверено:              {total - warmup}")
    print(f"  Баров, где точка была жива:   {cnt_alive_bars} "
          f"({100*cnt_alive_bars/(total-warmup):.1f}% всего времени)")
    print(f"  Средняя жизнь одной точки:    "
          f"{cnt_alive_bars/cnt_a:.1f} бар(а)" if cnt_a else "  Средняя жизнь: —")
    print(f"    из них умерло от слома:     {cnt_smert_slom}")
    print(f"    из них умерло от TWR:       {cnt_smert_twr}")
    print(f"    подпиталось (не умерло):    {cnt_podpitka}")
    print(f"  Триггер А (свежий спуск):     {cnt_a}")
    print(f"  Триггер Б (фрактал Ганса):    {cnt_b}")
    print(f"  Триггер В (Большой палец):    {cnt_c}")
    print(f"  ИТОГО раз позвали бы Совет:   {total_wake}")
    print("═" * 60)
    print("")
    print("А — оценка СВЕРХУ (ядро грубее Искры, часть она отсеет своим")
    print("голосом — так и было на реальных прогонах). Б и В — настоящие,")
    print("без всякой Искры, просто ждут живую точку. Нули там — честный")
    print("факт про эту историю, не повод чинить код.")


if __name__ == "__main__":
    main()
