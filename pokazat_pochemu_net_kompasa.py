# -*- coding: utf-8 -*-
# KOMPAS_GOVORIT_POCHEMU_V1
"""
КОМПАС ГОВОРИТ, ПОЧЕМУ ЕГО НЕТ

«Компаса нет: старший этаж W1 не пришёл» повторяется на каждом баре
всех прогонов и на всех инструментах. При этом РУКОЙ тот же W1
приходит прекрасно — в логе видно, как по просьбе трейдера
подгрузился EURUSDWeekly.csv.

Значит спотыкается не источник, а путь, которым за старшим этажом
ходит стол. Где именно — по нынешнему логу не понять: он говорит
только «не пришёл».

ЧТО ДЕЛАЕТ ПАТЧ. Ничего не чинит — заставляет компас объяснять отказ.
В `Биржа/global_anchor.py` добавляется строка с тем, что произошло:
сколько баров дал источник, сколько осталось после обрезки по дате
прогона и на чём остановились. Тогда причина станет видна с первого
же бара, а не после моих догадок.

Строка печатается ОДИН раз на пару «инструмент+этаж» — лог не
заливает.

БЕЗОПАСНОСТЬ: .bak_kompas2, идемпотентен, синтаксис до записи,
`--suho` не трогает диск. Работу компаса не меняет ни на шаг.

    python pokazat_pochemu_net_kompasa.py --suho
    python pokazat_pochemu_net_kompasa.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KOMPAS_GOVORIT_POCHEMU_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "global_anchor.py"

STAROE = '''    if not sbars or point is None or len(sbars) < 40:'''

NOVOE = '''    # KOMPAS_GOVORIT_POCHEMU_V1: раньше отказ был немым — «не пришёл»,
    # и всё. Теперь видно, на чём споткнулись: источник не дал баров,
    # обрезка по дате прогона съела всё, или их просто мало.
    try:
        _skolko = len(sbars or [])
        _klyuch_zh = (symbol, senior)
        if _skolko < 40 or point is None:
            if _klyuch_zh not in _POCHEMU_SKAZALI:
                _POCHEMU_SKAZALI.add(_klyuch_zh)
                if not _syrykh:
                    _p = "источник не дал ни одного бара"
                elif _skolko == 0:
                    _p = (f"источник дал {_syrykh}, но обрезка по дате "
                          f"{as_of_date} не оставила ни одного")
                elif point is None:
                    _p = f"баров {_skolko}, но цена шага (point) неизвестна"
                else:
                    _p = (f"баров всего {_skolko} — меньше сорока, "
                          f"мерить веер не на чем")
                print(f"[КОМПАС] {symbol} {senior}: {_p}")
    except Exception:
        pass

    if not sbars or point is None or len(sbars) < 40:'''

# запоминаем «сырое» число до обрезки
STAROE2 = '''    sbars, point = _sprosit_starshiy(symbol, senior)'''
NOVOE2 = '''    sbars, point = _sprosit_starshiy(symbol, senior)
    _syrykh = len(sbars or [])          # KOMPAS_GOVORIT_POCHEMU_V1'''

STAROE3 = '''_PUSTO_ZHIVYOT = 60.0          # секунд молчать, не переспрашивая'''
NOVOE3 = '''_PUSTO_ZHIVYOT = 60.0          # секунд молчать, не переспрашивая
_POCHEMU_SKAZALI: set = set()  # KOMPAS_GOVORIT_POCHEMU_V1: один раз на пару'''


def main():
    print()
    print("ПОЧЕМУ НЕТ КОМПАСА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
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
    for imya, staroe, novoe in (("память об отказе", STAROE3, NOVOE3),
                                ("число до обрезки", STAROE2, NOVOE2),
                                ("объяснение", STAROE, NOVOE)):
        if novy.count(staroe) != 1:
            print(f"  {imya}: ОТКАЗ — якорь встречается "
                  f"{novy.count(staroe)} раз(а)")
            return
        novy = novy.replace(staroe, novoe, 1)
        sdelano.append(imya)

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    for s in sdelano:
        print(f"  {s}: вставлено")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_kompas2"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: global_anchor.py.bak_kompas2")
    print("Теперь компас скажет, на чём споткнулся.")
    print()


if __name__ == "__main__":
    main()
