# -*- coding: utf-8 -*-
"""
tri_bara_2.py — окно приседающего: разворотник и ТРИ бара до и после.

Слово Шефа 25.09: «разворотник и три бара до и после». Пример —
дневка 23.01.2023: разворотник 1.09267, приседающий 18.01 — третий
бар до него (19.01 и 20.01 между). По прежнему окну (два бара до)
он выпадал, и Синди честно не ставила заявку.

Что меняет (всё — на один бар шире, в обе стороны):
  · Биржа/stol.py — строка «приседающий» на столе;
  · Биржа/hooks.py — окно городского переезда заявки;
  · Биржа/council.py — побудка «к разворотнику пришёл приседающий»
    (до трёх баров после);
  · Биржа/ruki_treydera.py — проверка экстремума пускает заявку на
    разворотник до трёх баров назад, если он край хода и стоп за ним;
  · знания A06 и A07 (MFI.md, RAZVOROTNIK.md) — правило словами.

Запуск: положить в корень репы, запустить. Копии `.bak_tri_bara_2`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "TRI_BARA_V2"
_SL = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос", "слоты")


def _znaniya(slot):
    z = os.path.join(_SL, slot, "знания")
    return [
        (os.path.join(z, "MFI.md"), [
            ("**Окно — три бара.** Приседающий считается, если он стоит на самом\n"
             "разворотном баре или не раньше чем за два бара до него: разворотник —\n"
             "третий. Один приседающий",
             "<!-- TRI_BARA_V2 -->\n"
             "**Окно — три бара в обе стороны.** Приседающий считается, если он\n"
             "стоит на самом разворотном баре или не дальше трёх баров до него (и\n"
             "так же — после него). Один приседающий"),
            ("за бар-два до разворотника", "за один–три бара до разворотника"),
            ("через бар-два ПОСЛЕ", "через один–три бара ПОСЛЕ"),
        ]),
        (os.path.join(z, "RAZVOROTNIK.md"), [
            ("один-два бара до него (см. `MFI.md`).\n",
             "один–три бара до него или после (см. `MFI.md`).\n"
             "<!-- TRI_BARA_V2 -->\n"),
        ]),
    ]


ZAMENY = dict(
    [
        (os.path.join("Биржа", "stol.py"), [
            ("_PRISED_OKNO = 3\n",
             "# TRI_BARA_V2 (слово Шефа 25.09): разворотник и три бара до —\n"
             "# всего четыре бара в окне.\n"
             "_PRISED_OKNO = 4\n"),
        ]),
        (os.path.join("Биржа", "hooks.py"), [
            ("_OKNO_BAROV_PRISED = 2\n",
             "# TRI_BARA_V2 (слово Шефа 25.09): три бара до разворотника.\n"
             "_OKNO_BAROV_PRISED = 3\n"),
        ]),
        (os.path.join("Биржа", "council.py"), [
            ("                    for _k in (1, 2):\n",
             "                    # TRI_BARA_V2: до трёх баров после разворотника\n"
             "                    for _k in (1, 2, 3):\n"),
            ("                        _do = any(_sq_p(_k + 1 + j) for j in range(3))\n",
             "                        _do = any(_sq_p(_k + 1 + j) for j in range(4))\n"),
        ]),
        (os.path.join("Биржа", "ruki_treydera.py"), [
            ("                            for _x in _bs_e[-3:])\n",
             "                            for _x in _bs_e[-4:])  # TRI_BARA_V2\n"),
        ]),
    ]
    + _znaniya("A06") + _znaniya("A07")
)


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
        bak = put + ".bak_tri_bara_2"
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
    print("  Окно приседающего — разворотник и три бара до и после.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
