# -*- coding: utf-8 -*-
"""
tester_pult.py   ·   MARKER: TESTER_PULT_V1

ТРИ ПОЛОМКИ ПУЛЬТА ТЕСТЕРА
--------------------------
1. ИНСТРУМЕНТ не выбирается. Прогон берёт пару из ПОСТА места, а пост
   один. Что бы Шеф ни хотел проверить, гоняется всегда одно и то же.

2. «ЛОВИТЬ N» ничего не ловит. Число доезжает только до строки в ленте
   («ищу до N мест»), а сам сплошной прогон идёт по ВСЕМ барам до
   конца данных. Поле выглядит рабочим и врёт.

3. ДАТА только нижняя. «С даты» есть, «по дату» нет — значит от
   заданного момента и до конца файла, отрезок не вырезать.

Из-за всех трёх вместе прогон и выглядел «замороженным на одном годе».

ЧТО ДЕЛАЕМ
----------
  · поле ИНСТРУМЕНТ: задан — гоним по нему, посты не трогаем (это
    подмена на время прогона, а не переназначение места);
  · поле ПО ДАТУ: вместе с «с даты» вырезает любой отрезок истории;
  · «ЛОВИТЬ N» начинает считать НАСТОЯЩИЕ срабатывания — сколько раз
    открылся ключ и трейдера спросили. Дошли до N — останавливаемся.
    Пусто или 0 — без предела, до конца отрезка.

Почему считаем именно пробуждения, а не бары: бар стоит ноль, вопрос
трейдеру стоит денег. «Ловить 20» значит «двадцать оплаченных
взглядов», а не двадцать баров истории.

ЧЕГО НЕ ДЕЛАЕМ
--------------
  · посты и метки жителей не трогаем — подмена живёт только в прогоне;
  · этаж по-прежнему берётся у места: масштаб это дело трейдера.

Идемпотентен, кладёт `.bak_pult_ГГГГММДД_ЧЧММСС`.

  py -3 tester_pult.py           — сделать
  py -3 tester_pult.py --suho    — только показать
"""

import ast
import sys
import time
from pathlib import Path

MARKER = "TESTER_PULT_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ── 1. кто работает: подмена инструмента на время прогона ──

A_STAROE = '''        rabotniki = []
        for _sl in ("A06", "A07", "A08"):
            r = vybor.rabota_dlya(tseh_id, _sl)
            if r.get("готов"):
                rabotniki.append((_sl, r["инструмент"], r["этаж"]))'''

A_NOVOE = '''        # TESTER_PULT_V1: инструмент можно подменить на время прогона.
        # Пусто — работаем парой места, как и раньше. Задан — гоним по
        # нему, а пост и метка жителя остаются нетронутыми: это
        # проверка, а не переназначение места.
        _podmena = (state.get("progon_symbol") or "").strip().upper()
        rabotniki = []
        for _sl in ("A06", "A07", "A08"):
            r = vybor.rabota_dlya(tseh_id, _sl)
            if r.get("готов"):
                _sym_r = _podmena or r["инструмент"]
                rabotniki.append((_sl, _sym_r, r["этаж"]))
                if _podmena and _podmena != r["инструмент"]:
                    print(f"[ПРОГОН] {_sl}: на время прогона "
                          f"{r['инструмент']} → {_podmena}")'''


# ── 2. верхняя граница отрезка и предел по срабатываниям ──

B_STAROE = '''        skolko = int(state.get("bars_to_live") or 1)
        _ot_daty = _razobrat_datu(state.get("progon_ot_daty") or "")'''

B_NOVOE = '''        # TESTER_PULT_V1: «ловить N» — это ПРЕДЕЛ ПО СРАБАТЫВАНИЯМ, а
        # не по барам. Бар город считает даром, а вопрос трейдеру стоит
        # денег, и считать надо оплаченные взгляды. 0 или пусто — без
        # предела, идём весь отрезок.
        try:
            skolko = int(state.get("bars_to_live") or 0)
        except (TypeError, ValueError):
            skolko = 0
        _ot_daty = _razobrat_datu(state.get("progon_ot_daty") or "")
        _po_datu = _razobrat_datu(state.get("progon_po_datu") or "")
        if _ot_daty and _po_datu and _po_datu < _ot_daty:
            _ot_daty, _po_datu = _po_datu, _ot_daty
            print("[ПРОГОН] даты стояли задом наперёд — поменял местами")'''


C_STAROE = '''            "content": (f"▶ ПРОГОН ПО ИСТОРИИ · {len(rabotniki)} "
                        f"трейдер(ов) · ищу до {skolko} мест каждому")})'''

C_NOVOE = '''            "content": (f"▶ ПРОГОН ПО ИСТОРИИ · {len(rabotniki)} "
                        f"трейдер(ов)"
                        + (f" · {_podmena}" if _podmena else "")
                        + (f" · с {_ot_daty}" if _ot_daty else "")
                        + (f" · по {_po_datu}" if _po_datu else "")
                        + (f" · ловлю {skolko} срабатывани(й)"
                           if skolko else " · до конца отрезка"))})'''


D_STAROE = '''            _s = max(_s, 300)          # ядру нужно окно на разгон
            for j in range(_s, len(_daty)):
                mesta.append((_daty[j], _sl, _sym, _tf,
                              {"дата": _daty[j], "подряд": True}))
            print(f"[ПРОГОН] {_sl}: {_sym} {_tf} — "
                  f"{len(_daty) - _s} баров, "
                  f"с {_daty[_s]} по {_daty[-1]}")'''

