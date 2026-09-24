# -*- coding: utf-8 -*-
"""
pervaya_tochka_ceny.py — первая точка цены берётся с того же места,
что и горка AO.

Слово Шефа 24.09 («да»): «по-моему, дивер не верно, линия на цене».
Первую точку AO город брал верно — самую высокую горку. А первую точку
цены искал в окне от этой горки до ближайшего ОТКАТА цены. Если откат
случался не скоро, окно растягивалось и хватало чужую вершину. Кадр
05.03: горка AO — 17.02, а цену город взял с 26.02 (1.0529) — другой
бугор. Цена и AO с разных мест — ровно то, чего мы требуем от Синди.

AO отстаёт от цены: вершина цены бывает на той же свече или чуть
раньше горки AO, а не позже. Теперь первая точка цены — край цены на
подъёме к горке AO: от ямки AO слева до самой горки (для LONG —
зеркально, на спуске к яме).

Проверено: на главных входах (01.07, 05.03, 21.04, 26.02, 17.07, 13.01)
вердикт не меняется — меняются линии и числа. По всем барам января–
августа вердикт «есть/нет» меняется примерно в 4% случаев.

Что правит: Биржа/sverka_divera.py (и линии на кадре, и проверку
большого края — они берут точки оттуда).

Запуск: положить в корень репы, запустить. Копия `.bak_pervaya_tochka`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "PERVAYA_TOCHKA_CENY_V1"
_A = '        do, pos = range(g, t + 1), range(t + 1, p + 1)\n'
ZAMENY = {
    os.path.join("Биржа", "sverka_divera.py"): [(
        _A,
        _A +
        '        # PERVAYA_TOCHKA_CENY_V1 (слово Шефа 24.09): первая точка цены\n'
        '        # — с того же места, что и горка AO. AO отстаёт от цены, так\n'
        '        # что край цены — на подъёме к горке (для LONG — на спуске к\n'
        '        # яме): от ямки AO слева до самой горки. Раньше окно шло до\n'
        '        # отката цены и хватало чужую, более позднюю вершину.\n'
        '        _s = g\n'
        '        while (_s - 1 >= 0 and ao[_s - 1] is not None\n'
        '               and ((ao[_s - 1] <= ao[_s]) if verh\n'
        '                    else (ao[_s - 1] >= ao[_s]))):\n'
        '            _s -= 1\n'
        '        do = range(_s, g + 1)\n',
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
        bak = put + ".bak_pervaya_tochka"
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
    print("  Первая точка цены — с того же места, что и горка AO.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
