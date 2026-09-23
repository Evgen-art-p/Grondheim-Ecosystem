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

    # DVE_GORKI_V1 — слово Шефа 22.09, по кадру QV32:
    #   один импульс — это отрезок от излома до вершины, «от 0 до 100».
    #   Пока цена не вышла за 100, идёт откат того же импульса и новой
    #   волны нет. Вышла — пошла следующая, и вот тогда на AO стоят ДВЕ
    #   ГОРКИ с ямкой между ними (ямка и есть тот откат). Вторая горка
    #   ниже первой — расхождение. Вниз зеркально: две ямки, горка
    #   между ними, вторая ямка мельче. Горок нет, AO просто ползёт —
    #   сравнивать нечего: они есть этажом ниже, но мы туда не идём.
    return dve_gorki(ao, highs, lows, vid, verh, b)


def dve_gorki(ao: list, highs: list, lows: list, vid: list,
              verh: bool, b: list = None) -> dict:
    """Две горки (две ямки) по ЭКСТРЕМУМАМ, на всех размерах. verh=True — SHORT.

    DVE_GORKI_MATRYOSHKA_V1 — слово Шефа 23.09: «линии должны тянуться
    по экстремумам, на цене и AO: самый экстремум AO и следующий
    меньше, и смотрим». И по его же скрину USDCNH: после отката пятая
    волна несёт СВОЙ дивер внутри — смотреть на всех размерах.

    Вниз (LONG), вверх зеркально. Одна пара:
      1-я точка AO — самый экстремум;
      откат — самый высокий бар цены после неё, он делит ход надвое;
      2-я точка AO — самое глубокое место AO после отката (если яма у
        края ещё роется — у края, и переедет глубже вместе с ней);
      цена — самый низ до отката и самый низ после него.
    Матрёшка: вторая точка пары становится первой точкой следующей,
    меньшей — и так до края. Первая пара — весь ход, последняя — край.

    Главные ключи ответа — большая пара, как и раньше. Все пары лежат в
    «пары», последняя с расхождением — в «край».
    """
    tochki = gorby(ao) if verh else yamy(ao)
    tochki = [(i, v) for i, v in tochki if i in vid]
    imya = "горка" if verh else "ямка"
    if not tochki:
        return {"ok": True, "est": False,
                "slovami": f"{'горок' if verh else 'ямок'} AO в поле "
                           "зрения нет — сравнивать нечего"}

    def _kogda(i):
        try:
            return str(b[i].get("date", ""))[:16] if b else f"бар {i}"
        except Exception:
            return f"бар {i}"

    p = None
    for _i in range(len(ao) - 1, -1, -1):
        if ao[_i] is not None:
            p = _i
            break

    def _para(g):
        """Одна пара от точки g до края. Строка — пары нет, и почему."""
        a1 = ao[g]
        if p is None or p <= g + 1:
            return f"{imya} {_kogda(g)} у самого края — второй ещё нет"
        posle = range(g + 1, p + 1)
        t = (min(posle, key=lambda k: lows[k]) if verh
             else max(posle, key=lambda k: highs[k]))
        if t >= p:
            return (f"после {_kogda(g)} цена в откате до самого края — "
                    "второго края ещё нет")
        do, pos = range(g, t + 1), range(t + 1, p + 1)
        if verh:
            ic1 = max(do, key=lambda k: highs[k])
            ic2 = max(pos, key=lambda k: highs[k])
            kray_vzyat = highs[ic2] > highs[ic1]
            c1, c2 = highs[ic1], highs[ic2]
            k2 = max(pos, key=lambda k: ao[k])
        else:
            ic1 = min(do, key=lambda k: lows[k])
            ic2 = min(pos, key=lambda k: lows[k])
            kray_vzyat = lows[ic2] < lows[ic1]
            c1, c2 = lows[ic1], lows[ic2]
            k2 = min(pos, key=lambda k: ao[k])
        a2 = ao[k2]
        # настоящая горка (ямка) или та, что ещё растёт у края; склон,
        # по которому AO просто ползёт, точкой не считается
        if k2 < p:
            tochka = ((a2 > ao[k2 - 1] and a2 > ao[k2 + 1]) if verh
                      else (a2 < ao[k2 - 1] and a2 < ao[k2 + 1]))
        else:
            tochka = (a2 > ao[p - 1]) if verh else (a2 < ao[p - 1])
        if not tochka:
            return (f"после отката {_kogda(t)} AO просто ползёт — второй "
                    f"{'горки' if verh else 'ямки'} нет")
        sila_slabee = a2 < a1 if verh else a2 > a1
        u_kraya = " (ещё растёт у края)" if k2 == p else ""
        slovami = (f"{_kogda(g)}: AO {a1:.5f}, край цены {c1:.5f} → "
                   f"откат {_kogda(t)} → {_kogda(k2)}{u_kraya}: "
                   f"AO {a2:.5f}, край цены {c2:.5f}")
        prich = []
        if not kray_vzyat:
            prich.append("цена прежний край не взяла — откат ещё идёт")
        if not sila_slabee:
            prich.append("сила не слабее прежней")
        if prich:
            slovami += " · " + ", ".join(prich)
        return {"est": bool(kray_vzyat and sila_slabee), "slovami": slovami,
                "цена_было": c1, "цена_стало": c2,
                "ao_было": a1, "ao_стало": a2,
                "i_цена_1": ic1, "i_цена_2": ic2,
                "i_ao_1": g, "i_ao_2": k2}

    # матрёшка: от самого экстремума — к краю, каждая пара меньше
    g, _a = (max(tochki, key=lambda t: t[1]) if verh
             else min(tochki, key=lambda t: t[1]))
    pary = []
    prichina = ""
    while True:
        r = _para(g)
        if isinstance(r, str):
            prichina = r
            break
        pary.append(r)
        if r["i_ao_2"] <= g or r["i_ao_2"] >= p:
            break
        g = r["i_ao_2"]

    if not pary:
        return {"ok": True, "est": False, "slovami": f"1-я {imya}: " + prichina,
                "пары": [], "край": None}

    bolshaya = pary[0]
    s_diverom = [x for x in pary if x["est"]]
    kray = s_diverom[-1] if s_diverom else None
    slovami = "весь ход: " + bolshaya["slovami"]
    if kray is not None and kray is not bolshaya:
        slovami += " || у края: " + kray["slovami"]
    if len(pary) > 1:
        slovami += f" || размеров: {len(pary)}, с расхождением: {len(s_diverom)}"
    otvet = {"ok": True, "est": bolshaya["est"], "slovami": slovami,
             "пары": pary, "край": kray}
    if bolshaya["est"]:
        for k in ("цена_было", "цена_стало", "ao_было", "ao_стало",
                  "i_цена_1", "i_цена_2", "i_ao_1", "i_ao_2"):
            otvet[k] = bolshaya[k]
    return otvet
