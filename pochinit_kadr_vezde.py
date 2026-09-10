# -*- coding: utf-8 -*-
# KADR_RISUETSYA_VEZDE_V1 — два места, где кадр молча не рисовался
"""
КАДР ПЕРЕРИСОВЫВАЕТСЯ ВЕЗДЕ

ДОЛГ, ЗАПИСАННЫЙ 09.09: «в двух местах кадр зовут по-старому, без
ожидания, и он молча не перерисовывается». Нашёл оба и понял почему.

ПРИЧИНА. `pokazat_kadr` — асинхронная (её сделали такой патчем
`postavit_kadr_v_potok.py`, когда рисование matplotlib в главном
потоке вешало сервер). А зовут её в двух местах ИЗ ОБЫЧНЫХ функций
и без ожидания:

    Биржа/ui_torg.py:1240   _k_kandidatu  — встать на найденное место
    Биржа/ui_torg.py:1320   _shagnut      — шаг по истории в тестере

Вызов асинхронной функции без ожидания НЕ ВЫПОЛНЯЕТСЯ вовсе. И —
самое неприятное — не бросает исключения: получается корутина,
которую никто не запустил. Поэтому `try/except` вокруг молчит, в
логе чисто, а кадр остаётся прошлым. Идеально тихая поломка.

Остальные вызовы в порядке: в прогоне по истории и при смене
трейдера стоит `await`, а кнопка «Взгляд» отдаёт корутину прямо в
обработчик — NiceGUI такую ждёт сам.

ЧТО ДЕЛАЕТ ПАТЧ. В обоих местах рисование уходит фоновой задачей —
тем же приёмом, что уже используется в этом файле (`create_task`).
Делать сами функции асинхронными нельзя дёшево: за ними тянется
цепочка обычных вызовов, и пришлось бы править полдюжины мест.

Заодно сообщение об ошибке становится честным: если задачу не
удалось поставить (нет живого цикла), это будет видно в логе, а не
проглотится.

БЕЗОПАСНОСТЬ: .bak_kadrvezde, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python pochinit_kadr_vezde.py --suho
    python pochinit_kadr_vezde.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KADR_RISUETSYA_VEZDE_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

PRAVKI = [
    (
        "искатель мест",
        '''        try:
            pokazat_kadr()
        except Exception as e:
            print(f"[ИСКАТЕЛЬ] кадр не перерисовался: {e}")''',
        '''        try:
            # KADR_RISUETSYA_VEZDE_V1: pokazat_kadr асинхронная, а мы
            # в обычной функции. Прямой вызов создаёт корутину и НЕ
            # выполняет её — молча, без исключения. Ставим задачей.
            import asyncio as _a
            _a.get_event_loop().create_task(pokazat_kadr())
        except Exception as e:
            print(f"[ИСКАТЕЛЬ] кадр не перерисовался: {e}")''',
    ),
    (
        "шаг по истории",
        '''        try:
            pokazat_kadr()          # сразу видно следующий бар
        except Exception as e:
            print(f"[ВРЕМЯ] кадр не перерисовался: {e}")''',
        '''        try:
            # KADR_RISUETSYA_VEZDE_V1: то же самое — задачей, иначе
            # корутина повиснет неисполненной и кадр останется прошлым.
            import asyncio as _a
            _a.get_event_loop().create_task(pokazat_kadr())
        except Exception as e:
            print(f"[ВРЕМЯ] кадр не перерисовался: {e}")''',
    ),
]


def main():
    print()
    print("КАДР РИСУЕТСЯ ВЕЗДЕ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return

    novy, sdelano = txt, []
    for imya, staroe, novoe in PRAVKI:
        n = novy.count(staroe)
        if n != 1:
            print(f"  {imya}: ОТКАЗ — якорь встречается {n} раз(а)")
            continue
        novy = novy.replace(staroe, novoe, 1)
        sdelano.append(imya)

    if not sdelano:
        print("Ни одного якоря не нашлось — файл не тронут.")
        return

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return

    for s in sdelano:
        print(f"  {s}: поправлено")
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_kadrvezde"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_kadrvezde")
    print("Теперь кадр едет и за искателем, и за шагом по истории.")
    print()


if __name__ == "__main__":
    main()
