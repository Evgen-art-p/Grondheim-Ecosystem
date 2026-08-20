# -*- coding: utf-8 -*-
"""
postavit_iskatel_na_svoyom_etazhe.py · MARKER: ISKATEL_SVOY_ETAZH_V1

СЛОВО ШЕФА (20.08)
──────────────────
«Ты пытаешься на каждом шаге по этажам ходить — не нужно этого. Первый
сигнал, авантюриста, первый разворотник — ищем на РАБОЧЕМ ТФ. То есть
задаём рабочий ТФ и гоняем. Нашёл — и перебрал. Так уже сэкономишь
время.»

Он прав, и это лучше того, что я предлагал. Я собирался ЗАПОМИНАТЬ
ответ старшего этажа. А правильно — не задавать этот вопрос вовсе,
пока ищем.

ЧТО ПРОИСХОДИТ СЕЙЧАС
─────────────────────
Искатель ищет разворотный бар с читаемой структурой — обе вещи
считаются на РАБОЧЕМ этаже. Старший ему для этого не нужен ни на
секунду. Но он зовёт общий сбор приборов, а тот внутри лезет за
старшим этажом — на каждом баре.

Замер Шефа (XAUUSD H1, 1500 баров): 83 с всего, из них 68 — походы за
барами H8. Девятьсот девятнадцать запусков терминала подряд, чтобы
девятьсот девятнадцать раз получить один и тот же ответ.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. `williams_core.build_market_data` получает необязательное
   `starshiy: bool = True`. По умолчанию всё как было — стол, движок,
   кадр ничего не заметят. `starshiy=False` — старший этаж не
   спрашивается вовсе, компас остаётся синей линией рабочего этажа
   (честный запасной вариант, он и так стоял при сбое источника).

2. `kandidaty._priznaki` ходит со `starshiy=False`. Ищем на своём
   этаже, как и сказано.

3. Найденному месту компас ДОСЧИТЫВАЕТСЯ отдельно — один раз на
   место, не на бар. Мест пять-пятнадцать, значит и походов столько
   же. Строка «компас BULL» в отчёте остаётся на месте.

Итого: девятьсот девятнадцать походов превращаются в число найденных
мест. Ни одного нового числа, ни одной новой проверки — просто не
задаём вопрос, который не нужен, пока ищем.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_iskatel_na_svoyom_etazhe.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "ISKATEL_SVOY_ETAZH_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "williams_core.py").exists()
            and (p / "Биржа" / "kandidaty.py").exists())


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


# ── ядро: необязательный отказ от старшего этажа ─────────────

C_YAKOR_PODPIS = '''def build_market_data(
    bars:      list[dict],
    symbol:    str   = "UNKNOWN",
    timeframe: str   = "D1",
    point:     Optional[float] = None,
) -> dict:'''

C_NOV_PODPIS = '''def build_market_data(
    bars:      list[dict],
    symbol:    str   = "UNKNOWN",
    timeframe: str   = "D1",
    point:     Optional[float] = None,
    starshiy:  bool  = True,   # ISKATEL_SVOY_ETAZH_V1
) -> dict:'''

C_YAKOR_ZOV = '''    try:
        from global_anchor import global_trend as _gt
        _bar_time = bars[-1]["date"]'''

C_NOV_ZOV = '''    # ISKATEL_SVOY_ETAZH_V1: starshiy=False — старший этаж не
    # спрашиваем вовсе. Нужно тем, кто ищет на СВОЁМ этаже (искатель:
    # разворотный бар и структура считаются на рабочем). Компас тогда
    # остаётся синей линией рабочего — тот же запасной вариант, что
    # стоял здесь при недоступном источнике.
    try:
        if not starshiy:
            raise RuntimeError("старший этаж не спрашиваем")
        from global_anchor import global_trend as _gt
        _bar_time = bars[-1]["date"]'''

# ── искатель: искать на своём этаже, компас — найденному месту ──

K_YAKOR_PRIZNAKI = '''def _priznaki(bars: list, symbol: str, tf: str, point: float):
    """Факты последнего бара окна. Не кандидат — не None."""
    from williams_core import build_market_data
    md = build_market_data(bars, symbol=symbol, timeframe=tf, point=point)'''

K_NOV_PRIZNAKI = '''def _dobrat_kompas(k: dict, bars: list, symbol: str, tf: str, point: float):
    """ISKATEL_SVOY_ETAZH_V1: компас НАЙДЕННОМУ месту, по одному разу
    на место, а не на каждый перебранный бар. Не вышло — остаётся то,
    что дал рабочий этаж; место от этого не пропадает."""
    try:
        from williams_core import build_market_data
        md = build_market_data(bars, symbol=symbol, timeframe=tf,
                               point=point, starshiy=True)
        if md and md.get("global_bias"):
            k["компас"] = md.get("global_bias")
    except Exception as e:
        print(f"[ИСКАТЕЛЬ] компас месту не досчитан ({e}) — не беда")
    return k


def _priznaki(bars: list, symbol: str, tf: str, point: float):
    """Факты последнего бара окна. Не кандидат — не None.

    ISKATEL_SVOY_ETAZH_V1: ищем на СВОЁМ, рабочем этаже. Разворотный
    бар и структура считаются здесь же, старший этаж для поиска не
    нужен — и не спрашивается (слово Шефа 20.08).
    """
    from williams_core import build_market_data
    md = build_market_data(bars, symbol=symbol, timeframe=tf, point=point,
                           starshiy=False)'''


def _pravit(f: Path, pary: list, imya: str) -> bool:
    t = f.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"· {imya}: маркер уже стоит — пропускаю")
        return True
    for yakor, _ in pary:
        n = t.count(yakor)
        if n != 1:
            print(f"✗ {imya}: якорь найден {n} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return False
    novyy = t
    for yakor, zamena in pary:
        novyy = novyy.replace(yakor, zamena, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ {imya}: после правки не разбирается — {e}")
        return False
    if SUHO:
        print(f"· {imya}: правка готова (сухой прогон)")
        return True
    bak = f.with_suffix(f".py.bak_svoyetazh_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ {imya}: НЕ компилируется ({e}) — откатил из {bak.name}")
        return False
    print(f"✓ {imya}: правка легла (копия: {bak.name})")
    return True


def _dopisat_zov_kompasa(koren: Path) -> bool:
    """В iskat: найденному месту досчитать компас (один раз на место)."""
    f = koren / "Биржа" / "kandidaty.py"
    t = f.read_text(encoding="utf-8")
    yakor = "        p = _priznaki(okno, symbol, tf, point)\n"
    if t.count(yakor) != 1:
        print(f"✗ kandidaty.py: вызов _priznaki найден {t.count(yakor)} раз")
        print("  компас месту досчитан не будет — скажи мне, доделаю")
        return False
    novyy = t.replace(
        yakor,
        yakor + "        if p:\n"
                "            _dobrat_kompas(p, okno, symbol, tf, point)"
                "   # ISKATEL_SVOY_ETAZH_V1\n", 1)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ kandidaty.py: досчёт компаса не встал ({e})")
        return False
    if SUHO:
        print("· kandidaty.py: досчёт компаса готов (сухой прогон)")
        return True
    f.write_text(novyy, encoding="utf-8")
    py_compile.compile(str(f), doraise=True)
    print("✓ kandidaty.py: найденному месту компас досчитывается отдельно")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")

    if not _pravit(koren / "Биржа" / "williams_core.py",
                   [(C_YAKOR_PODPIS, C_NOV_PODPIS),
                    (C_YAKOR_ZOV, C_NOV_ZOV)], "williams_core.py"):
        return 1
    uzhe = MARKER in (koren / "Биржа" / "kandidaty.py").read_text(
        encoding="utf-8")
    if not _pravit(koren / "Биржа" / "kandidaty.py",
                   [(K_YAKOR_PRIZNAKI, K_NOV_PRIZNAKI)], "kandidaty.py"):
        print("\n⚠️  ядро поправлено, искатель нет. Верни williams_core.py")
        print("   из свежей .bak_svoyetazh_* и покажи мне вывод.")
        return 1
    if not uzhe and not _dopisat_zov_kompasa(koren):
        return 1

    if SUHO:
        return 0
    print("\nПроверь тем же замером, один в один:")
    print("  py zamerit_iskatelya.py --symbol XAUUSD --tf H1 --barov 1500")
    print("\nСтрока «919 раз · XAUUSD H8» должна упасть до числа найденных")
    print("мест. Всё остальное — стол, кадр, движок — ходит на старший")
    print("этаж как ходило: там он по делу.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
