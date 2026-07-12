# -*- coding: utf-8 -*-
"""
patch_sud_sensorov_v2.py
────────────────────────────────────────────────────────────────────
СУД СЕНСОРОВ — их опыт: работа над своими ошибками (слово Шефа, 12.07).

Сенсор не теряет денег. Он промахивается СЛОВОМ. Сказал «жду» — рынок
ушёл без него. Сказал «зверь кормится» — сделка легла в минус. Судит его
ИСХОД, до которого он сам не дожил: сделка трейдера после его слова.

ЧЕСТНО ПРО v1: первая версия этого патча лепила в nositel ВТОРОЕ
определение sudit_sensora — рядом с уже существующим. Python берёт
последнее; получился второй источник правды в одном файле — ровно та
болезнь, от которой лечимся весь день (пять копий магика). Зеркало это
поймало до диска. v2: дубли не плодит, берёт то, что есть, и достраивает
недостающее.

ТРИ ШВА:

  1. ФОТО СТОЛА НА ВХОДЕ (hooks._persist_trading_state).
     Позиция уже помнит ветер входа (entry_bias). Теперь запоминает и
     ПОКАЗАНИЯ ВСЕХ ЧЕТЫРЁХ СЕНСОРОВ на баре входа — целиком, как они
     лежали в trading_state. Без слепка на закрытии судить нечего: стол
     перетирается каждый бар, и судить сенсора по ЧУЖОМУ бару было бы
     клеветой.

  2. СУД НА ЗАКРЫТИИ (hooks._judge_iskra_by_result — была заглушка).
     Рынок закрыл сделку → каждому сенсору возвращается ЕГО слово вместе
     с ответом рынка. Судит КОД, не LLM. Логика (nositel):
         ЗВАЛ  + минус         → МОЯ ОШИБКА (всегда в опыт — его школа)
         МОЛЧАЛ + крупный плюс → ПРОСПАЛ    (всегда в опыт)
         ЗВАЛ  + крупный плюс  → подтвердилось
         МОЛЧАЛ + крупный минус→ «моё молчание было право»
         остальное             → рутина, в якоря не идёт
     «Звал» = его показание тянуло В СТОРОНУ сделки: компас Веры против
     направления входа, сторона фрактала Ганса, фаза толпы под лонг/шорт.

  3. РУБИЛЬНИК УЧЁБЫ ОДИН НА ВСЕХ (nositel.UCHIT).
     Стерильность тестера глушила ТОЛЬКО запись трейдеров (подменой
     zapisat_vyvod). Сенсоры писали бы МИМО неё — и стерильный бэктест
     калечил бы Веру с Моржом. Теперь один флаг гасит всю запись в живых.

Требует: patch_klon_dushi_v2 (души сенсоров живы).
Идемпотентно. .bak рядом.  Из КОРНЯ репы:
    python patch_sud_sensorov_v2.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "SUD_SENSOROV_V2"

NOSITEL = Path("Биржа") / "nositel.py"
HOOKS = Path("Биржа") / "hooks.py"
TESTER = Path("Биржа") / "tester_express.py"

# ── секция суда сенсоров: вшиваем ТОЛЬКО если её нет ────────────
SENSOR_SECTION = '''# ════════════════════════════════════════════════════════════
# СУД СЕНСОРА — их опыт есть работа над своими ошибками (слово Шефа)
# ────────────────────────────────────────────────────────────
# У трейдера судья очевиден: рынок, деньги, R. А сенсор не торгует —
# он НАКРЫВАЕТ СТОЛ. Его правота проверяется ИСХОДОМ, до которого он
# сам не дожил: сделкой, которую его слово породило или проспало.
#
# Симметрия (без LLM, всё считает код):
#     ЗВАЛ  + минус  → ОШИБКА (всегда в опыт — это и есть его школа)
#     МОЛЧАЛ + крупный плюс → ПРОСПАЛ (всегда в опыт)
#     ЗВАЛ  + крупный плюс  → подтверждение
#     МОЛЧАЛ + крупный минус → «моё молчание было право»
#     остальное → рутина, в якоря не идёт (память живёт в журналах)
#
# «Звал» — значит его показание тянуло В СТОРОНУ сделки. Считается
# по слепку стола НА БАРЕ ВХОДА (не по текущему: стол перетирается
# каждый бар — судить сенсора по чужому бару было бы клеветой).
# ════════════════════════════════════════════════════════════

SENSOR_SLOTS = {           # ключ в trading_state → слот цеха
    "iskra": "A01",
    "morj":  "A02",
    "panic": "A03",
    "hans":  "A04",
}


def _zval(key: str, pokazanie: dict, direction: str):
    """Тянуло ли показание сенсора В СТОРОНУ сделки. None — не судим."""
    if not pokazanie or not direction:
        return None
    if key == "iskra":
        if pokazanie.get("t1_status") not in ("DETECTED", "CONFIRMED"):
            return False
        kompas = pokazanie.get("trend_direction")
        if not kompas:
            return False
        return ((kompas == "BULL" and direction == "LONG") or
                (kompas == "BEAR" and direction == "SHORT"))
    if key == "morj":
        # звал = подтвердил масштаб (зверь проснулся / волна 1 засчитана)
        return bool(pokazanie.get("wave_1_validated")) or \
            pokazanie.get("morj_status") == "AWAKE"
    if key == "panic":
        faza = pokazanie.get("panic_phase")
        # толпа тянет в лонг на жадности, в шорт — на ликвидации
        if faza in ("FOMO", "GREED"):
            return direction == "LONG"
        if faza in ("LIQUIDATION", "PANIC"):
            return direction == "SHORT"
        return False
    if key == "hans":
        if not pokazanie.get("fractal_valid"):
            return False
        side = pokazanie.get("fractal_side")
        if not side:
            return True            # фрактал есть, стороны не назвал
        return ((side in ("UP", "LONG") and direction == "LONG") or
                (side in ("DOWN", "SHORT") and direction == "SHORT"))
    return None


def _chto_skazal(key: str, p: dict) -> str:
    """Его собственное показание — словами, коротко. Для якоря."""
    if key == "iskra":
        zp = p.get("zero_point_price")
        return (f"точка {p.get('t1_status','—')} "
                f"{p.get('trend_direction') or ''} "
                f"{('@' + str(zp)) if zp else ''}").strip()
    if key == "morj":
        return (f"пасть {p.get('morj_status','—')}, "
                f"волна1={'да' if p.get('wave_1_validated') else 'нет'}")
    if key == "panic":
        return f"толпа {p.get('panic_phase','—')}"
    if key == "hans":
        fp = p.get("fractal_price")
        return (f"фрактал {'валиден' if p.get('fractal_valid') else 'нет'} "
                f"{p.get('fractal_side') or ''} {('@' + str(fp)) if fp else ''}").strip()
    return "—"


def sudit_sensora(key: str, pokazanie: dict, direction, pnl_r,
                  trader: str = "", bar: str = "") -> str:
    """Вывод сенсора из ЧУЖОЙ сделки, которую породило его слово.
    Пустая строка = рутина, в опыт не идёт."""
    if pnl_r is None or not pokazanie:
        return ""
    r = round(float(pnl_r), 2)
    kray = abs(r) >= KRAYNOST_R
    zval = _zval(key, pokazanie, direction)
    if zval is None:
        return ""
    skazal = _chto_skazal(key, pokazanie)
    kto = (trader or "трейдер").capitalize()
    when = f" ({bar})" if bar else ""

    if zval and r < 0:
        return (f"МОЯ ОШИБКА{when}: я дал «{skazal}» — {kto} вошёл "
                f"{direction} и получил {r}R. Моё слово повело в минус.")
    if (not zval) and r > 0 and kray:
        return (f"ПРОСПАЛ{when}: я дал «{skazal}» — а {kto} взял "
                f"{direction} на {r}R без меня. Движение было, я его не увидел.")
    if zval and r > 0 and kray:
        return (f"Подтвердилось{when}: «{skazal}» — {kto} взял {r}R "
                f"по моему слову. Так это и работает.")
    if (not zval) and r < 0 and kray:
        return (f"Моё молчание было право{when}: я не звал, {kto} вошёл "
                f"{direction} сам и получил {r}R.")
    return ""


def zapisat_vyvod_pare(ceh: str, slot: str, vyvod: str,
                       pnl_r=None, limit: int = 10) -> dict:
    """ПИШУЩИЙ КОНЕЦ СЕНСОРА: пара (цех, слот) → носитель → его якоря.
    Магика у сенсора нет и быть не должно — позиций не держит.
    Дыхание тише, чем у трейдера: чужая сделка трогает, но не так,
    как своя (сила вдвое меньше)."""
    if not vyvod:
        return {"дописано": False, "причина": "рутина"}
    try:
        from cartridge_registry import resolve_para
    except Exception as e:
        print(f"[МОСТ] ⚠️  реестр не поднялся ({e})")
        return {"дописано": False, "причина": "нет реестра"}

    n = resolve_para(ceh, slot)
    if not n:
        return {"дописано": False, "причина": f"слот {ceh}/{slot} пуст"}

    d = _dvizhok(n["папка"])
    if d is None:
        return {"дописано": False, "причина": "движок не поднялся"}

    try:
        if pnl_r is not None:
            sila = min(1.0, abs(float(pnl_r)) / 6.0)   # чужая сделка — тише
            tonus = ("минус" if "ОШИБКА" in vyvod or "ПРОСПАЛ" in vyvod
                     else "плюс")
            d.vdoh("работа", sila=sila, svezhest=1.0, tonus=tonus)
            d.sохранить()
    except Exception as e:
        print(f"[МОСТ] ⚠️  вдох не прошёл ({e})")

    try:
        res = d.dopisat_vyvod(vyvod, limit=limit)
    except AttributeError:
        return {"дописано": False, "причина": "нет руки опыта"}

    if res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']} ({slot}): «{vyvod[:60]}...»")
    return res'''

# ── рубильник UCHIT ─────────────────────────────────────────────
UCHIT_OLD = "KRAYNOST_R = 2.0"
UCHIT_NEW = '''KRAYNOST_R = 2.0


# ── РУБИЛЬНИК УЧЁБЫ, ОДИН НА ВСЕХ ───────────────────────────  # {M}
# Стерильность тестера глушила только запись ТРЕЙДЕРОВ (подменой
# zapisat_vyvod). Сенсоры пишут другой рукой (zapisat_vyvod_pare) и шли бы
# МИМО — стерильный бэктест калечил бы Веру с Моржом. Один флаг на всё.
UCHIT = True


def _pisat_mozhno() -> bool:
    """Разрешена ли запись в паспорт живого жителя (учебный прогон/реал)."""
    return bool(UCHIT)'''.replace("{M}", MARKER)

GATE_TRADER_OLD = '''    if not vyvod:
        return {"дописано": False, "причина": "рутина (в опыт не идёт)"}
    try:
        from cartridge_registry import resolve_by_magic'''
GATE_TRADER_NEW = '''    if not vyvod:
        return {"дописано": False, "причина": "рутина (в опыт не идёт)"}
    if not _pisat_mozhno():   # {M}: рубильник учёбы
        return {"дописано": False, "причина": "стерильный прогон"}
    try:
        from cartridge_registry import resolve_by_magic'''.replace("{M}", MARKER)

GATE_SENSOR_OLD = '''    if not vyvod:
        return {"дописано": False, "причина": "рутина"}
    try:
        from cartridge_registry import resolve_para'''
GATE_SENSOR_NEW = '''    if not vyvod:
        return {"дописано": False, "причина": "рутина"}
    if not _pisat_mozhno():   # {M}: рубильник учёбы
        return {"дописано": False, "причина": "стерильный прогон"}
    try:
        from cartridge_registry import resolve_para'''.replace("{M}", MARKER)

# ── hooks: слепок стола в позицию ───────────────────────────────
HOOKS_POS_OLD = '''            "entry_bias": chain.get("market_data", {}).get("global_bias"),
            "pnl":       None,
        })'''
HOOKS_POS_NEW = '''            "entry_bias": chain.get("market_data", {}).get("global_bias"),
            # {M}: СЛЕПОК СТОЛА — показания всех четырёх сенсоров на баре
            # ВХОДА, целиком. Стол перетирается каждый бар: судить сенсора
            # по чужому бару было бы клеветой. Это их опыт — слово, которое
            # рынок потом либо подтвердил, либо нет.
            "стол_входа": {
                k: dict(tstate.get(k, {}) or {})
                for k in ("iskra", "morj", "panic", "hans")
            },
            "pnl":       None,
        })'''.replace("{M}", MARKER)

# ── hooks: суд четверых ─────────────────────────────────────────
HOOKS_JUDGE_OLD = '''def _judge_iskra_by_result(pos: dict, pnl_r):
    """
    СУД ИСКРЫ — не построена в этом городе.

    В старом мире (-2) плюсовая сделка сдвигала ДНК Искры через
    studio.grondheim_memory.sync_to_dna. Это и есть тот самый
    маятник состояния, который Чертёж Единицы (Гл.4.2) прямо
    называет НЕ-опытом: "качание состояния, не вывод — обучение
    первого уровня, без понимания". Нога Опыта Стола Трейдера
    (Чертёж, Гл.5.2/9 — "долг: амнезия у штурвала") строится
    отдельно, по-новому, не восстановлением этого маятника.
    Честный no-op — не зовёт то, чего на диске больше нет.
    """
    return
'''

HOOKS_JUDGE_NEW = '''def _judge_iskra_by_result(pos: dict, pnl_r):
    """
    СУД СЕНСОРОВ — их нога Опыта. Построена.   # {M}

    (Имя историческое: судит теперь ВСЕХ ЧЕТВЕРЫХ — Веру, Моржа, Паникёра,
    Ганса. Зовётся из _settle_positions на каждой закрытой сделке; сигнатуру
    ради имени не ломаем.)

    Слово Шефа: опыт сенсора — это КАК ОН РАБОТАЕТ НАД СВОИМИ ОШИБКАМИ.
    Он не теряет денег — он промахивается СЛОВОМ. Судит его исход, до
    которого он сам не дожил: сделка трейдера, случившаяся после его слова.

    Судит КОД, не LLM (числа не галлюцинируют). «Звал» — значит показание
    тянуло В СТОРОНУ сделки (компас Веры, сторона фрактала Ганса, фаза
    толпы). Молчал и сделка в минус — не его промах, в опыт не идёт.

    Это НЕ старый sync_to_dna: тот качал ДНК за «хорошую работу» — маятник,
    который Чертёж (Гл.4.2) зовёт НЕ-опытом. Здесь — вывод СЛОВАМИ, который
    сенсор прочтёт перед следующим баром и сможет с ним спорить.

    Упадёт — торговый цикл цел, сделка в журнале записана.
    """
    stol = pos.get("стол_входа") or {}
    if not stol or pnl_r is None:
        return
    try:
        import sys as _s
        from pathlib import Path as _P
        _b = str(_P(__file__).resolve().parent)
        if _b not in _s.path:
            _s.path.insert(0, _b)
        from nositel import SENSOR_SLOTS, sudit_sensora, zapisat_vyvod_pare

        direction = pos.get("direction")
        bar = pos.get("opened_at") or ""

        # В якорь сенсора должен лечь ЧЕЛОВЕК, а не роль: Вера помнит, что
        # вошёл ИЛЬЯ, а не «Avanturist». Мост уже умеет: magic → носитель.
        trader = pos.get("trader") or ""
        try:
            from cartridge_registry import resolve_by_magic
            _t = resolve_by_magic(pos.get("magic"))
            if _t and _t.get("имя"):
                trader = _t["имя"]
        except Exception:
            pass

        for key, slot in SENSOR_SLOTS.items():
            pokazanie = stol.get(key) or {}
            vyvod = sudit_sensora(key, pokazanie, direction, pnl_r, trader, bar)
            if vyvod:
                zapisat_vyvod_pare("торговый_хаос", slot, vyvod, pnl_r=pnl_r)
    except Exception as e:
        print(f"[СУД] ⚠️  суд сенсоров не сработал ({e}) — сделка в журнале цела")
    return
'''.replace("{M}", MARKER)

# ── tester: рубильник ───────────────────────────────────────────
TESTER_OLD = """    if _nos is not None and not learn:
        _nos.zapisat_vyvod = (lambda *a, **k:
                              {'дописано': False, 'причина': 'стерильный прогон'})"""
TESTER_NEW = """    if _nos is not None:
        # {M}: ОДИН рубильник на всю запись в живых жителей — трейдеры И
        # сенсоры. Раньше глушился только zapisat_vyvod, и сенсоры писали бы
        # МИМО стерильности, калеча Веру с Моржом на обычном бэктесте.
        _nos.UCHIT = bool(learn)
    if _nos is not None and not learn:
        _nos.zapisat_vyvod = (lambda *a, **k:
                              {'дописано': False, 'причина': 'стерильный прогон'})""".replace("{M}", MARKER)


def die(m, c=1):
    print("✗ " + m)
    return c


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ СУД СЕНСОРОВ — работа над своими ошибками ═══")

    for p in (NOSITEL, HOOKS, TESTER):
        if not p.exists():
            return die(f"не нашёл {p} — ты в КОРНЕ репы?")

    # ── nositel ──────────────────────────────────────────────
    n = NOSITEL.read_text(encoding="utf-8")
    changed = False

    if "def sudit_sensora" in n:
        print("✓ nositel: суд сенсора УЖЕ ЕСТЬ — не дублирую "
              "(два определения = второй источник правды)")
    else:
        n = n.rstrip() + "\n\n\n" + SENSOR_SECTION.strip() + "\n"
        changed = True
        print("✓ nositel: вшита секция суда сенсоров (_zval, sudit_sensora, "
              "zapisat_vyvod_pare)")

    if "UCHIT" in n and "_pisat_mozhno" in n:
        print("✓ nositel: рубильник UCHIT уже стоит")
    else:
        if UCHIT_OLD not in n:
            return die("nositel: не нашёл KRAYNOST_R — сверь глазами.", 3)
        n = n.replace(UCHIT_OLD, UCHIT_NEW, 1)
        for old, new, what in ((GATE_TRADER_OLD, GATE_TRADER_NEW, "трейдера"),
                               (GATE_SENSOR_OLD, GATE_SENSOR_NEW, "сенсора")):
            if old in n:
                n = n.replace(old, new, 1)
            else:
                print(f"  ⚠ не нашёл вход в запись {what} — рубильник туда не встал")
        changed = True
        print("✓ nositel: рубильник UCHIT гасит запись и трейдеров, и сенсоров")

    if changed:
        bak = NOSITEL.with_suffix(".py.bak_sud")
        if not bak.exists():
            bak.write_text(NOSITEL.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  • бэкап: {bak}")
        NOSITEL.write_text(n, encoding="utf-8")

    # ── hooks ────────────────────────────────────────────────
    h = HOOKS.read_text(encoding="utf-8")
    if MARKER in h:
        print("✓ hooks уже пропатчен")
    else:
        for old, what in ((HOOKS_POS_OLD, "сборка позиции (entry_bias)"),
                          (HOOKS_JUDGE_OLD, "заглушка _judge_iskra_by_result")):
            if old not in h:
                return die(f"hooks: не нашёл «{what}». Сверь глазами.", 4)
        bak = HOOKS.with_suffix(".py.bak_sud")
        if not bak.exists():
            bak.write_text(h, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        h = h.replace(HOOKS_POS_OLD, HOOKS_POS_NEW, 1)
        h = h.replace(HOOKS_JUDGE_OLD, HOOKS_JUDGE_NEW, 1)
        HOOKS.write_text(h, encoding="utf-8")
        print("✓ hooks: слепок стола в позицию + суд четверых на закрытии")

    # ── tester ───────────────────────────────────────────────
    t = TESTER.read_text(encoding="utf-8")
    if MARKER in t:
        print("✓ tester уже пропатчен")
    elif TESTER_OLD not in t:
        print("⚠ tester: не нашёл блок стерильности — сначала "
              "patch_tester_sterile_opyt_v1.py! Иначе сенсоры будут писать "
              "в живых жителей даже на стерильном прогоне.")
    else:
        bak = TESTER.with_suffix(".py.bak_sud")
        if not bak.exists():
            bak.write_text(t, encoding="utf-8")
        TESTER.write_text(t.replace(TESTER_OLD, TESTER_NEW, 1), encoding="utf-8")
        print("✓ tester: UCHIT гасит запись и трейдеров, и сенсоров")

    print("───")
    print("КОЛЬЦО ЗАМКНУЛОСЬ НА СЕМИ: 3 трейдера (рынок судит деньгами)")
    print("+ 4 сенсора (рынок судит словом).")
    print("\nТеперь жми 🎓 УЧИТЬ и гони тестер — ловить 20-30.")
    print("Жди в логе:  [МОСТ] 🧠 ОПЫТ → Вера (A01): «МОЯ ОШИБКА...»")
    return 0


if __name__ == "__main__":
    sys.exit(main())
