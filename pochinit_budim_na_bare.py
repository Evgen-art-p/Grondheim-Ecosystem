# -*- coding: utf-8 -*-
# BUDIM_NA_SVOYOM_BARE_V1
"""
БУДИМ НА ТОМ БАРЕ, ГДЕ НЕКРОН ЗАКРЫЛСЯ

Слово Шефа: «некрон закрылся — он сформирован, трейдера будят. Некрон
стоит, и шагает уже новый бар в моменте». Так на живом рынке. А в
прогоне было не так.

ПРИЧИНА, найдена по коду. Курсор истории ставится на дату места — а
это дата НАЧАЛА бара. Машина времени отдаёт только то, что к моменту
уже ЗАКРЫЛОСЬ: бар `02:00` на H1 закрывается в `03:00`, то есть
позже курсора. Значит сам бар события городу ещё не виден, и он
работает по предыдущему — `01:00`.

Отсюда всё разом: некрон ищется на баре раньше события, кадр рисуется
без него, трейдера будят до того, как всё случилось, — и он честно
отвечает «жду ещё бар». Мы три дня чинили его словами, а виноват был
сдвиг курсора на один бар.

ЧТО ДЕЛАЕТ ПАТЧ. В прогоне курсор ставится на МОМЕНТ ЗАКРЫТИЯ бара
места, а не на его начало. Тогда город видит этот бар как последний
закрытый — ровно как на живом рынке, где некрон только что
сформировался, а следующий бар уже пошёл.

Всё остальное встаёт само: кадр рисуется с некроном, повод считается
по нему же, подпись совпадает.

БЕЗОПАСНОСТЬ: .bak_budim, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python pochinit_budim_na_bare.py --suho
    python pochinit_budim_na_bare.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "BUDIM_NA_SVOYOM_BARE_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

STAROE = '''                istoriya.postavit(data)'''

NOVOE = '''                # BUDIM_NA_SVOYOM_BARE_V1: курсор — на момент ЗАКРЫТИЯ
                # бара места, а не на его начало. Машина времени отдаёт
                # только закрытое: поставь курсор на начало — и сам бар
                # события окажется «ещё идущим», город возьмёт
                # предыдущий, а трейдера разбудят ДО того, как некрон
                # сформировался. Отсюда и его вечное «жду ещё бар».
                istoriya.postavit(_moment_zakrytiya(data, _tf))'''

TELO = '''

def _moment_zakrytiya(data_bara: str, etazh: str) -> str:
    """Момент, когда этот бар закрылся. Не вышло посчитать — отдаём
    как есть: лучше прежнее поведение, чем сломанный курсор."""
    try:
        from datetime import timedelta
        import istoriya as _ist
        import masshtab as _m
        t0 = _ist.kak_vremya(data_bara)
        minut = _m.minut(etazh)
        if t0 is None or not minut:
            return data_bara
        return (t0 + timedelta(minutes=minut)).strftime(_ist.FORMAT)
    except Exception as _e:
        print(f"[ПРОГОН] момент закрытия не посчитался ({_e}) — "
              f"ставлю курсор как раньше")
        return data_bara
'''


def main():
    print()
    print("БУДИМ НА СВОЁМ БАРЕ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
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
        print("   (нужна строка постановки курсора в прогоне по истории)")
        return
    novy = txt.replace(STAROE, NOVOE, 1)
    novy = novy.rstrip("\n") + "\n" + TELO + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    print("  курсор — на момент закрытия бара")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_budim"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_budim")
    print("Теперь некрон виден на том баре, где он закрылся.")
    print()


if __name__ == "__main__":
    main()
