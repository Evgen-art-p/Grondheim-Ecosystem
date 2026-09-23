# -*- coding: utf-8 -*-
"""
chetyre_chisla.py — на входе трейдер называет ЧЕТЫРЕ ЧИСЛА, по которым
увидел расхождение.

Слово Шефа 22.09: в разговоре Синди назвала точки и наклоны верно —
«линия по впадинам цены вниз, линия по ямам AO вверх». А в работе
говорит общими словами: «AO слабее прежнего горба». Пусть показывает,
по каким местам увидела.

Что стало (Биржа/ruki_treydera.py):
  · у руки otdat_prikaz четыре новых поля — цена_1, ao_1, цена_2, ao_2;
  · ENTER без них не принимается, ровно как без цены и стопа;
  · в лог рядом ложатся [ТОЧКИ] её и [ТОЧКИ] города — видно, по тем же
    местам смотрели или по разным.

Ничего нового не запрещается: сверка по-прежнему не блокирует вход,
решает трейдер. Требуется только показать свои точки.

Запуск: положить в корень репы, запустить. Сам находит файл.
Копия: ruki_treydera.py.bak_chetyre_chisla. Повторный запуск ничего
не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "CHETYRE_CHISLA_V1"
PUT = os.path.join("Биржа", "ruki_treydera.py")
PRAVKI = [('                "стоп": {"type": "number",\n                         "description": "цена стопа (для ENTER)"},\n', '                "стоп": {"type": "number",\n                         "description": "цена стопа (для ENTER)"},\n                # CHETYRE_CHISLA_V1: по каким точкам увидела расхождение.\n                # Слова «AO слабее прежнего горба» ничего не значат, пока\n                # не названы места. Четыре числа — две цены и два AO с\n                # ТЕХ ЖЕ мест: первая точка и вторая.\n                "цена_1": {"type": "number",\n                           "description": ("для ENTER: цена в ПЕРВОЙ точке "\n                                           "расхождения — вершина (вниз: "\n                                           "впадина), рядом с которой стоит "\n                                           "самый сильный горб (яма) AO")},\n                "ao_1": {"type": "number",\n                         "description": ("для ENTER: AO в этой же ПЕРВОЙ "\n                                         "точке — тот самый горб (яма)")},\n                "цена_2": {"type": "number",\n                           "description": ("для ENTER: цена во ВТОРОЙ точке "\n                                           "— новая вершина (впадина), "\n                                           "дальше по ходу")},\n                "ao_2": {"type": "number",\n                         "description": ("для ENTER: AO в этой же ВТОРОЙ "\n                                         "точке — горб (яма) под ней")},\n'), ('            if not isinstance(stop, (int, float)):\n                net.append("стоп")\n', '            if not isinstance(stop, (int, float)):\n                net.append("стоп")\n            # CHETYRE_CHISLA_V1: где увидела расхождение — числами.\n            _tochki = {}\n            for _pole in ("цена_1", "ao_1", "цена_2", "ao_2"):\n                _zn = args.get(_pole)\n                if isinstance(_zn, (int, float)):\n                    _tochki[_pole] = float(_zn)\n                else:\n                    net.append(_pole)\n'), ('            except Exception as _e_sd:\n                print(f"[ДИВЕР] посчитать не вышло ({_e_sd}) — не беда")\n', '                # CHETYRE_CHISLA_V1: её точки рядом с городскими —\n                # видно, по тем же местам смотрели или по разным.\n                try:\n                    _nak_c = ("выше" if _tochki["цена_2"] > _tochki["цена_1"]\n                              else "ниже")\n                    _nak_a = ("выше" if _tochki["ao_2"] > _tochki["ao_1"]\n                              else "ниже")\n                    print(f"[ТОЧКИ] её: цена {_tochki[\'цена_1\']}→"\n                          f"{_tochki[\'цена_2\']} ({_nak_c}), AO "\n                          f"{_tochki[\'ao_1\']}→{_tochki[\'ao_2\']} ({_nak_a})")\n                    if _d.get("ok") and _d.get("цена_было") is not None:\n                        print(f"[ТОЧКИ] города: цена {_d.get(\'цена_было\')}→"\n                              f"{_d.get(\'цена_стало\')}, AO "\n                              f"{_d.get(\'ao_было\')}→{_d.get(\'ao_стало\')}")\n                except Exception:\n                    pass\n            except Exception as _e_sd:\n                print(f"[ДИВЕР] посчитать не вышло ({_e_sd}) — не беда")\n'), ('                "ENTER без направления, цены и стопа не принимается: "\n', '                "ENTER без направления, цены, стопа и четырёх чисел "\n                "расхождения (цена_1, ao_1, цена_2, ao_2) не "\n                "принимается: "\n')]


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    p = os.path.join(papka, PUT)
    return p if os.path.isfile(p) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        p = godnyy(papka)
        if p:
            return p
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = godnyy(os.path.join(koren, imya))
                if p and p not in kandidaty:
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
    otv = input("Перетащи сюда папку репы и нажми Enter:\n").strip().strip('"').strip("'")
    return godnyy(otv)


def main():
    put = nayti()
    if not put:
        print("✗ Биржа/ruki_treydera.py не найден. Ничего не менял.")
        return
    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")
    if METKA in t:
        print("✓ Уже накатано раньше — ничего не менял.")
        return
    for n, (s, _) in enumerate(PRAVKI, 1):
        if t.count(s) != 1:
            print(f"✗ Правка {n}: место не нашлось как ожидалось "
                  f"(совпадений: {t.count(s)}). Ничего не менял. Покажи Брату.")
            return
    for s, n in PRAVKI:
        t = t.replace(s, n, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return
    bak = put + ".bak_chetyre_chisla"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    try:
        py_compile.compile(put, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, put)
        print(f"✗ Не скомпилировался, вернул как было: {e}")
        return
    print(f"✓ Готово: {put}")
    print(f"  копия до правки: {bak}")
    print("  На входе она теперь называет четыре числа; в логе [ТОЧКИ] её и города.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
