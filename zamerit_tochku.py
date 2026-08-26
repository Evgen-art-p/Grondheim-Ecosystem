# -*- coding: utf-8 -*-
"""
zamerit_tochku.py   ·   стенд, не патч (ничего не правит)

ЗАЧЕМ
-----
Мерить точку ноль ТЕМ ЖЕ кодом, которым живёт город, а не отдельной
лабораторной копией логики. Стенд гоняет `_vesti_tochku` из
`Биржа/hooks.py` бар за баром по CSV: окно 300 баров, кадр собирает
`williams_core`, состояние живёт между барами — ровно как в прогоне
подряд. Трейдеров, LLM и денег здесь нет: считается только механика.

Считает судьбу КАЖДОЙ точки: сколько прожила, дала ли волну 1, дошла
ли до отката. Пустая точка (без ноги) — главная цифра: это структура,
которая родилась и ничего не дала.

ПРАВИЛО ЗАМЕРА (урок 25.08)
---------------------------
Одно изменение за раз. Меняешь два условия сразу — числа сложатся
так, что не разберёшь, чьи они. И проверять, что условие СУЖАЕТ:
если после «отсева» точек стало БОЛЬШЕ — сломан замер, а не рынок.

  py -3 zamerit_tochku.py                — 3000 баров (≈2 года H4)
  py -3 zamerit_tochku.py 6000           — четыре года
  py -3 zamerit_tochku.py 3000 --spisok  — плюс список точек построчно
"""

import contextlib
import io
import sys
from pathlib import Path


def nayti_koren() -> Path:
    for k in (Path(__file__).resolve().parent, Path.cwd()):
        for p in [k, *k.parents]:
            if (p / "GRONDHEIM_CITY").is_dir() and (p / "Биржа").is_dir():
                return p
    print("Не нашёл корень репозитория (нужны папки GRONDHEIM_CITY и Биржа).")
    zhdat_i_vyyti(1)


def zhdat_i_vyyti(kod=0):
    try:
        input("\nEnter — закрыть окно...")
    except EOFError:
        pass
    sys.exit(kod)


OKNO = 300          # столько баров берёт рынок на кадр (rynok_novyy_bar)
BAROV_V_GODU = 1500  # H4


def main():
    N = 3000
    for a in sys.argv[1:]:
        if a.isdigit():
            N = int(a)
    spisok = "--spisok" in sys.argv

    koren = nayti_koren()
    csv = koren / "XAUUSDH4.csv"
    if not csv.exists():
        print(f"Нет файла истории: {csv}")
        zhdat_i_vyyti(1)

    sys.path.insert(0, str(koren / "Биржа"))
    import hooks
    from williams_core import read_mt5_csv, build_market_data

    # стол чистый: замер не должен начинаться с чужой живой точки
    st = hooks._put_stola()
    if st.exists():
        st.unlink()

    bars = read_mt5_csv(str(csv))
    bars = bars[-(OKNO + N):]
    print(f"Иду по истории: {N} баров, "
          f"с {bars[OKNO].get('date')} по {bars[-1].get('date')}")
    print("Считаю (LLM не зовётся, это чистая механика)…\n")

    tochki, tek = [], None
    zablokirovano = kray = 0

    for i in range(OKNO, len(bars)):
        okno = bars[i - OKNO + 1:i + 1]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            md = build_market_data(okno, symbol="EURUSD", timeframe="H4",
                                   point=0.00001)
            if md:
                hooks._vesti_tochku(md, "EURUSD", "H4")
        for s in buf.getvalue().splitlines():
            if "[ТОЧКА] ✦" in s:
                tek = {"с": bars[i].get("date"), "бар": i, "до": None,
                       "волна1": False, "откат": False}
                tochki.append(tek)
            elif "[ТОЧКА] ✕" in s and tek is not None:
                tek["до"] = i
                tek = None
            elif "новой не делает" in s:
                zablokirovano += 1
            elif "[ВОЛНА 1]" in s and "кончилась" in s and tek is not None:
                tek["волна1"] = True
            elif "сдвинул" in s:
                kray += 1
            elif "[ОТКАТ] ↩" in s and tek is not None:
                tek["откат"] = True

    god = N / BAROV_V_GODU
    posledniy = len(bars) - 1
    zhizni = sorted((t["до"] or posledniy) - t["бар"] for t in tochki)
    volna = [t for t in tochki if t["волна1"]]
    otkat = [t for t in tochki if t["откат"]]
    pusto = [t for t in tochki if not t["волна1"]]

    print(f"""точек                {len(tochki):4}   ({len(tochki)/god:.1f} в год)
из них дали волну 1  {len(volna):4}   ({len(volna)/god:.1f} в год)
дошли до отката      {len(otkat):4}   ({len(otkat)/god:.1f} в год)
пустых (без ноги)    {len(pusto):4}   ({100*len(pusto)/max(1, len(tochki)):.0f}%)
переездов края       {kray:4}
не пущено внутрь     {zablokirovano:4}   (0 — если патч «одна точка за раз» не стоит)
жизнь точки          медиана {zhizni[len(zhizni)//2] if zhizni else 0} бар.""")

    if spisok:
        print("\nточка                 прожила  волна 1  откат")
        for t in tochki:
            print(f"  {str(t['с']):<20} {((t['до'] or posledniy) - t['бар']):>5}  "
                  f"{'да' if t['волна1'] else '—':>7}  "
                  f"{'да' if t['откат'] else '—':>5}")

    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
