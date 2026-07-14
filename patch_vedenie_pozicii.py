# patch_vedenie_pozicii.py
# ─────────────────────────────────────────────────────────────
# VEDENIE_POZICII_V1 — ВТОРАЯ ПОЛОВИНА ВИЛЬЯМСА. Позиция начинает ЖИТЬ.
#
# СЛОВО ШЕФА (14.07):
#   «не видел пирамидинга.. я вообще, ведение позиции не видел»
#
# И он прав. Первый прогон: 6 сделок, ПЛЮСОВ НОЛЬ, PF 0.000, −5.15R.
# 67% закрытий — ровно по −1.0R (стоп не подтянут). Ни одной сделки ≥+2R.
#
# ── ДИАГНОЗ (по коду и по книге, не по догадке) ──
#
# 1. КНИГА САМА ПРИЗНАЁТСЯ (KOTIN_PHILOSOPHY.md, гл.9, дословно):
#      «Отложенный долг (слой 3, НЕ РЕАЛИЗОВАН): полный мани-менеджмент
#       Котина — пирамида доливок (объём убывает 5→4→3→2→1) и
#       трейлинг-стоп всей пирамиды за линией Аллигатора («сейф»,
#       риск→0). ПОКА ВЕДЕНИЕ УПРОЩЕНО.»
#      гл.10: «Стоп системы. НЕ ДВИГАЕТСЯ (до трейлинга пирамиды, слой 3).»
#
# 2. МЕХАНИЗМ ВЕДЕНИЯ НАПИСАН — И НЕ ЗОВЁТСЯ.
#    `_manage_positions_from_table` (мозг Исполнителя) умеет ВСЁ:
#    трейлинг только в защиту (`_stop_tightens`), реверсивную пирамиду
#    (долив не крупнее предыдущего), долив тянет стоп тем же ходом.
#    Но он срабатывает ТОЛЬКО если трейдер сказал MOVE_STOP / ADD.
#
# 3. А ТРЕЙДЕР СПИТ.
#    tester_express.py:545 — цикл идёт ПО КАНДИДАТАМ СИТА.
#    wake_council зовётся ОДИН раз (:694), ВНУТРИ этого цикла.
#    Между кандидатами — только `_settle_bar` (чистая физика, стоп и
#    колокол, БЕЗ агентов).
#    ⇒ Илья открыл на баре 1000. Следующий кандидат — бар 1500.
#      500 баров Совет НЕ СОБИРАЕТСЯ НИ РАЗУ.
#      НЕКОМУ сказать MOVE_STOP. НЕКОМУ сказать ADD.
#      Позиция умирает по стопу, не дожив до решения.
#
# ⇒ ЧЕТВЁРТЫЙ КРАН ТОГО ЖЕ КЛАССА: механизм есть, написан правильно,
#   НИКЕМ НЕ ПОЗВАН. (магик · слепок · bdb_dir · теперь ведение)
#
# ── ПОЧЕМУ БЕЗ ЭТОГО СИСТЕМА МАТЕМАТИЧЕСКИ УБЫТОЧНА ──
# У Вильямса выигрыш делает ПИРАМИДА, а не одиночный вход:
#   вход рискует 1R → цена пошла → СТОП В СЕЙФ (риск→0) → ДОЛИВ →
#   ДОЛИВ → exit_bell → закрыли ВСЮ пирамиду разом.
#   Убытки остаются по 1R, а прибыли РАСТУТ.
# Без ведения: минус ВСЕГДА полный, плюс ВСЕГДА обрезан. НАОБОРОТ.
#
# ── РЕШЕНИЕ ШЕФА: ГИБРИД (вариант В) ──
#
# СТОП ТЯНЕТ КОД — на каждом баре, БЕЗ LLM.
#   Книга гл.10: «Стоп системы. НЕ ЛИЧНЫЙ. Если двигать произвольно —
#   это другая система, не Котин.» ⇒ трейлинг — НЕ ВОПРОС ВКУСА, а ЗАКОН.
#   Канон (гл.7): «Зубы (Teeth) — ГРАНИЦА ПИРАМИДЫ ДОЛИВОК. Пока цена
#   выше Зубов (для лонга) — пирамида жива.» ⇒ ТЯНЕМ ЗА ЗУБАМИ.
#   Это и есть «сейф» из гл.9. Стоп только В ЗАЩИТУ, никогда обратно.
#
# ДОЛИВ РЕШАЕТ ТРЕЙДЕР — это уже РИСК, тут характер.
#   Триггер (гл.8): «каждый новый пробитый фрактал по тренду наращивает
#   позицию, пока цена держит сторону Зубов».
#   ⇒ Будим ОДНОГО трейдера (не весь Совет!) и ТОЛЬКО на фрактале.
#     Илья дольёт агрессивно, Василий откажется. ХАРАКТЕР РЕШАЕТ.
#   Дёшево: фракталы по тренду — не каждый бар.
#
# ИДЕМПОТЕНТЕН. BACKUP: *.bak_vedenie
# Запуск из корня репо:  python patch_vedenie_pozicii.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOOKS = ROOT / "Биржа" / "hooks.py"
TE    = ROOT / "Биржа" / "tester_express.py"
MARK  = "VEDENIE_POZICII_V1"


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 1 — ТРЕЙЛИНГ ЗА ЗУБАМИ (код, без LLM)
# ═══════════════════════════════════════════════════════════

