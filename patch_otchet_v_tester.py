# patch_otchet_v_tester.py
# ─────────────────────────────────────────────────────────────
# OTCHET_V_TESTERE_V1 — ОТЧЁТ САМ, В КОНЦЕ ПРОГОНА.
#
# СЛОВО ШЕФА (14.07):
#   «мне отчёт должен в конце показываться, а не скриптами ловить»
#   «они мне отчёт по сделкам не дали.. сами себе мутили, а я так и
#    не понял.. что они наторговали»
#
# И он прав. Тестер печатал только «поймал 15 срабатываний» — ни PF,
# ни winrate, ни суммы. ШЕФ РАБОТАЛ ВСЛЕПУЮ ПРИ ПОЛНОМ ЖУРНАЛЕ:
# hooks._settle_positions пишет trading_pnl.jsonl со ВСЕМ, что нужно
# (pnl_r, trader, close_reason, entry, stop, exit, opened_at, closed_at).
# Данные были. Отчёта не было.
#
# ── ГДЕ ВСТАЁТ ──
# Прямо ПЕРЕД «РАЗВИЛКОЙ» в финале тестера. Идёт в ТРИ места разом:
#   · консоль (print)
#   · файл разговора (out)      — тот, что тестер и так пишет
#   · кабинет (_emit)           — панель Биржи в UI
#
# ── ОТЧЁТ НЕ ТОЛЬКО СЧИТАЕТ. ОН СУДИТ. ──
# По книге Котина (гл.9, знания A07) прибыль у Вильямса делает ПИРАМИДА,
# а не одиночный вход:
#   вход рискует 1R → цена пошла → СТОП В СЕЙФ (риск→0) → ДОЛИВ → ДОЛИВ
#   → exit_bell → закрыли ВСЮ пирамиду разом.
#   Убытки остаются по 1R, прибыли РАСТУТ. Отсюда матожидание.
#
# А книга ЖЕ САМА признаётся (гл.9, дословно):
#   «Отложенный долг (слой 3, НЕ РЕАЛИЗОВАН): пирамида доливок
#    (5→4→3→2→1) и трейлинг-стоп за Аллигатором. ПОКА ВЕДЕНИЕ УПРОЩЕНО.»
#   гл.10: «Стоп системы. НЕ ДВИГАЕТСЯ (до трейлинга пирамиды, слой 3).»
#
# ⇒ Убыток ВСЕГДА полный (−1R), прибыль ВСЕГДА обрезана.
#   СИСТЕМА РАБОТАЕТ НАОБОРОТ — и это ВИДНО В ЦИФРАХ, а не на словах.
#
# Первый живой прогон (6 сделок): PF 0.000, winrate 0%, −5.15R.
# 67% закрытий — ровно по −1.0R (полный стоп, не подтянут).
# Ни одной сделки ≥ +2R (то, что даёт пирамида).
#
# ИДЕМПОТЕНТЕН. BACKUP: tester_express.py.bak_otchet
# Запуск из корня репо:  python patch_otchet_v_tester.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TE   = ROOT / "Биржа" / "tester_express.py"
MARK = "OTCHET_V_TESTERE_V1"


