# -*- coding: utf-8 -*-
# kompas_dlya_D1.py — компас появляется у трейдера на дневках.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python kompas_dlya_D1.py
#
# ═══ ОТЧЕГО БОЛЕЛО ═══
#
# В прогоне 16.09 на КАЖДОМ пробуде стояло:
#     [СТОЛ] ⚠️  компаса нет: старший этаж W1 не пришёл
#
# Синди отработала все 87 баров вслепую по старшей воде.
#
# Причина не в данных. Компас считается водой — структурой двух
# этажей выше рабочего. А лесенка воды знала только две ступени:
#
#     H4 → смотрим D1 и W1
#     H1 → смотрим H4 и D1
#
# D1 в лесенке НЕТ. Работала Синди как раз на D1.
#
# Дальше цепочка честная и оттого молчаливая: вода отвечает «для D1
# меня нет, ok=False», якорь этот ответ принимает и сразу возвращает —
# ДО всех своих диагностик. Поэтому в логе ни строчки [КОМПАС] с
# объяснением: до неё не доходит. Остаётся сухое «W1 не пришёл»,
# которое вдобавок называет не тот этаж — W1 тут ни при чём.
#
# ═══ ЧТО СТАВИМ ═══
#
# 1. ЛЕСЕНКА ДОСТРОЕНА ВВЕРХ:
#        D1 → смотрим W1 и MN1
#    Тот же приём, что у H4 и H1: два этажа выше рабочего. Ничего
#    нового не изобретаем.
#
# 2. СКЛЕЙКА УМЕЕТ МЕСЯЦ. Запасной путь (нет файла этажа — склеить
#    его из рабочих баров) знал только день и неделю. Теперь знает и
#    месяц: MN1 из дневок складывается так же просто.
#
# Данные для этого есть: в Биржа/test_data лежат EURUSDWeekly.csv и
# EURUSDMonthly.csv, и по остальным парам тоже. Мостик имён в
# feed_source уже переводит W1 → Weekly, MN1 → Monthly.
#
# ЧЕГО ЭТО НЕ ДЕЛАЕТ. Компас может по-прежнему сказать «воды нет» —
# если W1 и MN1 смотрят в разные стороны. Это не поломка, а честный
# ответ: большой воды сейчас нет. Разница в том, что теперь он будет
# сказан ПО ДЕЛУ, а не потому, что для этажа забыли написать правило.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт voda.py.bak_kompas_D1.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "KOMPAS_DLYA_D1_V1"

STAROE_1 = (
    'LESENKA = {\n'
    '    "H4": ("D1", "W1"),\n'
    '    "H1": ("H4", "D1"),\n'
    '}\n'
)
NOVOE_1 = (
    '# KOMPAS_DLYA_D1_V1: дневки в лесенке НЕ БЫЛО — и трейдер на D1\n'
    '# работал без компаса вовсе. В прогоне 16.09 это была каждая\n'
    '# строчка лога: «компаса нет, старший этаж W1 не пришёл». Этаж\n'
    '# был ни при чём: для D1 просто не написали правило.\n'
    'LESENKA = {\n'
    '    "D1": ("W1", "MN1"),\n'
    '    "H4": ("D1", "W1"),\n'
    '    "H1": ("H4", "D1"),\n'
    '}\n'
)

STAROE_2 = '    if kuda not in ("D1", "W1") or not bars:\n'
NOVOE_2 = (
    '    # KOMPAS_DLYA_D1_V1: добавлен MN1 — склейка знала только день\n'
    '    # и неделю, а месяц теперь тоже бывает нужен как этаж воды.\n'
    '    if kuda not in ("D1", "W1", "MN1") or not bars:\n'
)

STAROE_3 = (
    '        if kuda == "D1":\n'
    '            k = (t.year, t.month, t.day)\n'
    '        else:\n'
    '            iso = t.isocalendar()\n'
    '            k = (iso[0], iso[1])\n'
)
NOVOE_3 = (
    '        if kuda == "D1":\n'
    '            k = (t.year, t.month, t.day)\n'
    '        elif kuda == "MN1":\n'
    '            # KOMPAS_DLYA_D1_V1: месяц — год и номер месяца.\n'
    '            k = (t.year, t.month)\n'
    '        else:\n'
    '            iso = t.isocalendar()\n'
    '            k = (iso[0], iso[1])\n'
)

STAROE_4 = '    if not bars and rabochiy_tf and tf in ("D1", "W1"):\n'
NOVOE_4 = (
    '    # KOMPAS_DLYA_D1_V1: месяц тоже можно склеить, если файла нет.\n'
    '    if not bars and rabochiy_tf and tf in ("D1", "W1", "MN1"):\n'
)

PRAVKI = [(STAROE_1, NOVOE_1), (STAROE_2, NOVOE_2),
          (STAROE_3, NOVOE_3), (STAROE_4, NOVOE_4)]


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет воду сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "voda.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("voda.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько voda.py:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/voda.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("· уже сделано")
        return 0

    for nomer, (staroe, _) in enumerate(PRAVKI, 1):
        if tekst.count(staroe) != 1:
            print(f"✗ правка {nomer}: нашёл {tekst.count(staroe)} мест "
                  f"вместо одного. Ничего не тронул.")
            print("  Скажи Брату, поправим по месту.")
            return 1

    novyy = tekst
    for staroe, novoe in PRAVKI:
        novyy = novyy.replace(staroe, novoe, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_kompas_D1")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ компас достроен:")
    print("    · D1 → смотрим W1 и MN1")
    print("    · склейка научилась складывать месяц")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон на D1.")
    print("Строчки «компаса нет: старший этаж W1 не пришёл» быть не должно.")
    print("Если вместо неё появится «воды нет: W1 BULL, MN1 BEAR» —")
    print("это НЕ поломка, а честный ответ: этажи спорят, воды нет.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
