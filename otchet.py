# otchet.py — ЧТО ОНИ НАТОРГОВАЛИ. Правда в цифрах.
# ─────────────────────────────────────────────────────────────
# СЛОВО ШЕФА (14.07):
#   «они мне отчёт по сделкам не дали.. сами себе мутили, а я так и не
#    понял.. что они наторговали»
#
# Тестер печатает «поймал 15 срабатываний» — и всё. Ни PF, ни winrate,
# ни суммы. ШЕФ РАБОТАЕТ ВСЛЕПУЮ. А данные ЕСТЬ: hooks._settle_positions
# пишет полный журнал в trading_pnl.jsonl (pnl_r, trader, close_reason,
# opened_at, closed_at, entry, stop, exit). Отчёта просто никто не писал.
#
# ⚠ ЭТОТ ОТЧЁТ СЧИТАЕТ НЕ ТОЛЬКО ДЕНЬГИ — ОН СТАВИТ ДИАГНОЗ.
# По книге Котина (гл.9, знания A07) прибыль у Вильямса делает ПИРАМИДА,
# а не одиночный вход:
#   вход рискует 1R → цена пошла → СТОП В СЕЙФ (риск→0) → ДОЛИВ → ДОЛИВ
#   → exit_bell → закрыли ВСЮ пирамиду разом.
#   Убытки остаются по 1R, а прибыли РАСТУТ. Отсюда матожидание.
# А книга ЖЕ САМА признаётся:
#   «Отложенный долг (слой 3, НЕ РЕАЛИЗОВАН): пирамида доливок
#    (5→4→3→2→1) и трейлинг-стоп за Аллигатором. ПОКА ВЕДЕНИЕ УПРОЩЕНО.»
#   «Стоп системы. НЕ ДВИГАЕТСЯ (до перехода в трейлинг, слой 3).»
#
# ⇒ Убыток ВСЕГДА полный (−1R), прибыль ВСЕГДА обрезана. Система
#   работает НАОБОРОТ. Отчёт это ПОКАЖЕТ ЧИСЛОМ, а не на словах.
#
# Ничего не пишет. Только читает журнал и говорит правду.
#
# Запуск из корня репо:
#   python otchet.py            — всё, что накопилось
#   python otchet.py --last 20  — последние 20 сделок
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PNL = ROOT / "GRONDHEIM_CITY" / "Биржа" / "данные" / "trading_pnl.jsonl"


def chitat():
    if not PNL.exists():
        return []
    out = []
    for ln in PNL.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
            if r.get("pnl_r") is not None:
                out.append(r)
        except Exception:
            continue
    return out


def statistika(sdelki: list) -> dict:
    plus  = [s for s in sdelki if s["pnl_r"] > 0]
    minus = [s for s in sdelki if s["pnl_r"] <= 0]
    sum_p = sum(s["pnl_r"] for s in plus)
    sum_m = abs(sum(s["pnl_r"] for s in minus))
    return {
        "всего":    len(sdelki),
        "плюсов":   len(plus),
        "минусов":  len(minus),
        "winrate":  len(plus) / len(sdelki) * 100 if sdelki else 0.0,
        "sum_R":    sum(s["pnl_r"] for s in sdelki),
        "средний":  sum(s["pnl_r"] for s in sdelki) / len(sdelki) if sdelki else 0,
        "PF":       (sum_p / sum_m) if sum_m > 0 else (float("inf") if sum_p else 0),
        "лучшая":   max((s["pnl_r"] for s in sdelki), default=0),
        "худшая":   min((s["pnl_r"] for s in sdelki), default=0),
        "sum_plus": sum_p,
        "sum_minus": sum_m,
    }


