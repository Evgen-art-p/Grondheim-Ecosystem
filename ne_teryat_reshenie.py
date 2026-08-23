# -*- coding: utf-8 -*-
"""
ne_teryat_reshenie.py   ·   MARKER: NE_TERYAT_RESHENIE_V1

ЧТО СЛУЧИЛОСЬ
-------------
Прогон 23.08, бар 2025.02.24. Илья ВОШЁЛ — первый ордер за всё время:

    brut_action: ENTER · SHORT · вход 1.05099 · стоп 1.05283
    brut_verdict: APPROVED

Посчитал по свежему правилу, сам проговорил про два спреда сверху и
один снизу. А отчёт написал «входов 0», и Исполнитель ордер не
поставил. Решение до города не доехало.

ПОЧЕМУ
------
Ответ пришёл не JSON, а строками «ключ: значение» — тот же смысл, те
же имена полей, другой синтаксис. Разборщик ищет первую `{`, считает
скобки и парсит. Скобок нет — он МОЛЧА возвращает весь текст как
«голос», а сигнал отдаёт пустым.

Дальше рушится честно: пустой сигнал → нет action и вердикта → в
табло Исполнителю ложится пустота, ордер не ставится → в отчёт идёт
«без вердикта» и ноль входов. Человек вошёл, город не услышал.

Это тот же урок, что был сегодня дважды. Требовать безупречного
формата от того, кто по сути всё сделал верно, — то же самое, что
требовать волшебного слова НАБЛЮДАЮ вместо обычного «жду». И то же,
что было с руками: он говорил, а мы теряли слово.

ЧТО ДЕЛАЕМ
----------
  1. Не нашли JSON — разбираем строки вида `ключ: значение`. Поля
     названы точно так, как надо, брать их неоткуда больше.
  2. Запасной путь НЕ молчит: в консоль уходит строка, что формат
     поплыл и что удалось вынуть. Молча подбирать за трейдером
     нельзя — иначе не узнаем, что он сбился.
  3. В отчёте вместо безликого «без вердикта» — «ответ не разобран»,
     чтобы такое больше не пряталось за нулём во входах.

ЧЕГО НЕ ДЕЛАЕМ
--------------
  · ничего не додумываем за трейдера: чего в ответе нет, того нет.
    Сказал ENTER без цены — так и уйдёт, а санитар погасит, как и
    раньше;
  · JSON остаётся главным путём, запасной включается только когда
    первый не сработал.

Идемпотентен, кладёт `.bak_reshenie_ГГГГММДД_ЧЧММСС`.

  py -3 ne_teryat_reshenie.py           — сделать
  py -3 ne_teryat_reshenie.py --suho    — только показать
"""

import ast
import re
import sys
import time
from pathlib import Path

MARKER = "NE_TERYAT_RESHENIE_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ─────────── общий кусок: конец разборщика в каждом мозге ───────────

P_STAROE = '''                    except json.JSONDecodeError:
                        break
    return response.strip(), {}, {}'''

P_NOVOE = '''                    except json.JSONDecodeError:
                        break
    # NE_TERYAT_RESHENIE_V1: JSON не собрался — не выбрасываем решение.
    # 23.08 трейдер вошёл (ENTER, SHORT, цена и стоп посчитаны), но
    # ответил строками «ключ: значение» вместо скобок — и вход пропал
    # целиком: ордер не поставлен, в отчёте ноль. Смысл был, синтаксис
    # поплыл. Разбираем строками.
    _rasskaz, _signal, _dnevnik = _razobrat_strokami(response)
    if _signal or _dnevnik:
        print(f"[РАЗБОР] ⚠️  ответ не JSON — разобрал строками: "
              f"{len(_signal)} поле(й) сигнала, "
              f"{len(_dnevnik)} дневника")
        return _rasskaz, _signal, _dnevnik
    return response.strip(), {}, {}


# NE_TERYAT_RESHENIE_V1 ─────────────────────────────────────────
_CHISLA = ("_entry", "_stop", "_lot", "_new_stop", "_add_lot")


def _znachenie(s: str, klyuch: str):
    """Строку значения — в число, None или текст. Ничего не выдумываем:
    пусто и null остаются пустотой, а не нулём."""
    s = s.strip().strip('",').strip()
    if s.lower() in ("null", "none", "", "-", "—"):
        return None
    if klyuch.endswith(_CHISLA):
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None
    return s


def _razobrat_strokami(response: str):
    """Запасной разбор: «ключ: значение» построчно.

    Ответ идёт разделами (narrative / signal / diary_entry), поля
    внутри — с отступом. Раздел определяем по строке без значения,
    поля сигнала узнаём по имени: они всегда с приставкой ключа
    трейдера (brut_/avan_/cons_), спутать не с чем.
    """
    rasskaz, signal, dnevnik = "", {}, {}
    razdel = ""
    for stroka in (response or "").splitlines():
        golaya = stroka.strip()
        if not golaya or golaya.startswith("```"):
            continue
        if ":" not in golaya:
            continue
        klyuch, _, znach = golaya.partition(":")
        klyuch = klyuch.strip().strip('"').lower()
        znach = znach.strip()
        if klyuch in ("narrative", "signal", "diary_entry"):
            razdel = klyuch
            if klyuch == "narrative" and znach:
                rasskaz = znach.strip('",')
            continue
        if re.match(r"^(brut|avan|cons)_", klyuch):
            signal[klyuch] = _znachenie(znach, klyuch)
        elif razdel == "diary_entry" and klyuch in ("input", "action",
                                                    "result"):
            dnevnik[klyuch] = _znachenie(znach, klyuch)
    if not rasskaz:
        # рассказа отдельной строкой не было — берём первый связный
        # кусок текста до начала разделов, это и есть его голос
        for stroka in (response or "").splitlines():
            g = stroka.strip()
            if g and ":" not in g[:20] and not g.startswith("```"):
                rasskaz = g
                break
    return rasskaz, signal, dnevnik'''


