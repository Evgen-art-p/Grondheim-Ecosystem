# -*- coding: utf-8 -*-
# MARKER: RAZGOVOR_PRO_SVOY_INSTRUMENT_V1
"""
В РАЗГОВОРЕ ТРЕЙДЕР СМОТРИТ СВОЙ ИНСТРУМЕНТ, А НЕ ПОЛКУ.

ПОЙМАНО ШЕФОМ (03.09), живьём:
    шапка:  «Илья — GBPUSD D1»
    кадр:   «EURUSD · D1 · РЕАЛ · 2025.01.31»
    Илья:   «Аллигатор на дневном графике EURUSD сейчас спит...»
    лог:    [ПУЗЫРЬ] нажали: A06
            [CORE] GBPUSDH4.csv ... GBPUSDDaily.csv   ← его инструмент
            [CORE] _Point=1e-05 (EURUSD)              ← а смотрит евро
    Шеф: «на реальном рынке евро ищет, когда британец».

ПРИЧИНА — ПОЛОВИНА ПЕРЕЕЗДА
    Кадр справа уже починен патчем VZGLYAD_KAZHDOGO_V1: «раньше брали
    пару с полки — и на экране висел один общий кадр, одинаковый для
    всех троих, хотя работают они разными инструментами. Теперь кадр
    про того, чей пузырёк нажат». Для этого есть готовая рука
    `_para_aktivnogo()`: для A06/A07/A08 берёт пару из `vybor`
    (инструмент и этаж самого трейдера), для прочих — полку.

    А разговор остался на старом пути (RAZGOVOR_SO_STOLOM_V1):
        _rynok_seychas = _aktivnyy_rynok()      # полка загрузчика
    Замысел тогда был верный — «чтобы смотрел на то же, что и Шеф»,
    пока кадр был общий. После VZGLYAD_KAZHDOGO_V1 он стал вредным:
    Шеф смотрит кадр трейдера, трейдер отвечает про полку. Оттого и
    «евро, когда британец».

ЧТО ДЕЛАЕТСЯ
────────────
Разговор берёт ту же пару, что и кадр — через `_para_aktivnogo()`.
Для трейдера это ЕГО инструмент и ЕГО этаж. Для всех прочих
собеседников (Морж, Паникёр, Ганс, Архивариус, Исполнитель)
`_para_aktivnogo` сама возвращает полку — для них ничего не меняется.
Если у трейдера пара почему-то не читается — честно откатываемся на
полку, как было, разговор не рвём.

ЧТО НЕ ТРОГАЕТСЯ
    Кадр, вахта, кнопка РЫНОК, состав под пузырьками, сам `vybor` —
    не менялись. Правится одна строка выбора инструмента для чата.

Правит Биржа/ui_torg.py. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "RAZGOVOR_PRO_SVOY_INSTRUMENT_V1"

STAR = '''                _rynok_seychas = _aktivnyy_rynok()'''

NOV = '''                # RAZGOVOR_PRO_SVOY_INSTRUMENT_V1: берём ту же пару,
                # что и кадр справа — у трейдера СВОЙ инструмент и
                # свой этаж. Раньше здесь была полка загрузчика, и
                # Илья на GBPUSD отвечал про EURUSD, потому что евро
                # было выбрано слева. Для не-трейдеров
                # _para_aktivnogo сама вернёт полку — им как было.
                try:
                    _s_sv, _t_sv, _chey_sv, _net_sv = _para_aktivnogo()
                    _rynok_seychas = ((_s_sv, _t_sv) if (_s_sv and _t_sv)
                                      else _aktivnyy_rynok())
                except Exception as _e_sv:
                    print(f"[РЫНОК] пара трейдера не прочиталась "
                          f"({_e_sv}) — беру полку")
                    _rynok_seychas = _aktivnyy_rynok()'''


def _nayti_birzhu() -> Path:
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (koren / "Биржа", koren):
            if (p / "ui_torg.py").exists():
                return p
    print("Не нашёл Биржа/ui_torg.py.")
    s = input("Перетащи сюда папку «Биржа» и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if (p / "ui_torg.py").exists():
        return p
    raise SystemExit("не та папка — там нет ui_torg.py")


def main():
    f = _nayti_birzhu() / "ui_torg.py"
    src = f.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"\n{f}: уже накачено")
        return
    if STAR not in src:
        print(f"\n{f}: ! не нашёл строку выбора рынка для чата — не трогаю")
        return
    if src.count(STAR) != 1:
        print(f"\n{f}: ! строка встретилась {src.count(STAR)} раз(а) — "
              f"ожидал одну, не трогаю")
        return

    novyy = src.replace(STAR, NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_svoy_instr"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}: разговор идёт про инструмент трейдера (.bak_svoy_instr рядом)")
    print("   Теперь Илья на GBPUSD и отвечать будет про GBPUSD.")
    print("   Не-трейдеры (Морж, Архивариус, Исполнитель) — как было, с полки.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
