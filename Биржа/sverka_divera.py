# -*- coding: utf-8 -*-
# SVERKA_DIVERA_V1
"""Считает дивер по барам — чтобы слова трейдера было с чем сверить.

Канон Шефа (17.09):
  ГОРБ — три столбика: меньше-БОЛЬШЕ-меньше.
  ЯМА  — три столбика: больше-МЕНЬШЕ-больше.
  Главный — самый большой в поле зрения, не «предыдущий по счёту».

Город СЧИТАЕТ и ПОКАЗЫВАЕТ. Решает трейдер. Здесь нет ни одного
запрета — только числа.
"""

from typing import Optional

BAROV = 140          # столько же, сколько видно на кадре


def gorby(ao: list) -> list:
    """Места и высоты горбов: средний столбик выше обоих соседей."""
    out = []
    for i in range(1, len(ao) - 1):
        a, b, c = ao[i - 1], ao[i], ao[i + 1]
        if a is None or b is None or c is None:
            continue
        if b > a and b > c:
            out.append((i, b))
    return out


def yamy(ao: list) -> list:
    """Места и глубины ям: средний столбик ниже обоих соседей."""
    out = []
    for i in range(1, len(ao) - 1):
        a, b, c = ao[i - 1], ao[i], ao[i + 1]
        if a is None or b is None or c is None:
            continue
        if b < a and b < c:
            out.append((i, b))
    return out


def poschitat(symbol: str, timeframe: str, storona: str) -> dict:
    """Дивер по числам. storona: SHORT — по вершинам, LONG — по впадинам.

    Возвращает {"ok", "est", "slovami", "почему"}.
    ok=False — посчитать не вышло, и это НЕ приговор трейдеру.
    """
    try:
        import sys as _s
        from pathlib import Path as _P
        _p = str(_P(__file__).resolve().parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from feed_source import bars as _bars
        from williams_core import compute_ao_series
    except Exception as e:
        return {"ok": False, "est": None, "slovami": f"нет счёта ({e})"}

    try:
        b, _point = _bars(symbol, timeframe, BAROV + 60)
    except Exception as e:
        return {"ok": False, "est": None, "slovami": f"нет баров ({e})"}
    if not b or len(b) < 60:
        return {"ok": False, "est": None, "slovami": "мало баров"}

    b = b[-(BAROV + 40):]
    highs = [x["high"] for x in b]
    lows = [x["low"] for x in b]
    closes = [x["close"] for x in b]
    ao = compute_ao_series(highs, lows)

    # поле зрения — последние BAROV баров, как на кадре
    n = len(ao)
    start = max(0, n - BAROV)
    vid = list(range(start, n))

    verh = str(storona).upper() == "SHORT"   # шорт — по вершинам
    tochki = gorby(ao) if verh else yamy(ao)
    tochki = [(i, v) for i, v in tochki if i in vid]
    if len(tochki) < 1:
        return {"ok": False, "est": None,
                "slovami": "горбов в поле зрения не нашлось"}

    # главный — самый большой (или самая глубокая) в поле зрения
    glavnyy = max(tochki, key=lambda t: t[1]) if verh \
        else min(tochki, key=lambda t: t[1])
    # нынешний — последний, что не сам главный
    posle = [t for t in tochki if t[0] > glavnyy[0]]
    if not posle:
        return {"ok": False, "est": None,
                "slovami": "после главного горба нового ещё нет"}
    nyneshniy = posle[-1]

    ao_bylo, ao_stalo = glavnyy[1], nyneshniy[1]
    c_bylo = highs[glavnyy[0]] if verh else lows[glavnyy[0]]
    c_stalo = highs[nyneshniy[0]] if verh else lows[nyneshniy[0]]

    if verh:
        cena_dalshe = c_stalo > c_bylo
        sila_slabee = ao_stalo < ao_bylo
    else:
        cena_dalshe = c_stalo < c_bylo
        sila_slabee = ao_stalo > ao_bylo

    est = bool(cena_dalshe and sila_slabee)
    kuda_c = "выше" if c_stalo > c_bylo else "ниже"
    kuda_a = "выше" if ao_stalo > ao_bylo else "ниже"
    slovami = (f"цена {c_bylo:.5f}→{c_stalo:.5f} ({kuda_c}), "
               f"AO {ao_bylo:.5f}→{ao_stalo:.5f} ({kuda_a})")
    if not est:
        if not cena_dalshe:
            slovami += " · цена край не обновила"
        if not sila_slabee:
            slovami += " · сила не ослабла"
    return {"ok": True, "est": est, "slovami": slovami,
            "цена_было": c_bylo, "цена_стало": c_stalo,
            "ao_было": ao_bylo, "ao_стало": ao_stalo}
