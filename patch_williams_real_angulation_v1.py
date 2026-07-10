# -*- coding: utf-8 -*-
"""
patch_williams_real_angulation_v1.py
─────────────────────────────────────────────────────────────
НАСТОЯЩАЯ АНГУЛЯЦИЯ · Биржа/williams_core.py · detect_divergent_bar

ДИАГНОЗ (подтверждено внешним поиском, не выдумано):
  Код требовал bars_since_cross ∈ [5,7] — жёсткое окно РОВНО в три
  номера бара с момента пересечения Teeth. Это САМОДЕЛЬНАЯ замена,
  не канон Вильямса.

  Настоящая ангуляция Profitunity/MQL5 (проверено по официальному
  MQL5-индикатору "Angulation"):
    — окно поиска ДО 20 баров ("Bars to find angulation... Default
      is 20 bars"), не жёсткие 3 номера бара;
    — мера — УГОЛ расхождения (в градусах) между линией цены и
      линией Аллигатора ("Minimal angle to filter... Default 22°"),
      не количество баров само по себе.

  Дополнительно подтверждено практиками (Forex Factory, ветка по
  системе Вильямса): дивергентные бары сами по себе НЕ редкость —
  "they show up all the time... more conspicuous at market turns".
  Комментарий в коде "~0.3% баров = 3-4 в год" — придуманная студией
  цифра, канону не соответствует.

  Итог: узкое окно 5-7 баров отсеивало подавляющее большинство
  канонически валидных сигналов, потому что момент разворота
  Аллигатора и момент B/D/B бара редко попадают именно в эти три
  конкретных бара. Настоящий метод (угол, окно до 20 баров) должен
  находить их сильно чаще.

ЛЕЧЕНИЕ:
  1. detect_divergent_bar получает новый параметр point (нужен для
     безразмерного угла — в единицах point, не сырой цене).
  2. Новая пара функций: _teeth_cross_index (абсолютный индекс
     пересечения, не расстояние) + _angulation_angle (угол в
     градусах между краем цены и линией Teeth от cross_idx до
     текущего бара).
  3. angulation_ok = найден cross_idx В ПРЕДЕЛАХ 20 баров И угол
     >= 20° (канон: 22°, берём чуть мягче — точный порог настраиваем
     по факту статистики, если Шеф захочет).
  4. point прокидывается через read_ao_wave_form и build_market_data
     до самого detect_divergent_bar — без point угол не посчитать
     (нужна безразмерная единица).
  5. _bars_since_teeth_cross (старая, только на расстояние) удалена —
     нигде больше не используется.
  6. bars_since_cross в ответе остаётся (для обратной совместимости
     с логами/чтением), плюс новое поле angulation_deg — сам угол,
     видно в отладке и на дашборде.

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_williams_real_angulation_v1.py

Идемпотентно: маркер WILLIAMS_REAL_ANGULATION_V1 — повторный запуск
скажет "уже пропатчено" и ничего не тронет второй раз.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "williams_core.py"
MARKER = "# WILLIAMS_REAL_ANGULATION_V1 — маркер идемпотентности"

# ── 1. import math рядом с остальными импортами ────────────────
OLD_IMPORTS = """from pathlib import Path
from typing import Optional"""

NEW_IMPORTS = """import math
from pathlib import Path
from typing import Optional"""

# ── 2. Полная замена detect_divergent_bar + _empty_divergent_bar
#       + _bars_since_teeth_cross → новые функции ──────────────

OLD_BLOCK = '''def detect_divergent_bar(
    bars:         list[dict],
    ao_series:    list,
    teeth_series: Optional[list],
) -> dict:
    """
    Расходящийся бар (BuDB/BDB) по Profitunity Trading Group — Bill Williams.

    BuDB (бычий, оценивается ПОСЛЕДНИЙ бар окна):
      lower_low   — low[i] < low[i-1]            (ниже предыдущего бара)
      upper_close — close > (high + low) / 2     (закрытие в верхней половине)
      → bdb_candidate (локальный факт, ~44% баров)

    bdb_strong (Точка Ноль конца волны 2, ~0.3% баров = 3-4 в год):
      + дивергенция AO под нулём (цена ниже, AO выше предыдущего лоу, оба < 0)
      + ангуляция 5-7 баров от пересечения close с Teeth (сверху вниз)

    Зеркально BDB (медвежий): higher_high + lower_close, AO над нулём.

    teeth_series — SMMA(8) медианы (линия баланса Аллигатора), из compute_alligator.
    """
    i = len(bars) - 1
    if i < 1 or teeth_series is None:
        return _empty_divergent_bar()

    b   = bars[i]
    bp  = bars[i - 1]
    mid = (b["high"] + b["low"]) / 2

    lower_low   = b["low"]   < bp["low"]
    upper_close = b["close"] > mid
    higher_high = b["high"]  > bp["high"]
    lower_close = b["close"] < mid

    bull_candidate = lower_low and upper_close
    bear_candidate = higher_high and lower_close

    direction = "BULL" if bull_candidate else "BEAR" if bear_candidate else None

    bars_since_cross = _bars_since_teeth_cross(bars, teeth_series, direction)
    angulation_ok = (bars_since_cross is not None
                     and 5 <= bars_since_cross <= 7)
    ao_diver = _ao_divergence_at_bar(bars, ao_series, i, direction)

    bdb_candidate = bull_candidate or bear_candidate
    bdb_strong = bool(bdb_candidate and angulation_ok and ao_diver)

    return {
        "direction":        direction,
        "lower_low":        lower_low   if direction == "BULL" else False,
        "upper_close":      upper_close if direction == "BULL" else False,
        "higher_high":      higher_high if direction == "BEAR" else False,
        "lower_close":      lower_close if direction == "BEAR" else False,
        "bars_since_cross": bars_since_cross,
        "angulation_ok":    angulation_ok,
        "ao_divergence":    ao_diver,
        "bdb_candidate":    bdb_candidate,
        "bdb_strong":       bdb_strong,
    }


def _empty_divergent_bar() -> dict:
    return {
        "direction": None, "lower_low": False, "upper_close": False,
        "higher_high": False, "lower_close": False,
        "bars_since_cross": None, "angulation_ok": False,
        "ao_divergence": False, "bdb_candidate": False, "bdb_strong": False,
    }


def _bars_since_teeth_cross(bars: list, teeth_series: list, direction) -> Optional[int]:
    """
    Сколько баров назад close в последний раз пересёк линию Teeth.
    BULL: пересечение сверху вниз (close был >= teeth, стал < teeth).
    BEAR: снизу вверх. Возвращает число баров (0 = на текущем) или None.
    """
    i = len(bars) - 1
    if direction is None:
        return None
    for k in range(i, 0, -1):
        t  = teeth_series[k]   if k   < len(teeth_series) else None
        tp = teeth_series[k-1] if k-1 < len(teeth_series) else None
        if t is None or tp is None:
            continue
        c  = bars[k]["close"]
        cp = bars[k-1]["close"]
        if direction == "BULL":
            if cp >= tp and c < t:
                return i - k
        else:
            if cp <= tp and c > t:
                return i - k
    return None'''

NEW_BLOCK = '''def detect_divergent_bar(
    bars:         list[dict],
    ao_series:    list,
    teeth_series: Optional[list],
    point:        Optional[float] = None,
) -> dict:
    """
    Расходящийся бар (BuDB/BDB) по Profitunity Trading Group — Bill Williams.

    BuDB (бычий, оценивается ПОСЛЕДНИЙ бар окна):
      lower_low   — low[i] < low[i-1]            (ниже предыдущего бара)
      upper_close — close > (high + low) / 2     (закрытие в верхней половине)
      → bdb_candidate (локальный факт)

    bdb_strong:
      + дивергенция AO под нулём (цена ниже, AO выше предыдущего лоу, оба < 0)
      + НАСТОЯЩАЯ ангуляция (WILLIAMS_REAL_ANGULATION_V1): угол расхождения
        между краем цены и линией Teeth, окно ДО 20 баров с момента
        пересечения close/Teeth, порог угла ~20° (канон Profitunity/MQL5:
        окно по умолчанию 20 баров, порог 22° — см. официальный MQL5
        индикатор "Angulation"). Раньше здесь было САМОДЕЛЬНОЕ жёсткое
        окно "bars_since_cross ∈ [5,7]" — не соответствует канону и
        отсеивало почти все реальные сигналы.

    Зеркально BDB (медвежий): higher_high + lower_close, AO над нулём.

    teeth_series — SMMA(8) медианы (линия баланса Аллигатора), из compute_alligator.
    point — шаг цены, нужен для безразмерного угла (единицы point, не сырая цена).
    """
    i = len(bars) - 1
    if i < 1 or teeth_series is None:
        return _empty_divergent_bar()

    b   = bars[i]
    bp  = bars[i - 1]
    mid = (b["high"] + b["low"]) / 2

    lower_low   = b["low"]   < bp["low"]
    upper_close = b["close"] > mid
    higher_high = b["high"]  > bp["high"]
    lower_close = b["close"] < mid

    bull_candidate = lower_low and upper_close
    bear_candidate = higher_high and lower_close

    direction = "BULL" if bull_candidate else "BEAR" if bear_candidate else None

    cross_idx = _teeth_cross_index(bars, teeth_series, direction)
    bars_since_cross = (i - cross_idx) if cross_idx is not None else None

    angulation_deg = None
    angulation_ok = False
    if (cross_idx is not None and bars_since_cross is not None
            and bars_since_cross <= _ANGULATION_LOOKBACK):
        angulation_deg = _angulation_angle(
            bars, teeth_series, cross_idx, i, direction, point)
        if angulation_deg is not None:
            angulation_ok = angulation_deg >= _ANGULATION_MIN_DEG

    ao_diver = _ao_divergence_at_bar(bars, ao_series, i, direction)

    bdb_candidate = bull_candidate or bear_candidate
    bdb_strong = bool(bdb_candidate and angulation_ok and ao_diver)

    return {
        "direction":        direction,
        "lower_low":        lower_low   if direction == "BULL" else False,
        "upper_close":      upper_close if direction == "BULL" else False,
        "higher_high":      higher_high if direction == "BEAR" else False,
        "lower_close":      lower_close if direction == "BEAR" else False,
        "bars_since_cross": bars_since_cross,
        "angulation_deg":   round(angulation_deg, 1) if angulation_deg is not None else None,
        "angulation_ok":    angulation_ok,
        "ao_divergence":    ao_diver,
        "bdb_candidate":    bdb_candidate,
        "bdb_strong":       bdb_strong,
    }


def _empty_divergent_bar() -> dict:
    return {
        "direction": None, "lower_low": False, "upper_close": False,
        "higher_high": False, "lower_close": False,
        "bars_since_cross": None, "angulation_deg": None, "angulation_ok": False,
        "ao_divergence": False, "bdb_candidate": False, "bdb_strong": False,
    }


# WILLIAMS_REAL_ANGULATION_V1: канон Profitunity/MQL5 — окно поиска
# ангуляции ДО 20 баров, порог угла по умолчанию 22° (официальный
# MQL5-индикатор "Angulation"). Берём порог чуть мягче (20°) — запас
# на округления/разные символы; можно подстроить по факту статистики.
_ANGULATION_LOOKBACK = 20
_ANGULATION_MIN_DEG  = 20.0


def _teeth_cross_index(bars: list, teeth_series: list, direction) -> Optional[int]:
    """
    АБСОЛЮТНЫЙ индекс бара, где close последний раз пересёк линию Teeth
    в сторону, ОТКУДА начинается импульс, который B/D/B потом развернёт.
    BULL: пересечение сверху вниз (close был >= teeth, стал < teeth).
    BEAR: снизу вверх. Возвращает индекс бара или None.

    (WILLIAMS_REAL_ANGULATION_V1: раньше была _bars_since_teeth_cross,
    возвращавшая только РАССТОЯНИЕ в барах — этого недостаточно для
    угла, нужен сам индекс начала окна.)
    """
    i = len(bars) - 1
    if direction is None:
        return None
    for k in range(i, 0, -1):
        t  = teeth_series[k]   if k   < len(teeth_series) else None
        tp = teeth_series[k-1] if k-1 < len(teeth_series) else None
        if t is None or tp is None:
            continue
        c  = bars[k]["close"]
        cp = bars[k-1]["close"]
        if direction == "BULL":
            if cp >= tp and c < t:
                return k
        else:
            if cp <= tp and c > t:
                return k
    return None


def _angulation_angle(bars: list, teeth_series: list, cross_idx: int,
                      i: int, direction: str,
                      point: Optional[float]) -> Optional[float]:
    """
    НАСТОЯЩАЯ ангуляция (WILLIAMS_REAL_ANGULATION_V1) — угол расхождения
    (в градусах) между краем цены и линией Teeth от cross_idx до i.

    Канон Profitunity: "растягиваем резинку" между линией цены и линией
    Аллигатора — чем больше угол разрыва, тем сильнее ангуляция (сигнал
    надёжнее). Меряем в единицах point (безразмерно, любой инструмент),
    горизонталь — количество баров (тот же принцип, что в официальном
    MQL5-индикаторе "Angulation").

    BULL: край цены — LOW баров (нижняя кромка последнего движения вниз
          перед разворотом). BEAR: край цены — HIGH баров.
    Без point (не передан) угол посчитать нельзя — честно возвращает None.
    """
    if point is None or point <= 0:
        return None
    span = i - cross_idx
    if span <= 0:
        return None

    if direction == "BULL":
        price_edge_cross = bars[cross_idx]["low"]
        price_edge_now   = bars[i]["low"]
    else:
        price_edge_cross = bars[cross_idx]["high"]
        price_edge_now   = bars[i]["high"]

    teeth_cross = teeth_series[cross_idx] if cross_idx < len(teeth_series) else None
    teeth_now   = teeth_series[i]         if i         < len(teeth_series) else None
    if teeth_cross is None or teeth_now is None:
        return None

    price_slope = (price_edge_now - price_edge_cross) / point / span
    teeth_slope = (teeth_now - teeth_cross) / point / span
    price_angle = math.degrees(math.atan(price_slope))
    teeth_angle = math.degrees(math.atan(teeth_slope))
    return abs(price_angle - teeth_angle)'''

# ── 3. read_ao_wave_form: добавляем point, прокидываем в detect_divergent_bar ──

OLD_WAVE_SIG = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: Optional[list],
    window:       int = 150,
) -> dict:'''

NEW_WAVE_SIG = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: Optional[list],
    window:       int = 150,
    point:        Optional[float] = None,
) -> dict:'''

OLD_WAVE_CALL = '''    if teeth_w is not None:
        db = detect_divergent_bar(bars_w, ao_w, teeth_w)
        if db.get("bdb_strong"):'''

NEW_WAVE_CALL = '''    if teeth_w is not None:
        db = detect_divergent_bar(bars_w, ao_w, teeth_w, point=point)  # WILLIAMS_REAL_ANGULATION_V1
        if db.get("bdb_strong"):'''

# ── 4. build_market_data: прокидываем _point в оба вызова ──────

OLD_BMD_DIV = '''    divergence = detect_ao_divergence(bars, ao_series)
    teeth_series = alligator.get("teeth_series")
    divergent_bar = detect_divergent_bar(bars, ao_series, teeth_series)'''

NEW_BMD_DIV = '''    divergence = detect_ao_divergence(bars, ao_series)
    teeth_series = alligator.get("teeth_series")
    divergent_bar = detect_divergent_bar(bars, ao_series, teeth_series, point=_point)  # WILLIAMS_REAL_ANGULATION_V1'''

OLD_BMD_WAVE = '''    wave_form = read_ao_wave_form(bars, ao_series, teeth_series)'''

NEW_BMD_WAVE = '''    wave_form = read_ao_wave_form(bars, ao_series, teeth_series, point=_point)  # WILLIAMS_REAL_ANGULATION_V1'''


def _patch():
    if not TARGET.exists():
        print(f"[ПАТЧ] ❌ Не найден {TARGET} — запусти из корня репо.")
        raise SystemExit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ williams_core.py уже пропатчен (WILLIAMS_REAL_ANGULATION_V1) — пропускаю.")
        return False

    changed = 0
    for label, old, new in (
        ("import math",              OLD_IMPORTS,   NEW_IMPORTS),
        ("detect_divergent_bar+доп.", OLD_BLOCK,     NEW_BLOCK),
        ("read_ao_wave_form сигнатура", OLD_WAVE_SIG, NEW_WAVE_SIG),
        ("read_ao_wave_form вызов",   OLD_WAVE_CALL, NEW_WAVE_CALL),
        ("build_market_data: divergent_bar", OLD_BMD_DIV, NEW_BMD_DIV),
        ("build_market_data: wave_form",     OLD_BMD_WAVE, NEW_BMD_WAVE),
    ):
        if old in src:
            src = src.replace(old, new)
            changed += 1
            print(f"[ПАТЧ] 🔧 {label}")
        elif new in src:
            print(f"[ПАТЧ] ↺ {label} — уже на месте")
        else:
            print(f"[ПАТЧ] ⚠️  {label} — блок не совпал, проверь вручную")

    if changed == 0:
        print("[ПАТЧ] ⚠️  ничего не изменилось — сверь файл вручную.")
        return False

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] 💾 williams_core.py сохранён (изменений: {changed}).")
    return True


def main():
    print("═" * 62)
    print("  НАСТОЯЩАЯ АНГУЛЯЦИЯ · WILLIAMS_REAL_ANGULATION_V1")
    print("═" * 62)
    _patch()
    print("═" * 62)
    print("  ✅ ГОТОВО. Прогони tester_express.py на том же H4 CSV ещё раз —")
    print("     Сито 1 должно найти БОЛЬШЕ кандидатов, чем 24 (угол вместо")
    print("     жёсткого окна 5-7 баров пропустит канонически валидные точки,")
    print("     раньше отсеянные самодельным правилом).")
    print("═" * 62)


if __name__ == "__main__":
    main()
