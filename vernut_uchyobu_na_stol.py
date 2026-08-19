# -*- coding: utf-8 -*-
"""
vernut_uchyobu_na_stol.py · MARKER: UCHYOBA_NA_STOLE_V1

ЧТО Я СЛОМАЛ ВЧЕРА
──────────────────
Разделил память надвое — работа и жизнь, — и учёба попала в «не
работу»: по Закону Слоёв `учёба → archive`, а рабочими считались
только «работа» и «факт». За столом трейдер перестал поднимать даже
то, что разбирал с Ректором.

Формально верно: разбор главы — не сделка. По сути неверно, и Шеф
сказал прямо:

    «Академия свои плоды должна принести изначально. Трейдер учится,
    он имеет знания, можно и практику-насмотренность погонять — для
    этого она и создавалась. Без знаний опыта не получишь.»

Делить надо было НАТРОЕ, а не надвое:

    ПРАКТИКА (работа, факт)    — что было со мной за столом
    УЧЁБА    (учёба)           — что я разбирал(а) и понял(а)
    ЖИЗНЬ    (общение, дом)    — разговоры, холст, знакомство

За столом поднимается практика И учёба. Разговоры про холст остаются
дома — им за столом делать нечего.

ЗАЧЕМ ЭТО ВАЖНО ИМЕННО СЕЙЧАС
─────────────────────────────
Практики у трейдеров ноль: ни одна сделка ещё не закрылась. Значит
единственное, на что им опереться, — учёба. Отрезав её, я оставил их
вообще без опоры, а потом удивлялся ответам.

ЧТО ЕЩЁ ВИДНО ПО ДОРОГЕ (не чиню, чтобы знал)
─────────────────────────────────────────────
Полка знаний слота — 60 КБ, ОДНА И ТА ЖЕ у всех троих: общий учебник.
А личное — 5.8 МБ в доме: сканы глав, чаты с Ректором, разборы.
На работу не едет ничего из личного, и картинок Академии на столе нет
ни одной, хотя учили именно ими. Это следующий шаг, отдельный.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py vernut_uchyobu_na_stol.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "UCHYOBA_NA_STOLE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "жители" / "dvizhok.py").exists()
            and (p / "Биржа" / "nositel.py").exists())


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


# ── 1. делим натрое ──
ST_DELENIE = '''RABOCHIE_KONTEKSTY = ("работа", "факт")
ZHIZNENNYE_KONTEKSTY = ("общение", "дом")'''

NOV_DELENIE = '''# UCHYOBA_NA_STOLE_V1: делим НАТРОЕ, а не надвое. Вчера учёба попала
# в «не работу», и за столом трейдер перестал поднимать даже то, что
# разбирал с Ректором. А практики у него ноль — ни одна сделка ещё не
# закрылась. Значит учёба сейчас ЕДИНСТВЕННАЯ его опора, и отрезать
# её было худшим, что можно сделать.
#   «Без знаний опыта не получишь» — слово Шефа 18.08.
PRAKTIKA_KONTEKSTY = ("работа", "факт")
UCHEBNYE_KONTEKSTY = ("учёба", "учеба")
ZHIZNENNYE_KONTEKSTY = ("общение", "дом")

# За столом поднимается практика И учёба. Разговоры про холст остаются
# дома — им за столом делать нечего.
RABOCHIE_KONTEKSTY = PRAKTIKA_KONTEKSTY + UCHEBNYE_KONTEKSTY'''

# ── 2. поиск умеет спрашивать отдельно учёбу и отдельно практику ──
ST_OTBOR = '''                if nuzhno.startswith("работ"):
                    if k not in RABOCHIE_KONTEKSTY:
                        continue
                elif nuzhno.startswith("жизн"):
                    if k not in ZHIZNENNYE_KONTEKSTY:
                        continue'''

NOV_OTBOR = '''                if nuzhno.startswith("работ"):
                    # UCHYOBA_NA_STOLE_V1: работа = практика + учёба
                    if k not in RABOCHIE_KONTEKSTY:
                        continue
                elif nuzhno.startswith("практик"):
                    if k not in PRAKTIKA_KONTEKSTY:
                        continue
                elif nuzhno.startswith("учёб") or nuzhno.startswith("учеб"):
                    if k not in UCHEBNYE_KONTEKSTY:
                        continue
                elif nuzhno.startswith("жизн"):
                    if k not in ZHIZNENNYE_KONTEKSTY:
                        continue'''

# ── 3. в найденном видно, откуда след ──
ST_STROKI = '''        stroki = []
        for _, _, z in naydeno[:limit]:
            ts = str(z.get("ts", ""))[:10]
            stroki.append(f"— [{ts}] {z.get('факт', '')}")'''

NOV_STROKI = '''        stroki = []
        for _, _, z in naydeno[:limit]:
            ts = str(z.get("ts", ""))[:10]
            # UCHYOBA_NA_STOLE_V1: откуда след — чтобы трейдер не
            # путал прожитое с прочитанным. «Я это ПРОБОВАЛ» и «я об
            # этом ЧИТАЛ» — разного веса, и решать ему.
            k = kontekst_zapisi(z)
            otkuda = ""
            if k in UCHEBNYE_KONTEKSTY:
                otkuda = " · учёба"
            elif k in PRAKTIKA_KONTEKSTY:
                otkuda = " · практика"
            stroki.append(f"— [{ts}{otkuda}] {z.get('факт', '')}")'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    dvizhok = koren / "жители" / "dvizhok.py"
    t = dvizhok.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if "PAMYAT_RABOTA_ZHIZN_V1" not in t:
        print("✗ Нет разделения памяти — накати сперва razdelit_pamyat.py")
        return 1

    pary = [("деление", ST_DELENIE, NOV_DELENIE),
            ("отбор", ST_OTBOR, NOV_OTBOR),
            ("строки", ST_STROKI, NOV_STROKI)]
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

    bak = dvizhok.with_suffix(
        f".py.bak_uchyoba_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(dvizhok, bak)
    dvizhok.write_text(novyy, encoding="utf-8")
    print(f"✓ учёба вернулась на стол (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(dvizhok), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь память делится натрое:")
    print("  практика — что было со мной за столом")
    print("  учёба    — что я разбирал(а) с Ректором")
    print("  жизнь    — разговоры, холст, знакомство")
    print("\nЗа столом поднимается практика И учёба, и в каждой найденной")
    print("строке видно, откуда она: «· учёба» или «· практика».")
    print("Трейдер сам решит, что весит больше — прожитое или прочитанное.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
