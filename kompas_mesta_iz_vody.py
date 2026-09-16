# -*- coding: utf-8 -*-
# kompas_mesta_iz_vody.py — место берёт компас оттуда же, что и трейдер.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python kompas_mesta_iz_vody.py
#
# ═══ ЧТО НАШЛОСЬ ═══
#
# В прогоне 16.09 компас ЖИВОЙ: в логе 38 раскладов — 16 BULL, 3 BEAR,
# 19 «воды нет», со всеми числами по W1 и MN1. Трейдер его видит: он
# приходит столом.
#
# А в места.jsonl компас = None во ВСЕХ 160 местах. Включая те бары,
# где в логе стоял BULL.
#
# Потому что это две разные вещи с одним именем:
#
#   · компас НА СТОЛЕ — из воды, по структуре W1 и MN1. Живой.
#   · компас В МЕСТЕ  — из md["global_bias"], то есть направление
#                        РАБОЧЕГО этажа по вееру Аллигатора.
#
# Ровно та подмена, которую Шеф уже вычистил из стола (KOMPAS_
# CHESTNYY_V1: «трейдер думал, что видит верх, а видел свой же
# этаж»). Из стола убрали — в местах осталось. А так как веер больше
# не источник компаса, global_bias теперь никем не заполняется, и в
# месте лежит пустота.
#
# ═══ ЧЕМ ЭТО ПЛОХО ═══
#
# Трейдеру — ничем: он смотрит стол. А вот проверить нечем. В отчёте
# компас пуст всегда, и связать «вошла при BULL» или «вошла, когда
# этажи спорят» с результатом сделки невозможно. Именно того разбора,
# ради которого Шеф просил расклад в отчётах, сделать нельзя.
#
# ═══ ЧТО СТАВИМ ═══
#
# Место берёт компас ОТТУДА ЖЕ, откуда его берёт трейдер — из воды,
# на дату этого самого места (вода обрезает старшие бары по ней и в
# будущее не заглядывает, закон тестера соблюдён).
#
# Заодно в место кладётся «вода_почему» — чем именно вода такая. В
# отчёте будет видно не только «BULL», но и на чём он стоит.
#
# Не вышло спросить воду — работает как раньше, через рабочий этаж.
# Место от этого не пропадает, ничего не ломается.
#
# ЧЕГО НЕ ДЕЛАЕТ: на решения трейдера не влияет никак. Стол Синди не
# меняется ни на букву — это запись для отчёта, не для неё.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт kandidaty.py.bak_kompas_mesta.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "KOMPAS_MESTA_IZ_VODY_V1"

STAROE = (
    'def _dobrat_kompas(k: dict, bars: list, symbol: str, tf: str, point: float):\n'
    '    """ISKATEL_SVOY_ETAZH_V1: компас НАЙДЕННОМУ месту, по одному разу\n'
    '    на место, а не на каждый перебранный бар. Не вышло — остаётся то,\n'
    '    что дал рабочий этаж; место от этого не пропадает."""\n'
    '    try:\n'
    '        from williams_core import build_market_data\n'
    '        md = build_market_data(bars, symbol=symbol, timeframe=tf,\n'
    '                               point=point, starshiy=True)\n'
    '        if md and md.get("global_bias"):\n'
    '            k["компас"] = md.get("global_bias")\n'
    '    except Exception as e:\n'
    '        print(f"[ИСКАТЕЛЬ] компас месту не досчитан ({e}) — не беда")\n'
    '    return k\n'
)

NOVOE = (
    'def _dobrat_kompas(k: dict, bars: list, symbol: str, tf: str, point: float):\n'
    '    """KOMPAS_MESTA_IZ_VODY_V1: компас месту — ОТТУДА ЖЕ, откуда его\n'
    '    берёт трейдер: из ВОДЫ, по структуре двух старших этажей.\n'
    '\n'
    '    Раньше здесь стоял компас РАБОЧЕГО этажа (веер Аллигатора,\n'
    '    md["global_bias"]) — та самая подмена, что была вычищена из\n'
    '    стола как тихое враньё. Из стола убрали, а в местах осталась;\n'
    '    и с тех пор, как веер перестал быть источником компаса,\n'
    '    global_bias никем не заполняется — в месте лежала пустота.\n'
    '\n'
    '    Спрашиваем воду НА ДАТУ ЭТОГО МЕСТА: она обрезает старшие бары\n'
    '    по ней и в будущее не заглядывает — закон тестера цел.\n'
    '\n'
    '    Это запись ДЛЯ ОТЧЁТА. На стол трейдера и на его решения не\n'
    '    влияет ничем.\n'
    '    """\n'
    '    try:\n'
    '        from global_anchor import global_trend\n'
    '        st = global_trend(symbol, tf, as_of_date=k.get("дата"))\n'
    '        b = (st or {}).get("bias")\n'
    '        k["компас"] = b if b in ("BULL", "BEAR") else None\n'
    '        _why = (st or {}).get("why") or ""\n'
    '        if _why:\n'
    '            k["вода_почему"] = _why\n'
    '        return k\n'
    '    except Exception as e:\n'
    '        print(f"[ИСКАТЕЛЬ] вода месту не ответила ({e}) — "\n'
    '              f"беру рабочий этаж")\n'
    '    # Запасной путь — как было раньше.\n'
    '    try:\n'
    '        from williams_core import build_market_data\n'
    '        md = build_market_data(bars, symbol=symbol, timeframe=tf,\n'
    '                               point=point, starshiy=True)\n'
    '        if md and md.get("global_bias"):\n'
    '            k["компас"] = md.get("global_bias")\n'
    '    except Exception as e:\n'
    '        print(f"[ИСКАТЕЛЬ] компас месту не досчитан ({e}) — не беда")\n'
    '    return k\n'
)


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет искателя сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "kandidaty.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("kandidaty.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько kandidaty.py:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/kandidaty.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if tekst.count(STAROE) != 1:
        print(f"✗ нашёл {tekst.count(STAROE)} мест вместо одного —")
        print("  искатель мог измениться. Ничего не тронул.")
        print("  Скажи Брату, поправим по месту.")
        return 1

    novyy = tekst.replace(STAROE, NOVOE, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_kompas_mesta")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ место берёт компас из воды:")
    print("    · тот же компас, что видит трейдер на столе")
    print("    · спрашивается на дату места, в будущее не заглядывает")
    print("    · рядом кладётся, на чём вода стоит")
    print("    · не вышло — работает по-старому, место не пропадает")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("В места.jsonl у мест должен появиться компас: BULL, BEAR")
    print("или пусто, когда этажи спорят. Тогда станет видно главное:")
    print("при каком компасе она входит и чем это кончается.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
