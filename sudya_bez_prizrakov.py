# -*- coding: utf-8 -*-
"""
sudya_bez_prizrakov.py   ·   MARKER: SUDYA_BEZ_PRIZRAKOV_V1

ЧТО ПРОИСХОДИТ ПОСЛЕ КАЖДОЙ СДЕЛКИ
-----------------------------------
    [МАЯК] A02 morj: показание={...} звал=True вывод=ЕСТЬ
    [МАЯК] A02 ЗАПИСЬ → {'дописано': False,
                         'причина': 'слот торговый_хаос/A02 пуст'}
    [МАЯК] A03 panic: показание={...} звал=True вывод=ЕСТЬ
    [МАЯК] A03 ЗАПИСЬ → {'дописано': False,
                         'причина': 'слот торговый_хаос/A03 пуст'}

Судья сенсоров честно посчитал вывод, пошёл его записывать — и не
нашёл кому. Так на каждой закрытой сделке: два готовых вывода в
пустоту.

ПОЧЕМУ
------
Сенсоров нет. В цехе `торговый_хаос` есть только слоты A06, A07, A08 —
папок A01…A04 не существует, постов у них тоже нет. Их убрали вместе
с Искрой ещё 06.08.

Но таблица `SENSOR_SLOTS` в коде их по-прежнему перечисляет, а в
масках Моржа и Паника до сих пор написано «торговый_хаос/A02» и
«A03» — маски пережили упразднение мест, как пережил его магик Локи.

Вреда для сделки нет: суд падать не умеет. Но опыт не копится, а мы
как раз собрались мерить, учатся ли трейдеры. Мерить нечем, если
половина выводов уходит в пустоту.

ЧТО ДЕЛАЕМ
----------
  1. Судья спрашивает, СУЩЕСТВУЕТ ли слот, прежде чем считать по нему
     вывод. Нет слота — пропускаем молча, одной строкой, без
     ежесделочного крика.
  2. Таблицу `SENSOR_SLOTS` НЕ вычищаем и механизм не ломаем: заведёшь
     сенсоры снова — всё заработает само, без правок.
  3. Маски Моржа и Паника гасим: они числятся работающими в местах,
     которых нет. Тот же порядок, что с магиком Локи — маска не
     должна переживать место.

ЧЕГО НЕ ДЕЛАЕМ
--------------
  · жителей не трогаем: Морж и Паник остаются в ковчеге со своей
    памятью, гаснет только рабочая маска;
  · выводы по A06-A08 не меняем — там места живые.

Идемпотентен, кладёт `.bak_prizrak_ГГГГММДД_ЧЧММСС`.

  py -3 sudya_bez_prizrakov.py           — сделать
  py -3 sudya_bez_prizrakov.py --suho    — только показать
"""

import ast
import json
import sys
import time
from pathlib import Path

MARKER = "SUDYA_BEZ_PRIZRAKOV_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ─────────────────── 1. судья: есть ли такой слот ───────────────────

H_STAROE = '''        for key, slot in SENSOR_SLOTS.items():'''

H_NOVOE = '''        # SUDYA_BEZ_PRIZRAKOV_V1: сперва спрашиваем, есть ли место.
        # Сенсоров убрали 06.08 вместе с Искрой — папок A01…A04 в цехе
        # нет, постов тоже. А таблица их всё перечисляла, и после
        # КАЖДОЙ сделки два готовых вывода уходили в пустоту:
        # «дописано: False, слот пуст». Таблицу не трогаем: заведёшь
        # сенсоры снова — заработает само.
        _est = _slot_sushchestvuet("торговый_хаос")
        _prizraki = [s for s in SENSOR_SLOTS.values() if not _est(s)]
        if _prizraki:
            print(f"[МАЯК] мест нет, пропускаю: {', '.join(_prizraki)}")
        for key, slot in SENSOR_SLOTS.items():
            if not _est(slot):
                continue'''

