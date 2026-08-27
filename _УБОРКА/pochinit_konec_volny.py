# -*- coding: utf-8 -*-
"""
pochinit_konec_volny.py · MARKER: KONEC_VOLNY_1_V2

СЧЁТ ШЕФА ОКАЗАЛСЯ ВЕРНЕЕ МОЕГО КОДА
────────────────────────────────────
Шеф: «Не так редко. Несколько раз в год на четырёх часах. Считай сам:
длина волны — и сколько волн видимых на H4 ты насчитаешь за год?»

Посчитал. История EURUSD H4, 2700 баров ≈ 1.8 года:

    обратных разворотников при ЖИВОЙ точке ....... 9   (5 в год)
    из них прошли моё условие .................... 1

Пять в год — ровно то, что он сказал. А до события доходило одно за
полтора года, потому что я навесил лишнюю проверку.

ЧТО БЫЛО ЛИШНЕГО
────────────────
Я потребовал, чтобы структура позади обратного разворотника
УКЛАДЫВАЛАСЬ в число баров, прожитых точкой. Звучало разумно: раз
волна отмерена от точки, её структура не должна тянуться раньше.

Но линейка меряет структуру четырьмя переходами нуля AO назад — а это
медиана семьдесят шесть баров, и она почти всегда достаёт ЗА точку,
через предыдущую волну. Требовать, чтобы она уложилась в прожитое, —
значит ждать точку, которая прожила больше семидесяти баров. Таких
почти нет.

Условие моё, не твоё и не из канона. Снимаю.

ЧТО ОСТАЁТСЯ
────────────
Конец первой волны = разворотный бар в ОБРАТНУЮ сторону от точки, с
читаемой структурой, пока точка жива. Тот же прибор, что поймал саму
точку, ничего сверх.

Ожидаемо: около пяти событий в год на H4 вместо одного за полтора.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ postavit_konec_pervoy_volny.py — патч это проверит.
Запуск: py pochinit_konec_volny.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KONEC_VOLNY_1_V2"
NUZHEN = "KONEC_VOLNY_1_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "hooks.py").exists()


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


YAKOR2 = '''                isk["struktura_pozadi"] = wf.get("dlina")'''

NOV2 = '''                isk["struktura_pozadi"] = wf.get("dlina")
                # KONEC_VOLNY_1_V2: новая точка — новая жизнь. Без этой
                # строки отметка о конце волны 1 оставалась от ПРОШЛОЙ
                # точки и навсегда запирала событие: за 1.8 года срабатывало
                # ровно один раз, хотя обратных разворотников было девять.
                isk["konec_volny_1"] = None'''

YAKOR = '''            _dlina = wf.get("dlina") or 0
            _prozhito = int(isk.get("barov_s_tochki") or 0)
            if _dlina and _dlina <= _prozhito:'''

NOV = '''            # KONEC_VOLNY_1_V2: снято моё лишнее условие «структура
            # уложилась в прожитое точкой». Линейка меряет структуру
            # четырьмя нулями AO назад — медиана 76 баров, она почти
            # всегда достаёт за точку. С условием событие случалось раз
            # в полтора года, без него — пять раз в год, ровно как Шеф
            # и насчитал по длине волны.
            _dlina = wf.get("dlina") or 0
            _prozhito = int(isk.get("barov_s_tochki") or 0)
            if True:'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "hooks.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_konec_pervoy_volny.py — этот патч")
        print("  правит его условие, а не пишет событие с нуля.")
        return 1
    for yak in (YAKOR, YAKOR2):
        if t.count(yak) != 1:
            print(f"✗ якорь найден {t.count(yak)} раз — жду ровно один")
            print(f"  {yak.strip().splitlines()[0][:70]}")
            return 1

    novyy = t.replace(YAKOR, NOV, 1).replace(YAKOR2, NOV2, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_volna1v2_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ лишнее условие снято (копия: {bak.name})")
    print("\nТеперь конец первой волны — просто обратный разворотник с")
    print("читаемой структурой, пока точка жива. Около пяти событий в год")
    print("на H4 вместо одного за полтора года.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
