# -*- coding: utf-8 -*-
"""
postavit_mashinu_vremeni.py · MARKER: MASHINA_VREMENI_V1

ЗАЧЕМ
─────
Слово Шефа: «сейчас выходной, котировки стоят, но у меня есть истории,
этажи — давай через тестер сделаем новый метод подход».

И раньше: «самое важное — научиться видеть волну, видеть тот паттерн,
искать много по истории».

ЧТО МЕШАЛО
──────────
Тестерный кран (`feed_source._bars_from_folder`) отдаёт ВСЕГДА
последние `count` баров файла. То есть вечный конец истории, один и
тот же. Листать нечего: ни отмотать назад, ни шагнуть вперёд.
Поэтому «прогнать историю» и было невозможно без старого тестера.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Ставит в кран КУРСОР ВРЕМЕНИ — момент, в котором город «сейчас
находится». Кран отдаёт бары ДО этого момента и ни одного после.

    момент не задан  → всё как было: конец истории, ничего не менялось
    момент задан     → город стоит в этой точке прошлого

После этого на истории работает ВСЁ, что работает в реале, без единой
правки: кадр, стол, руки трейдера, обход этажей, Совет. Они краном не
интересуются — просят бары и получают бары.

ГЛАВНАЯ ТОНКОСТЬ: ЧЕСТНОСТЬ СТАРШИХ ЭТАЖЕЙ
──────────────────────────────────────────
Наивно отрезать «бары с датой меньше момента» нельзя. Если курсор
стоит на 23 июня 19:00, то дневной бар за 23 июня уже начался, но ещё
НЕ ЗАКРЫТ — в нём лежат цены, которых в 19:00 никто знать не мог.
Отдать его — значит показать трейдеру будущее и получить прогон,
который врёт в свою пользу.

Поэтому кран отдаёт только ЗАКРЫТЫЕ бары: конец бара (начало плюс
длительность этажа) должен быть не позже момента. Незакрытый бар
старшего этажа остаётся за краем, как и в жизни.

ЧТО ЕЩЁ ВНУТРИ
──────────────
* `Биржа/masshtab.py` — длительность этажа в минутах (её нигде не
  было, а без неё «закрыт ли бар» не посчитать);
* `Биржа/istoriya.py` — курсор: поставить, шагнуть, где стоим;
  хранится на общей площади цеха (`trading_state["feed"]["момент"]`),
  рядом с режимом крана — второго файла правды не заводим;
* `listat.py` в корне — листалка из консоли, чтобы пройти историю
  глазами: шаг вперёд, кадр на экран, что показывают числа.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_mashinu_vremeni.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "MASHINA_VREMENI_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "feed_source.py").exists()
            and (p / "Биржа" / "masshtab.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
# 1. длительность этажа — в лесенку
# ═══════════════════════════════════════════════════════════
ST_M = '''def est(tf: str) -> bool:'''
NOV_M = '''# MASHINA_VREMENI_V1: сколько минут длится один бар этажа. Нужно,
# чтобы понять, ЗАКРЫТ ли бар к заданному моменту истории. Без этого
# старший этаж показывает недожитый бар — то есть будущее.
MINUTY = {"MN1": 43200, "W1": 10080, "D1": 1440, "H12": 720, "H8": 480,
          "H4": 240, "H2": 120, "H1": 60, "M30": 30, "M15": 15,
          "M10": 10, "M5": 5}


def minut(tf: str) -> int:
    """Длительность бара этажа в минутах. Неизвестный этаж — 0."""
    return MINUTY.get((tf or "").strip().upper(), 0)


def est(tf: str) -> bool:'''


ISTORIYA_PY = '''# -*- coding: utf-8 -*-
# MASHINA_VREMENI_V1
"""
МАШИНА ВРЕМЕНИ — где город «сейчас находится» в истории.

ЗАЧЕМ
    Чтобы ходить по прошлому как по живому рынку: остановиться в
    любой точке, посмотреть кадр, спросить трейдера, шагнуть дальше.
    Так набивается глаз — и Шефу, и трейдеру.

