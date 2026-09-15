# -*- coding: utf-8 -*-
# pochinit_knopku_uborki_v2.py — чинит кнопку «уборка репозитория»
# ПРАВИЛЬНО. Моя прошлая правка (asyncio.create_task) была неверной —
# вот живая ошибка с твоего запуска:
#
#   RuntimeError: The current slot cannot be determined because the
#   slot stack for this task is empty.
#
# Дело в том, как устроен NiceGUI: когда он сам вызывает async-
# обработчик клика, он делает это ВНУТРИ задачи, которая знает, какому
# окну принадлежит клик — это и есть «стек слотов». asyncio.create_task()
# заводит НОВУЮ, отдельную задачу в фоне — она этого знания не
# наследует, и do_uborka() внутри неё не может понять, куда рисовать
# диалог.
#
# Правильный приём — не заводить свою задачу вручную, а отдать NiceGUI
# async-функцию напрямую как on_click. Тогда он сам выполнит её в
# нужном контексте, и ui.dialog() внутри do_uborka() будет знать, где
# рисоваться.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папкой Брат/).
# Запуск из PowerShell, из корня:   python pochinit_knopku_uborki_v2.py
#
# Идёт после pochinit_knopku_uborki.py и заменяет собой его правку.
# Если тот скрипт ещё не запускался — этот всё равно сработает,
# накатит сразу верный вариант.
#
# Ничего не удаляет. Кладёт рядом копию ui_brat.py.bak_knopka_uborki_v2.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "Брат" / "ui_brat.py"

# состояние после pochinit_knopku_uborki.py (V1, ошибочная правка)
BYLO_V1 = (
    '                # POCHINIT_KNOPKU_UBORKI_V1: do_uborka — async,\n'
    '                # голый вызов внутри lambda создавал корутину и\n'
    '                # тут же её ронял, не запустив (диалог закрывался,\n'
    '                # дальше — тишина). asyncio.create_task ставит её\n'
    '                # в очередь событийного цикла по-настоящему.\n'
    '                ui.button("уборка репозитория",\n'
    '                          on_click=lambda: (dlg.close(),\n'
    '                                            asyncio.create_task(\n'
    '                                                do_uborka()))\n'
    '                          ).props("flat no-caps").style('
)

# исходное состояние (если V1 ещё не накатывался)
BYLO_ISHODNOE = (
    '                ui.button("уборка репозитория",\n'
    '                          on_click=lambda: (dlg.close(), do_uborka())\n'
    '                          ).props("flat no-caps").style('
)

STALO = (
    '                # POCHINIT_KNOPKU_UBORKI_V2: не create_task —\n'
    '                # он рвёт стек слотов NiceGUI, do_uborka() внутри\n'
    '                # него не может понять, в каком окне рисовать\n'
    '                # диалог ("slot stack for this task is empty").\n'
    '                # NiceGUI сам умеет выполнять async on_click в\n'
    '                # правильном контексте — просто отдаём ему функцию.\n'
    '                async def _otkryt_uborku_repo():\n'
    '                    dlg.close()\n'
    '                    await do_uborka()\n'
    '\n'
    '                ui.button("уборка репозитория",\n'
    '                          on_click=_otkryt_uborku_repo\n'
    '                          ).props("flat no-caps").style('
)


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")

    if "POCHINIT_KNOPKU_UBORKI_V2" in tekst:
        print("· уже починено (V2)")
        return 0

    kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_knopka_uborki_v2")

    if BYLO_V1 in tekst:
        tekst = tekst.replace(BYLO_V1, STALO, 1)
        istochnik = "с ошибочной правки V1"
    elif BYLO_ISHODNOE in tekst:
        tekst = tekst.replace(BYLO_ISHODNOE, STALO, 1)
        istochnik = "с исходного состояния"
    else:
        print("✗ не нашёл ни V1, ни исходное место — ui_brat.py мог "
              "измениться иначе, скажи Брату, поправим по месту")
        return 1

    if not kopiya.exists():
        shutil.copy2(FAYL, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    FAYL.write_text(tekst, encoding="utf-8")
    print(f"✓ кнопка «уборка репозитория» починена верно ({istochnik})")
    print()
    print("Перезапусти Кабинет (main.py) — правка кода не подхватится "
          "на лету.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
