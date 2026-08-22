# -*- coding: utf-8 -*-
"""
ruki_ne_teryat_slovo.py   ·   MARKER: RUKI_NE_TERYAT_SLOVO_V1

ЧТО СЛУЧИЛОСЬ
-------------
В прогоне 22.08 место №20 (2025.11.26 08:00) вместо слов трейдера
получило служебную строку:

    «Разговор с руками не сошёлся — рук попросили больше, чем можно.»

Это не ответ Ильи. Это заглушка, которой кончается круг рук, когда он
исчерпан. И место с самым интересным баром — как раз тем, где годом
раньше отметился единственный конец волны 1, — ушло в отчёт пустым.

ТРИ ПОЛОМКИ В ОДНОЙ
-------------------
1. СЛОВО ТЕРЯЕТСЯ. Модель может писать текст ВМЕСТЕ с запросом рук —
   он лежит в том же ответе. Круг кончился — мы выбрасываем всё, что
   она успела сказать, и подставляем заглушку. Человек говорил, город
   не услышал.

2. КРУГ МОЖЕТ НЕ КОНЧАТЬСЯ. Счётчик растёт ТОЛЬКО когда рука нашлась.
   Позвала несуществующую — счётчик стоит, а заход потрачен. Так круг
   выкручивается вхолостую и упирается в предел, ни разу его не
   увеличив.

3. ПРЕДЕЛ МОЛЧАЛИВЫЙ. Мы просто перестаём давать руки и ждём, что
   собеседник догадается. Он не догадывается — он просит снова.

ЧТО ДЕЛАЕМ
----------
  · последний непустой текст запоминаем и отдаём его, даже если круг
    кончился: слово трейдера дороже нашей аккуратности;
  · заход считаем всегда, найдена рука или нет;
  · когда рук осталось мало — говорим об этом прямо, в разговор:
    «рук больше не будет, скажи словами»;
  · если круг всё же кончился без единого слова — в консоль уходит
    список званых рук, чтобы было видно, за чем он бегал по кругу, а
    в отчёт идёт честная пометка, а не загадка.

Идемпотентен, кладёт `.bak_rukislovo_ГГГГММДД_ЧЧММСС`.

  py -3 ruki_ne_teryat_slovo.py           — сделать
  py -3 ruki_ne_teryat_slovo.py --suho    — только показать
"""

import ast
import sys
import time
from pathlib import Path

MARKER = "RUKI_NE_TERYAT_SLOVO_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


A_STAROE = '''    ruki = dict(executors or {})
    sdelano = 0

    for _ in range(max_tool_rounds + 1):'''

A_NOVOE = '''    ruki = dict(executors or {})
    sdelano = 0
    # RUKI_NE_TERYAT_SLOVO_V1: последнее, что собеседник сказал СЛОВАМИ.
    # Он может писать текст в том же ответе, где просит руку, — и
    # раньше этот текст выбрасывался, если круг кончался.
    posledneye_slovo = ""
    zvali_ruki: list = []          # за чем бегал по кругу

    for _krug in range(max_tool_rounds + 1):'''


B_STAROE = '''        messages.append({"role": "assistant",
                         "content": msg.get("content") or "",
                         "tool_calls": msg["tool_calls"]})
        for tc in msg["tool_calls"]:'''

B_NOVOE = '''        # RUKI_NE_TERYAT_SLOVO_V1: запомнить слово, сказанное вместе с
        # просьбой о руке. Оно и есть ответ, если круг кончится.
        _skazal_seychas = (msg.get("content") or "").strip()
        if _skazal_seychas:
            posledneye_slovo = _skazal_seychas

        messages.append({"role": "assistant",
                         "content": msg.get("content") or "",
                         "tool_calls": msg["tool_calls"]})
        for tc in msg["tool_calls"]:'''


C_STAROE = '''            ruka = ruki.get(imya)
            if ruka:
                try:
                    otvet = str(ruka(args))
                except Exception as e:
                    otvet = f"рука {imya} сорвалась: {e}"
                sdelano += 1
                print(f"[РУКА] 🖐 {imya}({args}) → {len(otvet)} симв. "
                      f"({sdelano}/{max_tool_rounds})")
            else:
                otvet = f"Такой руки нет: {imya}"'''

