# -*- coding: utf-8 -*-
# KOROTKIY_BLANK_V1
"""
КОРОТКИЙ БЛАНК — два поля вместо одиннадцати.

    python patch_korotkiy_blank.py --suho    посмотреть
    python patch_korotkiy_blank.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_korotkiy.

ЧТО БЫЛО НЕ ТАК

    Я вывалил в карточку весь бланк разом: название, квартал, цех,
    слот, чем занят, судья, требования, условия, движок, обязанности —
    одиннадцать полей на одном экране. Заполнять такое никто не станет,
    и правильно: на сотне мест это не работа, а анкета.

ЧТО СТАЛО

    Видно ДВА поля: название и «чем занят» одной строкой. Этого хватает,
    чтобы место было опознаваемым.

    Квартал, цех и слот перестали быть полями вовсе. Их не пишут руками —
    они приходят от локации и картриджа. Теперь они просто подписаны
    строчкой под названием: где стоит и от какого картриджа.

    Всё остальное — обязанности, судья, требования, условия, движок —
    уехало под «подробнее». Свёрнуто. Нужно — раскрыл и дописал; не
    нужно — не мешает и глаз не ест.

    Причина найма и увольнения осталась одним полем: без неё трудовая
    история немая.

ЧЕГО ПАТЧ НЕ ТРОГАЕТ
    Ни механизм, ни дерево, ни поля документа. Только то, что показано
    на экране: в самом посте все поля как были.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
STRANICA = KOREN / "ГОРОД" / "ui_rabota.py"
MARKER = "# KOROTKIY_BLANK_V1 - marker"
BAK = ".bak_korotkiy"

# ── 1. поля делятся на видимые и убранные ────────────────────
STAROE_POLYA = '''POLYA = [
    ("название", "Название должности"),
    ("квартал", "Квартал"),
    ("цех", "Цех"),
    ("слот", "Слот"),
    ("чем_занят", "Чем занят — одной строкой"),
    ("судья", "Судья — чем меряется работа"),
    ("требования", "Требования"),
    ("условия", "Условия"),
    ("движок", "Движок (модуль, который умеет работать)"),
]
'''
NOVOE_POLYA = '''# KOROTKIY_BLANK_V1: на виду только то, что и правда пишут руками.
# Квартал, цех и слот сюда не попадают вовсе — они приходят от локации
# и картриджа, руками их писать незачем.
POLYA = [
    ("название", "Название должности"),
    ("чем_занят", "Чем занят — одной строкой"),
]

# под «подробнее» — свёрнуто, пусто по умолчанию, никого не держит
POLYA_ESHCHE = [
    ("судья", "Судья — чем меряется работа"),
    ("требования", "Требования"),
    ("условия", "Условия"),
    ("движок", "Движок (модуль, который умеет работать)"),
]
'''

# ── 2. карточка: два поля, остальное под «подробнее» ─────────
STAROE_KARTA = '''            polya_ui = {}
            with ui.element("div").style(
                    "display:grid; grid-template-columns:1fr 1fr; gap:8px;"):
                for klyuch, podpis in POLYA:
                    znach = post.get(klyuch, "") if est else (
                        m.get(klyuch, "") if klyuch in
                        ("квартал", "цех", "слот") else
                        (m["название"] if klyuch == "название" else ""))
                    polya_ui[klyuch] = ui.input(podpis, value=znach or "").props(
                        "dark dense outlined").style("font-size:0.78rem;")
            ui.html('<div class="rab-podpis">обязанности — по одной в строке</div>')
            obyaz = ui.textarea(
                value="\\n".join(post.get("обязанности", []) or [])).props(
                "dark dense outlined").style("width:100%; font-size:0.78rem;")

            def _sobrat() -> dict:
                d = {k: (polya_ui[k].value or "").strip() for k, _ in POLYA}
'''
NOVOE_KARTA = '''            # KOROTKIY_BLANK_V1: где стоит — строкой, а не тремя полями.
            _gde = " · ".join(x for x in (m.get("квартал"), m.get("цех"),
                                          m.get("слот")) if x)
            if _gde:
                ui.label(_gde).style("color:rgba(255,255,255,0.4); "
                                     "font-size:0.72rem; margin-bottom:8px;")

            polya_ui = {}
            for klyuch, podpis in POLYA:
                znach = post.get(klyuch, "") if est else (
                    m["название"] if klyuch == "название" else "")
                polya_ui[klyuch] = ui.input(podpis, value=znach or "").props(
                    "dark dense outlined").style(
                    "width:100%; font-size:0.78rem; margin-bottom:6px;")

            with ui.expansion("подробнее — обязанности, судья, условия").style(
                    "width:100%; font-size:0.75rem; "
                    "color:rgba(255,255,255,0.5);"):
                for klyuch, podpis in POLYA_ESHCHE:
                    polya_ui[klyuch] = ui.input(
                        podpis, value=post.get(klyuch, "") or "").props(
                        "dark dense outlined").style(
                        "width:100%; font-size:0.78rem; margin-bottom:6px;")
                ui.html('<div class="rab-podpis">обязанности — по одной в строке</div>')
                obyaz = ui.textarea(
                    value="\\n".join(post.get("обязанности", []) or [])).props(
                    "dark dense outlined").style(
                    "width:100%; font-size:0.78rem;")

            def _sobrat() -> dict:
                d = {k: (polya_ui[k].value or "").strip()
                     for k, _ in (POLYA + POLYA_ESHCHE)}
                # квартал, цех и слот не спрашиваем — берём от места
                for k in ("квартал", "цех", "слот"):
                    if m.get(k):
                        d[k] = m[k]
'''

STEZHKI = (
    ("поля поделены", STAROE_POLYA, NOVOE_POLYA),
    ("карточка укорочена", STAROE_KARTA, NOVOE_KARTA),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("═" * 58)
    print("КОРОТКИЙ БЛАНК" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 58)

    if not STRANICA.exists():
        print("✗ нет ГОРОД/ui_rabota.py — сперва поставь страницу")
        return 1

    tekst = STRANICA.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  ✗ якорь «{nazv}» найден {n} раз — файл не трогаю")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  · {nazv} — заменено")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_rabota.py"):
        return 1

    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_korotkiy_blank.py")
        return 0

    shutil.copy2(STRANICA, STRANICA.with_suffix(STRANICA.suffix + BAK))
    STRANICA.write_text(tekst, encoding="utf-8")
    print(f"\n✓ накатано (копия рядом: ui_rabota.py{BAK})")
    print("\nНа карточке теперь два поля и строчка «где стоит».")
    print("Остальное — под «подробнее», свёрнуто.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
