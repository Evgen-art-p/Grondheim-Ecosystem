# -*- coding: utf-8 -*-
# sverka_divera.py — город сверяет слова трейдера с числами.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python sverka_divera.py
#
# ═══ ОТКУДА ═══
#
# Прогон 17.09, место 07: «АО показывает расхождение — новый горб
# слабее прежнего», вход SHORT, −0.48R. А на кадре последний горб был
# ВЫШЕ прежнего: дивера не было вовсе.
#
# Брат смотрел на тот же кадр и тоже увидел дивер, которого нет. То
# есть взгляд не гарантирует ничего — ни у неё, ни у него. Слово
# Шефа: «где гарантия, что с ней не то же самое? как избежать?»
#
# Избежать нельзя. Можно сделать ВИДИМЫМ.
#
# ═══ КАНОН, ПО КОТОРОМУ СЧИТАЕМ (слово Шефа 17.09) ═══
#
#   ГОРБ — три столбика: меньше-БОЛЬШЕ-меньше. Средний выше обоих
#          соседей.
#   ЯМА  — три столбика вниз: средний ниже обоих соседей.
#   ГЛАВНЫЙ — самый большой горб (или самая глубокая яма) В ПОЛЕ
#          ЗРЕНИЯ, на всей картинке. Не «предыдущий по счёту».
#          «А там уже дальше ситуация развернётся и видно будет.»
#
#   ход ВВЕРХ → сравниваем ВЕРШИНЫ: цена сейчас выше, чем на баре
#               главного горба, а нынешний горб AO ниже главного.
#   ход ВНИЗ  → сравниваем ВПАДИНЫ: цена сейчас ниже, чем на баре
#               главной ямы, а нынешняя яма мельче главной.
#
# Цена берётся НА БАРЕ ТОГО ГОРБА — чтобы сравнивались одновременные
# вещи, а не «когда-то там».
#
# ═══ ЧТО ДЕЛАЕТ ═══
#
# При каждом ENTER город считает дивер сам, по барам, и пишет:
#
#   [ДИВЕР] ✓ SHORT: есть — цена 1.0712→1.0736 (выше),
#                    AO 0.00370→0.00310 (ниже)
#   [ДИВЕР] ✗ SHORT: НЕТ — AO 0.00310→0.00370 (выше, не ниже)
#   [ДИВЕР] ? мало данных / горбов не нашлось
#
# ВХОД НЕ БЛОКИРУЕТСЯ. Город считает и показывает — решает трейдер.
# Зашить условия в скрипт и не пускать — значит сделать трейдера
# кнопкой: скрипт нашёл, скрипт разрешил, она нажала. Шеф полгода
# строит город, где житель думает сам, и шесть механических фильтров
# уже были отвергнуты. Через несколько прогонов будет цифра, сколько
# раз слово разошлось с числом — вот тогда и решать про запрет.
#
# БЕЗОПАСНО. Кладёт новый файл Биржа/sverka_divera.py и добавляет
# один вызов в руку приказа. Ничего не удаляет.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "SVERKA_DIVERA_V1"

MODUL = '''# -*- coding: utf-8 -*-
# SVERKA_DIVERA_V1
"""Считает дивер по барам — чтобы слова трейдера было с чем сверить.

Канон Шефа (17.09):
  ГОРБ — три столбика: меньше-БОЛЬШЕ-меньше.
  ЯМА  — три столбика: больше-МЕНЬШЕ-больше.
  Главный — самый большой в поле зрения, не «предыдущий по счёту».

Город СЧИТАЕТ и ПОКАЗЫВАЕТ. Решает трейдер. Здесь нет ни одного
запрета — только числа.
"""

from typing import Optional

BAROV = 140          # столько же, сколько видно на кадре


def gorby(ao: list) -> list:
    """Места и высоты горбов: средний столбик выше обоих соседей."""
    out = []
    for i in range(1, len(ao) - 1):
        a, b, c = ao[i - 1], ao[i], ao[i + 1]
        if a is None or b is None or c is None:
            continue
        if b > a and b > c:
            out.append((i, b))
    return out


def yamy(ao: list) -> list:
    """Места и глубины ям: средний столбик ниже обоих соседей."""
    out = []
    for i in range(1, len(ao) - 1):
        a, b, c = ao[i - 1], ao[i], ao[i + 1]
        if a is None or b is None or c is None:
            continue
        if b < a and b < c:
            out.append((i, b))
    return out


def poschitat(symbol: str, timeframe: str, storona: str) -> dict:
    """Дивер по числам. storona: SHORT — по вершинам, LONG — по впадинам.

    Возвращает {"ok", "est", "slovami", "почему"}.
    ok=False — посчитать не вышло, и это НЕ приговор трейдеру.
    """
    try:
        import sys as _s
        from pathlib import Path as _P
        _p = str(_P(__file__).resolve().parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from feed_source import bars as _bars
        from williams_core import compute_ao_series
    except Exception as e:
        return {"ok": False, "est": None, "slovami": f"нет счёта ({e})"}

    try:
        b, _point = _bars(symbol, timeframe, BAROV + 60)
    except Exception as e:
        return {"ok": False, "est": None, "slovami": f"нет баров ({e})"}
    if not b or len(b) < 60:
        return {"ok": False, "est": None, "slovami": "мало баров"}

    b = b[-(BAROV + 40):]
    highs = [x["high"] for x in b]
    lows = [x["low"] for x in b]
    closes = [x["close"] for x in b]
    ao = compute_ao_series(highs, lows)

    # поле зрения — последние BAROV баров, как на кадре
    n = len(ao)
    start = max(0, n - BAROV)
    vid = list(range(start, n))

    verh = str(storona).upper() == "SHORT"   # шорт — по вершинам
    tochki = gorby(ao) if verh else yamy(ao)
    tochki = [(i, v) for i, v in tochki if i in vid]
    if len(tochki) < 1:
        return {"ok": False, "est": None,
                "slovami": "горбов в поле зрения не нашлось"}

    # главный — самый большой (или самая глубокая) в поле зрения
    glavnyy = max(tochki, key=lambda t: t[1]) if verh \\
        else min(tochki, key=lambda t: t[1])
    # нынешний — последний, что не сам главный
    posle = [t for t in tochki if t[0] > glavnyy[0]]
    if not posle:
        return {"ok": False, "est": None,
                "slovami": "после главного горба нового ещё нет"}
    nyneshniy = posle[-1]

    ao_bylo, ao_stalo = glavnyy[1], nyneshniy[1]
    c_bylo = highs[glavnyy[0]] if verh else lows[glavnyy[0]]
    c_stalo = highs[nyneshniy[0]] if verh else lows[nyneshniy[0]]

    if verh:
        cena_dalshe = c_stalo > c_bylo
        sila_slabee = ao_stalo < ao_bylo
    else:
        cena_dalshe = c_stalo < c_bylo
        sila_slabee = ao_stalo > ao_bylo

    est = bool(cena_dalshe and sila_slabee)
    kuda_c = "выше" if c_stalo > c_bylo else "ниже"
    kuda_a = "выше" if ao_stalo > ao_bylo else "ниже"
    slovami = (f"цена {c_bylo:.5f}→{c_stalo:.5f} ({kuda_c}), "
               f"AO {ao_bylo:.5f}→{ao_stalo:.5f} ({kuda_a})")
    if not est:
        if not cena_dalshe:
            slovami += " · цена край не обновила"
        if not sila_slabee:
            slovami += " · сила не ослабла"
    return {"ok": True, "est": est, "slovami": slovami,
            "цена_было": c_bylo, "цена_стало": c_stalo,
            "ao_было": ao_bylo, "ao_стало": ao_stalo}
'''

