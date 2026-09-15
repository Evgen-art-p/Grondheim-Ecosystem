# -*- coding: utf-8 -*-
# finalnyy_uroven1_A06.py — АО и приседающий по формулировке Шефа
# (14-15.09): последовательность взгляда, не формула из двух точек;
# некрон — будильник, а не четвёртое условие; строка на столе
# убирается — два судьи в одном поле хуже одного неидеального.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папками Биржа/ и
# GRONDHEIM_CITY/). Запуск из PowerShell, из корня:
#   python finalnyy_uroven1_A06.py
#
# Что меняет:
#   1. AO.md — переписан целиком: весь ход → самый выраженный
#      участок → цена продолжает → следующий участок слабее → дивер.
#      Пересечение нуля, номер волны, расстояние — не считаются.
#      Найденный участок остаётся точкой сравнения, пока ход не
#      развернулся — можно сравнивать с ним много раз подряд.
#      Без лишних выводов вроде «жди/не жди» — просто факт.
#   2. MFI.md — дорожка приседающих: один прямо на разворотном баре
#      уже достаточен; несколько подряд — тот же факт: объём растёт,
#      цена всё меньше продвигается. Без склеивания с AO.
#   3. промпт.md — раздел «КАК СМОТРЯТ» переставлен: НЕКРОН — будильник
#      (не сам факт, а сигнал начать смотреть три факта), сами три —
#      ЦЕНА (ход), AO (дивер), ПРИСЕДАЮЩИЙ.
#   4. stol.py — строка «дивергенция AO: True/False» (и медвежья
#      половина, добавленная прошлым патчем) убирается со стола.
#      Причина не в точности цифры — два судьи в одном поле зрения
#      хуже одного неидеального: если трейдер видит дивер глазами, а
#      рядом стоит казённое False, непонятно, кому верить.
#
# Ничего не удаляет безвозвратно — по одной копии на файл рядом,
# с хвостом .bak_uroven1_final. Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
ZNANIYA = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
           / "слоты" / "A06" / "знания")
PROMPT_PATH = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
               / "слоты" / "A06" / "промпт.md")
STOL_PATH = KOREN / "Биржа" / "stol.py"


AO_NOVOE = """# AO — Awesome Oscillator

Источник: Вильямс, «Торговый Хаос» (методология).

## Что это

Разница двух скользящих средних по медиане бара (high+low)/2:
короткая (5 баров) минус длинная (34 бара). Гистограмма от нуля.

Цвет столбика — выше или ниже ПРЕДЫДУЩЕГО столбика: выше — зелёный,
ниже — красный.

## Как смотреть

Весь видимый ход. Найди в его направлении самый выраженный горб или
яму. Если цена продолжает этот ход, а следующий заметный горб или
яма — уже меньше прежнего: толчок слабее. Это дивер.

Пересечение нуля между ними, расстояние, номер волны — не считаются.

Тот же вопрос можно увидеть несколько раз подряд, на разном шаге —
от общей картины до пары горбов у самого края. Один и тот же факт,
не два разных.

Пока ход не развернулся, найденный горб или яма остаётся точкой
сравнения для следующих шагов.

<!-- ZNANIYA_PERVOGO_UROVNYA_A06_V1 -->
"""

MFI_STARAYA_DOROZHKA = (
    "**Смотри дорожкой, а не по одному.** Один приседающий — просто бар.\n"
    "Несколько подряд перед разворотным — рынок готовился, дрались тут\n"
    "не раз.\n"
)
MFI_NOVAYA_DOROZHKA = (
    "Один приседающий прямо на разворотном баре — уже достаточен.\n"
    "\n"
    "Если перед разворотным бар не один, а несколько подряд — каждый\n"
    "раз объём растёт, а цена всё меньше продвигается.\n"
)

# ── промпт: перестановка «КАК СМОТРЯТ» ────────────────────────────────

PROMPT_BYLO = (
    "На твоём уровне три вещи. Больше ничего — не потому что остального\n"
    "нет, а потому что оно читается позже и другим масштабом.\n"
    "\n"
    "**НЕКРОН — сигнал.** Разворотный бар: цену сводили далеко и вернули.\n"
    "Он уже случился, потому тебя и позвали. Твой вопрос не «есть ли он»,\n"
    "а ГДЕ он стоит: в молодом ходе или в выдохшемся.\n"
    "\n"
    "**AO — сила импульса.** Выдыхается движение или нет. Цена ушла\n"
    "дальше, а горб мельче прошлого — выдохся. Это дивер. Он не команда\n"
    "разворачиваться, он говорит: место близко.\n"
    "\n"
    "**ПРИСЕДАЮЩИЙ — напряжение.** Объём вырос, а цена почти не\n"
    "сдвинулась — упёрлась. Один такой бар — просто бар; дорожка перед\n"
    "разворотным — здесь давно дрались.\n"
)

