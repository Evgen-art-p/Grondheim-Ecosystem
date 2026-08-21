# -*- coding: utf-8 -*-
"""
postavit_vybor_ne_meshaet.py · MARKER: VYBOR_NE_MESHAET_V1

СЛОВО ШЕФА (21.08)
──────────────────
«Илью посадил на место, в пузырьке на бирже он появился, а прогнать не
даёт — говорит, не назначен выбор входа. Исправь: выбор входа — дело
трейдера и с выбором места не связан. Машину не должно волновать.»

ЧТО ОСТАЛОСЬ ЗАПЕРТО
────────────────────
Первую защёлку сняли утром (MESTO_BEZ_VYBORA_V1): готовность места
перестала зависеть от паттерна. Но защёлки было ДВЕ, и вторая сидит в
самой бумаге трейдера. Пока выбор не сделан, ему в стопку уходит:

    «Своего входа ты ещё не выбрал(а) — и пока не выберешь, работать
     тебе не по чему. В работе это значит REJECTED с причиной
     "свой вход ещё не выбран"»

То есть машина не мешает, а мы прямым текстом велим человеку отказывать.
Он и отказывает — честно, по инструкции.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Приказ убран. Вместо него — приглашение:

    выбора нет → работаешь как работаешь, решая по столу; захочешь
                 выбрать своё место — объяви строкой ВЫБОР: …
    выбор есть → всё как было: работаешь по нему, не твоё место — пас

Сам вопрос «выбирай по СЕБЕ, а не то, что названо подтверждённым»
остаётся слово в слово — он хороший и достался дорого. Убрано ровно
одно: требование молчать, пока не выбрал.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_vybor_ne_meshaet.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VYBOR_NE_MESHAET_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "vybor.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


YAKOR = '''            "Своего входа ты ещё не выбрал(а) — и пока не выберешь, "
            "работать тебе не по чему. В работе это значит REJECTED с "
            "причиной «свой вход ещё не выбран»: брать чужой наугад хуже, "
            "чем честно молчать.\\n"'''

NOV = '''            # VYBOR_NE_MESHAET_V1: слово Шефа — «выбор входа дело
            # трейдера и с выбором места не связан, машину это не
            # должно волновать». Здесь стоял прямой приказ отказывать,
            # пока выбор не сделан, — человек честно и отказывал, по
            # инструкции. Приказ убран, вопрос оставлен.
            "Своего входа ты ещё не выбрал(а) — и это не мешает работать: "
            "смотри на стол и решай, как решается. Захочешь назвать своё "
            "место — назови, и город это запомнит.\\n"'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "vybor.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
        print("  (возможно, текст бумаги уже правили — покажи мне вывод)")
        return 1

    novyy = t.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_nemeshaet_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ выбор больше не мешает работать (копия: {bak.name})")
    print("\nБыло две защёлки: одна в готовности места (снята утром),")
    print("вторая — прямо в бумаге трейдера. Теперь сняты обе.")
    print("\nСам вопрос «выбирай по СЕБЕ, а не то, что названо")
    print("подтверждённым» остался слово в слово.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
