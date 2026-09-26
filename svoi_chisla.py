# -*- coding: utf-8 -*-
"""
svoi_chisla.py — две правки после дневки 2023 (−3.66R, «хуже стало»).

1. ВХОД ПО СВОИМ ЖЕ ЧИСЛАМ БЕЗ РАСХОЖДЕНИЯ. Два стопа из пяти:
     27.02 LONG — её числа: цена 0.959 → 1.0533 (ВЫШЕ), AO −0.0285 →
       −0.0162. Для LONG цена во второй точке должна быть НИЖЕ. Город
       сказал «нет, сила не слабее прежней», но ни одна проверка не
       отбила: край, одна яма, экстремум — не про этот случай.
     23.03 SHORT — её числа: цена 1.106 → 1.09299 (НИЖЕ). Для SHORT
       цена во второй точке должна быть ВЫШЕ.
   Её же числа говорили «расхождения нет». Это не толкование города, а
   её собственное утверждение — проверяем, что оно сходится с тем, что
   она заявляет. Не сходится — вход не принят, она получает, чего не
   хватает.

2. ТОНКАЯ ЛИНИЯ СРАВНИВАЛА НЕ С ТЕМ. 23.03 город нашёл «дивер у края»:
   январь 1.09267 → март 1.09299. А между ними была вершина 02.02 —
   1.10329, выше обоих. Первую точку цены у тонкой пары я брал только
   вокруг её горки AO (правка «первая точка цены»), и февральскую
   вершину город пропустил. Теперь у тонких пар (внутри матрёшки)
   первая точка цены — по всему отрезку от горки AO до отката, как было
   раньше. У толстой пары — как сейчас, по горке AO.

Проверено на дневке 2023 и эталонах H4/D1: 23.03 — тонкого дивера нет;
18.01, 02.02 (+1.34R), 14.04, 06.09, 20.09, 29.11, 28.12, QV26, 01.07,
17.07, 21.04, дневка 13.01.25 и 05.06.25 — как было.

Что правит: Биржа/ruki_treydera.py и Биржа/sverka_divera.py.

Запуск: положить в корень репы, запустить. Копии `.bak_svoi_chisla`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "SVOI_CHISLA_V1"
_PR = '            # PRISEDANIE_NA_VHODE_V1 (слово Шефа 24.09: «приседающий —\n'
_CH = (
    '            # SVOI_CHISLA_V1: её собственные четыре числа должны\n'
    '            # показывать расхождение — это её же утверждение, не\n'
    '            # толкование города. LONG: цена ниже, AO выше (яма мельче).\n'
    '            # SHORT: цена выше, AO ниже (горка ниже).\n'
    '            _short_ch = str(napravlenie or "").upper() == "SHORT"\n'
    '            _c1, _c2 = _tochki["цена_1"], _tochki["цена_2"]\n'
    '            _a1, _a2 = _tochki["ao_1"], _tochki["ao_2"]\n'
    '            _c_ok = (_c2 > _c1) if _short_ch else (_c2 < _c1)\n'
    '            _a_ok = (_a2 < _a1) if _short_ch else (_a2 > _a1)\n'
    '            if not (_c_ok and _a_ok):\n'
    '                _nado = ("для SHORT цена во второй точке выше первой, а AO "\n'
    '                         "ниже" if _short_ch else\n'
    '                         "для LONG цена во второй точке ниже первой, а AO "\n'
    '                         "выше (яма мельче)")\n'
    '                _est = (f"у тебя цена {_c1} → {_c2} "\n'
    '                        f"({\'выше\' if _c2 > _c1 else \'ниже\'}), AO {_a1} → "\n'
    '                        f"{_a2} ({\'выше\' if _a2 > _a1 else \'ниже\'})")\n'
    '                print(f"[СВОИ ЧИСЛА] ✗ {symbol} {rabochiy_etazh} "\n'
    '                      f"{napravlenie}: {_est} — расхождения нет")\n'
    '                return ("Приказ НЕ отдан: твои же четыре числа не "\n'
    '                        "показывают расхождения. Нужно: " + _nado +\n'
    '                        ". А " + _est + ". Посмотри кадр ещё раз: где "\n'
    '                        "пара, в которой это есть? Если её нет — входа "\n'
    '                        "нет.")\n'
)
ZAMENY = {
    os.path.join("Биржа", "ruki_treydera.py"): [(_PR, _CH + _PR)],
    os.path.join("Биржа", "sverka_divera.py"): [
        ('    def _para(g):\n', '    def _para(g, pervaya=True):\n'),
        ('        do = range(_s, _e + 1)\n',
         '        # SVOI_CHISLA_V1: у тонких пар (внутри матрёшки) первая\n'
         '        # точка цены — по всему отрезку от горки AO до отката:\n'
         '        # иначе вершина между ними (02.02.2023) выпадала.\n'
         '        do = range(_s, _e + 1) if pervaya else range(g, t + 1)\n'),
        ('        r = _para(g)\n', '        r = _para(g, pervaya=not pary)\n'),
    ],
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
        bak = put + ".bak_svoi_chisla"
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
    print("  Вход по числам без расхождения не принимается; тонкая пара начинается от края прошлой.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
