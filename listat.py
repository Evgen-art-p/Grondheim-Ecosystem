# -*- coding: utf-8 -*-
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
    print(f"\n📍 {symbol} {etazh} · стоим: {moment}")
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
    print(f"\n   цена           {(md or {}).get('price')}")
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
            print(f"\n   🖼 кадр: {put}")
    except Exception as e:
        print(f"   кадр не нарисовался: {e}")

    print(f"\n   дальше:  py listat.py {symbol} {etazh} +1")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
