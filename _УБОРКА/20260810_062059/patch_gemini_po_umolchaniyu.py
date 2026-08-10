# -*- coding: utf-8 -*-
# GEMINI_PO_UMOLCHANIYU_V1
"""
ГЛАЗА ПО УМОЛЧАНИЮ. Gemini вместо 4o mini + чистка мёртвых надписей.

    python patch_gemini_po_umolchaniyu.py --suho    посмотреть
    python patch_gemini_po_umolchaniyu.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_gemini.

ПОЧЕМУ

    Твой же опыт всё показал. Один и тот же кадр, EURUSD D1:

      Gemini  — Аллигатор проснулся, губы выше зубов, зубы выше челюсти,
                цена выше всех линий, AO растёт и выше нуля.
      4o mini — линии переплетены, Аллигатор спит, тренда нет, AO
                колеблется вокруг нуля.

    Это не два мнения. Это один глаз видит, а другой нет. На картинке
    справа линии разведены, а гистограмма AO зелёная и растущая — права
    Gemini.

    Поэтому Биржа открывается на Gemini, а не на самой дешёвой. Цена та
    же. Захочешь другую — переключатель на месте, каталог не тронут.

ЗАОДНО

    Убираю мёртвые надписи «нажми РЫНОК (нужен сигнал Искры)» и «Нажми
    РЫНОК — Искра оживёт». Искры нет с шестого числа, а кабинет всё ещё
    посылает к ней. Текст меняется на честный.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
UI = KOREN / "Биржа" / "ui_torg.py"
MARKER = "# GEMINI_PO_UMOLCHANIYU_V1 - marker"
BAK = ".bak_gemini"

STAROE_DEFAULT = '''DEFAULT_MODEL = MODELS_CATALOG[0]["id"]
'''
NOVOE_DEFAULT = '''# GEMINI_PO_UMOLCHANIYU_V1: открываемся на модели, которая ВИДИТ кадр.
# Проверено Шефом на одном и том же кадре: 4o mini читал «Аллигатор спит,
# линии переплетены» там, где линии разведены и AO растёт. Цена та же,
# переключатель на месте — это только чем открывается кабинет.
DEFAULT_MODEL = next(
    (m["id"] for m in MODELS_CATALOG if m["id"].startswith("google/gemini")),
    MODELS_CATALOG[0]["id"])
'''

ZAMENY = (
    ('нажми РЫНОК (нужен сигнал Искры)', 'нажми РЫНОК'),
    ('Нажми РЫНОК — Искра оживёт', 'Нажми РЫНОК — стол накроется'),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("=" * 58)
    print("GEMINI ПО УМОЛЧАНИЮ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("=" * 58)

    if not UI.exists():
        print("x не вижу Биржа/ui_torg.py — запускай из КОРНЯ репо")
        return 1

    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0

    n = tekst.count(STAROE_DEFAULT)
    if n != 1:
        print(f"  x якорь модели найден {n} раз — файл не трогаю")
        return 1
    tekst = tekst.replace(STAROE_DEFAULT, NOVOE_DEFAULT, 1)
    print("  + кабинет открывается на Gemini")

    for staroe, novoe in ZAMENY:
        k = tekst.count(staroe)
        if k:
            tekst = tekst.replace(staroe, novoe)
            print(f"  + мёртвая надпись про Искру убрана ({k} шт.)")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_torg.py"):
        return 1

    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_gemini_po_umolchaniyu.py")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
