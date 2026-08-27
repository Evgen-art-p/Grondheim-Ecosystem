# -*- coding: utf-8 -*-
"""
pochinit_slovo_zhdu.py · MARKER: SLOVO_ZHDU_V1

ЧТО ПОКАЗАЛ ПРОГОН (20.08, GBPUSD H4, 15 мест)
──────────────────────────────────────────────
Нина сказала «НАБЛЮДАЮ» дважды. А слово «жду» произнесла почти везде:

    «Я жду, пока рынок покажет более ясную структуру»
    «Жду формирования первой волны и последующего отката к ней»
    «нужно дождаться формирования первой волны и её отката»

То есть ждёт она постоянно — а отмечает это через раз. Инструмент у неё
в руках, но он не связан в её голове с тем словом, которое она и так
говорит.

Из-за этого второе событие — конец первой волны — в прогоне не поймалось
ни разу: город идёт за трейдером только там, где он взял на карандаш.
Не взял — ушли к следующему месту, и волна прошла мимо, даже если
случилась.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Одна строка в бумагу всех трёх трейдеров: «жду» и «НАБЛЮДАЮ» — это одно
и то же, только второе слышит город. Пишешь, что ждёшь, — скажи
НАБЛЮДАЮ, иначе город уйдёт и твоего момента ты не увидишь.

Это про инструмент, а не про решение. Ждать или не ждать, входить или
пасовать — по-прежнему целиком его дело. Мы только объясняем, какой
кнопкой пользоваться.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ наблюдения — патч это проверит.
Запуск: py pochinit_slovo_zhdu.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "SLOVO_ZHDU_V1"
NUZHEN = "NABLYUDENIE_V1"
SUHO = "--suho" in sys.argv

SLOTY = ("A06", "A07", "A08")


def _eto_koren(p: Path) -> bool:
    return (p / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
            / "слоты").is_dir()


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


YAKOR = ('        "Вошёл — наблюдение снимется само.\\n"')

NOV = (
    '        "Вошёл — наблюдение снимется само.\\n"\n'
    '        # SLOVO_ZHDU_V1: в прогоне трейдер говорил «жду» почти\n'
    '        # везде, а отмечал наблюдение через раз — и город уходил,\n'
    '        # не дождавшись с ним его же момента.\n'
    '        "ВАЖНО про это слово: «жду», «дождусь», «пока рано» и '
    '«НАБЛЮДАЮ» — про одно и то же, но услышать город может только '
    'последнее. Если в твоём ответе есть «жду» — значит скажи и '
    'НАБЛЮДАЮ, иначе город уйдёт к другому месту, а твой момент '
    'придёт без тебя.\\n"'
)


def _pravit(f: Path, imya: str) -> bool:
    t = f.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"· {imya}: маркер уже стоит — пропускаю")
        return True
    if t.count(YAKOR) != 1:
        print(f"✗ {imya}: якорь найден {t.count(YAKOR)} раз — жду один")
        return False
    novyy = t.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ {imya}: после правки не разбирается — {e}")
        return False
    if SUHO:
        print(f"· {imya}: правка готова (сухой прогон)")
        return True
    bak = f.with_suffix(f".py.bak_zhdu_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ {imya}: НЕ компилируется ({e}) — откатил из {bak.name}")
        return False
    print(f"✓ {imya}: сказано про слово (копия: {bak.name})")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    sloty = koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

    proverka = sloty / "A06" / "мозг.py"
    if proverka.exists() and NUZHEN not in proverka.read_text(
            encoding="utf-8"):
        print("✗ Сперва накати postavit_nablyudenie.py — без него у")
        print("  трейдера нет самого слова НАБЛЮДАЮ.")
        return 1

    for slot in SLOTY:
        mozg = sloty / slot / "мозг.py"
        if not mozg.exists():
            print(f"· {slot}: мозга нет — пропускаю")
            continue
        if not _pravit(mozg, f"{slot}/мозг.py"):
            print(f"\n⚠️  {slot} не поправлен. Остальное цело, копии рядом.")
            return 1

    if SUHO:
        return 0
    print("\nЧего ждать: строк «👁 взял на карандаш» станет больше, и")
    print("город будет доходить с трейдером до конца первой волны, а не")
    print("уходить к следующему месту, пока тот ждёт.")
    print("\nЕсли он и после этого будет говорить «жду» молча — значит")
    print("дело не в словах, и придумаем другое.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
