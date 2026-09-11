# -*- coding: utf-8 -*-
# KADR_PO_BARU_GORODA_V1
"""
КАДР НЕ ЗАГЛЯДЫВАЕТ ВПЕРЁД

НАЙДЕНО 11.09. Трейдера спрашивают на баре `2025.01.02 04:00`, а
кадр под вопросом подписан `05:00` — на час вперёд. Значит он
смотрит на бар, которого в момент вопроса ещё НЕ БЫЛО.

В прогоне по истории это не мелочь: он подглядывает в будущее. Пусть
на один бар — но весь прогон после этого врёт в его пользу, и любая
статистика по нему ничего не стоит.

ПРИЧИНА. `grafik.kadr` берёт последние бары источника и про бар, на
котором стоит город, не знает ничего. В живом режиме разницы нет —
последний закрытый и есть текущий. А в прогоне курсор успевает
сдвинуться, и кадр рисуется уже по новому бару.

ЧТО ДЕЛАЕТ ПАТЧ. Кадр обрезается по бару города: рисуем историю по
тот бар, на котором город стоит сейчас, и ни одним дальше. Город
говорит свой бар через общую площадь — то же место, откуда рука
приказа берёт отметку, так что третьей правды не появится.

Города не спросили или он молчит — рисуем как раньше. В живом режиме
ничего не меняется.

БЕЗОПАСНОСТЬ: .bak_kadrbar, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python pochinit_kadr_po_baru.py --suho
    python pochinit_kadr_po_baru.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KADR_PO_BARU_GORODA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "grafik.py"

STAROE = '''    if not bs:
        return None
    highs = [x["high"] for x in bs]'''

NOVOE = '''    # KADR_PO_BARU_GORODA_V1: не заглядываем вперёд. В прогоне курсор
    # успевает сдвинуться, и кадр рисовался по бару, которого в момент
    # вопроса ещё не было, — трейдер подглядывал в будущее.
    try:
        from hooks import load_trading_state as _lts
        _bar_goroda = str(((_lts() or {}).get("рынок") or {}).get("бар") or "")
        if _bar_goroda:
            _do = [b for b in bs if str(b.get("date", "")) <= _bar_goroda]
            # обрезаем ВСЕГДА, когда что-то осталось. Порога тут быть
            # не должно: «мало баров — нарисую как есть» означало бы
            # снова показать будущее, а короткий честный кадр лучше
            # длинного, но подглядывающего.
            if _do:
                if len(_do) != len(bs):
                    print(f"[КАДР] обрезал по бару города {_bar_goroda}: "
                          f"{len(bs)} → {len(_do)}")
                bs = _do
            else:
                print(f"[КАДР] по бару города {_bar_goroda} баров нет — "
                      f"кадра не будет")
                return None
    except Exception as _e_bar:
        print(f"[КАДР] бар города не спросился ({_e_bar}) — рисую как есть")

    if not bs:
        return None
    highs = [x["high"] for x in bs]'''


def main():
    print()
    print("КАДР ПО БАРУ ГОРОДА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()
    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")
    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if txt.count(STAROE) != 1:
        print(f"!! якорь встречается {txt.count(STAROE)} раз(а) — не трогаю")
        return
    novy = txt.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    print("  обрезка по бару города — вставлена")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_kadrbar"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: grafik.py.bak_kadrbar")
    print("Теперь он видит ровно тот бар, на котором его спросили.")
    print()


if __name__ == "__main__":
    main()
