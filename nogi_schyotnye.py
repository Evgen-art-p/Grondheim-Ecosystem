# -*- coding: utf-8 -*-
"""
nogi_schyotnye.py   ·   MARKER: NOGI_SCHYOTNYE_V1

ЧТО СЕЙЧАС
----------
У живой точки ровно два гнезда под события: `konec_volny_1` и
`konec_volny_2`. Заполнились оба — и точка молчит до слома. Пришёл
новый разворотник против неё? Раньше он рождал НОВУЮ точку поверх
живой (неверно, но хоть что-то происходило). После патча
`ODNA_TOCHKA_ZA_RAZ_V1` он не делает вообще ничего.

Замер это показал прямо: пять точек из сорока шести за четыре года
жили дольше девяноста баров — месяцами. Каждая дала ровно одну ногу и
один откат, и дальше город про них молчал.

ПОЧЕМУ ЭТО НЕПРАВДА
-------------------
Слово Шефа (26.08): от точки до точки идёт пятиволновка и разворот в
откат — «всё так же с макушкой, как в волне 1». То есть после первого
отката структура не кончается: идёт следующая нога со своей макушкой,
за ней свой откат, и так до слома. Механика ровно та же, разворотный
бар тот же — просто ей запрещено повторяться.

Канон Шефа (25.08): пропустил первую волну — жди первую внутри
третьей, потом внутри пятой. Каждый следующий шанс дороже, но он ЕСТЬ.
Сейчас трейдер получает один шанс на структуру вместо трёх.

ЧТО ДЕЛАЕМ
----------
Одно: разрешаем событиям повторяться, пока точка жива.

  · разворотник ПРОТИВ точки, когда макушка и откат уже отмечены, —
    это макушка СЛЕДУЮЩЕЙ ноги. Пишем её на место прежней, откат
    обнуляем, номер ноги увеличиваем;
  · дальше разворотник В СТОРОНУ точки закрывает уже этот откат —
    тем же блоком, что и первый, ни строки нового кода;
  · и так до слома.

Номер ноги ложится в стол и в ленту: «нога 2», «нога 3». НАЗЫВАТЬ их
третьей и пятой волной код не будет — это разметка, дело трейдера. Код
кладёт факт: которая по счёту нога от точки.

Счётчик попыток при новой ноге обнуляется: три попытки — право на
ОДНОМ сигнале (слово Шефа 25.08), а новый откат это новый сигнал.

ЧЕГО НЕ ДЕЛАЕМ
--------------
  · смерть точки не трогаем — только слом, как и был;
  · рождение не трогаем — «одна точка за раз» остаётся;
  · порогов, окон и чисел не заводим ни одного.

Идемпотентен, кладёт `.bak_nogi_ГГГГММДД_ЧЧММСС`.

  py -3 nogi_schyotnye.py           — сделать
  py -3 nogi_schyotnye.py --suho    — только показать
"""

import ast
import sys
import time
from pathlib import Path

MARKER = "NOGI_SCHYOTNYE_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ── 1. при рождении номер ноги обнуляется ──
R_STAROE = '''                isk["попыток"] = 0            # TRI_POPYTKI_V1'''

R_NOVOE = '''                isk["попыток"] = 0            # TRI_POPYTKI_V1
                isk["нога"] = 0               # NOGI_SCHYOTNYE_V1'''


# ── 2. новый блок: макушка следующей ноги ──
N_STAROE = '''        if (zhiva and napr in ("BULL", "BEAR") and storona != napr
                and cena is not None
                and not isk.get("konec_volny_1")):'''

N_NOVOE = '''        # NOGI_SCHYOTNYE_V1: макушка и откат уже отмечены, а пришёл
        # ещё один разворотник против точки. От точки до точки идёт
        # пятиволновка (слово Шефа 26.08): после отката начинается
        # следующая нога, у неё своя макушка и свой откат — той же
        # механикой, тем же баром. Раньше это событие пропадало:
        # оба гнезда заняты, и точка молчала до слома, хотя внутри
        # неё проходили ещё две волны со своими шансами на вход.
        #
        # Номер ноги — ФАКТ, а не разметка. Третья это волна или
        # пятая, решает трейдер: он смотрит.
        if (zhiva and napr in ("BULL", "BEAR") and storona != napr
                and cena is not None and isk.get("konec_volny_1")
                and isk.get("konec_volny_2")):
            _n = int(isk.get("нога") or 1) + 1
            isk["нога"] = _n
            isk["konec_volny_1"] = {
                "цена": cena, "бар": bar, "сторона": napr,
                "структура": wf.get("dlina") or 0,
                "баров_от_точки": int(isk.get("barov_s_tochki") or 0),
                "нога": _n,
            }
            isk["konec_volny_2"] = None
            isk["kray_posle"] = cena
            # три попытки — право на ОДНОМ сигнале; следующий откат
            # будет новым сигналом, счёт начинается заново
            isk["попыток"] = 0
            save_trading_state(t)
            _slovo = "вершина" if storona == "BULL" else "дно"
            print(f"[ВОЛНА {_n}] ⛰ {para}: нога {_n} кончилась @ {cena} "
                  f"· бар {bar} · {_slovo} новой ноги от той же точки")
            return _zapomnit_otvet({"alive": True, "konec_volny_1": True,
                                    "нога": _n, "direction": storona})

        if (zhiva and napr in ("BULL", "BEAR") and storona != napr
                and cena is not None
                and not isk.get("konec_volny_1")):'''


