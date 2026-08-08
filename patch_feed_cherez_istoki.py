# -*- coding: utf-8 -*-
# FEED_CHEREZ_ISTOKI_V1
"""
КРАН НАЧИНАЕТ ХОДИТЬ ЧЕРЕЗ ИСТОКИ, А ИСТОКИ ВИДНЫ В ГНЁЗДАХ МАЯКА.

    python patch_feed_cherez_istoki.py --suho     посмотреть
    python patch_feed_cherez_istoki.py            сделать

Запускать из КОРНЯ репо. Перед этим положить:
    Биржа/istoki.py
    Биржа/истоки/mt5.py
    Биржа/истоки/csv.py

ЧТО МЕНЯЕТСЯ
    Раньше `bars()` знал два крана и выбирал `if mode == "tester"`.
    Теперь он спрашивает исток по имени у `istoki.py`, а тот ищет его
    в папке `Биржа/истоки/`. Положил туда файл — появился новый
    источник, код править не надо.

    При успешном ответе исток втыкается в гнездо Маяка и горит там
    постоянно. Гнездо ничего не маршрутизирует — это доска: видно,
    откуда течёт и чем занято.

ЧТО НЕ ЛОМАЕТСЯ
    Имена `real` и `tester` остаются рабочими — кнопки кабинета
    переключают как переключали. Если папки истоков нет или исток не
    открылся, `bars()` честно падает обратно на старую развилку и
    работает как раньше. Ничего не ломается от того, что чего-то нет.
"""
import argparse
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "FEED_CHEREZ_ISTOKI_V1"
TARGET = Path("Биржа") / "feed_source.py"
BAK = Path("Биржа") / "feed_source.py.bak_istoki"

A_OLD = '''    mode = get_feed_mode()["mode"]
    if mode == "tester":
        return _bars_from_folder(symbol, tf, count)
    return _bars_from_terminal(symbol, tf, count)
'''

A_NEW = '''    mode = get_feed_mode()["mode"]

    # FEED_CHEREZ_ISTOKI_V1: сперва спрашиваем ИСТОК — файл в папке
    # Биржа/истоки/. Положил туда файл — появился новый источник, эту
    # функцию править не надо. Исток, ответивший барами, втыкается в
    # гнездо Маяка: город видит, откуда течёт.
    try:
        import istoki as _ist
        _b, _p = _ist.bars(mode, symbol, tf, count)
        if _b:
            return _b, _p
    except Exception as _e_ist:
        print(f"[FEED] истоки недоступны ({_e_ist}) — иду прежним путём")

    # Истока нет, он молчит или папку ещё не положили — работаем как
    # работали. Отсутствие нового не должно ломать старое.
    if mode == "tester":
        return _bars_from_folder(symbol, tf, count)
    return _bars_from_terminal(symbol, tf, count)
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    b = Path("Биржа")
    if not (b / "istoki.py").exists():
        print("✗ нет Биржа/istoki.py — положи его туда")
        return 1
    est = sorted((b / "истоки").glob("*.py")) if (b / "истоки").exists() else []
    if not est:
        print("⚠ папка Биржа/истоки пуста — кран будет работать по-старому")
    else:
        print("Истоки на месте: " + ", ".join(f.stem for f in est))

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"\n✓ {MARKER} уже стоит — ничего не делаю")
        return 0

    n = src.count(A_OLD)
    if n != 1:
        print(f"\n✗ якорь найден {n} раз (нужно 1). Файл не тот — не трогаю.")
        return 1
    novyy = src.replace(A_OLD, A_NEW, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    if a.suho:
        print("\n[СУХОЙ ПРОГОН] всё сходится, ничего не записал.")
        return 0

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK.name}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print("\n  Проверить, что видно: python istoki_pokazat.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
