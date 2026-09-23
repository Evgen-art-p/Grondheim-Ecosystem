# -*- coding: utf-8 -*-
"""
dve_gorki.py — канон Шефа 22.09: две горки и край цены.

Слово Шефа по кадру QV32: один ход — от излома до края, «от 0 до 100».
Пока цена не вышла за 100, идёт откат того же хода, новой волны нет.
Вышла — на AO стоят ДВЕ ГОРКИ, между ними ямка (тот самый откат).
Вторая горка ниже первой — расхождение. Вниз зеркально: две ямки,
горка между ними, вторая ямка мельче. Горок нет, AO просто ползёт —
сравнивать нечего: они есть этажом ниже, но туда мы не идём.

Что делает:
  1. Знания A06 (знания/AO.md): добавляет раздел «Когда сравнивать:
     две горки»; убирает два старых куска, которые ему противоречат —
     «последний горб не обязан закрыться справа» (оттуда шло сравнение
     с текущим столбиком) и «Дивер по волнам» (пересказ Брата).
  2. Сверка (Биржа/sverka_divera.py): вторая точка теперь ГОРКА у края,
     а не последний столбик; между горками обязательна ямка; цена
     должна взять прежний край. Заодно уходит строчка «дивер был там,
     здесь его нет» — она браковала верные входы после вершины.

Сверка по-прежнему ничего не запрещает, только пишет в лог.

Запуск: положить в корень репы, запустить. Сам находит оба файла,
сперва проверяет, потом пишет. Копии `.bak_dve_gorki`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA_AO = "AO_DVE_GORKI_V1"
METKA_SV = "DVE_GORKI_V1"
PUT_AO = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос",
                      "слоты", "A06", "знания", "AO.md")
PUT_SV = os.path.join("Биржа", "sverka_divera.py")
RAZDEL = '## Когда сравнивать: две горки\n\nОдин ход — от излома до его края; считай это «от 0 до 100». Пока цена\nне вышла за 100, идёт откат того же хода: новой волны нет, сравнивать\nнечего.\n\nЦена взяла прежний край — значит, на AO к этому месту стоят ДВЕ ГОРКИ,\nа между ними ямка: ямка и есть тот откат. Вторая горка ниже первой —\nрасхождение.\n\nВниз зеркально: цена взяла прежний низ — две ямки, между ними горка.\nВторая ямка мельче первой — расхождение.\n\nГорок (ямок) нет, AO просто ползёт вверх или вниз — сравнивать нечего.\nОни есть этажом ниже, но туда мы не спускаемся: на своём этаже работы\nнет.\n\nСмотри сперва всю картинку, потом край: вся картинка даёт первую горку,\nкрай — вторую.\n\n<!-- AO_DVE_GORKI_V1 -->\n\n'
STARYY_GORB = '**Последний горб не обязан закрыться справа.** Он незакончен только\nс правой стороны — там ещё не наступил столбик, который будет ниже.\nСлева подъём уже есть, и высота видна. Значит текущее значение AO —\nэто вершина растущего горба на данный момент, а не «ещё ничего».\n\nЖдать, пока горб дорисуется, нельзя: разворотный бар уже здесь, а\nпока горб закроется, момент уйдёт. Правило трёх столбиков — про\nпрошлые горбы, которым есть куда закрыться.\n\n'
PYAT = '## Дивер по волнам\n\nИсточник: Profitunity (школа Вильямса), «пять пуль» — первая пуля.\n\nТретья волна — самый высокий пик AO в поле зрения (100-140 баров).\n\nПосле неё четвёртая: AO проваливается. Может уйти за ноль — это\nне важно.\n\nПотом пятая: цена снова идёт вверх.\n\nДивер: цена в конце пятой выше цены на пике третьей волны, а AO на\nсамой высокой цене ниже пика третьей.\n\nAO смотрят на САМОЙ ВЫСОКОЙ цене. Если самая высокая цена уже позади,\nа сейчас цена ниже неё — дивер был там, а не здесь.\n\nВниз — зеркально: самая глубокая яма AO — третья; цена в пятой ниже\nцены на дне третьей, а AO на самой низкой цене мельче.\n\n<!-- AO_PYAT_PUL_V1 -->\n\n'
YAKOR = '<!-- ZNANIYA_PERVOGO_UROVNYA_A06_V1 -->'
SV_NACHALO = '    # DIVER_PYAT_PUL_V1 — по источнику'
SV_NOVOE = '    # DVE_GORKI_V1 — слово Шефа 22.09, по кадру QV32:\n    #   один импульс — это отрезок от излома до вершины, «от 0 до 100».\n    #   Пока цена не вышла за 100, идёт откат того же импульса и новой\n    #   волны нет. Вышла — пошла следующая, и вот тогда на AO стоят ДВЕ\n    #   ГОРКИ с ямкой между ними (ямка и есть тот откат). Вторая горка\n    #   ниже первой — расхождение. Вниз зеркально: две ямки, горка\n    #   между ними, вторая ямка мельче. Горок нет, AO просто ползёт —\n    #   сравнивать нечего: они есть этажом ниже, но мы туда не идём.\n    return dve_gorki(ao, highs, lows, vid, verh, b)\n\n\ndef dve_gorki(ao: list, highs: list, lows: list, vid: list,\n              verh: bool, b: list = None) -> dict:\n    """Две горки (две ямки) и край цены. verh=True — SHORT."""\n    tochki = gorby(ao) if verh else yamy(ao)\n    tochki = [(i, v) for i, v in tochki if i in vid]\n    if not tochki:\n        return {"ok": True, "est": False,\n                "slovami": ("горок AO в поле зрения нет — сравнивать нечего"\n                            if verh else\n                            "ямок AO в поле зрения нет — сравнивать нечего")}\n\n    def _kogda(i):\n        try:\n            return str(b[i].get("date", ""))[:16] if b else f"бар {i}"\n        except Exception:\n            return f"бар {i}"\n\n    # первая точка — самая большая горка (самая глубокая ямка)\n    g, a1 = (max(tochki, key=lambda t: t[1]) if verh\n             else min(tochki, key=lambda t: t[1]))\n    p = None\n    for _i in range(len(ao) - 1, -1, -1):\n        if ao[_i] is not None:\n            p = _i\n            break\n    if p is None or p <= g + 1:\n        return {"ok": True, "est": False,\n                "slovami": "главная горка у самого края — второй ещё нет"\n                if verh else "главная ямка у самого края — второй ещё нет"}\n\n    # вторая точка — горка (ямка) ПОСЛЕ первой\n    posle = [(i, v) for i, v in tochki if i > g]\n    if not posle:\n        return {"ok": True, "est": False,\n                "slovami": ("второй горки ещё нет — AO просто ползёт, "\n                            "откат не кончился" if verh else\n                            "второй ямки ещё нет — AO просто ползёт, "\n                            "откат не кончился")}\n    # вторая — ПОСЛЕДНЯЯ горка (ямка), та, что у края: именно её\n    # цена и подтверждает, взяв прежний край.\n    k2, a2 = posle[-1]\n\n    # ямка между горками — тот самый откат\n    mezhdu = [k for k in range(g + 1, k2) if ao[k] is not None]\n    if not mezhdu:\n        return {"ok": True, "est": False,\n                "slovami": "между горками нет отката" if verh\n                else "между ямками нет отката"}\n    d = (min(mezhdu, key=lambda k: ao[k]) if verh\n         else max(mezhdu, key=lambda k: ao[k]))\n\n    # край цены: до отката и после него\n    if verh:\n        c1 = max(highs[g:d + 1])\n        c2 = max(highs[d + 1:p + 1])\n        kray_vzyat = c2 > c1\n        sila_slabee = a2 < a1\n    else:\n        c1 = min(lows[g:d + 1])\n        c2 = min(lows[d + 1:p + 1])\n        kray_vzyat = c2 < c1\n        sila_slabee = a2 > a1\n\n    slovami = (f"1-я {\'горка\' if verh else \'ямка\'} {_kogda(g)}: "\n               f"AO {a1:.5f}, край цены {c1:.5f} · "\n               f"откат {_kogda(d)} · "\n               f"2-я {\'горка\' if verh else \'ямка\'} {_kogda(k2)}: "\n               f"AO {a2:.5f}, край цены {c2:.5f}")\n    if not (kray_vzyat and sila_slabee):\n        prich = []\n        if not kray_vzyat:\n            prich.append("цена прежний край не взяла — откат ещё идёт")\n        if not sila_slabee:\n            prich.append("сила не слабее прежней")\n        return {"ok": True, "est": False,\n                "slovami": slovami + " · " + ", ".join(prich)}\n    return {"ok": True, "est": True, "slovami": slovami,\n            "цена_было": c1, "цена_стало": c2,\n            "ao_было": a1, "ao_стало": a2}\n'


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if (os.path.isfile(os.path.join(papka, PUT_AO)) and
                     os.path.isfile(os.path.join(papka, PUT_SV))) else None


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
    otv = input("Перетащи сюда папку репы и нажми Enter:\n").strip().strip('"').strip("'")
    return godnyy(otv)


def prochest(put):
    with open(put, "rb") as f:
        t = f.read().decode("utf-8")
    return t.replace("\r\n", "\n"), "\r\n" in t


def zapisat(put, t, crlf):
    bak = put + ".bak_dve_gorki"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    return bak


def main():
    repo = nayti()
    if not repo:
        print("✗ Не нашёл репу (нужны знания A06/AO.md и Биржа/sverka_divera.py).")
        return
    p_ao = os.path.join(repo, PUT_AO)
    p_sv = os.path.join(repo, PUT_SV)
    t_ao, crlf_ao = prochest(p_ao)
    t_sv, crlf_sv = prochest(p_sv)
    if METKA_AO in t_ao and METKA_SV in t_sv:
        print("✓ Уже накатано раньше — ничего не менял.")
        return

    n_ao = t_ao
    if METKA_AO not in t_ao:
        if t_ao.count(YAKOR) != 1:
            print("✗ В AO.md не нашлась метка первого уровня. Ничего не менял. Покажи Брату.")
            return
        n_ao = t_ao.replace(YAKOR, RAZDEL + YAKOR, 1)
        # старые куски, спорящие с новым каноном
        n_ao = n_ao.replace(STARYY_GORB, "", 1)   # «горб не обязан закрыться»
        n_ao = n_ao.replace(PYAT, "", 1)          # «Дивер по волнам»

    n_sv = t_sv
    if METKA_SV not in t_sv:
        if SV_NACHALO not in t_sv:
            print("✗ В сверке не нашлось место «пяти пуль». Ничего не менял. Покажи Брату.")
            return
        n_sv = t_sv[:t_sv.index(SV_NACHALO)] + SV_NOVOE
        try:
            ast.parse(n_sv)
        except SyntaxError as e:
            print(f"✗ Сверка после правки не собирается: {e}. Ничего не менял.")
            return

    if n_sv != t_sv:
        bak = zapisat(p_sv, n_sv, crlf_sv)
        try:
            py_compile.compile(p_sv, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, p_sv)
            print(f"✗ Сверка не скомпилировалась, вернул как было: {e}")
            return
        print(f"✓ {p_sv}\n  копия до правки: {bak}")
    if n_ao != t_ao:
        bak = zapisat(p_ao, n_ao, crlf_ao)
        print(f"✓ {p_ao}\n  копия до правки: {bak}")
    print("  Канон: цена взяла край → две горки с ямкой между ними, вторая ниже.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
