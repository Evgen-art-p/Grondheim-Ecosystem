# -*- coding: utf-8 -*-
# STOP_I_VZGLYAD_V1
"""
СТОП СЛЫШНО · ВЗГЛЯД ТОЛЬКО ПО НАЖАТИЮ

ДВЕ БЕДЫ ИЗ ПРОГОНА 10.09.

1. КНОПКА СТОП НЕ ОСТАНАВЛИВАЕТ. Флаг она ставит, цикл его читает —
   а прогон идёт дальше. Причина: между барами цикл не отдаёт
   управление интерфейсу. Пока идёт сплошной ход (места собраны с
   пометкой «подряд»), внутренний цикл с ожиданием не выполняется
   вовсе, и клик по кнопке просто не успевает обработаться. Лечится
   одной строкой: короткая передышка на каждом месте — цикл событий
   успевает принять нажатие, и следующая же проверка его увидит.

2. ГРАФИКИ НЕ СХОДЯТСЯ. Трейдер работает M5, а ему досылается D1 с
   подписью «показал Шеф» — хотя Шеф ничего не показывал. Это моя
   вчерашняя недоделка: кадр помечался как «взгляд Шефа» при ЛЮБОЙ
   отрисовке, в том числе автоматической — при старте, при смене
   инструмента, при переключении тумблера. Теперь помечается только
   то, что Шеф показал РУКОЙ, нажав «Взгляд».

БЕЗОПАСНОСТЬ: .bak_stopvzg, идемпотентен, синтаксис до записи,
`--suho` не трогает диск. Каждая правка отдельно.

    python pochinit_stop_i_vzglyad.py --suho
    python pochinit_stop_i_vzglyad.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "STOP_I_VZGLYAD_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

PRAVKI = [
    ("СТОП слышно",
     '''            for data, _sl, _sym, _tf, k in mesta:
                if state.get("stop_requested"):''',
     '''            for data, _sl, _sym, _tf, k in mesta:
                # STOP_I_VZGLYAD_V1: передышка для интерфейса. Без неё
                # на сплошном ходу цикл не отпускает поток, нажатие
                # СТОП не успевает обработаться — и прогон идёт дальше,
                # хотя проверка флага стоит прямо ниже.
                await asyncio.sleep(0)
                if state.get("stop_requested"):'''),

    ("взгляд помечается только рукой",
     '''            try:
                from datetime import datetime as _dtv
                _t_zk["vzglyad_shefa"] = {
                    "путь": str(put),
                    "подпись": f"{symbol} {tf}",
                    "когда": _dtv.now().isoformat(timespec="seconds"),
                }
            except Exception:
                pass''',
     '''            # STOP_I_VZGLYAD_V1: помечаем только то, что Шеф показал
            # РУКОЙ. Раньше метка вешалась на любую отрисовку — и
            # трейдеру, работающему на M5, досылался автоматический D1
            # с подписью «показал Шеф». Графики не сходились.
            if state.pop("взгляд_рукой", False):
                try:
                    from datetime import datetime as _dtv
                    _t_zk["vzglyad_shefa"] = {
                        "путь": str(put),
                        "подпись": f"{symbol} {tf}",
                        "когда": _dtv.now().isoformat(timespec="seconds"),
                    }
                except Exception:
                    pass'''),

    ("кнопка Взгляд поднимает руку",
     '''                    ui.button("👁 Взгляд", on_click=lambda: pokazat_kadr()).props(''',
     '''                    # STOP_I_VZGLYAD_V1: рука Шефа — вот она.
                    ui.button("👁 Взгляд",
                              on_click=lambda: (
                                  state.__setitem__("взгляд_рукой", True),
                                  pokazat_kadr())[-1]).props('''),
]


def main():
    print()
    print("СТОП И ВЗГЛЯД" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if "VZGLYAD_DOHODIT_V1" not in txt:
        print("!! сперва postavit_vzglyad_dohodit.py")
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

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_stopvzg"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_stopvzg")
    print()


if __name__ == "__main__":
    main()
