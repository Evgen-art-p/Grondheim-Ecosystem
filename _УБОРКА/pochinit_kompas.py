# -*- coding: utf-8 -*-
"""
pochinit_kompas.py · MARKER: KOMPAS_CHESTNYY_V1

ЧТО НАШЛОСЬ
───────────
В логе Шефа десяток раз:  [FEED] ⚠️  Нет котировок: EURUSD D1
А на столе при этом:      — старший Аллигатор: BEAR   этаж: H4

H4 — это её РАБОЧИЙ этаж. Старший не пришёл, и компас молча подменился
расчётом по рабочему — но остался подписан как «старший Аллигатор».

Трейдер думает, что видит направление сверху, а видит свой же этаж.
Это тихое враньё: оно не падает, не жалуется и выглядит правдой.
Ровно того же рода, что кадр не того куска, — и такое же опасное,
потому что на компас опирается решение.

Как это вышло: в `stol.py` при пустом старшем этаже стоит откат на
`md["global_bias"]`, а тот считается по рабочему. Задумывалось,
похоже, как «лучше хоть что-то, чем ничего». На деле «хоть что-то»
под чужой подписью хуже, чем честное «не знаю».

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Старший этаж не пришёл — компас пуст, и на столе так и написано:

       — старший Аллигатор: НЕТ ДАННЫХ (D1 не пришёл)   этаж: H4

   Подмены рабочим этажом больше нет.

2. На столе появляется отдельная строка «направление на рабочем» —
   то самое `global_bias`, но названное своим именем. Факт полезный,
   врать он перестаёт только когда подписан правильно.

3. В консоль — предупреждение один раз на прогон, чтобы было видно:

       [СТОЛ] ⚠️  компаса нет: старший этаж D1 не пришёл

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_kompas.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KOMPAS_CHESTNYY_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "stol.py").exists()
            and (p / "Биржа" / "global_anchor.py").exists())


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


ST_KOMPAS = '''    compass = None
    try:
        from global_anchor import global_trend
        st = global_trend(symbol, timeframe,
                          as_of_date=(md.get("bar_time")))
        b = (st or {}).get("bias")
        compass = b if b in ("BULL", "BEAR") else None
    except Exception:
        compass = None
    if compass is None:
        gb = md.get("global_bias")
        compass = gb if gb in ("BULL", "BEAR") else None'''

NOV_KOMPAS = '''    compass = None
    starshiy_tf = None
    starshiy_prishyol = False
    try:
        from global_anchor import global_trend, senior_timeframe
        starshiy_tf = senior_timeframe(timeframe)
        st = global_trend(symbol, timeframe,
                          as_of_date=(md.get("bar_time")))
        starshiy_prishyol = bool((st or {}).get("ok"))
        b = (st or {}).get("bias")
        compass = b if b in ("BULL", "BEAR") else None
    except Exception:
        compass = None
    # KOMPAS_CHESTNYY_V1: раньше здесь стояла ПОДМЕНА — старший этаж
    # не пришёл, и компас брался из md["global_bias"], который считан
    # по РАБОЧЕМУ этажу. А на столе он оставался подписан «старший
    # Аллигатор»: трейдер думал, что видит направление сверху, а видел
    # свой же этаж. Тихое враньё — не падает, не жалуется, выглядит
    # правдой, и на него опирается решение.
    # Теперь: не пришёл — значит нет. Направление рабочего этажа
    # отдаётся отдельной строкой, под своим именем.
    if compass is None and not starshiy_prishyol:
        print(f"[СТОЛ] ⚠️  компаса нет: старший этаж "
              f"{starshiy_tf or '?'} не пришёл")
    svoy_etazh_napravlenie = md.get("global_bias")
    if svoy_etazh_napravlenie not in ("BULL", "BEAR"):
        svoy_etazh_napravlenie = None'''

ST_PRIBORY = '''        "старший_аллигатор": compass,          # куда смотрит большая вода'''
NOV_PRIBORY = '''        "старший_аллигатор": compass,          # куда смотрит большая вода
        # KOMPAS_CHESTNYY_V1: чем именно пуст компас и что говорит
        # рабочий этаж — под своим именем, а не под чужим
        "старший_этаж": starshiy_tf,
        "старший_пришёл": starshiy_prishyol,
        "направление_рабочего": svoy_etazh_napravlenie,'''


# строка стола: было «старший Аллигатор: —», из чего не понять,
# спит он или его вовсе нет
ST_STR = (
    '        f"старший Аллигатор: '
    "{p.get('старший_аллигатор') or '—'}"
    '   "'
)
NOV_STR = (
    '        (f"старший Аллигатор: '
    "{p.get('старший_аллигатор')}"
    '"\n'
    "         if p.get('старший_аллигатор')\n"
    '         else f"старший Аллигатор: НЕТ ДАННЫХ "\n'
    '              f"('
    "{p.get('старший_этаж') or 'старший этаж'}"
    ' не пришёл)")\n'
    '        + (f"   направление рабочего: '
    "{p.get('направление_рабочего')}"
    '"\n'
    "           if p.get('направление_рабочего') else \"\")\n"
    '        + f"   "'
)


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    stol = koren / "Биржа" / "stol.py"
    t = stol.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [("компас", ST_KOMPAS, NOV_KOMPAS),
            ("приборы", ST_PRIBORY, NOV_PRIBORY),
            ("строка стола", ST_STR, NOV_STR)]
    beda = [imya for imya, st, _ in pary if t.count(st) != 1]
    if beda:
        print(f"✗ якоря не найдены дословно: {', '.join(beda)}")
        return 1

    novyy = t
    for _, st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = stol.with_suffix(f".py.bak_kompas_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(stol, bak)
    stol.write_text(novyy, encoding="utf-8")
    print(f"✓ компас стал честным (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(stol), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь на столе:")
    print("  старший Аллигатор: BULL          — если пришёл")
    print("  старший Аллигатор: НЕТ ДАННЫХ    — если нет")
    print("\nПодмены рабочим этажом больше нет: трейдер видит, что")
    print("компаса нет, а не думает, что смотрит сверху.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
