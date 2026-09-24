# -*- coding: utf-8 -*-
"""
tri_bara_prisedanie.py — правило трёх баров для приседающего — в знания.

Слово Шефа 23–24.09: приседающий считается в пределах трёх баров — на
самом разворотном баре или не раньше чем за два бара до него
(разворотник — третий). Один или дорожка — всё равно.

Что было: в знаниях Синди стояло «разворотный и приседающий — один и
тот же бар» и «один приседающий прямо на разворотном баре — уже
достаточен». Она поняла это как «только на самом баре» и отказывалась,
когда приседающий стоял за бар до разворотника. 17.07 08:00 из-за этого
не переставила заявку ниже, на новый разворотник, — и заявка осталась
висеть слишком высоко.

Что делает:
  1. Знания A06 и A07 (MFI.md, RAZVOROTNIK.md) — дописано окно трёх
     баров словами Шефа.
  2. Биржа/stol.py — стол прямо говорит: «(в окне трёх баров —
     считается)».

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет все, потом пишет. Копии `.bak_tri_bara`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "TRI_BARA_PRISED_V1"
_SLOTY = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос", "слоты")

_OKNO = (
    "\n"
    "<!-- TRI_BARA_PRISED_V1 -->\n"
    "**Окно — три бара.** Приседающий считается, если он стоит на самом\n"
    "разворотном баре или не раньше чем за два бара до него: разворотник —\n"
    "третий. Один приседающий или дорожка подряд — всё равно. Приседающий\n"
    "за бар-два до разворотника — это тот же сигнал: рынок присел, а\n"
    "разворотный бар показал, в какую сторону. Дальше трёх баров — уже не\n"
    "считается.\n"
)


def _znaniya(slot):
    z = os.path.join(_SLOTY, slot, "знания")
    return [
        (os.path.join(z, "MFI.md"), [
            ("Один приседающий прямо на разворотном баре — уже достаточен.\n",
             "Один приседающий прямо на разворотном баре — уже достаточен.\n"
             + _OKNO),
            ("Разворотный и приседающий — один и тот же бар, увиденный с двух\n"
             "сторон (см. `RAZVOROTNIK.md`): разворотный — про форму, приседающий\n"
             "— про то, чем за эту форму заплатили.\n",
             "Чаще всего разворотный и приседающий — один и тот же бар, увиденный\n"
             "с двух сторон (см. `RAZVOROTNIK.md`): разворотный — про форму,\n"
             "приседающий — про то, чем за эту форму заплатили. Но приседающий\n"
             "может стоять и на бар-два раньше — окно трёх баров, выше.\n"),
        ]),
        (os.path.join(z, "RAZVOROTNIK.md"), [
            ("заплатили. Подробнее — `MFI.md`.\n",
             "заплатили. Подробнее — `MFI.md`.\n"
             "\n"
             "<!-- TRI_BARA_PRISED_V1 -->\n"
             "Приседающий не обязан стоять ровно на разворотнике: он\n"
             "считается в окне трёх баров — на самом разворотнике или за\n"
             "один-два бара до него (см. `MFI.md`).\n"),
        ]),
    ]


ZAMENY = dict(
    _znaniya("A06") + _znaniya("A07") + [
        (os.path.join("Биржа", "stol.py"), [
            ('        return f"есть — за {nazad} бар(а) до этого бара ({kogda})"\n',
             '        # TRI_BARA_PRISED_V1: прямо говорим, что это считается\n'
             '        return (f"есть — за {nazad} бар(а) до этого бара ({kogda}), "\n'
             '                f"в окне трёх баров — считается")\n'),
        ]),
    ]
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
        bak = put + ".bak_tri_bara"
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
    print("  Приседающий считается в окне трёх баров — в знаниях и на столе.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
