# -*- coding: utf-8 -*-
# MARKER: RUKA_PO_SMYSLU_V1
"""
РУКУ ИЩЕМ ПО СМЫСЛУ, А НЕ ПО ТОЧНОЙ БУКВЕ.

ПОЙМАНО ШЕФОМ (03.09), живьём, GBPUSD:
    ШЕФ: «ниже по лесенке что? на 30 минутке?»
    лог: [РУКА] ✕ stol_nсetazhe — такой руки нет (1/12)
    Илья: «Я не могу посмотреть "stol_nсetazhe". Возможно, ты
           опечатался. Могу посмотреть "stol_na_etazhe"».

    То есть рука была вызвана ПО-НАСТОЯЩЕМУ (RUKI_V_RAZGOVORE_V1
    доехал, руки в разговоре работают) — промах только в имени.

ПРИЧИНА (разобрано посимвольно, не на глаз)
    В имени `stol_nсetazhe` символ на шестом месте — КИРИЛЛИЧЕСКАЯ «с»
    (U+0441) вместо латинского `a_`. Модель ведёт весь разговор
    по-русски и на одном символе соскальзывает на кириллицу. Глазом
    неотличимо: «с» и «c» рисуются одинаково.
    А поиск руки был строгий: `ruki.get(imya)` — точное совпадение
    или ничего. Один невидимый символ = руки нет.

ЧТО ДЕЛАЕТСЯ
────────────
Поиск руки становится прощающим, в три шага:
  1. точное совпадение (как было — быстрый путь, ничего не меняется);
  2. нормализация: кириллические двойники → латиница, нижний регистр,
     прочь всё, кроме букв и цифр. `stol_nсetazhe` → `stolncetazhe`,
     `stol_na_etazhe` → `stolnaetazhe`;
  3. если и так не сошлось — ближайшая по написанию, но ТОЛЬКО при
     сходстве ≥ 0.82 и когда она заметно (≥0.10) обходит вторую.

    Замер на живом случае: `stol_na_etazhe` — 0.917, ближайшая чужая
    (`pokazat_etazh`) — 0.500. Разрыв огромный, спутать нечего.

    Опознание пишется в лог отдельной строкой:
      [РУКА] ~ stol_nсetazhe → понял как stol_na_etazhe (0.92)
    Чтобы всегда было видно, что рука подставлена по смыслу, а не
    названа точно.

ЧЕГО ЭТО НЕ ДЕЛАЕТ
    Не выдумывает руку, которой нет: если ничего не прошло порог —
    ответ прежний («такой руки нет, больше не проси»), и лог тот же.
    Не трогает список рук, работу, разговор, счётчик заходов.

Правит Биржа/llm.py. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "RUKA_PO_SMYSLU_V1"

STAR = '''            ruka = ruki.get(imya)
            zvali_ruki.append(imya)'''

NOV = '''            # RUKA_PO_SMYSLU_V1: прощаем кириллические двойники и
            # мелкие опечатки в имени руки — см. _nayti_ruku ниже.
            ruka, imya_tochno = _nayti_ruku(ruki, imya)
            if imya_tochno and imya_tochno != imya:
                imya = imya_tochno
            zvali_ruki.append(imya)'''

REZOLVER = '''

# ═══════════════════════════════════════════════════════════════
# RUKA_PO_SMYSLU_V1 — имя руки ищем по смыслу, а не по точной букве
# ═══════════════════════════════════════════════════════════════
# Модель говорит по-русски и иногда соскальзывает на кириллицу внутри
# латинского имени: `stol_nсetazhe` вместо `stol_na_etazhe` (шестой
# символ — кириллическая «с», глазом неотличима). Строгий ruki.get()
# на этом ронял вызов, и трейдер честно отвечал «такой руки нет».
# Здесь три шага: точно → нормализованно → ближайшее с высоким
# порогом. Выдумать руку, которой нет, эти шаги не могут.

_GOMOGLIFY = str.maketrans({
    "а": "a", "в": "b", "с": "c", "е": "e", "ё": "e", "н": "h", "к": "k",
    "м": "m", "о": "o", "р": "p", "т": "t", "у": "y", "х": "x",
    "ѕ": "s", "і": "i", "ј": "j",
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M",
    "О": "O", "Р": "P", "Т": "T", "У": "Y", "Х": "X",
})

_PORAG_SHODSTVA = 0.82   # ниже — не подставляем
_ZAPAS_NAD_VTOROY = 0.10  # лучшая должна заметно обойти вторую


def _norm_imya_ruki(s: str) -> str:
    s = (s or "").strip().strip('"').strip("'").translate(_GOMOGLIFY).lower()
    return "".join(ch for ch in s if ch.isalnum())


def _nayti_ruku(ruki: dict, imya: str):
    """(рука, настоящее_имя) или (None, None). Не выдумывает."""
    ruka = ruki.get(imya)
    if ruka:
        return ruka, imya

    tseli = list(ruki.keys())
    if not tseli:
        return None, None

    # шаг 2: нормализованное совпадение
    n = _norm_imya_ruki(imya)
    for k in tseli:
        if _norm_imya_ruki(k) == n:
            print(f"[РУКА] ~ {imya} → понял как {k} (двойники букв)")
            return ruki[k], k

    # шаг 3: ближайшее по написанию, с порогом и запасом над второй
    try:
        import difflib
        pary = sorted(
            ((difflib.SequenceMatcher(None, n, _norm_imya_ruki(k)).ratio(), k)
             for k in tseli), reverse=True)
        luchshaya, vtoraya = pary[0], (pary[1] if len(pary) > 1 else (0.0, ""))
        if luchshaya[0] >= _PORAG_SHODSTVA and \\
                (luchshaya[0] - vtoraya[0]) >= _ZAPAS_NAD_VTOROY:
            print(f"[РУКА] ~ {imya} → понял как {luchshaya[1]} "
                  f"({luchshaya[0]:.2f})")
            return ruki[luchshaya[1]], luchshaya[1]
    except Exception as e:
        print(f"[РУКА] поиск по смыслу сорвался: {e}")

    return None, None
'''


def _nayti_birzhu() -> Path:
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (koren / "Биржа", koren):
            if (p / "llm.py").exists() and (p / "ui_torg.py").exists():
                return p
    print("Не нашёл Биржа/llm.py.")
    s = input("Перетащи сюда папку «Биржа» и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if (p / "llm.py").exists():
        return p
    raise SystemExit("не та папка — там нет llm.py")


def main():
    f = _nayti_birzhu() / "llm.py"
    src = f.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"\n{f}: уже накачено")
        return
    if STAR not in src:
        print(f"\n{f}: ! не нашёл строку поиска руки дословно — файл правили, не трогаю")
        return
    if src.count(STAR) != 1:
        print(f"\n{f}: ! строка встретилась не один раз — не трогаю")
        return

    novyy = src.replace(STAR, NOV)
    novyy = novyy.rstrip("\n") + "\n" + REZOLVER + f"\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_ruka_smysl"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}: рука ищется по смыслу (.bak_ruka_smysl рядом)")
    print("   Точное имя — как было. Кириллические двойники и опечатки —")
    print("   опознаются, с записью в лог. Несуществующая рука — по-прежнему нет.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
