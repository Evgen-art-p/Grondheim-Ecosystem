# -*- coding: utf-8 -*-
"""
ekstremum_na_vhode.py — разворотник должен быть самим экстремумом цены.

Слово Шефа 24.09: «снова левые входы.. цена не экстремум». 26.02 и
04.04 (и 11.03 04:00) Синди входила SHORT на медвежьем разворотнике, а
вершина хода была раньше и выше: 26.02 — бар 1.05248, а край 24.02 был
1.05283; 04.04 — бар 1.11072, а край 03.04 был 1.11456. Дивер город
видел верно, но разворотник стоял не на экстремуме, а ниже него.
По Вильямсу дивергентный бар — это и есть новый край цены.

Что делает (Биржа/ruki_treydera.py, рука приказа): при ENTER, когда
город видит расхождение, он смотрит, где его край цены. Если этот бар
НЕ сам край (для SHORT — его вершина ниже вершины хода, для LONG — его
дно выше дна хода), вход не принимается, и Синди получает в ответ, где
был экстремум и какой у неё бар.

Проверено на входах прошлых прогонов:
  отбило бы: 26.02, 11.03 04:00, 04.04 (все три −1R);
  пропустило бы: 05.03, 11.03 20:00 (−1R, там бар и был краем),
  вершины 01.07 и 21.04, LONG 17.07 (все в плюс);
  отбило бы и январский LONG 13.01 (+1.38R): бар 1.02248, а дно хода
  было 1.02128 — он тоже был «не на экстремуме», просто повезло.

Запуск: положить в корень репы, запустить. Копия `.bak_ekstremum`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "EKSTREMUM_NA_VHODE_V1"
_A = '                        "край, или реши снова.")\n'
ZAMENY = {
    os.path.join("Биржа", "ruki_treydera.py"): [(
        _A,
        _A +
        '            # EKSTREMUM_NA_VHODE_V1 (слово Шефа 24.09: «цена не\n'
        '            # экстремум»). Дивергентный бар — это и есть новый край\n'
        '            # цены. Если город видит расхождение, а этот бар стоит\n'
        '            # ниже вершины хода (для LONG — выше дна) — вход левый.\n'
        '            try:\n'
        '                _pary_e = [x for x in ((locals().get("_d") or {})\n'
        '                           .get("пары") or []) if x.get("est")]\n'
        '            except Exception:\n'
        '                _pary_e = []\n'
        '            if _pary_e:\n'
        '                try:\n'
        '                    from feed_source import bars as _fb_e\n'
        '                    _bs_e, _pt_e = _fb_e(symbol, rabochiy_etazh, 60)\n'
        '                    _bar_e = _bs_e[-1] if _bs_e else None\n'
        '                except Exception as _e_e:\n'
        '                    _bar_e = None\n'
        '                    print(f"[ЭКСТРЕМУМ] проверить не вышло ({_e_e}) — "\n'
        '                          f"не мешаю")\n'
        '                _kr_e = _pary_e[-1].get("цена_стало")\n'
        '                if _bar_e and isinstance(_kr_e, (int, float)):\n'
        '                    _short_e = str(napravlenie).upper() == "SHORT"\n'
        '                    _moy_e = _bar_e["high"] if _short_e else _bar_e["low"]\n'
        '                    _dop_e = (_pt_e or 0.00001) * 0.5\n'
        '                    _ne_kray = ((_moy_e < _kr_e - _dop_e) if _short_e\n'
        '                                else (_moy_e > _kr_e + _dop_e))\n'
        '                    if _ne_kray:\n'
        '                        _slovo = "вершина" if _short_e else "дно"\n'
        '                        print(f"[ЭКСТРЕМУМ] ✗ {symbol} {rabochiy_etazh} "\n'
        '                              f"{napravlenie}: бар {_moy_e}, а край хода "\n'
        '                              f"{_kr_e} — вход не на экстремуме")\n'
        '                        return ("Приказ НЕ отдан: цена не на экстремуме. "\n'
        '                                f"{_slovo.capitalize()} хода — {_kr_e}, "\n'
        '                                f"а у этого бара {_slovo} {_moy_e}. "\n'
        '                                "Дивергентный бар — это и есть новый край "\n'
        '                                "цены; этот разворотник стоит не на краю, "\n'
        '                                "а после него. Жди разворотник на самом "\n'
        '                                "экстремуме или реши снова.")\n'
        '                    print(f"[ЭКСТРЕМУМ] ✓ {symbol} {rabochiy_etazh}: "\n'
        '                          f"бар {_moy_e} — край хода")\n',
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
        bak = put + ".bak_ekstremum"
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
    print("  Вход принимается только на крайнем баре — разворотник должен быть самой ценой-экстремумом.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
