# -*- coding: utf-8 -*-
"""
tester_pult_akkuratno.py   ·   MARKER: TESTER_PULT_V2

ЧТО ИСПРАВЛЯЮ ЗА СОБОЙ
----------------------
В `tester_pult.py` я добавил в панель ДВА поля с подписями, и панель
поехала: «БРАТ» обрезался, «ОЧИСТИТЬ» уехал за край экрана. Плюс завёл
ввод инструмента руками — при том, что выбор инструмента в кабинете
УЖЕ ЕСТЬ, слева, на полке загрузчика. Вторая правда там, где хватало
одной, да ещё и поверх тесной панели.

ЧТО ДЕЛАЕМ
----------
  1. Поле «инструмент» из панели УБИРАЕМ совсем. Прогон берёт
     инструмент с ПОЛКИ — с той строки, по которой Шеф кликнул слева.
     Одна дверь: тем же местом уже выбирается пара для кадра.
     Полка пуста — работаем парой места, как было до всего этого.

  2. Панель ужимаем: у дат остаётся одна подпись «отрезок:» на двоих,
     сами поля становятся уже, а что есть что — говорят подсказки
     внутри полей («с 2026.04.28», «по 2026.07.30»).

Освобождается примерно треть строки — «БРАТ», «СТОП», «УЧИТЬ» и
«ОЧИСТИТЬ» снова помещаются.

ЧЕГО НЕ ТРОГАЕМ
---------------
  · этаж по-прежнему берётся у МЕСТА, а не с полки: масштаб — дело
    трейдера, и полка тут не указ;
  · счётчик срабатываний и границы отрезка из первой правки остаются
    как есть, они работают.

Ставится ПОСЛЕ `tester_pult.py`. Идемпотентен, кладёт
`.bak_pult2_ГГГГММДД_ЧЧММСС`.

  py -3 tester_pult_akkuratno.py           — сделать
  py -3 tester_pult_akkuratno.py --suho    — только показать
"""

import ast
import sys
import time
from pathlib import Path

MARKER = "TESTER_PULT_V2"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ── 1. инструмент берём с полки, а не из поля ──

A_STAROE = '''        # TESTER_PULT_V1: инструмент можно подменить на время прогона.
        # Пусто — работаем парой места, как и раньше. Задан — гоним по
        # нему, а пост и метка жителя остаются нетронутыми: это
        # проверка, а не переназначение места.
        _podmena = (state.get("progon_symbol") or "").strip().upper()'''

A_NOVOE = '''        # TESTER_PULT_V2: чем гнать — говорит ПОЛКА слева, та строка,
        # по которой Шеф кликнул. Отдельного поля в панели нет и не
        # надо: этим же выбором уже берётся пара для кадра, и заводить
        # вторую дверь к одному и тому же — плодить расхождение.
        # Полка пуста — работаем парой места, как было.
        # Берём с полки ТОЛЬКО инструмент. Этаж остаётся у места:
        # масштаб дело трейдера, полка ему не указ.
        _podmena = ""
        try:
            _ps, _pt = _aktivnyy_rynok()
            _podmena = (_ps or "").strip().upper()
        except Exception as _epol:
            print(f"[ПРОГОН] полку не спросил ({_epol}) — иду парой места")'''


# ── 2. панель: убрать поле инструмента, ужать даты ──

B_STAROE = '''                        # TESTER_PULT_V1: чем гнать. Пусто — парой места.
                        toolbar_refs["symbol_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")
                        with toolbar_refs["symbol_label"]:
                            ui.label("инструмент:").style("color:rgba(255,255,255,0.45);font-size:11px;")
                        toolbar_refs["symbol_input"] = ui.element("div").style("display:none;align-items:center;")
                        with toolbar_refs["symbol_input"]:
                            def _on_symbol_change(e):   # TESTER_PULT_V1
                                state["progon_symbol"] = (e.value or "").strip().upper()
                            ui.input(
                                value="", placeholder="как у места",
                                on_change=_on_symbol_change,
                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:12px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:130px;")

                        toolbar_refs["bars_input"]'''

B_NOVOE = '''                        # TESTER_PULT_V2: поля «инструмент» здесь больше
                        # нет — чем гнать, говорит полка слева.
                        toolbar_refs["bars_input"]'''


# «по дату»: подпись убираем, подсказка внутри поля говорит сама
C_STAROE = '''                        toolbar_refs["po_datu_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")
                        with toolbar_refs["po_datu_label"]:
                            ui.label("по дату:").style("color:rgba(255,255,255,0.45);font-size:11px;")
                        toolbar_refs["po_datu_input"] = ui.element("div").style("display:none;align-items:center;")
                        with toolbar_refs["po_datu_input"]:
                            def _on_po_datu_change(e):   # TESTER_PULT_V1
                                state["progon_po_datu"] = (e.value or "").strip()
                            ui.input(
                                value="", placeholder="2026.07.30",
                                on_change=_on_po_datu_change,
                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:12px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:140px;")'''

