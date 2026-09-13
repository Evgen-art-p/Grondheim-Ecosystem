# -*- coding: utf-8 -*-
# pochinit_ves_putey.py — чинит «репозиторий — не смотрится» в окне
# ЧИСТКА у Брата.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папками ГОРОД/ и Брат/).
# Запуск из PowerShell, из корня:   python pochinit_ves_putey.py
#
# Найдено 12.09 на живом скриншоте: разведка «репозиторий» отдаёт
# ошибку "argument should be a str or an os.PathLike object... not
# 'tuple'". Причина — в ГОРОД/chistka.py функция _ves_putey() у трёх
# разведок (бэкапы_цеха, атлас) получает список ГОЛЫХ путей, а у
# разведки «репозиторий» — список пар (путь, причина), как их и
# возвращают все sobrat_* из uborshchik.py. _ves_putey() пыталась
# сделать Path() прямо из пары — вот и падение.
#
# Раньше это молчало, потому что группы репозитория обычно были
# пустыми (нечего было взвешивать). Как только в них появилось
# что-то реальное — вскрылось.
#
# Правка одна: _ves_putey() сама разворачивает пару, если её дали,
# и работает как раньше, если дали голый путь. Чинит все три места
# разом, ничего не ломая.
#
# Ничего не удаляет. Кладёт рядом копию chistka.py.bak_ves_putey.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "ГОРОД" / "chistka.py"

BYLO = (
    "def _ves_putey(puti) -> tuple:\n"
    "    fajlov = bajt = 0\n"
    "    for p in puti:\n"
    "        p = Path(p)\n"
)

STALO = (
    "def _ves_putey(puti) -> tuple:\n"
    "    fajlov = bajt = 0\n"
    "    for p in puti:\n"
    "        # POCHINIT_VES_PUTEY_V1: разведка репозитория отдаёт\n"
    "        # пары (путь, причина) — как их и возвращают sobrat_* из\n"
    "        # uborshchik.py. Голый путь тоже допустим — так его дают\n"
    "        # бэкапы цеха и атлас. Разворачиваем пару, если она пара.\n"
    "        if isinstance(p, (tuple, list)):\n"
    "            p = p[0]\n"
    "        p = Path(p)\n"
)


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")

    if BYLO in tekst:
        tekst = tekst.replace(BYLO, STALO, 1)
        kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_ves_putey")
        if not kopiya.exists():
            shutil.copy2(FAYL, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        FAYL.write_text(tekst, encoding="utf-8")
        print("✓ chistka.py: разведка «репозиторий» больше не падает "
              "на парах (путь, причина)")
        print()
        print("Перезапусти Кабинет (main.py), чтобы правка подхватилась —")
        print("процесс уже держит старый chistka.py в памяти.")
        return 0
    elif "POCHINIT_VES_PUTEY_V1" in tekst:
        print("· уже починено")
        return 0
    else:
        print("✗ не нашёл ожидаемое место — chistka.py мог измениться, "
              "скажи Брату, поправим по месту")
        return 1


if __name__ == "__main__":
    sys.exit(main())
