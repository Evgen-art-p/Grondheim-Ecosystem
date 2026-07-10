# -*- coding: utf-8 -*-
"""
patch_iskra_working_tf_first_v1.py
─────────────────────────────────────────────────────────────
РАБОЧИЙ ТФ — ГЛАВНЫЙ ИСТОЧНИК · единое окно 100-140 баров

СЛОВО ШЕФА (два подтверждённых факта):
  1. «Ставится рабочий ТФ, его прогоняешь, если сигнал — спускаешься
     для УТОЧНЕНИЯ». Лестница/компас — это ДОУТОЧНЕНИЕ, не ворота,
     без которых Совет вообще не может собраться.
  2. «При визуальном анализе при масштабе экрана 100-140 баров волна
     наиболее адекватно рисуется, и AO хорошо показывает 3 волну».
     Значит окно для чтения формы AO должно быть 100-140 баров —
     не 300 (Сито 1 в тестере) и не совсем точно 150 (wave_form).

ЧТО БЫЛО НЕ ТАК (три места, разные окна одного и того же):
  — tester_express.py, Сито 1: окно 300 баров на каждый кандидат.
  — williams_core.py, read_ao_wave_form: окно 150 баров по умолчанию.
  — iskra_live.py: макро-компас (дивер+горб-царь+пересечение нуля)
    обязателен ПЕРЕД тем, как вообще смотреть рабочий ТФ напрямую —
    лишние ворота поверх уже пройденного сита, да ещё третьим,
    несовпадающим окном.

  Три окна одного явления → одна и та же точка видна по-разному
  разным кускам кода → сигнал, найденный ситом, терялся на
  повторной проверке просто из-за рассинхрона масштаба, не из-за
  того, что рынок скупой на развороты.

ЛЕЧЕНИЕ:
  1. Единое окно 120 баров (середина канонического диапазона
     100-140) — И в Сите 1 (tester_express.py), И в read_ao_wave_form
     (williams_core.py). Один масштаб, один взгляд.
  2. iskra_live.py: рабочий ТФ — ПРЯМОЙ источник. Если на нём самом
     уже есть B/D/B точка (bdb_dir из wave_form) — это НАХОДКА, без
     всякого обязательного макро-компаса. Старая логика (компас +
     лестница) остаётся, но теперь как ЗАПАСНОЙ путь — только если
     на рабочем ТФ сигнала нет напрямую.

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_iskra_working_tf_first_v1.py

Идемпотентно: маркер ISKRA_WORKING_TF_FIRST_V1 — повторный запуск
скажет "уже пропатчено" и ничего не тронет второй раз.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
WILLIAMS = REPO / "Биржа" / "williams_core.py"
TESTER   = REPO / "Биржа" / "tester_express.py"
ISKRA    = (REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
           / "слоты" / "A01" / "мозг.py")
MARKER = "# ISKRA_WORKING_TF_FIRST_V1 — маркер идемпотентности"

# ── 1. williams_core.py: окно wave_form 150 → 120 ───────────────
OLD_WAVE_WINDOW = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: Optional[list],
    window:       int = 150,
    point:        Optional[float] = None,
) -> dict:'''

NEW_WAVE_WINDOW = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: Optional[list],
    window:       int = 120,   # ISKRA_WORKING_TF_FIRST_V1: канон Шефа —
                                # 100-140 баров, экран рисует волну и
                                # 3-ю волну AO наиболее адекватно
    point:        Optional[float] = None,
) -> dict:'''

# Фоллбэк, если williams_core.py ещё НЕ пропатчен предыдущим патчем
# (WILLIAMS_REAL_ANGULATION_V1 — там сигнатура уже с point). Если
# сигнатура старая (без point), правим её тоже.
OLD_WAVE_WINDOW_NO_POINT = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: Optional[list],
    window:       int = 150,
) -> dict:'''

NEW_WAVE_WINDOW_NO_POINT = '''def read_ao_wave_form(
    bars:         list,
    ao_series:    list,
    teeth_series: Optional[list],
    window:       int = 120,   # ISKRA_WORKING_TF_FIRST_V1: канон Шефа —
                                # 100-140 баров, экран рисует волну и
                                # 3-ю волну AO наиболее адекватно
) -> dict:'''

# ── 2. tester_express.py: окно Сита 1 300 → 120 ────────────────
OLD_SIEVE_WINDOW = '''        candidates = []
        for i in range(warmup, total):
            end = i + 1
            start = max(0, end - 300)
            window = bars_all[start:end]'''

NEW_SIEVE_WINDOW = '''        candidates = []
        for i in range(warmup, total):
            end = i + 1
            start = max(0, end - 120)   # ISKRA_WORKING_TF_FIRST_V1: канон
            # Шефа — 100-140 баров, тот же масштаб, что и read_ao_wave_form.
            # Было 300 — рассинхрон окна с повторной проверкой Искры прятал
            # реальные точки на ровном месте (разный "горб-царь" в разных
            # по ширине окнах одного и того же явления).
            window = bars_all[start:end]'''

# ── 3. iskra_live.py: рабочий ТФ — прямой источник, компас — запасной путь ──

OLD_DESCENT_CALL = '''    _start_tf = _start_timeframe(symbol, timeframe)
    _top_form = _read_form_on(symbol, _start_tf)
    _compass  = _compass_from(_top_form)
    if _compass is None:
        # Нет компаса (нет дивера-с-якорем) — Искре нечего ловить.
        _descent = {"found": False, "timeframe": None,
                    "zero_point": None, "compass": None, "start_tf": _start_tf}
    else:
        _res = _descend(symbol, _start_tf, _compass, _top_form)
        _descent = {"found": _res["found"], "timeframe": _res["timeframe"],
                    "zero_point": _res["zero_point"], "compass": _compass,
                    "start_tf": _start_tf}'''

NEW_DESCENT_CALL = '''    _start_tf = _start_timeframe(symbol, timeframe)
    _top_form = _read_form_on(symbol, _start_tf)

    # ISKRA_WORKING_TF_FIRST_V1 (слово Шефа): рабочий ТФ — ПРЯМОЙ и
    # ГЛАВНЫЙ источник сигнала. Если на нём самом уже есть B/D/B точка
    # (bdb_dir из wave_form, то же окно 100-140, что и Сито 1) — это
    # находка, БЕЗ всякого обязательного макро-компаса. Раньше макро-
    # компас (дивер+горб-царь+пересечение нуля) был ВОРОТАМИ перед
    # рабочим ТФ — лишний, более редкий фильтр поверх уже пройденного
    # сита. Теперь это ЗАПАСНОЙ путь — доуточнение, не ворота.
    _working_bdb = _top_form.get("bdb_dir")
    if _working_bdb is not None:
        _descent = {"found": True, "timeframe": _start_tf,
                    "zero_point": _top_form.get("bdb_price"),
                    "compass": _working_bdb, "start_tf": _start_tf}
    else:
        _compass = _compass_from(_top_form)
        if _compass is None:
            # Нет компаса (нет дивера-с-якорем) — Искре нечего ловить.
            _descent = {"found": False, "timeframe": None,
                        "zero_point": None, "compass": None, "start_tf": _start_tf}
        else:
            _res = _descend(symbol, _start_tf, _compass, _top_form)
            _descent = {"found": _res["found"], "timeframe": _res["timeframe"],
                        "zero_point": _res["zero_point"], "compass": _compass,
                        "start_tf": _start_tf}'''


def _patch_file(path: Path, replacements: list, label: str) -> int:
    if not path.exists():
        print(f"[ПАТЧ] ❌ Не найден {path}")
        raise SystemExit(1)
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✅ {label} уже пропатчен — пропускаю.")
        return 0
    changed = 0
    for name, old, new in replacements:
        if old in src:
            src = src.replace(old, new)
            changed += 1
            print(f"[ПАТЧ] 🔧 {label}: {name}")
        elif new in src:
            print(f"[ПАТЧ] ↺ {label}: {name} — уже на месте")
        else:
            print(f"[ПАТЧ] ⚠️  {label}: {name} — блок не совпал, проверь вручную")
    if changed:
        src = src.rstrip() + "\n\n" + MARKER + "\n"
        path.write_text(src, encoding="utf-8")
        print(f"[ПАТЧ] 💾 {label} сохранён (изменений: {changed}).")
    return changed


def main():
    print("═" * 62)
    print("  РАБОЧИЙ ТФ + ОКНО 100-140 · ISKRA_WORKING_TF_FIRST_V1")
    print("═" * 62)

    _patch_file(WILLIAMS, [
        ("read_ao_wave_form окно (с point)",    OLD_WAVE_WINDOW,          NEW_WAVE_WINDOW),
        ("read_ao_wave_form окно (без point)",  OLD_WAVE_WINDOW_NO_POINT, NEW_WAVE_WINDOW_NO_POINT),
    ], "williams_core.py")

    _patch_file(TESTER, [
        ("Сито 1 окно 300→120", OLD_SIEVE_WINDOW, NEW_SIEVE_WINDOW),
    ], "tester_express.py")

    _patch_file(ISKRA, [
        ("рабочий ТФ прямой источник", OLD_DESCENT_CALL, NEW_DESCENT_CALL),
    ], "A01/мозг.py (Искра)")

    print("═" * 62)
    print("  ✅ ГОТОВО. Прогони tester_express.py на том же H4 CSV ещё раз.")
    print("     Ожидание: спуск теперь чаще найдёт точку на самом рабочем")
    print("     ТФ (без обязательного макро-компаса) — Совет должен")
    print("     собираться заметно чаще, чем 1 раз из 24 кандидатов.")
    print("═" * 62)


if __name__ == "__main__":
    main()
