# -*- coding: utf-8 -*-
# PERVYY_UROVEN_CHISTO_V1
"""
НОВАЯ БУМАГА ТРЕЙДЕРА · первый уровень начисто

Слово Шефа 12.09: «сделаем по уровням — и нам проще, и трейдерам.
Первый уровень: некрон-сигнал, AO, приседающий. И ведут по барам
пальцем. Одно окно рабочее».

ЗАЧЕМ ПЕРЕПИСЫВАТЬ, А НЕ ДОПИСАТЬ. Нынешняя бумага — 31 килобайт,
склеенных из полутора десятков наших правок за неделю. В ней слоями
лежит то, что мы сами же потом отменяли, и рядом — второй уровень:
волны, точка ноль, три места входа, структура. Трейдер читает всё
это разом и честно пытается применить.

ЧТО В НОВОЙ, по Вильямсу и по слову Шефа:

    цель уровня — НЕ ПОТЕРЯТЬ
    некрон      — сигнал
    AO          — сила импульса
    приседающий — напряжение
    и ведут пальцем по барам

Вход — окружение бара: заявка за один край, стоп за другой. Один
этаж, одно окно. Условий ровно три, остальное — выдумка.

ЧТО УШЛО НА ПОЛКУ (не пропало — ждёт своего уровня): волны и их
номера, точка ноль, три места входа, пасть и ангуляция, разбор
структуры. Про это в новой бумаге сказано прямо, отдельным разделом,
чтобы он знал: оно есть, но не сейчас.

СТАРАЯ БУМАГА СОХРАНЯЕТСЯ как `промпт.md.bak_uroven1` у каждого
слота — вернуть можно в любой момент.

КУДА КЛАСТЬ: этот патч — в корень репы. Рядом с ним должен лежать
`promt_pervyy_uroven.md` (сам текст бумаги) — тоже в корень, патч
разложит его по слотам сам.

    python postavit_novuyu_bumagu.py --suho
    python postavit_novuyu_bumagu.py

`шесть·проверено·до·корня`
"""
import shutil
import sys
from pathlib import Path

MARKER = "PERVYY_UROVEN_CHISTO_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
ISTOCHNIK = _REPO / "promt_pervyy_uroven.md"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"


def main():
    print()
    print("НОВАЯ БУМАГА · ПЕРВЫЙ УРОВЕНЬ"
          + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    if not ISTOCHNIK.exists():
        print("!! рядом нет promt_pervyy_uroven.md — положи его в корень")
        return
    novyy = ISTOCHNIK.read_text(encoding="utf-8")
    if MARKER not in novyy:
        print("!! в файле бумаги нет метки — это не она")
        return
    print(f"  новая бумага: {len(novyy)} знаков")

    if not SLOTY.exists():
        print("!! слотов нет — запускать из корня репы")
        return

    tronuto = 0
    for slot in ("A06", "A07", "A08"):
        p = SLOTY / slot / "промпт.md"
        if not p.exists():
            print(f"  {slot}: файла нет — кладу новую")
        else:
            staraya = p.read_text(encoding="utf-8", errors="ignore")
            if MARKER in staraya:
                print(f"  {slot}: уже стоит")
                continue
            print(f"  {slot}: было {len(staraya)} знаков → станет "
                  f"{len(novyy)}")
            if not SUHO:
                shutil.copy2(p, p.with_suffix(".md.bak_uroven1"))
        if not SUHO:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(novyy, encoding="utf-8")
        tronuto += 1

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Заменено бумаг: {tronuto}. Старые — .bak_uroven1")
    print("Некрон · AO · приседающий. И пальцем по барам.")
    print()


if __name__ == "__main__":
    main()