D_NOVOE = '''            _s = max(_s, 300)          # ядру нужно окно на разгон
            # TESTER_PULT_V1: верхняя граница отрезка. Раньше её не
            # было вовсе — от даты и до конца файла, вырезать кусок
            # истории было нечем.
            _e = len(_daty)
            if _po_datu:
                _e = next((j for j, d in enumerate(_daty) if d > _po_datu),
                          len(_daty))
                if not _ot_daty:
                    # Год отсчитываем НАЗАД ОТ верхней границы, а не от
                    # конца файла: иначе «только по дату» давало пустой
                    # отрезок — нижняя граница оказывалась позже верхней.
                    _s = max(0, _e - _v_godu)
            _s = max(_s, 300)          # ядру нужно окно на разгон
            if _e <= _s:
                print(f"[ПРОГОН] {_sl}: между {_ot_daty or 'началом'} и "
                      f"{_po_datu} баров нет")
                continue
            for j in range(_s, _e):
                mesta.append((_daty[j], _sl, _sym, _tf,
                              {"дата": _daty[j], "подряд": True}))
            print(f"[ПРОГОН] {_sl}: {_sym} {_tf} — "
                  f"{_e - _s} баров, "
                  f"с {_daty[_s]} по {_daty[_e - 1]}")'''


# ── 3. счётчик срабатываний в сплошном ходу ──

E_STAROE = '''                    if not _kk.get("будим"):
                        continue
                    k = dict(k)
                    k["почему"] = _kk.get("почему", "")'''

E_NOVOE = '''                    if not _kk.get("будим"):
                        continue
                    k = dict(k)
                    k["почему"] = _kk.get("почему", "")
                    # TESTER_PULT_V1: вот оно, настоящее срабатывание —
                    # ключ открылся, сейчас трейдера спросят. Считаем
                    # здесь, а не по барам: платим мы за вопросы.
                    _razbudili += 1'''


F_STAROE = '''        proydeno = 0
        try:'''

F_NOVOE = '''        proydeno = 0
        _razbudili = 0          # TESTER_PULT_V1: оплаченных взглядов
        try:'''


# место, где заканчивается шаг: после ответа трейдера проверяем предел
G_STAROE = '''                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()'''

G_NOVOE = '''                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()
                # TESTER_PULT_V1: предел по срабатываниям. Проверяем
                # ПОСЛЕ ответа, чтобы последний взгляд был договорён до
                # конца, а не обрезан на полуслове.
                if skolko and _razbudili >= skolko:
                    state["chat_history"].append({
                        "role": "system",
                        "content": (f"⏹ поймано {_razbudili} "
                                    f"срабатывани(й) — предел, "
                                    f"останавливаюсь")})
                    update_chat_display()
                    break'''


# ── 4. пульт: два новых поля ──

H_STAROE = '''                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:12px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:140px;")

                        toolbar_refs["bars_input"] = ui.element("div").style("display:none;align-items:center;")'''

H_NOVOE = '''                            ).props(
                                'dense outlined '
                                'input-style="color:rgba(0,204,255,0.95);'
                                'font-family:JetBrains Mono;font-size:12px;'
                                'text-align:center;padding:0 2px;"'
                            ).style("width:140px;")

                        # TESTER_PULT_V1: верхняя граница отрезка.
                        # Вдвоём с «с даты» вырезает любой кусок истории.
                        toolbar_refs["po_datu_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")
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
                            ).style("width:140px;")

                        # TESTER_PULT_V1: чем гнать. Пусто — парой места.
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

                        toolbar_refs["bars_input"] = ui.element("div").style("display:none;align-items:center;")'''


I_STAROE = '''        for key in ("bars_input", "stop_btn", "bars_label",
                    "ot_daty_label", "ot_daty_input",   # PROGON_S_DATY_V1
                    "learn_btn"):   # TORG_LEARN_SWITCH_V1'''

I_NOVOE = '''        for key in ("bars_input", "stop_btn", "bars_label",
                    "ot_daty_label", "ot_daty_input",   # PROGON_S_DATY_V1
                    "po_datu_label", "po_datu_input",   # TESTER_PULT_V1
                    "symbol_label", "symbol_input",     # TESTER_PULT_V1
                    "learn_btn"):   # TORG_LEARN_SWITCH_V1'''


ZAMENY = [
    (A_STAROE, A_NOVOE), (B_STAROE, B_NOVOE), (C_STAROE, C_NOVOE),
    (D_STAROE, D_NOVOE), (E_STAROE, E_NOVOE), (F_STAROE, F_NOVOE),
    (G_STAROE, G_NOVOE), (H_STAROE, H_NOVOE), (I_STAROE, I_NOVOE),
]


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
        print("\n  сделано (сухой прогон)   Биржа/ui_torg.py — 9 правок")
    else:
        put.with_name(put.name + f".bak_pult_{SHTAMP}").write_text(
            text, encoding="utf-8")
        put.write_text(novyy, encoding="utf-8")
        print("\n  сделано                  Биржа/ui_torg.py — 9 правок")

    print("""
ЧТО ПОЯВИТСЯ НА ПУЛЬТЕ (кнопка ТЕСТЕР)
  ловить: [N]   с даты: [....]   по дату: [....]   инструмент: [....]

  инструмент пусто → как у места (EURUSD у Ильи)
  инструмент XAUUSD → весь прогон по золоту, пост не тронут
  ловить 0 или пусто → идём весь отрезок
  ловить 20 → остановимся после двадцатого вопроса трейдеру

  В ленте прогон теперь сам пишет, что понял:
  ▶ ПРОГОН ПО ИСТОРИИ · 1 трейдер(ов) · XAUUSD · с 2025.01.01
    · по 2025.06.30 · ловлю 20 срабатывани(й)

  И в конце: ⏹ поймано 20 срабатывани(й) — предел, останавливаюсь
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
