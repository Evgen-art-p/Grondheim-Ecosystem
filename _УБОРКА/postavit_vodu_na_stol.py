# -*- coding: utf-8 -*-
# MARKER: VODA_NA_STOLE_V1
"""
ВОДА НА СТОЛЕ, НЕ ВОРОТА — патч Биржи.

Слово Шефа (26.08): вода не разрешает и не запрещает точку. Она лежит
рядом отдельной строкой; трейдер видит оба факта и решает сам, в том
числе против воды, со своим стопом.

ЧТО ДЕЛАЕТ ЭТОТ СКРИПТ

  1. Кладёт новый файл  Биржа/voda.py
     Вода считается СТРУКТУРОЙ: две последние вершины и две последние
     впадины по обычному фракталу (2 бара). Обе выше — бык, обе ниже —
     медведь; разнобой не гасит — вода держится прежней стороной, пока
     её не сломает новый подтверждённый экстремум с обеих сторон. Тот
     же счёт этажом выше — для подтверждения. Вода есть только когда
     оба этажа смотрят в одну сторону, иначе на столе стоит «воды нет».
     Лесенка: H4 → дневка + неделька, H1 → H4 + дневка. Месяца нет.

  2. Биржа/global_anchor.py — старший этаж больше не мерится ВЕЕРОМ
     Аллигатора (веер соврал на откате в 43% случаев). Якорь отдаёт
     воду. Вид ответа тот же — читатели не ломаются.

  3. Биржа/kandidaty.py — СНИМАЕТ ВОРОТА POISK_PO_TRENDU_V1. Место
     против воды больше не выбрасывается: оно отдаётся трейдеру, вода
     кладётся рядом фактом. Счётчик остаётся — видно, сколько таких.

  4. Биржа/stol.py — строка «старший Аллигатор» заменена строкой ВОДА:
     сторона, оба этажа и чем именно её нет, если её нет.

Идемпотентен: второй запуск ничего не трогает. Перед правкой кладёт
.bak рядом с файлом. Пути ищет сам.

После накатки проверить, не поднимая города:
    py Биржа/voda.py EURUSD H4
    py Биржа/stol.py EURUSD H4
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "VODA_NA_STOLE_V1"


def _nayti_birzhu() -> Path:
    """Ищем папку Биржа сами — руками путей не пишем."""
    primety = ("stol.py", "kandidaty.py", "global_anchor.py")
    nashli = []
    korni = []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        mesta = [koren]
        try:
            mesta += [x for x in koren.iterdir() if x.is_dir()]
        except OSError:
            pass
        for p in mesta:
            if all((p / f).exists() for f in primety) and p not in nashli:
                nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл папку Биржа рядом со скриптом.")
        print("Положи скрипт в корень репозитория и запусти оттуда,")
        print("или перетащи сюда папку Биржа и нажми Enter:")
        s = input("папка: ").strip().strip('"')
        p = Path(s)
        if all((p / f).exists() for f in primety):
            return p
        raise SystemExit("Не та папка — в ней нет stol.py/kandidaty.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    n = int((input("которая? ").strip() or "1"))
    return nashli[n - 1]


def _pravka(path: Path, pary: list) -> bool:
    """Точечные замены по дословным якорям. Всё или ничего."""
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"  . {path.name}: уже накачен, пропускаю")
        return False
    novyy = text
    for staroe, novoe in pary:
        if novyy.count(staroe) != 1:
            raise SystemExit(
                f"  X {path.name}: якорь не найден или не один "
                f"({novyy.count(staroe)} совпадений). Файл НЕ ТРОНУТ.\n"
                f"    якорь: {staroe.strip()[:70]}")
        novyy = novyy.replace(staroe, novoe)
    novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
    ast.parse(novyy)
    shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    path.write_text(novyy, encoding="utf-8")
    print(f"  + {path.name}: поправлен (.bak рядом)")
    return True


# ─────────────────────────────────────────────────────────────
# 1. НОВЫЙ ФАЙЛ
# ─────────────────────────────────────────────────────────────
VODA_SRC = r'''
# -*- coding: utf-8 -*-
# VODA_NA_STOLE_V1
"""
ВОДА — ФАКТ НА СТОЛЕ, НЕ ВОРОТА.

