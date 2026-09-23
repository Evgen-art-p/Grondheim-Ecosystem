# -*- coding: utf-8 -*-
"""
uchebnyy_rezhim.py — линии расхождения прямо на кадре, по включению.

Слово Шефа 22.09: линии на кадре — учёба, не постоянное устройство.

Что делает:
  1. Биржа/sverka_divera.py — сверка отдаёт не только числа, но и
     МЕСТА точек (первая горка, вторая горка, края цены).
  2. Биржа/grafik.py — если включён учебный режим, на кадре рисуются
     две голубые линии: по краям цены и по горкам AO. Ровно те точки,
     что сверка пишет в лог, — картинка и счёт не разойдутся.

ВКЛЮЧЕНИЕ: положить в папку Биржа/ пустой файл «учебный_режим.txt».
ВЫКЛЮЧЕНИЕ: удалить этот файл. Линии видят все — и Шеф, и трейдер.

Нужен уже накатанный dve_gorki.py.

Запуск: положить в корень репы, запустить. Сперва проверяет оба файла,
потом пишет. Копии `.bak_uchebka`. Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "UCHEBKA_V1"
NUZHNA = "DVE_GORKI_V1"
PUT_SV = os.path.join("Биржа", "sverka_divera.py")
PUT_GR = os.path.join("Биржа", "grafik.py")
SV_STAROE = '    return {"ok": True, "est": True, "slovami": slovami,\n            "цена_было": c1, "цена_стало": c2,\n            "ao_было": a1, "ao_стало": a2}\n'
SV_NOVOE = '    # UCHEBKA_V1: отдаём и МЕСТА точек — по ним кадр рисует линии.\n    _r1 = range(g, d + 1)\n    _r2 = range(d + 1, p + 1)\n    if verh:\n        ic1 = max(_r1, key=lambda k: highs[k])\n        ic2 = max(_r2, key=lambda k: highs[k])\n    else:\n        ic1 = min(_r1, key=lambda k: lows[k])\n        ic2 = min(_r2, key=lambda k: lows[k])\n    return {"ok": True, "est": True, "slovami": slovami,\n            "цена_было": c1, "цена_стало": c2,\n            "ao_было": a1, "ao_стало": a2,\n            "i_цена_1": ic1, "i_цена_2": ic2,\n            "i_ao_1": g, "i_ao_2": k2}\n'
G_STAROE = '    # SVECHA_VIDNA_V1: нулевая линия и подписи — под тёмный фон.\n    axo.axhline(0, color="#ffffff66", linewidth=1.3, zorder=2)\n'
G_NOVOE = '    # UCHEBKA_V1: учебный режим — две линии расхождения прямо на кадре.\n    # Точки берутся у сверки, те же, что ложатся в лог: первая горка,\n    # ямка-откат, вторая горка и края цены. Включается файлом\n    # Биржа/учебный_режим.txt — нет файла, линий нет.\n    if _uchebnyy_rezhim():\n        try:\n            import sverka_divera as _sd\n            _hi = [x.get("high") for x in b]\n            _lo = [x.get("low") for x in b]\n            _vid = list(range(len(ao)))\n            for _verh in (True, False):\n                _r = _sd.dve_gorki(ao, _hi, _lo, _vid, _verh, b)\n                if not _r.get("est") or _r.get("i_ao_1") is None:\n                    continue\n                ax.plot([_r["i_цена_1"], _r["i_цена_2"]],\n                        [_r["цена_было"], _r["цена_стало"]],\n                        color="#22d3ee", linewidth=2.4, zorder=8)\n                axo.plot([_r["i_ao_1"], _r["i_ao_2"]],\n                         [_r["ao_было"], _r["ao_стало"]],\n                         color="#22d3ee", linewidth=2.4, zorder=8)\n                break\n        except Exception as _e_uch:\n            print(f"[УЧЕБКА] линии не нарисовались ({_e_uch}) — не беда")\n\n    # SVECHA_VIDNA_V1: нулевая линия и подписи — под тёмный фон.\n    axo.axhline(0, color="#ffffff66", linewidth=1.3, zorder=2)\n'
G_POMOSH = '\n\n# ── UCHEBKA_V1: учебный режим кадра ───────────────────────────\n# Слово Шефа 22.09: линии расхождения на кадре — учёба, а не\n# постоянное устройство. Пусть поработает с ними пару прогонов, потом\n# выключим и посмотрим, осталось ли чтение.\n# Включение: положить рядом файл «учебный_режим.txt» (пустой). Убрать\n# файл — линии пропадают. Никаких кнопок и настроек.\ndef _uchebnyy_rezhim() -> bool:\n    try:\n        return (Path(__file__).resolve().parent / "учебный_режим.txt").exists()\n    except Exception:\n        return False\n\n\n'
G_YAKOR = 'def narisovat(bars: list, alligator: dict, ao_series: list,'


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
    otv = input("Перетащи сюда папку репы и нажми Enter:\n").strip().strip('"').strip("'")
    return godnyy(otv)


def prochest(put):
    with open(put, "rb") as f:
        t = f.read().decode("utf-8")
    return t.replace("\r\n", "\n"), "\r\n" in t


def zapisat(put, t, crlf):
    bak = put + ".bak_uchebka"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    return bak


def main():
    repo = nayti()
    if not repo:
        print("✗ Не нашёл репу (нужны Биржа/sverka_divera.py и grafik.py).")
        return
    p_sv = os.path.join(repo, PUT_SV)
    p_gr = os.path.join(repo, PUT_GR)
    t_sv, crlf_sv = prochest(p_sv)
    t_gr, crlf_gr = prochest(p_gr)
    if NUZHNA not in t_sv:
        print("✗ Сверка ещё не на две горки — сначала dve_gorki.py. Ничего не менял.")
        return
    if METKA in t_sv and METKA in t_gr:
        print("✓ Уже накатано раньше — ничего не менял.")
        return

    n_sv = t_sv
    if METKA not in t_sv:
        if t_sv.count(SV_STAROE) != 1:
            print("✗ Место в сверке не нашлось как ожидалось. Ничего не менял. Покажи Брату.")
            return
        n_sv = t_sv.replace(SV_STAROE, SV_NOVOE, 1)
    n_gr = t_gr
    if METKA not in t_gr:
        if t_gr.count(G_STAROE) != 1 or t_gr.count(G_YAKOR) != 1:
            print("✗ Место в рисовалке не нашлось как ожидалось. Ничего не менял. Покажи Брату.")
            return
        n_gr = t_gr.replace(G_STAROE, G_NOVOE, 1)
        n_gr = n_gr.replace(G_YAKOR, G_POMOSH.lstrip("\n") + G_YAKOR, 1)
    for imya, t in (("sverka_divera.py", n_sv), ("grafik.py", n_gr)):
        try:
            ast.parse(t)
        except SyntaxError as e:
            print(f"✗ {imya} после правки не собирается: {e}. Ничего не менял.")
            return
    zapisany = []
    for put, t, staroe, crlf in ((p_sv, n_sv, t_sv, crlf_sv),
                                 (p_gr, n_gr, t_gr, crlf_gr)):
        if t == staroe:
            continue
        bak = zapisat(put, t, crlf)
        zapisany.append((put, bak))
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            for p, b in zapisany:
                shutil.copy2(b, p)
            print(f"✗ Не скомпилировалось, вернул как было: {e}")
            return
    for put, bak in zapisany:
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Включить учёбу: положи в папку Биржа/ пустой файл «учебный_режим.txt».")
    print("  Выключить: удали этот файл.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
