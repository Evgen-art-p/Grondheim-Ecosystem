# -*- coding: utf-8 -*-
"""
dve_gorki_yamka.py — вторая горка ищется ЗА ЯМКОЙ, а не на склоне первой.

Прогон 23.09 (июнь–июль 2025): на вершине 01.07 цена обновила край
(1.1745 → 1.1835), а AO стоял ниже (0.0133 → 0.0104) — дивер видно
глазом, а линий не было на девяти кадрах подряд. Причина: AO отстаёт от
цены. Сразу после маленького отката 27.06 он ещё сползал с первой горки,
и «самый высокий AO после отката» попадал на склон — город говорил
«AO просто ползёт» и молчал.

Что делает: в Биржа/sverka_divera.py функция dve_gorki заменяется
целиком. Всё прежнее остаётся (экстремумы, матрёшка, толстая и тонкая),
добавлен один шаг по канону «две горки, ямка между ними»: если вторая
точка попала на склон — найти ямку (самое глубокое место AO от отката до
нового края цены) и взять вторую горку после неё.
Кадр (grafik.py) не трогает — там уже стоит матрёшка.

Проверено на живых барах: прежние кадры (UG96, QV26 и др.) — линии те
же; на вершине 01.07 (TN44…WN95) появилась пара 26.06 → 01.07.

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет, потом пишет. Копия `.bak_yamka`. Повторный запуск ничего
не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA_SV = "DVE_GORKI_YAMKA_V1"
METKA_GR = "UCHEBKA_MATRYOSHKA_V1"
PUT_SV = os.path.join("Биржа", "sverka_divera.py")
PUT_GR = os.path.join("Биржа", "grafik.py")
FUNKCIYA = 'def dve_gorki(ao: list, highs: list, lows: list, vid: list,\n              verh: bool, b: list = None) -> dict:\n    """Две горки (две ямки) по ЭКСТРЕМУМАМ, на всех размерах. verh=True — SHORT.\n\n    DVE_GORKI_MATRYOSHKA_V1 + DVE_GORKI_YAMKA_V1 — слово Шефа 23.09: «линии должны тянуться\n    по экстремумам, на цене и AO: самый экстремум AO и следующий\n    меньше, и смотрим». И по его же скрину USDCNH: после отката пятая\n    волна несёт СВОЙ дивер внутри — смотреть на всех размерах.\n\n    Вниз (LONG), вверх зеркально. Одна пара:\n      1-я точка AO — самый экстремум;\n      откат — самый высокий бар цены после неё, он делит ход надвое;\n      2-я точка AO — самое глубокое место AO после отката (если яма у\n        края ещё роется — у края, и переедет глубже вместе с ней);\n      цена — самый низ до отката и самый низ после него.\n    Матрёшка: вторая точка пары становится первой точкой следующей,\n    меньшей — и так до края. Первая пара — весь ход, последняя — край.\n\n    Главные ключи ответа — большая пара, как и раньше. Все пары лежат в\n    «пары», последняя с расхождением — в «край».\n    """\n    tochki = gorby(ao) if verh else yamy(ao)\n    tochki = [(i, v) for i, v in tochki if i in vid]\n    imya = "горка" if verh else "ямка"\n    if not tochki:\n        return {"ok": True, "est": False,\n                "slovami": f"{\'горок\' if verh else \'ямок\'} AO в поле "\n                           "зрения нет — сравнивать нечего"}\n\n    def _kogda(i):\n        try:\n            return str(b[i].get("date", ""))[:16] if b else f"бар {i}"\n        except Exception:\n            return f"бар {i}"\n\n    p = None\n    for _i in range(len(ao) - 1, -1, -1):\n        if ao[_i] is not None:\n            p = _i\n            break\n\n    def _para(g):\n        """Одна пара от точки g до края. Строка — пары нет, и почему."""\n        a1 = ao[g]\n        if p is None or p <= g + 1:\n            return f"{imya} {_kogda(g)} у самого края — второй ещё нет"\n        posle = range(g + 1, p + 1)\n        t = (min(posle, key=lambda k: lows[k]) if verh\n             else max(posle, key=lambda k: highs[k]))\n        if t >= p:\n            return (f"после {_kogda(g)} цена в откате до самого края — "\n                    "второго края ещё нет")\n        do, pos = range(g, t + 1), range(t + 1, p + 1)\n        if verh:\n            ic1 = max(do, key=lambda k: highs[k])\n            ic2 = max(pos, key=lambda k: highs[k])\n            kray_vzyat = highs[ic2] > highs[ic1]\n            c1, c2 = highs[ic1], highs[ic2]\n            k2 = max(pos, key=lambda k: ao[k])\n        else:\n            ic1 = min(do, key=lambda k: lows[k])\n            ic2 = min(pos, key=lambda k: lows[k])\n            kray_vzyat = lows[ic2] < lows[ic1]\n            c1, c2 = lows[ic1], lows[ic2]\n            k2 = min(pos, key=lambda k: ao[k])\n        # настоящая горка (ямка) или та, что ещё растёт у края; склон,\n        # по которому AO просто ползёт, точкой не считается\n        def _tochka(k):\n            if k < p:\n                return ((ao[k] > ao[k - 1] and ao[k] > ao[k + 1]) if verh\n                        else (ao[k] < ao[k - 1] and ao[k] < ao[k + 1]))\n            return (ao[p] > ao[p - 1]) if verh else (ao[p] < ao[p - 1])\n\n        # DVE_GORKI_YAMKA_V1 — AO отстаёт от цены: сразу после отката он\n        # ещё сползает с первой горки, и «самый высокий AO после отката»\n        # оказывается на склоне. Тогда ищем ямку между горками (канон:\n        # «две горки, ямка между ними») — самое глубокое место AO от\n        # отката до нового края цены, а вторую горку — после неё.\n        if not _tochka(k2):\n            do_kraya = range(t, ic2 + 1)\n            d = (min(do_kraya, key=lambda k: ao[k]) if verh\n                 else max(do_kraya, key=lambda k: ao[k]))\n            if d < p:\n                za = range(d + 1, p + 1)\n                k2 = (max(za, key=lambda k: ao[k]) if verh\n                      else min(za, key=lambda k: ao[k]))\n        a2 = ao[k2]\n        tochka = _tochka(k2)\n        if not tochka:\n            return (f"после отката {_kogda(t)} AO просто ползёт — второй "\n                    f"{\'горки\' if verh else \'ямки\'} нет")\n        sila_slabee = a2 < a1 if verh else a2 > a1\n        u_kraya = " (ещё растёт у края)" if k2 == p else ""\n        slovami = (f"{_kogda(g)}: AO {a1:.5f}, край цены {c1:.5f} → "\n                   f"откат {_kogda(t)} → {_kogda(k2)}{u_kraya}: "\n                   f"AO {a2:.5f}, край цены {c2:.5f}")\n        prich = []\n        if not kray_vzyat:\n            prich.append("цена прежний край не взяла — откат ещё идёт")\n        if not sila_slabee:\n            prich.append("сила не слабее прежней")\n        if prich:\n            slovami += " · " + ", ".join(prich)\n        return {"est": bool(kray_vzyat and sila_slabee), "slovami": slovami,\n                "цена_было": c1, "цена_стало": c2,\n                "ao_было": a1, "ao_стало": a2,\n                "i_цена_1": ic1, "i_цена_2": ic2,\n                "i_ao_1": g, "i_ao_2": k2}\n\n    # матрёшка: от самого экстремума — к краю, каждая пара меньше\n    g, _a = (max(tochki, key=lambda t: t[1]) if verh\n             else min(tochki, key=lambda t: t[1]))\n    pary = []\n    prichina = ""\n    while True:\n        r = _para(g)\n        if isinstance(r, str):\n            prichina = r\n            break\n        pary.append(r)\n        if r["i_ao_2"] <= g or r["i_ao_2"] >= p:\n            break\n        g = r["i_ao_2"]\n\n    if not pary:\n        return {"ok": True, "est": False, "slovami": f"1-я {imya}: " + prichina,\n                "пары": [], "край": None}\n\n    bolshaya = pary[0]\n    s_diverom = [x for x in pary if x["est"]]\n    kray = s_diverom[-1] if s_diverom else None\n    slovami = "весь ход: " + bolshaya["slovami"]\n    if kray is not None and kray is not bolshaya:\n        slovami += " || у края: " + kray["slovami"]\n    if len(pary) > 1:\n        slovami += f" || размеров: {len(pary)}, с расхождением: {len(s_diverom)}"\n    otvet = {"ok": True, "est": bolshaya["est"], "slovami": slovami,\n             "пары": pary, "край": kray}\n    if bolshaya["est"]:\n        for k in ("цена_было", "цена_стало", "ao_было", "ao_стало",\n                  "i_цена_1", "i_цена_2", "i_ao_1", "i_ao_2"):\n            otvet[k] = bolshaya[k]\n    return otvet\n'
BLOK = '    # UCHEBKA_V1: учебный режим — две линии расхождения прямо на кадре.\n    # UCHEBKA_MATRYOSHKA_V1 (23.09, слово Шефа): рисуем самую большую\n    # пару (весь ход) — толстой линией, и последнюю справа (край) —\n    # тонкой. Если это одна и та же пара — одна линия. Расхождение\n    # нашлось в обе стороны — берём ту сторону, где край свежее.\n    # Включается файлом Биржа/учебный_режим.txt — нет файла, линий нет.\n    if _uchebnyy_rezhim():\n        try:\n            import sverka_divera as _sd\n            _hi = [x.get("high") for x in b]\n            _lo = [x.get("low") for x in b]\n            _vid = list(range(len(ao)))\n            _luchshe, _svezhest = None, -1\n            for _verh in (True, False):\n                _r = _sd.dve_gorki(ao, _hi, _lo, _vid, _verh, b)\n                _pary = [x for x in (_r.get("пары") or []) if x.get("est")]\n                if not _pary:\n                    continue\n                if _pary[-1]["i_цена_2"] > _svezhest:\n                    _luchshe, _svezhest = _pary, _pary[-1]["i_цена_2"]\n            if _luchshe:\n                _risovat = [(_luchshe[0], 2.4)]\n                if _luchshe[-1] is not _luchshe[0]:\n                    _risovat.append((_luchshe[-1], 1.3))\n                for _p, _tol in _risovat:\n                    ax.plot([_p["i_цена_1"], _p["i_цена_2"]],\n                            [_p["цена_было"], _p["цена_стало"]],\n                            color="#22d3ee", linewidth=_tol, zorder=8)\n                    axo.plot([_p["i_ao_1"], _p["i_ao_2"]],\n                             [_p["ao_было"], _p["ao_стало"]],\n                             color="#22d3ee", linewidth=_tol, zorder=8)\n        except Exception as _e_uch:\n            print(f"[УЧЕБКА] линии не нарисовались ({_e_uch}) — не беда")\n\n'
NACHALO_BLOKA = "    # UCHEBKA_V1: учебный режим — две линии"
KONEC_BLOKA = "    # SVECHA_VIDNA_V1: нулевая линия"


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if (os.path.isfile(os.path.join(papka, PUT_SV)) and
                     os.path.isfile(os.path.join(papka, PUT_GR))) else None


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


def prochest(put):
    with open(put, "rb") as f:
        syroe = f.read()
    crlf = b"\r\n" in syroe
    return syroe.decode("utf-8").replace("\r\n", "\n"), crlf


def zapisat(put, tekst, crlf):
    bak = put + ".bak_yamka"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    data = tekst.replace("\n", "\r\n") if crlf else tekst
    with open(put, "wb") as f:
        f.write(data.encode("utf-8"))
    return bak


def novaya_sverka(tekst):
    """Заменить dve_gorki целиком — чем бы она сейчас ни была."""
    if METKA_SV in tekst:
        return tekst, "уже стоит"
    derevo = ast.parse(tekst)
    uzly = [u for u in derevo.body
            if isinstance(u, ast.FunctionDef) and u.name == "dve_gorki"]
    if len(uzly) != 1:
        raise RuntimeError("в сверке не нашлась функция dve_gorki — "
                           "пришли Брату файл Биржа/sverka_divera.py")
    u = uzly[0]
    stroki = tekst.split("\n")
    nov = (stroki[:u.lineno - 1] + FUNKCIYA.rstrip("\n").split("\n")
           + stroki[u.end_lineno:])
    novyy = "\n".join(nov)
    ast.parse(novyy)
    return novyy, "заменю"


def novyy_grafik(tekst):
    """Заменить учебный блок линий — от его начала до нулевой линии AO."""
    if METKA_GR in tekst:
        return tekst, "уже стоит"
    if tekst.count(NACHALO_BLOKA) != 1:
        raise RuntimeError("в grafik.py не нашёлся учебный блок линий — "
                           "пришли Брату файл Биржа/grafik.py")
    i = tekst.index(NACHALO_BLOKA)
    j = tekst.find(KONEC_BLOKA, i)
    if j < 0:
        raise RuntimeError("в grafik.py не нашёлся конец учебного блока — "
                           "пришли Брату файл Биржа/grafik.py")
    novyy = tekst[:i] + BLOK + tekst[j:]
    ast.parse(novyy)
    return novyy, "заменю"


def main():
    repa = nayti()
    if not repa:
        print("✗ Репу не нашёл. Ничего не менял.")
        return
    p_sv = os.path.join(repa, PUT_SV)
    p_gr = os.path.join(repa, PUT_GR)
    t_sv, crlf_sv = prochest(p_sv)
    t_gr, crlf_gr = prochest(p_gr)

    # сперва проверяем ОБА файла, пишем только если оба в порядке
    try:
        n_sv, s_sv = novaya_sverka(t_sv)
        n_gr, s_gr = novyy_grafik(t_gr)
    except Exception as e:
        print(f"✗ {e}\n  Ничего не менял.")
        return
    print(f"Сверка: {s_sv} · кадр: {s_gr}")
    if n_sv == t_sv and n_gr == t_gr:
        print("✓ Всё уже стоит. Ничего не менял.")
        return

    for put, novyy, staryy, crlf in ((p_sv, n_sv, t_sv, crlf_sv),
                                     (p_gr, n_gr, t_gr, crlf_gr)):
        if novyy == staryy:
            continue
        bak = zapisat(put, novyy, crlf)
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Вторая горка теперь ищется за ямкой, а не на склоне первой.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
