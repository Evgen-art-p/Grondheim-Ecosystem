# -*- coding: utf-8 -*-
# ao_gorby_i_yamy_A06.py — в описании кадра AO были только горбы,
# ямы пропущены.
#
# Кладётся в КОРЕНЬ репозитория. Запуск из PowerShell, из корня:
#   python ao_gorby_i_yamy_A06.py
#
# Найдено 15.09: строка «ЧТО ТЫ ВИДИШЬ НА КАДРЕ» → «Нижняя полоса —
# AO» говорила только про горбы (столбики над нулём). А бычий дивер
# (падение выдыхается — то, что нужно для LONG) ищется по ЯМАМ, под
# нулём. Раз в описании их нет — трейдер может решить, что под нулём
# смотреть нечего, хотя AO.md прямо говорит «горб или яма».
#
# Ничего не удаляет. Кладёт рядом копию промпт.md.bak_ao_yamy.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
PROMPT_PATH = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
               / "слоты" / "A06" / "промпт.md")

BYLO = (
    "**Нижняя полоса — AO.** Столбики над нулём и под нулём. Их гребни и\n"
    "есть горбы: смотри не на цифру, а на то, какой горб выше прошлого и\n"
    "куда в это время шла цена.\n"
)

STALO = (
    "**Нижняя полоса — AO.** Столбики над нулём и под нулём. Гребни над\n"
    "нулём — горбы, гребни под нулём — ямы. Смотри не на цифру, а на то,\n"
    "какой горб или яма выше/мельче прошлого и куда в это время шла\n"
    "цена.\n"
)


def main() -> int:
    if not PROMPT_PATH.exists():
        print(f"✗ нет файла {PROMPT_PATH} — запускать из корня репозитория")
        return 1

    tekst = PROMPT_PATH.read_text(encoding="utf-8")

    if "гребни под нулём — ямы" in tekst:
        print("· уже сделано")
        return 0
    if BYLO not in tekst:
        print("✗ не нашёл ожидаемое место — промпт мог измениться, "
              "скажи Брату, поправим по месту")
        return 1

    tekst = tekst.replace(BYLO, STALO, 1)
    kopiya = PROMPT_PATH.with_suffix(PROMPT_PATH.suffix + ".bak_ao_yamy")
    if not kopiya.exists():
        shutil.copy2(PROMPT_PATH, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    PROMPT_PATH.write_text(tekst, encoding="utf-8")
    print("✓ AO на кадре: горбы и ямы названы симметрично")
    print()
    print("Перезапусти Кабинет (main.py) — правка не подхватится на лету.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
