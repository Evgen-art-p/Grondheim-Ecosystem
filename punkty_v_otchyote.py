# -*- coding: utf-8 -*-
"""
punkty_v_otchyote.py — рядом с R показываем пункты.

Слово Шефа 24.09: «R и пункты». R — мера при лоте от риска; пункты —
при лоте ступеньками. Пусть будут видны оба: четыре мелких стопа и
один большой плюс в R и в пунктах выглядят по-разному.

Пункты — разница цены в минимальных шагах: для EURUSD 0.00001
(стоп 1.05254 − 1.05085 = 169 пунктов), для JPY — 0.001, для золота —
0.01. Плюс — в пользу сделки, минус — против.

Что делает:
  1. Биржа/otchyot.py — в «Чем кончилось»: строка «итог в пунктах» и
     столбец «пункты» в таблице сделок.
  2. Биржа/ui_otchyot.py — в шапке рядом с «общий ...R»: «пункты: ...».

Запуск: положить в корень репы, запустить. Копии `.bak_punkty`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "PUNKTY_V_OTCHYOTE_V1"

_FUNKCIYA = (
    '        # PUNKTY_V_OTCHYOTE_V1: пункты — разница цены в минимальных шагах.\n'
    '        def _punkty(_z):\n'
    '            _pp = _z.get("pnl_price")\n'
    '            if not isinstance(_pp, (int, float)):\n'
    '                return None\n'
    '            _s = str(_z.get("symbol") or "").upper()\n'
    '            _pt = (0.001 if ("JPY" in _s or "XAG" in _s) else\n'
    '                   0.01 if ("XAU" in _s or "GOLD" in _s) else 0.00001)\n'
    '            return int(round(_pp / _pt))\n'
)

ZAMENY = {
    os.path.join("Биржа", "otchyot.py"): [
        ('    def _itog_sdelok(self) -> list:\n'
         '        zakr = self._zakrytiya()\n',
         '    def _itog_sdelok(self) -> list:\n'
         '        zakr = self._zakrytiya()\n' + _FUNKCIYA),
        ('            s.append(f"| итог в R | {sum(r_est):+.2f}R |")\n',
         '            s.append(f"| итог в R | {sum(r_est):+.2f}R |")\n'
         '            _pk_vse = [_punkty(x) for x in zakr]\n'
         '            _pk_vse = [v for v in _pk_vse if v is not None]\n'
         '            if _pk_vse:\n'
         '                s.append(f"| итог в пунктах | {sum(_pk_vse):+d} |")\n'),
        ('        s.append("| # | закрыта | пара | кто | вход | выход | чем | R |")\n'
         '        s.append("|---|---|---|---|---|---|---|---|")\n',
         '        s.append("| # | закрыта | пара | кто | вход | выход | чем | R | пункты |")\n'
         '        s.append("|---|---|---|---|---|---|---|---|---|")\n'),
        ('            rs = f"{float(rv):+.2f}" if isinstance(rv, (int, float)) else "—"\n',
         '            rs = f"{float(rv):+.2f}" if isinstance(rv, (int, float)) else "—"\n'
         '            _pk1 = _punkty(x)\n'
         '            ps = f"{_pk1:+d}" if _pk1 is not None else "—"\n'),
        ('                     f"{rs} |")\n',
         '                     f"{rs} | {ps} |")\n'),
    ],
    os.path.join("Биржа", "ui_otchyot.py"): [
        ('                    _rz = _z.get("pnl_r")\n'
         '                    if isinstance(_rz, (int, float)):\n'
         '                        _ry.append(float(_rz))\n',
         '                    _rz = _z.get("pnl_r")\n'
         '                    if isinstance(_rz, (int, float)):\n'
         '                        _ry.append(float(_rz))\n'
         '                    # PUNKTY_V_OTCHYOTE_V1: пункты сделки\n'
         '                    _pp = _z.get("pnl_price")\n'
         '                    if isinstance(_pp, (int, float)):\n'
         '                        _s = str(_z.get("symbol") or "").upper()\n'
         '                        _pt = (0.001 if ("JPY" in _s or "XAG" in _s) else\n'
         '                               0.01 if ("XAU" in _s or "GOLD" in _s)\n'
         '                               else 0.00001)\n'
         '                        _pk_sh.append(int(round(_pp / _pt)))\n'),
        ('        _ry = []\n'
         '        try:\n'
         '            from hooks import PNL_PATH as _pp_sh\n',
         '        _ry = []\n'
         '        _pk_sh = []   # PUNKTY_V_OTCHYOTE_V1\n'
         '        try:\n'
         '            from hooks import PNL_PATH as _pp_sh\n'),
        ('                + f\'<span style="color:{_c_sr};">средний: \'\n'
         '                  f\'<b>{_sredniy:+.2f}R</b></span>\'\n',
         '                + f\'<span style="color:{_c_sr};">средний: \'\n'
         '                  f\'<b>{_sredniy:+.2f}R</b></span>\'\n'
         '                + (f\'<span style="color:\'\n'
         '                   f\'{"#3ddc6b" if sum(_pk_sh) > 0 else "#ff5c5c"};">\'\n'
         '                   f\'пункты: <b>{sum(_pk_sh):+d}</b></span>\'\n'
         '                   if _pk_sh else \'\')\n'),
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
        bak = put + ".bak_punkty"
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
    print("  В отчёте и шапке рядом с R — пункты.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
