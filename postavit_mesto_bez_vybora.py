# -*- coding: utf-8 -*-
"""
postavit_mesto_bez_vybora.py · MARKER: MESTO_BEZ_VYBORA_V1

СЛОВО ШЕФА (21.08)
──────────────────
«Снимай привязку места от выбора входа, всё не важно — должны работать
Нининым кодом.»

ЧТО БЫЛО
────────
Готовность места стояла на трёх ногах: инструмент, этаж и ПАТТЕРН —
выбранное место входа. Нет паттерна — место молчит:

    [СОВЕТ] 🤐 A07 молчит: свой вход ещё не выбран
    [СОВЕТ] 🤐 A08 молчит: свой вход ещё не выбран

Правило было поставлено 08.08 из хорошего побуждения: чтобы никто не
работал чужой стратегией наугад. Но с тех пор изменилось главное —
движок стал ОБЩИМ. Точка ноль, волна 1, откат, наблюдение, попытки —
всё это лежит в hooks, council и столе, одинаково для всех трёх мест.
Разное только то, что человек сам скажет, глядя на стол.

Значит запирать место больше не за чем: чужой стратегии в коде нет,
есть одна структура и три её момента.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Готовность встаёт на две ноги: инструмент и этаж. Паттерн остаётся —
он по-прежнему читается, лежит меткой и попадает трейдеру в стопку, —
но больше не запирает дверь.

    выбрал вход — работает со своим выбором
    не выбрал   — работает так же, решая по столу

Метку никто не отменял и не подменяет: захочет выбрать — выберет, и
это будет его слово, а не наша галочка.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_mesto_bez_vybora.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "MESTO_BEZ_VYBORA_V1"
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


YAKOR = '''    return {"инструмент": instr, "этаж": etazh, "паттерн": pattern,
            "откуда_инструмент": otk_i if instr else "",
            "откуда_этаж": otk_e,
            "готов": bool(instr and etazh and pattern)}'''

NOV = '''    # MESTO_BEZ_VYBORA_V1: слово Шефа — «снимай привязку места от
    # выбора входа, должны работать Нининым кодом». Движок стал общим:
    # точка, волна, откат, наблюдение, попытки лежат в hooks, council и
    # столе одинаково для всех трёх мест. Чужой стратегии в коде больше
    # нет, значит и запирать дверь не за чем. Паттерн читается и идёт
    # трейдеру в стопку как прежде — просто он больше не пропуск.
    return {"инструмент": instr, "этаж": etazh, "паттерн": pattern,
            "откуда_инструмент": otk_i if instr else "",
            "откуда_этаж": otk_e,
            "готов": bool(instr and etazh)}'''

YAKOR2 = '''    if not r.get("паттерн"):
        return "свой вход ещё не выбран"'''

NOV2 = '''    # MESTO_BEZ_VYBORA_V1: без выбора место больше не молчит —
    # работает общим кодом. Строка оставлена на случай, если
    # готовность когда-нибудь снова свяжут с паттерном.'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "vybor.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    for yakor in (YAKOR, YAKOR2):
        if t.count(yakor) != 1:
            print(f"✗ якорь найден {t.count(yakor)} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return 1

    novyy = t.replace(YAKOR, NOV, 1).replace(YAKOR2, NOV2, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_bezvybora_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ место работает без выбора (копия: {bak.name})")
    print("\nСтроки «A07 молчит: свой вход ещё не выбран» больше не будет —")
    print("если у места есть инструмент и этаж, оно работает.")
    print("\nМетка выбора не тронута: захочет выбрать — выберет, и это")
    print("будет его слово. Просто теперь оно не пропуск на работу.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