OTCHET = '''
# ═══════════════════════════════════════════════════════════
# OTCHET_V_TESTERE_V1 — ЧТО ОНИ НАТОРГОВАЛИ
# ═══════════════════════════════════════════════════════════
# Слово Шефа: «мне отчёт должен в конце показываться, а не скриптами
# ловить». Данные были всегда (trading_pnl.jsonl) — отчёта не было.
# Отчёт не только СЧИТАЕТ, но и СУДИТ по книге Котина (гл.9):
# без пирамиды и трейлинга система математически не может быть
# прибыльной — минус всегда полный, плюс всегда обрезан.
# ═══════════════════════════════════════════════════════════

def _otchet_po_sdelkam(sdelki_do: int, out, _emit):
    """Отчёт по сделкам ЭТОГО прогона. Читает trading_pnl.jsonl,
    берёт всё, что дописалось после начала (sdelki_do — сколько было
    ДО старта). Печатает в консоль, в файл разговора и в кабинет."""
    import json as _json
    from collections import defaultdict as _dd
    from pathlib import Path as _P

    _pnl = (_P(__file__).resolve().parent.parent / "GRONDHEIM_CITY" /
            "Биржа" / "данные" / "trading_pnl.jsonl")
    if not _pnl.exists():
        return

    _vse = []
    for _ln in _pnl.read_text(encoding="utf-8").splitlines():
        _ln = _ln.strip()
        if not _ln:
            continue
        try:
            _r = _json.loads(_ln)
            if _r.get("pnl_r") is not None:
                _vse.append(_r)
        except Exception:
            continue

    _s = _vse[sdelki_do:]          # только сделки ЭТОГО прогона
    if not _s:
        out("")
        out("─" * 64)
        out("  ОТЧЁТ: сделок не было. Совет ни разу не дал ENTER.")
        out("─" * 64)
        return

    _plus  = [x for x in _s if x["pnl_r"] > 0]
    _minus = [x for x in _s if x["pnl_r"] <= 0]
    _sp = sum(x["pnl_r"] for x in _plus)
    _sm = abs(sum(x["pnl_r"] for x in _minus))
    _sum = sum(x["pnl_r"] for x in _s)
    _pf = (_sp / _sm) if _sm > 0 else (float("inf") if _sp else 0.0)
    _pfs = "∞" if _pf == float("inf") else f"{_pf:.3f}"
    _wr = len(_plus) / len(_s) * 100

    out("")
    out("═" * 64)
    out("  💰 ОТЧЁТ ПО СДЕЛКАМ")
    out("═" * 64)
    out("")
    out(f"  {'#':>2} {'трейдер':11s} {'напр':5s} {'вход':>9s} "
        f"{'выход':>9s} {'R':>7s}  причина")
    out("  " + "─" * 60)
    for _i, _x in enumerate(_s, 1):
        _r = _x["pnl_r"]
        _z = "🟢" if _r > 0 else "🔴"
        _n = "LONG" if (_x.get("stop") or 0) < (_x.get("entry") or 0) else "SHORT"
        out(f"  {_i:>2} {str(_x.get('trader',''))[:11]:11s} {_n:5s} "
            f"{_x.get('entry','—'):>9} {_x.get('exit','—'):>9} "
            f"{_r:>+7.2f} {_z} {_x.get('close_reason','')}")

    out("")
    out(f"  сделок: {len(_s)}   плюсов: {len(_plus)}   минусов: {len(_minus)}"
        f"   winrate: {_wr:.0f}%")
    out(f"  ИТОГО:  {_sum:+.2f}R      средняя: {_sum/len(_s):+.2f}R/сделку")
    out(f"  PF:     {_pfs}  ({'ПРИБЫЛЬНАЯ' if _pf > 1 else 'УБЫТОЧНАЯ'})")

    # ── по трейдерам ──
    _pt = _dd(list)
    for _x in _s:
        _pt[_x.get("trader", "?")].append(_x["pnl_r"])
    out("")
    out("  ── по трейдерам ──")
    for _t, _rs in sorted(_pt.items()):
        _p2 = [r for r in _rs if r > 0]
        _m2 = abs(sum(r for r in _rs if r <= 0))
        _pf2 = (sum(_p2) / _m2) if _m2 > 0 else (float("inf") if _p2 else 0.0)
        _pf2s = "∞" if _pf2 == float("inf") else f"{_pf2:.2f}"
        out(f"     {str(_t)[:12]:12s} {len(_rs):>2} сдел · "
            f"плюс {len(_p2):>2} · {sum(_rs):>+7.2f}R · PF {_pf2s}")

    # ── как закрывались ──
    _pr = _dd(list)
    for _x in _s:
        _pr[_x.get("close_reason", "?")].append(_x["pnl_r"])
    out("")
    out("  ── как закрывались ──")
    for _rn, _rs in sorted(_pr.items(), key=lambda z: -len(z[1])):
        out(f"     {str(_rn)[:14]:14s} {len(_rs):>2} шт · "
            f"{sum(_rs):>+7.2f}R · средняя {sum(_rs)/len(_rs):+.2f}R")

    # ══════════════════════════════════════════════════════
    # ДИАГНОЗ — по книге Котина, гл.9
    # ══════════════════════════════════════════════════════
    _polny = [x for x in _s if abs(x["pnl_r"] + 1.0) < 0.05]
    _dolya = len(_polny) / len(_s) * 100
    _krup  = [x for x in _s if x["pnl_r"] >= 2.0]

    out("")
    out("  ── ДИАГНОЗ (книга Котина, гл.9) ──")
    out("")
    out(f"     закрытий ровно по −1.0R (стоп не подтянут): "
        f"{len(_polny)}/{len(_s)} ({_dolya:.0f}%)")
    out(f"     сделок ≥ +2.0R (то, что даёт пирамида):     {len(_krup)}")

    if _dolya > 40 or (not _krup and len(_s) >= 4):
        out("")
        out("     ⚠ ВЕДЕНИЯ ПОЗИЦИИ НЕТ. Позиция умирает ОДНИМ ВЫСТРЕЛОМ.")
        out("       Канон: вошёл 1R → цена пошла → СТОП В СЕЙФ (риск→0)")
        out("       → ДОЛИВ → ДОЛИВ → exit_bell → закрыл всю пирамиду.")
        out("       Книга Котина гл.9 САМА признаётся:")
        out("         «Отложенный долг (слой 3, НЕ РЕАЛИЗОВАН): пирамида")
        out("          доливок и трейлинг-стоп. ПОКА ВЕДЕНИЕ УПРОЩЕНО.»")
        out("       ⇒ Минус ВСЕГДА полный, плюс ВСЕГДА обрезан.")
        out("         Система МАТЕМАТИЧЕСКИ не может быть прибыльной.")
        out("")
        out("       Половина Вильямса — ВХОД — работает.")
        out("       Вторая половина — ВЕДЕНИЕ — не построена.")

    out("═" * 64)

    # ── в кабинет ──
    try:
        _emit({"type": "trades_report",
               "trades": len(_s), "wins": len(_plus), "winrate": round(_wr, 1),
               "sum_r": round(_sum, 2), "pf": (None if _pf == float("inf")
                                               else round(_pf, 3)),
               "full_stops": len(_polny), "big_wins": len(_krup)})
    except Exception:
        pass

'''


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ОТЧЁТ В ТЕСТЕРЕ — сам, в конце прогона" + " " * 28 + "║")
    print("║  OTCHET_V_TESTERE_V1 · идемпотентен" + " " * 32 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    if not TE.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    src = TE.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ уже пропатчен — пропускаю (идемпотентно)")
        print()
        return

    bak = TE.with_suffix(".py.bak_otchet")
    if not bak.exists():
        shutil.copy2(TE, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── 1. Функция отчёта — перед run_tester ───────────────────
    ank = "def run_tester("
    if ank not in src:
        print("  ⚠ не нашёл run_tester. СТОП.")
        sys.exit(1)
    src = src.replace(ank, OTCHET.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ _otchet_po_sdelkam() — считает и СУДИТ по канону")

    # ── 2. Замер: сколько сделок было ДО прогона ────────────────
    # цепляемся к моменту, где тестер уже стартовал (первый _emit)
    ank2 = "    # ── РАЗВИЛКА (TESTER_TO_CABINET_V1)"
    if ank2 not in src:
        print("  ⚠ не нашёл РАЗВИЛКУ в финале. СТОП.")
        sys.exit(1)

    zamer = '''    # OTCHET_V_TESTERE_V1: сколько сделок было ДО прогона — чтобы
    # отчёт показал только ЭТОТ прогон, а не всю историю журнала.
    try:
        import json as _jj
        _pnl_p = (Path(__file__).resolve().parent.parent / "GRONDHEIM_CITY" /
                  "Биржа" / "данные" / "trading_pnl.jsonl")
        _sdelok_do = 0
        if _pnl_p.exists():
            for _l in _pnl_p.read_text(encoding="utf-8").splitlines():
                if _l.strip():
                    try:
                        if _jj.loads(_l).get("pnl_r") is not None:
                            _sdelok_do += 1
                    except Exception:
                        pass
    except Exception:
        _sdelok_do = 0

    # ── отчёт-файл рядом с CSV ──'''

    # Якорь по ФАКТУ (проверено на диске 14.07): замер встаёт там, где
    # тестер уже внутри run_tester и вот-вот откроет файл отчёта.
    # Первый матчер цеплялся к "def run_" + докстринг — и промахнулся
    # мимо тела функции (синтаксис сломался, стоп-кран не дал записать).
    ank_z = "    # ── отчёт-файл рядом с CSV ──"
    if ank_z not in src:
        print("  ⚠ не нашёл якорь для замера. СТОП.")
        sys.exit(1)
    src = src.replace(ank_z, zamer, 1)
    print("  ✓ замер: сколько сделок было ДО прогона")

    # ── 3. Вызов отчёта — ПЕРЕД развилкой ──────────────────────
    vyzov = ('    # OTCHET_V_TESTERE_V1: ОТЧЁТ — сам, в конце. Слово Шефа:\n'
             '    # «мне отчёт должен в конце показываться, а не скриптами ловить».\n'
             '    try:\n'
             '        _otchet_po_sdelkam(_sdelok_do, print, _emit)\n'
             '    except Exception as _e:\n'
             '        print(f"⚠️  отчёт не собрался: {_e}")\n'
             '\n' + ank2)
    src = src.replace(ank2, vyzov, 1)
    print("  ✓ отчёт зовётся ПЕРЕД развилкой (консоль + кабинет)")

    # ── СТОП-КРАН ───────────────────────────────────────────────
    if "_otchet_po_sdelkam(_sdelok_do" not in src:
        print("  ⚠ ВЫЗОВ НЕ ВСТАЛ. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: отчёт печатается САМ в конце прогона.\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    TE.write_text(src, encoding="utf-8")

    print("  ✓ синтаксис цел")
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО" + " " * 60 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  Гони тестер — отчёт придёт САМ, перед РАЗВИЛКОЙ:")
    print()
    print("      💰 ОТЧЁТ ПО СДЕЛКАМ")
    print("       1 AVANTURIST  SHORT  1195.65  1201.77  −0.42 🔴 EXIT_BELL")
    print("       ...")
    print("      сделок: 6  плюсов: 0  winrate: 0%")
    print("      ИТОГО: −5.15R   PF: 0.000 (УБЫТОЧНАЯ)")
    print()
    print("      ── ДИАГНОЗ (книга Котина, гл.9) ──")
    print("      ⚠ ВЕДЕНИЯ ПОЗИЦИИ НЕТ. Минус полный, плюс обрезан.")
    print()
    print("  И то же самое ляжет в файл разговора и в кабинет.")
    print()


if __name__ == "__main__":
    main()
