# -*- coding: utf-8 -*-
# FLET_LEKAR_V2
"""
ЛЕКАРЬ: снимает неверную первую версию и кладёт вторую.

Первая версия (FLET_NE_ZAPRET_V1) написала в бумагу трейдера то,
чего Брат не проверял: «в конце хода пасть закрыта всегда, линии
успели сойтись». Шеф поправил — Аллигатор конец хода показывает не
так; там ангуляция и комплексный осмотр в нужном масштабе, и на
этом уровне про Аллигатора лучше не говорить вовсе.

Патч уже был накачен, поэтому обычным скриптом не обойтись: сперва
надо вернуть файлы к тому, что было ДО первой версии, и только потом
класть вторую.

═══ ЧТО ДЕЛАЕТ ═══

Для каждого слота, для промпта и для паттернов:

  1. уже стоит V2 — не трогает;
  2. стоит V1 — берёт `.bak_flet` (файл, каким он был до первой
     версии), проверяет, что в нём нет ни V1, ни V2, возвращает
     его на место — и только тогда кладёт V2;
  3. не стоит ничего — просто кладёт V2;
  4. бэкапа нет, а V1 стоит — НИЧЕГО НЕ ТРОГАЕТ и говорит об этом.
     Лучше оставить как есть, чем чинить вслепую.

Что кладёт V2:
  · промпт — абзац про фазы пасти («спит — флэт, работы нет»,
    зевнула, раскрыта, ангулированная) убирается целиком;
  · знания — флэт остаётся как был, вместе с «уйти»; добавлена одна
    мысль: решает не пасть, а цена слева, горб и бар.

Про то, что делают линии в конце хода, не сказано ничего.

Запускать из корня репозитория:
    python pochinit_flet.py

Идемпотентен. Есть --suho: показать, ничего не трогая.
"""
from __future__ import annotations

import sys
from pathlib import Path

V1 = "FLET_NE_ZAPRET_V1"
V2 = "FLET_NE_ZAPRET_V2"
SUHO = "--suho" in sys.argv

SLOTY = Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

PROMT_OLD = """**Про пасть Аллигатора — простое чтение фазы (уточнено 05.09).**
Спит — флэт, работы нет. Зевнула — движение только начинается.
Раскрыта — тренд идёт. Сильно растянутая, ангулированная пасть часто
(не всегда) сопровождает конец импульса — это отдельное наблюдение,
а не условие для входа: пасть не проверяется как ворота «если так, то
входи», её просто читают — компасом, а не сигналом, как и остальные
приборы.

"""

PROMT_NEW = ""

PAT_OLD = """Разворотных баров здесь найдётся сколько угодно, и ни один не работает.
Правильный ответ — уйти."""

PAT_NEW = """Разворотных баров здесь найдётся сколько угодно, и ни один не работает.
Правильный ответ — уйти.

**Но решает не пасть.** Кончился ли ход, отвечают цена слева, горб и
бар: слева был ход, цена ушла далеко и стоит на пределе, горб мельче
прежнего, рядом приседающий и разворотный бар — это конец хода, а не
флэт, как бы ни лежали линии. Флэт — это когда слева не приходило
ничего: ход не кончился, его не было."""


def nayti_koren() -> Path:
    kandidat = Path(__file__).resolve().parent
    for papka in [kandidat, *kandidat.parents]:
        if (papka / SLOTY).is_dir():
            return papka
    print("Не нашёл папку слотов рядом со скриптом.")
    print("Положи скрипт в корень репозитория и запусти оттуда.")
    input("Enter — закрыть...")
    sys.exit(1)


def lechit(fayl: Path, staroe: str, novoe: str, imya: str) -> str:
    if not fayl.exists():
        return f"{imya}: нет файла"

    tekst = fayl.read_text(encoding="utf-8")

    if V2 in tekst:
        return f"{imya}: уже вторая версия, не трогаю"

    otkat = ""
    if V1 in tekst:
        bak = fayl.with_suffix(fayl.suffix + ".bak_flet")
        if not bak.exists():
            return (f"{imya}: ⚠ стоит первая версия, а бэкапа "
                    f"{bak.name} рядом нет — НЕ трогаю, скажи Брату")
        bylo = bak.read_text(encoding="utf-8")
        if V1 in bylo or V2 in bylo:
            return (f"{imya}: ⚠ в бэкапе {bak.name} уже есть патч — "
                    "НЕ трогаю, скажи Брату")
        if not SUHO:
            fayl.write_text(bylo, encoding="utf-8")
        tekst = bylo
        otkat = "первая версия снята, "

    skolko = tekst.count(staroe)
    if skolko != 1:
        return f"{imya}: ⚠ {otkat}совпадений {skolko}, нужно 1 — стоп"

    novyy = tekst.replace(staroe, novoe, 1).rstrip("\n") + f"\n\n<!-- {V2} -->\n"

    if SUHO:
        return f"{imya}: ✔ {otkat}готов к правке (сухой прогон)"

    bak2 = fayl.with_suffix(fayl.suffix + ".bak_flet2")
    if not bak2.exists():
        bak2.write_text(tekst, encoding="utf-8")
    fayl.write_text(novyy, encoding="utf-8")
    return f"{imya}: ✔ {otkat}вторая версия на месте"


def main() -> None:
    koren = nayti_koren()
    print(f"Корень: {koren}\n")

    for papka in sorted((koren / SLOTY).iterdir()):
        if not papka.is_dir():
            continue
        promt = papka / "промпт.md"
        patterny = papka / "знания" / "PATTERNY.md"
        if not promt.exists() and not patterny.exists():
            continue
        print(f"{papka.name}:")
        print("   ", lechit(promt, PROMT_OLD, PROMT_NEW, "промпт"))
        print("   ", lechit(patterny, PAT_OLD, PAT_NEW, "паттерны"))

    print("\nПроверить глазами: в промпте не должно остаться абзаца")
    print("«Про пасть Аллигатора — простое чтение фазы».")
    input("\nEnter — закрыть...")


if __name__ == "__main__":
    main()
