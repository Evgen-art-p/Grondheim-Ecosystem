# -*- coding: utf-8 -*-
# MARKER: PUZYR_KAK_V_AKADEMII_V1
"""
ПУЗЫРЁК — КАК В АКАДЕМИИ, ГДЕ ОН РАБОТАЕТ.

ПОЙМАНО ШЕФОМ (03.09): «суть не влияет, но в Академии работает
легко, а здесь нет» — про синее кольцо «активный агент» на шапке
Биржи, которое не загоралось, хотя клик доходил и state менялся
(строка «Илья — EURUSD D1» тому доказательство).

НАЙДЕНА ПРИЧИНА (сравнением с Академией — она буквально калька
Биржи, комментарий в ui_akademia.py так и говорит)
    CSS-класс `.avatar.active` (синее кольцо) в обоих файлах
    ОДИНАКОВЫЙ. Разное — САМ ЭЛЕМЕНТ, на который класс вешают:
      Академия (работает):  ui.element("div") + .on("click", ...)
      Биржа (не работает):  ui.button(on_click=...) + .props("flat
                             dense no-caps")
    ui.button — это компонент Quasar (QBtn), у него своя внутренняя
    разметка и стили; "flat"/"dense" переопределяют часть оформления
    поверх обычных CSS-классов. Обычный div такого фокуса не делает —
    что повесили классом, то и рисуется.

ЧТО ДЕЛАЕТСЯ
────────────
Пузырёк на Бирже становится тем же элементом, что в Академии: обычный
div с классом + `.on("click", ...)`. Клик и раньше доходил (лог тому
свидетель) — меняется только то, ЧЕМ нарисован пузырёк, не логика
переключения.

Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PUZYR_KAK_V_AKADEMII_V1"

STAR = '''                        def _nazhali(w=old_id):
                            print(f"[ПУЗЫРЬ] нажали: {w}")
                            switch_agent(w)

                        avatar = ui.button(on_click=_nazhali).classes(cls)
                        avatar.props("flat dense no-caps").style(style)'''

NOV = '''                        def _nazhali(w=old_id):
                            print(f"[ПУЗЫРЬ] нажали: {w}")
                            switch_agent(w)

                        # PUZYR_KAK_V_AKADEMII_V1: div, не ui.button —
                        # у кнопки Quasar своя разметка, синее кольцо
                        # активного агента под ней не загоралось.
                        avatar = ui.element("div").classes(cls)
                        avatar.on("click", _nazhali)
                        avatar.style(style)'''


def _nayti_birzhu() -> Path:
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (koren / "Биржа", koren):
            if (p / "ui_torg.py").exists():
                return p
    print("Не нашёл Биржа/ui_torg.py.")
    s = input("Перетащи сюда папку «Биржа» и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if (p / "ui_torg.py").exists():
        return p
    raise SystemExit("не та папка — там нет ui_torg.py")


def main():
    birzha = _nayti_birzhu()
    f = birzha / "ui_torg.py"
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"\n{f}: уже накачено")
        return
    if STAR not in src:
        print(f"\n{f}: ! не нашёл кусок дословно — файл правили, не трогаю")
        return
    if src.count(STAR) != 1:
        print(f"\n{f}: ! кусок встретился не один раз — не трогаю")
        return

    novyy = src.replace(STAR, NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_puzyr"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}: пузырёк теперь div, как в Академии (.bak_puzyr рядом)")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