Слово Шефа (26.08): точка на H4 рождается только от собственной
структуры H4. Вода её не разрешает и не запрещает — она ложится рядом
ОТДЕЛЬНОЙ СТРОКОЙ. Трейдер видит оба факта и решает сам, в том числе
войти против воды, со своим стопом.

Этот файл считает воду так, чтобы она была действительностью, а не
выдумкой.

КАК СЧИТАЕТСЯ
    · Структура этажа — две последние вершины и две последние впадины
      (обычный фрактал, 2 бара с каждой стороны — тот же detect_fractals,
      что уже есть в ядре).
      Обе выше предыдущих — бык. Обе ниже — медведь.
    · Разнобой НЕ ГАСИТ воду: она держится прежней стороной, пока её не
      сломает новый подтверждённый экстремум с обеих сторон.
    · Тот же счёт повторяется этажом выше — для подтверждения.
    · Вода на столе есть ТОЛЬКО когда оба этажа смотрят в одну сторону.
      Иначе на столе стоит «воды нет» — а не выдуманное направление.

ЛЕСЕНКА (месяц выкинут, выше недельки не лезем)
    H4 → дневка + неделька
    H1 → H4 + дневка

ПОЧЕМУ НЕ ВЕЕР АЛЛИГАТОРА
    Веер соврал на откате в 43% случаев — такой факт трейдеру на стол
    класть нельзя. Зигзаг с порогом ATR проверен отдельно: не помог,
    хуже монетки и сам, и в связке. Фрактал-дневка+неделька держит 54%
    против веерных 46% там, где они расходятся — на двух рынках, 16 и
    22 года истории.

ЕСЛИ ЭТАЖА НЕТ В ИСТОЧНИКЕ
    Дневка и неделька СКЛЕИВАЮТСЯ из рабочих баров (день = баров одной
    даты, неделя = баров одной календарной недели). Это те же самые
    котировки, просто сложенные — и на столе так и написано: «склеена».
    Выдуманного направления не появляется ни при каком раскладе.

ПРОВЕРИТЬ РУКАМИ
    py Биржа/voda.py EURUSD H4
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path
from typing import Optional

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))

# Лесенка воды. Меняется одной строкой — не по коду.
LESENKA = {
    "H4": ("D1", "W1"),
    "H1": ("H4", "D1"),
}

GLUBINA = 400        # сколько баров этажа берём на счёт структуры
GLUBINA_SKLEYKI = 8000   # сколько рабочих баров просить на склейку


# ─────────────────────────────────────────────────────────────
# СТРУКТУРА ЭТАЖА
# ─────────────────────────────────────────────────────────────

def struktura(bars: list) -> tuple:
    """Куда смотрит структура: ("BULL"|"BEAR"|None, словами).

    Идём по подтверждённым фракталам в том порядке, в каком их видел
    рынок. На каждом новом фрактале смотрим две последние вершины и две
    последние впадины: обе выше — бык, обе ниже — медведь, разнобой —
    держим прежнюю сторону.
    """
    if not bars or len(bars) < 12:
        return None, "баров мало"
    try:
        from williams_core import detect_fractals
    except Exception as e:
        return None, f"ядро не подключилось ({e})"

    f = detect_fractals(bars, lookback=2)
    verh = list(f.get("all_up") or [])
    niz = list(f.get("all_down") or [])
    if len(verh) < 2 or len(niz) < 2:
        return None, "вершин или впадин меньше двух"

    # Фрактал подтверждается через 2 бара после своего центра — раньше
    # его на графике нет, и знать о нём мы не имеем права.
    momenty = sorted([(x["bar_index"] + 2, "V") for x in verh]
                     + [(x["bar_index"] + 2, "N") for x in niz])

    storona = None
    for t, _ in momenty:
        v = [x for x in verh if x["bar_index"] + 2 <= t][-2:]
        n = [x for x in niz if x["bar_index"] + 2 <= t][-2:]
        if len(v) < 2 or len(n) < 2:
            continue
        vverh = v[-1]["price"] > v[-2]["price"] and n[-1]["price"] > n[-2]["price"]
        vniz = v[-1]["price"] < v[-2]["price"] and n[-1]["price"] < n[-2]["price"]
        if vverh:
            storona = "BULL"
        elif vniz:
            storona = "BEAR"
        # разнобой — вода держится прежней стороной

    v2, n2 = verh[-2:], niz[-2:]
    slovami = (f"вершины {v2[0]['price']}→{v2[1]['price']}, "
               f"впадины {n2[0]['price']}→{n2[1]['price']}")
    if storona is None:
        return None, "сторона ни разу не сложилась (" + slovami + ")"
    return storona, slovami


