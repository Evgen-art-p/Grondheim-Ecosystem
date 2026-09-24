# -*- coding: utf-8 -*-
"""
shapka_po_zhurnalu.py — шапка отчёта считает сделки по журналу.

Прогон 24.09 18:33 (январь–апрель): в отчёте 7 сделок, −0.77R, а в шапке
6 сделок, +0.23R. Пропал один стоп: SHORT 11.03, у которого город сам
перевёз заявку (1.08617 → 1.0907, «новый фрактал по тренду»). Шапка
искала результат по цене входа, записанной на МЕСТЕ, — а сделка
закрылась с другой ценой входа, после переезда. То же будет с каждой
заявкой, которую Синди переставит сама (MOVE_ORDER).

Что делает (Биржа/ui_otchyot.py): шапка больше не ищет сделки через
места. Она берёт все закрытия из журнала за время этого прогона (от его
начала до начала следующего) — ровно как это делает сам отчёт.
Каждая закрытая сделка в журнале — одна строка, так что дважды не
посчитается.

Запуск: положить в корень репы, запустить. Копия `.bak_shapka_zhurnal`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "SHAPKA_PO_ZHURNALU_V1"
_STAROE = (
    '        # KRAY_I_SHAPKA_V1: каждая СДЕЛКА один раз. Цена входа стоит\n'
    '        # и на местах ведения — раньше одна сделка шла в счёт столько\n'
    '        # раз, сколько её смотрели.\n'
    '        _ry = []\n'
    '        _uzhe = set()\n'
    '        for _m in mesta:\n'
    '            _c = _m.get("цена_входа")\n'
    '            if not isinstance(_c, (int, float)):\n'
    '                continue\n'
    '            _k = round(float(_c), 5)\n'
    '            if _k in _uzhe:\n'
    '                continue\n'
    '            _r, _ = _itog_mesta(_m)\n'
    '            if _r is not None:\n'
    '                _uzhe.add(_k)\n'
    '                _ry.append(_r)\n'
)
_NOVOE = (
    '        # SHAPKA_PO_ZHURNALU_V1: сделки — прямо из журнала закрытий за\n'
    '        # время этого прогона, как в самом отчёте. Через места терялись\n'
    '        # сделки, у которых заявку перевезли (город или MOVE_ORDER):\n'
    '        # цена входа на месте и в журнале уже разная.\n'
    '        _ry = []\n'
    '        try:\n'
    '            from hooks import PNL_PATH as _pp_sh\n'
    '            from datetime import datetime as _dt_sh\n'
    '            _p_sh = Path(_pp_sh)\n'
    '            if _p_sh.exists():\n'
    '                for _ln in _p_sh.read_text(encoding="utf-8").splitlines():\n'
    '                    _ln = _ln.strip()\n'
    '                    if not _ln:\n'
    '                        continue\n'
    '                    try:\n'
    '                        _z = json.loads(_ln)\n'
    '                        _t = _dt_sh.fromisoformat(str(_z.get("ts") or "")[:19])\n'
    '                    except Exception:\n'
    '                        continue\n'
    '                    if _OKNO[0] is None or _t < _OKNO[0]:\n'
    '                        continue\n'
    '                    if _OKNO[1] is not None and _t >= _OKNO[1]:\n'
    '                        continue\n'
    '                    _rz = _z.get("pnl_r")\n'
    '                    if isinstance(_rz, (int, float)):\n'
    '                        _ry.append(float(_rz))\n'
    '        except Exception as _e_sh:\n'
    '            print(f"[ОТЧЁТ] шапка: журнал не прочитался ({_e_sh})")\n'
)
ZAMENY = {os.path.join("Биржа", "ui_otchyot.py"): [(_STAROE, _NOVOE)]}


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
        bak = put + ".bak_shapka_zhurnal"
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
    print("  Шапка отчёта считает по журналу закрытий этого прогона — как сам отчёт.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
