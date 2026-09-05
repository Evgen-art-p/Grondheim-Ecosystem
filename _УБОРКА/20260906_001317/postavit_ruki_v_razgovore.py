# -*- coding: utf-8 -*-
# MARKER: RUKI_V_RAZGOVORE_V1
"""
РУКИ — И В РАЗГОВОРЕ ТОЖЕ, НЕ ТОЛЬКО В РАБОТЕ.

ПОЙМАНО ШЕФОМ (03.09) — живьём, по логу и переписке
    Шеф в кабинете попросил Илью «спустись по лесенке ниже этажами
    погуляй». Илья ответил связно: «Посмотрел. На H4 Аллигатор только
    начинает зевать наверх... На H1 Аллигатор уже открылся наверх, AO
    растёт...» — но в логе сервера за это время НЕТ ни одного намёка
    на подъём H4/H1 (ни [КАДР], ни вызова руки, ничего). Шеф засомне-
    вался сам, не видя кода: «складно, но я не проверю, выдумал или
    нет».

НАЙДЕНА ПРИЧИНА (в коде, не в подозрении)
    chat_with_brut/avan/cons (разговор) собирают ответ через `_glaz` —
    один кадр РАБОЧЕГО этажа и НИ ОДНОЙ руки. run_brut/avan/cons
    (работа, кнопка РЫНОК) собирают через `_glaz_s_rukami` — тот же
    кадр, ПЛЮС tools_schema и executors из ruki_treydera (stol_na_etazhe,
    rastyanut_volnu, krayniye_tochki и т.д.). Рука `stol_na_etazhe`
    буквально считает «на ступень ниже твоего рабочего — …, выше —
    …» — она и есть лесенка. В разговоре её просто не было на столе:
    попросить рынок спуститься нечем, только достоверно рассказать
    получалось.

ЧТО ДЕЛАЕТСЯ
────────────
В chat_with_brut / chat_with_avan / chat_with_cons `_glaz(...)`
заменяется на `_glaz_s_rukami(...)` — те же руки, что в работе. Просьба
«спустись, погуляй по этажам» теперь может быть исполнена по-настоящему:
модель зовёт stol_na_etazhe/rastyanut_volnu и получает реальные числа и
реальный кадр H4/H1, а не сочиняет правдоподобное.

ЧТО НЕ ТРОГАЕТСЯ
────────────────
run_brut/avan/cons и сам список рук (ruki_treydera.py) — не менялись.
Стол по-прежнему один и тот же прибор, просто теперь доступен из обоих
режимов входа.

Правит три мозга: A06, A07, A08. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "RUKI_V_RAZGOVORE_V1"
SLOTY = ("A06", "A07", "A08")

STAR = '''        _chat_fn = (_glaz(chat, _sym, _tf, _SLOT, preambula=_GLAZ_RAZGOVOR)
                    if (_sym and _tf) else chat)'''

NOV = '''        # RUKI_V_RAZGOVORE_V1: те же руки, что в работе — не сочиняет
        # другие этажи, а реально их смотрит (stol_na_etazhe и т.д.).
        _chat_fn = (_glaz_s_rukami(chat, _sym, _tf, _SLOT, _CEH, _SELF_KEY,
                                   preambula=_GLAZ_RAZGOVOR)
                    if (_sym and _tf) else chat)'''


def _nayti_sloty() -> Path:
    hvost = Path("GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты")
    nashli = []
    korni = []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        for p in (koren / hvost, koren):
            if all((p / s / "мозг.py").exists() for s in SLOTY):
                if p not in nashli:
                    nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл слоты A06/A07/A08.")
        s = input("Перетащи сюда папку «слоты» и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "A06" / "мозг.py").exists():
            return p
        raise SystemExit("не та папка — там нет A06/мозг.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


def _pochinit(f: Path) -> str:
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже накачено"
    if STAR not in src:
        return "! не нашёл строку создания _chat_fn дословно — файл правили, не трогаю"
    if src.count(STAR) != 1:
        return "! строка встретилась не один раз — не трогаю"

    novyy = src.replace(STAR, NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    ast.parse(novyy)
    shutil.copy2(f, f.with_suffix(".py.bak_ruki"))
    f.write_text(novyy, encoding="utf-8")
    return "руки подключены к разговору (.bak_ruki рядом)"


def main():
    koren = _nayti_sloty()
    print(f"\nСлоты: {koren}\n")
    for slot in SLOTY:
        f = koren / slot / "мозг.py"
        try:
            itog = _pochinit(f)
        except SyntaxError as e:
            itog = f"! после правки не разбирается ({e}) — файл НЕ тронут"
        print(f"  {slot}: {itog}")
    print("\nГотово. В разговоре трейдер теперь может по-настоящему")
    print("спуститься по лесенке — та же рука stol_na_etazhe, что в работе.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