# ─────────────────────────────────────────────────────────────
# БАРЫ ЭТАЖА
# ─────────────────────────────────────────────────────────────

def _kak_vremya(s: str):
    from datetime import datetime
    s = (s or "").strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def skleit(bars: list, kuda: str) -> list:
    """Сложить мелкие бары в дневные или недельные.

    Не новая математика: высшая точка группы — high, низшая — low.
    Больше воде ничего и не нужно, она считается по экстремумам.
    """
    kuda = (kuda or "").upper()
    if kuda not in ("D1", "W1") or not bars:
        return []
    groups: dict = {}
    poryadok = []
    for b in bars:
        t = _kak_vremya(b.get("date", ""))
        if t is None:
            continue
        if kuda == "D1":
            k = (t.year, t.month, t.day)
        else:
            iso = t.isocalendar()
            k = (iso[0], iso[1])
        g = groups.get(k)
        if g is None:
            groups[k] = {
                "date": b.get("date", ""), "open": b["open"],
                "high": b["high"], "low": b["low"], "close": b["close"],
                "volume": b.get("volume", 0), "spread": b.get("spread", 0.0),
            }
            poryadok.append(k)
        else:
            g["high"] = max(g["high"], b["high"])
            g["low"] = min(g["low"], b["low"])
            g["close"] = b["close"]
            g["volume"] = (g.get("volume") or 0) + (b.get("volume") or 0)
    return [groups[k] for k in poryadok]


def bary_etazha(symbol: str, tf: str, as_of_date: Optional[str],
                rabochiy_tf: str = "") -> tuple:
    """Бары этажа: (бары, откуда_словами). Пусто — честно пусто."""
    otkuda = tf
    bars = []
    try:
        from feed_source import bars as source_bars
        b, _p = source_bars(symbol, tf, count=GLUBINA * 3)
        bars = list(b or [])
    except Exception:
        bars = []

    if not bars and rabochiy_tf and tf in ("D1", "W1"):
        try:
            from feed_source import bars as source_bars
            b, _p = source_bars(symbol, rabochiy_tf, count=GLUBINA_SKLEYKI)
            syrye = list(b or [])
            if as_of_date:
                cut = as_of_date.strip()
                syrye = [x for x in syrye if x.get("date", "") <= cut]
            bars = skleit(syrye, tf)
            otkuda = f"{tf} склеена из {rabochiy_tf}"
        except Exception:
            bars = []

    if as_of_date and bars:
        cut = as_of_date.strip()
        # Дата бара — его НАЧАЛО. Дневка, начавшаяся сегодня утром,
        # содержит весь сегодняшний день, включая то, что ещё не
        # случилось — это и есть заглядывание в будущее. Поэтому у
        # взятых из источника этажей последний бар отбрасываем: он
        # не закрыт. У склеенных этого делать не надо — они собраны
        # только из тех мелких баров, что уже были.
        bars = [x for x in bars if x.get("date", "") <= cut]
        if otkuda == tf and bars:
            bars = bars[:-1]
    if len(bars) > GLUBINA:
        bars = bars[-GLUBINA:]
    return bars, otkuda


