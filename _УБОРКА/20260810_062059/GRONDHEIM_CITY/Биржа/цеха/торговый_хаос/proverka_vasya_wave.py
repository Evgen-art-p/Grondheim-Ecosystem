# -*- coding: utf-8 -*-
"""
ПРОВЕРКА: VASYA_SVOY_RAZVOROT_V1 — собственный глаз Василия

НОЛЬ LLM-ВЫЗОВОВ. Совет не будится, модели не трогаются, ни копейки
не тратится. _read_vasya_wave — чистая геометрия: спуск по лесенке,
бары из источника, ядро williams_core. Никакого chat() внутри.

ЧТО ПОКАЗЫВАЕТ:
  1. какой этаж лежит в шине от Искры (found_timeframe)
  2. на какой этаж спускается Василий (step_down от него)
  3. что видит его глаз на этом этаже (bdb_dir / bdb_price / dlina)

ЗАПУСК: из корня репо
    python proverka_vasya_wave.py
    python proverka_vasya_wave.py EURUSD        # другой символ
    python proverka_vasya_wave.py XAUUSD H4     # + принудительный этаж Искры

Если в шине пусто (Искра ещё не бегала) — берётся этаж из аргумента
или H4 по умолчанию, чтобы всё равно померить геометрию.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]   # PERENOS_V_TSEH_V1: файл теперь в цеха/торговый_хаос/
BIRZHA = REPO / "Биржа"
A08_DIR = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / "A08"
A08_BRAIN = A08_DIR / "мозг.py"


def _load_vasya():
    """Поднимает мозг A08 как модуль, не трогая пакетную структуру."""
    if not A08_BRAIN.exists():
        print(f"✗ не найден мозг Василия: {A08_BRAIN}")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("vasya_brain", A08_BRAIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
    forced_tf = sys.argv[2] if len(sys.argv) > 2 else None

    if str(BIRZHA) not in sys.path:
        sys.path.insert(0, str(BIRZHA))

    vasya = _load_vasya()

    # ── 1. что в шине от Искры ───────────────────────────────
    try:
        from hooks import load_trading_state
        tstate = load_trading_state()
        iskra = tstate.get("iskra", {}) or {}
        shina_tf = iskra.get("found_timeframe")
        feed_mode = (tstate.get("feed", {}) or {}).get("mode", "real")
    except Exception as e:
        print(f"⚠️  шина не прочиталась ({e}) — работаю без неё")
        iskra, shina_tf, feed_mode = {}, None, "?"

    iskra_tf = forced_tf or shina_tf or "H4"

    print("═" * 62)
    print(f"  ПРОВЕРКА ГЛАЗА ВАСИЛИЯ · {symbol}")
    print("═" * 62)
    print(f"  кран источника          : {feed_mode}")
    print(f"  этаж Искры в шине       : {shina_tf or '(пусто — Искра не бегала)'}")
    if forced_tf:
        print(f"  этаж форсирован из строки: {forced_tf}")
    print(f"  берём за этаж Искры     : {iskra_tf}")
    print(f"  точка Искры (zero_point): {iskra.get('zero_point_price')}")
    print(f"  компас Искры            : {iskra.get('compass')}")
    print("─" * 62)

    # ── 2. куда спускается Василий ───────────────────────────
    try:
        from mt5_feed import step_down
        own_tf = step_down(iskra_tf)
    except Exception as e:
        print(f"✗ лесенка не поднялась: {e}")
        return 1

    if own_tf is None:
        print(f"  этаж Василия            : НЕТ — {iskra_tf} это дно лесенки")
        print("  → Василий честно молчит (сенсор без факта). Это не баг.")
    else:
        print(f"  этаж Василия (ниже на 1): {own_tf}")
    print("─" * 62)

    # ── 3. что видит его глаз ────────────────────────────────
    try:
        wf = vasya._read_vasya_wave(symbol, iskra_tf)
    except Exception as e:
        print(f"✗ _read_vasya_wave упала: {type(e).__name__}: {e}")
        return 1

    print("  ЕГО СОБСТВЕННЫЙ ГЛАЗ (own_wave):")
    for k in ("timeframe", "bdb_dir", "bdb_price",
              "dlina", "struktura_chitaetsya"):
        print(f"    {k:22} = {wf.get(k)}")

    print("─" * 62)
    if wf.get("bdb_dir"):
        print(f"  ✓ РАЗВОРОТ ЕСТЬ: {wf['bdb_dir']} @ {wf.get('bdb_price')} "
              f"на {wf.get('timeframe')}")
        print("    Василий увидит его на столе как own_wave.")
    elif wf.get("timeframe"):
        print(f"  ○ этаж {wf['timeframe']} прочитан, разворотного бара пока нет.")
        print("    Это честный ноль — не ошибка. Глаз работает, добычи нет.")
    else:
        print("  ⚠️  форма пустая — этаж не прочитался вовсе.")
        print("    Проверь: есть ли бары этого ТФ в источнике (кран/папка).")
    print("═" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
