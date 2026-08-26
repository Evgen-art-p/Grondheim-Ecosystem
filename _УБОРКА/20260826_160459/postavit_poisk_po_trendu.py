# -*- coding: utf-8 -*-
"""
postavit_poisk_po_trendu.py · MARKER: POISK_PO_TRENDU_V1

ЧТО НАШЛОСЬ
───────────
Трейдер пятнадцать раз подряд отказывался словами «это против
направления» — и был прав. Замер, EURUSD H4 за 1.8 года:

    точек ноль всего .............. 51
    ПРОТИВ дневного тренда ........ 29  (57%)
    по дневному ................... 18  (35%)
    дневных данных нет ............  4  (8%)

Больше половины мест, куда его приводили, — против большой воды. Не
он в неадеквате: искатель работал БЕЗ НАПРАВЛЕНИЯ. Компас лежал на
столе как украшение и в отборе мест не участвовал вовсе.

А в источниках это первое, от чего пляшут:

    КАНОН_ВХОДА: не торговать дивергентный бар ПРОТИВ тренда
    в сильном тренде.
    Котин: «волны нам параллельно, интересует, куда направлен
    ДНЕВНОЙ Аллигатор».

Мы это просто потеряли по дороге.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Найденному месту искатель и так досчитывает компас — по одному разу
на место (ISKATEL_SVOY_ETAZH_V1). Теперь этот компас ещё и решает,
отдавать место или нет:

    точка смотрит туда же, куда старший Аллигатор → место годится
    точка против старшего                          → мимо, молча
    старшего этажа нет вовсе                       → место годится
                                                     (не отсекаем из-за
                                                      нехватки данных)

Ни одного нового расчёта: тот же компас, что и раньше, просто теперь
его слышно. Поиск на рабочем этаже не тронут — разворотник и структура
считаются там же, где считались.

Ожидаемо: мест станет примерно втрое меньше — с 51 до 18 за полтора
года, около десяти в год на H4. Это не потеря, а отсев тех мест, где
трейдер и так отказывал.

В журнале в конце поиска строка: «мимо старшего тренда: N мест».

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_poisk_po_trendu.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "POISK_PO_TRENDU_V1"
NUZHEN = "ISKATEL_SVOY_ETAZH_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "kandidaty.py").exists()


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


YAKOR = '''            _dobrat_kompas(p, okno, symbol, tf, point)   # ISKATEL_SVOY_ETAZH_V1'''

NOV = '''            _dobrat_kompas(p, okno, symbol, tf, point)   # ISKATEL_SVOY_ETAZH_V1
            # POISK_PO_TRENDU_V1: место против старшего тренда — мимо.
            # Трейдер пятнадцать раз подряд отказывал словами «это
            # против направления», и был прав: 57% точек смотрели
            # против дневного Аллигатора. Канон: не торговать
            # разворотный бар против тренда в сильном тренде. Котин:
            # «интересует, куда направлен ДНЕВНОЙ Аллигатор».
            # Старшего этажа нет — место годится: из-за нехватки данных
            # ничего не отсекаем.
            _komp = p.get("компас")
            if _komp in ("BULL", "BEAR") and _komp != p.get("разворотный"):
                _mimo_trenda += 1
                p = None'''

YAKOR2 = '''        p = _priznaki(okno, symbol, tf, point)'''
NOV2 = '''        p = _priznaki(okno, symbol, tf, point)
        _bylo_mesto = bool(p)   # POISK_PO_TRENDU_V1'''

# счётчик и итоговая строка
YAKOR3 = '''def iskat('''
NOV3 = '''def iskat('''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "kandidaty.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_iskatel_na_svoyom_etazhe.py")
        return 1
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
        return 1

    novyy = t.replace(YAKOR, NOV, 1)

    # счётчик — рядом с тем, что считает промахи рамки
    schet = "    mimo = 0                       # OKNO_ISKATELYA_V1: прошли мимо рамки"
    if novyy.count(schet) != 1:
        print("✗ не нашёл, где объявлен счётчик рамки — останавливаюсь")
        return 1
    novyy = novyy.replace(
        schet, schet + "\n    _mimo_trenda = 0               # POISK_PO_TRENDU_V1", 1)

    # итоговая строка — перед блоком, который говорит про рамку
    pech = "    if mimo and govorit:"
    if novyy.count(pech) != 1:
        print("✗ не нашёл блок печати про рамку — останавливаюсь")
        return 1
    novyy = novyy.replace(
        pech,
        '    # POISK_PO_TRENDU_V1: отсев по старшей воде тоже вслух.\n'
        '    if _mimo_trenda:\n'
        '        _skazat = govorit or print\n'
        '        _skazat(f"[ИСКАТЕЛЬ] мимо старшего тренда: {_mimo_trenda} "\n'
        '                f"мест — там большая вода против")\n'
        + pech, 1)

    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_potrendu_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ искатель смотрит на старший тренд (копия: {bak.name})")
    print("\nМест станет примерно втрое меньше — и это не потеря, а отсев")
    print("тех, где трейдер и так отказывал: «против направления».")
    print("\nВ журнале появится: «[ИСКАТЕЛЬ] мимо старшего тренда: N мест».")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
