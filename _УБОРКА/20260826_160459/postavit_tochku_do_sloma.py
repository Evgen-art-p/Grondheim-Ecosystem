# -*- coding: utf-8 -*-
"""
postavit_tochku_do_sloma.py · MARKER: TOCHKA_DO_SLOMA_V1

СЛОВО ШЕФА (20.08)
──────────────────
«Сколько у нас поймано точек ноль? Ровно столько должно быть от этих
точек волн. От истинных.»

Значит исходов у точки ровно два:

    цена ушла за точку  → точка не истинная, гаснет
    не ушла             → ждём её волну столько, сколько надо

Третьего быть не должно. А он был.

СЧЁТ, КОТОРЫЙ ЭТО ПОКАЗАЛ
─────────────────────────
EURUSD H4, 2700 баров ≈ 1.8 года:

    родилось точек ............. 89
    дожили до волны ............ 10
    умерли структурным сломом .. 54   ← честно: цена ушла за точку
    умерли «ритм угас» ......... 31   ← НАШЕ выдуманное число

Треть точек убивало правило, которого нет ни у Вильямса, ни у Котина,
ни в КАНОН_ВХОДА. Оно записано в самом коде как наша калибровка
(KALIBROVKA_POROGA_V1): «TWR нейтрален 3 бара подряд». Пятёрка,
тринадцать и тридцать четыре — из книги. Тройка — наша.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Смерть точки по угасшему ритму снимается. Нейтральный TWR больше не
хоронит точку — он остаётся показанием и попадает в ответ как есть,
чтобы трейдер видел, что ритм замер, и решал сам.

Структурный слом не тронут: цена закрылась за ценой точки — точка
гаснет, и по слову Шефа ниже родится новая, иногда на том же баре,
что обновил минимум.

Счётчик нейтральных баров остаётся считаться и лежать в столе — он
никому не мешает и пригодится, если однажды решим смотреть на ритм
глазом, а не числом.

ЧЕГО ЖДАТЬ ПОСЛЕ
────────────────
Точка станет жить дольше — ровно до слома. Волн от точек станет
примерно втрое больше: около двадцати в год на H4, три-четыре на
дневке. Это и есть счёт Шефа.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_tochku_do_sloma.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TOCHKA_DO_SLOMA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "hooks.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


YAKOR = '''        if _n >= 3:
            isk["alive"] = False
            isk["neutral_bars_count"] = 0
            save_trading_state(tstate)
            return {"alive": False,
                    "reason": f"TWR нейтрален {_n} бар(а) подряд — ритм угас во флэте",
                    "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1'''

NOV = '''        # TOCHKA_DO_SLOMA_V1: смерть по ритму СНЯТА.
        # Слово Шефа: сколько поймано точек — столько и должно быть от
        # них волн, от истинных. Значит исходов два: цена ушла за точку
        # (не истинная) или ждём её волну сколько надо. Третьего нет.
        # А это правило («3 бара нейтрали») — наше выдуманное число,
        # его нет ни у Вильямса, ни у Котина, ни в каноне. Оно убивало
        # 31 точку из 89 — треть, и все они могли оказаться истинными.
        # Нейтраль остаётся ПОКАЗАНИЕМ: счётчик считается и лежит в
        # столе, трейдер видит, что ритм замер, и решает сам.
        if False:
            isk["alive"] = False
            isk["neutral_bars_count"] = 0
            save_trading_state(tstate)
            return {"alive": False,
                    "reason": f"TWR нейтрален {_n} бар(а) подряд — ритм угас во флэте",
                    "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1'''

YAKOR2 = '''        return {"alive": True,
                "reason": f"TWR нейтрален {_n}/3 — ещё жива, считаю",'''

NOV2 = '''        return {"alive": True,
                "reason": f"TWR нейтрален {_n} бар(а) — жива, ритм замер",'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "hooks.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    for yak in (YAKOR, YAKOR2):
        if t.count(yak) != 1:
            print(f"✗ якорь найден {t.count(yak)} раз — жду ровно один")
            print(f"  {yak.strip().splitlines()[0][:70]}")
            return 1

    novyy = t.replace(YAKOR, NOV, 1).replace(YAKOR2, NOV2, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_doslома_{datetime.now():%Y%m%d_%H%M%S}"
                        .replace("слома", "sloma"))
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ точка живёт до слома (копия: {bak.name})")
    print("\nТеперь у точки ровно два исхода: слом или волна.")
    print("Волн станет примерно втрое больше — около двадцати в год на H4.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
