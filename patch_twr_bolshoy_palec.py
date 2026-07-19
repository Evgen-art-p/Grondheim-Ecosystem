#!/usr/bin/env python3
# patch_twr_bolshoy_palec.py
# ─────────────────────────────────────────────────────────────
# TWR_BOLSHOY_PALEC_V1 · 19-20.07
#
# ТЗ Студии «Шесть Пальцев» (Лока) + Шеф, канон Нового Хаоса гл.9/3.6:
#   1. compute_twr() — Ритм Рынка: SMA(5/13/34) по Close (НЕ Аллигатор,
#      тот SMMA по медианам 13/8/5 — разные звери). neutral=True, когда
#      5-периодная застряла между 13 и 34 (импульс разворота угас).
#   2. detect_thumb_trade() — Большой палец: ранний вход Авантюриста
#      ДО пробоя фрактала Ганса. Три бара лесенкой (монотонные
#      high/low) + минимум 2 из 3 — GREEN/SQUAT (объём подтверждает).
#      Активация — пробой экстремума лесенки текущим баром.
#
# Оба — чистая математика (код), без LLM. Идёт в market_data как
# "twr" и "thumb_trade" — сенсоры кладут факт, решение за трейдерами.
#
# ИДЕМПОТЕНТНОСТЬ: маркер TWR_BOLSHOY_PALEC_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Биржа" / "williams_core.py"
MARKER = "TWR_BOLSHOY_PALEC_V1"


NEW_FUNCTIONS = '''

def compute_twr(bars: list[dict]) -> dict:
    """
    TWR — Ритм Рынка (Новый Хаос, гл.9). Три SMA Вильямса по CLOSE:
      tide   = SMA(5,  close)
      wave   = SMA(13, close)
      ripple = SMA(34, close)

    НЕ Аллигатор: тот SMMA (сглаженная) по медианам (H+L)/2, периоды
    13/8/5. TWR — SMA (простая) по Close, периоды 5/13/34. Канон
    зафиксирован Студией «Шесть Пальцев» 19.07 — формула дословная.

    neutral=True — импульс разворота УГАС во флэте: 5-периодная
    застряла МЕЖДУ 13 и 34 (линии переплелись, нет выстроенного
    строя ни вверх, ни вниз). Строй есть (not neutral), когда tide
    строго за пределами коридора [min(wave,ripple), max(wave,ripple)].
    """
    closes = [b["close"] for b in bars]
    n = len(closes)
    if n < 34:
        return {"tide": None, "wave": None, "ripple": None, "neutral": None}

    def _sma(vals, period):
        if len(vals) < period:
            return None
        return sum(vals[-period:]) / period

    tide   = _sma(closes, 5)
    wave   = _sma(closes, 13)
    ripple = _sma(closes, 34)
    if tide is None or wave is None or ripple is None:
        return {"tide": None, "wave": None, "ripple": None, "neutral": None}

    lo, hi = min(wave, ripple), max(wave, ripple)
    neutral = lo <= tide <= hi

    return {
        "tide":    round(tide,   6),
        "wave":    round(wave,   6),
        "ripple":  round(ripple, 6),
        "neutral": bool(neutral),
    }


def detect_thumb_trade(bars: list[dict], point: Optional[float] = None) -> dict:
    """
    БОЛЬШОЙ ПАЛЕЦ (Thumb Trade, Новый Хаос гл.3.6) — ранний вход
    Авантюриста ДО пробоя фрактала Ганса, внутри формирующегося
    разворота точки c.

    Три бара подряд ЛЕСЕНКОЙ (bars[-4], bars[-3], bars[-2] — монотонно
    убывающие high И low для BULL, монотонно растущие для BEAR),
    минимум 2 из этих 3 баров — GREEN или SQUAT (MFI, объём подтверждает
    движение — канон «четырёх окон»). Активация (triggered) — ТЕКУЩИЙ
    бар (bars[-1]) пробивает экстремум последнего бара лесенки:
      BULL: high[-1] > high[-2]  (пробой вверх после падения к развороту)
      BEAR: low[-1]  < low[-2]   (пробой вниз)

    Возвращает {"direction": "BULL"|"BEAR"|None, "triggered": bool,
                "trigger_price": float|None, "green_squat_count": int}.
    ИНЖЕНЕРНАЯ ПОМЕТКА (не пластик — честно): «монотонная лесенка +
    2 из 3 GREEN/SQUAT + пробой экстремума» — буквальный перевод
    канона гл.3.6 в проверяемые числа. Проверить на живых данных
    первым прогоном тестера, откалибровать если Аван либо молчит
    всегда, либо палит слишком часто.
    """
    n = len(bars)
    if n < 4:
        return {"direction": None, "triggered": False,
                "trigger_price": None, "green_squat_count": 0}

    b0, b1, b2 = bars[-4], bars[-3], bars[-2]
    cur = bars[-1]

    def _mfi_type(b, pb):
        return compute_mfi(b, pb, point=point)["type"]

    gs_count = 0
    if n >= 5:
        if _mfi_type(b0, bars[-5]) in ("GREEN", "SQUAT"):
            gs_count += 1
    if _mfi_type(b1, b0) in ("GREEN", "SQUAT"):
        gs_count += 1
    if _mfi_type(b2, b1) in ("GREEN", "SQUAT"):
        gs_count += 1

    ladder_bull = (b0["high"] > b1["high"] > b2["high"]
                   and b0["low"] > b1["low"] > b2["low"])
    ladder_bear = (b0["high"] < b1["high"] < b2["high"]
                   and b0["low"] < b1["low"] < b2["low"])

    direction = None
    if ladder_bull and gs_count >= 2:
        direction = "BULL"
    elif ladder_bear and gs_count >= 2:
        direction = "BEAR"

    triggered = False
    trigger_price = None
    if direction == "BULL":
        trigger_price = b2["high"]
        triggered = cur["high"] > trigger_price
    elif direction == "BEAR":
        trigger_price = b2["low"]
        triggered = cur["low"] < trigger_price

    return {"direction": direction, "triggered": bool(triggered),
            "trigger_price": (round(trigger_price, 6)
                              if trigger_price is not None else None),
            "green_squat_count": gs_count}

# ''' + MARKER + ''' - marker

'''


