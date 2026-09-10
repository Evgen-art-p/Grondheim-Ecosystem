# -*- coding: utf-8 -*-
# METKA_NAZYVAET_KADR_V1 — метка перестаёт быть безымянной
"""
КОНТРОЛЬНАЯ МЕТКА НАЗЫВАЕТ, ЧЕЙ ЭТО КАДР

БЕДА. Метка ставится на КАЖДУЮ отрисовку, а за один взгляд кадр
рисуется несколько раз. В логе получается пачка:

    [КАДР] контрольная метка: JC51
    [КАДР] контрольная метка: TH10
    [КАДР] контрольная метка: ST81

и какая из них ушла трейдеру — неизвестно. Спросить «какой код в
углу?» можно, а проверить ответ нечем: любой из трёх подойдёт.
Долг записан ещё 08.09 и до сих пор мешает разбирать каждый спор.

Живой случай 10.09: трейдер рассказывал про NVDA H4, а кадр рисовался
по USDCNH — это выяснилось только по строкам `_Point` рядом, то есть
случайно. Метка про инструмент молчала.

ЧТО ДЕЛАЕТ ПАТЧ. Одна строка в `Биржа/grafik.py`: рядом с меткой
печатается инструмент и этаж, а сам код ставится и НА КАРТИНКУ,
и в лог — как было.

    [КАДР] контрольная метка: JC51 · USDCNH H1

Теперь вопрос «какой код в углу?» становится проверкой: по ответу
видно не только ВИДИТ ли он картинку, но и КАКУЮ.

ЧЕГО НЕ ТРОГАЕТ: сам код метки, её вид на картинке, рисование.

БЕЗОПАСНОСТЬ: .bak_metka, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python pochinit_metku_kadra.py --suho
    python pochinit_metku_kadra.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "METKA_NAZYVAET_KADR_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "grafik.py"

STAROE = "        print(f'[КАДР] контрольная метка: {_kod}')"

NOVOE = ("        # METKA_NAZYVAET_KADR_V1: метка без имени кадра\n"
         "        # бесполезна — за один взгляд их печатается несколько,\n"
         "        # и ответ трейдера не с чем сверить.\n"
         "        _chey = f\"{symbol} {timeframe}\".strip() or \"?\"\n"
         "        print(f'[КАДР] контрольная метка: {_kod} · {_chey}')")


def main():
    print()
    print("МЕТКА НАЗЫВАЕТ КАДР" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
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

    print("  печать метки — поправлена")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_metka"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: grafik.py.bak_metka")
    print("Теперь в логе видно, к какому кадру относится код.")
    print()


if __name__ == "__main__":
    main()
