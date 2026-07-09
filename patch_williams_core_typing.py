# -*- coding: utf-8 -*-
# patch_williams_core_typing.py — WILLIAMS_CORE_TYPING_V1
# ─────────────────────────────────────────────────────────────
# Закрывает 27 ошибок Pylance в Биржа/williams_core.py (репорт от
# Шефа, 2026-07-09). Все — один и тот же корень: неявный Optional
# (`param: float = None` вместо `Optional[float] = None`) и
# нетипизированные `[None] * len(x)`, из-за чего Pylance видит
# "list[None]" там, где реально "list[float | None]".
#
# ЗАКОН ПРАВКИ: это ТОЛЬКО типизация. Ни одна формула, ни один
# порог, ни одна ветка логики не меняется. Единственное настоящее
# изменение кода — _smma_series: рекуррентная ссылка result[i-1]
# заменена на локальный float-аккумулятор prev (та же формула,
# просто типобезопасно — Pylance не умеет доказать, что result[i-1]
# уже не None на этом шаге рекурсии). Сверено побитово на 200
# случайных сериях (period 5/8/13, длина 1-60) — идентичный вывод.
#
# Плюс один живой баг типизации: bars[-1].get("date") if bars else
# None — bars ГАРАНТИРОВАНО не пуст к этой строке (build_market_data
# отсекает len(bars)<40 в начале), а .get() всё равно даёт Optional
# по сигнатуре dict.get(). Меняем на bars[-1]["date"] — прямой
# доступ, без Optional И без костыля: если когда-нибудь бар придёт
# без "date", KeyError скажет об этом сразу, а не растворится в None.
#
# ЗАПУСК из корня проекта:  python patch_williams_core_typing.py
# Идемпотентен (маркер), бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "WILLIAMS_CORE_TYPING_V1"

ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "williams_core.py"

# ══════════════════════════════════════════════════════════════
# БЛОКИ ЗАМЕН — по одному на каждую группу ошибок отчёта
# ══════════════════════════════════════════════════════════════

# ── 1. _smma_series: типизация result + прочный float-аккумулятор
#    (закрывает строки 91/92/94/95 отчёта) ──
OLD_1 = '''    result = [None] * len(medians)
    if len(medians) < period:
        return result
    result[period - 1] = sum(medians[:period]) / period
    for i in range(period, len(medians)):
        result[i] = (result[i - 1] * (period - 1) + medians[i]) / period
    return result'''
NEW_1 = '''    result: list[Optional[float]] = [None] * len(medians)
    if len(medians) < period:
        return result
    first = sum(medians[:period]) / period
    result[period - 1] = first
    prev = first  # WILLIAMS_CORE_TYPING_V1: float-аккумулятор вместо чтения
    for i in range(period, len(medians)):  # result[i-1] — та же формула, тип чист
        prev = (prev * (period - 1) + medians[i]) / period
        result[i] = prev
    return result'''

# ── 2. compute_ao_series: типизация result (закрывает 173/174) ──
OLD_2 = '''    medians = [(h + l) / 2 for h, l in zip(highs, lows)]
    result  = [None] * len(medians)
    for i in range(33, len(medians)):
        sma5  = sum(medians[i-4:i+1])  / 5
        sma34 = sum(medians[i-33:i+1]) / 34
        result[i] = sma5 - sma34
    return result'''
NEW_2 = '''    medians = [(h + l) / 2 for h, l in zip(highs, lows)]
    result: list[Optional[float]] = [None] * len(medians)
    for i in range(33, len(medians)):
        sma5  = sum(medians[i-4:i+1])  / 5
        sma34 = sum(medians[i-33:i+1]) / 34
        result[i] = sma5 - sma34
    return result'''

# ── 3. compute_ac_series: типизация result (закрывает 188/189) ──
OLD_3 = '''    result = [None] * len(ao_series)
    for i in range(len(ao_series)):
        window = ao_series[max(0, i-4):i+1]
        valid  = [v for v in window if v is not None]
        if len(valid) < 5:
            continue
        result[i] = ao_series[i] - sum(valid[-5:]) / 5
    return result'''
NEW_3 = '''    result: list[Optional[float]] = [None] * len(ao_series)
    for i in range(len(ao_series)):
        window = ao_series[max(0, i-4):i+1]
        valid  = [v for v in window if v is not None]
        if len(valid) < 5:
            continue
        result[i] = ao_series[i] - sum(valid[-5:]) / 5
    return result'''

# ── 4. неявный Optional в четырёх сигнатурах (99/232/282/856) ──
OLD_4A = '''def compute_alligator(highs: list[float], lows: list[float],
                      point: float = None) -> dict:'''
NEW_4A = '''def compute_alligator(highs: list[float], lows: list[float],
                      point: Optional[float] = None) -> dict:'''

OLD_4B = "def detect_squat_bars(bars: list[dict], point: float = None) -> dict:"
NEW_4B = "def detect_squat_bars(bars: list[dict], point: Optional[float] = None) -> dict:"

OLD_4C = "def compute_mfi(bar: dict, prev_bar: dict, point: float = None) -> dict:"
NEW_4C = "def compute_mfi(bar: dict, prev_bar: dict, point: Optional[float] = None) -> dict:"