# ─────────── отчёт: честная пометка вместо «без вердикта» ───────────

O_STAROE = '''            "вердикт": verdikt or ("промолчал" if not skazal else "без вердикта"),'''

O_NOVOE = '''            # NE_TERYAT_RESHENIE_V1: «без вердикта» звучало безобидно и
            # пряталось за нулём во входах — а за ним стоял потерянный
            # вход. Называем прямо.
            "вердикт": verdikt or ("промолчал" if not skazal
                                   else "ОТВЕТ НЕ РАЗОБРАН"),'''


def sobrat(koren: Path) -> list:
    g = koren / "GRONDHEIM_CITY"
    out = []
    for p in sorted(g.glob("Биржа/цеха/*/слоты/*/мозг.py")):
        # только мозги трейдеров: у конторы разбор свой, якоря там нет
        if P_STAROE in p.read_text(encoding="utf-8"):
            out.append((p, [(P_STAROE, P_NOVOE)]))
    out.append((koren / "Биржа" / "otchyot.py", [(O_STAROE, O_NOVOE)]))
    return out


# ─────────────────────────── механика ───────────────────────────

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


def pravit(put: Path, zameny) -> str:
    if not put.is_file():
        return "мимо: файла нет"
    text = put.read_text(encoding="utf-8")
    if MARKER in text:
        return "уже"
    for staroe, _ in zameny:
        n = text.count(staroe)
        if n != 1:
            return f"мимо: якорь встретился {n} раз"
    novyy = text
    for staroe, novoe in zameny:
        novyy = novyy.replace(staroe, novoe, 1)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        return f"мимо: правка ломает синтаксис ({e.lineno}: {e.msg})"
    if SUHO:
        return "сделано (сухой прогон)"
    put.with_name(put.name + f".bak_reshenie_{SHTAMP}").write_text(
        text, encoding="utf-8")
    put.write_text(novyy, encoding="utf-8")
    return "сделано"


def main():
    koren = nayti_koren()
    print(f"Корень города: {koren}")
    if SUHO:
        print("СУХОЙ ПРОГОН — ничего не записываю.\n")

    itogi = []
    print()
    for put, zameny in sobrat(koren):
        r = pravit(put, zameny)
        print(f"  {r:<26} {put.relative_to(koren)}")
        itogi.append(r)

    print("\n" + "─" * 64)
    print(f"поправлено: {sum(1 for x in itogi if x.startswith('сделано'))}   "
          f"уже стояло: {sum(1 for x in itogi if x == 'уже')}   "
          f"не тронуто: {sum(1 for x in itogi if x.startswith('мимо'))}")
    print("─" * 64)

    print("""
ЧТО ПОЯВИТСЯ В КОНСОЛИ
  [РАЗБОР] ⚠️  ответ не JSON — разобрал строками: 7 поле(й) сигнала,
           3 дневника

  Если эта строка идёт часто — значит формат плывёт постоянно, и
  тогда стоит смотреть бумагу, а не подпирать разбором. Молча
  подбирать за трейдером мы не будем.

ЧТО ПРОВЕРИТЬ
  Тот же февраль. На 24.02 у него был ENTER SHORT 1.05099 / стоп
  1.05283. Теперь этот вход должен дойти: появиться в отчёте как
  APPROVED и уйти Исполнителю заявкой.

  И это будет ПЕРВАЯ его сделка — значит впервые появится событие
  для памяти жителя: вход и, когда закроется, результат.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
