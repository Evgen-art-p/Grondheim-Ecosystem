# -*- coding: utf-8 -*-
# DATY_PO_CHELOVECHESKI_V1 — число.месяц.год и честная пустота
"""
ДАТЫ ПО-ЧЕЛОВЕЧЕСКИ, ПУСТОТА — С ОБЪЯСНЕНИЕМ

СЛУЧАЙ 10.09. Шеф задал тестеру отрезок `2016.03.16 → 2016.30.04`,
прогон ответил «Ничего не нашлось в истории — пусто», и решили, что
тестер не находит трейдера. А данных по EURUSD M5 просто нет за
2016 год — они с 2025.03.12 по 2026.07.16. Прогон честно прошёл по
пустоте и честно промолчал о причине.

Плюс вторая дата вообще нечитаемая: `2016.30.04` — тридцатый месяц.
Разбор молча вернул пусто и пошёл «от сегодня», ничего не сказав.

ЧТО ДЕЛАЕТ ПАТЧ, три правки в `Биржа/ui_torg.py`:

 1. ПОДСКАЗКА В ПОЛЯХ — `с 28.04.2026` и `по 30.07.2026`. Разбор и
    раньше понимал оба порядка, а подсказка звала писать наоборот.
    Теперь зовёт по-человечески: число, месяц, год.

 2. НЕЧИТАЕМАЯ ДАТА — говорится вслух, в чат, а не только в консоль:
    «тридцатого месяца не бывает». Раньше молча уходила в пустоту.

 3. ПУСТОЙ ПРОГОН ОБЪЯСНЯЕТСЯ. Вместо «пусто» — что есть в истории
    и почему заданный отрезок в неё не попал.

БЕЗОПАСНОСТЬ: .bak_daty, идемпотентен, синтаксис до записи,
`--suho` не трогает диск. Каждая правка ставится отдельно.

    python pochinit_daty_testera.py --suho
    python pochinit_daty_testera.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "DATY_PO_CHELOVECHESKI_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

PRAVKI = [
    ("подсказка «с»",
     'value="", placeholder="с 2026.04.28",',
     'value="", placeholder="с 28.04.2026",   # DATY_PO_CHELOVECHESKI_V1'),

    ("подсказка «по»",
     'value="", placeholder="по 2026.07.30",',
     'value="", placeholder="по 30.07.2026",  # DATY_PO_CHELOVECHESKI_V1'),

    ("нечитаемая дата",
     '''        try:
            itog = f"{int(god):04d}.{int(mes):02d}.{int(den):02d} {vremya}"
        except ValueError:
            print(f"[ПРОГОН] дату «{s}» не разобрал — иду от сегодня")
            return ""''',
     '''        try:
            god, mes, den = int(god), int(mes), int(den)
            # DATY_PO_CHELOVECHESKI_V1: «2016.30.04» — тридцатый месяц.
            # Раньше такое молча уходило в пустоту, и прогон шёл не
            # туда, куда просили, ничего не сказав.
            if not (1 <= mes <= 12 and 1 <= den <= 31):
                raise ValueError(f"месяц {mes}, день {den}")
            itog = f"{god:04d}.{mes:02d}.{den:02d} {vremya}"
        except ValueError as _e:
            print(f"[ПРОГОН] дату «{s}» не разобрал ({_e}) — иду от сегодня")
            try:
                ui.notify(f"дату «{s}» не понял — пишется "
                          f"число.месяц.год", type="warning")
            except Exception:
                pass
            return ""'''),

    ("пустой прогон объясняется",
     '''            state["chat_history"].append({
                "role": "system",
                "content": "Ничего не нашлось в истории — пусто."})''',
     '''            # DATY_PO_CHELOVECHESKI_V1: «пусто» само по себе врёт —
            # похоже, будто сломан прогон. Чаще всего история просто
            # в другом отрезке. Говорим, какая она есть.
            _skazat = "Ничего не нашлось в истории — пусто."
            try:
                _kraya = []
                for _sl2 in (state.get("tester_sloty") or []):
                    _s2, _t2 = _para_slota(_sl2)
                    _v2, _ = _src_bars(_s2, _t2, 0)
                    if _v2:
                        _kraya.append(f"{_s2} {_t2}: история с "
                                      f"{_v2[0].get('date', '?')} по "
                                      f"{_v2[-1].get('date', '?')}")
                if _kraya:
                    _zadano = (state.get("progon_ot_daty") or "").strip()
                    _do = (state.get("progon_po_datu") or "").strip()
                    _otrez = (f" Задан отрезок {_zadano or 'с начала'} → "
                              f"{_do or 'до конца'}.")
                    _skazat = ("В заданном отрезке баров нет. " +
                               " · ".join(_kraya) + "." + _otrez)
            except Exception:
                pass
            state["chat_history"].append({
                "role": "system", "content": _skazat})'''),
]


def main():
    print()
    print("ДАТЫ ПО-ЧЕЛОВЕЧЕСКИ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")
    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return

    novy, sdelano = txt, []
    for imya, staroe, novoe in PRAVKI:
        n = novy.count(staroe)
        if n != 1:
            print(f"  {imya}: ОТКАЗ — якорь встречается {n} раз(а)")
            continue
        novy = novy.replace(staroe, novoe, 1)
        sdelano.append(imya)

    if not sdelano:
        print("Ни одного якоря — файл не тронут.")
        return

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return

    for s in sdelano:
        print(f"  {s}: поправлено")
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_daty"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_daty")
    print()


if __name__ == "__main__":
    main()
