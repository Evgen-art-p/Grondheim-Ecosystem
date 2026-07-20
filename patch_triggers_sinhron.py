#!/usr/bin/env python3
# patch_triggers_sinhron.py
# ─────────────────────────────────────────────────────────────
# TRIGGERS_SINHRON_V1 · 20.07
#
# Наблюдение Шефа (картинка c→1→2, всё внутри ОДНОЙ волны 1):
# станции цепочки обязаны быть синхронны по направлению. Раньше
# Триггер Б (фрактал Ганса) срабатывал на ЛЮБОМ пробое — вверх или
# вниз, — не спрашивая, куда смотрит живая точка. Одна волна могла
# бы разбудить Совет по фракталу совсем ДРУГОГО направления, чем
# нашла Искра — то есть чтение "не в ту сторону", ровно то, чего
# Шеф и опасался.
#
# ПАТЧ: Триггер Б засчитывается, только если направление пробоя
# фрактала (_hans_breakout: LONG/SHORT) совпадает с направлением
# живой точки (BULL/BEAR). Триггер В — так же, thumb_trade.direction
# должен совпадать с направлением точки.
#
# ЗАВИСИМОСТЬ: применить ПОСЛЕ patch_tochka_napravlenie.py (нужно,
# чтобы proverit_tochku() отдавала "direction" в своём ответе).
#
# ИДЕМПОТЕНТНОСТЬ: маркер TRIGGERS_SINHRON_V1 в обоих файлах — патч
# не накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
MARKER = "TRIGGERS_SINHRON_V1"

_HANS_MAP = "_HANS_TO_BULL_BEAR = {\"LONG\": \"BULL\", \"SHORT\": \"BEAR\"}  # " + MARKER


# ── council.py ────────────────────────────────────────────────

COUNCIL_TARGET = _ROOT / "Биржа" / "council.py"

COUNCIL_ANCHOR = '''    # Триггер Б — фрактал Ганса пробит вне пасти на ЭТОМ баре
    hans_dir = _hans_breakout(md, bars)
    if hans_dir is not None:
        return {"trigger": True, "kind": "fractal",
                "napravlenie": hans_dir, "tochka": tochka}

    # Триггер В — Большой палец Авантюриста сработал на ЭТОМ баре
    thumb = md.get("thumb_trade", {}) or {}
    if thumb.get("triggered"):
        return {"trigger": True, "kind": "thumb",
                "napravlenie": thumb.get("direction"), "tochka": tochka}'''

COUNCIL_REPLACEMENT = '''    # ''' + MARKER + ''': направление точки — синхронность станций c→1→2.
    # Пробой фрактала/палец в ДРУГУЮ сторону — не наша волна, молчим.
    _napr_tochki = tochka.get("direction")

    # Триггер Б — фрактал Ганса пробит вне пасти на ЭТОМ баре,
    # В ТУ ЖЕ сторону, что и живая точка
    hans_dir = _hans_breakout(md, bars)
    if hans_dir is not None and _HANS_TO_BULL_BEAR.get(hans_dir) == _napr_tochki:
        return {"trigger": True, "kind": "fractal",
                "napravlenie": hans_dir, "tochka": tochka}

    # Триггер В — Большой палец Авантюриста, В ТУ ЖЕ сторону
    thumb = md.get("thumb_trade", {}) or {}
    if thumb.get("triggered") and thumb.get("direction") == _napr_tochki:
        return {"trigger": True, "kind": "thumb",
                "napravlenie": thumb.get("direction"), "tochka": tochka}'''


# ── tester_express.py ────────────────────────────────────────

TESTER_TARGET = _ROOT / "Биржа" / "tester_express.py"

TESTER_ANCHOR = '''            if _tochka.get("alive"):
                _hd = _hans_breakout(md, window)
                if _hd is not None:
                    _cheap_trigger = ("fractal", _hd)
                else:
                    _thumb = md.get("thumb_trade", {}) or {}
                    if _thumb.get("triggered"):'''

TESTER_REPLACEMENT = '''            if _tochka.get("alive"):
                # ''' + MARKER + ''': синхронность — пробой/палец должен
                # смотреть в ТУ ЖЕ сторону, что и живая точка.
                _napr_tochki = _tochka.get("direction")
                _hd = _hans_breakout(md, window)
                if _hd is not None and _HANS_TO_BULL_BEAR.get(_hd) == _napr_tochki:
                    _cheap_trigger = ("fractal", _hd)
                else:
                    _thumb = md.get("thumb_trade", {}) or {}
                    if (_thumb.get("triggered")
                            and _thumb.get("direction") == _napr_tochki):'''


def _patch_file(target: Path, anchor: str, replacement: str, need_map: bool,
                 map_anchor_hint: str) -> bool:
    """Возвращает True, если реально записал файл; False — если пропустил
    (маркер уже стоял, идемпотентно)."""
    if not target.exists():
        raise SystemExit(f"❌ не найден: {target}")

    src = target.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён в {target.name} — пропуск (идемпотентно).")
        return False

    if anchor not in src:
        raise SystemExit(f"❌ якорь не найден в {target.name} — патч НЕ применён")

    src = src.replace(anchor, replacement, 1)

    if need_map:
        if map_anchor_hint not in src:
            raise SystemExit(f"❌ якорь для карты LONG/SHORT→BULL/BEAR не найден "
                              f"в {target.name} — патч НЕ применён")
        src = src.replace(map_anchor_hint, _HANS_MAP + "\n\n\n" + map_anchor_hint, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис в {target.name}: {e} — файл НЕ тронут")

    backup = target.with_suffix(".py.bak_sinhron")
    shutil.copy2(target, backup)
    target.write_text(src, encoding="utf-8")
    print(f"✓ записано: {target}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(target), doraise=True)
    print(f"✓ py_compile прошёл ({target.name})")
    return True


def main():
    # council.py: карта LONG/SHORT->BULL/BEAR кладём перед функцией
    # _deshyovaya_proverka_tochki (используем сигнатуру как якорь).
    did_council = _patch_file(
        COUNCIL_TARGET, COUNCIL_ANCHOR, COUNCIL_REPLACEMENT,
        need_map=True,
        map_anchor_hint="def _deshyovaya_proverka_tochki(symbol: str, timeframe: str,")

    # tester_express.py: своя копия карты (файл самостоятельный, читает
    # bare-импортами) — кладём на МОДУЛЬНОМ уровне (не внутри функции/
    # try — там ломает отступы), рядом с _TEST_POINT.
    did_tester = _patch_file(
        TESTER_TARGET, TESTER_ANCHOR, TESTER_REPLACEMENT,
        need_map=True,
        map_anchor_hint="_TEST_POINT = {")

    if did_council or did_tester:
        print(f"✓ {MARKER} применён (изменено файлов: "
              f"{int(did_council) + int(did_tester)} из 2)")
    else:
        print(f"✓ {MARKER}: оба файла уже были пропатчены — ничего не изменилось")


if __name__ == "__main__":
    main()
