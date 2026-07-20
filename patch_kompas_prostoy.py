#!/usr/bin/env python3
# patch_kompas_prostoy.py
# ─────────────────────────────────────────────────────────────
# KOMPAS_PROSTOY_V1 · 20.07 (заменяет KOMPAS_DINAMICHESKI_V1 —
# тот патч НЕ применять, он трогал не то, что нужно)
#
# Диагноз Шефа (20.07): компас не должен искать целую точку разворота
# на старшем этаже (дивер+якорь-царь+пересечение нуля) — это комплекс
# для НАХОЖДЕНИЯ точки, компасу нужен только простой ответ "куда дует
# ветер". Полностью согласен — но при попытке решить это первым
# патчем (KOMPAS_DINAMICHESKI_V1, менял _start_timeframe) нашлась
# опасная связка: _start_timeframe() в этом файле служит ТРЕМ разным
# целям сразу — (1) этаж для компаса, (2) этаж, на котором Искра
# ищет САМУ точку "рабочим ТФ первым" (ISKRA_WORKING_TF_FIRST_V1),
# (3) старт спуска по лесенке, если на рабочем пусто. Раньше все три
# роли совпадали ТОЛЬКО потому, что feed_config.json не существовал
# и функция тихо возвращала fallback=рабочий ТФ. Патч, меняющий
# _start_timeframe() глобально, увёл бы поиск САМОЙ ТОЧКИ на макро-
# этаж вместо рабочего — сломал бы то, что защищено отдельным каноном.
#
# ПРАВИЛЬНОЕ РЕШЕНИЕ: две независимые роли — два независимых источника.
#   _start_timeframe() / _top_form / _descend — НЕ ТРОГАЕМ ВООБЩЕ,
#   работают как работали (поиск точки рабочим ТФ первым — цел).
#   Новая, ОТДЕЛЬНАЯ пара функций — только для компаса:
#     _macro_timeframe(fallback)   — 2 этажа вверх по лесенке (динамически)
#     _read_alligator_on(symbol, tf) — простой замер Аллигатора этажа
#   _compass_from() переписан: не дивер+якорь+пересечение нуля, а
#   простое сравнение Губы/Зубы/Челюсть (куда открыта пасть).
#
# ИДЕМПОТЕНТНОСТЬ: маркер KOMPAS_PROSTOY_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = (Path(__file__).resolve().parent / "GRONDHEIM_CITY" / "Биржа"
          / "цеха" / "торговый_хаос" / "слоты" / "A01" / "мозг.py")
MARKER = "KOMPAS_PROSTOY_V1"


ANCHOR_COMPASS_FROM = '''def _compass_from(form: dict):
    """
    КОМПАС = СВЯЗКА (§1d). Дивер засчитывается ТОЛЬКО с якорем-царём
    и пересечением нуля после него. Голый дивер ложен — их полно.
      BULL: divergence_dir=BULL + есть anchor_ao_max + zero_cross_after_max
      BEAR: divergence_dir=BEAR + есть anchor_ao_min + zero_cross_after_min
    Возвращает "BULL" / "BEAR" / None.
    """
    d = form.get("divergence_dir")
    if d == "BULL":
        if form.get("anchor_ao_max") is not None and form.get("zero_cross_after_max"):
            return "BULL"
    elif d == "BEAR":
        if form.get("anchor_ao_min") is not None and form.get("zero_cross_after_min"):
            return "BEAR"
    return None'''