ANCHOR_INSERT_AFTER = '''    return {
        "type":     mtype,
        "volume":   bar["volume"],
        "spread":   bar["spread"],
        "mfi":      round(mfi_cur,  10),
        "mfi_prev": round(mfi_prev, 10),
    }


def detect_ao_divergence(bars: list[dict], ao_series: list[Optional[float]]) -> dict:'''

ANCHOR_INSERT_REPLACEMENT = '''    return {
        "type":     mtype,
        "volume":   bar["volume"],
        "spread":   bar["spread"],
        "mfi":      round(mfi_cur,  10),
        "mfi_prev": round(mfi_prev, 10),
    }
''' + NEW_FUNCTIONS + '''

def detect_ao_divergence(bars: list[dict], ao_series: list[Optional[float]]) -> dict:'''


ANCHOR_WIRE = '''    squat      = detect_squat_bars(bars, point=_point)
    mfi        = compute_mfi(bars[-1], bars[-2], point=_point)
    divergence = detect_ao_divergence(bars, ao_series)'''

ANCHOR_WIRE_REPLACEMENT = '''    squat      = detect_squat_bars(bars, point=_point)
    mfi        = compute_mfi(bars[-1], bars[-2], point=_point)
    divergence = detect_ao_divergence(bars, ao_series)
    twr         = compute_twr(bars)                       # TWR_BOLSHOY_PALEC_V1
    thumb_trade = detect_thumb_trade(bars, point=_point)   # TWR_BOLSHOY_PALEC_V1'''


ANCHOR_RETURN = '''        "squat": {
            "last_squat": squat["last_squat"],
            "count":      squat["count"],
        },
    }'''

ANCHOR_RETURN_REPLACEMENT = '''        "squat": {
            "last_squat": squat["last_squat"],
            "count":      squat["count"],
        },

        "twr":         twr,           # TWR_BOLSHOY_PALEC_V1: Ритм Рынка (SMA 5/13/34 close)
        "thumb_trade": thumb_trade,    # TWR_BOLSHOY_PALEC_V1: ранний вход Авантюриста
    }'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    for anchor, name in [(ANCHOR_INSERT_AFTER, "вставка функций"),
                          (ANCHOR_WIRE, "подключение в build_market_data"),
                          (ANCHOR_RETURN, "запись в возвращаемый словарь")]:
        if anchor not in src:
            raise SystemExit(f"❌ якорь не найден ({name}) — файл разошёлся "
                              f"с ожидаемым, патч НЕ применён")

    src = src.replace(ANCHOR_INSERT_AFTER, ANCHOR_INSERT_REPLACEMENT, 1)
    src = src.replace(ANCHOR_WIRE, ANCHOR_WIRE_REPLACEMENT, 1)
    src = src.replace(ANCHOR_RETURN, ANCHOR_RETURN_REPLACEMENT, 1)

    # ── проверка синтаксиса ДО записи на диск ──
    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_twr")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