def napravlenie(symbol: str, tf: str, as_of_date: Optional[str] = None,
                rabochiy_tf: str = "") -> dict:
    """Структура одного этажа: {"сторона", "почему", "откуда", "баров"}."""
    bars, otkuda = bary_etazha(symbol, tf, as_of_date, rabochiy_tf)
    if not bars:
        return {"сторона": None, "почему": f"{tf} не дал баров",
                "откуда": otkuda, "баров": 0}
    s, why = struktura(bars)
    return {"сторона": s, "почему": why, "откуда": otkuda, "баров": len(bars)}


# ─────────────────────────────────────────────────────────────
# ВОДА НА СТОЛ
# ─────────────────────────────────────────────────────────────

def voda_na_stole(symbol: str, working_tf: str,
                  as_of_date: Optional[str] = None) -> dict:
    """Вода для рабочего этажа. Тот же контракт, что был у якоря:
    {"bias": "BULL"|"BEAR"|"NONE", "senior_tf", "ok", "why", ...}

    bias="NONE" — воды НЕТ. Это честный факт, а не поломка: два этажа
    смотрят в разные стороны, и выдумывать сторону мы не станем.
    """
    tf = (working_tf or "").upper()
    para = LESENKA.get(tf)
    if not para:
        return {"bias": "NONE", "senior_tf": None, "ok": False,
                "why": f"воды для {tf or '?'} нет — лесенка держит только "
                       f"{', '.join(LESENKA)}",
                "вода_этажи": None}

    a, b = para
    ra = napravlenie(symbol, a, as_of_date, rabochiy_tf=tf)
    rb = napravlenie(symbol, b, as_of_date, rabochiy_tf=tf)

    etazhi = (f"{a}: {ra['сторона'] or '—'} ({ra['почему']}) · "
              f"{b}: {rb['сторона'] or '—'} ({rb['почему']})")

    if ra["сторона"] is None or rb["сторона"] is None:
        pusto = a if ra["сторона"] is None else b
        return {"bias": "NONE", "senior_tf": a, "ok": True,
                "why": f"воды нет: {pusto} не сложился",
                "вода_этажи": etazhi, "этажи": (a, b),
                "откуда": (ra["откуда"], rb["откуда"])}

    if ra["сторона"] != rb["сторона"]:
        return {"bias": "NONE", "senior_tf": a, "ok": True,
                "why": f"воды нет: {a} {ra['сторона']}, {b} {rb['сторона']}",
                "вода_этажи": etazhi, "этажи": (a, b),
                "откуда": (ra["откуда"], rb["откуда"])}

    return {"bias": ra["сторона"], "senior_tf": a, "ok": True,
            "why": f"{a} и {b} смотрят в одну сторону",
            "вода_этажи": etazhi, "этажи": (a, b),
            "откуда": (ra["откуда"], rb["откуда"])}


def slovami(v: dict) -> str:
    """Вода одной строкой — для стола и для кабинета."""
    if not v:
        return "ВОДА: не считалась"
    b = v.get("bias")
    if b in ("BULL", "BEAR"):
        return (f"ВОДА: {b}   ({v.get('why')})"
                f"   [{v.get('вода_этажи') or ''}]")
    return f"ВОДА: НЕТ НА СТОЛЕ   ({v.get('why')})   [{v.get('вода_этажи') or ''}]"


if __name__ == "__main__":
    a = _sys.argv[1:]
    if len(a) < 2:
        print("py voda.py EURUSD H4 [YYYY.MM.DD HH:MM]")
        raise SystemExit(1)
    try:
        import hooks
        hooks.postavit_ceh("торговый_хаос")
    except Exception:
        pass
    kogda = a[2] if len(a) > 2 else None
    r = voda_na_stole(a[0].upper(), a[1].upper(), as_of_date=kogda)
    print(slovami(r))

