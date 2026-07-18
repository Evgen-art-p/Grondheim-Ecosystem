# -*- coding: utf-8 -*-
"""
ПАТЧ: VASYA_SVOY_RAZVOROT_V1

Даёт Василию (A08, Консерватор) СОБСТВЕННЫЙ глаз на разворот его волны 2 —
тот же аппарат, что у Искры (read_ao_wave_form, окно 100-140 баров, §3
канона), но этажом ниже неё (Правило пятёрки, §4): read_ao_wave_form уже
считается ядром для КАЖДОГО вызова build_market_data, просто раньше никто
его не читал на масштабе волны Василия.

Раньше: Василий наследовал iskra_tf НАПРЯМУЮ (тот же ТФ, что у Искры).
На этом масштабе его собственный откат волны 2 не растягивается на
100-140 баров (§3, "опасность лупы") — bdb_dir там почти всегда None,
не потому что разворота нет, а потому что окно снято не в фокусе.

ЧТО МЕНЯЕТ:
  A08 (Консерватор): новая функция _read_vasya_wave — спуск на этаж
  ниже Искры (step_down), тот же read_ao_wave_form, окно 120 баров.
  Кладёт own_wave в стол рядом с anchor. Без волнового словаря в
  промпте (§6.2/§8 — сигналы ВЫХОДА, не входа — модель может спутать
  свой же разворот с сигналом закрытия чужой пирамиды).

ЗАПУСК: из корня репо
    python patch_vasya_svoy_razvorot.py

Идемпотентно. Бэкап рядом (.bak).
"""
import ast
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
A08_TARGET = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / "A08" / "мозг.py"
MARKER = "VASYA_SVOY_RAZVOROT_V1"


