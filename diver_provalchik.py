# -*- coding: utf-8 -*-
"""
diver_provalchik.py — сверка дивера по канону Шефа (22.09).

Слово Шефа: «между горбами должен быть провальчик, а между ямами —
подъёмчик»; «цена всё выше и выше — обновлять максимум».

Что было: Биржа/sverka_divera.py брала цену в баре главного горба и
сравнивала с сегодняшней. Проверки «обновила ли цена вершину хода»
и «был ли провальчик между горбами» не было. 30.05.2025 00:00: цена
1.13842 ниже вершины хода 1.14181, а сверка писала «дивер ✓».

Что стало: главный горб → провальчик после него → второй горб
(справа может быть незакончен). Цена на втором горбе должна
обновить вершину хода. Ноль, расстояние, номер волны — не считаются.
Для LONG то же зеркально: ямы, подъёмчик, впадины.

Сверка по-прежнему ничего не запрещает — только пишет в лог.

Запуск: положить в корень репы, запустить. Сам находит Биржа/.
Копия: sverka_divera.py.bak_provalchik. Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "DIVER_PROVALCHIK_V1"
IMYA = "sverka_divera.py"
YAKOR = "    # главный — самый большой (или самая глубокая) в поле зрения\n"
KONEC = '            "ao_было": ao_bylo, "ao_стало": ao_stalo}\n'

NOVYY_HVOST = '    # DIVER_PROVALCHIK_V1 — канон Шефа 22.09:\n    #   «между горбами должен быть провальчик, а между ямами —\n    #   подъёмчик»; «цена всё выше и выше — обновлять максимум».\n    # Главный горб — самый большой в поле зрения. После него AO\n    # обязан провалиться (провальчик) и снова пойти вверх — это\n    # второй горб (справа он может быть незакончен). Цена на\n    # втором горбе должна ОБНОВИТЬ вершину, что была от главного\n    # горба до провальчика. Не обновила — ход не продолжился,\n    # дивера нет. Ноль, расстояние, номер волны — не считаются.\n    return dve_tochki(ao, highs, lows, vid, verh)\n\n\ndef dve_tochki(ao: list, highs: list, lows: list, vid: list,\n               verh: bool) -> dict:\n    """Две точки дивера по канону. verh=True — SHORT (горбы и\n    вершины), False — LONG (ямы и впадины)."""\n    tochki = gorby(ao) if verh else yamy(ao)\n    tochki = [(i, v) for i, v in tochki if i in vid]\n    if len(tochki) < 1:\n        return {"ok": False, "est": None,\n                "slovami": "горбов в поле зрения не нашлось" if verh\n                else "ям в поле зрения не нашлось"}\n\n    # главный — самый большой горб (самая глубокая яма) в поле зрения\n    glavnyy = max(tochki, key=lambda t: t[1]) if verh \\\n        else min(tochki, key=lambda t: t[1])\n    g = glavnyy[0]\n\n    p = None\n    for _i in range(len(ao) - 1, -1, -1):\n        if ao[_i] is not None:\n            p = _i\n            break\n    if p is None or p <= g + 1:\n        return {"ok": True, "est": False,\n                "slovami": "главный горб у самого края — второго ещё нет"\n                if verh else "главная яма у самого края — второй ещё нет"}\n\n    # провальчик (для ям — подъёмчик): крайняя точка AO между\n    # главным и сегодняшним днём\n    mezhdu = [(k, ao[k]) for k in range(g + 1, p) if ao[k] is not None]\n    if not mezhdu:\n        return {"ok": True, "est": False,\n                "slovami": "между главным и краем пусто"}\n    d = (min(mezhdu, key=lambda t: t[1]) if verh\n         else max(mezhdu, key=lambda t: t[1]))[0]\n    # провальчик должен кончиться: после него AO пошёл обратно\n    posle = [ao[k] for k in range(d + 1, p + 1) if ao[k] is not None]\n    if not posle or (verh and max(posle) <= ao[d]) or \\\n            (not verh and min(posle) >= ao[d]):\n        return {"ok": True, "est": False,\n                "slovami": ("AO ещё уходит вниз от главного горба — "\n                            "провальчика нет, второго горба нет") if verh\n                else ("AO ещё поднимается от главной ямы — "\n                      "подъёмчика нет, второй ямы нет")}\n\n    # второй горб — от провальчика до края (справа может быть незакончен)\n    nog = [k for k in range(d + 1, p + 1) if ao[k] is not None]\n    if verh:\n        k2 = max(nog, key=lambda k: ao[k])\n        ao_bylo, ao_stalo = glavnyy[1], ao[k2]\n        c_bylo = max(highs[g:d + 1])          # вершина хода до провальчика\n        c_stalo = max(highs[d + 1:p + 1])     # вершина на втором горбе\n        cena_dalshe = c_stalo > c_bylo\n        sila_slabee = ao_stalo < ao_bylo\n    else:\n        k2 = min(nog, key=lambda k: ao[k])\n        ao_bylo, ao_stalo = glavnyy[1], ao[k2]\n        c_bylo = min(lows[g:d + 1])\n        c_stalo = min(lows[d + 1:p + 1])\n        cena_dalshe = c_stalo < c_bylo\n        sila_slabee = ao_stalo > ao_bylo\n\n    est = bool(cena_dalshe and sila_slabee)\n    kuda_c = "выше" if c_stalo > c_bylo else "ниже"\n    kuda_a = "выше" if ao_stalo > ao_bylo else "ниже"\n    slovami = (f"цена {c_bylo:.5f}→{c_stalo:.5f} ({kuda_c}), "\n               f"AO {ao_bylo:.5f}→{ao_stalo:.5f} ({kuda_a}), "\n               f"{\'провальчик\' if verh else \'подъёмчик\'} {ao[d]:.5f}")\n    if not est:\n        if not cena_dalshe:\n            slovami += (" · цена вершину хода не обновила" if verh\n                        else " · цена впадину хода не обновила")\n        if not sila_slabee:\n            slovami += " · сила не ослабла"\n    return {"ok": True, "est": est, "slovami": slovami,\n            "цена_было": c_bylo, "цена_стало": c_stalo,\n            "ao_было": ao_bylo, "ao_стало": ao_stalo}\n'


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    p = os.path.join(papka, "Биржа", IMYA)
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
    otv = input("Перетащи сюда папку репы (где лежит папка Биржа) и нажми Enter:\n")
    return godnyy(otv.strip().strip('"').strip("'"))


def main():
    put = nayti()
    if not put:
        print(f"✗ Биржа/{IMYA} не найден. Ничего не менял.")
        return
    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")

    if METKA in t:
        print("✓ Уже накатано раньше — ничего не менял.")
        return
    if t.count(YAKOR) != 1 or t.count(KONEC) != 1 or t.index(KONEC) < t.index(YAKOR):
        print("✗ Место в сверке не нашлось как ожидалось. Ничего не менял. Покажи Брату.")
        return

    i = t.index(YAKOR)
    j = t.index(KONEC) + len(KONEC)
    t = t[:i] + NOVYY_HVOST + t[j:]
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return

    bak = put + ".bak_provalchik"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    vyvod = t.replace("\n", "\r\n") if crlf else t
    with open(put, "wb") as f:
        f.write(vyvod.encode("utf-8"))
    try:
        py_compile.compile(put, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, put)
        print(f"✗ Не скомпилировался, вернул как было: {e}")
        return
    print(f"✓ Готово: {put}")
    print(f"  копия до правки: {bak}")
    print("  Сверка дивера: провальчик между горбами + цена обновляет вершину хода.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
