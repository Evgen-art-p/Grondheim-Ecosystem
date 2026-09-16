# -*- coding: utf-8 -*-
# kadr_bez_okna.py — кадр перестаёт рисоваться в умершую вкладку.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python kadr_bez_okna.py
#
# ЗАЧЕМ. В логе прогона 16.09: вкладка браузера умерла посреди работы
# (связь моргнула, страница обновилась), прогон честно продолжил считать
# в фоне — а кадр продолжал рисоваться в мёртвое окно и вывалил в лог
# полотно стека «Client has been deleted but is still being used».
#
# У ЛЕНТЫ такая защита есть (PROGON_BEZ_OKNA_V1): не смогла нарисовать —
# сказала одну строчку и работает молча. У КАДРА её не было.
#
# ПОЧЕМУ ОБЫЧНЫЙ try/except ТУТ НЕ ГОДИТСЯ. NiceGUI на отрисовку в
# мёртвое окно НЕ бросает ошибку — он пишет предупреждение со стеком в
# лог и идёт дальше. Ловить нечего. Значит надо спрашивать прямо:
# жива ли ещё эта вкладка. Живого клиента NiceGUI держит у себя в
# списке; умершего оттуда убирает. По этому списку и спрашиваем.
#
# ЧТО ДЕЛАЕТ. В Биржа/ui_torg.py добавляет маленькую проверку
# _kadr_zhivoy() и одну стражу в начале pokazat_kadr. Окно живо —
# всё как было. Окно умерло — одна строчка в лог вместо полотна.
# Больше ничего не трогает.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт ui_torg.py.bak_bez_okna.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "KADR_BEZ_OKNA_V1"

YAKOR_FUNKCII = "    async def pokazat_kadr(put=None):\n"

YAKOR_STRAZHI = (
    '        if not kadr_ref["element"]:\n'
    '            return None\n'
    '        # VZGLYAD_PO_VYBORU_V1: сперва спрашиваем ПОЛКУ.\n'
)

POMOSHCHNIK = '''    def _kadr_zhivoy() -> bool:
        """KADR_BEZ_OKNA_V1: жива ли вкладка, в которую рисуем кадр.

        Вкладка могла умереть, пока прогон работает в фоне. NiceGUI на
        отрисовку в мёртвое окно НЕ бросает ошибку — он предупреждает и
        валит в лог полный стек. Поэтому try/except тут бесполезен:
        ловить нечего, надо спрашивать заранее.

        Живого клиента NiceGUI держит в своём списке, умершего убирает.
        Не смогли спросить — считаем живым и рисуем как раньше: молчать
        без причины хуже, чем лишняя строчка в логе.
        """
        el = kadr_ref["element"]
        if not el:
            return False
        try:
            from nicegui import Client as _Cl
            kl = getattr(el, "client", None)
            if kl is None or not hasattr(_Cl, "instances"):
                return True
            return kl.id in _Cl.instances
        except Exception:
            return True

'''

NOVAYA_STRAZHA = (
    '        if not kadr_ref["element"]:\n'
    '            return None\n'
    '        # KADR_BEZ_OKNA_V1: вкладка умерла — рисовать некуда.\n'
    '        # Тот же уговор, что у ленты: работаем молча, отчёт всё\n'
    '        # равно пишется на диск.\n'
    '        if not _kadr_zhivoy():\n'
    '            print("[ПРОГОН] окно не принимает кадр — "\n'
    '                  "работаю молча, отчёт пишется на диск")\n'
    '            return None\n'
    '        # VZGLYAD_PO_VYBORU_V1: сперва спрашиваем ПОЛКУ.\n'
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

    if tekst.count(YAKOR_FUNKCII) != 1 or tekst.count(YAKOR_STRAZHI) != 1:
        print("✗ не нашёл ожидаемое место (или нашёл несколько) —")
        print("  кабинет мог измениться. Ничего не тронул.")
        print("  Скажи Брату, поправим по месту.")
        return 1

    novyy = tekst.replace(YAKOR_FUNKCII, POMOSHCHNIK + YAKOR_FUNKCII, 1)
    novyy = novyy.replace(YAKOR_STRAZHI, NOVAYA_STRAZHA, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_bez_okna")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ кадр больше не рисуется в мёртвую вкладку")
    print("    · добавлена проверка _kadr_zhivoy()")
    print("    · стража в начале pokazat_kadr — как у ленты")
    print()
    print("Перезапусти Кабинет (main.py).")
    print("Проверить просто: запусти прогон, закрой вкладку, посмотри лог.")
    print("Должна быть одна строчка про кадр вместо полотна со стеком.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
