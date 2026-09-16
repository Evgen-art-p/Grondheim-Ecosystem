# -*- coding: utf-8 -*-
# slovo_ne_prikaz_A06.py — убирает противоречие в задании Ильи.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python slovo_ne_prikaz_A06.py
#
# ═══ ОТЧЕГО БОЛЕЛО ═══
#
# В прогоне 16.09 из четырёх пробудов Илья отдал приказ с первого
# раза ОДИН. Остальные три города не принял: «в ответе есть поля
# решения, но рукой приказ не отдан — слово приказом не считается».
# Каждый такой пробуд шёл дважды: два кадра, два обращения к модели.
#
# Виноват не Илья. Город давал ему два противоположных приказа.
#
# В промпт.md написано: «РЕШЕНИЕ В ЭТОТ ОТВЕТ НЕ ПИШЕТСЯ. Войти можно
# только рукой otdat_prikaz». И образец ответа там без решения.
#
# А в мозг.py к тому же заданию дописывалось: «Выдай строго JSON
# {narrative, signal, diary_entry}. Нет открытой позиции: signal
# ключи — brut_verdict, brut_reason, brut_direction, brut_entry,
# brut_stop, brut_lot».
#
# Это СТАРЫЙ язык, времён до рук. Он требовал ровно того, что бумага
# запрещает — написать решение полями в ответе. И стоял последним, а
# последнее слово весит больше. Илья слушался его, заполнял signal —
# и получал отказ за то, что сделал, как велено.
#
# ═══ ЧТО ДЕЛАЕМ ═══
#
# Убираем из задания весь кусок про signal. Остаётся то же, что на
# бумаге: JSON {narrative, diary_entry}, решение — только рукой.
#
# Правим ТОЛЬКО слова, которые видит Илья. Разбор signal в коде не
# трогаем: он безвреден и подстрахует, если поле всё-таки прилетит.
#
# Только A06. A07 и A08 — слово Шефа: пока не трогаем.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт мозг.py.bak_slovo_ne_prikaz.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "SLOVO_NE_PRIKAZ_V2"

PUT = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
       / "слоты" / "A06" / "мозг.py")

STAROE = (
    '        "Выдай строго JSON {narrative, signal, diary_entry}.\\n"\n'
    '        "Нет открытой позиции: signal ключи — brut_verdict "\n'
    '        "(APPROVED/REJECTED), brut_reason, brut_direction, "\n'
    '        "brut_entry, brut_stop, brut_lot.\\n"\n'
    '        "Есть открытая позиция (см. блок \'position\' на столе): signal "\n'
    '        "ключи — brut_action (ENTER/WAIT/HOLD/MOVE_STOP/ADD/CLOSE), "\n'
    '        "brut_reason, brut_new_stop (если MOVE_STOP), brut_add_lot "\n'
    '        "(если ADD).\\n"\n'
)

NOVOE = (
    '        # SLOVO_NE_PRIKAZ_V2: здесь стояло «Выдай строго JSON\n'
    '        # {narrative, signal, diary_entry}» и список ключей\n'
    '        # решения — brut_verdict, brut_direction, brut_entry,\n'
    '        # brut_stop. Старый язык, времён до рук.\n'
    '        #\n'
    '        # Бумага говорит: решение в ответ не пишется, только\n'
    '        # рукой. А эта строка требовала обратного — и стояла\n'
    '        # последней, а последнее слово весит больше. Трейдер\n'
    '        # слушался её, заполнял signal и получал отказ за то,\n'
    '        # что сделал как велено. Три пробуда из четырёх шли\n'
    '        # дважды из-за одного этого противоречия.\n'
    '        "Выдай строго JSON {narrative, diary_entry}.\\n"\n'
    '        "Решения в этом ответе НЕТ и быть не может. Войти, "\n'
    '        "передвинуть стоп, долить или закрыть — только рукой "\n'
    '        "otdat_prikaz. Не работаешь на этом баре — та же рука с "\n'
    '        "WAIT и причиной. Не позвал руку — ничего не произошло, "\n'
    '        "сколько ни рассказывай.\\n"\n'
)


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет мозг Ильи сам. Руками путь прописывать не надо."""
    if PUT.exists():
        return PUT
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("мозг.py")
               if "A06" in str(p) and not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько мозгов A06:")
        for nomer, put in enumerate(nashlos, 1):
            print(f"  {nomer}. {put}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл мозг A06 — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if tekst.count(STAROE) != 1:
        print(f"✗ нашёл {tekst.count(STAROE)} мест вместо одного —")
        print("  задание могло измениться. Ничего не тронул.")
        print("  Скажи Брату, поправим по месту.")
        return 1

    novyy = tekst.replace(STAROE, NOVOE, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_slovo_ne_prikaz")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ противоречие убрано:")
    print("    · из задания Ильи ушёл весь кусок про signal")
    print("    · осталось то же, что на бумаге: решение только рукой")
    print("    · A07 и A08 не тронуты — слово Шефа")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("Смотреть в лог: строчка «[РУКА] 🖐 otdat_prikaz» должна идти")
    print("СРАЗУ после кадра, без «[СЛОВО]» и без «[ПЕРЕСПРОС]» перед ней.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
