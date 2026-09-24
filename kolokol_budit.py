# -*- coding: utf-8 -*-
"""
kolokol_budit.py — колокол больше не закрывает сделку сам, а будит.

Слово Шефа 24.09 («да»). Колокол — это старый детектор: две последние
маленькие вершины цены (бар выше соседей), цена выше, AO ниже — звон.
Ни большой горки, ни края — два соседних бугорка. Он звенит почти
всё время: на июльском LONG звонил бы каждый бар с 24 по 31 июля.
Пересчёт трёх удержанных позиций показал: оба раза, когда Синди
выходила сама, она выходила лучше кода.

Что делает:
  1. Биржа/hooks.py — колокол позицию НЕ закрывает. Когда он начинает
     звонить (было тихо — стало звонит), город помечает позицию и пишет
     [КОЛОКОЛ] 🔔 в лог. Пока звонит подряд — повторно не будит.
  2. Биржа/council.py — на этом баре Синди будят: «звонит колокол:
     медвежье (бычье) расхождение AO — ход выдыхается. Реши сама —
     держать или закрыть». Решает она — глазом и своим правилом выхода.
Стоп за Зубами при линиях в ряд остаётся страховкой, как был.

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет оба, потом пишет. Копии `.bak_kolokol_budit`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "KOLOKOL_BUDIT_V1"

_STARYY = (
    '        elif reason is None and close is not None and (\n'
    '                (direction == "LONG" and bell)\n'
    '                or (direction == "SHORT"\n'
    '                    and bool(md.get("divergence_ao")))):\n'
    '            exit_price, reason = close, "EXIT_BELL"\n'
)
_NOVYY = (
    '        # KOLOKOL_BUDIT_V1 (слово Шефа 24.09): колокол больше НЕ\n'
    '        # закрывает сам. Он звенит на двух соседних бугорках и почти\n'
    '        # всегда; когда Синди выходила сама — выходила лучше кода.\n'
    '        # Теперь колокол только БУДИТ трейдера — на баре, где начал\n'
    '        # звонить. Пока звонит подряд — повторно не будит.\n'
    '        if reason is None and close is not None:\n'
    '            _zvon = ((direction == "LONG" and bell)\n'
    '                     or (direction == "SHORT"\n'
    '                         and bool(md.get("divergence_ao"))))\n'
    '            if _zvon and not pos.get("_колокол_звенел"):\n'
    '                pos["колокол"] = bar_time\n'
    '                print(f"[КОЛОКОЛ] 🔔 {pos.get(\'trader\')} {direction}: "\n'
    '                      f"звонит — будим трейдера, решает она")\n'
    '            pos["_колокол_звенел"] = bool(_zvon)\n'
)
_SOVET = '            # просто стоит открытой — молчим, стоп ведёт код\n'

ZAMENY = {
    os.path.join("Биржа", "hooks.py"): [(_STARYY, _NOVYY)],
    os.path.join("Биржа", "council.py"): [(
        _SOVET,
        '            # KOLOKOL_BUDIT_V1: колокол начал звонить на этом баре —\n'
        '            # будим. Закрывать или держать — решает трейдер.\n'
        '            if bar_goroda and str(p.get("колокол") or "") == bar_goroda:\n'
        '                _dk = str(p.get("direction") or "LONG").upper()\n'
        '                _chto_k = ("медвежье расхождение AO — ход вверх "\n'
        '                           "выдыхается" if _dk == "LONG" else\n'
        '                           "бычье расхождение AO — ход вниз выдыхается")\n'
        '                return {"будим": True,\n'
        '                        "почему": f"звонит колокол: {_chto_k}. Реши "\n'
        '                                  f"сама — держать или закрыть"}\n'
        + _SOVET,
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
        bak = put + ".bak_kolokol_budit"
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
    print("  Колокол больше не закрывает сам — он будит трейдера, решает она.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