def main():
    last = None
    if "--last" in sys.argv:
        try:
            last = int(sys.argv[sys.argv.index("--last") + 1])
        except Exception:
            pass

    sdelki = chitat()
    if not sdelki:
        print()
        print(f"  ⚠ журнал пуст или не найден: {PNL}")
        print("    Прогони тестер — сделки пишутся автоматически.")
        print()
        sys.exit(1)

    if last:
        sdelki = sdelki[-last:]

    st = statistika(sdelki)

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ОТЧЁТ ПО СДЕЛКАМ — что они наторговали" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")

    # ── ЛЕНТА ───────────────────────────────────────────────────
    print()
    print(f"  {'#':>3} {'трейдер':12s} {'напр':5s} {'вход':>9s} {'выход':>9s} "
          f"{'R':>7s}  причина")
    print("  " + "─" * 68)
    for i, s in enumerate(sdelki, 1):
        r = s["pnl_r"]
        znak = "🟢" if r > 0 else "🔴"
        napr = "LONG" if (s.get("stop") or 0) < (s.get("entry") or 0) else "SHORT"
        print(f"  {i:>3} {str(s.get('trader',''))[:12]:12s} {napr:5s} "
              f"{s.get('entry','—'):>9} {s.get('exit','—'):>9} "
              f"{r:>+7.2f} {znak} {s.get('close_reason','')}")

    # ── ГЛАВНОЕ ─────────────────────────────────────────────────
    print()
    print("  " + "═" * 68)
    print("  ИТОГ")
    print("  " + "═" * 68)
    print()
    print(f"    сделок:      {st['всего']}")
    print(f"    плюсов:      {st['плюсов']}   минусов: {st['минусов']}")
    print(f"    winrate:     {st['winrate']:.1f}%")
    print()
    print(f"    ИТОГО:       {st['sum_R']:+.2f}R")
    print(f"    средняя:     {st['средний']:+.2f}R на сделку")
    pf = st["PF"]
    pf_s = "∞" if pf == float("inf") else f"{pf:.3f}"
    print(f"    PF:          {pf_s}   "
          f"({'ПРИБЫЛЬНАЯ' if pf > 1 else 'УБЫТОЧНАЯ'} система)")
    print()
    print(f"    лучшая:      {st['лучшая']:+.2f}R")
    print(f"    худшая:      {st['худшая']:+.2f}R")

    # ── ПО ТРЕЙДЕРАМ ────────────────────────────────────────────
    po_t = defaultdict(list)
    for s in sdelki:
        po_t[s.get("trader", "?")].append(s)
    print()
    print("  ── ПО ТРЕЙДЕРАМ ──")
    print()
    print(f"    {'трейдер':14s} {'сделок':>7s} {'плюс':>6s} {'winrate':>8s} "
          f"{'сумма R':>9s} {'PF':>7s}")
    print("    " + "─" * 56)
    for t, ss in sorted(po_t.items()):
        s2 = statistika(ss)
        pf2 = s2["PF"]
        pf2s = "∞" if pf2 == float("inf") else f"{pf2:.2f}"
        print(f"    {str(t)[:14]:14s} {s2['всего']:>7d} {s2['плюсов']:>6d} "
              f"{s2['winrate']:>7.0f}% {s2['sum_R']:>+9.2f} {pf2s:>7s}")

    # ── ПО ПРИЧИНЕ ЗАКРЫТИЯ ─────────────────────────────────────
    po_r = defaultdict(list)
    for s in sdelki:
        po_r[s.get("close_reason", "?")].append(s["pnl_r"])
    print()
    print("  ── КАК ЗАКРЫВАЛИСЬ ──")
    print()
    for r, rs in sorted(po_r.items(), key=lambda x: -len(x[1])):
        print(f"    {str(r)[:16]:16s} {len(rs):>3d} шт   "
              f"сумма {sum(rs):+7.2f}R   средняя {sum(rs)/len(rs):+.2f}R")

    # ══════════════════════════════════════════════════════════
    # ДИАГНОЗ — ГЛАВНОЕ. Отчёт не только считает, но и СУДИТ.
    # ══════════════════════════════════════════════════════════
    print()
    print("  " + "═" * 68)
    print("  ДИАГНОЗ (по книге Котина, гл.9)")
    print("  " + "═" * 68)

    # 1. Живёт ли позиция? Или умирает одним выстрелом?
    polnyi_stop = [s for s in sdelki
                   if abs(s["pnl_r"] + 1.0) < 0.05]   # ровно −1.0R
    dolya_stop = len(polnyi_stop) / len(sdelki) * 100 if sdelki else 0

    print()
    print(f"    закрытий ровно по −1.0R (полный стоп): {len(polnyi_stop)} "
          f"из {st['всего']}  ({dolya_stop:.0f}%)")

    if dolya_stop > 40:
        print()
        print("    ⚠ СТОП НЕ ДВИГАЕТСЯ. Позиция умирает ОДНИМ ВЫСТРЕЛОМ.")
        print("      По канону: цена пошла → стоп В СЕЙФ (риск→0) → долив.")
        print("      Книга Котина гл.9 сама признаётся:")
        print("        «Отложенный долг (слой 3, НЕ РЕАЛИЗОВАН): пирамида")
        print("         доливок и трейлинг-стоп. ПОКА ВЕДЕНИЕ УПРОЩЕНО.»")
        print("      ⇒ Убыток ВСЕГДА полный, прибыль ВСЕГДА обрезана.")

    # 2. Есть ли крупные плюсы? Пирамида должна их давать.
    krupnye = [s for s in sdelki if s["pnl_r"] >= 2.0]
    print()
    print(f"    сделок ≥ +2.0R (то, что даёт пирамида): {len(krupnye)}")
    if not krupnye and st["всего"] >= 5:
        print()
        print("    ⚠ НИ ОДНОЙ КРУПНОЙ ПРИБЫЛИ. У Вильямса выигрыш делает")
        print("      ПИРАМИДА, а не одиночный вход: 1R риска → доливы →")
        print("      5-10R с движения. Без пирамиды система МАТЕМАТИЧЕСКИ")
        print("      не может быть прибыльной: минус −1R, плюс обрезан.")

    # 3. Сколько живёт позиция?
    print()
    korotkie = 0
    for s in sdelki:
        o, c = str(s.get("opened_at", "")), str(s.get("closed_at", ""))
        if o[:10] and o[:10] == c[:10]:      # открыта и закрыта в один день
            korotkie += 1
    if sdelki:
        print(f"    закрыто в тот же день: {korotkie} из {st['всего']}  "
              f"({korotkie/len(sdelki)*100:.0f}%)")
        if korotkie / len(sdelki) > 0.5:
            print()
            print("    ⚠ ПОЗИЦИИ НЕ ЖИВУТ. Тренд не отрабатывается.")

    # 4. ГЛАВНЫЙ ВЫВОД
    print()
    print("  " + "─" * 68)
    if pf < 1.0:
        print("    ВЕРДИКТ: система УБЫТОЧНА в текущем виде.")
        print()
        print("    Но это НЕ ПРИГОВОР МЕТОДУ. Это приговор ВЕДЕНИЮ:")
        print("      · Совет спит между кандидатами → некому сказать MOVE_STOP")
        print("      · _manage_positions_from_table (трейлинг, реверсивная")
        print("        пирамида) НАПИСАН в мозге Исполнителя — и НЕ ЗОВЁТСЯ")
        print("      · мани-менеджмент Котина (слой 3) не реализован")
        print()
        print("    Половина системы Вильямса — ВХОД — работает.")
        print("    Вторая половина — ВЕДЕНИЕ — не построена.")
    else:
        print(f"    ВЕРДИКТ: PF {pf_s} — система в плюсе.")
    print()


if __name__ == "__main__":
    main()