C_NOVOE = '''                        # TESTER_PULT_V2: подписи у второй даты нет —
                        # подсказка внутри поля говорит сама, а строка
                        # панели узкая и каждый ярлык стоит места.
                        toolbar_refs["po_datu_input"] = ui.element("div").style("display:none;align-items:center;")
                        with toolbar_refs["po_datu_input"]:
                            def _on_po_datu_change(e):   # TESTER_PULT_V1
                                state["progon_po_datu"] = (e.value or "").strip()
                            ui.input(
                                value="", placeholder="по 2026.07.30",
                                on_change=_on_po_datu_change,
                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:11px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:112px;")'''


# первая дата: подпись «с даты:» → «отрезок:» (одна на обе), поле уже
D_STAROE = '''                        with toolbar_refs["ot_daty_label"]:
                            ui.label("с даты:").style("color:rgba(255,255,255,0.45);font-size:11px;")'''

D_NOVOE = '''                        with toolbar_refs["ot_daty_label"]:
                            # TESTER_PULT_V2: одна подпись на обе даты
                            ui.label("отрезок:").style("color:rgba(255,255,255,0.45);font-size:11px;")'''

E_STAROE = '''                            ui.input(
                                value="", placeholder="2026.04.28",
                                on_change=_on_daty_change,
                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:12px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:140px;")'''

E_NOVOE = '''                            ui.input(
                                value="", placeholder="с 2026.04.28",
                                on_change=_on_daty_change,
                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:11px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:112px;")'''


F_STAROE = '''                    "po_datu_label", "po_datu_input",   # TESTER_PULT_V1
                    "symbol_label", "symbol_input",     # TESTER_PULT_V1
                    "learn_btn"):   # TORG_LEARN_SWITCH_V1'''

F_NOVOE = '''                    "po_datu_input",                    # TESTER_PULT_V2
                    "learn_btn"):   # TORG_LEARN_SWITCH_V1'''


ZAMENY = [(A_STAROE, A_NOVOE), (B_STAROE, B_NOVOE), (C_STAROE, C_NOVOE),
          (D_STAROE, D_NOVOE), (E_STAROE, E_NOVOE), (F_STAROE, F_NOVOE)]


def nayti_koren() -> Path:
    for k in (Path(__file__).resolve().parent, Path.cwd()):
        for p in [k, *k.parents]:
            if (p / "GRONDHEIM_CITY").is_dir() and (p / "Биржа").is_dir():
                return p
    print("Не нашёл корень репозитория (нужны папки GRONDHEIM_CITY и Биржа).")
    zhdat_i_vyyti(1)


def zhdat_i_vyyti(kod=0):
    try:
        input("\nEnter — закрыть окно...")
    except EOFError:
        pass
    sys.exit(kod)


def main():
    koren = nayti_koren()
    print(f"Корень города: {koren}")
    if SUHO:
        print("СУХОЙ ПРОГОН — ничего не записываю.\n")

    put = koren / "Биржа" / "ui_torg.py"
    text = put.read_text(encoding="utf-8")
    if MARKER in text:
        print("\n  уже стояло — ничего не делаю.")
        zhdat_i_vyyti(0)
    if "TESTER_PULT_V1" not in text:
        print("\n  ⚠️  сперва нужен tester_pult.py — этой правкой я "
              "исправляю его же. Файл НЕ тронут.")
        zhdat_i_vyyti(1)

    for i, (staroe, _) in enumerate(ZAMENY, 1):
        n = text.count(staroe)
        if n != 1:
            print(f"\n  мимо: якорь №{i} «"
                  f"{staroe.strip().splitlines()[0][:46]}…» встретился {n} раз")
            print("  Файл НЕ тронут. Покажи это Брату.")
            zhdat_i_vyyti(1)

    novyy = text
    for staroe, novoe in ZAMENY:
        novyy = novyy.replace(staroe, novoe, 1)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n  мимо: правка ломает синтаксис ({e.lineno}: {e.msg})")
        zhdat_i_vyyti(1)

    if SUHO:
        print("\n  сделано (сухой прогон)   Биржа/ui_torg.py — 6 правок")
    else:
        put.with_name(put.name + f".bak_pult2_{SHTAMP}").write_text(
            text, encoding="utf-8")
        put.write_text(novyy, encoding="utf-8")
        print("\n  сделано                  Биржа/ui_torg.py — 6 правок")

    print("""
КАК ТЕПЕРЬ ВЫГЛЯДИТ ПАНЕЛЬ

  РЫНОК · ВАХТА · РЕАЛ · ТЕСТЕР · ловить:[N] · отрезок:[с ..][по ..]
  · БРАТ · СТОП · УЧИТЬ · ОЧИСТИТЬ

  Инструмент выбирается СЛЕВА, на полке: кликнул строку — по ней и
  пойдёт прогон. Тем же кликом уже выбирается кадр, так что смотришь
  и гонишь ты одно и то же.

  Этаж остаётся у МЕСТА, не с полки. Кликнешь строку D1, а у Ильи
  этаж H4 — гнать будем EURUSD H4. Так задумано: инструмент даёшь ты,
  масштаб выбирает трейдер.

  В ленте прогон по-прежнему говорит, что понял:
  ▶ ПРОГОН ПО ИСТОРИИ · 1 трейдер(ов) · EURUSD · с … · по …
    · ловлю 20 срабатывани(й)
  Если там не то, что ты выбрал слева, — значит полка не подхватилась.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
