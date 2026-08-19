# -*- coding: utf-8 -*-
"""
pochinit_puzyri.py · MARKER: PUZYRI_V1

ЧТО ПРОИСХОДИТ
──────────────
В кабинете пузырьки трейдеров не нажимаются, никто ничего не пишет,
отчётов нет — тишина.

Две причины, обе нашлись в коде.

ПРИЧИНА ПЕРВАЯ: КЛИК НА ГОЛОМ DIV
    Пузырьки сделаны так же, как был сделан тумблер РЕАЛ/ТЕСТЕР —
    голым `div` с обработчиком на всплытии события. Тумблер по этой
    же причине не нажимался, я его починил, а пузырьки оставил: моя
    недоделка. Клик по такому элементу теряется, стоит любому слою
    лечь сверху.

ПРИЧИНА ВТОРАЯ, ХУЖЕ: АКТИВНОЙ СТОИТ ИСКРА
    Подсветка «кто сейчас выбран» прибита к A01:

        cls = f'avatar {"active" if old_id == "A01" else ""} …'

    A01 — Искра, упразднённая 06.08. Её нет ни в цехе, ни в списке.
    Значит НИ ОДИН пузырёк не подсвечен, и кабинет открывается с
    активным агентом, которого не существует: кадр не рисуется
    (пары нет), отчёт пуст (отчётов у Искры не бывает), чат не о ком.
    Тишина ровно та, что ты видишь.

ЧТО ПРАВИТ
──────────
1. Пузырьки становятся настоящими кнопками — клик обрабатывает сама
   кнопка, а не ловит всплытие.
2. Подсвечивается тот, кто ДЕЙСТВИТЕЛЬНО активен, — первый в составе,
   а не зашитая Искра. Кабинет открывается на живом человеке.
3. Каждое нажатие оставляет след в консоли:

       [ПУЗЫРЬ] нажали: A06

   Если после патча в консоли пусто — значит клик не доходит и до
   кнопки, и беда выше; тогда шли снимок этого места.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_puzyri.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PUZYRI_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists() and (p / "main.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


ST = '''                    for r in roster:
                        old_id = r["old_id"]
                        occupied = bool(r["resident"])
                        cls = f'avatar {"active" if old_id == "A01" else ""} {"" if occupied else "vacant"}'
                        avatar = ui.element("div").classes(cls)
                        style = ""
                        if occupied:
                            av = _avatar_url_for(r["resident"]["папка"], static_prefix)
                            if av:
                                style = f"background-image:url('{av}');"
                        avatar.style(style)
                        avatar.on("click", lambda e, w=old_id: switch_agent(w))
                        with avatar:
                            if not occupied:
                                ui.label(old_id).style("font-size: 9px")
                        avatars_ref["elements"][old_id] = avatar'''

NOV = '''                    # PUZYRI_V1: были голые div — клик держался на
                    # всплытии и терялся, как у тумблера. И подсветка
                    # «кто выбран» была прибита к A01, то есть к Искре,
                    # упразднённой 06.08: кабинет открывался на агенте,
                    # которого нет, оттого ни кадра, ни отчёта, ни чата.
                    for r in roster:
                        old_id = r["old_id"]
                        occupied = bool(r["resident"])
                        aktiven = (old_id == state.get("active_agent"))
                        cls = (f'avatar {"active" if aktiven else ""} '
                               f'{"" if occupied else "vacant"}')
                        style = ""
                        if occupied:
                            av = _avatar_url_for(r["resident"]["папка"], static_prefix)
                            if av:
                                style = f"background-image:url('{av}');"

                        def _nazhali(w=old_id):
                            print(f"[ПУЗЫРЬ] нажали: {w}")
                            switch_agent(w)

                        avatar = ui.button(on_click=_nazhali).classes(cls)
                        avatar.props("flat dense no-caps").style(style)
                        with avatar:
                            if not occupied:
                                ui.label(old_id).style("font-size: 9px")
                        avatars_ref["elements"][old_id] = avatar'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ui_torg = koren / "Биржа" / "ui_torg.py"
    t = ui_torg.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if t.count(ST) != 1:
        print(f"✗ блок пузырьков найден {t.count(ST)} раз — жду ровно один")
        return 1

    novyy = t.replace(ST, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = ui_torg.with_suffix(f".py.bak_puzyri_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(ui_torg, bak)
    ui_torg.write_text(novyy, encoding="utf-8")
    print(f"✓ пузырьки переделаны (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(ui_torg), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nОбнови страницу кабинета и жми пузырёк. В консоли должно быть:")
    print("    [ПУЗЫРЬ] нажали: A06")
    print("\nИ кабинет теперь открывается на живом человеке, а не на")
    print("упразднённой Искре — кадр и отчёт появятся сами.")
    print("\nЕсли в консоли пусто — клик не доходит и до кнопки: тогда")
    print("шли снимок шапки кабинета, буду смотреть, что лежит сверху.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