# VODA_NA_STOLE_V1 - marker
'''


# ─────────────────────────────────────────────────────────────
# 2. ЯКОРЬ — вместо веера отдаёт воду
# ─────────────────────────────────────────────────────────────
GA_STAROE = """    senior = senior_timeframe(working_tf)
    if senior is None:
        return {"bias": "NONE", "senior_tf": None, "ok": False,
                "why": "рабочий на потолке лесенки — старшего этажа нет"}
"""

GA_NOVOE = """    # VODA_NA_STOLE_V1: направление старшего этажа меряется СТРУКТУРОЙ
    # (две вершины и две впадины по фракталу, подтверждение этажом выше),
    # а не веером Аллигатора. Веер соврал на откате в 43% случаев — такой
    # факт трейдеру на стол класть нельзя. Вид ответа прежний, читатели
    # не меняются. Вода не сложилась — вернётся bias=NONE, и это честное
    # «воды нет», а не поломка.
    try:
        import voda as _voda
        _v = _voda.voda_na_stole(symbol, working_tf, as_of_date=as_of_date)
        if _v:
            return _v
    except Exception as _e:
        print(f"[ЯКОРЬ] вода не посчиталась ({_e}) — беру старый веер")

    senior = senior_timeframe(working_tf)
    if senior is None:
        return {"bias": "NONE", "senior_tf": None, "ok": False,
                "why": "рабочий на потолке лесенки — старшего этажа нет"}
"""


# ─────────────────────────────────────────────────────────────
# 3. ИСКАТЕЛЬ — ворота сняты
# ─────────────────────────────────────────────────────────────
KAND_STAROE = """            _komp = p.get("компас")
            if _komp in ("BULL", "BEAR") and _komp != p.get("разворотный"):
                _mimo_trenda += 1
                p = None
"""

KAND_NOVOE = """            # VODA_NA_STOLE_V1: ВОРОТ БОЛЬШЕ НЕТ. Раньше место против
            # старшего тренда выбрасывалось — код решал за трейдера,
            # входить или нет. Слово Шефа: вода это факт на столе, а не
            # разрешение. Место отдаётся как есть, вода кладётся рядом
            # отдельным полем; решает человек — он и рискует своим стопом.
            _komp = p.get("компас")
            p["вода"] = _komp
            if _komp in ("BULL", "BEAR") and _komp != p.get("разворотный"):
                _mimo_trenda += 1
"""

KAND_STAROE_2 = """        _skazat(f"[ИСКАТЕЛЬ] мимо старшего тренда: {_mimo_trenda} "
                f"мест — там большая вода против")
"""

KAND_NOVOE_2 = """        _skazat(f"[ИСКАТЕЛЬ] против воды: {_mimo_trenda} мест — "
                f"отданы трейдеру как есть, судит он")
"""


# ─────────────────────────────────────────────────────────────
# 4. СТОЛ — вода отдельной строкой
# ─────────────────────────────────────────────────────────────
STOL_STAROE_1 = """    compass = None
    starshiy_tf = None
    starshiy_prishyol = False
    try:
"""

STOL_NOVOE_1 = """    compass = None
    starshiy_tf = None
    starshiy_prishyol = False
    _voda_etazhi = None       # VODA_NA_STOLE_V1
    _voda_why = ""            # VODA_NA_STOLE_V1
    try:
"""

STOL_STAROE_2 = """        starshiy_prishyol = bool((st or {}).get("ok"))
        b = (st or {}).get("bias")
        compass = b if b in ("BULL", "BEAR") else None
    except Exception:
        compass = None
"""

STOL_NOVOE_2 = """        starshiy_prishyol = bool((st or {}).get("ok"))
        b = (st or {}).get("bias")
        compass = b if b in ("BULL", "BEAR") else None
        # VODA_NA_STOLE_V1: чем именно вода такая — целиком на стол
        _voda_etazhi = (st or {}).get("вода_этажи")
        _voda_why = (st or {}).get("why") or ""
    except Exception:
        compass = None
"""

STOL_STAROE_3 = """        "старший_аллигатор": compass,          # куда смотрит большая вода
"""

STOL_NOVOE_3 = """        "старший_аллигатор": compass,          # куда смотрит большая вода
        # VODA_NA_STOLE_V1: вода — ФАКТ рядом с сигналом, не ворота.
        # Считается структурой старших этажей (фрактал: две вершины,
        # две впадины). Нет согласия этажей — нет и воды.
        "вода": compass,
        "вода_этажи": _voda_etazhi,
        "вода_почему": _voda_why,
"""

STOL_STAROE_4 = '''        (f"старший Аллигатор: {p.get('старший_аллигатор')}"
         if p.get('старший_аллигатор')
         else f"старший Аллигатор: НЕТ ДАННЫХ "
              f"({p.get('старший_этаж') or 'старший этаж'} не пришёл)")
        + (f"   направление рабочего: {p.get('направление_рабочего')}"
           if p.get('направление_рабочего') else "")
        + f"   "
        f"этаж: {p.get('этаж') or '—'}",
