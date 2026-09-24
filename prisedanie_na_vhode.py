# -*- coding: utf-8 -*-
"""
prisedanie_na_vhode.py — вход без приседающего не принимается.

Слово Шефа 24.09: «приседающий — дыры». Прогон 24.09, первое же место:
01.07 04:00 Синди отдала SHORT «на краю медвежий разворотный бар с
приседающим» — а приседающего в окне трёх баров не было (последний
30.06 08:00, за пять баров). Стол она в этот раз не звала — отдала
приказ по одной картинке. Стоп выбило тем же баром.

Приседающий — факт MFI, а не толкование (как дивер). Вход по канону —
разворотный бар с приседающим на нём или за один-два бара до него.

Что делает (Биржа/ruki_treydera.py, рука приказа): при ENTER город сам
смотрит строку стола про приседающий. Если там «нет» — приказ не
принимается, и город говорит, где был последний приседающий, как
говорил бы стол. «Есть» или «не ясно» — идёт дальше как раньше.
В лог — строка [ПРИСЕД] ✓ или ✗.

Запуск: положить в корень репы, запустить. Сам находит файл, сперва
проверяет, потом пишет. Копия `.bak_prised_vhod`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "PRISEDANIE_NA_VHODE_V1"

ZAMENY = {
    os.path.join("Биржа", "ruki_treydera.py"): [(
        '                return ("Приказ НЕ отдан: не хватает " + ", ".join(net) +\n'
        '                        ". Войти вслепую нельзя — назови и позови снова.")\n',
        '                return ("Приказ НЕ отдан: не хватает " + ", ".join(net) +\n'
        '                        ". Войти вслепую нельзя — назови и позови снова.")\n'
        '            # PRISEDANIE_NA_VHODE_V1 (слово Шефа 24.09: «приседающий —\n'
        '            # дыры»). Приседающий — факт MFI, не толкование. Вход по\n'
        '            # канону — разворотник с приседающим на нём или за один-два\n'
        '            # бара до него. Нет его — вход не принимается, и город\n'
        '            # говорит, где был последний, — ровно как стол.\n'
        '            try:\n'
        '                import stol as _stol_mod\n'
        '                _pr = str(((_stol_mod.nakryt(symbol, rabochiy_etazh) or {})\n'
        '                           .get("приборы") or {}).get("приседающий_бар")\n'
        '                          or "")\n'
        '            except Exception as _e_pr:\n'
        '                _pr = ""\n'
        '                print(f"[ПРИСЕД] проверить не вышло ({_e_pr}) — не мешаю")\n'
        '            if _pr.startswith("нет"):\n'
        '                print(f"[ПРИСЕД] ✗ {symbol} {rabochiy_etazh}: вход без "\n'
        '                      f"приседающего — {_pr}")\n'
        '                return ("Приказ НЕ отдан: приседающего в окне трёх баров "\n'
        '                        "нет — стол говорит: «" + _pr + "». По канону вход — "\n'
        '                        "разворотный бар с приседающим на нём или за один-два "\n'
        '                        "бара до него (MFI.md). Посмотри стол и реши снова.")\n'
        '            if _pr:\n'
        '                print(f"[ПРИСЕД] ✓ {symbol} {rabochiy_etazh}: {_pr}")\n',
    )],
}


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if all(os.path.isfile(os.path.join(papka, p))
                        for p in ZAMENY) else None


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
    otv = input("Не нашёл репу. Перетащи сюда папку репы и нажми Enter: ")
    otv = otv.strip().strip('"').strip("'")
    return godnyy(otv) if otv else None


def main():
    repa = nayti()
    if not repa:
        print("✗ Репу не нашёл. Ничего не менял.")
        return
    gotovo = []
    for otn, zameny in ZAMENY.items():
        put = os.path.join(repa, otn)
        with open(put, "rb") as f:
            syroe = f.read()
        crlf = b"\r\n" in syroe
        tekst = syroe.decode("utf-8").replace("\r\n", "\n")
        if METKA in tekst:
            print(f"· {otn}: уже стоит")
            continue
        novyy = tekst
        for staroe, novoe in zameny:
            if novyy.count(staroe) != 1:
                print(f"✗ {otn}: не нашлось место правки — пришли Брату "
                      f"этот файл.\n  Ничего не менял.")
                return
            novyy = novyy.replace(staroe, novoe)
        if otn.endswith(".py"):
            ast.parse(novyy)
        gotovo.append((put, novyy, crlf))
    if not gotovo:
        print("✓ Всё уже стоит. Ничего не менял.")
        return
    for put, novyy, crlf in gotovo:
        bak = put + ".bak_prised_vhod"
        if not os.path.exists(bak):
            shutil.copy2(put, bak)
        with open(put, "wb") as f:
            f.write((novyy.replace("\n", "\r\n") if crlf else novyy)
                    .encode("utf-8"))
        try:
            if put.endswith(".py"):
                py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Вход без приседающего в окне трёх баров город не принимает — и говорит, где последний.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
