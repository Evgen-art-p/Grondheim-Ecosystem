# -*- coding: utf-8 -*-
# rasshirit_uborshchika.py — снимает слишком узкий фильтр имён в
# uborshchik.py, из-за которого он проходил мимо большинства патчей.
#
# Кладётся в КОРЕНЬ репозитория (рядом с uborshchik.py).
# Запуск из PowerShell, из корня:   python rasshirit_uborshchika.py
#
# Найдено 12.09: sobrat_patchi() смотрел метку MARKER только у файлов,
# чьё имя начинается с "patch_" или "postavit_". В корне 98 файлов
# честно несут MARKER, и 72 из них уборщик даже не открывал — не из-за
# отсутствия метки, а из-за имени. Патч отработал или нет, решала сама
# метка (ищется по всему репо) — фильтр по имени не добавлял
# безопасности, только слепоту.
#
# Правка убирает фильтр по имени. Проверка по метке (MARKER = "...",
# ищется в остальных файлах репо) остаётся ровно той же — ничего не
# станет менее осторожным, уборщик просто перестанет закрывать глаза.
#
# Ничего не удаляет. Кладёт рядом копию uborshchik.py.bak_shire.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "uborshchik.py"

BYLO = (
    '    for p in sorted(KOREN.glob("*.py")):\n'
    '        if not p.name.startswith(("patch_", "postavit_")):\n'
    '            continue\n'
    '        if p.name in NEPRIKASAEMYE:\n'
    '            continue\n'
)

STALO = (
    '    # RASSHIRIT_UBORSHCHIKA_V1: раньше здесь стояла проверка имени\n'
    '    # ("patch_"/"postavit_") — фильтр по имени не добавлял\n'
    '    # безопасности (её и так даёт метка ниже), только прятал патчи\n'
    '    # с другими именами от проверки вовсе.\n'
    '    for p in sorted(KOREN.glob("*.py")):\n'
    '        if p.name in NEPRIKASAEMYE:\n'
    '            continue\n'
)


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")

    if BYLO in tekst:
        tekst = tekst.replace(BYLO, STALO, 1)
        kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_shire")
        if not kopiya.exists():
            shutil.copy2(FAYL, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        FAYL.write_text(tekst, encoding="utf-8")
        print("✓ uborshchik.py теперь смотрит метку у ЛЮБОГО .py в корне, "
              "не только patch_/postavit_")
        return 0
    elif "RASSHIRIT_UBORSHCHIKA_V1" in tekst:
        print("· уже расширено")
        return 0
    else:
        print("✗ не нашёл ожидаемое место — uborshchik.py мог измениться, "
              "скажи Брату, поправим по месту")
        return 1


if __name__ == "__main__":
    sys.exit(main())
