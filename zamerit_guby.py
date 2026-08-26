# -*- coding: utf-8 -*-
"""
zamerit_guby.py   ·   стенд, не патч (ничего не правит)

ВОПРОС
------
Слово Шефа (25.08): настоящая точка ноль рождается там, где цена
СХОДИЛА к синей линии (губам) и там развернулась. Не «коснулась
за N баров» — а ушла далеко и вернулась.

Прошлый замер этого условия был сломан: он ОТСЕИВАЛ точки, а их
становилось больше (15 → 38). Причина понятна: пока рождение было
свободным, отсев одной точки открывал дорогу трём другим. С патчем
`ODNA_TOCHKA_ZA_RAZ_V1` эта петля закрыта, и мерить можно честно.

КАК МЕРЯЕМ
----------
Порога НЕ выдумываем. Стенд ходит по истории тем же кодом города,
и про КАЖДУЮ родившуюся точку записывает три числа:

    ушла   — самое дальнее удаление цены от губ за окно перед
             рождением (в пунктах, безразмерно)
    у губ  — расстояние от бара рождения до губ (в пунктах)
    нога   — дала ли эта точка волну 1

Потом раскладывает точки по тому, коснулся ли бар рождения губ, и
показывает, у кого чаще выходила нога. Число порога, если оно есть,
должно вылезти из таблицы само — а не быть подобрано заранее.

  py -3 zamerit_guby.py               — 6000 баров (≈4 года H4)
  py -3 zamerit_guby.py 3000
  py -3 zamerit_guby.py 6000 --spisok — плюс каждая точка строкой
"""

import contextlib
import io
import sys
from pathlib import Path

OKNO = 300          # кадр рынка, как в rynok_novyy_bar
NAZAD = 20          # сколько баров назад смотрим «ушла далеко»
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
    POINT = 0.00001
    print(f"Иду по истории: {N} баров, "
          f"с {bars[OKNO].get('date')} по {bars[-1].get('date')}")
    print("Считаю (LLM не зовётся, это чистая механика)…\n")

    guby = {}          # индекс бара → значение губ на нём
    tochki, tek = [], None

    for i in range(OKNO, len(bars)):
        okno = bars[i - OKNO + 1:i + 1]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            md = build_market_data(okno, symbol="EURUSD", timeframe="H4",
                                   point=POINT)
            if md:
                hooks._vesti_tochku(md, "EURUSD", "H4")
        if not md:
            continue
        lips = (md.get("alligator") or {}).get("lips")
        guby[i] = lips

        for s in buf.getvalue().splitlines():
            if "[ТОЧКА] ✦" in s:
                b = bars[i]
                # ушла: самое дальнее удаление СЕРЕДИНЫ бара от губ
                # за NAZAD баров до рождения, в пунктах
                ushla = 0.0
                for j in range(max(OKNO, i - NAZAD), i):
                    lj = guby.get(j)
                    if lj is None:
                        continue
                    sredina = (bars[j]["high"] + bars[j]["low"]) / 2
                    ushla = max(ushla, abs(sredina - lj) / POINT)
                # у губ: насколько бар рождения от них далеко (0 —
                # губы внутри бара, он их накрыл)
                if lips is None:
                    u_gub, kosnulsya = None, None
                elif b["low"] <= lips <= b["high"]:
                    u_gub, kosnulsya = 0.0, True
                else:
                    u_gub = (min(abs(b["low"] - lips),
                                 abs(b["high"] - lips)) / POINT)
                    kosnulsya = False
                tek = {"с": b.get("date"), "бар": i, "ушла": ushla,
                       "у_губ": u_gub, "коснулся": kosnulsya,
                       "нога": False, "откат": False}
                tochki.append(tek)
            elif "[ТОЧКА] ✕" in s:
                tek = None
            elif "[ВОЛНА 1]" in s and "кончилась" in s and tek is not None:
                tek["нога"] = True
            elif "[ОТКАТ] ↩" in s and tek is not None:
                tek["откат"] = True

    god = N / BAROV_V_GODU
    znayem = [t for t in tochki if t["коснулся"] is not None]
    kos = [t for t in znayem if t["коснулся"]]
    ne_kos = [t for t in znayem if not t["коснулся"]]

    def dolya(gruppa, klyuch="нога"):
        if not gruppa:
            return "—"
        n = sum(1 for t in gruppa if t[klyuch])
        return f"{n}/{len(gruppa)} ({100*n/len(gruppa):.0f}%)"

    print(f"""точек всего          {len(tochki):4}   ({len(tochki)/god:.1f} в год)
дали ногу            {dolya(tochki)}
дошли до отката      {dolya(tochki, 'откат')}

РАЗБИВКА ПО ГУБАМ (коснулся ли бар рождения синей линии)
  бар накрыл губы    точек {len(kos):3}   нога {dolya(kos)}   откат {dolya(kos,'откат')}
  губ не достал      точек {len(ne_kos):3}   нога {dolya(ne_kos)}   откат {dolya(ne_kos,'откат')}
""")

    # ЧЕТВЕРТИ: делим точки по числу и смотрим, где чаще выходит нога.
    # Порог не назначаем — если он есть, он вылезет сам.
    def chetverti(klyuch: str, imya: str):
        est = sorted((t for t in tochki if t.get(klyuch) is not None),
                     key=lambda t: t[klyuch])
        if len(est) < 8:
            return
        k = max(1, len(est) // 4)
        print(f"\n{imya} — по четвертям (от меньшего к большему):")
        for n in range(4):
            gr = est[n * k:(n + 1) * k] if n < 3 else est[3 * k:]
            if not gr:
                continue
            nog = sum(1 for t in gr if t["нога"])
            print(f"  {gr[0][klyuch]:>6.0f} … {gr[-1][klyuch]:>6.0f} пунктов "
                  f"· точек {len(gr):>3} · нога {nog}/{len(gr)} "
                  f"({100*nog/len(gr):.0f}%)")

    chetverti("у_губ", "РАССТОЯНИЕ ДО ГУБ на баре рождения")
    chetverti("ушла", f"КАК ДАЛЕКО УХОДИЛА от губ за {NAZAD} баров до")

    # распределение «у губ» у тех, кто не достал: где стоит граница?
    dalekie = sorted((t["у_губ"] for t in ne_kos if t["у_губ"] is not None))
    if dalekie:
        def kv(p):
            return dalekie[min(len(dalekie) - 1, int(len(dalekie) * p))]
        print(f"кто не достал — сколько пунктов до губ: "
              f"четверть ≤{kv(0.25):.0f}, половина ≤{kv(0.5):.0f}, "
              f"три четверти ≤{kv(0.75):.0f}, дальше всех {dalekie[-1]:.0f}")

    ushedshie = sorted((t["ушла"] for t in tochki if t["ушла"]))
    if ushedshie:
        def kv2(p):
            return ushedshie[min(len(ushedshie) - 1, int(len(ushedshie) * p))]
        print(f"как далеко цена уходила от губ за {NAZAD} баров до точки: "
              f"четверть ≤{kv2(0.25):.0f}, половина ≤{kv2(0.5):.0f}, "
              f"три четверти ≤{kv2(0.75):.0f}")

    if spisok:
        print("\nточка                  ушла   у губ  нога  откат")
        for t in tochki:
            u = "—" if t["у_губ"] is None else f"{t['у_губ']:.0f}"
            print(f"  {str(t['с']):<20} {t['ушла']:>6.0f} {u:>7} "
                  f"{'да' if t['нога'] else '—':>5} "
                  f"{'да' if t['откат'] else '—':>6}")

    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
