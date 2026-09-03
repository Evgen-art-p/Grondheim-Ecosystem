# -*- coding: utf-8 -*-
# MARKER: UBORKA_03_09_V1
"""
УБОРКА МЁРТВОГО КОДА (03.09) — то, что было «показано, но не тронуто».

ПРОВЕРЕНО ПЕРЕД УДАЛЕНИЕМ (03.09, не по памяти — по коду)
    · council.py: _ISKRA и _SENSORS определены и нигде больше не
      читаются (грепом по всему файлу — ни одного обращения). Совет
      упразднён 06.08, троих будит cartridge_registry, эти константы
      остались от старого пути. _ARKHIV РЯДОМ — жив (используется в
      _ARKHIV на строке ~667), его не трогаем.
    · hooks.py: on_before_run() — старый вход СТАРОГО CSV/webhook-пути
      Совета. С 14.08 бары идут через rynok_novyy_bar (RUKA_RYNKA_V1).
      Ни одного вызова on_before_run по всему репо — только упоминание
      в комментарии tester_express.py, что этого вызова в тестерном
      пути не было.
    · Биржа/kalibrovka.py, mt5_feed_с_step_up.py, rezident_menedzher.py,
      strazh.py — из старого списка «под вопросом» (08.08) ТРИ уже
      унесены прежним uborshchik.py в _УБОРКА/20260813_163035/.
      kalibrovka.py остался и остаётся ЖИВЫМ — его читает vremya.py
      (`import kalibrovka; kalibrovka._SESSII`, торговые сессии). Этот
      файл НЕ трогаем — он не мёртвый.
    · ui_torg.py: ветки A01-A04 и чат с Моржом — НЕ ТРОГАЕМ этим
      патчем. Это отдельная, более крупная и более рискованная правка
      (UI-файл, много завязок) — заслуживает отдельного захода, не
      попутного.

Идемпотентен. .bak рядом с каждым правленым файлом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "UBORKA_03_09_V1"

ISKRA_SENSORS_STAR = '''
# Искра — голова, будится первой отдельно (ворота по её спуску).
_ISKRA = ("торговый_хаос", "A01", "run_iskra")

# сенсоры после Искры — порядок как в кнопке РЫНОК
_SENSORS = [
    ("A02", "торговый_хаос", "A02", "run_morj"),
    ("A03", "торговый_хаос", "A03", "run_panikyor"),
    ("A04", "торговый_хаос", "A04", "run_hans"),
]
'''
ISKRA_SENSORS_NOV = (
    "\n# UBORKA_03_09_V1: _ISKRA и _SENSORS убраны — не читались нигде\n"
    "# в репо после упразднения Совета 06.08 (кто будит кого, решает\n"
    "# cartridge_registry). _ARKHIV ниже жив, его не трогаем.\n"
)


def _nayti_birzhu() -> Path:
    """Папка Биржа/ — ищем от скрипта и от cwd."""
    kandidaty = []
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (koren / "Биржа", koren):
            if (p / "council.py").exists() and (p / "hooks.py").exists():
                if p not in kandidaty:
                    kandidaty.append(p)
    if len(kandidaty) == 1:
        return kandidaty[0]
    if not kandidaty:
        print("Не нашёл Биржа/council.py и Биржа/hooks.py рядом.")
        s = input("Перетащи сюда папку «Биржа» и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "council.py").exists():
            return p
        raise SystemExit("не та папка — там нет council.py")
    print("Нашёл несколько:")
    for i, p in enumerate(kandidaty, 1):
        print(f"  {i}. {p}")
    return kandidaty[int((input("которая? ").strip() or "1")) - 1]


def _ubrat_iskra_sensors(f: Path) -> str:
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже убрано"
    if ISKRA_SENSORS_STAR not in src:
        return "! не нашёл блок _ISKRA/_SENSORS дословно — файл правили, не трогаю"

    novyy = src.replace(ISKRA_SENSORS_STAR, ISKRA_SENSORS_NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    ast.parse(novyy)
    shutil.copy2(f, f.with_suffix(".py.bak_uborka"))
    f.write_text(novyy, encoding="utf-8")
    return "_ISKRA/_SENSORS убраны (.bak_uborka рядом)"


def _ubrat_on_before_run(f: Path) -> str:
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже убрано"

    zagolovok = "def on_before_run("
    i0 = src.find(zagolovok)
    if i0 == -1:
        return "! on_before_run не найден — похоже, уже убран раньше"

    # начало функции — с закомментированной строки-разделителя над def,
    # если она прямо перед ним; иначе с самого def
    nachalo = i0
    prefix = src[:i0]
    if prefix.rstrip("\n").endswith("\n"):
        pass  # пусто — просто берём с def

    i1 = src.find("\ndef ", i0 + len(zagolovok))
    if i1 == -1:
        return "! не нашёл конец функции (следующий def) — не трогаю"

    novyy = src[:nachalo] + src[i1 + 1:]  # +1 съедает ведущий \n перед следующим def
    novyy = (novyy[:nachalo].rstrip("\n") + "\n\n\n"
             f"# {MARKER}: on_before_run() убрана — старый CSV/webhook-путь,\n"
             "# ни одного вызова по репо с 14.08 (бары идут через\n"
             "# rynok_novyy_bar). # {MARKER} - marker\n\n\n"
             + novyy[nachalo:])

    ast.parse(novyy)
    shutil.copy2(f, f.with_suffix(".py.bak_uborka"))
    f.write_text(novyy, encoding="utf-8")
    return "on_before_run() убрана (.bak_uborka рядом)"


def main():
    birzha = _nayti_birzhu()
    print(f"\nБиржа: {birzha}\n")

    itog1 = _ubrat_iskra_sensors(birzha / "council.py")
    print(f"  council.py: {itog1}")

    try:
        itog2 = _ubrat_on_before_run(birzha / "hooks.py")
    except SyntaxError as e:
        itog2 = f"! после правки не разбирается ({e}) — файл НЕ тронут"
    print(f"  hooks.py: {itog2}")

    print("\nkalibrovka.py НЕ трогали — он живой, его читает vremya.py.")
    print("ui_torg.py (ветки A01-A04) НЕ трогали — отдельная задача.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
