# -*- coding: utf-8 -*-
# POSTAVIT_PERECHITAT_V1
"""
ПАТЧ: перечитать можно всегда.

Запускать из КОРНЯ РЕПО:
    python postavit_perechitat.py

ЧТО БЫЛО НЕ ТАК
    Житель прочитал материал криво — и всё, дверь закрыта: отметка
    «прочитано» стоит, «📖 Прочитать» отвечает «уже прочитал всё, что
    на столе» и больше ничего не делает. Убрать отметку руками нельзя.

    А криво читают часто и по разным причинам: заряд под минус
    единицу, картинка не дошла, знания были старые. Все три мы сегодня
    чинили — и каждый раз упирались в то, что проверить починку не на
    чем: материал считается пройденным.

ЧТО ДЕЛАЕТ
    Нового на столе нет, а «Прочитать» нажали — значит хотят ещё раз.
    Читает всё, что лежит, заново. В чате честно пишет «перечитывает».

    Отметку «прочитано» при этом НЕ снимает и прошлый вывод НЕ стирает:
    оба останутся в памяти. Это его опыт — как прочитал тогда и как
    прочитал теперь. Разница между ними и есть самое ценное.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# PERECHITAT_V1"


def _nayti():
    kand = [p for p in _KOREN.rglob("ui_akademia.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл ui_akademia.py. Запускай из корня репозитория.")
        return None
    if len(kand) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kand, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            return kand[int(input("Который? номер: ").strip()) - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kand[0]


STARO_1 = '''        if not novye:
            ui.notify(f"{imya} уже прочитал(а) всё, что на столе", type="info")
            return'''

NOVO_1 = '''        # PERECHITAT_V1: нового нет, а кнопку нажали — значит хотят
        # ещё раз. Житель мог прочитать криво: заряд был на дне,
        # картинка не дошла, знания были старые. Запирать дверь после
        # одного кривого захода нельзя — иначе починку не на чем
        # проверить.
        _perechityvaem = False
        if not novye:
            if not fajly:
                ui.notify("На столе пусто — читать нечего", type="info")
                return
            novye = list(fajly)
            _perechityvaem = True'''


STARO_2 = '''        state["чат"].append({"role": "assistant", "кто": "СТОЛ",
                             "content": f"📖 {imya} садится читать {len(novye)} материал(ов) со стола…"})'''

NOVO_2 = '''        _glagol = "перечитывает" if _perechityvaem else "садится читать"
        state["чат"].append({"role": "assistant", "кто": "СТОЛ",
                             "content": f"📖 {imya} {_glagol} "
                                        f"{len(novye)} материал(ов) со стола…"})'''


ZAMENY = [
    ("разрешить перечитать", STARO_1, NOVO_1),
    ("сказать, что перечитывает", STARO_2, NOVO_2),
]


def main():
    print("=" * 58)
    print("ПЕРЕЧИТАТЬ")
    print("=" * 58)

    fajl = _nayti()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return

    print("\n--- ЗАМЕНЫ ---")
    ne = []
    for imya, staro, _n in ZAMENY:
        c = tekst.count(staro)
        print(f"  {'✓' if c == 1 else '⚠ ' + str(c)}  {imya}")
        if c != 1:
            ne.append(imya)
    if ne:
        print(f"\n⚠ не сошлось: {', '.join(ne)} — ничего не тронул.")
        return

    novyy = tekst
    for _i, staro, novo in ZAMENY:
        novyy = novyy.replace(staro, novo, 1)
    novyy = novyy.rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_perechitat")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город:")
    print("  Жми «📖 Прочитать» второй раз — прочитает заново,")
    print("  в чате будет «перечитывает».")
    print("  Перед этим остуди его кнопкой ❄ Душ — тогда сравнение")
    print("  будет честным: кривое чтение часто от заряда, а не от глаз.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_PERECHITAT_V1 - marker
