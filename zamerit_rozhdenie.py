# -*- coding: utf-8 -*-
"""
zamerit_rozhdenie.py   ·   стенд, не патч (ничего не правит)

ВОПРОС
------
Из 46 точек за четыре года 29 умирают в первые двенадцать баров и НИ
ОДНА из них не даёт ноги. Все 17 ног — у точек, проживших дольше.
Значит лечить надо не смерть, а рождение: чем настоящий конец
коррекции отличается от локального разворотника В ТОТ МОМЕНТ, когда
он появился?

КАК МЕРЯЕМ
----------
Порогов не назначаем и условий не выдумываем. Стенд ходит по истории
кодом города и в момент КАЖДОГО рождения снимает всё, что уже лежит
на кадре: компас старшего фона, пасть Аллигатора, длину структуры
позади, натяжение резинки, окно объёма, ритм. Потом делит точки на
две кучи — дала ногу / не дала — и показывает каждый прибор по обеим.

Прибор годится в условие рождения, только если он эти кучи РАЗВОДИТ.
Одинаковые числа в двух колонках — прибор молчит, и никакой порог из
него не выжать.

  py -3 zamerit_rozhdenie.py             — 6000 баров (≈4 года H4)
  py -3 zamerit_rozhdenie.py 3000
  py -3 zamerit_rozhdenie.py 6000 --spisok
"""

import contextlib
import io
import sys
from pathlib import Path

OKNO = 300
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


def snyat_pribory(md: dict, napr: str) -> dict:
    """Всё, что кадр уже знает про этот бар. Ничего не считаем заново."""
    al = md.get("alligator") or {}
    wf = md.get("wave_form") or {}
    rb = md.get("rubber_band") or {}
    tw = md.get("twr") or {}
    mfi = md.get("mfi") or {}
    kompas = md.get("global_bias")
    return {
        "компас": kompas,
        "компас_за": (kompas == napr),
        "компас_против": (kompas in ("BULL", "BEAR") and kompas != napr),
        "пасть_спит": bool(al.get("sleeping")),
        "пасть_баров": al.get("bars_open"),
        "структура_позади": wf.get("dlina"),
        "натяжение": rb.get("distance_now"),
        "натяжение_макс": rb.get("distance_max"),
        "пик_натяжения": bool(rb.get("is_peak")),
        "ритм_нейтрален": bool(tw.get("neutral")),
        "окно_объёма": mfi.get("type"),
        "дивергенция": wf.get("divergence_dir"),
        "дивергенция_за": (wf.get("divergence_dir") == napr),
    }


def main():
    N = 6000
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

    bars = read_mt5_csv(str(csv))
    bars = bars[-(OKNO + N):]
    print(f"Иду по истории: {N} баров, "
          f"с {bars[OKNO].get('date')} по {bars[-1].get('date')}")
    print("Считаю (LLM не зовётся, это чистая механика)…\n")

    tochki, tek = [], None
    for i in range(OKNO, len(bars)):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            md = build_market_data(bars[i - OKNO + 1:i + 1], symbol="EURUSD",
                                   timeframe="H4", point=0.00001)
            if md:
                hooks._vesti_tochku(md, "EURUSD", "H4")
        if not md:
            continue
        for s in buf.getvalue().splitlines():
            if "[ТОЧКА] ✦" in s:
                napr = "BULL" if " BULL " in s else "BEAR"
                tek = {"с": bars[i].get("date"), "бар": i, "до": None,
                       "сторона": napr, "нога": False, "откат": False}
                tek.update(snyat_pribory(md, napr))
                tochki.append(tek)
            elif "погасла" in s and tek is not None:
                tek["до"] = i
                tek = None
            elif "[ВОЛНА 1]" in s and "кончилась" in s and tek is not None:
                tek["нога"] = True
            elif "[ОТКАТ] ↩" in s and tek is not None:
                tek["откат"] = True

    posl = len(bars) - 1
    for t in tochki:
        t["прожила"] = (t["до"] or posl) - t["бар"]
    zhivye = [t for t in tochki if t["нога"]]
    pustye = [t for t in tochki if not t["нога"]]

    print(f"точек {len(tochki)}  ({len(tochki)/(N/BAROV_V_GODU):.1f} в год)   "
          f"с ногой {len(zhivye)}   пустых {len(pustye)}\n")
    print(f"{'ПРИБОР В МОМЕНТ РОЖДЕНИЯ':<28}{'дала ногу':>14}{'пустая':>14}")
    print("─" * 56)

    def stroka(imya, znach):
        a = [znach(t) for t in zhivye if znach(t) is not None]
        b = [znach(t) for t in pustye if znach(t) is not None]
        if a and isinstance(a[0], bool):
            fa = f"{100*sum(a)/len(a):.0f}%" if a else "—"
            fb = f"{100*sum(b)/len(b):.0f}%" if b else "—"
        else:
            a = sorted(a)
            b = sorted(b)
            fa = f"{a[len(a)//2]:.0f}" if a else "—"
            fb = f"{b[len(b)//2]:.0f}" if b else "—"
        print(f"{imya:<28}{fa:>14}{fb:>14}")

    stroka("компас ЗА точку", lambda t: t["компас_за"])
    stroka("компас ПРОТИВ точки", lambda t: t["компас_против"])
    stroka("пасть спит", lambda t: t["пасть_спит"])
    stroka("пасть открыта, баров", lambda t: t["пасть_баров"])
    stroka("структура позади, баров", lambda t: t["структура_позади"])
    stroka("натяжение сейчас, пунктов", lambda t: t["натяжение"])
    stroka("натяжение макс, пунктов", lambda t: t["натяжение_макс"])
    stroka("пик натяжения", lambda t: t["пик_натяжения"])
    stroka("ритм нейтрален", lambda t: t["ритм_нейтрален"])
    stroka("дивергенция за точку", lambda t: t["дивергенция_за"])
    stroka("окно объёма GREEN", lambda t: t["окно_объёма"] == "GREEN")
    stroka("окно объёма SQUAT", lambda t: t["окно_объёма"] == "SQUAT")
    stroka("окно объёма FADE", lambda t: t["окно_объёма"] == "FADE")
    stroka("окно объёма FAKE", lambda t: t["окно_объёма"] == "FAKE")
    print("─" * 56)
    print("проценты — доля точек в своей колонке; числа — медиана")

    if spisok:
        print("\nточка                прожила нога компас пасть структура натяж.")
        for t in tochki:
            print(f"  {str(t['с']):<20}{t['прожила']:>6}  "
                  f"{'да' if t['нога'] else '—':>3}  "
                  f"{str(t['компас']):>5}  "
                  f"{'спит' if t['пасть_спит'] else 'откр':>5}  "
                  f"{str(t['структура_позади']):>7}  "
                  f"{'' if t['натяжение'] is None else round(t['натяжение'])}")

    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
