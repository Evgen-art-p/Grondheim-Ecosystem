# -*- coding: utf-8 -*-
"""
zamerit_iskatelya.py

Ничего не чинит и ничего не меняет. Гоняет искателя на твоей машине с
секундомером и показывает, ГДЕ уходит время. Нужен, чтобы перестать
гадать: у меня история пролетает на любом варианте, потому что данные
лежат в памяти, а у тебя они на диске и в терминале.

Считает три вещи:
  · сколько всего заняло и сколько баров перебрал
  · сколько раз кто-то ходил за барами (и на какие этажи)
  · пятнадцать самых дорогих мест по суммарному времени

Запуск из корня репо:
    py zamerit_iskatelya.py                 (EURUSD H4, 600 баров)
    py zamerit_iskatelya.py --symbol XAUUSD --tf H1 --barov 1500
"""
import argparse
import cProfile
import io
import pstats
import sys
import time
from collections import Counter
from pathlib import Path


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "kandidaty.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    put = input("Не нашёл корень. Перетащи сюда папку репо и Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--tf", default="H4")
    ap.add_argument("--barov", type=int, default=600,
                    help="сколько баров истории перебрать (меньше — быстрее)")
    ap.add_argument("--mest", type=int, default=5)
    a = ap.parse_args()

    koren = nayti_koren()
    sys.path[:0] = [str(koren / "Биржа"), str(koren)]
    print(f"Город: {koren}")

    import feed_source
    rezhim = feed_source.get_feed_mode().get("mode")
    print(f"кран: {rezhim}   пара: {a.symbol} {a.tf}   "
          f"баров: {a.barov}\n")

    # ── считаем, кто и куда ходит за барами ──
    schyot = Counter()
    vremya = Counter()
    nastoyashchiy = feed_source.bars

    def _mericha(symbol, tf, count=2000):
        t0 = time.perf_counter()
        r = nastoyashchiy(symbol, tf, count)
        dt = time.perf_counter() - t0
        klyuch = f"{symbol} {tf}" + ("" if r[0] else "  ← ПУСТО")
        schyot[klyuch] += 1
        vremya[klyuch] += dt
        return r

    feed_source.bars = _mericha
    # искатель и ядро берут bars по имени модуля — подменяем и там
    import williams_core
    for mod_name in ("kandidaty", "global_anchor", "williams_core"):
        try:
            __import__(mod_name)
        except Exception:
            pass

    import kandidaty

    print("── гоняю искателя ──")
    tihiy = io.StringIO()
    nastoyashchiy_stdout = sys.stdout
    prof = cProfile.Profile()
    t0 = time.perf_counter()
    try:
        sys.stdout = tihiy
        prof.enable()
        spisok = kandidaty.iskat(a.symbol, a.tf, skolko=a.mest,
                                 predel_barov=a.barov, govorit=lambda *x: None)
        prof.disable()
    finally:
        sys.stdout = nastoyashchiy_stdout
    itogo = time.perf_counter() - t0

    print(f"\nвсего: {itogo:.1f} с · перебрано до {a.barov} баров · "
          f"найдено мест: {len(spisok)}")
    if itogo > 0 and a.barov:
        print(f"на бар: {itogo / a.barov * 1000:.0f} мс")

    print("\n── кто ходил за барами ──")
    if not schyot:
        print("  никто (данные уже были в памяти)")
    for k, n in schyot.most_common(10):
        print(f"  {n:5} раз · {vremya[k]:6.1f} с всего · {k}")

    print("\n── пятнадцать самых дорогих мест ──")
    s = io.StringIO()
    st = pstats.Stats(prof, stream=s).sort_stats("cumulative")
    st.print_stats(15)
    for line in s.getvalue().splitlines():
        t = line.strip()
        if not t or t.startswith(("Ordered by", "ncalls")) or "function calls" in t:
            continue
        print("  " + t[:120])

    print("\nПокажи этот вывод целиком — по нему видно, где именно")
    print("уходит время, и гадать больше не придётся.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
