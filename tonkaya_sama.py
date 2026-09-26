# -*- coding: utf-8 -*-
"""
tonkaya_sama.py — дивер у края (тонкая линия) считается сам по себе.

Слово Шефа 25.09: «тонкая сама по себе». Толстая — дивер на всю
картинку: импульс, видимый на рабочем этаже (100–140 баров), третья
волна против пятой. Тонкая — дивер внутри самой пятой, у края; его
может и не видно, только глубже. Волн мы не считаем и не знаем точно,
где мы, — большой дивер может быть и за краем экрана (мы внутри ещё
большей волны). Фрактальность.

Что было не так: 23.09 я предложил правило «пара у края считается,
только если у большой пары есть расхождение» (Шеф сказал «делаем», но
мысль была моя). Оно прятало тонкую линию и закрывало вход, если у
толстой дивера нет. Ноябрь 2023 на дневке — ровно так.

Что делает:
  1. Биржа/sverka_divera.py — дивер у края больше не «не считается»;
     вердикт сверки — «есть», если расхождение есть хоть на одном
     размере.
  2. Биржа/grafik.py — учебные линии рисуются, где бы ни было
     расхождение: есть только у края — будет только тонкая.
  3. Биржа/ruki_treydera.py — проверка края отбивает вход, только если
     расхождения нет ни на одном размере; из описания четырёх чисел
     убрано «у края считается, только если…», вместо него — «тонкая
     считается сама по себе».

Запуск: положить в корень репы, запустить. Копии `.bak_tonkaya_sama`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "TONKAYA_SAMA_V1"

_SV_BLOK_A = (
    '    # BOLSHOY_KRAY_V1 (слово Шефа 23.09): пара у края считается,\n'
    '    # только если у большой пары есть расхождение. Иначе это откат\n'
    '    # внутри хода — «от 0 до 100», сравнивать нечего.\n'
    '    if kray is not None and not bolshaya["est"]:\n'
    '        slovami += (" || у края дивер есть, но не считается: большой "\n'
    '                    "край не взят — откат внутри хода")\n'
    '        kray = None\n'
)
_SV_BLOK_B = (
    '    # TONKAYA_SAMA_V1 (слово Шефа 25.09): тонкая — сама по себе.\n'
    '    # Большой дивер может быть и за краем экрана; у края он свой.\n'
)
_SV_OTV_A = (
    '    otvet = {"ok": True, "est": bolshaya["est"], "slovami": slovami,\n'
    '             "пары": pary, "край": kray}\n'
    '    if bolshaya["est"]:\n'
    '        for k in ("цена_было", "цена_стало", "ao_было", "ao_стало",\n'
    '                  "i_цена_1", "i_цена_2", "i_ao_1", "i_ao_2"):\n'
    '            otvet[k] = bolshaya[k]\n'
)
_SV_OTV_B = (
    '    # TONKAYA_SAMA_V1: дивер есть, если он есть хоть на одном размере.\n'
    '    _glavnaya = bolshaya if bolshaya["est"] else kray\n'
    '    otvet = {"ok": True, "est": _glavnaya is not None, "slovami": slovami,\n'
    '             "пары": pary, "край": kray}\n'
    '    if _glavnaya is not None:\n'
    '        for k in ("цена_было", "цена_стало", "ao_было", "ao_стало",\n'
    '                  "i_цена_1", "i_цена_2", "i_ao_1", "i_ao_2"):\n'
    '            otvet[k] = _glavnaya[k]\n'
)
_GR_A = (
    '                # BOLSHOY_KRAY_V1: нет расхождения у большой пары —\n'
    '                # это откат внутри хода, линий не рисуем вовсе.\n'
    '                _vse = _r.get("пары") or []\n'
    '                if not _vse or not _vse[0].get("est"):\n'
    '                    continue\n'
    '                _pary = [x for x in _vse if x.get("est")]\n'
)
_GR_B = (
    '                # TONKAYA_SAMA_V1: рисуем, где бы ни было расхождение —\n'
    '                # тонкая сама по себе, даже без дивера у толстой.\n'
    '                _vse = _r.get("пары") or []\n'
    '                _pary = [x for x in _vse if x.get("est")]\n'
)
_RK_A = (
    '            _bolshoy_k = _sl_k.split("||")[0]\n'
    '            if "цена прежний край не взяла" in _bolshoy_k:\n'
)
_RK_B = (
    '            _bolshoy_k = _sl_k.split("||")[0]\n'
    '            # TONKAYA_SAMA_V1: край не взят у большой пары — отбиваем,\n'
    '            # только если расхождения нет ни на одном размере.\n'
    '            try:\n'
    '                _est_k = any(_x.get("est") for _x in\n'
    '                             ((locals().get("_d") or {}).get("пары") or []))\n'
    '            except Exception:\n'
    '                _est_k = False\n'
    '            if "цена прежний край не взяла" in _bolshoy_k and not _est_k:\n'
)
_OP_A = (
    '                                           "(толстая линия). "\n'
    '                                           # BOLSHOY_KRAY_V1\n'
    '                                           "Пара у края считается, "\n'
    '                                           "только если у большой пары "\n'
    '                                           "уже есть расхождение — цена "\n'
    '                                           "взяла большой край. Пока не "\n'
    '                                           "взяла, это откат внутри хода, "\n'
    '                                           "и мелкий дивер в нём — не "\n'
    '                                           "вход")},\n'
)
_OP_B = (
    '                                           "(толстая линия). "\n'
    '                                           # TONKAYA_SAMA_V1\n'
    '                                           "Дивер у края (тонкая линия) "\n'
    '                                           "считается сам по себе: "\n'
    '                                           "большой может быть и за "\n'
    '                                           "краем экрана")},\n'
)
ZAMENY = {
    os.path.join("Биржа", "sverka_divera.py"): [(_SV_BLOK_A, _SV_BLOK_B),
                                                 (_SV_OTV_A, _SV_OTV_B)],
    os.path.join("Биржа", "grafik.py"): [(_GR_A, _GR_B)],
    os.path.join("Биржа", "ruki_treydera.py"): [(_RK_A, _RK_B), (_OP_A, _OP_B)],
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
        bak = put + ".bak_tonkaya_sama"
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
    print("  Тонкая линия — дивер у края — считается сама по себе.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
