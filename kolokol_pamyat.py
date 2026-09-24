# -*- coding: utf-8 -*-
"""
kolokol_pamyat.py — метка колокола доходит до стола, и Синди будят.

Прогон 24.09 18:33 (январь–апрель): колокол на январском LONG звонил
четыре бара подряд, в логе четыре [КОЛОКОЛ] 🔔 — а Синди ни разу не
разбудили. Моя недоработка: расчёт позиций сохраняет стол только когда
что-то закрылось. Метку «колокол зазвонил» он ставил на позицию, но
если ничего не закрылось — метка пропадала вместе с баром. Совет её не
видел, а «звенел ли в прошлый бар» тоже терялось — отсюда звон
каждый бар.

Что делает (Биржа/hooks.py): если колокол поставил или снял метку, а
закрытий на баре не было — метку всё равно кладём в стол.

Запуск: положить в корень репы, запустить. Копия `.bak_kolokol_pamyat`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "KOLOKOL_PAMYAT_V1"
_A = '\n    if closed:\n        chain["open_positions"] = still_open\n'
ZAMENY = {
    os.path.join("Биржа", "hooks.py"): [(
        _A,
        '\n'
        '    # KOLOKOL_PAMYAT_V1: метку колокола — в стол, даже если на баре\n'
        '    # ничего не закрылось. Иначе она пропадала: Синди не будили,\n'
        '    # а «звенел ли в прошлый бар» терялось и звон шёл каждый бар.\n'
        '    if not closed and any("_колокол_звенел" in _q for _q in still_open):\n'
        '        try:\n'
        '            _tk = load_trading_state()\n'
        '            for _p in _tk.get("positions") or []:\n'
        '                for _q in still_open:\n'
        '                    if ((_p.get("magic"), _p.get("entry"),\n'
        '                         _p.get("opened_at"))\n'
        '                            == (_q.get("magic"), _q.get("entry"),\n'
        '                                _q.get("opened_at"))):\n'
        '                        for _kk in ("колокол", "_колокол_звенел"):\n'
        '                            if _kk in _q:\n'
        '                                _p[_kk] = _q[_kk]\n'
        '            save_trading_state(_tk)\n'
        '        except Exception as _e_kp:\n'
        '            print(f"[КОЛОКОЛ] метку сохранить не вышло ({_e_kp})")\n'
        + _A[1:],
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
        bak = put + ".bak_kolokol_pamyat"
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
    print("  Метка колокола теперь сохраняется — Синди будят один раз на звон.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
