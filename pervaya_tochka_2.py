# -*- coding: utf-8 -*-
"""
pervaya_tochka_2.py — первая точка цены: вся горка AO, а не только подъём.

Прогон 25.09, дневка 2025: минус один — SHORT 05.06, и Шеф прав, вход
неверный. Моя ошибка в прошлой правке (pervaya_tochka_ceny.py): я брал
край цены только на ПОДЪЁМЕ к горке AO — «AO отстаёт, значит вершина
цены раньше». А в апреле вышло наоборот: горка AO 17.04, а вершина цены
1.15727 — 21.04, четыре дня ПОСЛЕ неё, пока AO ещё стоял у самой горки.
Город взял первой точкой 1.14736 (11.04) и решил, что 05.06 цена
(1.14944) край взяла. А настоящий край 1.15727 взят не был — проверка
края должна была её остановить.

Теперь первая точка цены — край цены по всей горке AO: от ямки слева
до самой горки И дальше, пока AO после горки ещё идёт вниз (для LONG —
зеркально), но не дальше отката цены. На кадре 05.03 чужую вершину
26.02 это по-прежнему не хватает.

Проверено: SHORT 05.06.2025 на дневке — город теперь говорит «цена
прежний край не взяла», вход отбился бы. Дневка 13.01 и 17.09, H4
01.07, 05.03, 21.04, 17.07, 13.01, 26.02 — вердикт тот же.

Что правит: Биржа/sverka_divera.py.

Запуск: положить в корень репы, запустить. Копия `.bak_pervaya_tochka_2`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "PERVAYA_TOCHKA_V2"
ZAMENY = {
    os.path.join("Биржа", "sverka_divera.py"): [(
        '            _s -= 1\n'
        '        do = range(_s, g + 1)\n',
        '            _s -= 1\n'
        '        # PERVAYA_TOCHKA_V2: и вправо — пока AO после горки ещё\n'
        '        # спускается (для LONG — поднимается), но не дальше отката\n'
        '        # цены. Вершина цены бывает и ПОСЛЕ горки AO (апрель 2025).\n'
        '        _e = g\n'
        '        while (_e + 1 <= t and ao[_e + 1] is not None\n'
        '               and ((ao[_e + 1] <= ao[_e]) if verh\n'
        '                    else (ao[_e + 1] >= ao[_e]))):\n'
        '            _e += 1\n'
        '        do = range(_s, _e + 1)\n',
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
        bak = put + ".bak_pervaya_tochka_2"
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
    print("  Первая точка цены — вся горка AO, вместе с вершиной цены после неё.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
