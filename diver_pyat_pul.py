# -*- coding: utf-8 -*-
"""
diver_pyat_pul.py — сверка дивера по источнику (Profitunity, «пять пуль»).

Третья волна — самый высокий пик AO в поле зрения; четвёртая — AO
проваливается (может уйти за ноль); дивер — цена в конце пятой выше
цены на пике третьей, а AO на самой высокой цене ниже пика третьей.
Если самая высокая цена уже позади — сверка пишет «дивер был там-то,
здесь его нет». Вниз — зеркально.

Сверка ничего не запрещает — только пишет в лог.

Запуск: положить в корень репы, запустить. Сам находит Биржа/.
Копия: sverka_divera.py.bak_pyat_pul. Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "DIVER_PYAT_PUL_V1"
YAKOR = "    # главный — самый большой (или самая глубокая) в поле зрения\n"
KONEC = '            "ao_было": ao_bylo, "ao_стало": ao_stalo}\n'
NOVYY = '    # DIVER_PYAT_PUL_V1 — по источнику (Profitunity, «пять пуль»):\n    #   третья волна — самый высокий пик AO в поле зрения (100-140\n    #   баров); четвёртая — AO проваливается, может уйти за ноль;\n    #   дивер — цена в конце импульса выше цены на пике третьей, а AO\n    #   на САМОЙ ВЫСОКОЙ цене ниже пика третьей. Вниз — зеркально.\n    return pyat_pul(ao, highs, lows, vid, verh, b)\n\n\ndef pyat_pul(ao: list, highs: list, lows: list, vid: list,\n             verh: bool, b: list = None) -> dict:\n    """Дивер по источнику. verh=True — SHORT (пики и вершины),\n    False — LONG (ямы и впадины)."""\n    tochki = gorby(ao) if verh else yamy(ao)\n    tochki = [(i, v) for i, v in tochki if i in vid]\n    if len(tochki) < 1:\n        return {"ok": False, "est": None,\n                "slovami": "пиков AO в поле зрения не нашлось" if verh\n                else "ям AO в поле зрения не нашлось"}\n\n    def _kogda(i):\n        try:\n            return str(b[i].get("date", ""))[:16] if b else f"бар {i}"\n        except Exception:\n            return f"бар {i}"\n\n    # третья волна — самый высокий пик (самая глубокая яма)\n    g = (max(tochki, key=lambda t: t[1]) if verh\n         else min(tochki, key=lambda t: t[1]))[0]\n    p = None\n    for _i in range(len(ao) - 1, -1, -1):\n        if ao[_i] is not None:\n            p = _i\n            break\n    if p is None or p <= g + 1:\n        return {"ok": True, "est": False,\n                "slovami": "третья волна у самого края — пятой ещё нет"}\n\n    # самая высокая цена после третьей (самая низкая — вниз)\n    ryad = range(g, p + 1)\n    if verh:\n        kh = max(ryad, key=lambda k: highs[k])\n        c3, c5 = highs[g], highs[kh]\n        cena_vyshe = c5 > c3\n        ao_nizhe = ao[kh] is not None and ao[kh] < ao[g]\n    else:\n        kh = min(ryad, key=lambda k: lows[k])\n        c3, c5 = lows[g], lows[kh]\n        cena_vyshe = c5 < c3\n        ao_nizhe = ao[kh] is not None and ao[kh] > ao[g]\n\n    slovami = (f"3-я волна {_kogda(g)}: цена {c3:.5f}, AO {ao[g]:.5f} · "\n               f"{\'самая высокая\' if verh else \'самая низкая\'} цена "\n               f"{_kogda(kh)}: {c5:.5f}, AO {ao[kh]:.5f}")\n\n    # четвёртая — между третьей и крайней ценой AO провалился и\n    # пошёл обратно (ноль не важен)\n    mezhdu = [k for k in range(g + 1, kh) if ao[k] is not None]\n    if not mezhdu:\n        return {"ok": True, "est": False,\n                "slovami": slovami + " · четвёртой волны нет — пятой не было"}\n    d = (min(mezhdu, key=lambda k: ao[k]) if verh\n         else max(mezhdu, key=lambda k: ao[k]))\n    if (verh and ao[kh] <= ao[d]) or (not verh and ao[kh] >= ao[d]):\n        return {"ok": True, "est": False,\n                "slovami": slovami + " · AO после провала не пошёл обратно — "\n                                     "пятой не было"}\n    est_byl = bool(cena_vyshe and ao_nizhe)\n    if not est_byl:\n        prich = []\n        if not cena_vyshe:\n            prich.append("цена не ушла дальше третьей")\n        if not ao_nizhe:\n            prich.append("AO не слабее третьей")\n        return {"ok": True, "est": False,\n                "slovami": slovami + " · " + ", ".join(prich)}\n    if kh != p:\n        return {"ok": True, "est": False,\n                "slovami": slovami + f" · дивер был {_kogda(kh)}, а сейчас "\n                           f"цена {\'ниже\' if verh else \'выше\'} той — "\n                           "здесь его нет"}\n    return {"ok": True, "est": True, "slovami": slovami,\n            "цена_было": c3, "цена_стало": c5,\n            "ao_было": ao[g], "ao_стало": ao[kh]}\n'
PUT = os.path.join("Биржа", "sverka_divera.py")

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
    otv = input("Перетащи сюда папку репы и нажми Enter:\n")
    return godnyy(otv.strip().strip('"').strip("'"))


def zapisat(put, t, crlf, bak_imya):
    bak = put + bak_imya
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    vyvod = t.replace("\n", "\r\n") if crlf else t
    with open(put, "wb") as f:
        f.write(vyvod.encode("utf-8"))
    return bak


def main():
    put = nayti()
    if not put:
        print("✗ Биржа/sverka_divera.py не найден. Ничего не менял.")
        return
    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")
    if METKA in t:
        print("✓ Уже накатано раньше — ничего не менял.")
        return
    if t.count(YAKOR) != 1 or t.count(KONEC) != 1:
        print("✗ Место в сверке не нашлось как ожидалось. Ничего не менял. Покажи Брату.")
        return
    i = t.index(YAKOR)
    j = t.index(KONEC) + len(KONEC)
    t = t[:i] + NOVYY + t[j:]
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return
    bak = zapisat(put, t, crlf, ".bak_pyat_pul")
    try:
        py_compile.compile(put, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, put)
        print(f"✗ Не скомпилировался, вернул как было: {e}")
        return
    print(f"✓ Готово: {put}")
    print(f"  копия до правки: {bak}")
    print("  Сверка дивера — по «пяти пулям»: 3-я волна, 4-я, самая высокая цена.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
