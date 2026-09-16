# -*- coding: utf-8 -*-
# kadr_pryamo_v_pamyat.py — прогон кладёт кадр в общую память сам.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python kadr_pryamo_v_pamyat.py
#
# ВАЖНО: идёт после kadr_bez_okna.py и kadr_ne_teryaetsya.py.
#
# ═══ ОТЧЕГО БОЛЕЛО ═══
#
# Лог прогона 16.09 показал: кадры рисуются исправно, по контрольной
# метке их за два пробуда шесть штук. Ни одной жалобы. А в панели
# висел кадр из ПРОШЛОГО прогона, двухмесячной давности.
#
# Значит теряются не при рисовании, а по дороге в панель.
#
# Дорога такая: прогон зовёт pokazat_kadr. Но это функция ТОГО окна,
# в котором прогон начинался. Шеф перезагружал страницу, окно стало
# другое, а прогон продолжает звать старое. И делает это молча: у
# pokazat_kadr несколько тихих выходов, любой из них уводит кадр в
# никуда, не сказав ни слова.
#
# ═══ ЧТО СТАВИМ ═══
#
# Убираем зависимость от окна вовсе. Прогон нарисовал кадр — и СРАЗУ
# кладёт его в общую память, до всякого показа. Дальше любая живая
# вкладка подбирает его своим таймером за секунду.
#
# Теперь неважно, сколько раз перезагружалась страница и что там
# случилось внутри pokazat_kadr: путь кадра в панель больше не идёт
# через окно, которого может уже не быть.
#
# Показ при этом не убираем — окно живо, кадр появится сразу, без
# ожидания секунды. Просто он больше не единственная дорога.
#
# Плюс одна строчка в лог: какой кадр отдан в панель. Чтобы в
# следующий раз не гадать, а смотреть.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт ui_torg.py.bak_pryamo.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "KADR_PRYAMO_V_PAMYAT_V1"
NUZHEN = "KADR_NE_TERYAETSYA_V1"

STAROE = (
    '                except Exception as _ek:\n'
    '                    print(f"[ПРОГОН] кадр не нарисовался: {_ek}")\n'
    '                try:\n'
    '                    await pokazat_kadr(_kadr)\n'
    '                except Exception:\n'
    '                    pass\n'
)

NOVOE = (
    '                except Exception as _ek:\n'
    '                    print(f"[ПРОГОН] кадр не нарисовался: {_ek}")\n'
    '                # KADR_PRYAMO_V_PAMYAT_V1: кладём кадр в общую\n'
    '                # память СРАЗУ, до всякого показа. pokazat_kadr —\n'
    '                # функция того окна, где прогон начинался; после\n'
    '                # перезагрузки страницы она уводит кадр в никуда,\n'
    '                # и делает это молча. Общая память ни от какого\n'
    '                # окна не зависит: любая живая вкладка подберёт\n'
    '                # кадр своим таймером за секунду.\n'
    '                if _kadr:\n'
    '                    try:\n'
    '                        _KADR_NA_VIDU["put"] = str(_kadr)\n'
    '                        _KADR_NA_VIDU["podpis"] = f"{_sym} · {_tf}"\n'
    '                        _KADR_NA_VIDU["schet"] += 1\n'
    '                        print(f"[КАДР] в панель: "\n'
    '                              f"{Path(_kadr).name}")\n'
    '                    except Exception as _ep:\n'
    '                        print(f"[КАДР] в панель не лёг: {_ep}")\n'
    '                try:\n'
    '                    await pokazat_kadr(_kadr)\n'
    '                except Exception:\n'
    '                    pass\n'
)


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет кабинет Биржи сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "ui_torg.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("ui_torg.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько:")
        for nomer, put in enumerate(nashlos, 1):
            print(f"  {nomer}. {put}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/ui_torg.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if NUZHEN not in tekst:
        print("✗ сперва накати kadr_ne_teryaetsya.py — этот идёт следом.")
        print("  Ничего не тронул.")
        return 1

    if tekst.count(STAROE) != 1:
        print(f"✗ нашёл {tekst.count(STAROE)} мест вместо одного —")
        print("  кабинет мог измениться. Ничего не тронул.")
        print("  Скажи Брату, поправим по месту.")
        return 1

    novyy = tekst.replace(STAROE, NOVOE, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_pryamo")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ кадр идёт в панель напрямую:")
    print("    · прогон кладёт кадр в общую память сразу, как нарисовал")
    print("    · дорога больше не зависит от окна и перезагрузок страницы")
    print("    · в лог добавлена строчка «[КАДР] в панель: ...»")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("В логе на каждом пробуде должна появиться строчка «в панель»,")
    print("а в углу кадра — новый жёлтый код. Сверь их с датой на столе.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
