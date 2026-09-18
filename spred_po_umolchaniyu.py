# -*- coding: utf-8 -*-
# spred_po_umolchaniyu.py — на истории спреда нет, ставим три пункта.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python spred_po_umolchaniyu.py
#
# ═══ ЧТО НАШЛОСЬ ═══
#
# Прогон 17.09: три года H4, 69 входов, 55 закрытий — и ОДИН плюс.
# Итог −50.86R.
#
# Сперва думали на дивер. Посчитали — и гипотеза рухнула:
#
#     дивер подтверждён (✓):  35 сделок · в плюс 0 · средний −0.98R
#     дивер НЕ подтверждён:   15 сделок · в плюс 1 · средний −0.80R
#
# Разницы нет. Тридцать пять сделок с настоящим дивером — и ни одной
# прибыльной. Значит вход тут ни при чём.
#
# Посчитали стопы:
#
#     отступ стопа за край разворотного бара:
#       медиана 0 пунктов
#       ровно на краю или внутри — 66 входов из 69
#       больше 5 пунктов — НИ ОДНОГО
#
# ═══ ПРИЧИНА, И ВИНОВАТ НИКТО ═══
#
# В барах из CSV спред не записан. _spred_ceny честно возвращает None,
# дальше подставляется ноль — и стол считает:
#
#     заявка = low − 0   → ровно low
#     стоп   = high + 0  → ровно high
#
# То есть СТОЛ САМ ВЫДАЁТ голые края бара. Трейдер их исправно
# копирует — как её и учили — и получает стоп ровно на уровне, куда
# рынок возвращается почти всегда. Обычный ретест снимает сделку до
# того, как она успеет стать правой.
#
# Стол при этом предупреждает словами: «⚠ спред НЕ учтён: история без
# спреда». Но предупреждение словами, а числа рядом — без спреда. Она
# берёт числа.
#
# На реальном счёте спред придёт от терминала и этого не случится. В
# тестере — случается каждый раз.
#
# ═══ ЧТО СТАВИМ (слово Шефа) ═══
#
# «Ставь три пункта, ордера выше свечи — два спреда, ниже свечи —
#  один спред.»
#
# Нет спреда в истории — берём ТРИ ПУНКТА по умолчанию. Правило
# распределения не трогаем, оно уже стоит верно: сверху два спреда,
# снизу один.
#
# Что это даёт на EURUSD (шаг 0.00001):
#     спред        = 0.00003
#     сверху (×2)  = 0.00006  — стоп шорта над максимумом
#     снизу  (×1)  = 0.00003  — заявка шорта под минимумом
#
# Стол перестанет выдавать голый край, и стоп встанет ЗА бар, а не НА
# него.
#
# Цифру легко поменять: она стоит одной строкой в начале stol.py —
# SPRED_PO_UMOLCHANIYU = 3.
#
# Живой спред из терминала по-прежнему главнее: умолчание берётся,
# только когда его нет.
#
# БЕЗОПАСНО. Проверяет ast.parse. Рядом кладёт stol.py.bak_spred.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "SPRED_PO_UMOLCHANIYU_V1"

STAROE_1 = '_BIRZHA = Path(__file__).resolve().parent\n'
NOVOE_1 = (
    '_BIRZHA = Path(__file__).resolve().parent\n'
    '\n'
    '# SPRED_PO_UMOLCHANIYU_V1: сколько пунктов спреда брать, когда в\n'
    '# истории его нет. Слово Шефа 17.09: «ставь три пункта, ордера\n'
    '# выше свечи — два спреда, ниже свечи — один спред».\n'
    '#\n'
    '# Ноль вместо спреда стоил прогону 54 убытка из 55: стол выдавал\n'
    '# голые края бара, стоп вставал ровно на край, и обычный ретест\n'
    '# снимал сделку до того, как она успевала стать правой.\n'
    '#\n'
    '# Живой спред из терминала главнее — это только на бесспредовую\n'
    '# историю. Менять цифру можно прямо здесь.\n'
    'SPRED_PO_UMOLCHANIYU = 3\n'
)

STAROE_2 = (
    '        sp = (b[-1] or {}).get("spread")\n'
    '        shag = point or p\n'
    '        if sp in (None, "") or not shag:\n'
    '            return None, "в баре нет спреда"\n'
    '        sp = float(sp)\n'
    '        if sp <= 0:\n'
    '            return None, "история без спреда"\n'
    '        return sp * float(shag), f"{sp:.0f} пункт(ов)"\n'
)
NOVOE_2 = (
    '        sp = (b[-1] or {}).get("spread")\n'
    '        shag = point or p\n'
    '        if not shag:\n'
    '            return None, "шага цены нет"\n'
    '        try:\n'
    '            sp = float(sp) if sp not in (None, "") else 0.0\n'
    '        except (TypeError, ValueError):\n'
    '            sp = 0.0\n'
    '        if sp <= 0:\n'
    '            # SPRED_PO_UMOLCHANIYU_V1: в истории спреда нет —\n'
    '            # раньше отсюда уходил None, и выше подставлялся\n'
    '            # НОЛЬ. Стол выдавал голые края бара, стоп вставал\n'
    '            # ровно на край. Ноль — это не «спреда нет», это\n'
    '            # «его не записали»; в рынке его не бывает.\n'
    '            return (SPRED_PO_UMOLCHANIYU * float(shag),\n'
    '                    f"{SPRED_PO_UMOLCHANIYU} пункт(а) по умолчанию — "\n'
    '                    f"в истории спреда нет")\n'
    '        return sp * float(shag), f"{sp:.0f} пункт(ов)"\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    prosto = KOREN / "Биржа" / "stol.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nash = [p for p in KOREN.rglob("stol.py")
            if not any(m in str(p) for m in musor)]
    if len(nash) == 1:
        return nash[0]
    if len(nash) > 1:
        print("Нашёл несколько stol.py:")
        for n, p in enumerate(nash, 1):
            print(f"  {n}. {p}")
        o = input("Какой правим? номер: ").strip()
        if o.isdigit() and 1 <= int(o) <= len(nash):
            return nash[int(o) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/stol.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("· уже сделано")
        return 0

    pravki = [(STAROE_1, NOVOE_1), (STAROE_2, NOVOE_2)]
    for nomer, (staroe, _) in enumerate(pravki, 1):
        if tekst.count(staroe) != 1:
            print(f"✗ правка {nomer}: нашёл {tekst.count(staroe)} мест "
                  f"вместо одного. Ничего не тронул.")
            return 1

    novyy = tekst
    for staroe, novoe in pravki:
        novyy = novyy.replace(staroe, novoe, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno})")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_spred")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ спред по умолчанию встал:")
    print("    · три пункта, когда в истории спреда нет")
    print("    · сверху два спреда, снизу один — правило не тронуто")
    print("    · живой спред из терминала по-прежнему главнее")
    print("    · цифра меняется одной строкой в начале stol.py")
    print()
    print("Перезапусти Кабинет (main.py) и прогони ТОТ ЖЕ отрезок.")
    print("Смотреть: отступ стопа от края бара. Был 0 у 66 входов из 69,")
    print("должен стать 6 пунктов сверху и 3 снизу.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
