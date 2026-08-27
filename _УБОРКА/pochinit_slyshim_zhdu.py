# -*- coding: utf-8 -*-
"""
pochinit_slyshim_zhdu.py · MARKER: SLYSHIM_ZHDU_V1

СЛОВО НЕ ПОМОГЛО — ПРОВЕРЕНО
────────────────────────────
Я дописал трейдеру в бумагу: пишешь «жду» — скажи и НАБЛЮДАЮ. Прогон
21.08, пятнадцать мест:

    «Пока что я жду.»
    «Я жду, пока тишина договорит.»
    «Я жду формирования первой волны и отката к ней.»
    «Мой выбор — первый откат к новой волне, поэтому я пока жду.»

Слово «жду» — почти в каждом ответе. Ритуальное НАБЛЮДАЮ — дважды из
пятнадцати. Тринадцать раз город уходил к следующему месту, пока она
ждала.

Я сам сказал: если и после подсказки будет ждать молча — значит дело не
в словах. Так и вышло. Требовать от человека волшебное слово, когда он
говорит обычное, — это наша неудобная кнопка, а не его невнимательность.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Город начинает слышать обычную речь. «Жду», «подожду», «дождусь»,
«пока рано» — то же самое, что НАБЛЮДАЮ, и город остаётся с трейдером.

Ничего не решается за него:
  · вошёл (APPROVED)      → наблюдение снимается, дальше ведёт позиция
  · сказал УХОЖУ          → снимается
  · сказал «жду» в любом виде → город остаётся и считает молча
  · не сказал ничего      → как было: ничего не меняем

Ритуальное НАБЛЮДАЮ остаётся и работает как работало — просто теперь
оно не единственный способ быть услышанным. За чем следит, берём из
той же фразы, где он это сказал.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ наблюдения — патч это проверит.
Запуск: py pochinit_slyshim_zhdu.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "SLYSHIM_ZHDU_V1"
NUZHEN = "NABLYUDENIE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "council.py").exists()


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


YAKOR = '''        if "НАБЛЮДАЮ" in verh:
            za = ""
            for stroka in tekst.splitlines():
                if "НАБЛЮДАЮ" in stroka.upper():
                    za = stroka.split(":", 1)[1] if ":" in stroka else stroka
                    break'''

NOV = '''        # SLYSHIM_ZHDU_V1: слышим обычную речь, а не только ритуал.
        # В прогоне 21.08 трейдер сказал «жду» почти в каждом из
        # пятнадцати ответов, а ритуальное НАБЛЮДАЮ — дважды. Требовать
        # волшебное слово, когда человек говорит обычное, — это наша
        # неудобная кнопка, а не его невнимательность.
        _ZHDU = ("НАБЛЮДАЮ", "ЖДУ", "ЖДАТЬ", "ПОДОЖДУ", "ДОЖДУСЬ",
                 "ПОКА РАНО", "ЖДЁМ", "ЖДЕМ")
        if any(s in verh for s in _ZHDU):
            za = ""
            for stroka in tekst.splitlines():
                _v = stroka.upper()
                if any(s in _v for s in _ZHDU):
                    za = stroka.split(":", 1)[1] if ":" in stroka else stroka
                    break'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "council.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_nablyudenie.py")
        return 1
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
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

    bak = f.with_suffix(f".py.bak_slyshim_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ город слышит «жду» (копия: {bak.name})")
    print("\nПо прошлому прогону: было 2 наблюдения из 15, станет около")
    print("13 — трейдер и так ждал в каждом из них, просто своими словами.")
    print("\nВходов это не прибавит само по себе. Зато город перестанет")
    print("уходить, пока трейдер ждёт, и волна 1 будет доходить чаще.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
