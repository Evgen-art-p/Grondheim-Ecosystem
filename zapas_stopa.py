# -*- coding: utf-8 -*-
"""
zapas_stopa.py — запас за краем разворотника: пятая часть риска.

Решение Шефа 26.09: «те пять из тринадцати». Из тринадцати её стопов
пять — «не хватило размаха»: цену протащило за стоп всего на 0–20% от
размера стопа, а потом она ушла на +2R в её сторону (06.11.2024 — 0 п.,
26.02.2025 — 32 п., 11.03.2025 — 68 п., дневка 27.02.2023 — 167 п.,
14.04.2023 — 191 п.). Остальные семь — честные ошибки направления,
их запас не спасает.

Правило: стоп, который назвала Синди (за краем разворотника), город
отодвигает ещё на пятую часть расстояния вход–стоп. Для SHORT — выше,
для LONG — ниже. R считается от этого, отодвинутого стопа.
Честно: 20% взято как раз с этих пяти стопов — настоящая проверка
будет на новых прогонах.

Что правит:
  1. Исполнитель (мозг.py) — при рождении заявки и при её перестановке
     (MOVE_ORDER). В логе: [СТОП] 🛡 … стоп X → Y — запас.
  2. Биржа/ruki_treydera.py — в описании поля «стоп» сказано, что
     город сам добавит запас, чтобы она не удивлялась другому числу.

Запуск: положить в корень репы, запустить. Копии `.bak_zapas_stopa`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "ZAPAS_STOPA_V1"
_ISP = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "контора", "слоты",
                    "исполнитель", "мозг.py")
_ROD_A = '        _sym, _tf = _rynok_treydera(key, market)\n'
_ROD_B = _ROD_A + (
    '        # ZAPAS_STOPA_V1 (решение Шефа 26.09): запас за краем\n'
    '        # разворотника — пятая часть риска. Треть её стопов была «не\n'
    '        # хватило размаха»: протащило за стоп на 0–20% и потом ушло\n'
    '        # в её сторону.\n'
    '        if (isinstance(entry, (int, float)) and isinstance(stop, (int, float))\n'
    '                and entry != stop):\n'
    '            _st_bylo = stop\n'
    '            _zap = abs(entry - stop) * 0.2\n'
    '            stop = (stop + _zap) if stop > entry else (stop - _zap)\n'
    '            stop = round(stop, 5)\n'
    '            print(f"[СТОП] 🛡 {TRADER_NAME[key]} {direction}: стоп "\n'
    '                  f"{_st_bylo} → {stop} — запас пятая часть риска")\n'
)
_MOVE_A = '            _bylo = (zv.get("entry"), zv.get("stop"))\n'
_MOVE_B = (
    '            # ZAPAS_STOPA_V1: и у переставленной заявки — запас\n'
    '            _ns_bylo = ns\n'
    '            ns = round((ns + abs(ne - ns) * 0.2) if ns > ne\n'
    '                       else (ns - abs(ne - ns) * 0.2), 5)\n'
    '            print(f"[СТОП] 🛡 {zv.get(\'trader\')} {dz}: стоп {_ns_bylo} → "\n'
    '                  f"{ns} — запас пятая часть риска")\n'
    + _MOVE_A
)
ZAMENY = {
    _ISP: [(_ROD_A, _ROD_B), (_MOVE_A, _MOVE_B)],
    os.path.join("Биржа", "ruki_treydera.py"): [(
        '"description": "цена стопа (для ENTER)"},',
        '"description": ("цена стопа (для ENTER): за краем "\n'
        '                                         "разворотника. ZAPAS_STOPA_V1: "\n'
        '                                         "город сам отодвинет его ещё на "\n'
        '                                         "пятую часть риска — запас от "\n'
        '                                         "выброса на несколько пунктов")},',
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
        bak = put + ".bak_zapas_stopa"
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
    print("  Стоп ставится с запасом — пятая часть риска за краем разворотника.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
