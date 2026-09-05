# -*- coding: utf-8 -*-
# MARKER: DOM_V_RAZGOVORE_V1
"""
ДОМ — В РАЗГОВОР, НЕ В РАБОТУ.

СЛОВО ШЕФА (08.08, записано тогда же, но не сделано)
    «Дом на Бирже не подмешивается (s_domom=False, нарочно — Закон
    Входа-Выхода и экономия на тестере). Предложено включать дом в
    РАЗГОВОРЕ, не в работе».

ЧТО БЫЛО НЕ ТАК
────────────────
`dusha_slota(ceh, slot)` во всех трёх мозгах звался БЕЗ s_domom и в
chat_with_* (личный разговор), и в run_* (рабочее решение) — то есть
одинаково. Домашний_промпт не подмешивался НИГДЕ. В разговоре трейдер
видел своё ядро, натуру, метки, маяки — но не дом, поэтому на личный
вопрос честно отвечал только про рынок: снаружи работы у него, со
стороны, будто ничего и не было.

ЧТО ДЕЛАЕТСЯ
────────────
В chat_with_brut / chat_with_avan / chat_with_cons (и только там)
вызов dusha_slota получает s_domom=True.

ЧТО НЕ ТРОГАЕТСЯ
────────────────
В run_brut / run_avan / run_cons (рабочий цикл, тестер) вызов
остаётся как был — s_domom не передан, действует default False.
Закон Входа-Выхода и экономия на тестере (тысячи вызовов) — как и
решил Шеф. Патч ищет вызов ТОЛЬКО внутри тела chat_with_* функции,
границу видит по следующему `def ` в начале строки — в run_* не
заходит совсем.

Правит три мозга: A06, A07, A08. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "DOM_V_RAZGOVORE_V1"
SLOTY = ("A06", "A07", "A08")
CHAT_FN = {"A06": "chat_with_brut", "A07": "chat_with_avan", "A08": "chat_with_cons"}

STAR = "_n = dusha_slota(_CEH, _SLOT)"
NOV = "_n = dusha_slota(_CEH, _SLOT, s_domom=True)   # DOM_V_RAZGOVORE_V1: дом — в разговор"


def _nayti_sloty() -> Path:
    """Папка .../торговый_хаос/слоты — ищем сами, от скрипта и от cwd."""
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


def _pochinit(f: Path, chat_fn: str) -> str:
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже накачено"

    zagolovok = f"def {chat_fn}("
    i0 = src.find(zagolovok)
    if i0 == -1:
        return f"! не нашёл {chat_fn}() — файл правили, не трогаю"

    # конец функции — следующий def в начале строки после заголовка
    i1 = src.find("\ndef ", i0 + len(zagolovok))
    if i1 == -1:
        i1 = len(src)

    telo = src[i0:i1]
    if STAR not in telo:
        return f"! не нашёл вызов dusha_slota внутри {chat_fn} — не трогаю"
    if telo.count(STAR) != 1:
        return f"! вызов dusha_slota в {chat_fn} встретился не один раз — не трогаю"

    novoe_telo = telo.replace(STAR, NOV)
    novyy = src[:i0] + novoe_telo + src[i1:]
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    ast.parse(novyy)      # на диск не кладём то, что не разбирается
    shutil.copy2(f, f.with_suffix(".py.bak_dom"))
    f.write_text(novyy, encoding="utf-8")
    return f"дом подмешан в {chat_fn} (.bak_dom рядом)"


def main():
    koren = _nayti_sloty()
    print(f"\nСлоты: {koren}\n")
    for slot in SLOTY:
        f = koren / slot / "мозг.py"
        try:
            itog = _pochinit(f, CHAT_FN[slot])
        except SyntaxError as e:
            itog = f"! после правки не разбирается ({e}) — файл НЕ тронут"
        print(f"  {slot}: {itog}")
    print("\nГотово. В личном разговоре трейдер теперь видит и дом.")
    print("В рабочем цикле (run_*) ничего не изменилось — там дома по-прежнему нет.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
