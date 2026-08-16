# -*- coding: utf-8 -*-
"""
postavit_okno_iskatelya.py · MARKER: OKNO_ISKATELYA_V1

ЗАЧЕМ
─────
Первый прогон: 30 мест, 30 отказов, ни одного входа. Разбор показал,
что дело не в трейдерах — их звали не туда.

Длины волн у найденных мест были такие:

    22, 25, 32, 36, 37, 38, 41, 47, 55, 57, 62, 68, 75, 79, 82, 92,
    92, 93, 93, 94, 96, 101, 101, 103, 110, 114, 115, 121, 142, 189

В окно 100-140 попало 7 из 30. На остальных масштаб не тот: либо
мелочь в 22-40 баров, либо великан на 189 — AO под такое не посчитан,
и трейдер честно отвечает «не вижу». Деньги на модель уходили на
заведомо нечитаемую картинку.

ПОСЧИТАНО, А НЕ ПРИДУМАНО
─────────────────────────
Прогнал искатель по 3000 барам H4 (около двух лет), без отбора:

    кандидатов всего:  79
    в окне 100-140:    31 (39%)
    в рамке  80-180:   58 (73%)
    короче 70:         10 · длиннее 200: 2

Значит фильтр поток не осушит: 31 место за два года на одном
инструменте — прогон из десяти набирается спокойно.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Искатель зовёт трейдера ТОЛЬКО там, где волна укладывается в окно.
Рамка задаётся одной строкой и по умолчанию равна канону Шефа —
100-140 баров. Слова Шефа: «раскладываешь эту волну на 100-140, она
может быть немного меньше или больше, но точность не главное» —
поэтому рамка ЯВНАЯ и меняется в одном месте, а не зашита по коду.

Отсеянные не пропадают молча: искатель считает их и говорит, сколько
мест прошло мимо и почему. Это важно — иначе однажды окажется, что
фильтр съел всё, а мы будем гадать.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не трогает решения трейдеров и не подбирает им этаж. Только не зовёт
туда, где смотреть нечего.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_okno_iskatelya.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "OKNO_ISKATELYA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "kandidaty.py").exists() and (p / "main.py").exists()


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


ST_OKNO = '''OKNO_RASCHYOTA = 300      # сколько баров нужно математике для расчёта'''

NOV_OKNO = '''OKNO_RASCHYOTA = 300      # сколько баров нужно математике для расчёта

# ── OKNO_ISKATELYA_V1: на каком масштабе вообще стоит звать ──
# Слова Шефа: «раскладываешь эту волну на 100-140, она может быть
# немного меньше или больше, но точность не главное». Волна короче —
# разворотный бар не разглядеть; длиннее — AO посчитан не под неё, и
# дивергенция говорит о другой волне.
#
# Считано, а не придумано: на 3000 барах H4 (≈2 года) кандидатов 79,
# из них в окне 100-140 — 31 (39%), в рамке 80-180 — 58 (73%).
# Поток фильтр не осушает.
#
# Рамка здесь ЯВНАЯ и меняется одной строкой — если решишь, что она
# узка, поправь тут, а не по коду.
OKNO_VOLNY = (100, 140)


def v_okne(dlina) -> bool:
    """Ложится ли волна в рамку. Длина неизвестна — не наше дело
    решать за трейдера: считаем, что не ложится, и не зовём."""
    if not dlina:
        return False
    return OKNO_VOLNY[0] <= dlina <= OKNO_VOLNY[1]'''

ST_ISKAT = '''def iskat(symbol: str, tf: str, do_momenta: str = "", skolko: int = 10,
          predel_barov: int = 4000, otstup: int = 12, govorit=None):'''

NOV_ISKAT = '''def iskat(symbol: str, tf: str, do_momenta: str = "", skolko: int = 10,
          predel_barov: int = 4000, otstup: int = 12, govorit=None,
          tolko_v_okne: bool = True):'''

ST_FILTR = '''        p = _priznaki(okno, symbol, tf, point)
        if p:
            posledniy_i = i
            nayden.append(p)'''

NOV_FILTR = '''        p = _priznaki(okno, symbol, tf, point)
        if p:
            posledniy_i = i
            # OKNO_ISKATELYA_V1: зовём только там, где масштаб годится.
            # Мимо — считаем и идём дальше: место не потеряно, просто
            # смотреть на нём нечего, и платить за это незачем.
            if tolko_v_okne and not v_okne(p.get("длина_волны")):
                mimo += 1
                continue
            nayden.append(p)'''

ST_SCHYOT = '''    nayden = []
    posledniy_i = None'''
NOV_SCHYOT = '''    nayden = []
    mimo = 0                       # OKNO_ISKATELYA_V1: прошли мимо рамки
    posledniy_i = None'''

ST_VOZVRAT = '''            if len(nayden) >= skolko:
                break
    return nayden'''
NOV_VOZVRAT = '''            if len(nayden) >= skolko:
                break
    # OKNO_ISKATELYA_V1: отсеянные не пропадают молча — иначе однажды
    # фильтр съест всё, а мы будем гадать, почему пусто.
    if mimo and govorit:
        govorit(f"[ИСКАТЕЛЬ] мимо рамки {OKNO_VOLNY[0]}-{OKNO_VOLNY[1]} "
                f"баров: {mimo} мест — там масштаб не тот")
    elif mimo:
        print(f"[ИСКАТЕЛЬ] мимо рамки {OKNO_VOLNY[0]}-{OKNO_VOLNY[1]}: "
              f"{mimo} мест")
    return nayden'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    kand = koren / "Биржа" / "kandidaty.py"
    t = kand.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [("окно", ST_OKNO, NOV_OKNO),
            ("подпись iskat", ST_ISKAT, NOV_ISKAT),
            ("счётчик", ST_SCHYOT, NOV_SCHYOT),
            ("фильтр", ST_FILTR, NOV_FILTR),
            ("возврат", ST_VOZVRAT, NOV_VOZVRAT)]
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

    bak = kand.with_suffix(f".py.bak_okno_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(kand, bak)
    kand.write_text(novyy, encoding="utf-8")
    print(f"✓ рамка встала (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(kand), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь искатель зовёт только там, где волна 100-140 баров.")
    print("Отсеянные считаются и видны строкой [ИСКАТЕЛЬ] мимо рамки.")
    print("Рамка — одна строка OKNO_VOLNY в Биржа/kandidaty.py.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
