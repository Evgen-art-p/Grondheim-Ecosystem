# -*- coding: utf-8 -*-
# snyat_romby_ao.py — снимает ромбы (метки провалов и горбов) с кадра AO.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python snyat_romby_ao.py
#
# ЗАЧЕМ. Решение Шефа 16.09: ромбы отвергнуты. Обе версии
# (METKI_PROVALOV_AO_V1 и METKI_PROVALOV_AO_V2) резали гистограмму по
# пересечению нуля и метили крайний столбик каждого куска. Выходило
# механическое чередование ям и вершин — не то, что видит глаз. Прибор
# нельзя брать в отрыве от цены, фракталов и Аллигатора.
#
# ЧТО ДЕЛАЕТ. Убирает из Биржа/grafik.py ровно три вещи:
#     1. цвет метки C_AO_METKA
#     2. весь блок рисования ромбов в полосе AO
#     3. два маркера METKI_PROVALOV_AO_* внизу файла
# Больше ничего. Остальное на кадре остаётся как было: тёмный фон,
# контрольная метка в углу, разворотники, приседающие, фракталы,
# Аллигатор.
#
# БЕЗОПАСНО. Сначала собирает новый текст в памяти и проверяет, что это
# рабочий Python (ast.parse). Не проверилось — не пишет вовсе. Рядом
# кладёт копию grafik.py.bak_bez_rombov.
# Запускать можно сколько угодно раз: второй запуск скажет «уже сделано».

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent

# Приметы, по которым режем. Взяты дословно из живого файла.
NACHALO_CVETA = "# METKI_PROVALOV_AO_V1: метка на дне провала"
KONEC_CVETA = 'C_AO_METKA = "#ffd24a"'
NACHALO_BLOKA = "# METKI_PROVALOV_AO_V1 (слово Шефа 15.09)"
KONEC_BLOKA = "# SVECHA_VIDNA_V1: нулевая линия"
MARKERY = (
    "# METKI_PROVALOV_AO_V1 - marker",
    "# METKI_PROVALOV_AO_V2 - marker",
)


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti_grafik():
    """Ищет рисовалку сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "grafik.py"
    if prosto.exists():
        return prosto

    myosor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", "backup")
    nashlos = [p for p in KOREN.rglob("grafik.py")
               if not any(m in str(p) for m in myosor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько рисовалок:")
        for nomer, put in enumerate(nashlos, 1):
            print(f"  {nomer}. {put}")
        otvet = input("Какую правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def srezat_ot_do(tekst, primeta_start, primeta_stop):
    """Режет целыми строками: от строки с одной приметой до строки с другой
    (сама строка-стоп остаётся на месте)."""
    i = tekst.find(primeta_start)
    if i < 0:
        return tekst, False
    j = tekst.find(primeta_stop, i)
    if j < 0:
        return tekst, False
    nachalo = tekst.rfind("\n", 0, i) + 1
    konec = tekst.rfind("\n", 0, j) + 1
    return tekst[:nachalo] + tekst[konec:], True


def main():
    put = nayti_grafik()
    if put is None:
        print("✗ не нашёл Биржа/grafik.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if "METKI_PROVALOV_AO" not in tekst:
        print("· уже сделано — ромбов в рисовалке нет")
        return 0

    novyy = tekst
    sdelano = []

    # 1. Цвет метки — от строки комментария до строки с самим цветом.
    i = novyy.find(NACHALO_CVETA)
    j = novyy.find(KONEC_CVETA, i) if i >= 0 else -1
    if i >= 0 and j >= 0:
        nachalo = novyy.rfind("\n", 0, i) + 1
        konec = novyy.find("\n", j) + 1
        novyy = novyy[:nachalo] + novyy[konec:]
        sdelano.append("убран цвет метки C_AO_METKA")

    # 2. Сам блок рисования ромбов внутри полосы AO.
    novyy, vyshlo = srezat_ot_do(novyy, NACHALO_BLOKA, KONEC_BLOKA)
    if vyshlo:
        sdelano.append("убран блок рисования ромбов")

    # 3. Маркеры внизу файла.
    stroki = [s for s in novyy.splitlines(keepends=True)
              if s.strip() not in MARKERY]
    if len(stroki) != len(novyy.splitlines(keepends=True)):
        sdelano.append("убраны маркеры METKI_PROVALOV_AO_*")
    novyy = "".join(stroki)

    if not sdelano:
        print("✗ приметы не нашлись — рисовалка могла измениться.")
        print("  Ничего не тронул. Покажи grafik.py Брату, поправим по месту.")
        return 1

    if "METKI_PROVALOV_AO" in novyy or "C_AO_METKA" in novyy:
        print("✗ что-то от ромбов осталось в тексте. Ничего не пишу.")
        return 1

    # Проверка, что файл после правки живой.
    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_bez_rombov")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ ромбы сняты с кадра AO:")
    for chto in sdelano:
        print(f"    · {chto}")
    print()
    print("Перезапусти Кабинет (main.py) — рисовалка перечитывается при старте.")
    print("Файлы Биржа/grafik.py.bak_metki_ao и .bak_metki_ao2 больше не нужны,")
    print("можешь их удалить или убрать в архив.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
