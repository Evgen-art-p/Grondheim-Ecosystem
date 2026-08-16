# -*- coding: utf-8 -*-
# ISKATEL_V1
"""
ИСКАТЕЛЬ КАНДИДАТОВ — код находит поводы, трейдер выбирает.

ЗАКОН ЭТОГО ФАЙЛА
    Здесь нет ни одного суждения о рынке. Кандидат — это МЕСТО, где
    формально сложились три факта, и ничего больше:

        · есть разворотный бар;
        · читается волновая структура;
        · известна её длина в барах.

    Ни «хороший вход», ни «сигнал», ни «подтверждено». Слово Шефа:
    «трейдерам никакой код не должен говорить, что делать, а только
    факты-математику, а трейдер по этой математике судит».

    КАНОН_ВХОДА.md §1②: величина зигзага не принципиальна — какой
    нашли на снимке, тот и работаем. Значит от кода не требуется
    попасть в «настоящую» пятую волну. Требуется не пропустить место,
    на которое стоит взглянуть.

ЦЕНА
    Ноль. Это чистая математика по барам: 1500 баров — 3.4 секунды.
    Платим только когда по найденному месту зовём трейдера.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))

OKNO_RASCHYOTA = 300      # сколько баров нужно математике для расчёта


def _priznaki(bars: list, symbol: str, tf: str, point: float):
    """Факты последнего бара окна. Не кандидат — не None."""
    from williams_core import build_market_data
    md = build_market_data(bars, symbol=symbol, timeframe=tf, point=point)
    if not md:
        return None
    wf = md.get("wave_form") or {}
    if not wf.get("bdb_dir"):
        return None
    if not wf.get("struktura_chitaetsya"):
        return None
    rb = md.get("rubber_band") or {}
    # Момент, в который город должен встать, чтобы УВИДЕТЬ этот бар.
    # Дата бара — это его НАЧАЛО; к этой секунде он ещё не закрыт, и
    # кран его честно прячет (иначе показывал бы будущее). Поэтому
    # момент = конец бара, иначе трейдер встаёт на бар раньше и
    # самого разворотного бара не видит.
    _data = bars[-1].get("date", "")
    _moment = _data
    try:
        import masshtab
        from datetime import timedelta
        import istoriya
        _t0 = istoriya.kak_vremya(_data)
        _m = masshtab.minut(tf)
        if _t0 is not None and _m:
            _moment = (_t0 + timedelta(minutes=_m)).strftime(istoriya.FORMAT)
    except Exception:
        pass
    return {
        "дата": _data,
        "момент": _moment,
        "разворотный": wf.get("bdb_dir"),
        "цена_разворотного": wf.get("bdb_price"),
        "длина_волны": wf.get("dlina"),
        "дивергенция_в_волне": wf.get("divergence_dir"),
        "дивергенция_AO": md.get("divergence_ao"),
        "отрыв_цены": rb.get("distance_now"),
        "доля_натяжения": rb.get("tension_ratio"),
        "компас": md.get("global_bias"),
        "цена": (md.get("price") or {}).get("close"),
    }


def est_seychas(symbol: str, tf: str):
    """Кандидат ли ТЕКУЩИЙ бар (по тому, что отдаёт кран).

    Это же — ключ пробуждения в реале: пришла свеча, спросили, есть
    ли повод. Нет — никого не будим и ничего не платим.
    """
    import feed_source as fs
    b, point = fs.bars(symbol, tf, OKNO_RASCHYOTA)
    if not b or point is None:
        return None
    return _priznaki(b, symbol, tf, point)


def iskat(symbol: str, tf: str, do_momenta: str = "", skolko: int = 10,
          predel_barov: int = 4000, otstup: int = 12, govorit=None):
    """Пробежать историю НАЗАД от точки и набрать кандидатов.

    do_momenta — откуда начинать искать (пусто = с конца истории).
    skolko     — сколько набрать и остановиться.
    predel_barov — насколько глубоко копать, чтобы не молотить зря.
    otstup     — сколько баров считать ОДНИМ местом.

    Про отступ. Признаки держатся несколько баров подряд, и без
    склейки список выглядит так:

        2026.05.27 16:00 · волна 93 баров
        2026.05.27 08:00 · волна 91 баров
        2026.05.27 04:00 · волна 90 баров

    Это одно место, а не три: та же волна, тот же разворот. Двенадцать
    таких «кандидатов» оказались бы тремя настоящими. Поэтому соседей
    ближе отступа считаем одним местом и берём самый свежий из них —
    тот, на котором картина уже сложилась целиком.

    Возвращает список кандидатов, СВЕЖИЕ ПЕРВЫМИ.
    """
    import istoriya
    vse = istoriya._vse_bary(symbol, tf)
    if not vse:
        return []
    import feed_source as fs
    point = fs._test_point(symbol)

    konec = len(vse) - 1
    if do_momenta:
        konec = -1
        for j, b in enumerate(vse):
            if b.get("date", "") <= do_momenta:
                konec = j
            else:
                break
        if konec < 0:
            return []

    nayden = []
    posledniy_i = None
    nachalo = max(OKNO_RASCHYOTA, konec - predel_barov)
    for i in range(konec, nachalo - 1, -1):
        if posledniy_i is not None and (posledniy_i - i) < otstup:
            continue
        okno = vse[max(0, i - OKNO_RASCHYOTA + 1):i + 1]
        if len(okno) < OKNO_RASCHYOTA // 2:
            break
        p = _priznaki(okno, symbol, tf, point)
        if p:
            posledniy_i = i
            nayden.append(p)
            if govorit:
                govorit(f"[ИСКАТЕЛЬ] · {p['дата']} · {p['разворотный']} · "
                        f"волна {p['длина_волны']} баров")
            if len(nayden) >= skolko:
                break
    return nayden


def slovami(k: dict) -> str:
    """Кандидат одной строкой — для ленты кабинета."""
    if not k:
        return ""
    return (f"{k.get('дата')} · разворотный {k.get('разворотный')} @ "
            f"{k.get('цена_разворотного')} · волна {k.get('длина_волны')} "
            f"баров · компас {k.get('компас')}")


if __name__ == "__main__":
    import hooks
    a = _sys.argv[1:]
    if len(a) < 2:
        print("py kandidaty.py XAUUSD H4 [сколько]")
        raise SystemExit(1)
    hooks.postavit_ceh("торговый_хаос")
    n = int(a[2]) if len(a) > 2 else 10
    spisok = iskat(a[0].upper(), a[1].upper(), skolko=n, govorit=print)
    print(f"\nнашёл {len(spisok)} кандидатов (свежие первыми):")
    for k in spisok:
        print("  " + slovami(k))

# ISKATEL_V1 - marker
