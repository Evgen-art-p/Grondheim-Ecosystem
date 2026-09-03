# -*- coding: utf-8 -*-
# MARKER: PUZYR_PODSVETKA_V2
"""
ПУЗЫРЁК: ВЕРНУТЬ КНОПКУ, ПОДСВЕТКУ ДЕЛАТЬ СТИЛЕМ.

ЧТО БЫЛО (моя ошибка 03.09, PUZYR_KAK_V_AKADEMII_V1)
    Я заменил ui.button на div «как в Академии» — и клик перестал
    доходить. Причина была написана прямо над тем местом, в
    комментарии PUZYRI_V1: «были голые div — клик держался на
    всплытии и терялся, как у тумблера». То есть div уже пробовали,
    он не работал, переход на ui.button был осознанной починкой. Я её
    откатил, не прочитав. Этот патч возвращает кнопку.

ПОЧЕМУ КОЛЬЦО ВСЁ-ТАКИ НЕ ГОРЕЛО
    CSS `.avatar.active` (синее кольцо) задаёт border-color и
    box-shadow. У QBtn свои стили на те же свойства, и они выигрывают
    у классов, навешенных снаружи. В Академии пузырёк — div, там
    спорить не с кем, поэтому класса хватает.

ЧТО ДЕЛАЕТСЯ ТЕПЕРЬ
    Элемент остаётся кнопкой (клик работает, как работал). Подсветка
    активного/готового перестаёт зависеть от классов: update_avatar_states
    пишет её ПРЯМО В style элемента, с !important. Inline-стиль
    сильнее любых стилей Quasar — спорить больше не с чем.
    Базовая часть style (аватарка фоном) запоминается при создании
    пузырька и не затирается.

    Классы .active/.done по-прежнему навешиваются — они никому не
    мешают и остаются, если позже захочется вернуться к чистому CSS.

ЧТО НЕ ТРОГАЕТСЯ
    switch_agent, roster, логика клика — не менялись. Правится только
    то, ЧЕМ рисуется подсветка.

Патч понимает оба исходных состояния файла: и когда стоит мой
ошибочный div, и когда файл уже откачен из .bak_puzyr.
Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PUZYR_PODSVETKA_V2"

# ── 1. вернуть кнопку ────────────────────────────────────────────────

DIV_VERSIYA = '''                        # PUZYR_KAK_V_AKADEMII_V1: div, не ui.button —
                        # у кнопки Quasar своя разметка, синее кольцо
                        # активного агента под ней не загоралось.
                        avatar = ui.element("div").classes(cls)
                        avatar.on("click", _nazhali)
                        avatar.style(style)'''

BUTTON_VERSIYA = '''                        avatar = ui.button(on_click=_nazhali).classes(cls)
                        avatar.props("flat dense no-caps").style(style)'''

BUTTON_NOVAYA = '''                        avatar = ui.button(on_click=_nazhali).classes(cls)
                        avatar.props("flat dense no-caps").style(style)
                        # PUZYR_PODSVETKA_V2: базовый style (аватарка
                        # фоном) запоминаем — подсветка будет дописываться
                        # к нему, а не затирать его.
                        avatar._bazovyy_style = style'''

# ── 2. подсветка стилем, а не классом ───────────────────────────────

STATES_STAR = '''    def update_avatar_states():
        for aid, el in avatars_ref["elements"].items():
            row = _agent_row(roster, aid)
            base = "avatar vacant" if (row and not row["resident"]) else "avatar"
            el.classes(replace=base)
            if aid == state["active_agent"]:
                el.classes(add="active")
            if aid in state["reports"]:
                el.classes(add="done")'''

STATES_NOV = '''    # PUZYR_PODSVETKA_V2: кольцо рисуем ПРЯМО В style, с !important.
    # Классы .active/.done оставляем — они не мешают, но у QBtn свои
    # стили на border-color/box-shadow, и класс снаружи им проигрывает.
    # Inline-стиль сильнее — спорить больше не с чем.
    _PODSVETKA = {
        "active": ("border-color: rgba(0,204,255,0.75) !important; "
                   "box-shadow: 0 0 0 2px rgba(0,204,255,0.25) inset, "
                   "0 0 30px rgba(0,204,255,0.35) !important;"),
        "done":   ("border-color: rgba(0,255,136,0.75) !important; "
                   "box-shadow: 0 0 0 2px rgba(0,255,136,0.25) inset, "
                   "0 0 30px rgba(0,255,136,0.35) !important;"),
    }

    def update_avatar_states():
        for aid, el in avatars_ref["elements"].items():
            row = _agent_row(roster, aid)
            base = "avatar vacant" if (row and not row["resident"]) else "avatar"
            el.classes(replace=base)
            if aid == state["active_agent"]:
                el.classes(add="active")
            if aid in state["reports"]:
                el.classes(add="done")

            # активный важнее «отчёт готов»: смотрим-то мы на него
            if aid == state["active_agent"]:
                hvost = _PODSVETKA["active"]
            elif aid in state["reports"]:
                hvost = _PODSVETKA["done"]
            else:
                hvost = ""
            try:
                bazovyy = getattr(el, "_bazovyy_style", "") or ""
                el.style(replace=bazovyy + hvost)
            except Exception:
                pass'''


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
    f = _nayti_birzhu() / "ui_torg.py"
    src = f.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"\n{f}: уже накачено")
        return

    novyy = src

    # 1. вернуть кнопку — что бы сейчас ни стояло
    if DIV_VERSIYA in novyy:
        novyy = novyy.replace(DIV_VERSIYA, BUTTON_NOVAYA)
        otkuda = "вернул кнопку (стоял мой ошибочный div)"
    elif BUTTON_VERSIYA in novyy:
        novyy = novyy.replace(BUTTON_VERSIYA, BUTTON_NOVAYA)
        otkuda = "кнопка была на месте, добавил память базового стиля"
    else:
        print(f"\n{f}: ! не нашёл создание пузырька ни в одном из двух видов — не трогаю")
        return

    # 2. подсветка стилем
    if STATES_STAR not in novyy:
        print(f"\n{f}: ! не нашёл update_avatar_states дословно — не трогаю")
        return
    novyy = novyy.replace(STATES_STAR, STATES_NOV)

    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_podsvetka"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}: {otkuda}; подсветка теперь inline-стилем")
    print("   (.bak_podsvetka рядом)")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
