# -*- coding: utf-8 -*-
# GRAFIK_ODNA_KARTINKA_V1
"""
ГРАФИК БИРЖИ — одна картинка на двоих.

ЗАЧЕМ. Решение Шефа (06.08): трейдер не просыпается от сигнала кода —
он СМОТРИТ, видит паттерн или не видит, и только увидев подключает
индикаторы. Значит ему нужна картинка. А Шефу нужна ТА ЖЕ САМАЯ, иначе
проверить трейдера нечем.

Отсюда главное решение: рисуем PNG, а не интерактивный виджет. Один
файл идёт и в кабинет на экран, и в запрос модели со зрением. Не два
механизма, а один — что Шеф видит, то трейдер и смотрел.

ЧТО РИСУЕМ (первый заход — минимум, который читается)
    свечи · три линии Аллигатора · AO гистограммой снизу
Фракталы стрелками и объём — вторым слоем, когда станет видно, что
основное читается. Нарисовать всё сразу легко, разглядеть — тяжело:
на скриншоте терминала Шефа половина деталей уже терялась.

ПОЧЕМУ БЕЗ ЛИШНЕЙ КРАСОТЫ. Читает это модель. Ей нужны толстые линии,
крупные бары и высокий контраст, а не тонкая сетка и мелкие подписи.
Светлый фон — по той же причине.

ЧТО НУЖНО ОДИН РАЗ:
    pip install matplotlib
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

# ── Кадр. Не весь экран, а окно последних баров: на терминальном
# скриншоте всё сразу — мелко и нечитаемо (проверено на живом).
BAROV_V_KADRE = 100

# ── Цвета. Аллигатор канонический: челюсть синяя, зубы красные,
# губы зелёные. Свечи — не «красное/зелёное» в тон линиям, иначе
# сливается: тёмная и светлая.
C_UP = "#f2f2f2"
C_DOWN = "#3a3a3a"
C_KRAY = "#1a1a1a"
C_JAW = "#1f6feb"
C_TEETH = "#d92626"
C_LIPS = "#2ea043"
C_FON = "#fdf6e3"
C_AO_UP = "#2ea043"
C_AO_DOWN = "#d92626"


def narisovat(bars: list, alligator: dict, ao_series: list,
              symbol: str = "", timeframe: str = "",
              kuda: Optional[Path] = None,
              barov: int = BAROV_V_KADRE) -> Optional[Path]:
    """Рисует кадр и возвращает путь к PNG. Нет matplotlib — вернёт None.

    bars       — список баров как их отдаёт feed_source
    alligator  — как его отдаёт compute_alligator (нужны *_series)
    ao_series  — как его отдаёт compute_ao_series
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import MaxNLocator
    except ImportError:
        return None

    if not bars or len(bars) < 10:
        return None

    n = min(barov, len(bars))
    b = bars[-n:]

    def _hvost(seq):
        """Последние n значений ряда, выровненные по кадру."""
        if not seq:
            return [None] * n
        s = list(seq)[-n:]
        return [None] * (n - len(s)) + s

    jaw = _hvost(alligator.get("jaw_series"))
    teeth = _hvost(alligator.get("teeth_series"))
    lips = _hvost(alligator.get("lips_series"))
    ao = _hvost(ao_series)

    # Свечи сверху, AO снизу — как в терминале, глаз к этому привык.
    # Пропорция 7:3: гистограмма нужна для формы, а не для чтения цифр.
    fig, (ax, axo) = plt.subplots(
        2, 1, figsize=(16, 9), dpi=110, sharex=True,
        gridspec_kw={"height_ratios": [7, 3], "hspace": 0.06})
    fig.patch.set_facecolor(C_FON)

    x = list(range(n))
    shirina = 0.62

    for i, bar in enumerate(b):
        o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
        rastet = c >= o
        # тень
        ax.plot([i, i], [l, h], color=C_KRAY, linewidth=1.1, zorder=2)
        # тело; доджи рисуем полоской, иначе бар пропадает
        telo = abs(c - o)
        if telo < (h - l) * 0.02:
            ax.plot([i - shirina / 2, i + shirina / 2], [c, c],
                    color=C_KRAY, linewidth=1.4, zorder=3)
        else:
            ax.add_patch(plt.Rectangle(
                (i - shirina / 2, min(o, c)), shirina, telo,
                facecolor=C_UP if rastet else C_DOWN,
                edgecolor=C_KRAY, linewidth=0.9, zorder=3))

    # Аллигатор — толсто, это главные линии кадра
    for ryad, cvet, imya in ((jaw, C_JAW, "Челюсть"),
                             (teeth, C_TEETH, "Зубы"),
                             (lips, C_LIPS, "Губы")):
        xs = [i for i, v in enumerate(ryad) if v is not None]
        ys = [v for v in ryad if v is not None]
        if xs:
            ax.plot(xs, ys, color=cvet, linewidth=2.2, zorder=4, label=imya)

    ax.set_facecolor(C_FON)
    ax.grid(True, color="#00000012", linewidth=0.8)
    ax.set_xlim(-1, n)
    ax.legend(loc="upper left", fontsize=11, framealpha=0.85)
    zag = f"{symbol} {timeframe}".strip()
    if zag:
        ax.set_title(zag, fontsize=15, loc="left", color="#222")
    ax.yaxis.set_major_locator(MaxNLocator(nbins=9))
    ax.tick_params(labelsize=10)
    for s in ax.spines.values():
        s.set_color("#00000030")

    # AO — знак и форма важнее величины
    xs = [i for i, v in enumerate(ao) if v is not None]
    ys = [v for v in ao if v is not None]
    if xs:
        cveta = [C_AO_UP if (k == 0 or ys[k] >= ys[k - 1]) else C_AO_DOWN
                 for k in range(len(ys))]
        axo.bar(xs, ys, color=cveta, width=0.7, zorder=3)
    axo.axhline(0, color="#00000055", linewidth=1.1, zorder=2)
    axo.set_facecolor(C_FON)
    axo.grid(True, color="#00000012", linewidth=0.8)
    axo.set_ylabel("AO", fontsize=11)
    axo.tick_params(labelsize=9)
    for s in axo.spines.values():
        s.set_color("#00000030")

    # Подписи времени — редко: частые превращаются в кашу
    shag = max(1, n // 8)
    poz = list(range(0, n, shag))
    axo.set_xticks(poz)
    axo.set_xticklabels([str(b[i].get("date", ""))[:16] for i in poz],
                        rotation=0, fontsize=9)

    if kuda is None:
        kuda = Path(__file__).resolve().parent / "кадр.png"
    kuda = Path(kuda)
    kuda.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(kuda, facecolor=C_FON, bbox_inches="tight")
    plt.close(fig)
    return kuda


def kadr(symbol: str, timeframe: str, kuda: Optional[Path] = None,
         barov: int = BAROV_V_KADRE) -> Optional[Path]:
    """Взять бары из источника, посчитать индикаторы и нарисовать кадр.

    Готовая кнопка для кабинета: «посмотреть» — Шеф видит то же, что
    ляжет трейдеру, и никого при этом не будит и модель не тратит.
    """
    import sys
    p = Path(__file__).resolve().parent
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
    from feed_source import bars as source_bars
    from williams_core import compute_alligator, compute_ao_series

    bs, point = source_bars(symbol, timeframe, count=max(400, barov + 60))
    if not bs:
        return None
    highs = [x["high"] for x in bs]
    lows = [x["low"] for x in bs]
    al = compute_alligator(highs, lows, point=point)
    ao = compute_ao_series(highs, lows)
    return narisovat(bs, al, ao, symbol, timeframe, kuda=kuda, barov=barov)
