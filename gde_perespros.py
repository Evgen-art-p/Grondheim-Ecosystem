# -*- coding: utf-8 -*-
# gde_perespros.py — находит файл, в котором живёт переспрос.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python gde_perespros.py
#
# ЗАЧЕМ. В логе прогона есть строчки про переспрос и про то, что
# слово приказом не считается. В репозитории на GitHub этих строк
# нет — значит код есть на диске, но не уехал наверх, и Брат его
# не видит.
#
# Этот скрипт НИЧЕГО не меняет. Только смотрит и говорит, в каком
# файле что нашлось. Дальше Шеф перетащит найденный файл в чат.

import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent

# Приметы — куски строк прямо из лога.
PRIMETY = [
    "ПЕРЕСПРОС",
    "Слово приказом не считается",
    "приказ с прошлого бара",
    "За столом",
    "решения нет",
]

MUSOR = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", "site-packages",
         ".git", "__pycache__", "backup")


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def main():
    print(f"Смотрю в {KOREN}")
    print("Ищу, где живёт переспрос…\n")

    nashlos = {}
    smotreno = 0

    for put in KOREN.rglob("*.py"):
        if any(m in str(put) for m in MUSOR):
            continue
        if ".bak" in put.name:
            continue
        try:
            tekst = put.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        smotreno += 1
        for primeta in PRIMETY:
            if primeta in tekst:
                nashlos.setdefault(put, []).append(primeta)

    print(f"просмотрено файлов: {smotreno}\n")

    if not nashlos:
        print("✗ ничего не нашлось.")
        print("  Похоже, запущено не из корня репозитория —")
        print("  положи этот файл рядом с main.py и запусти оттуда.")
        return 1

    # Сперва те, где примет больше — они и есть нужные.
    poryadok = sorted(nashlos.items(), key=lambda p: -len(p[1]))

    print("Нашёл вот что:\n")
    for put, primety in poryadok:
        try:
            otn = put.relative_to(KOREN)
        except Exception:
            otn = put
        print(f"  {otn}")
        print(f"      примет: {len(primety)} — {', '.join(primety)}")
        print()

    glavnyy = poryadok[0][0]
    try:
        glavnyy_otn = glavnyy.relative_to(KOREN)
    except Exception:
        glavnyy_otn = glavnyy

    print("─" * 60)
    print("ГЛАВНЫЙ ПОДОЗРЕВАЕМЫЙ:")
    print(f"    {glavnyy_otn}")
    print()
    print("Перетащи этот файл в чат Брату — он посмотрит и скажет,")
    print("почему Илья пишет решение словами вместо руки.")
    print("Если файлов в списке несколько — тащи первые два.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
