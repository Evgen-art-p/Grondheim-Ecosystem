# -*- coding: utf-8 -*-
"""
prisedanie_posle.py — две правки после дневки 2023 («снова не переставляет»).

1. ЗАЯВКА БЕЗ ТОЧКИ ОТМЕНЫ. 18.01.2023 SHORT-заявка на 1.07658 со
   стопом 1.0888. Цена ушла выше стопа, а заявка висела ещё несколько
   баров, пока Синди не сняла её сама. Правило «бар закрылся за стопом
   заявки — сигнал умер, заявку снять» в городе есть, но оно смотрит на
   точку отмены, а исполнитель при рождении заявки её не ставил.
   Теперь ставит: точка отмены = стоп заявки.

2. ПРИСЕДАЮЩИЙ ПОСЛЕ РАЗВОРОТНИКА. Слово Шефа: окно три бара — и ДО,
   и ПОСЛЕ разворотника. 30.01.2023 медвежий разворотник 1.09138,
   приседающий пришёл 31.01 — через бар после. Город «после» не видел
   вовсе: не будил, стол молчал, проверки не пускали.
   Теперь:
     · Совет будит: «к разворотнику BEAR 2023.01.30 @ 1.09138 пришёл
       приседающий через 1 бар — в окне трёх баров, считается»
       (если до и на самом разворотнике приседающего не было и это
       первый приседающий после него);
     · проверка экстремума пускает заявку на разворотник бар-два назад,
       если он и есть край хода, а стоп за ним (левые входы — стоп НЕ за
       краем — по-прежнему отбиваются);
     · в знаниях Синди (MFI.md, A06 и A07) — что приседающий может
       прийти и после разворотника.

Что правит: исполнитель (мозг.py), Биржа/council.py,
Биржа/ruki_treydera.py, знания A06 и A07 (MFI.md).

Запуск: положить в корень репы, запустить. Копии `.bak_prised_posle`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "PRISEDANIE_POSLE_V1"
_CEH = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха")
_ISP = os.path.join(_CEH, "контора", "слоты", "исполнитель", "мозг.py")

_POVOD_A = (
    '        if rb.get("direction"):\n'
    '            povody.append(f"разворотный бар {rb[\'direction\']} @ {rb[\'price\']}")\n'
)
_POVOD_B = _POVOD_A + (
    '        # PRISEDANIE_POSLE_V1 (слово Шефа: окно три бара — и до, и\n'
    '        # после разворотника). Этот бар — приседающий, а разворотник\n'
    '        # был бар-два назад без приседающего до и на себе: будим.\n'
    '        elif len(bs) >= 8:\n'
    '            try:\n'
    '                from williams_core import compute_mfi as _mfi_p\n'
    '\n'
    '                def _sq_p(m):\n'
    '                    return (_mfi_p(bs[-m], bs[-m - 1], point=point)\n'
    '                            .get("type") == "SQUAT")\n'
    '\n'
    '                if _sq_p(1):\n'
    '                    for _k in (1, 2):\n'
    '                        _n = len(bs) - _k\n'
    '                        _rbk = detect_necron_bar(\n'
    '                            bs[:_n], (al.get("jaw_series") or [])[:_n],\n'
    '                            (al.get("teeth_series") or [])[:_n],\n'
    '                            (al.get("lips_series") or [])[:_n])\n'
    '                        if not _rbk.get("direction"):\n'
    '                            continue\n'
    '                        _do = any(_sq_p(_k + 1 + j) for j in range(3))\n'
    '                        _mezhdu = any(_sq_p(j) for j in range(2, _k + 1))\n'
    '                        if not _do and not _mezhdu:\n'
    '                            _d_p = str(bs[-(_k + 1)].get("date") or "")[:16]\n'
    '                            povody.append(\n'
    '                                f"к разворотнику {_rbk[\'direction\']} {_d_p} "\n'
    '                                f"@ {_rbk[\'price\']} пришёл приседающий через "\n'
    '                                f"{_k} бар(а) — в окне трёх баров, считается")\n'
    '                        break\n'
    '            except Exception as _e_p:\n'
    '                print(f"[КЛЮЧ] приседающий после разворотника не "\n'
    '                      f"посчитался: {_e_p}")\n'
)

_EKS_A = (
    '                    _ne_kray = ((_moy_e < _kr_e - _dop_e) if _short_e\n'
    '                                else (_moy_e > _kr_e + _dop_e))\n'
)
_EKS_B = _EKS_A + (
    '                    # PRISEDANIE_POSLE_V1: приседающий мог прийти после\n'
    '                    # разворотника — тогда заявка ставится на тот бар, он\n'
    '                    # бар-два назад. Край хода среди последних трёх баров\n'
    '                    # и стоп ЗА этим краем — это вход на экстремуме. Стоп\n'
    '                    # не за краем — по-прежнему левый вход.\n'
    '                    if _ne_kray and isinstance(stop, (int, float)):\n'
    '                        _za_e = ((stop >= _kr_e - _dop_e) if _short_e\n'
    '                                 else (stop <= _kr_e + _dop_e))\n'
    '                        _ned_e = any(\n'
    '                            ((_x["high"] >= _kr_e - _dop_e) if _short_e\n'
    '                             else (_x["low"] <= _kr_e + _dop_e))\n'
    '                            for _x in _bs_e[-3:])\n'
    '                        if _za_e and _ned_e:\n'
    '                            _ne_kray = False\n'
    '                            print(f"[ЭКСТРЕМУМ] ✓ {symbol} {rabochiy_etazh}: "\n'
    '                                  f"край хода {_kr_e} бар-два назад, стоп "\n'
    '                                  f"за ним — вход на том разворотнике")\n'
)

_MFI_A = ("разворотный бар показал, в какую сторону. Дальше трёх баров — уже не\n"
          "считается.\n")
_MFI_B = _MFI_A + (
    "\n"
    "<!-- PRISEDANIE_POSLE_V1 -->\n"
    "Бывает и наоборот: приседающий приходит через бар-два ПОСЛЕ\n"
    "разворотника. Это тоже считается — окно три бара в обе стороны.\n"
    "Тогда заявку ставят (или переставляют) на тот разворотник: вход за\n"
    "его край, стоп за другой. Город разбудит словами «к разворотнику\n"
    "пришёл приседающий».\n"
)


def _mfi(slot):
    return (os.path.join(_CEH, "торговый_хаос", "слоты", slot, "знания",
                         "MFI.md"), [(_MFI_A, _MFI_B)])


ZAMENY = dict([
    (_ISP, [(
        '            "_ждёт_с":   bar_time,\n',
        '            "_ждёт_с":   bar_time,\n'
        '            # PRISEDANIE_POSLE_V1: точка отмены — стоп заявки. Бар\n'
        '            # закрылся за ним до срабатывания — сигнал умер, город\n'
        '            # снимает заявку сам (правило в hooks уже есть).\n'
        '            "signal_start": stop,\n',
    )]),
    (os.path.join("Биржа", "council.py"), [(_POVOD_A, _POVOD_B)]),
    (os.path.join("Биржа", "ruki_treydera.py"), [(_EKS_A, _EKS_B)]),
    _mfi("A06"),
    _mfi("A07"),
])


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
        bak = put + ".bak_prised_posle"
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
    print("  Заявка снимается за стопом; приседающий после разворотника будит и считается.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
