# -*- coding: utf-8 -*-
"""
zamerit_starshiy.py   ·   стенд, не патч (ничего не правит)

ВОПРОС (со слов Шефа, 26.08)
----------------------------
Точка ноль — не бар, а МЕСТО: конец коррекции СТАРШЕГО порядка.
Разворотный бар одинаков и на окончании волн 1/3/5, и на окончании 2
или 4 — сам он не знает, какой конец поймал. Знает этаж выше.

Проверяем дословно: разворотник на рабочем H4 — точка ноль только
если на СТАРШЕМ (дневном) этаже коррекция закончилась.

КАК МЕРЯЕМ
----------
Дневки склеиваются из тех же H4-баров. Берутся ТОЛЬКО ЗАКРЫТЫЕ дни —
день, внутри которого стоит рабочий бар, не виден (иначе замер
подглядывает в будущее и врёт в свою пользу).

В момент каждого рождения снимаем со старшего этажа: его собственный
разворотник и сколько дней назад он был, знак его AO и был ли переход
через ноль, его компас, читается ли у него структура. Потом делим
точки на «дала ногу» и «пустая» и смотрим, разводит ли старший этаж
эти кучи.

Порог не назначаем. Внизу — лесенка: сколько точек и сколько ног
останется, если требовать старший разворотник за последние N дней.
Если определение верное, доля ног должна расти резко, а не на проценты.

  py -3 zamerit_starshiy.py            — 3000 баров (≈2 года H4)
  py -3 zamerit_starshiy.py 1500
  py -3 zamerit_starshiy.py 3000 --spisok
"""

import contextlib
import io
import sys
from pathlib import Path

OKNO = 300          # кадр рабочего этажа, как в rynok_novyy_bar
OKNO_D1 = 300       # кадр старшего этажа
NAZAD_DNEY = 20     # как далеко назад ищем старший разворотник
BAROV_V_GODU = 1500


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


def sklеit_dnevki(bars: list) -> tuple:
    """H4 → D1. Возвращает (дневки, день→номер дневки)."""
    dnevki, nomer = [], {}
    for b in bars:
        den = str(b.get("date", "")).split(" ")[0]
        if not dnevki or dnevki[-1]["_den"] != den:
            nomer[den] = len(dnevki)
            dnevki.append({"_den": den, "date": den, "open": b["open"],
                           "high": b["high"], "low": b["low"],
                           "close": b["close"],
                           "volume": b.get("volume", 0),
                           "spread": b.get("spread", 0)})
        else:
            d = dnevki[-1]
            d["high"] = max(d["high"], b["high"])
            d["low"] = min(d["low"], b["low"])
            d["close"] = b["close"]
            d["volume"] = d.get("volume", 0) + b.get("volume", 0)
    return dnevki, nomer