C_NOVOE = '''            ruka = ruki.get(imya)
            zvali_ruki.append(imya)
            # RUKI_NE_TERYAT_SLOVO_V1: заход считаем ВСЕГДА. Раньше
            # счётчик рос только на найденной руке — и звонок в пустоту
            # тратил заход, не двигая счётчик. Круг выкручивался
            # вхолостую и упирался в предел, ни разу его не увеличив.
            sdelano += 1
            if ruka:
                try:
                    otvet = str(ruka(args))
                except Exception as e:
                    otvet = f"рука {imya} сорвалась: {e}"
                print(f"[РУКА] 🖐 {imya}({args}) → {len(otvet)} симв. "
                      f"({sdelano}/{max_tool_rounds})")
            else:
                otvet = (f"Такой руки нет: {imya}. Больше её не проси — "
                         f"её не появится.")
                print(f"[РУКА] ✕ {imya} — такой руки нет "
                      f"({sdelano}/{max_tool_rounds})")'''


D_STAROE = '''    return "Разговор с руками не сошёлся — рук попросили больше, чем можно."'''

D_NOVOE = '''    # RUKI_NE_TERYAT_SLOVO_V1: круг кончился. Раньше здесь терялось
    # всё, что собеседник успел сказать, и в отчёт уходила заглушка
    # вместо слов трейдера. Слово дороже нашей аккуратности.
    if posledneye_slovo:
        print(f"[РУКИ] круг кончился ({sdelano}/{max_tool_rounds}), "
              f"беру последнее сказанное словами")
        return posledneye_slovo
    _skolko = {}
    for _i in zvali_ruki:
        _skolko[_i] = _skolko.get(_i, 0) + 1
    _spisok = ", ".join(f"{k}×{v}" for k, v in
                        sorted(_skolko.items(), key=lambda x: -x[1]))
    print(f"[РУКИ] ⚠️  круг кончился и НИ СЛОВА не сказано. "
          f"Звали: {_spisok or 'ничего'}")
    return (f"(промолчал: круг рук кончился, слов не было. "
            f"Звал: {_spisok or 'ничего'})")'''


# предупредить собеседника, что руки заканчиваются
E_STAROE = '''        if tools_schema and sdelano < max_tool_rounds:
            payload["tools"] = tools_schema
            payload["tool_choice"] = "auto"'''

E_NOVOE = '''        if tools_schema and sdelano < max_tool_rounds:
            payload["tools"] = tools_schema
            payload["tool_choice"] = "auto"
        elif tools_schema:
            # RUKI_NE_TERYAT_SLOVO_V1: раньше мы просто молча убирали
            # руки и ждали, что собеседник догадается. Он не
            # догадывался — просил снова. Теперь говорим прямо.
            messages.append({
                "role": "user",
                "content": ("Рук больше не будет — предел на этот взгляд "
                            "исчерпан. Ответь тем, что уже видишь: "
                            "словами и своим JSON, как обычно.")})'''


ZAMENY = [(A_STAROE, A_NOVOE), (E_STAROE, E_NOVOE), (B_STAROE, B_NOVOE),
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

    put = koren / "Биржа" / "llm.py"
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
        print("\n  сделано (сухой прогон)   Биржа/llm.py — 5 правок")
    else:
        put.with_name(put.name + f".bak_rukislovo_{SHTAMP}").write_text(
            text, encoding="utf-8")
        put.write_text(novyy, encoding="utf-8")
        print("\n  сделано                  Биржа/llm.py — 5 правок")

    print("""
ЧТО ИЗМЕНИТСЯ

  · Заглушки «разговор с руками не сошёлся» в отчёте больше не будет:
    если человек сказал хоть слово — в отчёт пойдёт оно.
  · Если он и правда промолчал, в отчёте будет видно, за чем он бегал:
    «(промолчал: круг рук кончился, слов не было. Звал: stol_na_etazhe×9,
    izmerit_volnu×4)» — по этому списку сразу понятно, зациклился он
    или честно не успел.
  · В консоли появятся строки [РУКА] ✕ для рук, которых нет, и
    [РУКИ] ⚠️ при пустом круге.

ЧТО ПОСМОТРЕТЬ ПОСЛЕ ПРОГОНА
  Если в консоли пойдут [РУКА] ✕ — значит модель зовёт руку, которой
  у нас нет, и надо смотреть ЕЁ ИМЯ: либо руку завести, либо убрать
  из бумаги обещание, которого мы не держим.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