PROMPT_STALO = (
    "На твоём уровне три факта. Больше ничего — не потому что остального\n"
    "нет, а потому что оно читается позже и другим масштабом.\n"
    "\n"
    "**НЕКРОН — будильник.** Разворотный бар: цену сводили далеко и\n"
    "вернули. Не факт из трёх, а сигнал начать их смотреть — без него\n"
    "смотреть не на чем.\n"
    "\n"
    "**ЦЕНА — ход.** Растут фракталы-хаи и фракталы-лои или падают —\n"
    "молодой ход или выдохшийся (`TREND_PO_TSENE.md`).\n"
    "\n"
    "**AO — дивер.** Самый выраженный горб или яма против следующего,\n"
    "пока цена продолжает: меньше прежнего — дивер (`AO.md`).\n"
    "\n"
    "**ПРИСЕДАЮЩИЙ — объём.** Один на разворотном баре — уже достаточен.\n"
    "Несколько подряд — объём растёт, цена всё меньше продвигается\n"
    "(`MFI.md`).\n"
)

# ── stol.py: откат медвежьей строки ────────────────────────────────

STOL_BYLO_1 = (
    '        "дивергенция_ao": md.get("divergence_ao"),\n'
    '        # DOBAVIT_MEDVEZHYU_DIVERGENCIYU_V1: тот же честный код,\n'
    '        # что считает бычью (md["divergence_ao"]), считает и\n'
    '        # медвежью — она лежала в md["exit_bell"] и на стол не\n'
    '        # попадала вовсе.\n'
    '        "дивергенция_ao_медвежья": md.get("exit_bell"),\n'
    '        "приседающий_бар": bool((md.get("squat") or {}).get("last_squat")),\n'
)
STOL_STALO_1 = (
    '        # UBRAT_STROKU_DIVERGENCII_V1 (14-15.09, Шеф): два судьи в\n'
    '        # одном поле зрения хуже одного неидеального. Трейдер видит\n'
    '        # дивер глазами по всей картине (лесенка, а не пара точек) —\n'
    '        # казённое True/False рядом создаёт ложный спор с собой.\n'
    '        # Раньше здесь стояли "дивергенция_ao" и "дивергенция_ao_'
    'медвежья".\n'
    '        "приседающий_бар": bool((md.get("squat") or {}).get("last_squat")),\n'
)

STOL_BYLO_2 = (
    "        f\"дивергенция AO: {p.get('дивергенция_ao')} (рост)   \"\n"
    "        f\"{p.get('дивергенция_ao_медвежья')} (падение)   \"\n"
    "        f\"приседающий бар: {p.get('приседающий_бар')}\",\n"
)
STOL_STALO_2 = (
    "        f\"приседающий бар: {p.get('приседающий_бар')}\",\n"
)

# запасной вариант: если DOBAVIT_MEDVEZHYU_DIVERGENCIYU_V1 не запускался,
# в stol.py всё ещё исходный (только бычья строка)
STOL_BYLO_1_ISHODNYY = (
    '        "дивергенция_ao": md.get("divergence_ao"),\n'
    '        "приседающий_бар": bool((md.get("squat") or {}).get("last_squat")),\n'
)
STOL_BYLO_2_ISHODNYY = (
    "        f\"дивергенция AO: {p.get('дивергенция_ao')}   \"\n"
    "        f\"приседающий бар: {p.get('приседающий_бар')}\",\n"
)


def _kopiya(put: Path, hvost: str) -> None:
    k = put.with_suffix(put.suffix + hvost)
    if not k.exists():
        shutil.copy2(put, k)
        print(f"  (копия старого: {k.name})")