ЗАКОН ЭТОГО ФАЙЛА
    Момент — ОДИН на город и лежит на общей площади цеха, рядом с
    режимом крана (trading_state["feed"]). Второго места правды нет:
    иначе кадр покажет одно, стол посчитает другое.

    Момент действует ТОЛЬКО в тестерном режиме. В реале его нет и
    быть не может — там время идёт само.
"""
from __future__ import annotations

import sys as _sys
from datetime import datetime, timedelta
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))

FORMAT = "%Y.%m.%d %H:%M"


def _plosh():
    from hooks import load_trading_state
    return (load_trading_state().get("feed") or {})


def gde_stoim() -> str:
    """Момент истории строкой «2026.06.23 19:00». Пусто — конца
    истории, то есть как было до машины времени."""
    return (_plosh().get("момент") or "").strip()


def postavit(moment) -> str:
    """Поставить город в точку истории. Пусто — снять курсор."""
    from hooks import load_trading_state, save_trading_state
    if isinstance(moment, datetime):
        moment = moment.strftime(FORMAT)
    moment = (moment or "").strip()
    t = load_trading_state()
    t.setdefault("feed", {})
    if moment:
        t["feed"]["момент"] = moment
    else:
        t["feed"].pop("момент", None)
    save_trading_state(t)
    return moment


def kak_vremya(s: str):
    """Строку бара — во время. Дневки и выше приходят без часов."""
    s = (s or "").strip()
    for f in (FORMAT, "%Y.%m.%d", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    return None


def _vse_bary(symbol: str, etazh: str) -> list:
    """ВСЕ бары файла, мимо курсора.

    Важно: спрашивать их у крана нельзя — кран уже обрезан этим же
    курсором, и шаг вперёд упирался бы в собственный край, откатывая
    момент назад. Курсор должен смотреть на полную ленту, а обрезает
    он только то, что видят трейдер и кадр.
    """
    import feed_source as fs
    from williams_core import read_mt5_csv
    p = fs._find_csv(symbol, etazh)
    if p is None:
        return []
    klyuch = str(p.resolve())
    bars = fs._FOLDER_BARS_CACHE.get(klyuch)
    if bars is None:
        bars = read_mt5_csv(str(p)) or []
        fs._FOLDER_BARS_CACHE[klyuch] = bars
    return bars


def shag(etazh: str, skolko: int = 1, symbol: str = "") -> str:
    """Шагнуть на N баров ЭТОГО этажа вперёд (или назад, если минус).

    Шагаем не по календарю, а по реальным барам файла: в выходные и
    праздники рынка нет, и календарный шаг увёл бы в пустоту.
    """
    seychas = gde_stoim()
    sym = symbol or (_plosh().get("symbol") or "")
    if not sym:
        return seychas
    vse = _vse_bary(sym, etazh)
    if not vse:
        return seychas
    daty = [b.get("date", "") for b in vse]
    if not seychas:
        i = len(daty) - 1
    else:
        i = -1
        for j, d in enumerate(daty):
            if d <= seychas:
                i = j
            else:
                break
        if i < 0:
            i = 0
    j = max(0, min(len(daty) - 1, i + skolko))
    return postavit(daty[j])


def dokuda_est(symbol: str, etazh: str) -> tuple:
    """(первый бар, последний бар) этажа в файле — границы прогулки.
    Тоже по полной ленте, мимо курсора."""
    vse = _vse_bary(symbol, etazh)
    if not vse:
        return "", ""
    return vse[0].get("date", ""), vse[-1].get("date", "")


def zakryt_li(data_bara: str, etazh: str, moment: str) -> bool:
    """Закрыт ли бар этажа к моменту.

    Главная честность машины времени: бар, который ещё идёт, отдавать
    нельзя — в нём цены, которых в этот момент никто не знал.
    """
    if not moment:
        return True
    import masshtab
    t0 = kak_vremya(data_bara)
    tm = kak_vremya(moment)
    if t0 is None or tm is None:
        return str(data_bara) <= str(moment)
    m = masshtab.minut(etazh)
    if not m:
        return t0 <= tm
    return t0 + timedelta(minutes=m) <= tm + timedelta(minutes=1)


# MASHINA_VREMENI_V1 - marker
'''


# ═══════════════════════════════════════════════════════════
# 2. кран режет историю по моменту
# ═══════════════════════════════════════════════════════════
ST_FEED = '''    if not bars:
        return [], None
    point = _test_point(symbol)
    tail = bars[-count:] if count and len(bars) > count else bars
    return tail, point'''

NOV_FEED = '''    if not bars:
        return [], None
    point = _test_point(symbol)

    # MASHINA_VREMENI_V1: если город поставлен в точку истории —
    # отдаём только то, что к этому моменту уже ЗАКРЫЛОСЬ. Незакрытый
    # бар старшего этажа содержит цены, которых тогда никто не знал;
    # отдать его — значит показать трейдеру будущее.
    try:
        import istoriya
        moment = istoriya.gde_stoim()
    except Exception:
        moment = ""
    if moment:
        do_momenta = [b for b in bars
                      if istoriya.zakryt_li(b.get("date", ""), tf, moment)]
        bars = do_momenta or []
        if not bars:
            return [], None

    tail = bars[-count:] if count and len(bars) > count else bars
    return tail, point'''


LISTAT_PY = '''# -*- coding: utf-8 -*-
# MASHINA_VREMENI_V1
"""
ЛИСТАЛКА ИСТОРИИ — пройти прошлое глазами.

    py listat.py XAUUSD H4                 — встать в конец истории
    py listat.py XAUUSD H4 2024.03.15      — встать в точку
    py listat.py XAUUSD H4 +10             — шагнуть на 10 баров
    py listat.py XAUUSD H4 -50             — отмотать назад
    py listat.py стоп                      — снять курсор (конец истории)
    py listat.py XAUUSD H4 цех=<имя>       — другой цех (по умолчанию
                                             торговый_хаос)

