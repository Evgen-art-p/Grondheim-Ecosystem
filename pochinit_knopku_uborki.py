# -*- coding: utf-8 -*-
# pochinit_knopku_uborki.py — чинит кнопку «уборка репозитория» у Брата:
# она закрывала окно и НИЧЕГО не делала дальше.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папкой Брат/).
# Запуск из PowerShell, из корня:   python pochinit_knopku_uborki.py
#
# Найдено 12.09: кнопка была написана как
#     on_click=lambda: (dlg.close(), do_uborka())
# do_uborka — async-функция. Просто вызвать её внутри лямбды —
# значит создать корутину и тут же её выбросить, не запустив: Питон
# в этот момент честно пишет в консоль "coroutine 'do_uborka' was
# never awaited", а снаружи это выглядит как «нажал — закрылось —
# и тишина». dlg.close() в той же строке выполняется как обычная
# функция, поэтому диалог всё-таки закрывался — вот и обман.
#
# Правка: заворачиваем вызов в asyncio.create_task(), чтобы корутина
# реально встала в очередь событийного цикла. asyncio уже
# импортирован в файле — ничего добавлять не нужно.
#
# Проверено отдельно, вне интерфейса: старый способ («голый» вызов
# async-функции внутри lambda) корутину не запускает вовсе, новый —
# запускает и она честно отрабатывает.
#
# Ничего не удаляет. Кладёт рядом копию ui_brat.py.bak_knopka_uborki.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "Брат" / "ui_brat.py"

BYLO = (
    '                ui.button("уборка репозитория",\n'
    '                          on_click=lambda: (dlg.close(), do_uborka())\n'
    '                          ).props("flat no-caps").style('
)

STALO = (
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


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")

    if BYLO in tekst:
        tekst = tekst.replace(BYLO, STALO, 1)
        kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_knopka_uborki")
        if not kopiya.exists():
            shutil.copy2(FAYL, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        FAYL.write_text(tekst, encoding="utf-8")
        print("✓ кнопка «уборка репозитория» теперь реально запускает "
              "do_uborka()")
        print()
        print("Перезапусти Кабинет (main.py) — правка кода не подхватится "
              "на лету.")
        return 0
    elif "POCHINIT_KNOPKU_UBORKI_V1" in tekst:
        print("· уже починено")
        return 0
    else:
        print("✗ не нашёл ожидаемое место — ui_brat.py мог измениться, "
              "скажи Брату, поправим по месту")
        return 1


if __name__ == "__main__":
    sys.exit(main())
