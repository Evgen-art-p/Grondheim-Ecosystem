# -*- coding: utf-8 -*-
# MENEDZHER_TOLKO_CEHA_V1
"""
ПАТЧ · Менеджер: только цеха, копия без вопросов.

Догоняет MENEDZHER_KARTRIDZHEY_V1. Ставится ПОСЛЕ него.

ДВЕ ПРАВКИ, обе по слову Шефа.

1. КОНТОРА УХОДИТ ИЗ МЕНЕДЖЕРА
   Строка, с которой ничего нельзя сделать: ни размножить, ни вынуть,
   ни назначить — назначение живёт на странице Работы. Менеджер про
   сменные картриджи; контора часть квартала. Разное — значит и
   показывать в разных местах.

   Запреты в razmnozhit()/ubrat() ОСТАЮТСЯ ремнём безопасности: если
   контора однажды попадёт в список другим путём, кнопки откажут.

2. КОПИЯ БЕЗ ПОЛЕЙ ВВОДА
   Менеджер ничего не создаёт — он тиражирует готовое. Оригинал выбран
   слева, это и есть весь выбор. Имя следует из оригинала:

       торговый_хаос  →  торговый_хаос_2   (занято → _3, _4 …)
       название       →  «Торговый хаос 2»

   Хвост _N у оригинала срезается, иначе копия копии вышла бы
   торговый_хаос_2_2. Переименовать потом — строка в манифесте.

ИДЕМПОТЕНТНОСТЬ
    Маркер, .bak, всё-или-ничего по трём кускам. Второй запуск молчит.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "MENEDZHER_TOLKO_CEHA_V1"

# ── 1. ceha(): конторы в список не кладём ────────────────────

P1_STAR = '''    out.sort(key=lambda c: (c["квартал"], c["вид"] != "контора", c["имя"]))
    return out'''

P1_NOV = '''    # MENEDZHER_TOLKO_CEHA_V1: конторы тут не место. Менеджер про
    # сменные картриджи, а контора — часть квартала: её не размножают,
    # не вынимают и жителя на неё сажают не здесь. Мёртвую строку в
    # списке не держим.
    out = [c for c in out if c.get("вид") != "контора"]
    out.sort(key=lambda c: (c["квартал"], c["имя"]))
    return out'''

# ── 2. razmnozhit(): имя подбираем сами ──────────────────────

P2_STAR = '''def razmnozhit(iz: dict, imya: str, nazvanie: str) -> tuple:
    """Снять копию цеха один в один. Оригинал не трогаем."""
    # MENEDZHER_KARTRIDZHEY_V1: контору не размножают — она одна на
    # квартал по устройству. Копия ложится РЯДОМ с оригиналом, то есть
    # в его же квартал: цех привязан к зданию и судье, копия в чужом
    # квартале была бы сиротой.
    if iz.get("вид") == "контора":
        return False, "контора не размножается — она одна на квартал"
    imya = _chistoe(imya)
    if not imya:
        return False, "у цеха должно быть имя"
    cel = Path(iz["папка"]).parent / imya
    if cel.exists():
        return False, f"цех «{imya}» уже есть"'''

P2_NOV = '''def _imya_kopii(papka: Path) -> tuple:
    """Первое свободное имя рядом с оригиналом. MENEDZHER_TOLKO_CEHA_V1.

    Хвост _N срезаем, иначе копия копии вышла бы торговый_хаос_2_2.
    """
    roditel = papka.parent
    baza = re.sub(r"_\\d+$", "", papka.name)
    n = 2
    while (roditel / f"{baza}_{n}").exists():
        n += 1
    return f"{baza}_{n}", n


def razmnozhit(iz: dict) -> tuple:
    """Снять копию цеха один в один. Оригинал не трогаем.

    MENEDZHER_TOLKO_CEHA_V1: имени не спрашиваем. Менеджер не создаёт
    картриджи, он тиражирует готовые — оригинал уже выбран, это весь
    выбор. Имя следует из оригинала, переименовать можно потом.
    """
    # MENEDZHER_KARTRIDZHEY_V1: контору не размножают — она одна на
    # квартал по устройству. Копия ложится РЯДОМ с оригиналом, то есть
    # в его же квартал: цех привязан к зданию и судье, копия в чужом
    # квартале была бы сиротой.
    if iz.get("вид") == "контора":
        return False, "контора не размножается — она одна на квартал"
    papka = Path(iz["папка"])
    if not papka.is_dir():
        return False, "папки оригинала нет"
    imya, nomer = _imya_kopii(papka)
    nazvanie = re.sub(r"\\s+\\d+$", "",
                      (iz.get("название") or papka.name)).strip()
    nazvanie = f"{nazvanie} {nomer}"
    cel = papka.parent / imya
    if cel.exists():
        return False, f"цех «{imya}» уже есть"'''

# ── 3. страница: полей ввода нет ─────────────────────────────

P3_STAR = '''            ui.html('<div class="c-podpis">снять копию</div>')
            ui.label("Копия идёт чистой: без данных, журналов и стола. "
                     "Новый цех начинает свою жизнь.").style(
                "color:rgba(255,255,255,0.4); font-size:0.72rem;")
            novoe_imya = ui.input("Имя папки (без пробелов)").props(
                "dark dense outlined").style(
                "width:100%; font-size:0.78rem; margin-top:6px;")
            novoe_nazv = ui.input("Название по-человечески").props(
                "dark dense outlined").style(
                "width:100%; font-size:0.78rem; margin-top:6px;")

            def _kopiya():
                ok, msg = razmnozhit(c, novoe_imya.value or "",
                                     (novoe_nazv.value or "").strip())
                ui.notify(("🧩 " if ok else "⚠ ") + msg,
                          color="positive" if ok else "negative")
                if ok:
                    sost["вybrano"] = (c.get("квартал", ""),
                                       _chistoe(novoe_imya.value or ""))
                risovat_spisok()
                risovat_kartu()'''

P3_NOV = '''            # MENEDZHER_TOLKO_CEHA_V1: полей ввода нет. Имя копии
            # следует из оригинала — показываем, каким оно будет.
            budet, _ = _imya_kopii(Path(c["папка"]))
            ui.html('<div class="c-podpis">снять копию</div>')
            ui.label("Копия идёт чистой: без данных, журналов и стола. "
                     "Новый цех начинает свою жизнь.").style(
                "color:rgba(255,255,255,0.4); font-size:0.72rem;")
            ui.label(f"ляжет рядом как  {budet}").style(
                "color:rgba(139,233,253,0.7); font-size:0.74rem; "
                "font-family:monospace; margin-top:4px;")

            def _kopiya():
                novoe, _n = _imya_kopii(Path(c["папка"]))
                ok, msg = razmnozhit(c)
                ui.notify(("🧩 " if ok else "⚠ ") + msg,
                          color="positive" if ok else "negative")
                if ok:
                    sost["вybrano"] = (c.get("квартал", ""), novoe)
                risovat_spisok()
                risovat_kartu()'''

PRAVKI = [
    ("конторы вон из списка", P1_STAR, P1_NOV),
    ("razmnozhit без имени", P2_STAR, P2_NOV),
    ("страница без полей ввода", P3_STAR, P3_NOV),
]


def _teper() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def naiti_koren() -> Path:
    starty = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starty:
        for kand in [start, *start.parents]:
            if (kand / "GRONDHEIM_CITY" / "локации").is_dir() \
                    and (kand / "ГОРОД" / "rabota.py").is_file():
                return kand
    raise SystemExit("Не нашёл корень репо. Запусти из корня "
                     "Grondheim-Ecosystem.")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

    koren = naiti_koren()
    print(f"Корень: {koren}\n")
    put = koren / "ГОРОД" / "ui_ceha.py"

    if not put.exists():
        raise SystemExit("нет ГОРОД/ui_ceha.py")
    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("ui_ceha.py: уже пропатчен, не трогал")
        return
    if "MENEDZHER_KARTRIDZHEY_V1" not in tekst:
        raise SystemExit(
            "Сперва накати menedzher_kartridzhey.py — этот патч догоняющий.")

    ne_nashlos = [i for i, s, _ in PRAVKI if s not in tekst]
    if ne_nashlos:
        print("ui_ceha.py: НЕ НАШЁЛ куски: " + "; ".join(ne_nashlos) +
              ". Ничего не менял.")
        return

    novyy = tekst
    for _, star, nov in PRAVKI:
        if novyy.count(star) != 1:
            print("ui_ceha.py: кусок встречается не один раз — не рискую.")
            return
        novyy = novyy.replace(star, nov, 1)

    bak = put.with_suffix(put.suffix + f".bak_{_teper()}")
    shutil.copyfile(put, bak)
    put.write_text(novyy, encoding="utf-8")
    print(f"ui_ceha.py: пропатчен ({len(PRAVKI)} правки), "
          f"старый в {bak.name}")
    print("\nГотово. Перезапусти приложение и открой /ceha:\n"
          "  в списке только цеха, у копии полей нет.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
