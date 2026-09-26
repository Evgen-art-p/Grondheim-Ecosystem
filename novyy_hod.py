# -*- coding: utf-8 -*-
"""
novyy_hod.py — сравнивать с горкой текущего хода, а не позапрошлого.

Дневка, конец ноября 2023 (кадр MT92): рост от октябрьского дна 1.0448,
разворотник с приседающими, дивер у края. А город сравнивал этот рост
с ИЮЛЬСКОЙ горкой AO (0.0293, цена 1.12758) — через весь спуск
август–октябрь. «Цена прежний край не взяла» — и вход закрыт, линий нет.
Но июльский ход давно перекрыт: в октябре цена ушла ниже всего, что
было в поле зрения до июля. Это уже другой ход.

Правило: если после самой высокой горки AO (для LONG — самой глубокой
ямы) цена ушла за край ВСЕГО поля зрения в обратную сторону — прежний
ход перекрыт, и горка для сравнения ищется только после этого края,
в новом ходу. Обычный откат (волна 4) край всего поля не перекрывает —
там всё как было.

Проверено: ноябрь 2023 — пара теперь 21.11 → 29.11 внутри нового хода.
На всех прежних эталонах (H4 01.07, 05.03, 21.04, 17.07, 13.01, 26.02;
дневка 05.06, 13.01, 17.09) — вердикт тот же. На H4 январь–август 2025
вердикт меняется в 3% баров.

Что правит: Биржа/sverka_divera.py.

Запуск: положить в корень репы, запустить. Копия `.bak_novyy_hod`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "NOVYY_HOD_V1"
_A = ('    g, _a = (max(tochki, key=lambda t: t[1]) if verh\n'
      '             else min(tochki, key=lambda t: t[1]))\n')
_B = _A + (
    '    # NOVYY_HOD_V1: прежний ход перекрыт — ищем горку в новом. Если\n'
    '    # после самой высокой горки (самой глубокой ямы) цена ушла за\n'
    '    # край ВСЕГО поля зрения в обратную сторону, тот ход кончен:\n'
    '    # сравнивать надо внутри нового, после этого края.\n'
    '    for _nh in range(6):\n'
    '        _p_nh = max(i for i in range(len(ao)) if ao[i] is not None)\n'
    '        _posle_nh = range(g + 1, _p_nh + 1)\n'
    '        if not _posle_nh:\n'
    '            break\n'
    '        _k_nh = (min(_posle_nh, key=lambda k: lows[k]) if verh\n'
    '                 else max(_posle_nh, key=lambda k: highs[k]))\n'
    '        _do_nh = range(min(vid) if vid else 0, g + 1)\n'
    '        _slom = ((lows[_k_nh] < min(lows[k] for k in _do_nh)) if verh\n'
    '                 else (highs[_k_nh] > max(highs[k] for k in _do_nh)))\n'
    '        if not _slom:\n'
    '            break\n'
    '        _ost_nh = [(i, v) for i, v in tochki if i > _k_nh]\n'
    '        if not _ost_nh:\n'
    '            return {"ok": True, "est": False,\n'
    '                    "slovami": ("прежний ход перекрыт: цена ушла за край "\n'
    '                                "всего поля зрения — в новом ходу "\n'
    '                                + ("горок" if verh else "ямок")\n'
    '                                + " ещё нет"),\n'
    '                    "пары": [], "край": None}\n'
    '        g, _a = (max(_ost_nh, key=lambda t: t[1]) if verh\n'
    '                 else min(_ost_nh, key=lambda t: t[1]))\n'
)
ZAMENY = {os.path.join("Биржа", "sverka_divera.py"): [(_A, _B)]}


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
        bak = put + ".bak_novyy_hod"
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
    print("  Горка для сравнения ищется в текущем ходу, если прежний ход перекрыт.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
