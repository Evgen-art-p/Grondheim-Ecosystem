# -*- coding: utf-8 -*-
# hold_tolko_pri_pozicii_A06.py — HOLD только когда есть что держать.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python hold_tolko_pri_pozicii_A06.py
#
# ВАЖНО: идёт после ruka_poslednim_slovom_A06.py.
#
# ═══ ЧТО СЛОМАЛОСЬ И ПО ЧЬЕЙ ВИНЕ ═══
#
# Это Брат сломал сам. Убирая из задания блок про signal, он вместе с
# ним вырезал строку:
#
#   «Есть открытая позиция (см. блок position на столе): ключи —
#    brut_action (ENTER/WAIT/HOLD/MOVE_STOP/ADD/CLOSE)…»
#
# Это было ЕДИНСТВЕННОЕ место, где город объяснял: HOLD, MOVE_STOP,
# ADD и CLOSE уместны только при открытой позиции. Условие ушло, а
# сами слова остались — они живут в описании руки, где просто «HOLD —
# держу как есть», без всякого «если есть что держать».
#
# А новое окончание говорит: «работаешь — ENTER, не работаешь — WAIT,
# третьего нет». HOLD в этот список не попал вовсе.
#
# Дальше по-человечески понятно. Слово доступно — трейдер его берёт и
# САМ СЕБЕ СОЧИНЯЕТ основание. В прогоне 16.09 Синди сказала: «Я уже
# в SHORT позиции, и пока нет причин для закрытия» — а на столе было
# позиций=0, та сделка закрылась стопом тремя неделями раньше. Она не
# врала: она достроила мир под слово, которое ей разрешили сказать.
#
# ═══ ЧТО СТАВИМ ═══
#
# 1. В КОНЕЦ ЗАДАНИЯ — недостающее условие: пусто на столе, значит
#    ENTER или WAIT; есть позиция — HOLD, MOVE_STOP, ADD, CLOSE.
#
# 2. ТУДА ЖЕ — правило, которого не было никогда: ЧТО НА СТОЛЕ, ТО И
#    ЕСТЬ ПРАВДА. Нет блока position — позиции нет, сколько бы ты её
#    ни помнил. Память о сделке и сама сделка — разные вещи.
#
# 3. В ОПИСАНИЕ РУКИ — то же условие при каждом слове, чтобы HOLD не
#    выглядел доступным всегда. Правится общий файл рук, но меняются
#    только ПОЯСНЕНИЯ к словам; ни одно правило исполнения не
#    трогается, и на A07/A08 это не влияет: у них те же слова
#    означали то же самое.
#
# БЕЗОПАСНО. Правит два файла, каждый проверяет отдельно и пишет
# только если сошлись оба. Рядом кладёт копии.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "HOLD_PRI_POZICII_V1"
NUZHEN = "RUKA_POSLEDNIM_SLOVOM_V1"

MOZG = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
        / "слоты" / "A06" / "мозг.py")
RUKI = KOREN / "Биржа" / "ruki_treydera.py"

M_STAROE = (
    '        "Не работаешь на этом баре — та же рука с WAIT и "\n'
    '        "причиной.\\n"\n'
)
M_NOVOE = (
    '        "Не работаешь на этом баре — та же рука с WAIT и "\n'
    '        "причиной.\\n"\n'
    '        # HOLD_PRI_POZICII_V1: это условие было вырезано вместе со\n'
    '        # старым блоком signal — и трейдер начал говорить HOLD без\n'
    '        # позиции, сочиняя себе основание: «я уже в SHORT».\n'
    '        "\\nЭти два слова — когда на столе ПУСТО. Если позиция "\n'
    '        "открыта (блок position на столе), слова другие: HOLD — "\n'
    '        "держу как есть, MOVE_STOP — передвинуть стоп, ADD — "\n'
    '        "долить, CLOSE — закрыть.\\n"\n'
    '        "ЧТО НА СТОЛЕ, ТО И ЕСТЬ ПРАВДА. Нет блока position — "\n'
    '        "позиции НЕТ, сколько бы ты её ни помнил. Сделка могла "\n'
    '        "закрыться стопом, пока тебя не будили. Память о сделке и "\n'
    '        "сама сделка — разные вещи: держать нечего, и HOLD тут "\n'
    '        "сказать не о чем.\\n"\n'
)

