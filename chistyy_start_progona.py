# -*- coding: utf-8 -*-
"""
chistyy_start_progona.py — новый прогон не тащит события старого.

Прогон 24.09 13:57: Синди разбудили «сделка закрылась: STOP_LOSS @
1.18078», хотя в этом прогоне она не входила вовсе. Это закрытие —
из ПРОШЛОГО прогона (12:53, тот самый SHORT 01.07). Город помнит на
столе «последнее закрытие» с баром 01.07 08:00; новый прогон дошёл до
того же бара — и город решил, что сделка закрылась сейчас.

Что делает (Биржа/ui_torg.py, старт прогона по истории): перед первым
баром стирает со стола «последнее закрытие» и позиции/заявки, которые
остались от прошлого, остановленного прогона. В лог — что стёрто.
Журналы сделок и отчёты не трогает.

Запуск: положить в корень репы, запустить. Сам находит файл, сперва
проверяет, потом пишет. Копия `.bak_chistyy_start`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "CHISTYY_START_PROGONA_V1"
_A = (
    '        state["tester_running"] = True\n'
    '        state["stop_requested"] = False\n'
    '        state["stop_hard"] = False          # STOP_ZHYOSTKO_V1\n'
    '        _pometit_stop_dlya_mozga(False)\n'
    '        _bylo_moment = ""\n'
)
ZAMENY = {
    os.path.join("Биржа", "ui_torg.py"): [(
        _A,
        _A +
        '        # CHISTYY_START_PROGONA_V1: новый прогон — чистый стол.\n'
        '        # «Последнее закрытие» и позиции прошлого прогона будили\n'
        '        # трейдера чужими событиями на тех же барах.\n'
        '        try:\n'
        '            from hooks import load_trading_state as _lts0\n'
        '            from hooks import save_trading_state as _sts0\n'
        '            _t0 = _lts0()\n'
        '            _bylo_z = _t0.pop("последнее_закрытие", None)\n'
        '            # живые (mode=live) не трогаем — только прошлые прогоны\n'
        '            _vse0 = _t0.get("positions") or []\n'
        '            _zhivye0 = [p for p in _vse0\n'
        '                        if str(p.get("mode") or "").lower() == "live"]\n'
        '            _bylo_p = len(_vse0) - len(_zhivye0)\n'
        '            if _bylo_p:\n'
        '                _t0["positions"] = _zhivye0\n'
        '            if _bylo_z is not None or _bylo_p:\n'
        '                _sts0(_t0)\n'
        '                print(f"[ПРОГОН] 🧹 чистый стол: прошлое закрытие "\n'
        '                      f"{\'стёрто\' if _bylo_z is not None else \'не было\'}"\n'
        '                      f", позиций/заявок прошлого прогона снято: {_bylo_p}")\n'
        '        except Exception as _e_ch:\n'
        '            print(f"[ПРОГОН] почистить стол не вышло ({_e_ch})")\n',
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
        bak = put + ".bak_chistyy_start"
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
    print("  Новый прогон начинается с чистого стола: чужое закрытие больше не будит.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