'''

STOL_NOVOE_4 = '''        _voda_strokoy(p),   # VODA_NA_STOLE_V1
'''

STOL_HVOST = '''

# ══════════════════════════════════════════════════════════════
# VODA_NA_STOLE_V1 — вода отдельной строкой
# ══════════════════════════════════════════════════════════════

def _voda_strokoy(p: dict) -> str:
    # Вода на столе: сторона, оба этажа, и чем её нет, если её нет.
    # Слово Шефа: вода не разрешает и не запрещает. Она лежит рядом с
    # сигналом, и трейдер решает сам — в том числе войти против неё, со
    # своим стопом. Поэтому здесь нет ни «можно», ни «нельзя»: только
    # куда смотрит структура старших этажей.
    v = (p or {}).get("вода")
    etazhi = (p or {}).get("вода_этажи") or ""
    pochemu = (p or {}).get("вода_почему") or ""
    svoy = (p or {}).get("направление_рабочего")
    hvost = (f"   направление рабочего: {svoy}" if svoy else "")
    hvost += f"   этаж: {(p or {}).get('этаж') or '—'}"
    golova = f"ВОДА: {v}" if v in ("BULL", "BEAR") else "ВОДА: НЕТ НА СТОЛЕ"
    if pochemu:
        golova += f"   ({pochemu})"
    golova += hvost
    if etazhi:
        golova += f"\\n     этажи: {etazhi}"
    return golova
'''


def main():
    b = _nayti_birzhu()
    print(f"\nБиржа: {b}\n")

    v = b / "voda.py"
    if v.exists() and MARKER in v.read_text(encoding="utf-8"):
        print("  . voda.py: уже лежит, пропускаю")
    else:
        if v.exists():
            shutil.copy2(v, v.with_suffix(".py.bak"))
        ast.parse(VODA_SRC)
        v.write_text(VODA_SRC, encoding="utf-8")
        print("  + voda.py: положен")

    _pravka(b / "global_anchor.py", [(GA_STAROE, GA_NOVOE)])
    _pravka(b / "kandidaty.py", [(KAND_STAROE, KAND_NOVOE),
                                 (KAND_STAROE_2, KAND_NOVOE_2)])

    s = b / "stol.py"
    if MARKER in s.read_text(encoding="utf-8"):
        print("  . stol.py: уже накачен, пропускаю")
    else:
        t = s.read_text(encoding="utf-8")
        for staroe, novoe in ((STOL_STAROE_1, STOL_NOVOE_1),
                              (STOL_STAROE_2, STOL_NOVOE_2),
                              (STOL_STAROE_3, STOL_NOVOE_3),
                              (STOL_STAROE_4, STOL_NOVOE_4)):
            if t.count(staroe) != 1:
                raise SystemExit(
                    f"  X stol.py: якорь не найден или не один "
                    f"({t.count(staroe)}). Файл НЕ ТРОНУТ.\n"
                    f"    якорь: {staroe.strip()[:70]}")
            t = t.replace(staroe, novoe)
        t = t.rstrip() + "\n" + STOL_HVOST + "\n# " + MARKER + " - marker\n"
        ast.parse(t)
        shutil.copy2(s, s.with_suffix(".py.bak"))
        s.write_text(t, encoding="utf-8")
        print("  + stol.py: строка воды и её сборщик на месте (.bak рядом)")

    print("\nГотово. Проверить, не поднимая города:")
    print("    py Биржа/voda.py EURUSD H4")
    print("    py Биржа/stol.py EURUSD H4")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
