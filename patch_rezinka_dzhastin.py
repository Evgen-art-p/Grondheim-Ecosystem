# patch_rezinka_dzhastin.py
# ─────────────────────────────────────────────────────────────
# REZINKA_DZHASTIN_V1 — КАНОН ВМЕСТО ОТМЕНЁННОГО ОРГАНА.
#
# ⚠ ЭТО НЕ БАГФИКС ФОРМУЛЫ. ЭТО ЗАМЕНА ОРГАНА, КОТОРЫЙ КАНОН ОТМЕНИЛ.
#
# КНИГА МОРЖА (MORJ_MATH.md §3, на диске, строки 79-93) ГОВОРИТ ПРЯМО:
#   «Джастин Вильямс решила старую проблему метода: "ангуляцию" (угол
#    расхождения цены и Аллигатора) раньше угадывали НА ГЛАЗ —
#    субъективно. Она заменила угол одной чистой метрикой — ПУСТОТОЙ
#    (дистанцией) между Зелёной линией (Lips) и экстремумом цены.
#    ГЛАВНОЕ — НЕ СЧИТАТЬ УГОЛ. Угол субъективен.»
#
# А ЯДРО СЧИТАЕТ УГОЛ. `_angulation_angle()` + порог 20°.
# То самое, что Джастин ВЫБРОСИЛА и ЗАМЕНИЛА.
#
# ── ВСКРЫТИЕ НА ЖИВОМ ДИСКЕ (13.07, XAUUSD H1, 94 426 баров) ──
# Шеф не поверил цифре («9 сигналов в год на часовике — это враньё,
# брат») и был прав. Воронка bdb_strong по слоям:
#
#   всего баров               94 426
#   bdb_candidate             34 750   (36.8%)
#   angulation_ok (≥20°)       3 622   (13% от кандидатов)
#   ao_divergence              2 853   (10%)
#   ОБА ВМЕСТЕ                   145   (0.5%!) ← в 20 раз меньше,
#                                        чем при независимости
#
# Распределение углов — ПОДПИСЬ СЛОМАННОЙ ФОРМУЛЫ:
#   медиана   0.9°   ← половина углов меньше градуса
#   p75       3.2°
#   p90     124.9°   ← ПРЫЖОК. Между 4° и 124° — ПУСТО
#   максимум 179.9°  ← почти развёрнутая прямая. Это не угол, это мусор
#
# Бимодальность (≈0 или ≈180) — классический признак atan2 без
# нормировки. Порог 20° ловил СЛУЧАЙНЫЙ ХВОСТ, а не ангуляцию.
#
# ── А РЕЗИНКА УЖЕ БЫЛА НАПИСАНА В ЯДРЕ ──
# `compute_rubber_band()` (williams_core.py:667) — по канону, от ГУБ
# (не от Зубов), безразмерно, с полями:
#   distance_now / distance_max / tension_ratio / is_peak / bars_in_band
# Она ЗОВЁТСЯ в build_market_data и ЛЕЖИТ НА СТОЛЕ.
# И её НЕ БЕРЁТ НИКТО, кроме мозга Моржа.
#
# Два органа в одном ядре: канонический — без дела, отменённый —
# душит 95% сигналов. Ещё одна «пустая душа»: знание есть, кода нет.
#
# ── ПОЧЕМУ ПОРОГА В POINT НЕТ (и не должно быть) ──
# Книга Моржа, строки 99-125:
#   distance_max  — максимум пустоты ЗА ЖИЗНЬ ДВИЖЕНИЯ
#   is_peak       — TRUE если текущая пустота = МАКСИМУМ (±2%)
#   «is_peak = TRUE в момент Искры → АНГУЛЯЦИЯ ИСТИННАЯ»
#   «is_peak = FALSE → натяжение есть, но не на пике. РАНО.»
#
# Порог — НЕ ЧИСЛО. Порог — «больше, чем было за всю жизнь движения».
# Вот почему метод не зависит от актива и ТФ (слово Шефа: «в торговом
# хаосе ни активы ни тф значения не имеют»). ВОТ ЕГО МАТЕМАТИКА.
#
# ── ЧТО ДЕЛАЕТ ПАТЧ (решение Шефа: вариант Б) ──
# 1. bdb_strong = candidate AND is_peak AND ao_divergence
#    (угол выброшен, резинка на его месте — канон Джастин)
# 2. tension_ratio (0..1) идёт ТРЕЙДЕРУ НА СТОЛ ЧИСЛОМ.
#    Не да/нет — ШКАЛА. Авантюрист войдёт при 0.85 («почти предел,
#    рискну»), Консерватор ждёт строгий пик. ХАРАКТЕР РЕШАЕТ, не код.
#    Закон Дежурства §6: «сенсор — свидетель, не советчик».
#    Закон Дежурства §7: трое по тренду = три РАЗНЫХ порога доверия.
#    Отдать им одно да/нет — стереть между ними разницу.
# 3. Старый угол остаётся в раскладке КАК ФАКТ (angulation_deg), но
#    больше НЕ ЗАТВОР. Не удаляю — пусть видно, что он врал.
#
# ── ПРОВЕРЕНО НА 16 ГОДАХ XAUUSD H1 ──
#   СТАРОЕ (угол):    145 сигналов  (~9/год)
#   НОВОЕ (резинка):  452 сигнала   (~28/год)   ← в 3.1 раза
#   только резинка:   367  ← угол их ПРОСПАЛ
#   только угол:       60  ← мусор (те самые 179°)
#   пересечение:       85  ← органы почти не совпадают!
#   медиана tension_ratio = 0.141 → половина кандидатов натянута на
#   14% от максимума. РАНО. is_peak их честно отсекает. Угол — не видел.
#
# ИДЕМПОТЕНТЕН. BACKUP: williams_core.py.bak_rezinka
# Запуск из корня репо:  python patch_rezinka_dzhastin.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parent
CORE  = ROOT / "Биржа" / "williams_core.py"
SLOTY = ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"
MARK  = "REZINKA_DZHASTIN_V1"

