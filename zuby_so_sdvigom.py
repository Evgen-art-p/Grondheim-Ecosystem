# -*- coding: utf-8 -*-
"""
zuby_so_sdvigom.py — трейлинг за Зубами берёт Зубы СО СДВИГОМ.

Что было: _treyling_za_zubami в Биржа/hooks.py брала Зубы без сдвига —
последнее насчитанное значение. На кадре оно нарисовано на 5 баров
ПРАВЕЕ текущей свечи. Стоп вставал туда, где Зубы будут через пять
баров, а не туда, где они стоят под свечой (как у Вильямса в MT4).
Пример: 2025.05.30 08:00, SHORT от 1.13447 — стоп уехал на 1.13322,
а под свечой Зубы лежали около 1.1307, и цена до них не дошла.

Что стало: трейлинг берёт значение Зубов, которое стоит ПОД текущим
баром — сырое значение пятью барами раньше (как _shifted_series(…, 5)).
Общие Зубы в williams_core.py НЕ трогаются — ими пользуются другие
приборы, и там это сделано сознательно.

Запуск: положить в корень репы, запустить (двойной клик или python).
Сам находит Биржа/hooks.py. Делает копию hooks.py.bak_zuby_sdvig.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil
import sys

METKA = "ZUBY_SO_SDVIGOM_V1"
SDVIG = 5

STAROE = (
    '    allig = md.get("alligator", {}) or {}\n'
    '    teeth = allig.get("teeth")\n'
    '    close = (md.get("price", {}) or {}).get("close")\n'
    '    if teeth is None or close is None:\n'
    '        return\n'
)

NOVOE = (
    '    allig = md.get("alligator", {}) or {}\n'
    '    # ZUBY_SO_SDVIGOM_V1: Зубы СО СДВИГОМ на 5 баров, как у Вильямса.\n'
    '    # allig["teeth"] — сырое последнее значение; на кадре оно\n'
    '    # нарисовано на 5 баров правее свечи. Под текущим баром стоит\n'
    '    # значение, насчитанное 5 баров назад, — за ним и тянем стоп.\n'
    '    # Раньше стоп вставал «в будущее», вплотную к цене.\n'
    '    _ts = allig.get("teeth_series") or []\n'
    '    teeth = _ts[-1 - 5] if len(_ts) > 5 else None\n'
    '    close = (md.get("price", {}) or {}).get("close")\n'
    '    if teeth is None or close is None:\n'
    '        if positions and close is not None:\n'
    '            print("[ТРЕЙЛ] ⚠️  Зубов со сдвигом нет — стоп не тяну")\n'
    '        return\n'
)


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    p = os.path.join(papka, "Биржа", "hooks.py")
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            if "_treyling_za_zubami" in f.read():
                return p
    except Exception:
        return None
    return None


def nayti_hooks():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        p = godnyy(papka)
        if p:
            return p

    # соседние папки
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = godnyy(os.path.join(koren, imya))
                if p and p not in kandidaty:
                    kandidaty.append(p)
        except Exception:
            pass

    if len(kandidaty) == 1:
        otv = input(f"Нашёл: {kandidaty[0]}\nЭтот? (Enter — да, н — нет): ")
        if otv.strip().lower() not in ("н", "n", "нет", "no"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p}")
        otv = input("Какой? Цифра: ").strip()
        if otv.isdigit() and 1 <= int(otv) <= len(kandidaty):
            return kandidaty[int(otv) - 1]

    otv = input("Перетащи сюда папку репы (где лежит папка Биржа) и нажми Enter:\n")
    return godnyy(otv.strip().strip('"').strip("'"))


def main():
    put = nayti_hooks()
    if not put:
        print("✗ Биржа/hooks.py не найден. Ничего не менял.")
        return

    with open(put, "rb") as f:
        syroe = f.read()
    tekst = syroe.decode("utf-8")
    crlf = "\r\n" in tekst
    tekst_n = tekst.replace("\r\n", "\n")

    if METKA in tekst_n:
        print("✓ Уже накатано раньше — ничего не менял.")
        return

    skolko = tekst_n.count(STAROE)
    if skolko != 1:
        print(f"✗ Место в трейлинге не нашлось как ожидалось (совпадений: {skolko}).")
        print("  Ничего не менял. Покажи Брату.")
        return

    novyy = tekst_n.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return

    bak = put + ".bak_zuby_sdvig"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)

    vyvod = novyy.replace("\n", "\r\n") if crlf else novyy
    with open(put, "wb") as f:
        f.write(vyvod.encode("utf-8"))

    try:
        py_compile.compile(put, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, put)
        print(f"✗ Не скомпилировался, вернул как было: {e}")
        return

    print(f"✓ Готово: {put}")
    print(f"  копия до правки: {bak}")
    print("  Трейлинг теперь тянет стоп за Зубами, что стоят ПОД свечой.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
