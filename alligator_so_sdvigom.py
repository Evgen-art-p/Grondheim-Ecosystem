# -*- coding: utf-8 -*-
"""
alligator_so_sdvigom.py — Аллигатор по канону Вильямса: СО СДВИГОМ везде.

Слово Шефа (21.09): сдвиг 8/5/3 — канон Вильямса. Считать без сдвига
неверно нигде, в том числе в резинке.

Что было: williams_core.py считал Челюсть, Зубы и Губы БЕЗ сдвига —
последнее насчитанное значение. На кадре (как в MT4) они нарисованы
сдвинутыми вперёд, поэтому глаз видел одно, а числа говорили другое.
Без сдвига брали: стол Синди (числа челюсть/зубы/губы), компас по
синей, пробой фрактала за Челюстью, раскрытие пасти (спит/открыт),
резинку Джастин, веер в global_anchor, трейлинг в tester_express.

Что стало (всё — в Биржа/williams_core.py):
  1. compute_alligator отдаёт Челюсть, Зубы, Губы СО СДВИГОМ 8/5/3 —
     то значение, что стоит ПОД текущей свечой. Раскрытие пасти
     (спит / открыт / сколько баров) — тоже по сдвинутым линиям.
     Ряды *_series остаются сырыми: разворотник (Necron) и кадр
     сдвигают их сами, второй раз сдвигать нельзя.
  2. Компас по синей: наклон Челюсти меряется по сдвинутой линии.
  3. Резинка Джастин: Губы и Зубы — со сдвигом.
Всё, кто берёт числа Аллигатора из ядра, получают канон сами.

Запуск: положить в корень репы, запустить. Сам находит
Биржа/williams_core.py. Делает копию williams_core.py.bak_alligator_sdvig.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "ALLIGATOR_SO_SDVIGOM_V1"
IMYA = "williams_core.py"
PRIMETA = "def compute_alligator"

PRAVKI = [
    # 1. Сами линии и раскрытие пасти
    (
        '    jaw   = jaw_s[-1]\n'
        '    teeth = teeth_s[-1]\n'
        '    lips  = lips_s[-1]\n',

        '    # ALLIGATOR_SO_SDVIGOM_V1: канон Вильямса — линии сдвинуты\n'
        '    # вперёд на 8/5/3 бара. Под текущей свечой стоит значение,\n'
        '    # насчитанное 8/5/3 бара назад. Его и отдаём — ровно то, что\n'
        '    # нарисовано на кадре и в MT4. Ряды *_series ниже остаются\n'
        '    # СЫРЫМИ: Necron и кадр сдвигают их сами.\n'
        '    _jaw_sh   = _shifted_series(jaw_s,   8)\n'
        '    _teeth_sh = _shifted_series(teeth_s, 5)\n'
        '    _lips_sh  = _shifted_series(lips_s,  3)\n'
        '    jaw   = _jaw_sh[-1]   if _jaw_sh   else None\n'
        '    teeth = _teeth_sh[-1] if _teeth_sh else None\n'
        '    lips  = _lips_sh[-1]  if _lips_sh  else None\n',
    ),
    (
        '    for i in range(len(jaw_s) - 1, -1, -1):\n'
        '        j = jaw_s[i]; t = teeth_s[i]; l = lips_s[i]\n',

        '    for i in range(len(_jaw_sh) - 1, -1, -1):\n'
        '        j = _jaw_sh[i]; t = _teeth_sh[i]; l = _lips_sh[i]\n',
    ),
    # 2. Компас по синей: наклон по сдвинутой Челюсти
    (
        '    if len(jaw_series) > slope_lookback:\n'
        '        cand = jaw_series[-1 - slope_lookback]\n',

        '    # ALLIGATOR_SO_SDVIGOM_V1: jaw уже со сдвигом 8 — прошлую\n'
        '    # берём тоже со сдвигом, иначе наклон меряется вкривь.\n'
        '    if len(jaw_series) > slope_lookback + 8:\n'
        '        cand = jaw_series[-1 - 8 - slope_lookback]\n',
    ),
    # 3. Резинка Джастин — Губы и Зубы со сдвигом
    (
        '        bars, lips_series, teeth_series, _rb_dir, _point)\n',

        '        bars,\n'
        '        _shifted_series(lips_series, 3) if lips_series else None,\n'
        '        _shifted_series(teeth_series, 5) if teeth_series else None,\n'
        '        _rb_dir, _point)  # ALLIGATOR_SO_SDVIGOM_V1\n',
    ),
]


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    p = os.path.join(papka, "Биржа", IMYA)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            if PRIMETA in f.read():
                return p
    except Exception:
        return None
    return None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        p = godnyy(papka)
        if p:
            return p

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
    put = nayti()
    if not put:
        print(f"✗ Биржа/{IMYA} не найден. Ничего не менял.")
        return

    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")

    if METKA in t:
        print("✓ Уже накатано раньше — ничего не менял.")
        return

    for n, (staroe, _) in enumerate(PRAVKI, 1):
        k = t.count(staroe)
        if k != 1:
            print(f"✗ Правка {n}: место не нашлось как ожидалось "
                  f"(совпадений: {k}). Ничего не менял. Покажи Брату.")
            return

    for staroe, novoe in PRAVKI:
        t = t.replace(staroe, novoe, 1)

    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return

    bak = put + ".bak_alligator_sdvig"
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
    print("  Аллигатор в ядре теперь со сдвигом 8/5/3 — как на кадре и в MT4.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