def main() -> int:
    sdelano, uzhe, ne_nashlos = 0, 0, 0

    # 1. AO.md — переписать целиком
    ao_put = ZNANIYA / "AO.md"
    if not ao_put.exists():
        print(f"✗ нет файла {ao_put}")
        ne_nashlos += 1
    else:
        tekushchee = ao_put.read_text(encoding="utf-8")
        if tekushchee == AO_NOVOE:
            print("· уже сделано — AO.md")
            uzhe += 1
        else:
            _kopiya(ao_put, ".bak_uroven1_final")
            ao_put.write_text(AO_NOVOE, encoding="utf-8")
            print("✓ AO.md переписан — последовательность взгляда, без формулы")
            sdelano += 1

    # 2. MFI.md — дорожка приседающих
    mfi_put = ZNANIYA / "MFI.md"
    if not mfi_put.exists():
        print(f"✗ нет файла {mfi_put}")
        ne_nashlos += 1
    else:
        tekst = mfi_put.read_text(encoding="utf-8")
        if MFI_STARAYA_DOROZHKA in tekst:
            tekst = tekst.replace(MFI_STARAYA_DOROZHKA, MFI_NOVAYA_DOROZHKA, 1)
            _kopiya(mfi_put, ".bak_uroven1_final")
            mfi_put.write_text(tekst, encoding="utf-8")
            print("✓ MFI.md: один приседающий на баре достаточен")
            sdelano += 1
        elif MFI_NOVAYA_DOROZHKA in tekst:
            print("· уже сделано — MFI.md")
            uzhe += 1
        else:
            print("✗ не нашёл место в MFI.md")
            ne_nashlos += 1

    # 3. промпт — некрон/цена/AO/приседающий
    if not PROMPT_PATH.exists():
        print(f"✗ нет файла {PROMPT_PATH}")
        ne_nashlos += 1
    else:
        tekst = PROMPT_PATH.read_text(encoding="utf-8")
        if PROMPT_BYLO in tekst:
            tekst = tekst.replace(PROMPT_BYLO, PROMPT_STALO, 1)
            _kopiya(PROMPT_PATH, ".bak_uroven1_final")
            PROMPT_PATH.write_text(tekst, encoding="utf-8")
            print("✓ промпт: некрон — будильник, три факта — цена/AO/приседающий")
            sdelano += 1
        elif "НЕКРОН — будильник" in tekst:
            print("· уже сделано — промпт")
            uzhe += 1
        else:
            print("✗ не нашёл место в промпте")
            ne_nashlos += 1

    # 4. stol.py — откат строки со стола
    if not STOL_PATH.exists():
        print(f"✗ нет файла {STOL_PATH}")
        ne_nashlos += 1
    else:
        tekst = STOL_PATH.read_text(encoding="utf-8")
        izmeneno = False
        if STOL_BYLO_1 in tekst:
            tekst = tekst.replace(STOL_BYLO_1, STOL_STALO_1, 1)
            izmeneno = True
        elif STOL_BYLO_1_ISHODNYY in tekst:
            tekst = tekst.replace(STOL_BYLO_1_ISHODNYY,
                                   STOL_STALO_1, 1)
            izmeneno = True
        elif "UBRAT_STROKU_DIVERGENCII_V1" not in tekst:
            print("✗ не нашёл первое место в stol.py (словарь приборов)")
            ne_nashlos += 1
        if STOL_BYLO_2 in tekst:
            tekst = tekst.replace(STOL_BYLO_2, STOL_STALO_2, 1)
            izmeneno = True
        elif STOL_BYLO_2_ISHODNYY in tekst:
            tekst = tekst.replace(STOL_BYLO_2_ISHODNYY,
                                   STOL_STALO_2, 1)
            izmeneno = True
        elif "UBRAT_STROKU_DIVERGENCII_V1" not in tekst:
            print("✗ не нашёл второе место в stol.py (текст строки)")
            ne_nashlos += 1
        if izmeneno:
            _kopiya(STOL_PATH, ".bak_uroven1_final")
            STOL_PATH.write_text(tekst, encoding="utf-8")
            print("✓ stol.py: строка дивергенции убрана со стола")
            sdelano += 1
        elif "UBRAT_STROKU_DIVERGENCII_V1" in tekst:
            print("· уже сделано — stol.py")
            uzhe += 1

    print()
    print(f"ИТОГ: сделано {sdelano}, было уже в порядке {uzhe}, "
          f"не нашлось мест {ne_nashlos}")
    if sdelano:
        print("Перезапусти Кабинет (main.py) — правки кода не подхватятся "
              "на лету.")
    return 1 if ne_nashlos else 0


if __name__ == "__main__":
    sys.exit(main())
