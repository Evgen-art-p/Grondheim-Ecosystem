# -*- coding: utf-8 -*-
# pochinit_sverki.py — сверки метки и дивера перестают падать.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python pochinit_sverki.py
#
# ═══ ЧТО СЛОМАЛОСЬ ═══
#
# Ошибка Брата, и простая. Внутри руки приказа этаж зовётся
# rabochiy_etazh, а в обеих сверках было написано timeframe. Имя
# наугад, не проверено.
#
# В прогоне 17.09 из-за этого обе проверки падали на первой строке:
#
#     [МЕТКА] сверить не вышло (name 'timeframe' is not defined)
#     [ДИВЕР] посчитать не вышло (name 'timeframe' is not defined)
#
# Девять входов — и ни одной сверки. Ради них всё и строилось.
#
# Упали мягко, прогону не помешали: «не беда» и дальше. Но и пользы
# не принесли никакой.
#
# ═══ ЧТО ДЕЛАЕМ ═══
#
# Меняем имя на правильное в обоих местах. Больше ничего.
#
# БЕЗОПАСНО. Проверяет ast.parse. Рядом кладёт копию.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "POCHINIT_SVERKI_V1"

STAROE_1 = (
    '                _chey = f"{symbol} {timeframe}".strip()\n'
)
NOVOE_1 = (
    '                # POCHINIT_SVERKI_V1: внутри руки этаж зовётся\n'
    '                # rabochiy_etazh. Стояло чужое имя, взятое\n'
    '                # наугад, и сверка падала на первой же строке.\n'
    '                _chey = f"{symbol} {rabochiy_etazh}".strip()\n'
)

STAROE_2 = (
    '                _d = _sd.poschitat(symbol, timeframe, napravlenie)\n'
)
NOVOE_2 = (
    '                # POCHINIT_SVERKI_V1: то же чужое имя, та же беда.\n'
    '                _d = _sd.poschitat(symbol, rabochiy_etazh, napravlenie)\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    prosto = KOREN / "Биржа" / "ruki_treydera.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("ruki_treydera.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/ruki_treydera.py — запускай из корня репо")
        return 1

    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("· уже сделано")
        return 0

    pravki = [(STAROE_1, NOVOE_1), (STAROE_2, NOVOE_2)]
    for nomer, (staroe, _) in enumerate(pravki, 1):
        if tekst.count(staroe) != 1:
            print(f"✗ правка {nomer}: нашёл {tekst.count(staroe)} мест "
                  f"вместо одного. Ничего не тронул.")
            return 1

    novyy = tekst
    for staroe, novoe in pravki:
        novyy = novyy.replace(staroe, novoe, 1)

    # сторож: чужого имени не должно остаться ни в метке, ни в дивере
    _hvost = novyy.split("def _otdat")[-1][:6000]
    _plohо = "time" + "frame"
    if _plohо in _hvost:
        print(f"✗ в руке осталось {_plohо} — не пишу, покажи Брату.")
        return 1

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno})")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_sverki")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ сверки починены:")
    print("    · этаж зовётся rabochiy_etazh — и в метке, и в дивере")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("Теперь в логе должны появиться настоящие строчки:")
    print("    [МЕТКА] ✓ / ✗ / ∅")
    print("    [ДИВЕР] ✓ / ✗ / ?")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
