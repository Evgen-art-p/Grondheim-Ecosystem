# -*- coding: utf-8 -*-
"""
pult_i_para_po_postu.py   ·   MARKER: PARA_PO_POSTU_V1

ДВЕ МОИ ОШИБКИ, ОБЕ ВИДНЫ НА СКРИНЕ 24.08
------------------------------------------
1. ПОЛКА СОГНАЛА ДВОИХ НА ОДИН ИНСТРУМЕНТ.
   В шапке правильно: Илья — EURUSD H4, Нина — XAUUSD H4. А в ленте
   прогона: «2 трейдер(ов) · EURUSD». Вчера, когда Шеф попросил
   вернуть выбор инструмента на полку слева, на Бирже сидел ОДИН
   человек, и подмена выглядела разумной. Стало двое — и полка, одна
   на всех, переехала обоим посты.

   Для параллельного сравнения это не мелочь, а срыв самой затеи:
   сажали двоих, чтобы посмотреть, кто входит на ОДНОЙ истории по
   СВОЕЙ воле. Пара должна приходить из поста каждого, а не сверху.

   Убираю подмену совсем. Полка слева остаётся тем, чем была до моей
   вчерашней правки, — выбором того, что смотришь. А чем работает
   трейдер, говорит его пост.

   Хочешь сравнить двоих на одном рынке — пропиши обоим одну пару в
   постах. Тогда они идут по ней потому, что так назначено, а не
   потому, что кабинет молча переехал их выбор.

2. ПОДПИСЬ «ЛОВИТЬ:» ОТОРВАНА ОТ СВОЕГО ПОЛЯ.
   На панели вышло: «ловить: отрезок: 2025.02.01 2025.03.10 15».
   Поле числа стоит в конце, а его подпись — в начале, потому что я
   воткнул даты между ними. Переставляю: сперва отрезок с двумя
   датами, потом «ловить» со своим полем рядом.

ЧЕГО НЕ ТРОГАЮ
--------------
  · границы отрезка и счётчик срабатываний — работают, видно по
    ленте: «с 2025.02.01 по 2025.03.10 · ловлю 15», 302 бара на
    двоих;
  · посты и метки жителей.

Идемпотентен, кладёт `.bak_parapost_ГГГГММДД_ЧЧММСС`.

  py -3 pult_i_para_po_postu.py           — сделать
  py -3 pult_i_para_po_postu.py --suho    — только показать
"""

import ast
import sys
import time
from pathlib import Path

MARKER = "PARA_PO_POSTU_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ─────────── 1. пара из поста, без подмены с полки ───────────

A_STAROE = '''        # TESTER_PULT_V2: чем гнать — говорит ПОЛКА слева, та строка,
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
            print(f"[ПРОГОН] полку не спросил ({_epol}) — иду парой места")
        rabotniki = []
        for _sl in ("A06", "A07", "A08"):
            r = vybor.rabota_dlya(tseh_id, _sl)
            if r.get("готов"):
                _sym_r = _podmena or r["инструмент"]
                rabotniki.append((_sl, _sym_r, r["этаж"]))
                if _podmena and _podmena != r["инструмент"]:
                    print(f"[ПРОГОН] {_sl}: на время прогона "
                          f"{r['инструмент']} → {_podmena}")'''

A_NOVOE = '''        # PARA_PO_POSTU_V1: пара приходит из ПОСТА каждого, и ниоткуда
        # больше. Подмены с полки здесь БОЛЬШЕ НЕТ: пока на Бирже сидел
        # один человек, она выглядела разумной, а на двоих согнала обоих
        # на один инструмент — 24.08 Илья и Нина пошли по евро, хотя у
        # Нины в посте золото. Для сравнения двух трейдеров это срыв
        # самой затеи: они должны идти по своей паре, а не по той, что
        # кабинет молча выбрал за них.
        #
        # Полка слева снова только то, ЧТО СМОТРИШЬ. Нужен общий рынок
        # для сравнения — пропиши обоим одну пару в постах.
        _podmena = ""
        rabotniki = []
        for _sl in ("A06", "A07", "A08"):
            r = vybor.rabota_dlya(tseh_id, _sl)
            if r.get("готов"):
                rabotniki.append((_sl, r["инструмент"], r["этаж"]))'''

