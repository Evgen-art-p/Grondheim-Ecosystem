# -*- coding: utf-8 -*-
"""
bolshoy_kray.py — мелкий дивер внутри отката не считается, пока цена не
взяла большой край.

Решение Шефа 23.09 («делаем»). Прогон июля 2025 на Луне: спуск 08–16.07
был откатом внутри большого хода вверх — июньское дно 1.14516 цена не
брала. У края мелкий дивер был, Синди брала его четыре раза: +0.25, −1,
−1, −1. Откат шёл дальше вниз. Канон «от 0 до 100»: пока цена внутри
отката, сравнивать нечего.

Правило: пара у края считается, только если у большой пары уже есть
расхождение — цена взяла большой край. Нет — это откат внутри хода.

Что делает — три правки, все вместе или никакой:
  1. Биржа/ruki_treydera.py — в описание четырёх чисел (его Синди видит
     при каждом приказе) дописано это правило её словами.
  2. Биржа/grafik.py — учебные линии рисуются, только если есть
     расхождение у большой пары. Внутри отката линий нет, чтобы не звать
     глаз туда, где входа нет.
  3. Биржа/sverka_divera.py — в лог: «у края дивер есть, но не
     считается: большой край не взят».
Сверка по-прежнему ничего не запрещает — решает Синди.

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет все три, потом пишет. Копии `.bak_bolshoy_kray`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "BOLSHOY_KRAY_V1"
FAYLY = {
    os.path.join("Биржа", "ruki_treydera.py"): [(
        '                                           "(толстая линия)")},\n',
        '                                           "(толстая линия). "\n'
        '                                           # BOLSHOY_KRAY_V1\n'
        '                                           "Пара у края считается, "\n'
        '                                           "только если у большой пары "\n'
        '                                           "уже есть расхождение — цена "\n'
        '                                           "взяла большой край. Пока не "\n'
        '                                           "взяла, это откат внутри хода, "\n'
        '                                           "и мелкий дивер в нём — не "\n'
        '                                           "вход")},\n',
    )],
    os.path.join("Биржа", "grafik.py"): [(
        '                _pary = [x for x in (_r.get("пары") or []) if x.get("est")]\n',
        '                # BOLSHOY_KRAY_V1: нет расхождения у большой пары —\n'
        '                # это откат внутри хода, линий не рисуем вовсе.\n'
        '                _vse = _r.get("пары") or []\n'
        '                if not _vse or not _vse[0].get("est"):\n'
        '                    continue\n'
        '                _pary = [x for x in _vse if x.get("est")]\n',
    )],
    os.path.join("Биржа", "sverka_divera.py"): [(
        '    kray = s_diverom[-1] if s_diverom else None\n'
        '    slovami = "весь ход: " + bolshaya["slovami"]\n'
        '    if kray is not None and kray is not bolshaya:\n'
        '        slovami += " || у края: " + kray["slovami"]\n',
        '    kray = s_diverom[-1] if s_diverom else None\n'
        '    slovami = "весь ход: " + bolshaya["slovami"]\n'
        '    # BOLSHOY_KRAY_V1 (слово Шефа 23.09): пара у края считается,\n'
        '    # только если у большой пары есть расхождение. Иначе это откат\n'
        '    # внутри хода — «от 0 до 100», сравнивать нечего.\n'
        '    if kray is not None and not bolshaya["est"]:\n'
        '        slovami += (" || у края дивер есть, но не считается: большой "\n'
        '                    "край не взят — откат внутри хода")\n'
        '        kray = None\n'
        '    if kray is not None and kray is not bolshaya:\n'
        '        slovami += " || у края: " + kray["slovami"]\n',
    )],
}


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if all(os.path.isfile(os.path.join(papka, p))
                        for p in FAYLY) else None


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
    gotovo = []   # (путь, новый текст, crlf)
    for otn, zameny in FAYLY.items():
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
        ast.parse(novyy)
        gotovo.append((put, novyy, crlf))
    if not gotovo:
        print("✓ Всё уже стоит. Ничего не менял.")
        return
    for put, novyy, crlf in gotovo:
        bak = put + ".bak_bolshoy_kray"
        if not os.path.exists(bak):
            shutil.copy2(put, bak)
        with open(put, "wb") as f:
            f.write((novyy.replace("\n", "\r\n") if crlf else novyy)
                    .encode("utf-8"))
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Мелкий дивер внутри отката не считается, пока цена не взяла "
          "большой край.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