# ── 3. в ленте отката видно, которая это нога ──
O_STAROE = '''            _slovo = "вершины" if storona == "BULL" else "дна"
            print(f"[ОТКАТ] ↩ {para}: кончился @ {cena} · бар {bar} "
                  f"· {max(0, _ot_makushki)} бар(ов) от {_slovo}")'''

O_NOVOE = '''            _slovo = "вершины" if storona == "BULL" else "дна"
            _n = int(isk.get("нога") or 1)   # NOGI_SCHYOTNYE_V1
            isk["konec_volny_2"]["нога"] = _n
            save_trading_state(t)
            print(f"[ОТКАТ] ↩ {para}: кончился @ {cena} · бар {bar} "
                  f"· {max(0, _ot_makushki)} бар(ов) от {_slovo} "
                  f"· нога {_n}")'''



# ── 4. номер ноги ДОХОДИТ ДО ТРЕЙДЕРА (стол, не только консоль) ──
# Лента в консоли — наша, стол — его. Без этого трейдер видит
# «ВОЛНА 1 кончилась» на третьей ноге и честно считает её первой.

S1_STAROE = '''        "волна_1": (lambda _k: ({
            "кончилась": True,
            "макушка": _k.get("цена"),
            "бар": _k.get("бар"),
            "баров_от_точки": _k.get("баров_от_точки"),
        } if _k else {"кончилась": False}))(isk.get("konec_volny_1") or {}),'''

S1_NOVOE = '''        "волна_1": (lambda _k: ({
            "кончилась": True,
            "макушка": _k.get("цена"),
            "бар": _k.get("бар"),
            "баров_от_точки": _k.get("баров_от_точки"),
            # NOGI_SCHYOTNYE_V1: которая это нога от точки. Пусто у
            # структур, начатых до патча, — тогда просто первая.
            "нога": _k.get("нога") or 1,
        } if _k else {"кончилась": False}))(isk.get("konec_volny_1") or {}),'''

S2_STAROE = '''        "волна_2": (lambda _k: ({
            "кончилась": True,
            "цена": _k.get("цена"),
            "бар": _k.get("бар"),
            "баров_от_макушки": _k.get("баров_от_макушки"),
        } if _k else {"кончилась": False}))(isk.get("konec_volny_2") or {}),'''

S2_NOVOE = '''        "волна_2": (lambda _k: ({
            "кончилась": True,
            "цена": _k.get("цена"),
            "бар": _k.get("бар"),
            "баров_от_макушки": _k.get("баров_от_макушки"),
            "нога": _k.get("нога") or 1,   # NOGI_SCHYOTNYE_V1
        } if _k else {"кончилась": False}))(isk.get("konec_volny_2") or {}),'''

S3_STAROE = '''        (lambda _v, _t: (
            f"ВОЛНА 1: от {_t.get('цена')} → "
            f"{'вершина' if _t.get('сторона') == 'BULL' else 'дно'} "
            f"{_v.get('макушка')}"
            f"   {_v.get('баров_от_точки')} бар(ов) от точки"
            f"   бар {_v.get('бар')}"
            if _v.get("кончилась") else "ВОЛНА 1: ещё идёт"))('''

S3_NOVOE = '''        (lambda _v, _t: (
            f"ВОЛНА {_v.get('нога') or 1}: от {_t.get('цена')} → "
            f"{'вершина' if _t.get('сторона') == 'BULL' else 'дно'} "
            f"{_v.get('макушка')}"
            f"   {_v.get('баров_от_точки')} бар(ов) от точки"
            f"   бар {_v.get('бар')}"
            # NOGI_SCHYOTNYE_V1: нога от точки, а не всегда «первая».
            + (f"   нога {_v.get('нога')} от точки"
               if (_v.get('нога') or 1) > 1 else "")
            if _v.get("кончилась")
            else f"ВОЛНА {(_t.get('нога_идёт') or 1)}: ещё идёт"))('''