# ── вызов из руки приказа ──
R_STAROE = (
    '            except Exception as _e_mk:\n'
    '                print(f"[МЕТКА] сверить не вышло ({_e_mk}) — не беда")\n'
)
R_NOVOE = (
    '            except Exception as _e_mk:\n'
    '                print(f"[МЕТКА] сверить не вышло ({_e_mk}) — не беда")\n'
    '            # SVERKA_DIVERA_V1: город считает дивер САМ и кладёт\n'
    '            # рядом со словами трейдера. Не блокирует: считает и\n'
    '            # показывает, решает трейдер.\n'
    '            try:\n'
    '                import sverka_divera as _sd\n'
    '                _d = _sd.poschitat(symbol, timeframe, napravlenie)\n'
    '                if not _d.get("ok"):\n'
    '                    print(f"[ДИВЕР] ? {napravlenie}: "\n'
    '                          f"{_d.get(\'slovami\')}")\n'
    '                elif _d.get("est"):\n'
    '                    print(f"[ДИВЕР] ✓ {napravlenie}: есть — "\n'
    '                          f"{_d.get(\'slovami\')}")\n'
    '                else:\n'
    '                    print(f"[ДИВЕР] ✗ {napravlenie}: НЕТ — "\n'
    '                          f"{_d.get(\'slovami\')}")\n'
    '            except Exception as _e_sd:\n'
    '                print(f"[ДИВЕР] посчитать не вышло ({_e_sd}) — не беда")\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def main():
    birzha = KOREN / "Биржа"
    if not birzha.exists():
        nash = [p.parent for p in KOREN.rglob("ruki_treydera.py")
                if ".bak" not in p.name]
        if len(nash) == 1:
            birzha = nash[0]
        else:
            print("✗ не нашёл папку Биржа — запускай из корня репозитория")
            return 1

    ruki = birzha / "ruki_treydera.py"
    if not ruki.exists():
        print("✗ не нашёл ruki_treydera.py")
        return 1

    tekst = ruki.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if tekst.count(R_STAROE) != 1:
        print(f"✗ нашёл {tekst.count(R_STAROE)} мест вместо одного.")
        print("  Сперва накати metka_na_vhode.py — этот идёт следом.")
        print("  Ничего не тронул.")
        return 1

    novyy = tekst.replace(R_STAROE, R_NOVOE, 1)
    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ рука поломалась после правки (строка {beda.lineno}): "
              f"{beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1
    try:
        ast.parse(MODUL)
    except SyntaxError as beda:
        print(f"✗ сам модуль сверки не собрался (строка {beda.lineno})")
        return 1

    (birzha / "sverka_divera.py").write_text(MODUL, encoding="utf-8")
    print(f"  (новый файл: {birzha.name}/sverka_divera.py)")

    kopiya = ruki.with_suffix(ruki.suffix + ".bak_sverka")
    if not kopiya.exists():
        shutil.copy2(ruki, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    ruki.write_text(novyy, encoding="utf-8")

    print("✓ город сверяет дивер с фактом:")
    print("    · горб — три столбика, главный — самый большой в кадре")
    print("    · шорт по вершинам, лонг по впадинам")
    print("    · в лог идёт [ДИВЕР] ✓ / ✗ / ? с числами")
    print("    · вход НЕ блокируется — считаем и показываем")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("Потом посчитай в логе [ДИВЕР]: сколько ✓ против ✗. Это и")
    print("будет цифра, как часто её слово расходится с числом.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