REPLACEMENT_COMPASS_FROM = '''def _macro_timeframe(fallback: str) -> str:
    """
    ''' + MARKER + ''': этаж КОМПАСА — 2 этажа вверх по лесенке от
    рабочего (fallback), 1 если двух нет, сам fallback если он уже
    на самом верху (MN1). НЕ путать с _start_timeframe() — та даёт
    этаж для ПОИСКА ТОЧКИ (working-tf-first, спуск), эта — только
    для ориентира направления. Разные роли, разные источники.
    """
    try:
        from mt5_feed import _TF_LADDER
        tf = (fallback or "").upper()
        if tf in _TF_LADDER:
            i = _TF_LADDER.index(tf)
            if i - 2 >= 0:
                return _TF_LADDER[i - 2]
            if i - 1 >= 0:
                return _TF_LADDER[i - 1]
    except Exception as e:
        print(f"[ISKRA] ℹ️  макро-лесенка не поднялась ({e}) — компас от рабочего")
    return fallback


def _read_alligator_on(symbol: str, tf: str) -> dict:
    """
    ''' + MARKER + ''': разовый замер ОДНОГО показателя старшего
    этажа для компаса — Аллигатора (Губы/Зубы/Челюсть). Не полный
    market_data, не wave_form — компасу не нужна точка, только
    направление пасти. Пустой словарь — этаж слепой (спуск это поймёт
    как compass=None, честно).
    """
    from mt5_feed import pull_bars
    from williams_core import build_market_data

    bars, point = pull_bars(symbol, tf)
    if not bars or point is None:
        return {}
    md = build_market_data(bars, symbol=symbol, timeframe=tf, point=point)
    if not md:
        return {}
    return md.get("alligator", {}) or {}


def _compass_from(alligator: dict):
    """
    ''' + MARKER + ''' (слово Шефа 20.07): компас — ПРОСТОЕ чтение
    тренда старшего этажа, куда смотрит пасть Аллигатора. НЕ полный
    комплекс дивер+якорь-царь+пересечение нуля — тот ищет ТОЧКУ на
    рабочем этаже (см. _descend), компасу точка не нужна, только
    направление. Раньше компас требовал того же редкого комплекса,
    что и сама точка, — на старшем этаже это совпадало ещё реже.
      Губы > Зубы > Челюсть  -> BULL (пасть смотрит вверх)
      Губы < Зубы < Челюсть  -> BEAR (пасть смотрит вниз)
      иначе (спит/перепутаны/этаж слепой) -> None
    """
    jaw   = alligator.get("jaw")
    teeth = alligator.get("teeth")
    lips  = alligator.get("lips")
    if jaw is None or teeth is None or lips is None:
        return None
    if lips > teeth > jaw:
        return "BULL"
    if lips < teeth < jaw:
        return "BEAR"
    return None'''


ANCHOR_CALL_SITE = '''    _start_tf = _start_timeframe(symbol, timeframe)
    _top_form = _read_form_on(symbol, _start_tf)'''

REPLACEMENT_CALL_SITE = '''    _start_tf = _start_timeframe(symbol, timeframe)
    _top_form = _read_form_on(symbol, _start_tf)

    # ''' + MARKER + ''': компас — ОТДЕЛЬНЫЙ, независимый источник
    # (макро-этаж + простой Аллигатор), НЕ тот же _start_tf/_top_form,
    # что кормит поиск точки ниже (working-tf-first — не трогаем).
    _macro_tf = _macro_timeframe(timeframe)
    _macro_alligator = _read_alligator_on(symbol, _macro_tf)'''


ANCHOR_COMPASS_CALL = '''    _compass = _compass_from(_top_form)'''

REPLACEMENT_COMPASS_CALL = '''    _compass = _compass_from(_macro_alligator)   # ''' + MARKER + ''': с макро-этажа, не с _top_form'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    if "KOMPAS_DINAMICHESKI_V1" in src:
        raise SystemExit("❌ найден маркер KOMPAS_DINAMICHESKI_V1 — тот патч уже "
                          "применён поверх файла, а этот патч рассчитан на файл "
                          "БЕЗ него. Верни файл из бэкапа "
                          "мозг.py.bak_kompas и накати ЭТОТ патч заново.")

    for anchor, name in [(ANCHOR_COMPASS_FROM, "_compass_from"),
                          (ANCHOR_CALL_SITE, "точка вызова _start_tf/_top_form"),
                          (ANCHOR_COMPASS_CALL, "вызов _compass_from")]:
        if anchor not in src:
            raise SystemExit(f"❌ якорь не найден ({name}) — файл разошёлся "
                              f"с ожидаемым, патч НЕ применён")

    src = src.replace(ANCHOR_COMPASS_FROM, REPLACEMENT_COMPASS_FROM, 1)
    src = src.replace(ANCHOR_CALL_SITE, REPLACEMENT_CALL_SITE, 1)
    src = src.replace(ANCHOR_COMPASS_CALL, REPLACEMENT_COMPASS_CALL, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_kompas2")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