H_HVOST = '''

# ══════════════════════════════════════════════════════════════
# SUDYA_BEZ_PRIZRAKOV_V1 — есть ли такое место в цехе
# ══════════════════════════════════════════════════════════════

def _slot_sushchestvuet(ceh: str):
    """Вернёт проверялку: есть ли у цеха такой слот НА ДИСКЕ.

    Спрашиваем папку, а не маски и не посты: маска переживает
    упразднение места (так было и с магиком Локи), а пост у сенсоров
    не заводили вовсе. Папка со слотом — то, что есть или чего нет.

    Список считаем ОДИН раз на сделку и держим в замыкании: судья
    ходит по четырём сенсорам, и лазить на диск четырежды незачем.
    """
    imena = set()
    try:
        from pathlib import Path as _P
        _koren = _P(__file__).resolve().parent.parent / "GRONDHEIM_CITY"
        _d = _koren / "Биржа" / "цеха" / ceh / "слоты"
        if _d.is_dir():
            imena = {p.name for p in _d.iterdir() if p.is_dir()}
    except Exception as e:
        print(f"[МАЯК] слоты цеха не прочлись ({e}) — сужу как раньше")
        return lambda _s: True          # не знаем — не мешаем
    if not imena:
        return lambda _s: True
    return lambda s: s in imena
'''


# ─────────────────── 2. маски призраков ───────────────────

def gasit_maski(koren: Path):
    """Маска не должна переживать место, которого нет."""
    print("\n2. МАСКИ В НЕСУЩЕСТВУЮЩИХ МЕСТАХ")
    sloty_dir = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха")
    est = {}
    for ceh in sloty_dir.iterdir() if sloty_dir.is_dir() else []:
        d = ceh / "слоты"
        est[ceh.name] = ({p.name for p in d.iterdir() if p.is_dir()}
                         if d.is_dir() else set())

    tronuto = 0
    for f in sorted((koren / "GRONDHEIM_CITY" / "жители").glob(
            "*/*/маски/работа/mask.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not d.get("_активна"):
            continue
        ceh = (d.get("Workshop_ID") or "").strip()
        slot = (d.get("Turbo_Role") or "").strip()
        if not ceh or ceh not in est or not slot:
            continue
        if slot in est[ceh]:
            continue
        imya = f.parents[2].name
        print(f"   гашу      {imya:<10} {ceh}/{slot} — такого места нет")
        d["_активна"] = False
        d["Workshop_ID"] = None
        d["Turbo_Role"] = None
        d["magic"] = None
        if not SUHO:
            f.with_name(f.name + f".bak_prizrak_{SHTAMP}").write_text(
                f.read_text(encoding="utf-8"), encoding="utf-8")
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        tronuto += 1
    print(f"   → погашено: {tronuto}" if tronuto else "   → чисто")


# ─────────────────────────── механика ───────────────────────────

def nayti_koren() -> Path:
    for k in (Path(__file__).resolve().parent, Path.cwd()):
        for p in [k, *k.parents]:
            if (p / "GRONDHEIM_CITY").is_dir() and (p / "Биржа").is_dir():
                return p
    print("Не нашёл корень репозитория (нужны папки GRONDHEIM_CITY и Биржа).")
    zhdat_i_vyyti(1)


def zhdat_i_vyyti(kod=0):
    try:
        input("\nEnter — закрыть окно...")
    except EOFError:
        pass
    sys.exit(kod)


def main():
    koren = nayti_koren()
    print(f"Корень города: {koren}")
    if SUHO:
        print("СУХОЙ ПРОГОН — ничего не записываю.")

    print("\n1. СУДЬЯ СЕНСОРОВ")
    put = koren / "Биржа" / "hooks.py"
    text = put.read_text(encoding="utf-8")
    if MARKER in text:
        print("   уже стояло")
    elif text.count(H_STAROE) != 1:
        print(f"   мимо: якорь встретился {text.count(H_STAROE)} раз — "
              f"код НЕ тронут")
    else:
        novyy = text.replace(H_STAROE, H_NOVOE, 1)
        novyy = novyy.rstrip("\n") + "\n" + H_HVOST
        novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
            if not SUHO:
                put.with_name(put.name + f".bak_prizrak_{SHTAMP}").write_text(
                    text, encoding="utf-8")
                put.write_text(novyy, encoding="utf-8")
            print("   сделано   Биржа/hooks.py")
        except SyntaxError as e:
            print(f"   мимо: правка ломает синтаксис ({e.lineno}: {e.msg})")

    gasit_maski(koren)

    print("""
────────────────────────────────────────────────────────────────
ЧТО ИЗМЕНИТСЯ В ЛОГЕ
  Было — после каждой сделки четыре строки, две из них впустую:
      [МАЯК] A02 ЗАПИСЬ → {'дописано': False, 'причина': 'слот пуст'}

  Станет — одна строка на сделку:
      [МАЯК] мест нет, пропускаю: A01, A02, A03, A04

  Заведёшь сенсоры снова — судья увидит папки и заработает сам,
  никаких правок не понадобится.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