TREYLING = '''

# ═══════════════════════════════════════════════════════════
# VEDENIE_POZICII_V1 — ТРЕЙЛИНГ ЗА ЗУБАМИ («СЕЙФ»)
# ═══════════════════════════════════════════════════════════
# Канон (KOTIN_PHILOSOPHY.md):
#   гл.7: «Зубы (Teeth, красная линия) — ГРАНИЦА ПИРАМИДЫ ДОЛИВОК.
#          Пока цена выше Зубов (для лонга) — пирамида жива.
#          Пробой Зубов вниз = смерть пирамиды.»
#   гл.9: «трейлинг-стоп всей пирамиды за линией Аллигатора
#          («сейф», риск→0)»
#   гл.10: «Стоп системы. НЕ ЛИЧНЫЙ. Если двигать произвольно —
#          это другая система, не Котин.»
#
# ⇒ Трейлинг — НЕ ВОПРОС ВКУСА. Это ЗАКОН, и его исполняет КОД,
#   на каждом баре, без единого вызова LLM. Трейдер тут не решает.
#   (Решение Шефа: гибрид. Стоп — код. Долив — характер.)
#
# Стоп двигается ТОЛЬКО В ЗАЩИТУ (монотонно). Никогда обратно —
# ослабить стоп значит перестать быть Котиным.
# ═══════════════════════════════════════════════════════════

def _treyling_za_zubami(state: dict):
    """Тянет стоп всей пирамиды за Зубами (Teeth). Зовётся КАЖДЫЙ БАР,
    ДО проверки стопа — чтобы «сейф» успел сработать раньше, чем
    рынок дотянется до старого стопа.

    LONG:  стоп подтягивается вверх к Зубам (но не выше цены).
    SHORT: стоп подтягивается вниз к Зубам.

    Только в защитную сторону. Ослабление — молча игнорируем
    (по канону это уже не Котин)."""
    chain = state.get("chain_data", {})
    md    = chain.get("market_data", {})
    positions = chain.get("open_positions", []) or []
    if not positions or not md:
        return

    allig = md.get("alligator", {}) or {}
    teeth = allig.get("teeth")
    close = (md.get("price", {}) or {}).get("close")
    if teeth is None or close is None:
        return

    tstate = load_trading_state()
    live = tstate.get("positions", []) or []
    dirty = False

    for pos in live:
        if pos.get("status") != "OPEN":
            continue
        direction = (pos.get("direction") or "").upper()
        old = pos.get("stop")
        entry = pos.get("entry")
        if old is None or entry is None:
            continue

        if direction == "LONG":
            # цена ушла под Зубы — пирамида мертва, стоп не тянем
            # (её добьёт _settle_positions по стопу или колоколу)
            if close < teeth:
                continue
            novy = teeth
            if novy <= old:          # только в защиту
                continue
            if novy >= close:        # стоп не может быть выше цены
                continue
        elif direction == "SHORT":
            if close > teeth:
                continue
            novy = teeth
            if novy >= old:
                continue
            if novy <= close:
                continue
        else:
            continue

        # СЕЙФ: момент, когда риск стал НУЛЕВЫМ или отрицательным
        v_seyfe = ((direction == "LONG"  and old < entry <= novy) or
                   (direction == "SHORT" and old > entry >= novy))

        pos["stop"] = round(novy, 6)
        pos["trailed"] = pos.get("trailed", 0) + 1
        dirty = True

        if v_seyfe:
            print(f"[СЕЙФ] 🔒 {pos.get('trader')} {direction}: стоп "
                  f"{old} → {novy} — РИСК ОБНУЛЁН (за Зубами)")
        else:
            print(f"[ТРЕЙЛ] ⬆ {pos.get('trader')} {direction}: стоп "
                  f"{old} → {novy} (за Зубами)")

    if dirty:
        tstate["positions"] = live
        save_trading_state(tstate)

'''