R_STAROE = (
    '                "что": {"type": "string",\n'
    '                        "description": ("ENTER — войти · WAIT — не работаю · "\n'
    '                                        "HOLD — держу как есть · MOVE_STOP — "\n'
    '                                        "передвинуть стоп · ADD — долить · "\n'
    '                                        "CLOSE — закрыть")},\n'
)
R_NOVOE = (
    '                # HOLD_PRI_POZICII_V1: у каждого слова названо, КОГДА\n'
    '                # оно уместно. Раньше «HOLD — держу как есть» стояло\n'
    '                # без условия, и трейдер брал его без позиции,\n'
    '                # сочиняя себе сделку, которой нет.\n'
    '                "что": {"type": "string",\n'
    '                        "description": ("Позиции НЕТ: ENTER — войти · "\n'
    '                                        "WAIT — не работаю. "\n'
    '                                        "Позиция ОТКРЫТА (есть блок "\n'
    '                                        "position на столе): HOLD — держу "\n'
    '                                        "как есть · MOVE_STOP — передвинуть "\n'
    '                                        "стоп · ADD — долить · CLOSE — "\n'
    '                                        "закрыть. Позиции нет — HOLD, "\n'
    '                                        "MOVE_STOP, ADD и CLOSE сказать не "\n'
    '                                        "о чем.")},\n'
)


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti(put_pryamo, imya, primeta=None):
    """Ищет файл сам. Руками путь прописывать не надо."""
    if put_pryamo.exists():
        return put_pryamo
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob(imya)
               if not any(m in str(p) for m in musor)
               and (primeta is None or primeta in str(p))]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print(f"Нашёл несколько {imya}:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def podgotovit(put, staroe, novoe):
    """Собирает новый текст, ничего не записывая."""
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        return None, "уже сделано"
    if tekst.count(staroe) != 1:
        return None, f"нашёл {tekst.count(staroe)} мест вместо одного"
    novyy = tekst.replace(staroe, novoe, 1)
    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        return None, f"после правки файл поломался (строка {beda.lineno})"
    return novyy, ""


def main():
    mozg = nayti(MOZG, "мозг.py", "A06")
    ruki = nayti(RUKI, "ruki_treydera.py")
    if mozg is None or ruki is None:
        print("✗ не нашёл мозг A06 или ruki_treydera.py —")
        print("  запускай из корня репозитория")
        return 1

    if NUZHEN not in mozg.read_text(encoding="utf-8"):
        print("✗ сперва накати ruka_poslednim_slovom_A06.py.")
        print("  Ничего не тронул.")
        return 1

    m_novyy, m_beda = podgotovit(mozg, M_STAROE, M_NOVOE)
    r_novyy, r_beda = podgotovit(ruki, R_STAROE, R_NOVOE)

    if m_beda == "уже сделано" and r_beda == "уже сделано":
        print("· уже сделано")
        return 0

    for imya, beda in (("мозг A06", m_beda), ("ruki_treydera.py", r_beda)):
        if beda and beda != "уже сделано":
            print(f"✗ {imya}: {beda}")
            print("  Ничего не тронул ни в одном файле.")
            print("  Скажи Брату, поправим по месту.")
            return 1

    for put, novyy in ((mozg, m_novyy), (ruki, r_novyy)):
        if novyy is None:
            continue
        kopiya = put.with_suffix(put.suffix + ".bak_hold")
        if not kopiya.exists():
            shutil.copy2(put, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        put.write_text(novyy, encoding="utf-8")

    print("✓ HOLD вернулся на своё место:")
    print("    · пусто на столе — только ENTER или WAIT")
    print("    · есть позиция — HOLD, MOVE_STOP, ADD, CLOSE")
    print("    · «что на столе, то и есть правда» — новое правило")
    print("    · в описании руки у каждого слова названо, когда оно к месту")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("Смотреть просто: если в логе есть «с руки: HOLD», рядом")
    print("должно стоять «позиций=1». HOLD при позиций=0 — значит мимо.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