def main():
    N = 3000
    for a in sys.argv[1:]:
        if a.isdigit():
            N = int(a)
    spisok = "--spisok" in sys.argv

    koren = nayti_koren()
    csv = koren / "EURUSDH4.csv"
    if not csv.exists():
        print(f"Нет файла истории: {csv}")
        zhdat_i_vyyti(1)

    sys.path.insert(0, str(koren / "Биржа"))
    import hooks
    from williams_core import read_mt5_csv, build_market_data

    st = hooks._put_stola()
    if st.exists():
        st.unlink()

    POINT = 0.00001
    vse = read_mt5_csv(str(csv))
    dnevki, nomer_dnya = sklеit_dnevki(vse)
    start = max(OKNO, len(vse) - N)
    print(f"Иду по истории: {len(vse)-start} баров, "
          f"с {vse[start].get('date')} по {vse[-1].get('date')}")
    print(f"Старший этаж: дневки, склеены из тех же баров "
          f"({len(dnevki)} дней всего). Текущий день не показывается.")
    print("Считаю (LLM не зовётся, это чистая механика)…\n")

    kesh_d1 = {}

    def starshiy(den: str):
        """Кадр старшего этажа на ЗАКРЫТЫХ днях до этого дня."""
        if den in kesh_d1:
            return kesh_d1[den]
        i = nomer_dnya.get(den)
        md = None
        if i is not None and i >= 40:
            okno = dnevki[max(0, i - OKNO_D1):i]     # текущий день НЕ входит
            md = build_market_data(okno, symbol="EURUSD", timeframe="D1",
                                   point=POINT, starshiy=True) or None
        kesh_d1[den] = (md, i)
        return kesh_d1[den]

    def starshiy_razvorotnik(i_dnya: int, storona: str):
        """Сколько дней назад старший этаж дал разворотник той стороны."""
        for nazad in range(1, NAZAD_DNEY + 1):
            j = i_dnya - nazad
            if j < 41:
                break
            okno = dnevki[max(0, j - OKNO_D1):j + 1]
            md = build_market_data(okno, symbol="EURUSD", timeframe="D1",
                                   point=POINT, starshiy=True)
            if md and (md.get("wave_form") or {}).get("bdb_dir") == storona:
                return nazad
        return None

    tochki, tek = [], None
    for i in range(start, len(vse)):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            md = build_market_data(vse[i - OKNO + 1:i + 1], symbol="EURUSD",
                                   timeframe="H4", point=POINT)
            if md:
                hooks._vesti_tochku(md, "EURUSD", "H4")
        if not md:
            continue
        stroki = buf.getvalue().splitlines()
        for s in stroki:
            if "[ТОЧКА] ✦" in s:
                napr = "BULL" if " BULL " in s else "BEAR"
                den = str(vse[i].get("date", "")).split(" ")[0]
                md_st, i_dnya = starshiy(den)
                swf = (md_st or {}).get("wave_form") or {}
                sao = (md_st or {}).get("ao") or {}
                tek = {
                    "с": vse[i].get("date"), "бар": i, "до": None,
                    "сторона": napr, "нога": False, "откат": False,
                    "ст_компас_за": ((md_st or {}).get("global_bias") == napr),
                    "ст_разворотник_сейчас": (swf.get("bdb_dir") == napr),
                    "ст_структура": bool(swf.get("struktura_chitaetsya")),
                    "ст_AO_за": (
                        None if sao.get("value") is None else
                        ((sao["value"] > 0) if napr == "BULL"
                         else (sao["value"] < 0))),
                    "ст_AO_развернулся": (
                        None if sao.get("value") is None
                        or sao.get("prev_value") is None else
                        ((sao["value"] > sao["prev_value"]) if napr == "BULL"
                         else (sao["value"] < sao["prev_value"]))),
                    "ст_дней_назад": (starshiy_razvorotnik(i_dnya, napr)
                                      if i_dnya is not None else None),
                }
                tochki.append(tek)
            elif "погасла" in s and tek is not None:
                tek["до"] = i
                tek = None
            elif "[ВОЛНА 1]" in s and "кончилась" in s and tek is not None:
                tek["нога"] = True
            elif "[ОТКАТ] ↩" in s and tek is not None:
                tek["откат"] = True

    posl = len(vse) - 1
    for t in tochki:
        t["прожила"] = (t["до"] or posl) - t["бар"]
    zh = [t for t in tochki if t["нога"]]
    pu = [t for t in tochki if not t["нога"]]
    god = (len(vse) - start) / BAROV_V_GODU

    print(f"точек {len(tochki)}  ({len(tochki)/god:.1f} в год)   "
          f"с ногой {len(zh)}   пустых {len(pu)}\n")
    print(f"{'СТАРШИЙ ЭТАЖ В МОМЕНТ РОЖДЕНИЯ':<34}{'нога':>10}{'пустая':>10}")
    print("─" * 54)

    def stroka(imya, klyuch):
        a = [t[klyuch] for t in zh if t[klyuch] is not None]
        b = [t[klyuch] for t in pu if t[klyuch] is not None]
        fa = f"{100*sum(a)/len(a):.0f}%" if a else "—"
        fb = f"{100*sum(b)/len(b):.0f}%" if b else "—"
        print(f"{imya:<34}{fa:>10}{fb:>10}")

    stroka("его компас ЗА точку", "ст_компас_за")
    stroka("его разворотник той же стороны", "ст_разворотник_сейчас")
    stroka("его структура читается", "ст_структура")
    stroka("его AO на стороне точки", "ст_AO_за")
    stroka("его AO развернулся к точке", "ст_AO_развернулся")
    print("─" * 54)

    print(f"\nЛЕСЕНКА: если требовать старший разворотник за последние N дней\n"
          f"{'N дней':>8}{'точек':>10}{'из них ног':>13}{'доля':>8}")
    for n in (1, 2, 3, 5, 8, 12, 20):
        gr = [t for t in tochki
              if t["ст_дней_назад"] is not None and t["ст_дней_назад"] <= n]
        nog = sum(1 for t in gr if t["нога"])
        dolya = f"{100*nog/len(gr):.0f}%" if gr else "—"
        print(f"{n:>8}{len(gr):>10}{nog:>13}{dolya:>8}")
    print(f"{'без него':>8}{len(tochki):>10}{len(zh):>13}"
          f"{100*len(zh)/max(1,len(tochki)):>7.0f}%")

    if spisok:
        print("\nточка                прожила нога  ст.разв  ст.AO  ст.компас")
        for t in tochki:
            print(f"  {str(t['с']):<20}{t['прожила']:>6}  "
                  f"{'да' if t['нога'] else '—':>3}  "
                  f"{str(t['ст_дней_назад']):>7}  "
                  f"{'за' if t['ст_AO_за'] else 'против':>6}  "
                  f"{'за' if t['ст_компас_за'] else 'против':>8}")

    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