На каждом шаге рисует кадр и показывает голые числа: где Аллигатор,
что с AO, есть ли разворотный бар, какая волна намерена. Модель НЕ
зовётся — это бесплатно. Смотришь сам.

Позвать по этой же точке трейдера — обычной кнопкой РЫНОК в кабинете
или Советом: они возьмут из крана ровно то, что видишь ты.
"""
import sys
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
for _p in (str(_KOREN / "Биржа"), str(_KOREN / "ГОРОД")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 0

    # Стол у каждого цеха свой, и режим крана лежит в нём. Без этой
    # строки листалка читала общий стол и всегда видела РЕАЛ.
    import hooks
    ceh = "торговый_хаос"
    for x in list(a):
        if x.startswith("цех="):
            ceh = x.split("=", 1)[1]
            a.remove(x)
    hooks.postavit_ceh(ceh)

    import feed_source as fs
    import istoriya

    if a[0].lower() in ("стоп", "stop", "сброс"):
        istoriya.postavit("")
        print("Курсор снят — кран снова отдаёт конец истории.")
        return 0

    if len(a) < 2:
        print("Скажи инструмент и этаж: py listat.py XAUUSD H4")
        return 1
    symbol, etazh = a[0].upper(), a[1].upper()

    if fs.get_feed_mode()["mode"] != "tester":
        print("⚠ Кран стоит в РЕАЛЕ. Включи ТЕСТЕР в кабинете, иначе")
        print("  листать нечего — история читается только из папки.")
        return 1

    pervyy, posledniy = istoriya.dokuda_est(symbol, etazh)
    if not pervyy:
        print(f"Нет истории {symbol} {etazh} в Биржа/test_data")
        return 1

    if len(a) > 2:
        chto = a[2]
        if chto[0] in "+-":
            istoriya.shag(etazh, int(chto), symbol=symbol)
        else:
            istoriya.postavit(chto if " " in chto else chto + " 23:59")
    elif not istoriya.gde_stoim():
        istoriya.postavit(posledniy)

    moment = istoriya.gde_stoim()
    print(f"\\n📍 {symbol} {etazh} · стоим: {moment}")
    print(f"   история: {pervyy} → {posledniy}")

    b, point = fs.bars(symbol, etazh, 300)
    if not b:
        print("   баров до этого момента нет — отмотай вперёд")
        return 1
    print(f"   видно баров: {len(b)} · последний закрытый: {b[-1]['date']}")

    from williams_core import build_market_data
    md = build_market_data(b, symbol=symbol, timeframe=etazh, point=point)
    al = (md or {}).get("alligator") or {}
    wf = (md or {}).get("wave_form") or {}
    rb = (md or {}).get("rubber_band") or {}
    print(f"\\n   цена           {(md or {}).get('price')}")
    print(f"   компас         {(md or {}).get('global_bias')}")
    print(f"   Аллигатор спит {al.get('spit')}")
    print(f"   AO             {((md or {}).get('ao') or {}).get('value')}")
    print(f"   волна баров    {wf.get('dlina')}  "
          f"(читается: {wf.get('struktura_chitaetsya')})")
    print(f"   разворотный    {wf.get('bdb_dir')} @ {wf.get('bdb_price')}")
    print(f"   дивергенция    {(md or {}).get('divergence_ao')}")
    print(f"   отрыв цены     {rb.get('distance_now')} "
          f"(доля {rb.get('tension_ratio')})")

    try:
        import grafik
        put = grafik.kadr(symbol, etazh)
        if put:
            print(f"\\n   🖼 кадр: {put}")
    except Exception as e:
        print(f"   кадр не нарисовался: {e}")

    print(f"\\n   дальше:  py listat.py {symbol} {etazh} +1")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\\nEnter — закрыть окно. ")
    sys.exit(kod)
'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    masshtab = koren / "Биржа" / "masshtab.py"
    feed = koren / "Биржа" / "feed_source.py"
    istoriya = koren / "Биржа" / "istoriya.py"
    listat = koren / "listat.py"

    print("\n1. Длительность этажа — в лесенку")
    t = masshtab.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · уже стоит")
    elif t.count(ST_M) != 1:
        print(f"  ✗ якорь найден {t.count(ST_M)} раз — жду один")
        return 1
    else:
        novyy = t.replace(ST_M, NOV_M, 1) + f"\n# {MARKER} - marker\n"
        ast.parse(novyy)
        if not SUHO:
            shutil.copy2(masshtab, masshtab.with_suffix(
                f".py.bak_vremya_{datetime.now():%Y%m%d_%H%M%S}"))
            masshtab.write_text(novyy, encoding="utf-8")
        print("  ✓ минуты на этаж")

    print("\n2. Курсор истории — Биржа/istoriya.py")
    if istoriya.exists() and MARKER in istoriya.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        ast.parse(ISTORIYA_PY)
        if not SUHO:
            istoriya.write_text(ISTORIYA_PY, encoding="utf-8")
        print("  ✓ положен")

    print("\n3. Кран режет историю по моменту")
    t = feed.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · уже стоит")
    elif t.count(ST_FEED) != 1:
        print(f"  ✗ якорь крана найден {t.count(ST_FEED)} раз — жду один")
        return 1
    else:
        novyy = t.replace(ST_FEED, NOV_FEED, 1) + f"\n# {MARKER} - marker\n"
        ast.parse(novyy)
        if not SUHO:
            shutil.copy2(feed, feed.with_suffix(
                f".py.bak_vremya_{datetime.now():%Y%m%d_%H%M%S}"))
            feed.write_text(novyy, encoding="utf-8")
        print("  ✓ курсор в кране")

    print("\n4. Листалка — listat.py в корне")
    if listat.exists() and MARKER in listat.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        ast.parse(LISTAT_PY)
        if not SUHO:
            listat.write_text(LISTAT_PY, encoding="utf-8")
        print("  ✓ положена")

    if not SUHO:
        import py_compile
        for f in (masshtab, istoriya, feed, listat):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nКак пользоваться (кран должен стоять в ТЕСТЕРЕ):")
        print("   py listat.py XAUUSD H4 2024.03.15   — встать в точку")
        print("   py listat.py XAUUSD H4 +1           — шаг вперёд")
        print("   py listat.py стоп                   — снять курсор")
        print("\nПока курсор стоит, в этой же точке стоит ВЕСЬ город:")
        print("жми РЫНОК в кабинете — трейдеры увидят ровно то, что ты.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
