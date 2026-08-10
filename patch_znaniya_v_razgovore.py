# -*- coding: utf-8 -*-
# ZNANIYA_V_RAZGOVORE_V1
"""
ЗНАНИЯ — В РАЗГОВОР. Откуда взялись «уровни сопротивления».

    python patch_znaniya_v_razgovore.py --suho    посмотреть
    python patch_znaniya_v_razgovore.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копии рядом: .bak_znaniya.

ЧТО НАШЛОСЬ

    Ты спросил, откуда она взяла уровни — их правда нет в её системе.
    Полез смотреть и нашёл: В РАЗГОВОРЕ ЕЙ НЕ ДАЮТ ЗНАНИЙ ВОВСЕ.

    Папка знаний — книга Котина, индикаторы, паттерны, разворотный бар,
    входы — загружается ровно в одном месте: когда она РАБОТАЕТ по
    кнопке РЫНОК. А когда ты с ней разговариваешь, ей передают бумагу
    места, стол и картинку — и всё. Полки за спиной нет.

    Спрашиваешь про паттерн — отвечать нечем, кроме общей эрудиции.
    Оттуда и лезут «уровни сопротивления», «цена у верхних уровней» и
    прочий язык из интернета. Это не она выдумывает — это дыра в том,
    что ей дали.

ЧТО СТАНОВИТСЯ

    В разговоре у неё та же полка, что и в работе: все пять файлов.
    Спросил про паттерн — отвечает по своей книге, а не по чужой.

    Плюс короткая оговорка в бумаге: говори языком своей школы. В ней
    есть пасть и зубы, фракталы, приседающий бар, разворотный бар, AO
    и дивергенция, волны и откаты. Уровней поддержки и сопротивления в
    ней нет. Не знаешь — скажи, что не знаешь, а не подставляй чужое
    слово.

ЧЕСТНО ПРО ЦЕНУ

    Полка тяжёлая — около сорока тысяч знаков. Каждый ответ в чате
    станет дороже. В работе это и так грузилось всегда, а разговоров
    у тебя десятки, не тысячи, так что переживём. Станет дорого —
    оставим в разговоре входы, паттерны и разворотный бар, а книгу
    Котина будет поднимать по запросу, у неё для этого уже есть рука.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
SLOTS = ("A06", "A07", "A08")
MARKER = "# ZNANIYA_V_RAZGOVORE_V1 - marker"
BAK = ".bak_znaniya"

STAROE_SYSTEM = '''    system = prompt + work_ctx
'''
NOVOE_SYSTEM = '''    # ZNANIYA_V_RAZGOVORE_V1: полка за спиной. В разговоре знаний не было
    # вовсе — ни книги Котина, ни входов, ни паттернов, — и на вопрос про
    # паттерн отвечать было нечем, кроме общей эрудиции. Отсюда «уровни
    # сопротивления», которых в этой школе нет.
    _znaniya = ""
    try:
        _znaniya = _znaniya_roli()
    except Exception:
        pass
    work_ctx += (
        "\\n\\nГоворишь языком своей школы. В ней есть пасть и зубы "
        "Аллигатора, фракталы, приседающий бар, разворотный бар, AO и "
        "дивергенция, волны и откаты. «Уровней поддержки и сопротивления» "
        "в ней нет — это чужой словарь. Не знаешь чего-то — так и скажи, "
        "не подставляй чужое слово вместо своего.\\n")

    system = prompt + work_ctx
'''

STAROE_ZOV = '''        return _chat_fn(system=system, user=question, history=history,
'''
NOVOE_ZOV = '''        return _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
'''

STEZHKI = (
    ("полка в разговор", STAROE_SYSTEM, NOVOE_SYSTEM),
    ("полка в вызов", STAROE_ZOV, NOVOE_ZOV),
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
    print("ЗНАНИЯ В РАЗГОВОР" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("=" * 58)

    if not SLOTY.exists():
        print("x не вижу слоты — запускай из КОРНЯ репо")
        return 1

    vse_ok = True
    for slot in SLOTS:
        put = SLOTY / slot / "мозг.py"
        if not put.exists():
            print(f"  {slot}: мозга нет — пропускаю")
            continue
        tekst = put.read_text(encoding="utf-8")
        if MARKER in tekst:
            print(f"  {slot}: уже накатано")
            continue
        sboy = False
        for nazv, staroe, novoe in STEZHKI:
            n = tekst.count(staroe)
            if n != 1:
                print(f"  x {slot}: якорь «{nazv}» найден {n} раз — не трогаю")
                if n == 0:
                    print("    Скорее всего не накатан "
                          "patch_razgovor_so_stolom.py — поставь сперва его.")
                sboy = True
                vse_ok = False
                break
            tekst = tekst.replace(staroe, novoe, 1)
            print(f"    · {nazv}")
        if sboy:
            continue
        tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
        if not proverit_python(tekst, slot):
            vse_ok = False
            continue
        if a.suho:
            print(f"  {slot}: + готов")
            continue
        shutil.copy2(put, put.with_suffix(put.suffix + BAK))
        put.write_text(tekst, encoding="utf-8")
        print(f"  {slot}: + накатано")

    print("-" * 58)
    if not vse_ok:
        return 1
    if a.suho:
        print("Сухой прогон прошёл. Накатывать: "
              "python patch_znaniya_v_razgovore.py")
        return 0
    print("Спроси её снова: «какой паттерн ты ждёшь?».")
    print("Ответ должен быть на языке её школы, а не общими словами.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
