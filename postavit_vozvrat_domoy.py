# -*- coding: utf-8 -*-
# VOZVRAT_NA_RABOCHIY_V1
"""
СХОДИЛ ПОСМОТРЕТЬ — ВЕРНИСЬ НА СВОЙ ЭТАЖ

Слово Шефа 11.09: «зачем по разным обрывкам работать? Если он берёт
график с другим этажом — для посмотреть, — а работает на другом, то
он вернуться должен».

КАК БЫЛО. Трейдер идёт рукой на старший этаж, смотрит — и этот кадр
остаётся последним, что у него перед глазами. Решение и приказ он
отдаёт, глядя на ЧУЖОЙ этаж. Работа по обрывкам: разобрал на своём,
посмотрел на другом, а вошёл неизвестно по какому.

КАК СТАЛО. Сходил на чужой этаж — к ответу руки прикладывается и
СВОЙ рабочий кадр. Последнее перед глазами всегда дом. Не надеемся,
что он вспомнит вернуться: возвращает город.

ТРИ ПОХОДА РАЗНЫЕ, и патч трогает только первый:

 · ПОСМОТРЕТЬ — сходил и вернулся. Это он и делает руками, здесь
   возврат и добавляется.
 · СМЕНИТЬ РАБОЧИЙ ЭТАЖ — решил работать на другом, записал его
   себе рукой. Возвращать некуда, он уже дома: если рабочий этаж
   совпал с тем, куда сходил, возврат не делается.
 · НЕСТИ ВАХТУ НА ДРУГОМ ЭТАЖЕ — меняется, где его будят. Этого
   патч не касается вовсе, по слову Шефа: «пока с возвратом
   разберёмся, потом вахта».

Моменты НЕ равняем. У старшего этажа свой последний бар, и это
нормально — так и на живом графике. Важно одно: домой вернулся.

КУДА КЛАСТЬ ЭТОТ ФАЙЛ: в корень репы, рядом с main.py. Оттуда и
запускать.

БЕЗОПАСНОСТЬ: .bak_vozvrat, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_vozvrat_domoy.py --suho
    python postavit_vozvrat_domoy.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "VOZVRAT_NA_RABOCHIY_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ruki_treydera.py"

# ── рука «показать этаж» ─────────────────────────────────────
STAROE_POK = '''        if not put:
            return f"котировок {symbol} {tf} не дали"
        return f"[КАДР: {put}] {symbol} {tf}, последние 140 баров"'''

NOVOE_POK = '''        if not put:
            return f"котировок {symbol} {tf} не дали"
        return (f"[КАДР: {put}] {symbol} {tf}, последние 140 баров"
                + _domoy(tf))'''

# ── рука «стол на этаже» ─────────────────────────────────────
STAROE_STOL = '''            if put:
                return (f"[КАДР: {put}] {symbol} {tf} · стол ниже\\n"
                        + chisla)
            return chisla'''

NOVOE_STOL = '''            if put:
                return (f"[КАДР: {put}] {symbol} {tf} · стол ниже\\n"
                        + chisla + _domoy(tf))
            return chisla + _domoy(tf)'''

TELO = '''

    def _domoy(kuda_hodil: str) -> str:
        """VOZVRAT_NA_RABOCHIY_V1: сходил на чужой этаж — вот твой.

        Возвращает хвост к ответу руки: кадр рабочего этажа, чтобы
        последним перед глазами был ДОМ, а не тот этаж, куда ходили
        смотреть. Решение и вход — всегда на своём.

        Сходил на свой же (или рабочего этажа нет) — хвоста нет:
        возвращать некуда. Это же покрывает случай, когда трейдер
        сменил рабочий этаж на тот, куда пришёл, — он уже дома.
        """
        try:
            svoy = (rabochiy_etazh or "").strip().upper()
            if not svoy or svoy == (kuda_hodil or "").strip().upper():
                return ""
            import grafik
            _p = grafik.kadr(symbol, svoy, linii=False)
            if not _p:
                return (f"\\n\\n(домой на {svoy} не вернулся: котировок не "
                        f"дали. Решай по своему этажу, а не по {kuda_hodil}.)")
            print(f"[ВОЗВРАТ] {slot}: посмотрел {kuda_hodil} → домой на {svoy}")
            return (f"\\n\\n[КАДР: {_p}] ВЕРНУЛСЯ ДОМОЙ · {symbol} {svoy} — "
                    f"твой рабочий этаж. Смотрел ты {kuda_hodil}, а решаешь "
                    f"и входишь здесь.")
        except Exception as _e:
            print(f"[ВОЗВРАТ] не вышло ({_e}) — трейдер остался на "
                  f"{kuda_hodil}")
            return ""
'''


def main():
    print()
    print("ВОЗВРАТ НА РАБОЧИЙ ЭТАЖ"
          + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()
    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")
    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return

    novy = txt
    for imya, st, nv in (("рука «показать этаж»", STAROE_POK, NOVOE_POK),
                         ("рука «стол на этаже»", STAROE_STOL, NOVOE_STOL)):
        if novy.count(st) != 1:
            print(f"  ОТКАЗ на «{imya}» — якорь встречается "
                  f"{novy.count(st)} раз(а), файл не тронут")
            return
        novy = novy.replace(st, nv, 1)
        print(f"  {imya}: возврат добавлен")

    # тело кладём внутрь ruki(), перед сборкой словаря рук
    yakor_telo = "    def _krayniye(args: dict) -> str:"
    if novy.count(yakor_telo) != 1:
        print("  ОТКАЗ — не нашёл, куда положить возврат")
        return
    novy = novy.replace(yakor_telo, TELO.strip("\n") + "\n\n" + yakor_telo, 1)
    print("  домашний кадр: функция вставлена")

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return
    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_vozvrat"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ruki_treydera.py.bak_vozvrat")
    print("Посмотрел чужой этаж — дальше перед глазами свой.")
    print()


if __name__ == "__main__":
    main()
