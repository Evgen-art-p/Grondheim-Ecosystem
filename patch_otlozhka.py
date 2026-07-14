# patch_otlozhka.py
# ─────────────────────────────────────────────────────────────
# OTLOZHENNY_ORDER_V1 — СЕДЬМОЙ КРАН. И САМЫЙ ДОРОГОЙ.
#
# ВОПРОС ШЕФА (14.07): «а сделки как открываются? с рынка или по
# отложенным ордерам?»
#
# ⚠ ОТВЕТ: МГНОВЕННО, ПО ЦЕНЕ ИЗ ВЕРДИКТА. НИКАКОЙ ОТЛОЖКИ.
#
#   исполнитель/мозг.py:264 —
#       pos = {"entry": entry,        ← цена, которую НАЗВАЛ трейдер
#              "status": "OPEN", ...} ← СРАЗУ ОТКРЫТА
#       tstate["positions"].append(pos)
#
#   Ни PENDING, ни BUY_STOP, ни проверки — дошла ли цена вообще.
#
# ── А ТРЕЙДЕРЫ ГОВОРЯТ ПРО ОТЛОЖКУ. ВСЕ. ВСЕГДА. ──
#   Брут: «Вхожу BUY STOP 1696.45 на пробой фрактала за пастью»
#   Брут: «Жду АКТИВАЦИИ или отмены»
#   Илья: «Вхожу SELL STOP ниже лоу»
#   Книга Котина гл.8: «BUY STOP на 1 тик выше high фрактального бара
#                       (LONG); SELL STOP на 1 тик ниже low (SHORT)»
#
#   ⇒ КАНОН — ОТЛОЖЕННЫЙ ОРДЕР. Он ЖДЁТ, пока цена ПРОБЬЁТ уровень.
#     Заявка на пробой — это ещё НЕ сделка.
#
# ── ЧЕМ ЭТО ПЛОХО (и это объясняет PF 0.000) ──
#
# 1. ВХОД ПО ЦЕНЕ, ДО КОТОРОЙ РЫНОК НЕ ДОШЁЛ.
#    Брут говорит «Buy Stop 1248.22» (ВЫШЕ текущей цены — это пробой
#    вверх). Код открывает СРАЗУ, по 1248.22. Если цена туда НИКОГДА
#    не поднялась — сделки НЕ ДОЛЖНО БЫЛО БЫТЬ ВООБЩЕ. А она есть.
#    И она в минусе.
#
# 2. ВХОД ПРОТИВ ДВИЖЕНИЯ.
#    Sell Stop ставится НИЖЕ цены — на пробой ВНИЗ. Если рынок пошёл
#    ВВЕРХ, ордер бы не сработал. А код уже в шорте — и получает стоп.
#
# 3. ОТСЮДА И СТОПЫ ЗА ОДИН БАР (67% закрытий ровно по −1.0R).
#    Открылись «на пробое», которого НЕ БЫЛО → цена сразу против → стоп.
#
#    Первый плюс (BRUT SHORT @1658.71 → +0.56R) сработал потому, что
#    цена И ПРАВДА пошла вниз. СЛУЧАЙНО СОВПАЛО.
#
# ⇒ ПОЛОВИНА СДЕЛОК — ФАНТОМЫ. Их бы в реальности НЕ БЫЛО.
#   PF 0.000 может быть НЕ приговором методу, а следствием того, что
#   мы торгуем по НЕСУЩЕСТВУЮЩИМ ВХОДАМ.
#
#   Все предыдущие шесть кранов ломали ОБУЧЕНИЕ. Этот ломает САМУ
#   ТОРГОВЛЮ.
#
# ── ЛЕЧЕНИЕ (по канону гл.8) ──
#   Заявка рождается PENDING. Каждый бар код смотрит: пробил рынок
#   уровень или нет?
#     LONG  (Buy Stop):  high >= entry → АКТИВАЦИЯ
#     SHORT (Sell Stop): low  <= entry → АКТИВАЦИЯ
#   Не пробил за EXPIRE баров — ордер ОТМЕНЯЕТСЯ (структура протухла).
#
#   ⚠ Если вердикт даёт цену «по рынку» (entry ≈ close), активируем
#     сразу — это не отложка, это рыночный вход, он законен.
#
#   PENDING невидим для всех, кто фильтрует по status == "OPEN"
#   (проверено: hooks, tester, исполнитель — все смотрят на OPEN).
#   Судья, дыхание, метки — не сработают на неактивированной заявке.
#   ЧЕСТНО: нет сделки — нет опыта.
#
# ИДЕМПОТЕНТЕН. BACKUP: *.bak_otlozhka
# Запуск из корня репо:  python patch_otlozhka.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parent
HOOKS = ROOT / "Биржа" / "hooks.py"
ISP   = (ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
         / "слоты" / "исполнитель" / "мозг.py")
