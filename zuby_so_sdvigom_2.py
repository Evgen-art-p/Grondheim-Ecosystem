# -*- coding: utf-8 -*-
"""
zuby_so_sdvigom_2.py — починка моей же ошибки в zuby_so_sdvigom.py.

Что сломалось: первый патч велел трейлингу брать ряд Зубов
(teeth_series) из market_data. А в market_data ряд НЕ доезжает —
туда кладутся только три числа: челюсть, зубы, губы. Трейлинг
каждый бар писал «Зубов со сдвигом нет — стоп не тяну» (202 раза
за прогон 21.09 23:10) и НИ РАЗУ не подтянул стоп.

Что стало: после alligator_so_sdvigom.py ядро само отдаёт Зубы
СО СДВИГОМ. Трейлинг просто берёт их — allig["teeth"].

Патч проверяет, что в ядре сдвиг уже стоит (ALLIGATOR_SO_SDVIGOM_V1),
иначе ничего не трогает.

Запуск: положить в корень репы, запустить. Сам находит Биржа/.
Копия: hooks.py.bak_zuby_sdvig_2. Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "ZUBY_SO_SDVIGOM_V2"
METKA_YADRA = "ALLIGATOR_SO_SDVIGOM_V1"

STAROE = (
    '    # ZUBY_SO_SDVIGOM_V1: Зубы СО СДВИГОМ на 5 баров, как у Вильямса.\n'
    '    # allig["teeth"] — сырое последнее значение; на кадре оно\n'
    '    # нарисовано на 5 баров правее свечи. Под текущим баром стоит\n'
    '    # значение, насчитанное 5 баров назад, — за ним и тянем стоп.\n'
    '    # Раньше стоп вставал «в будущее», вплотную к цене.\n'
    '    _ts = allig.get("teeth_series") or []\n'
    '    teeth = _ts[-1 - 5] if len(_ts) > 5 else None\n'
)
NOVOE = (
    '    # ZUBY_SO_SDVIGOM_V2: ряд Зубов в market_data не доезжает —\n'
    '    # там только числа. Ядро (ALLIGATOR_SO_SDVIGOM_V1) уже отдаёт\n'
    '    # Зубы СО СДВИГОМ — те, что под свечой. Их и берём.\n'
    '    teeth = allig.get("teeth")\n'
)


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    h = os.path.join(papka, "Биржа", "hooks.py")
    w = os.path.join(papka, "Биржа", "williams_core.py")
    if os.path.isfile(h) and os.path.isfile(w):
        try:
            with open(h, "r", encoding="utf-8") as f:
                if "_treyling_za_zubami" in f.read():
                    return papka
        except Exception:
            return None
    return None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        if godnyy(papka):
            return papka

    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = os.path.join(koren, imya)
                if godnyy(p) and p not in kandidaty:
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
    otv = otv.strip().strip('"').strip("'")
    return otv if godnyy(otv) else None


def main():
    repo = nayti()
    if not repo:
        print("✗ Папка Биржа не найдена. Ничего не менял.")
        return

    with open(os.path.join(repo, "Биржа", "williams_core.py"), "r", encoding="utf-8") as f:
        if METKA_YADRA not in f.read():
            print("✗ В ядре ещё нет сдвига (alligator_so_sdvigom.py не накатан).")
            print("  Сначала запусти его, потом этот. Ничего не менял.")
            return

    put = os.path.join(repo, "Биржа", "hooks.py")
    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")

    if METKA in t:
        print("✓ Уже накатано раньше — ничего не менял.")
        return

    k = t.count(STAROE)
    if k != 1:
        print(f"✗ Место в трейлинге не нашлось как ожидалось (совпадений: {k}).")
        print("  Ничего не менял. Покажи Брату.")
        return

    t = t.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return

    bak = put + ".bak_zuby_sdvig_2"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    vyvod = t.replace("\n", "\r\n") if crlf else t
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
    print("  Трейлинг снова тянет стоп — за Зубами со сдвигом из ядра.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