S4_STAROE = '''            f"ОТКАТ: кончился @ {_o.get('цена')}"
            f"   {_o.get('баров_от_макушки')} бар(ов) от "
            f"{'вершины' if _t.get('сторона') == 'BULL' else 'дна'}"
            f"   бар {_o.get('бар')}"'''

S4_NOVOE = '''            f"ОТКАТ: кончился @ {_o.get('цена')}"
            f"   {_o.get('баров_от_макушки')} бар(ов) от "
            f"{'вершины' if _t.get('сторона') == 'BULL' else 'дна'}"
            f"   бар {_o.get('бар')}"
            + (f"   нога {_o.get('нога')} от точки"   # NOGI_SCHYOTNYE_V1
               if (_o.get('нога') or 1) > 1 else "")'''


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
        print("СУХОЙ ПРОГОН — ничего не записываю.")

    put = koren / "Биржа" / "hooks.py"
    text = put.read_text(encoding="utf-8")

    print("\n1. НОГИ ВНУТРИ ТОЧКИ")
    if MARKER in text:
        print("   уже стояло — ничего не делаю")
        zhdat_i_vyyti(0)
    if "ODNA_TOCHKA_ZA_RAZ_V1" not in text:
        print("   мимо: сперва нужен патч odna_tochka_za_raz.py — без него\n"
              "   разворотник внутри точки рождает новую, и считать нечего")
        zhdat_i_vyyti(1)

    pary = (("рождение", R_STAROE, R_NOVOE),
            ("новая нога", N_STAROE, N_NOVOE),
            ("лента отката", O_STAROE, O_NOVOE))
    for imya, staroe, _ in pary:
        n = text.count(staroe)
        if n != 1:
            print(f"   мимо: якорь «{imya}» встретился {n} раз — "
                  f"код НЕ тронут")
            zhdat_i_vyyti(1)

    novyy = text
    for _, staroe, novoe in pary:
        novyy = novyy.replace(staroe, novoe, 1)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"   мимо: правка ломает синтаксис ({e.lineno}: {e.msg}) — "
              f"код НЕ тронут")
        zhdat_i_vyyti(1)

    if not SUHO:
        put.with_name(put.name + f".bak_nogi_{SHTAMP}").write_text(
            text, encoding="utf-8")
        put.write_text(novyy, encoding="utf-8")
    print("   сделано   Биржа/hooks.py")

    print("\n2. НОМЕР НОГИ НА СТОЛ ТРЕЙДЕРА")
    put2 = koren / "Биржа" / "stol.py"
    text2 = put2.read_text(encoding="utf-8")
    pary2 = (("волна_1", S1_STAROE, S1_NOVOE),
             ("волна_2", S2_STAROE, S2_NOVOE),
             ("строка волны", S3_STAROE, S3_NOVOE),
             ("строка отката", S4_STAROE, S4_NOVOE))
    if MARKER in text2:
        print("   уже стояло")
    else:
        mimo = False
        for imya, staroe, _ in pary2:
            n = text2.count(staroe)
            if n != 1:
                print(f"   мимо: якорь «{imya}» встретился {n} раз — "
                      f"стол НЕ тронут")
                mimo = True
                break
        if not mimo:
            novyy2 = text2
            for _, staroe, novoe in pary2:
                novyy2 = novyy2.replace(staroe, novoe, 1)
            novyy2 = novyy2.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
            try:
                ast.parse(novyy2)
                if not SUHO:
                    put2.with_name(
                        put2.name + f".bak_nogi_{SHTAMP}").write_text(
                        text2, encoding="utf-8")
                    put2.write_text(novyy2, encoding="utf-8")
                print("   сделано   Биржа/stol.py")
            except SyntaxError as e:
                print(f"   мимо: правка ломает синтаксис "
                      f"({e.lineno}: {e.msg}) — стол НЕ тронут")

    print("""
────────────────────────────────────────────────────────────────
ЧТО ИЗМЕНИТСЯ В ЛЕНТЕ

  Было — точка живёт месяц, а город сказал о ней два раза:
      [ТОЧКА]  ✦ родилась BULL @ 1.0834
      [ВОЛНА 1] ⛰ кончилась @ 1.0902
      [ОТКАТ]  ↩ кончился @ 1.0861
      …тишина до слома…

  Станет — структура рассказывается до конца:
      [ОТКАТ]  ↩ кончился @ 1.0861 · нога 1
      [ВОЛНА 2] ⛰ нога 2 кончилась @ 1.0958
      [ОТКАТ]  ↩ кончился @ 1.0903 · нога 2
      [ВОЛНА 3] ⛰ нога 3 кончилась @ 1.1041

  Номер ноги — факт, не разметка: которая по счёту от точки.
  Третья это волна или пятая — говорит трейдер, он смотрит.

  Откатить: рядом лежит hooks.py.bak_nogi_<штамп>.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
