# -*- coding: utf-8 -*-
"""
popravit_otkat_ot_volny.py   ·   MARKER: OTKAT_OT_VOLNY_V1

ЧТО ЧИНИМ
---------
Смысловая ошибка в вывеске третьего места входа. Везде, где место
названо коротко, стоит «первый откат К НОВОЙ ВОЛНЕ». Правильно
наоборот: волна 1 пошла от точки, дошла до края и кончилась; цена
вернулась к линиям баланса — это откат ОТ волны. Кончился откат —
вот там вход.

Тело текста в знаниях описано верно, врёт только заголовок и короткая
строка в бумаге трейдера. Заучивают именно короткое — оттого во всех
47 ответах годового прогона повторялась заученная формула, а не то,
что лежало на столе.

ЧТО ТРОГАЕМ
-----------
  · знания/VHODY.md во всех слотах всех цехов Биржи  (заголовок + тело)
  · Академия/руда/тексты/VHODY.md                    (та же копия)
  · промпт.md во всех слотах всех цехов Биржи        (одна строка)

ЧЕГО НЕ ТРОГАЕМ, НАМЕРЕННО
--------------------------
  · метки жителей (`2_метки/metki.json`). Метка — СОБСТВЕННОЕ слово
    человека и дата, когда он его сказал. Переписать её значит подделать
    его память. Школу правим, а выбор житель объявит заново сам —
    и в истории меток будет видно, передумал он или повторил.
  · отчёты прошлых прогонов — это факт того, что было.

Идемпотентен: второй запуск скажет «уже стоит». Перед правкой кладёт
рядом копию `.bak_otkatot_ГГГГММДД_ЧЧММСС`.

Запуск из корня репозитория:  py -3 popravit_otkat_ot_volny.py
Сухой прогон (ничего не пишет):  py -3 popravit_otkat_ot_volny.py --suho
"""

import sys
import time
from pathlib import Path

MARKER = "OTKAT_OT_VOLNY_V1"
METKA = f"<!-- {MARKER} -->"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv

# ─────────────────────────── замены ───────────────────────────
# (что ищем, на что меняем). Якоря длинные и дословные: не нашёлся —
# файл не трогаем и говорим об этом вслух, а не правим наугад.

ZAMENY_VHODY = [
    (
        "## Место третье: первый откат к новой волне",
        "## Место третье: конец первого отката ОТ новой волны",
    ),
    (
        "Первая волна прошла, цена откатила к линиям, откат кончился — и вот\n"
        "теперь входишь.",

        "Волна 1 пошла от точки, дошла до своего края и кончилась. Цена\n"
        "вернулась к линиям баланса — это откат ОТ волны, а не к ней. Пока он\n"
        "идёт, входа нет. Кончился откат — вот там ты и входишь.",
    ),
]

ZAMENY_PROMPT = [
    (
        "по первой волне нового движения, без подтверждения. Третье — на первом\n"
        "откате к этой волне, позже и дешевле по риску.",

        "по первой волне нового движения, без подтверждения. Третье — в конце\n"
        "первого отката ОТ этой волны, позже и дешевле по риску.",
    ),
]


# ─────────────────────────── дороги ───────────────────────────

def nayti_koren() -> Path:
    """Корень репо ищем сами: сначала рядом со скриптом, потом вверх."""
    kandidaty = [Path(__file__).resolve().parent, Path.cwd()]
    for k in kandidaty:
        for p in [k, *k.parents]:
            if (p / "GRONDHEIM_CITY").is_dir():
                return p
    print("Не нашёл папку GRONDHEIM_CITY — положи скрипт в корень репозитория.")
    zhdat_i_vyyti(1)


def sobrat_celi(koren: Path):
    """Все копии, а не одну: VHODY.md лежит в каждом слоте отдельно."""
    goroda = koren / "GRONDHEIM_CITY"
    vhody = sorted(goroda.glob("Биржа/цеха/*/слоты/*/знания/VHODY.md"))
    akadem = goroda / "Академия" / "руда" / "тексты" / "VHODY.md"
    if akadem.is_file():
        vhody.append(akadem)
    # Бумаги конторы (архивариус, исполнитель) про входы не говорят
    # вовсе — берём только те, где эта строка вообще есть.
    prompty = [p for p in sorted(goroda.glob("Биржа/цеха/*/слоты/*/промпт.md"))
               if "Про входы главное" in p.read_text(encoding="utf-8")]
    return vhody, prompty


# ─────────────────────────── работа ───────────────────────────

def pravit(put: Path, zameny) -> str:
    """Вернёт: 'сделано' | 'уже' | 'мимо: …' """
    text = put.read_text(encoding="utf-8")

    if MARKER in text:
        return "уже"

    ne_nashlos = [staroe for staroe, _ in zameny if staroe not in text]
    if ne_nashlos:
        kusok = ne_nashlos[0].split("\n")[0][:60]
        return f"мимо: не нашёл якорь «{kusok}…»"

    novyy = text
    for staroe, novoe in zameny:
        novyy = novyy.replace(staroe, novoe)
    novyy = novyy.rstrip("\n") + "\n\n" + METKA + "\n"

    if SUHO:
        return "сделано (сухой прогон, не записано)"

    bak = put.with_name(put.name + f".bak_otkatot_{SHTAMP}")
    bak.write_text(text, encoding="utf-8")
    put.write_text(novyy, encoding="utf-8")
    return "сделано"


def zhdat_i_vyyti(kod=0):
    """Windows, двойной клик: окно не должно схлопнуться молча."""
    try:
        input("\nEnter — закрыть окно...")
    except EOFError:
        pass
    sys.exit(kod)


def main():
    koren = nayti_koren()
    print(f"Корень города: {koren}")
    if SUHO:
        print("СУХОЙ ПРОГОН — ничего не записываю, только показываю.\n")

    vhody, prompty = sobrat_celi(koren)
    if not vhody and not prompty:
        print("Ни одного VHODY.md и ни одной бумаги не нашлось — проверь путь.")
        zhdat_i_vyyti(1)

    itogi = {"сделано": 0, "уже": 0, "мимо": 0}

    print(f"\nЗНАНИЯ — {len(vhody)} копий VHODY.md:")
    for p in vhody:
        rezultat = pravit(p, ZAMENY_VHODY)
        print(f"  {rezultat:<22} {p.relative_to(koren)}")
        itogi["мимо" if rezultat.startswith("мимо") else
              ("уже" if rezultat == "уже" else "сделано")] += 1

    print(f"\nБУМАГА ТРЕЙДЕРА — {len(prompty)} копий промпт.md:")
    for p in prompty:
        rezultat = pravit(p, ZAMENY_PROMPT)
        print(f"  {rezultat:<22} {p.relative_to(koren)}")
        itogi["мимо" if rezultat.startswith("мимо") else
              ("уже" if rezultat == "уже" else "сделано")] += 1

    print("\n" + "─" * 62)
    print(f"поправлено: {itogi['сделано']}   уже стояло: {itogi['уже']}   "
          f"не тронуто: {itogi['мимо']}")
    print("─" * 62)

    print("""
МЕТКИ ЖИТЕЛЕЙ НЕ ТРОНУТЫ — так задумано.
У Ильи в метке лежит старая формулировка, переписанная им с вывески.
Спроси его заново, когда правка встанет: повторит — это его выбор,
передумает — будет видно в истории меток, что и когда изменилось.
Посмотреть, у кого что записано:  py -3 vybor_pokazat.py
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