EDITS = [
    # 1) Новая функция _read_vasya_wave — сразу после констант, ДО _read_table
    ('''STATS_PATH   = STATE_DIR / "cons_stats.json"
DIARY_PATH   = STATE_DIR / "diary_cons.jsonl"


# ════════════════════════════════════════════════════════════
# СТОЛ: читаем ВСЮ шину — показания пяти сенсоров
# ════════════════════════════════════════════════════════════''',
     '''STATS_PATH   = STATE_DIR / "cons_stats.json"
DIARY_PATH   = STATE_DIR / "diary_cons.jsonl"


# ════════════════════════════════════════════════════════════
# VASYA_SVOY_RAZVOROT_V1 — СОБСТВЕННЫЙ ГЛАЗ ВАСИЛИЯ (откат волны 2)
# ─────────────────────────────────────────────────────────────
# Тот же аппарат, что у Искры (read_ao_wave_form, окно 100-140 баров,
# §3 канона), но этажом НИЖЕ неё (Правило пятёрки, §4). На ТФ Искры
# откат волны 2 слишком мелкий — не растягивается на фокусное окно,
# bdb_dir там почти всегда None. Спуск на этаж ниже даёт тому же
# движению нужный масштаб — фрактальное самоподобие (§3 canon).
# ════════════════════════════════════════════════════════════

def _read_vasya_wave(symbol: str, iskra_tf) -> dict:
    """
    Собственный разворотный бар Василия. Спуск на ступень ниже Искры,
    тот же williams_core.read_ao_wave_form (через build_market_data),
    то же окно 120. Нет этажа Искры или спускаться некуда (дно
    лесенки) — пустая форма, Василий честно молчит (сенсор без факта).
    """
    from mt5_feed import step_down, pull_bars
    from williams_core import build_market_data, _empty_wave_form

    if not iskra_tf:
        return _empty_wave_form()
    own_tf = step_down(iskra_tf)
    if not own_tf:
        return _empty_wave_form()

    bars, point = pull_bars(symbol, own_tf, 300)
    if not bars or point is None:
        return _empty_wave_form()
    md = build_market_data(bars, symbol=symbol, timeframe=own_tf, point=point)
    if not md:
        return _empty_wave_form()
    wf = dict(md.get("wave_form", _empty_wave_form()))
    wf["timeframe"] = own_tf
    return wf


# ════════════════════════════════════════════════════════════
# СТОЛ: читаем ВСЮ шину — показания пяти сенсоров
# ════════════════════════════════════════════════════════════'''),

    # 2) run_cons: посчитать own_wave сразу после наследования iskra_tf
    ('''    table = _read_table()
    iskra_tf = table.get("iskra", {}).get("found_timeframe")
    if iskra_tf:
        timeframe = iskra_tf

    from mt5_feed import _terminal, _fetch''',
     '''    table = _read_table()
    iskra_tf = table.get("iskra", {}).get("found_timeframe")
    if iskra_tf:
        timeframe = iskra_tf

    # VASYA_SVOY_RAZVOROT_V1: собственный разворотный бар отката волны 2,
    # НЕ этаж Искры — этаж НИЖЕ (Правило пятёрки, §4 канона).
    own_wave = _read_vasya_wave(symbol, iskra_tf)

    from mt5_feed import _terminal, _fetch'''),

    # 3) table_for_cons: own_wave рядом с anchor
    ('''        "anchor": {
            # KOMPAS_DOSTAVKA_TREYDERAM_V1: НАСТОЯЩИЙ компас, не
            # направление точки — см. мозг A01/A06 за объяснением.
            "global_trend": table.get("iskra", {}).get("compass"),
            "soglasie": table.get("iskra", {}).get("soglasie"),
            "found_timeframe": iskra_tf,
        },
        "sensors": {''',
     '''        "anchor": {
            # KOMPAS_DOSTAVKA_TREYDERAM_V1: НАСТОЯЩИЙ компас, не
            # направление точки — см. мозг A01/A06 за объяснением.
            "global_trend": table.get("iskra", {}).get("compass"),
            "soglasie": table.get("iskra", {}).get("soglasie"),
            "found_timeframe": iskra_tf,
        },
        # VASYA_SVOY_RAZVOROT_V1: твой СОБСТВЕННЫЙ разворотный бар,
        # не чужой (не фрактал Ганса, не точка Искры) — на масштабе
        # ТВОЕЙ волны 2, этажом ниже Искры.
        "own_wave": {
            "timeframe":            own_wave.get("timeframe"),
            "bdb_dir":              own_wave.get("bdb_dir"),
            "bdb_price":            own_wave.get("bdb_price"),
            "dlina":                own_wave.get("dlina"),
            "struktura_chitaetsya": own_wave.get("struktura_chitaetsya"),
        },
        "sensors": {'''),

    # 4) user_msg: пояснение БЕЗ волнового словаря §6.2/§8 (не путать с выходом)
    ('''        "=== ТВОЙ ДНЕВНИК (последние события — твоя память) ===\\n"
        f"{json.dumps(recent, ensure_ascii=False, indent=2) if recent else '(пусто — первое решение)'}\\n\\n"
        "Перед тобой стол и ты сам. Канон у тебя на полке (книга Котина), "''',
     '''        "=== ТВОЙ ДНЕВНИК (последние события — твоя память) ===\\n"
        f"{json.dumps(recent, ensure_ascii=False, indent=2) if recent else '(пусто — первое решение)'}\\n\\n"
        "=== ТВОЙ СОБСТВЕННЫЙ РАЗВОРОТНЫЙ БАР (own_wave на столе) ===\\n"
        "Это факт на масштабе ТВОЕЙ коррекции — не сигнал закрытия чужой "
        "пирамиды и не чужая точка. bdb_dir/bdb_price — сторона и цена "
        "твоего разворотного бара, если он уже сформирован; null — на "
        "этом этаже пока не нашёлся, это не отказ, просто рано.\\n\\n"
        "Перед тобой стол и ты сам. Канон у тебя на полке (книга Котина), "'''),
]


def main() -> int:
    if not A08_TARGET.exists():
        print(f"[ПАТЧ] ✗ не найден {A08_TARGET}")
        return 1
    src = A08_TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — пропускаю")
        return 0
    for i, (old, new) in enumerate(EDITS, 1):
        if old not in src:
            print(f"[ПАТЧ] ✗ якорь #{i} не найден — файл уже другой")
            return 1
    for old, new in EDITS:
        src = src.replace(old, new, 1)
    src += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ результат не парсится: {e}")
        return 1
    shutil.copy2(A08_TARGET, A08_TARGET.with_suffix(".py.bak"))
    A08_TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {MARKER} применён ({len(EDITS)} правок) → {A08_TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