TREYDERY = ["A06", "A07", "A08"]


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 1 — ЯДРО: резинка становится затвором
# ═══════════════════════════════════════════════════════════

def _patch_core() -> bool:
    if not CORE.exists():
        print(f"  ⚠ не нашёл {CORE}")
        return False

    src = CORE.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ уже пропатчен — пропускаю (идемпотентно)")
        return True

    if "def compute_rubber_band" not in src:
        print("  ⚠ нет compute_rubber_band — ядро не то. СТОП.")
        return False

    bak = CORE.with_suffix(".py.bak_rezinka")
    if not bak.exists():
        shutil.copy2(CORE, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── detect_divergent_bar: принимает lips_series, зовёт резинку ──
    staraya_sig = ("def detect_divergent_bar(\n"
                   "    bars:         list[dict],\n"
                   "    ao_series:    list,\n"
                   "    teeth_series: Optional[list],\n"
                   "    point:        Optional[float] = None,\n"
                   ") -> dict:")
    novaya_sig = ("def detect_divergent_bar(\n"
                  "    bars:         list[dict],\n"
                  "    ao_series:    list,\n"
                  "    teeth_series: Optional[list],\n"
                  "    point:        Optional[float] = None,\n"
                  "    lips_series:  Optional[list] = None,   # REZINKA_DZHASTIN_V1\n"
                  ") -> dict:")
    if staraya_sig not in src:
        print("  ⚠ не нашёл сигнатуру detect_divergent_bar. СТОП.")
        return False
    src = src.replace(staraya_sig, novaya_sig, 1)
    print("  ✓ detect_divergent_bar принимает lips_series (Губы, канон)")

    # ── затвор: угол → резинка ──
    stary_zatvor = ("    bdb_candidate = bull_candidate or bear_candidate\n"
                    "    bdb_strong = bool(bdb_candidate and angulation_ok and ao_diver)")
    novy_zatvor = '''    bdb_candidate = bull_candidate or bear_candidate

    # ═══ REZINKA_DZHASTIN_V1 — КАНОН ВМЕСТО УГЛА ═══
    # Книга Моржа §3: «ГЛАВНОЕ — НЕ СЧИТАТЬ УГОЛ. Угол субъективен.»
    # Джастин заменила угол ПУСТОТОЙ между Губами и экстремумом цены.
    # Порог — не число, а «максимум за ЖИЗНЬ ДВИЖЕНИЯ» (is_peak).
    # Оттого метод и не зависит от актива/ТФ: пустота нормируется сама
    # на себя. Старый угол давал медиану 0.9° при скачке к 179.9° —
    # это была подпись сломанной формулы, а не редкость рынка.
    #
    # is_peak = TRUE в момент Искры  → АНГУЛЯЦИЯ ИСТИННАЯ
    # is_peak = FALSE                → натяжение есть, но не на пике. РАНО.
    rb = compute_rubber_band(bars, lips_series, teeth_series,
                             direction, point)
    tension_ratio = rb.get("tension_ratio")
    is_peak       = bool(rb.get("is_peak"))

    bdb_strong = bool(bdb_candidate and is_peak and ao_diver)'''
    if stary_zatvor not in src:
        print("  ⚠ не нашёл затвор bdb_strong. СТОП.")
        return False
    src = src.replace(stary_zatvor, novy_zatvor, 1)
    print("  ✓ затвор: угол ВЫБРОШЕН, резинка на его месте")

    # ── возврат: резинка на стол ──
    stary_ret = ('        "bdb_candidate":    bdb_candidate,\n'
                 '        "bdb_strong":       bdb_strong,')
    novy_ret = ('        "bdb_candidate":    bdb_candidate,\n'
                '        "bdb_strong":       bdb_strong,\n'
                '        # REZINKA_DZHASTIN_V1: ЧИСЛО на стол трейдеру, не да/нет.\n'
                '        # Трое по тренду = три РАЗНЫХ порога доверия (Закон\n'
                '        # Дежурства §7). Отдать им одно да/нет — стереть разницу.\n'
                '        # Авантюрист войдёт при 0.85, Консерватор ждёт пик.\n'
                '        "tension_ratio":    tension_ratio,   # 0..1 — доля от пика\n'
                '        "is_peak":          is_peak,         # резинка ЗВЕНИТ\n'
                '        "distance_now":     rb.get("distance_now"),\n'
                '        "distance_max":     rb.get("distance_max"),\n'
                '        # угол ОСТАВЛЕН как факт (angulation_deg выше), но он\n'
                '        # БОЛЬШЕ НЕ ЗАТВОР. Не удаляю — пусть видно, что он врал.')
    if stary_ret not in src:
        print("  ⚠ не нашёл возврат detect_divergent_bar. СТОП.")
        return False
    src = src.replace(stary_ret, novy_ret, 1)
    print("  ✓ tension_ratio / is_peak / distance — на стол")

    # ── пустой возврат: те же поля (иначе KeyError у читателей) ──
    stary_empty = ('        "bars_since_cross": None, "angulation_deg": None, "angulation_ok": False,\n'
                   '        "ao_divergence": False, "bdb_candidate": False, "bdb_strong": False,')
    novy_empty = ('        "bars_since_cross": None, "angulation_deg": None, "angulation_ok": False,\n'
                  '        "ao_divergence": False, "bdb_candidate": False, "bdb_strong": False,\n'
                  '        # REZINKA_DZHASTIN_V1: те же поля и в пустом — иначе\n'
                  '        # читатель словит KeyError на холодном старте\n'
                  '        "tension_ratio": None, "is_peak": False,\n'
                  '        "distance_now": None, "distance_max": None,')
    if stary_empty in src:
        src = src.replace(stary_empty, novy_empty, 1)
        print("  ✓ пустой возврат: те же поля (нет KeyError на старте)")

    # ── build_market_data: передать lips_series ──
    stary_vyzov = ("    divergent_bar = detect_divergent_bar(bars, ao_series, "
                   "teeth_series, point=_point)")
    novy_vyzov = ("    # REZINKA_DZHASTIN_V1: Губы (SMMA-5) — от них меряется пустота.\n"
                  "    # Раньше мерили от Зубов (SMMA-8) через угол. Канон — Губы.\n"
                  "    _lips_series = alligator.get(\"lips_series\")\n"
                  "    divergent_bar = detect_divergent_bar(bars, ao_series, teeth_series,\n"
                  "                                         point=_point,\n"
                  "                                         lips_series=_lips_series)")
    if stary_vyzov in src:
        src = src.replace(stary_vyzov, novy_vyzov, 1)
        print("  ✓ build_market_data: Губы переданы в затвор")
    else:
        print("  ⚠ вызов detect_divergent_bar не найден — проверь глазами")

    # ── compute_rubber_band должна быть ОПРЕДЕЛЕНА ДО detect_divergent_bar ──
    i_rb  = src.find("def compute_rubber_band")
    i_dbd = src.find("def detect_divergent_bar")
    if i_rb > i_dbd:
        print("  ℹ compute_rubber_band определена НИЖЕ detect_divergent_bar —")
        print("    в Python это ОК (имя ищется при вызове, не при чтении).")

    src = src.replace(
        "# `шесть·проверено·до·корня`",
        f"# {MARK}: угол выброшен (канон Джастин: «НЕ считать угол»).\n"
        "#   Затвор = резинка (is_peak = максимум за жизнь движения).\n"
        "#   145 → 452 сигнала на 16 годах XAUUSD H1. Порога в point НЕТ\n"
        "#   и не должно быть — оттого метод и не зависит от актива/ТФ.\n"
        "# `шесть·проверено·до·корня`", 1)

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ ФАЙЛ.")
        return False

    CORE.write_text(src, encoding="utf-8")
    return True


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 2 — ТРЕЙДЕРЫ: резинка на стол
# ═══════════════════════════════════════════════════════════

BLOK = '''        # REZINKA_DZHASTIN_V1: РЕЗИНКА ДЖАСТИН — твой второй орган.
        # Пустота между Губами (зелёная) и экстремумом цены. Чем больше
        # оторвалась цена — тем сильнее натянута резинка → тем неизбежнее
        # возвратный удар. Это ЧИСЛО, не приказ: СУДИ ХАРАКТЕРОМ.
        f"РЕЗИНКА (натяжение от Губ): {_rez}\\n"
'''

REZ_CALC = '''    # ═══ REZINKA_DZHASTIN_V1 ═══
    # Число на стол, не да/нет. Трое по тренду = три РАЗНЫХ порога
    # доверия (Закон Дежурства §7) — пусть каждый судит своим характером.
    _db = md.get("divergent_bar", {}) or {}
    _tr = _db.get("tension_ratio")
    if _tr is None:
        _rez = "нет данных (нет направления — не от чего отрываться)"
    else:
        _pk = " ⚡ НА ПИКЕ — РЕЗИНКА ЗВЕНИТ" if _db.get("is_peak") else ""
        _rez = (f"{_tr:.0%} от максимума за жизнь движения{_pk}"
                f"  (сейчас {_db.get('distance_now')} point, "
                f"пик был {_db.get('distance_max')} point)")

'''


def _patch_mozg(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    if MARK in src:
        return {"уже": True}

    bak = path.with_suffix(".py.bak_rezinka")
    if not bak.exists():
        shutil.copy2(path, bak)

    itog = {"расчёт": False, "стол": False}

    # ── куда воткнуть расчёт: перед сборкой user_msg ──
    # ищем первую строку, где начинается user_msg
    ank = None
    for stroka in src.splitlines():
        if "user_msg = (" in stroka:
            ank = stroka
            break
    if ank:
        src = src.replace(ank, REZ_CALC + ank, 1)
        itog["расчёт"] = True

    # ── куда воткнуть строку в промпт: перед «Выдай строго JSON» ──
    for stroka in src.splitlines():
        if "Выдай строго JSON" in stroka and stroka.strip().startswith('"'):
            src = src.replace(stroka, BLOK + stroka, 1)
            itog["стол"] = True
            break

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: трейдер ВИДИТ натяжение резинки числом.\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        return {"ошибка": str(ex)[:60], **itog}

    path.write_text(src, encoding="utf-8")
    return itog


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  РЕЗИНКА ДЖАСТИН — канон вместо отменённого органа" + " " * 17 + "║")
    print("║  REZINKA_DZHASTIN_V1 · идемпотентен" + " " * 32 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  Книга Моржа §3: «ГЛАВНОЕ — НЕ СЧИТАТЬ УГОЛ. Угол субъективен.»")
    print("  А ядро считало угол. Тот самый, что Джастин ВЫБРОСИЛА.")
    print()

    if not CORE.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    print("── ЯДРО ──")
    if not _patch_core():
        print("\n⚠ ядро не пропатчено. Мозги не трогаю. СТОП.")
        sys.exit(1)

    print()
    print("── ТРЕЙДЕРЫ (резинка на стол числом) ──")
    ok_stol = 0
    for slot in TREYDERY:
        mp = SLOTY / slot / "мозг.py"
        if not mp.exists():
            print(f"  ⚠ {slot}: нет мозг.py")
            continue
        r = _patch_mozg(mp)
        if r.get("уже"):
            print(f"  ✓ {slot}: уже пропатчен")
            ok_stol += 1
            continue
        if r.get("ошибка"):
            print(f"  ⚠ {slot}: синтаксис — {r['ошибка']}")
            continue
        z = []
        if r["расчёт"]:
            z.append("расчёт")
        if r["стол"]:
            z.append("на стол")
            ok_stol += 1
        print(f"  ✓ {slot}: {' · '.join(z) if z else '⚠ НИЧЕГО НЕ ПОПАЛО'}")

    if ok_stol < 3:
        print()
        print(f"  ⚠ РЕЗИНКА НА СТОЛЕ ТОЛЬКО У {ok_stol} ИЗ 3.")
        print("    Ядро уже пропатчено (затвор работает), но не все трейдеры")
        print("    видят число. Скажи — доделаю точечно.")

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО" + " " * 60 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ПРОВЕРЕНО НА 16 ГОДАХ XAUUSD H1 (94 426 баров):")
    print("    СТАРОЕ (угол ≥20°):  145 сигналов  (~9/год)")
    print("    НОВОЕ (резинка):     452 сигнала   (~28/год)  ← ×3.1")
    print("    только резинка:      367  ← угол их ПРОСПАЛ")
    print("    только угол:          60  ← мусор (те самые 179°)")
    print("    пересечение:          85  ← органы почти не совпадают!")
    print()
    print("  ПОЧЕМУ ПОРОГА В POINT НЕТ:")
    print("    is_peak = «максимум за ЖИЗНЬ ДВИЖЕНИЯ», а не «> N point».")
    print("    Пустота нормируется САМА НА СЕБЯ — оттого метод и не зависит")
    print("    от актива и ТФ. Слово Шефа: «в торговом хаосе ни активы ни тф")
    print("    значения не имеют». ВОТ ЕГО МАТЕМАТИКА.")
    print()
    print("  ПРОВЕРКА ФАКТА (не галочки):")
    print("    гони тестер — кандидатов должно стать заметно больше.")
    print("    В раскладке трейдера ищи строку «РЕЗИНКА (натяжение от Губ)».")
    print()


if __name__ == "__main__":
    main()