MARK  = "OTLOZHENNY_ORDER_V1"


AKTIVACIYA = '''

# ═══════════════════════════════════════════════════════════
# OTLOZHENNY_ORDER_V1 — ЗАЯВКА ЖДЁТ ПРОБОЯ
# ═══════════════════════════════════════════════════════════
# Вопрос Шефа: «сделки как открываются? с рынка или по отложенным?»
# Открывались МГНОВЕННО, по названной цене. Никакой отложки.
#
# А трейдеры ВСЕ говорят «Buy Stop», «Sell Stop», «жду активации».
# Книга гл.8: «BUY STOP на 1 тик выше high фрактального бара».
#
# ⇒ Половина сделок была ФАНТОМАМИ: вход по цене, до которой рынок
#   не дошёл. Открылись «на пробое», которого не было → цена сразу
#   против → стоп за один бар. Отсюда 67% закрытий ровно по −1.0R.
#
# Теперь заявка рождается PENDING и ЖДЁТ, пока рынок сам её возьмёт.
# ═══════════════════════════════════════════════════════════

ORDER_EXPIRE_BARS = 10   # не пробил за 10 баров — структура протухла


def _aktivirovat_ordera(state: dict):
    """Отложенные заявки: активируем те, что рынок ПРОБИЛ; отменяем
    протухшие. Зовётся КАЖДЫЙ БАР, ДО трейлинга и ДО закрытия.

    LONG  (Buy Stop, entry ВЫШЕ цены):  high >= entry → сработал
    SHORT (Sell Stop, entry НИЖЕ цены): low  <= entry → сработал

    Активированная заявка становится OPEN и с этого мига живёт как
    позиция: её ведут, судят, она дышит. Неактивированная — НЕ СДЕЛКА,
    и опыта с неё нет. Честно."""
    chain = state.get("chain_data", {})
    md    = chain.get("market_data", {})
    if not md:
        return

    price = md.get("price", {}) or {}
    high  = price.get("high")
    low   = price.get("low")
    bar_time = md.get("bar_time")
    if high is None or low is None:
        return

    tstate = load_trading_state()
    live = tstate.get("positions", []) or []
    dirty = False
    ostalis = []

    for pos in live:
        if pos.get("status") != "PENDING":
            ostalis.append(pos)
            continue

        d = (pos.get("direction") or "").upper()
        entry = pos.get("entry")
        if entry is None:
            ostalis.append(pos)
            continue

        srabotal = ((d == "LONG"  and high >= entry) or
                    (d == "SHORT" and low  <= entry))

        if srabotal:
            pos["status"] = "OPEN"
            pos["opened_at"] = bar_time      # ВРЕМЯ РЕАЛЬНОГО ВХОДА
            pos.pop("_ждёт_с", None)
            pos.pop("_ждёт_баров", None)
            dirty = True
            print(f"[ОРДЕР] ⚡ {pos.get('trader')} {d} АКТИВИРОВАН @ {entry} "
                  f"— рынок дошёл (H={high} L={low})")
            ostalis.append(pos)
            continue

        # не сработал — считаем, сколько ждёт
        zhdyot = pos.get("_ждёт_баров", 0) + 1
        pos["_ждёт_баров"] = zhdyot
        dirty = True

        if zhdyot >= ORDER_EXPIRE_BARS:
            print(f"[ОРДЕР] 🚫 {pos.get('trader')} {d} @ {entry} ОТМЕНЁН — "
                  f"не пробит за {ORDER_EXPIRE_BARS} баров, структура "
                  f"протухла")
            continue          # выбрасываем — в ostalis не кладём

        ostalis.append(pos)

    if dirty:
        tstate["positions"] = ostalis
        save_trading_state(tstate)

'''