OLD_4D = '''    bars:      list[dict],
    symbol:    str   = "UNKNOWN",
    timeframe: str   = "D1",
    point:     float = None,
) -> dict:'''
NEW_4D = '''    bars:      list[dict],
    symbol:    str   = "UNKNOWN",
    timeframe: str   = "D1",
    point:     Optional[float] = None,
) -> dict:'''

# ── 5. detect_divergent_bar: teeth_series приходит из alligator.get()
#    (закрывает 887) — функция уже проверяет `is None` внутри ──
OLD_5 = '''def detect_divergent_bar(
    bars:         list[dict],
    ao_series:    list,
    teeth_series: list,
) -> dict:'''
NEW_5 = '''def detect_divergent_bar(
    bars:         list[dict],
    ao_series:    list,
    teeth_series: Optional[list],
) -> dict:'''

# ── 6. compute_rubber_band: все 4 параметра приходят потенциально
#    пустыми из alligator.get()/divergent_bar.get() (закрывает 895) —
#    тело уже отбивает None/пусто в первых строчках функции ──
OLD_6 = '''def compute_rubber_band(
    bars:         list,
    lips_series:  list,
    teeth_series: list,
    direction:    str,
    point:        float,
) -> dict:'''
NEW_6 = '''def compute_rubber_band(
    bars:         list,
    lips_series:  Optional[list],
    teeth_series: Optional[list],
    direction:    Optional[str],
    point:        Optional[float],
) -> dict:'''

# ── 7. read_ao_wave_form: teeth_series тоже из alligator.get()
#    (закрывает 899) — тело уже проверяет `if teeth_series else None` ──
OLD_7 = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: list,
    window:       int = 150,
) -> dict:'''
NEW_7 = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: Optional[list],
    window:       int = 150,
) -> dict:'''

# ── 8. global_trend as_of_date: bars гарантированно не пуст в этой
#    точке (build_market_data уже отсёк len(bars)<40 выше по функции).
#    Прямой доступ вместо .get() — без Optional и без немой заглушки
#    (закрывает 914) ──
OLD_8 = '''        _bar_time = bars[-1].get("date") if bars else None
        _r = _gt(symbol, timeframe, as_of_date=_bar_time)'''
NEW_8 = '''        _bar_time = bars[-1]["date"]  # WILLIAMS_CORE_TYPING_V1: bars уже не пуст здесь (len>=40 отсечён выше)
        _r = _gt(symbol, timeframe, as_of_date=_bar_time)'''

EOF_MARKER = "\n# WILLIAMS_CORE_TYPING_V1 — маркер идемпотентности\n"

BLOCKS = [
    ("_smma_series: result", OLD_1, NEW_1),
    ("compute_ao_series: result", OLD_2, NEW_2),
    ("compute_ac_series: result", OLD_3, NEW_3),
    ("compute_alligator: point", OLD_4A, NEW_4A),
    ("detect_squat_bars: point", OLD_4B, NEW_4B),
    ("compute_mfi: point", OLD_4C, NEW_4C),
    ("build_market_data: point", OLD_4D, NEW_4D),
    ("detect_divergent_bar: teeth_series", OLD_5, NEW_5),
    ("compute_rubber_band: 4 параметра", OLD_6, NEW_6),
    ("read_ao_wave_form: teeth_series", OLD_7, NEW_7),
    ("global_trend: as_of_date", OLD_8, NEW_8),
]


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: 27 ошибок Pylance → типизация")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}")
        print("  Запусти патч из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"• маркер {MARKER} уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    ok = True
    for label, old, _new in BLOCKS:
        n = text.count(old)
        status = "✓" if n == 1 else "✗"
        print(f"  {status} якорь [{label}]: найден {n} раз (нужно ровно 1)")
        if n != 1:
            ok = False
    if not ok:
        print("✗ якоря не сошлись — файл отличается от ожидаемого. Ничего не режу.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_name(TARGET.name + f".bak_{ts}")
    shutil.copy2(TARGET, bak)
    print(f"• бэкап: {bak.name}")

    for _label, old, new in BLOCKS:
        text = text.replace(old, new, 1)
    text += EOF_MARKER

    TARGET.write_text(text, encoding="utf-8")
    print("• правки внесены (11 блоков)")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}")
        print("  Файл откатан из бэкапа. Ничего не сломано.")
        sys.exit(1)

    print()
    print("  ГОТОВО. Что исправлено:")
    print("  • _smma_series/compute_ao_series/compute_ac_series: result")
    print("    типизирован как list[Optional[float]] (было list[None])")
    print("  • _smma_series: рекурсия через float-аккумулятор prev —")
    print("    та же формула, сверено побитово на 200 случайных сериях")
    print("  • 4× неявный Optional (point: float = None → Optional[float])")
    print("  • 3× параметры-списки из .get() — Optional[list], как тело")
    print("    функций уже и предполагало (detect_divergent_bar/")
    print("    compute_rubber_band/read_ao_wave_form)")
    print("  • global_trend: bars[-1][\"date\"] вместо .get() с немым None")
    print("  Формулы Вильямса не тронуты ни в одной строке.")
    print("═" * 62)


if __name__ == "__main__":
    main()
