# -*- coding: utf-8 -*-
# kompas_prichina_v_log.py — видно, почему компаса нет.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python kompas_prichina_v_log.py
#
# ═══ ЗАЧЕМ ═══
#
# После kompas_dlya_D1.py лесенка воды знает дневки, и жалоба
# «компаса нет: старший этаж W1 не пришёл» из лога ушла.
#
# А компас всё равно None — во всех 26 слепках прогона 16.09.
#
# И это не поломка, а МОЛЧАНИЕ. Вода теперь отвечает по делу: этаж
# пришёл, посчитан, но стороны нет — W1 и MN1 смотрят вразнобой.
# Причина такого ответа кладётся на стол в поле «вода_почему», а в
# лог не выводится вообще. Оттого и тишина: жалобы нет, компаса нет,
# и понять почему нечем.
#
# ═══ ЧТО СТАВИМ ═══
#
# Одну строчку в лог. Ничего больше.
#
#   · компаса нет, но этаж пришёл → печатаем причину и оба этажа:
#         [КОМПАС] EURUSD D1: воды нет — W1 BULL, MN1 BEAR
#   · компас появился → печатаем, какой и на чём:
#         [КОМПАС] EURUSD D1: BULL — W1 BULL, MN1 BULL
#
# Печатается ОДИН РАЗ на каждый новый расклад, а не на каждом баре:
# иначе лог утонет так же, как тонет в сохранениях стола.
#
# ═══ ЧЕГО ЭТОТ ПАТЧ НЕ ДЕЛАЕТ ═══
#
# Ни одного правила не меняет. Ни одной цифры не трогает. Трейдеру на
# стол ничего не добавляет и ничего с него не убирает — поле
# «вода_почему» там и так лежало. Это чисто окно, чтобы Шеф увидел,
# что происходит со старшей водой.
#
# Привычку Синди сперва брать стол рукой, а потом судить, патч не
# задевает никак.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт stol.py.bak_kompas_prichina.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "KOMPAS_PRICHINA_V1"

# ── 1. память «уже сказали» на верхнем уровне файла ──
STAROE_1 = (
    'def nakryt(symbol: str, timeframe: str,\n'
)
NOVOE_1 = (
    '# KOMPAS_PRICHINA_V1: про какой расклад воды уже говорили в лог.\n'
    '# Без этого строчка повторялась бы на каждом баре и утопила бы\n'
    '# лог так же, как его топят сохранения стола.\n'
    '_KOMPAS_SKAZANO = set()\n'
    '\n'
    '\n'
    'def nakryt(symbol: str, timeframe: str,\n'
)

# ── 2. сама строчка ──
STAROE_2 = (
    '    if compass is None and not starshiy_prishyol:\n'
    '        print(f"[СТОЛ] ⚠️  компаса нет: старший этаж "\n'
    '              f"{starshiy_tf or \'?\'} не пришёл")\n'
)
NOVOE_2 = (
    '    if compass is None and not starshiy_prishyol:\n'
    '        print(f"[СТОЛ] ⚠️  компаса нет: старший этаж "\n'
    '              f"{starshiy_tf or \'?\'} не пришёл")\n'
    '    else:\n'
    '        # KOMPAS_PRICHINA_V1: этаж пришёл — значит молчание компаса\n'
    '        # имеет причину, и она лежит на столе в «вода_почему».\n'
    '        # Раньше эта причина не выходила наружу: жалобы нет,\n'
    '        # компаса нет, понять нечем. Теперь видно.\n'
    '        try:\n'
    '            _et = ""\n'
    '            if isinstance(_voda_etazhi, dict):\n'
    '                _et = ", ".join(f"{k} {v}"\n'
    '                                for k, v in _voda_etazhi.items())\n'
    '            elif _voda_etazhi:\n'
    '                _et = str(_voda_etazhi)\n'
    '            _rasklad = f"{compass or \'воды нет\'} · {_et} · {_voda_why}"\n'
    '            _klyuch = (symbol, timeframe, _rasklad)\n'
    '            if _klyuch not in _KOMPAS_SKAZANO:\n'
    '                _KOMPAS_SKAZANO.add(_klyuch)\n'
    '                _chto = compass if compass else "воды нет"\n'
    '                _hvost = _et or _voda_why or "причина не названа"\n'
    '                print(f"[КОМПАС] {symbol} {timeframe}: "\n'
    '                      f"{_chto} — {_hvost}")\n'
    '        except Exception as _e_kp:\n'
    '            print(f"[КОМПАС] сказать не вышло ({_e_kp}) — не беда")\n'
)

PRAVKI = [(STAROE_1, NOVOE_1), (STAROE_2, NOVOE_2)]


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет стол сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "stol.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("stol.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько stol.py:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
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

    kopiya = put.with_suffix(put.suffix + ".bak_kompas_prichina")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ причина компаса теперь видна:")
    print("    · нет воды — скажет, что показали W1 и MN1")
    print("    · есть компас — скажет, какой и на чём")
    print("    · по одному разу на расклад, лог не топит")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("Ищи в логе строчки [КОМПАС] — по ним будет видно, бывает ли")
    print("старшая вода вообще или этажи всегда спорят.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
