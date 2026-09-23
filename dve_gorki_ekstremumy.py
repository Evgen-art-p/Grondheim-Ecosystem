# -*- coding: utf-8 -*-
"""
dve_gorki_ekstremumy.py — линии расхождения по ЭКСТРЕМУМАМ.

Слово Шефа 23.09: «линии должны тянуться по экстремумам, на цене и AO:
самый экстремум AO и следующий меньше, и смотрим». Образец — кадр UG96.

Что было: вторая точка AO цеплялась за мелкую ямку — на склоне, на
горке, у края — а не за настоящую вторую яму. На UK57 линия ушла на
горку над нулём, на XS44/QV26/JV94 — на рябь в начале мая.

Что делает:
  1. Биржа/sverka_divera.py — функция dve_gorki заменяется целиком:
     1-я точка AO — самый экстремум в поле зрения; откат цены делит ход
     надвое; 2-я точка AO — самый глубокий AO ПОСЛЕ отката (если яма у
     края ещё роется — у края, и переедет глубже вместе с ней); цена —
     самый низ до отката и после него. Вверх зеркально.
  2. Биржа/grafik.py — учебный блок линий: если расхождение нашлось в
     обе стороны, рисует более свежую пару.

Сверка по-прежнему ничего не запрещает, только считает и пишет в лог.

Запуск: положить в корень репы, запустить. Сам находит оба файла,
сперва проверяет всё, потом пишет. Копии `.bak_ekstremumy`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA_SV = "DVE_GORKI_EKSTREMUMY_V1"
METKA_GR = "UCHEBKA_EKSTREMUMY_V1"
PUT_SV = os.path.join("Биржа", "sverka_divera.py")
PUT_GR = os.path.join("Биржа", "grafik.py")
FUNKCIYA = 'def dve_gorki(ao: list, highs: list, lows: list, vid: list,\n              verh: bool, b: list = None) -> dict:\n    """Две горки (две ямки) по ЭКСТРЕМУМАМ. verh=True — SHORT.\n\n    DVE_GORKI_EKSTREMUMY_V1 — слово Шефа 23.09: «линии должны тянуться\n    по экстремумам, на цене и AO: самый экстремум AO и следующий\n    меньше, и смотрим». Образец — кадр UG96.\n\n    Вниз (LONG), вверх зеркально:\n      1-я точка AO — самая глубокая ямка в поле зрения;\n      откат — самый высокий бар цены после неё: он делит ход надвое;\n      2-я точка AO — самое глубокое место AO ПОСЛЕ отката (не последняя\n        ямка и не рябь на склоне); если яма у края ещё роется, точка\n        стоит у края и переедет глубже вместе с ней;\n      цена — самый низ до отката и самый низ после него.\n    Цена прежний низ не взяла — сравнивать нечего. AO после отката\n    просто ползёт, ямы нет — тоже нечего.\n    """\n    tochki = gorby(ao) if verh else yamy(ao)\n    tochki = [(i, v) for i, v in tochki if i in vid]\n    if not tochki:\n        return {"ok": True, "est": False,\n                "slovami": ("горок AO в поле зрения нет — сравнивать нечего"\n                            if verh else\n                            "ямок AO в поле зрения нет — сравнивать нечего")}\n\n    def _kogda(i):\n        try:\n            return str(b[i].get("date", ""))[:16] if b else f"бар {i}"\n        except Exception:\n            return f"бар {i}"\n\n    imya = "горка" if verh else "ямка"\n\n    # 1-я точка — самый экстремум AO в поле зрения\n    g, a1 = (max(tochki, key=lambda t: t[1]) if verh\n             else min(tochki, key=lambda t: t[1]))\n    p = None\n    for _i in range(len(ao) - 1, -1, -1):\n        if ao[_i] is not None:\n            p = _i\n            break\n    if p is None or p <= g + 1:\n        return {"ok": True, "est": False,\n                "slovami": f"главная {imya} у самого края — второй ещё нет"}\n\n    # откат по цене — он делит ход на «до» и «после»\n    posle = range(g + 1, p + 1)\n    t = (min(posle, key=lambda k: lows[k]) if verh\n         else max(posle, key=lambda k: highs[k]))\n    if t >= p:\n        return {"ok": True, "est": False,\n                "slovami": f"1-я {imya} {_kogda(g)} · цена в откате до "\n                           "самого края — второго края ещё нет"}\n    do = range(g, t + 1)\n    pos = range(t + 1, p + 1)\n\n    if verh:\n        ic1 = max(do, key=lambda k: highs[k])\n        ic2 = max(pos, key=lambda k: highs[k])\n        c1, c2 = highs[ic1], highs[ic2]\n        kray_vzyat = c2 > c1\n        k2 = max(pos, key=lambda k: ao[k])\n    else:\n        ic1 = min(do, key=lambda k: lows[k])\n        ic2 = min(pos, key=lambda k: lows[k])\n        c1, c2 = lows[ic1], lows[ic2]\n        kray_vzyat = c2 < c1\n        k2 = min(pos, key=lambda k: ao[k])\n    a2 = ao[k2]\n\n    # 2-я точка — настоящая горка (ямка) или та, что ещё растёт у края;\n    # склон, по которому AO просто ползёт, точкой не считается\n    if k2 < p:\n        est_tochka = ((a2 > ao[k2 - 1] and a2 > ao[k2 + 1]) if verh\n                      else (a2 < ao[k2 - 1] and a2 < ao[k2 + 1]))\n    else:\n        est_tochka = (a2 > ao[p - 1]) if verh else (a2 < ao[p - 1])\n    if not est_tochka:\n        return {"ok": True, "est": False,\n                "slovami": f"1-я {imya} {_kogda(g)}: AO {a1:.5f} · после "\n                           f"отката {_kogda(t)} AO просто ползёт — второй "\n                           f"{\'горки\' if verh else \'ямки\'} нет"}\n\n    sila_slabee = a2 < a1 if verh else a2 > a1\n    u_kraya = " (ещё растёт у края)" if k2 == p else ""\n    slovami = (f"1-я {imya} {_kogda(g)}: AO {a1:.5f}, край цены {c1:.5f} · "\n               f"откат {_kogda(t)} · "\n               f"2-я {imya} {_kogda(k2)}{u_kraya}: "\n               f"AO {a2:.5f}, край цены {c2:.5f}")\n    if not (kray_vzyat and sila_slabee):\n        prich = []\n        if not kray_vzyat:\n            prich.append("цена прежний край не взяла — откат ещё идёт")\n        if not sila_slabee:\n            prich.append("сила не слабее прежней")\n        return {"ok": True, "est": False,\n                "slovami": slovami + " · " + ", ".join(prich)}\n    return {"ok": True, "est": True, "slovami": slovami,\n            "цена_было": c1, "цена_стало": c2,\n            "ao_было": a1, "ao_стало": a2,\n            "i_цена_1": ic1, "i_цена_2": ic2,\n            "i_ao_1": g, "i_ao_2": k2}\n'
BLOK = '    # UCHEBKA_V1: учебный режим — две линии расхождения прямо на кадре.\n    # UCHEBKA_EKSTREMUMY_V1 (23.09): точки — у сверки, по экстремумам\n    # (1-я — самый экстремум AO, 2-я — самый глубокий после отката\n    # цены). Если расхождение нашлось в обе стороны, рисуем ту пару,\n    # что свежее — чья вторая точка цены ближе к правому краю.\n    # Включается файлом Биржа/учебный_режим.txt — нет файла, линий нет.\n    if _uchebnyy_rezhim():\n        try:\n            import sverka_divera as _sd\n            _hi = [x.get("high") for x in b]\n            _lo = [x.get("low") for x in b]\n            _vid = list(range(len(ao)))\n            _para = None\n            for _verh in (True, False):\n                _r = _sd.dve_gorki(ao, _hi, _lo, _vid, _verh, b)\n                if not _r.get("est") or _r.get("i_ao_1") is None:\n                    continue\n                if _para is None or _r["i_цена_2"] > _para["i_цена_2"]:\n                    _para = _r\n            if _para:\n                ax.plot([_para["i_цена_1"], _para["i_цена_2"]],\n                        [_para["цена_было"], _para["цена_стало"]],\n                        color="#22d3ee", linewidth=2.4, zorder=8)\n                axo.plot([_para["i_ao_1"], _para["i_ao_2"]],\n                         [_para["ao_было"], _para["ao_стало"]],\n                         color="#22d3ee", linewidth=2.4, zorder=8)\n        except Exception as _e_uch:\n            print(f"[УЧЕБКА] линии не нарисовались ({_e_uch}) — не беда")\n\n'
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
    bak = put + ".bak_ekstremumy"
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
    print("  Линии теперь по экстремумам: самый экстремум AO → самый "
          "глубокий после отката цены.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