B_STAROE = '''                        + (f" · {_podmena}" if _podmena else "")'''

B_NOVOE = '''                        # PARA_PO_POSTU_V1: у каждого своя пара — пишем
                        # их все, чтобы сразу видеть, кто чем гонит.
                        + " · " + ", ".join(f"{_s}:{_sy} {_tf2}"
                                            for _s, _sy, _tf2 in rabotniki)'''


# ─────────── 2. подпись «ловить» — рядом со своим полем ───────────

C_STAROE = '''                        toolbar_refs["bars_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")
                        with toolbar_refs["bars_label"]:
                            ui.label("ловить:").style("color:rgba(255,255,255,0.45);font-size:11px;")
                        # PROGON_S_DATY_V1: поле «с даты». Пусто — ищем'''

C_NOVOE = '''                        # PARA_PO_POSTU_V1: «ловить» переехало ВНИЗ, к
                        # своему полю. Раньше подпись стояла здесь, а
                        # число — после дат, и на панели читалось
                        # «ловить: отрезок: 01.02 10.03 15»: подпись от
                        # одного поля, значение от другого.
                        # PROGON_S_DATY_V1: поле «с даты». Пусто — ищем'''

D_STAROE = '''                        # TESTER_PULT_V2: поля «инструмент» здесь больше
                        # нет — чем гнать, говорит полка слева.
                        toolbar_refs["bars_input"] = ui.element("div").style("display:none;align-items:center;")'''

D_NOVOE = '''                        # TESTER_PULT_V2: поля «инструмент» здесь больше
                        # нет — чем работать, говорит пост трейдера.
                        # PARA_PO_POSTU_V1: подпись «ловить» теперь тут,
                        # вплотную к своему полю.
                        toolbar_refs["bars_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")
                        with toolbar_refs["bars_label"]:
                            ui.label("ловить:").style("color:rgba(255,255,255,0.45);font-size:11px;")
                        toolbar_refs["bars_input"] = ui.element("div").style("display:none;align-items:center;")'''


ZAMENY = [(A_STAROE, A_NOVOE), (B_STAROE, B_NOVOE),
          (C_STAROE, C_NOVOE), (D_STAROE, D_NOVOE)]


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
    if "TESTER_PULT_V2" not in text:
        print("\n  ⚠️  нужен tester_pult_akkuratno.py — этой правкой я "
              "исправляю его. Файл НЕ тронут.")
        zhdat_i_vyyti(1)

    for i, (staroe, _) in enumerate(ZAMENY, 1):
        n = text.count(staroe)
        if n != 1:
            print(f"\n  мимо: якорь №{i} «"
                  f"{staroe.strip().splitlines()[0][:44]}…» × {n}")
            print("  Файл НЕ тронут.")
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
        print("\n  сделано (сухой прогон)   Биржа/ui_torg.py — 4 правки")
    else:
        put.with_name(put.name + f".bak_parapost_{SHTAMP}").write_text(
            text, encoding="utf-8")
        put.write_text(novyy, encoding="utf-8")
        print("\n  сделано                  Биржа/ui_torg.py — 4 правки")

    print("""
ЧТО ИЗМЕНИТСЯ

  Панель:  ТЕСТЕР · отрезок:[с ..][по ..] · ловить:[N] · СТОП · ...
           подпись снова рядом со своим полем.

  Лента:   ▶ ПРОГОН ПО ИСТОРИИ · 2 трейдер(ов)
           · A06:EURUSD H4, A07:XAUUSD H4 · с ... · по ...
           теперь сразу видно, кто чем гонит.

  ЕСЛИ ХОЧЕШЬ СРАВНИТЬ ИЛЬЮ И НИНУ — пропиши обоим в постах одну
  пару (EURUSD H4). Тогда они пойдут по одной истории потому, что так
  назначено, и сравнение будет честным.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
