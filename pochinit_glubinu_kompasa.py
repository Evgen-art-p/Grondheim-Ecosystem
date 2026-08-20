# -*- coding: utf-8 -*-
"""
pochinit_glubinu_kompasa.py · MARKER: GLUBINA_KOMPASA_V1

ЧТО НАЙДЕНО
───────────
На живом терминале компас молчит: «[FEED] ⚠️ Нет котировок: EURUSD D1»,
и стол честно пишет «старший Аллигатор: НЕТ ДАННЫХ». При этом проверка
котировок показывает, что дневки терминал отдаёт прекрасно — двести
баров, свежие, до сегодняшнего утра.

Разница в одном числе. `global_anchor.global_trend` просит у источника
СТО ТЫСЯЧ баров старшего этажа:

    sbars, point = source_bars(symbol, senior, count=100000)

Сто тысяч дневок — это четыреста лет. MetaTrader на такой запрос
возвращает пустоту, а не «сколько есть»; попытки повтора в насосе не
помогают, потому что дело не в прокачке истории, а в самом числе.

Почему не замечали: в ТЕСТЕРЕ бары приходят из папки, и там сто тысяч
означают просто «весь файл» — компас работал. Как только кран встал на
реал, старший этаж пропал.

Сразу за этим запросом в том же файле стоит:

    # берём последние 300 из отсечённого (хватает на Аллигатор + запас)

То есть больше трёхсот баров компасу и не нужно — сто тысяч просились
впустую с самого начала.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Просит посильную глубину, лесенкой сверху вниз: 2000 (столько по
умолчанию просит сам насос) → 500 → 200. Первый непустой ответ и
берём. Ни одного нового числа: 2000 — умолчание `mt5_feed.pull_bars`,
200 — то, что проверка котировок только что получила живьём.

Отсечка будущего, обрезка до 300 баров и весь расчёт веера — не
тронуты.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_glubinu_kompasa.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "GLUBINA_KOMPASA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "global_anchor.py").exists()


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


YAKOR = '''    sbars, point = source_bars(symbol, senior, count=100000)'''

NOV = '''    # GLUBINA_KOMPASA_V1: было count=100000 — сто тысяч дневок, четыреста
    # лет. В тестере это значило «весь файл» и работало; живой MetaTrader
    # на такое число отдаёт ПУСТО, и компас пропадал молча, а трейдер
    # оставался без старшей воды. Ниже по коду и так берутся последние
    # 300 баров — больше компасу не нужно никогда.
    # Лесенка посильных глубин: 2000 — умолчание mt5_feed.pull_bars,
    # 200 — то, что терминал отдаёт заведомо. Первый непустой ответ.
    sbars, point = [], None
    for _glubina in (2000, 500, 200):
        sbars, point = source_bars(symbol, senior, count=_glubina)
        if sbars:
            break'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "global_anchor.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    n = t.count(YAKOR)
    if n != 1:
        print(f"✗ якорь найден {n} раз — жду ровно один")
        print(f"  {YAKOR.strip()}")
        return 1

    novyy = t.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_kompas_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ компас просит посильную глубину (копия: {bak.name})")
    print("\nПроверить сразу, без модели и без денег:")
    print("  py stol_pokazat.py EURUSD H4")
    print("\nВ строке «старший Аллигатор» вместо НЕТ ДАННЫХ должно")
    print("появиться BULL или BEAR. Если старший спит — так и напишет,")
    print("это тоже честный ответ, а не поломка.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
