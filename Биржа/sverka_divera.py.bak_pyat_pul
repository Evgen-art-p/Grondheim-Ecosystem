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

    # DIVER_PROVALCHIK_V1 — канон Шефа 22.09:
    #   «между горбами должен быть провальчик, а между ямами —
    #   подъёмчик»; «цена всё выше и выше — обновлять максимум».
    # Главный горб — самый большой в поле зрения. После него AO
    # обязан провалиться (провальчик) и снова пойти вверх — это
    # второй горб (справа он может быть незакончен). Цена на
    # втором горбе должна ОБНОВИТЬ вершину, что была от главного
    # горба до провальчика. Не обновила — ход не продолжился,
    # дивера нет. Ноль, расстояние, номер волны — не считаются.
    return dve_tochki(ao, highs, lows, vid, verh)


def dve_tochki(ao: list, highs: list, lows: list, vid: list,
               verh: bool) -> dict:
    """Две точки дивера по канону. verh=True — SHORT (горбы и
    вершины), False — LONG (ямы и впадины)."""
    tochki = gorby(ao) if verh else yamy(ao)
    tochki = [(i, v) for i, v in tochki if i in vid]
    if len(tochki) < 1:
        return {"ok": False, "est": None,
                "slovami": "горбов в поле зрения не нашлось" if verh
                else "ям в поле зрения не нашлось"}

    # главный — самый большой горб (самая глубокая яма) в поле зрения
    glavnyy = max(tochki, key=lambda t: t[1]) if verh \
        else min(tochki, key=lambda t: t[1])
    g = glavnyy[0]

    p = None
    for _i in range(len(ao) - 1, -1, -1):
        if ao[_i] is not None:
            p = _i
            break
    if p is None or p <= g + 1:
        return {"ok": True, "est": False,
                "slovami": "главный горб у самого края — второго ещё нет"
                if verh else "главная яма у самого края — второй ещё нет"}

    # провальчик (для ям — подъёмчик): крайняя точка AO между
    # главным и сегодняшним днём
    mezhdu = [(k, ao[k]) for k in range(g + 1, p) if ao[k] is not None]
    if not mezhdu:
        return {"ok": True, "est": False,
                "slovami": "между главным и краем пусто"}
    d = (min(mezhdu, key=lambda t: t[1]) if verh
         else max(mezhdu, key=lambda t: t[1]))[0]
    # провальчик должен кончиться: после него AO пошёл обратно
    posle = [ao[k] for k in range(d + 1, p + 1) if ao[k] is not None]
    if not posle or (verh and max(posle) <= ao[d]) or \
            (not verh and min(posle) >= ao[d]):
        return {"ok": True, "est": False,
                "slovami": ("AO ещё уходит вниз от главного горба — "
                            "провальчика нет, второго горба нет") if verh
                else ("AO ещё поднимается от главной ямы — "
                      "подъёмчика нет, второй ямы нет")}

    # второй горб — от провальчика до края (справа может быть незакончен)
    nog = [k for k in range(d + 1, p + 1) if ao[k] is not None]
    if verh:
        k2 = max(nog, key=lambda k: ao[k])
        ao_bylo, ao_stalo = glavnyy[1], ao[k2]
        c_bylo = max(highs[g:d + 1])          # вершина хода до провальчика
        c_stalo = max(highs[d + 1:p + 1])     # вершина на втором горбе
        cena_dalshe = c_stalo > c_bylo
        sila_slabee = ao_stalo < ao_bylo
    else:
        k2 = min(nog, key=lambda k: ao[k])
        ao_bylo, ao_stalo = glavnyy[1], ao[k2]
        c_bylo = min(lows[g:d + 1])
        c_stalo = min(lows[d + 1:p + 1])
        cena_dalshe = c_stalo < c_bylo
        sila_slabee = ao_stalo > ao_bylo

    est = bool(cena_dalshe and sila_slabee)
    kuda_c = "выше" if c_stalo > c_bylo else "ниже"
    kuda_a = "выше" if ao_stalo > ao_bylo else "ниже"
    slovami = (f"цена {c_bylo:.5f}→{c_stalo:.5f} ({kuda_c}), "
               f"AO {ao_bylo:.5f}→{ao_stalo:.5f} ({kuda_a}), "
               f"{'провальчик' if verh else 'подъёмчик'} {ao[d]:.5f}")
    if not est:
        if not cena_dalshe:
            slovami += (" · цена вершину хода не обновила" if verh
                        else " · цена впадину хода не обновила")
        if not sila_slabee:
            slovami += " · сила не ослабла"
    return {"ok": True, "est": est, "slovami": slovami,
            "цена_было": c_bylo, "цена_стало": c_stalo,
            "ao_было": ao_bylo, "ao_стало": ao_stalo}