def _patch_hooks() -> bool:
    if not HOOKS.exists():
        print(f"  ⚠ не нашёл {HOOKS}")
        return False
    src = HOOKS.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ hooks.py уже пропатчен — пропускаю")
        return True

    bak = HOOKS.with_suffix(".py.bak_vedenie")
    if not bak.exists():
        shutil.copy2(HOOKS, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # функция трейлинга — перед _settle_positions
    ank = "def _settle_positions(state: dict):"
    if ank not in src:
        print("  ⚠ не нашёл _settle_positions. СТОП.")
        return False
    src = src.replace(ank, TREYLING.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ _treyling_za_zubami() — стоп ползёт за Зубами («сейф»)")

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: трейлинг за Зубами (канон гл.7/9/10).\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ.")
        return False

    HOOKS.write_text(src, encoding="utf-8")
    return True


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 2 — ТЕСТЕР: трейлинг на каждом баре + долив на фрактале
# ═══════════════════════════════════════════════════════════

def _patch_tester() -> bool:
    if not TE.exists():
        print(f"  ⚠ не нашёл {TE}")
        return False
    src = TE.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ tester уже пропатчен — пропускаю")
        return True

    bak = TE.with_suffix(".py.bak_vedenie")
    if not bak.exists():
        shutil.copy2(TE, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── _settle_bar: трейлинг ДО закрытия ──────────────────────
    staroe = ("    st = {'chain_data': {'market_data': md,\n"
              "                         'open_positions': positions}}\n"
              "    try:\n"
              "        _settle_positions(st)   # закрывает по стопу/колоколу, "
              "пишет pnl_r")
    novoe = ("    st = {'chain_data': {'market_data': md,\n"
             "                         'open_positions': positions}}\n"
             "    try:\n"
             "        # VEDENIE_POZICII_V1: СНАЧАЛА тянем стоп за Зубами («сейф»),\n"
             "        # ПОТОМ проверяем закрытие. Порядок важен: сейф должен\n"
             "        # успеть сработать РАНЬШЕ, чем рынок дотянется до старого\n"
             "        # стопа. Это код, не LLM — по канону (гл.10) трейлинг НЕ\n"
             "        # вопрос вкуса, а закон системы.\n"
             "        try:\n"
             "            from hooks import _treyling_za_zubami\n"
             "            _treyling_za_zubami(st)\n"
             "            # стоп мог сдвинуться — перечитываем позиции\n"
             "            st['chain_data']['open_positions'] = (\n"
             "                load_trading_state().get('positions', []) or [])\n"
             "        except Exception as _te:\n"
             "            print(f'[ТРЕЙЛ] ⚠️  {_te}')\n"
             "\n"
             "        _settle_positions(st)   # закрывает по стопу/колоколу, "
             "пишет pnl_r")
    if staroe not in src:
        print("  ⚠ не нашёл тело _settle_bar. СТОП.")
        return False
    src = src.replace(staroe, novoe, 1)
    print("  ✓ _settle_bar: трейлинг на КАЖДОМ баре, ДО закрытия")

    # ── ДОЛИВ: будим ОДНОГО трейдера на фрактале по тренду ─────
    doliv = '''

# ═══════════════════════════════════════════════════════════
# VEDENIE_POZICII_V1 — ДОЛИВ: БУДИМ ТРЕЙДЕРА НА ФРАКТАЛЕ
# ═══════════════════════════════════════════════════════════
# Канон (гл.8): «каждый новый пробитый фрактал по тренду наращивает
# позицию, пока цена держит сторону Зубов».
#
# Стоп тянет КОД (закон). А долив — РИСК, и тут решает ХАРАКТЕР:
# Илья дольёт агрессивно, Василий откажется. Решение Шефа: гибрид.
#
# ⚠ БУДИМ ОДНОГО ТРЕЙДЕРА, НЕ ВЕСЬ СОВЕТ. И ТОЛЬКО НА ФРАКТАЛЕ —
# не на каждом баре. Иначе разорение: позиция живёт сотни баров.
# Фракталы по тренду редки — цена копеечная.
# ═══════════════════════════════════════════════════════════

_VEDENIE_SLOT = {100001: ("торговый_хаос", "A06", "run_brut"),
                 100002: ("торговый_хаос", "A07", "run_avan"),
                 100003: ("торговый_хаос", "A08", "run_cons")}


def _vesti_poziciyu(window, symbol, timeframe, point, out=print):
    """Долив по канону: новый фрактал по тренду → будим ХОЗЯИНА позиции
    (одного!) → он решает ADD / MOVE_STOP / HOLD своим характером.

    Возвращает True, если кого-то будили (для счёта вызовов)."""
    from williams_core import build_market_data
    from hooks import load_trading_state

    positions = [p for p in (load_trading_state().get('positions', []) or [])
                 if p.get('status') == 'OPEN']
    if not positions:
        return False

    md = build_market_data(window, symbol=symbol,
                           timeframe=timeframe, point=point)
    if not md:
        return False

    fr = md.get('fractals', {}) or {}
    allig = md.get('alligator', {}) or {}
    teeth = allig.get('teeth')
    close = (md.get('price', {}) or {}).get('close')
    if teeth is None or close is None:
        return False

    budili = False
    for pos in positions:
        d = (pos.get('direction') or '').upper()

        # ── ТРИГГЕР: свежий фрактал ПО ТРЕНДУ, цена держит сторону Зубов ──
        # Ключи ПРОВЕРЕНЫ НА ДИСКЕ (14.07): build_market_data отдаёт
        #   fractals: {'last_up': {'price':..., 'bar_index':..., 'date':...},
        #              'last_down': {...}, 'count_up':.., 'count_down':..}
        # Первый заход я написал fr.get('up')/fr.get('bull') — ПО ДОГАДКЕ.
        # Долив не сработал бы НИ РАЗУ. Смотреть в код, потом писать.
        if d == 'LONG':
            if close < teeth:          # пирамида мертва (гл.7)
                continue
            f = fr.get('last_up') or {}
            f_price = f.get('price') if isinstance(f, dict) else None
            if not f_price or close <= f_price:   # фрактал ещё не пробит
                continue
        elif d == 'SHORT':
            if close > teeth:
                continue
            f = fr.get('last_down') or {}
            f_price = f.get('price') if isinstance(f, dict) else None
            if not f_price or close >= f_price:
                continue
        else:
            continue

        # тот же фрактал дважды не доливаем
        if pos.get('last_fractal') == f_price:
            continue

        slot = _VEDENIE_SLOT.get(pos.get('magic'))
        if not slot:
            continue
        ceh, sid, fn = slot

        out(f"  🔺 ДОЛИВ? {pos.get('trader')} {d}: фрактал {f_price} пробит, "
            f"цена {close} держит Зубы {round(teeth, 2)} — бужу хозяина")

        try:
            brain = _slot_brain(ceh, sid)
            r = getattr(brain, fn)(symbol=symbol, timeframe=timeframe)
            if not (r or {}).get('ok'):
                continue
            budili = True

            # пометим фрактал — второй раз по нему не будим
            _ts = load_trading_state()
            for _p in _ts.get('positions', []) or []:
                if _p.get('magic') == pos.get('magic'):
                    _p['last_fractal'] = f_price
            from hooks import save_trading_state
            save_trading_state(_ts)

            nar = (r.get('narrative') or '').strip()
            if nar:
                out(f"     └─ {nar[:200]}")
        except Exception as _e:
            out(f"     ⚠️  ведение не вышло: {_e}")

    return budili

'''
    ank2 = "def _table_snapshot():"
    if ank2 not in src:
        print("  ⚠ не нашёл _table_snapshot. СТОП.")
        return False
    src = src.replace(ank2, doliv.lstrip("\n") + "\n" + ank2, 1)
    print("  ✓ _vesti_poziciyu() — будит ХОЗЯИНА на фрактале (не весь Совет)")

    # ── зовём ведение в цикле досеттливания ────────────────────
    staroe3 = ("            for _b in range(_last_settled + 1, i + 1):")
    novoe3 = ("            # VEDENIE_POZICII_V1: на каждом баре между кандидатами\n"
              "            # позиция ЖИВЁТ: код тянет стоп (в _settle_bar), а на\n"
              "            # фрактале по тренду просыпается ХОЗЯИН и решает — долить\n"
              "            # или нет. Раньше здесь была только физика: позиция\n"
              "            # умирала одним выстрелом, не дожив до решения.\n"
              "            for _b in range(_last_settled + 1, i + 1):")
    if staroe3 in src:
        src = src.replace(staroe3, novoe3, 1)

    # вставляем вызов ведения ПОСЛЕ _settle_bar внутри того же цикла
    staroe4 = ("                _settle_bar(bars_all[max(0, _b - 299):_b + 1],\n"
               "                            symbol, timeframe, point)")
    novoe4 = ("                _settle_bar(bars_all[max(0, _b - 299):_b + 1],\n"
              "                            symbol, timeframe, point)\n"
              "                # VEDENIE_POZICII_V1: долив — только если позиция жива\n"
              "                try:\n"
              "                    _vesti_poziciyu(bars_all[max(0, _b - 299):_b + 1],\n"
              "                                    symbol, timeframe, point, out)\n"
              "                except Exception as _ve:\n"
              "                    print(f'[ВЕДЕНИЕ] ⚠️  {_ve}')")
    if staroe4 not in src:
        print("  ⚠ не нашёл вызов _settle_bar в цикле. СТОП.")
        return False
    src = src.replace(staroe4, novoe4, 1)
    print("  ✓ ведение зовётся на каждом баре (дёшево: только на фрактале)")

    # ── СТОП-КРАН ──────────────────────────────────────────────
    if "_vesti_poziciyu(bars_all" not in src:
        print("  ⚠ ВЕДЕНИЕ НЕ ЗОВЁТСЯ. НЕ ПИШУ ФАЙЛ.")
        return False

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: позиция ЖИВЁТ — трейлинг кодом, долив характером.\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ.")
        return False

    TE.write_text(src, encoding="utf-8")
    return True


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ВЕДЕНИЕ ПОЗИЦИИ — вторая половина Вильямса" + " " * 24 + "║")
    print("║  VEDENIE_POZICII_V1 · гибрид (решение Шефа)" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  Книга Котина гл.9 сама признаётся:")
    print("    «Отложенный долг (слой 3, НЕ РЕАЛИЗОВАН): пирамида доливок")
    print("     и трейлинг-стоп. ПОКА ВЕДЕНИЕ УПРОЩЕНО.»")
    print()

    if not HOOKS.exists() or not TE.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    print("── ЯДРО: СТОП ТЯНЕТ КОД (закон, гл.10) ──")
    if not _patch_hooks():
        print("\n⚠ hooks не пропатчен. Тестер не трогаю. СТОП.")
        sys.exit(1)

    print()
    print("── ТЕСТЕР: ДОЛИВ РЕШАЕТ ТРЕЙДЕР (риск, характер) ──")
    if not _patch_tester():
        print("\n⚠ тестер не пропатчен. СТОП.")
        sys.exit(1)

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО — позиция начинает ЖИТЬ" + " " * 36 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ГИБРИД (решение Шефа):")
    print("    СТОП  — тянет КОД, каждый бар, за ЗУБАМИ. Без LLM.")
    print("            Канон гл.10: «Стоп СИСТЕМЫ. Не личный.» Это ЗАКОН.")
    print("            Дошёл до входа → 🔒 СЕЙФ, риск обнулён.")
    print("    ДОЛИВ — решает ТРЕЙДЕР, и только на ФРАКТАЛЕ по тренду.")
    print("            Канон гл.8. Это РИСК — тут характер:")
    print("            Илья дольёт агрессивно, Василий откажется.")
    print()
    print("  ЦЕНА: будим ОДНОГО трейдера (не Совет!) и только на фрактале.")
    print("        Фракталы по тренду редки — копейки.")
    print()
    print("  ЧТО ИСКАТЬ В ЛОГЕ:")
    print("    [ТРЕЙЛ] ⬆ AVANTURIST LONG: стоп 1234.67 → 1238.10 (за Зубами)")
    print("    [СЕЙФ]  🔒 AVANTURIST LONG: стоп → 1247.40 — РИСК ОБНУЛЁН")
    print("    🔺 ДОЛИВ? BRUT LONG: фрактал 1252.30 пробит — бужу хозяина")
    print()
    print("  И в отчёте: закрытий по −1.0R должно СТАТЬ МЕНЬШЕ,")
    print("  а сделки ≥ +2R — ПОЯВИТЬСЯ. Вот это и будет доказательство.")
    print()


if __name__ == "__main__":
    main()
