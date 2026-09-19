# -*- coding: utf-8 -*-
# vklyuchit_treyling.py — включает ведение стопа за Зубами.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python vklyuchit_treyling.py
#
# ═══ ЧТО НАШЛОСЬ ═══
#
# В hooks.py есть готовая функция _treyling_za_zubami: тянет стоп за
# Зубами Аллигатора, только в защитную сторону, печатает [ТРЕЙЛ] и
# [СЕЙФ] при обнулении риска.
#
# ЕЁ НИКТО НЕ ЗОВЁТ. Единственное упоминание во всём файле — её
# собственное определение. Написана, проверена, не подключена. Оттого
# в логах ни одной строчки [ТРЕЙЛ] или [СЕЙФ] за все прогоны.
#
# ═══ ПОЧЕМУ ЭТО ВАЖНО ═══
#
# Прогнали четыре способа ведения стопа на 64 входах Синди, на живых
# барах EURUSD H4:
#
#   никто — стоп стоит          −46.4R   плюсовых  2
#   фракталы СВОЕГО этажа H4    −15.3R   плюсовых 14   ← стоит у неё
#   фракталы старшего D1        −30.9R   плюсовых  7
#   фракталы младшего H1         −5.1R   плюсовых 23
#   АЛЛИГАТОР (Зубы)             −6.1R   плюсовых 27   ← лучший по
#                                                        прибыльным
#
# То есть ЛУЧШЕЕ ВЕДЕНИЕ УЖЕ НАПИСАНО и просто выключено. Фракталы
# младшего этажа дают столько же, но требуют второго этажа данных и
# невидимы трейдеру на кадре. Зубы она видит своими глазами.
#
# А хуже всех — редкие мерки: свой фрактал (раз в двое суток) и
# дневной (раз в неделю). Стоп стоит, пока не станет поздно.
#
# ═══ ЧТО СТАВИМ ═══
#
# Один вызов в rynok_novyy_bar — ровно там, где обещано в докстринге
# самой функции: КАЖДЫЙ БАР, ДО проверки стопов, чтобы сейф успел
# сработать раньше, чем рынок дотянется до старого стопа.
#
# Обёрнуто в try: не посчитался Аллигатор — бар идёт дальше, позиции
# закрываются как раньше. Включение не должно ломать старое.
#
# ЧЕГО НЕ ДЕЛАЕТ. Руку MOVE_STOP у трейдера не отнимает и её ведение
# по фракталам не запрещает — это бумага, не код. Если оба тянут в
# одну сторону, побеждает тот, кто ближе; только в защиту.
#
# БЕЗОПАСНО. Проверяет ast.parse. Рядом кладёт hooks.py.bak_treyling.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "VKLYUCHIT_TREYLING_V1"

STAROE = (
    '    _bylo_v_stole = len(cd["open_positions"])\n'
    '    try:\n'
    '        _settle_positions(state)\n'
)

NOVOE = (
    '    _bylo_v_stole = len(cd["open_positions"])\n'
    '    # VKLYUCHIT_TREYLING_V1: тянем стоп за Зубами ДО проверки\n'
    '    # стопов — так обещано в докстринге самой функции: «чтобы\n'
    '    # сейф успел сработать раньше, чем рынок дотянется до\n'
    '    # старого стопа».\n'
    '    #\n'
    '    # Функция была написана и НИКЕМ НЕ ВЫЗЫВАЛАСЬ: ни одной\n'
    '    # строчки [ТРЕЙЛ] за все прогоны. А на замере по 64 входам\n'
    '    # она дала −6.1R против −15.3R у фракталов своего этажа и\n'
    '    # −46.4R у неподвижного стопа. Лучшее ведение лежало\n'
    '    # выключенным.\n'
    '    try:\n'
    '        _treyling_za_zubami(state)\n'
    '    except Exception as e:\n'
    '        print(f"[РЫНОК] ⚠️  стоп не подтянулся ({e}) — иду дальше")\n'
    '    try:\n'
    '        _settle_positions(state)\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    prosto = KOREN / "Биржа" / "hooks.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nash = [p for p in KOREN.rglob("hooks.py")
            if not any(m in str(p) for m in musor)]
    if len(nash) == 1:
        print(f"Нашёл: {nash[0]}")
        return nash[0]
    if len(nash) > 1:
        print("Нашёл несколько hooks.py:")
        for n, p in enumerate(nash, 1):
            print(f"  {n}. {p}")
        o = input("Какой правим? номер: ").strip()
        if o.isdigit() and 1 <= int(o) <= len(nash):
            return nash[int(o) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/hooks.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if "def _treyling_za_zubami" not in tekst:
        print("✗ в hooks.py нет самой функции _treyling_za_zubami.")
        print("  Ничего не тронул.")
        return 1

    if tekst.count("_treyling_za_zubami(") > 1:
        print("· похоже, трейлинг уже кем-то вызывается — не трогаю.")
        return 0

    if tekst.count(STAROE) != 1:
        print(f"✗ нашёл {tekst.count(STAROE)} мест вместо одного —")
        print("  hooks.py мог измениться. Ничего не тронул.")
        print("  Скажи Брату, поправим по месту.")
        return 1

    novyy = tekst.replace(STAROE, NOVOE, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno})")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_treyling")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ трейлинг за Зубами включён:")
    print("    · зовётся каждый бар, ДО проверки стопов")
    print("    · только в защитную сторону, ослабление игнорируется")
    print("    · не посчитался — бар идёт дальше, ничего не ломается")
    print()
    print("Перезапусти Кабинет (main.py) и прогони ТОТ ЖЕ отрезок.")
    print("В логе должны появиться строчки [ТРЕЙЛ] ⬆ и [СЕЙФ] 🔒 —")
    print("их не было ни разу за все прогоны.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