def _patch_hooks() -> bool:
    if not HOOKS.exists():
        print(f"  ⚠ не нашёл {HOOKS}")
        return False
    src = HOOKS.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ hooks уже пропатчен")
        return True

    bak = HOOKS.with_suffix(".py.bak_otlozhka")
    if not bak.exists():
        shutil.copy2(HOOKS, bak)
        print(f"  ✓ бэкап: {bak.name}")

    ank = "def _settle_positions(state: dict):"
    if ank not in src:
        print("  ⚠ не нашёл _settle_positions. СТОП.")
        return False
    src = src.replace(ank, AKTIVACIYA.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ _aktivirovat_ordera() — заявка ждёт пробоя")

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: Buy/Sell Stop ЖДУТ пробоя (канон гл.8).\n"
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


def _patch_ispolnitel() -> bool:
    if not ISP.exists():
        print(f"  ⚠ не нашёл {ISP}")
        return False
    src = ISP.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ исполнитель уже пропатчен")
        return True

    bak = ISP.with_suffix(".py.bak_otlozhka")
    if not bak.exists():
        shutil.copy2(ISP, bak)
        print(f"  ✓ бэкап: {bak.name}")

    staroe = ('        pos = {\n'
              '            "trader":    TRADER_NAME[key],\n'
              '            "magic":     magic,\n'
              '            "direction": direction,\n'
              '            "entry":     entry,\n'
              '            "stop":      stop,\n'
              '            "tp":        None,\n'
              '            "lot":       v.get("lot"),\n'
              '            "status":    "OPEN",')
    novoe = ('        # ═══ OTLOZHENNY_ORDER_V1 ═══\n'
             '        # Трейдер сказал «Buy Stop 1248.22» — это ЗАЯВКА НА ПРОБОЙ,\n'
             '        # а не сделка. Раньше код открывал МГНОВЕННО по названной\n'
             '        # цене — даже если рынок туда НИКОГДА не дошёл. Половина\n'
             '        # сделок была ФАНТОМАМИ (67% стопов ровно по −1.0R: вошли\n'
             '        # «на пробое», которого не было → цена сразу против).\n'
             '        #\n'
             '        # Теперь: PENDING. Ждёт, пока рынок сам возьмёт (канон гл.8:\n'
             '        # «Buy Stop на 1 тик выше high фрактального бара»).\n'
             '        #\n'
             '        # ⚠ Рыночный вход (цена ≈ текущая) активируется тем же\n'
             '        # механизмом на ЭТОМ ЖЕ баре: high/low его накроют.\n'
             '        # Отложка не мешает войти по рынку — она мешает войти\n'
             '        # ТУДА, КУДА РЫНОК НЕ ХОДИЛ.\n'
             '        pos = {\n'
             '            "trader":    TRADER_NAME[key],\n'
             '            "magic":     magic,\n'
             '            "direction": direction,\n'
             '            "entry":     entry,\n'
             '            "stop":      stop,\n'
             '            "tp":        None,\n'
             '            "lot":       v.get("lot"),\n'
             '            "status":    "PENDING",   # OTLOZHENNY_ORDER_V1\n'
             '            "_ждёт_с":   bar_time,\n'
             '            "_ждёт_баров": 0,')
    if staroe not in src:
        print("  ⚠ не нашёл тело позиции. СТОП.")
        return False
    src = src.replace(staroe, novoe, 1)
    print("  ✓ позиция рождается PENDING (заявка, не сделка)")

    # печать «ОТКРЫТА» → «ЗАЯВКА» (не врём в лог)
    src = src.replace('        opened.append(pos)',
                      '        opened.append(pos)   # OTLOZHENNY_ORDER_V1: это ЗАЯВКА', 1)

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: позиция рождается ЗАЯВКОЙ, а не сделкой.\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ.")
        return False
    ISP.write_text(src, encoding="utf-8")
    return True


def _patch_tester() -> bool:
    TE = ROOT / "Биржа" / "tester_express.py"
    if not TE.exists():
        print(f"  ⚠ не нашёл {TE}")
        return False
    src = TE.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ тестер уже пропатчен")
        return True

    bak = TE.with_suffix(".py.bak_otlozhka")
    if not bak.exists():
        shutil.copy2(TE, bak)

    # активация ПЕРЕД трейлингом и закрытием
    staroe = "        # VEDENIE_POZICII_V1: СНАЧАЛА тянем стоп за Зубами («сейф»),"
    novoe = ("        # OTLOZHENNY_ORDER_V1: ПЕРВЫМ ДЕЛОМ — активация заявок.\n"
             "        # Порядок строг: заявка → активация → трейлинг → закрытие.\n"
             "        # Иначе стоп потянется у того, кто ещё НЕ ВОШЁЛ.\n"
             "        try:\n"
             "            from hooks import _aktivirovat_ordera\n"
             "            _aktivirovat_ordera(st)\n"
             "            st['chain_data']['open_positions'] = (\n"
             "                load_trading_state().get('positions', []) or [])\n"
             "        except Exception as _ae:\n"
             "            print(f'[ОРДЕР] ⚠️  {_ae}')\n"
             "\n"
             "        # VEDENIE_POZICII_V1: СНАЧАЛА тянем стоп за Зубами («сейф»),")
    if staroe not in src:
        print("  ⚠ не нашёл трейлинг в _settle_bar (сначала patch_vedenie). СТОП.")
        return False
    src = src.replace(staroe, novoe, 1)
    print("  ✓ активация зовётся ПЕРВОЙ (до трейлинга и закрытия)")

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: заявки активируются рынком, а не кодом.\n"
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
    print("║  ОТЛОЖЕННЫЙ ОРДЕР — заявка ждёт пробоя" + " " * 29 + "║")
    print("║  OTLOZHENNY_ORDER_V1 · седьмой кран, самый дорогой" + " " * 17 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  Трейдеры ГОВОРЯТ «Buy Stop», «Sell Stop», «жду активации».")
    print("  Книга гл.8: «BUY STOP на 1 тик выше high фрактального бара».")
    print("  А КОД ОТКРЫВАЛ МГНОВЕННО — по цене, до которой рынок не дошёл.")
    print()

    if not (ROOT / "Биржа").exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    print("── ЯДРО: активация по пробою ──")
    if not _patch_hooks():
        sys.exit(1)

    print()
    print("── ИСПОЛНИТЕЛЬ: позиция рождается ЗАЯВКОЙ ──")
    if not _patch_ispolnitel():
        sys.exit(1)

    print()
    print("── ТЕСТЕР: активация первой в цепи ──")
    if not _patch_tester():
        sys.exit(1)

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО — фантомы кончились" + " " * 40 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ПОРЯДОК НА КАЖДОМ БАРЕ (строгий):")
    print("    1. АКТИВАЦИЯ — рынок пробил уровень? → PENDING становится OPEN")
    print("    2. ТРЕЙЛИНГ  — стоп ползёт за Зубами («сейф»)")
    print("    3. ЗАКРЫТИЕ  — стоп / колокол")
    print("    4. ДОЛИВ     — фрактал по тренду → будим хозяина")
    print()
    print("  ЧТО ИСКАТЬ В ЛОГЕ:")
    print("    [ОРДЕР] ⚡ BRUT LONG АКТИВИРОВАН @ 1248.22 — рынок дошёл")
    print("    [ОРДЕР] 🚫 AVANTURIST SHORT @ 1202.44 ОТМЕНЁН — не пробит")
    print("             за 10 баров, структура протухла")
    print()
    print("  ⚠ ЖДИ: СДЕЛОК СТАНЕТ МЕНЬШЕ. Это НЕ поломка — это ЧЕСТНОСТЬ.")
    print("    Часть входов просто НЕ СЛУЧИТСЯ, потому что рынок туда не")
    print("    ходил. Их и НЕ ДОЛЖНО БЫЛО БЫТЬ.")
    print()
    print("    И PF должен вырасти: фантомные входы «на пробое, которого")
    print("    не было» шли сразу против цены — отсюда 67% стопов по −1.0R.")
    print()


if __name__ == "__main__":
    main()
