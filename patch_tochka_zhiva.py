#!/usr/bin/env python3
# patch_tochka_zhiva.py
# ─────────────────────────────────────────────────────────────
# TOCHKA_ZHIVA_V1 · 19-20.07
#
# §5р.6 диагноз: ворота Совета — снимок ОДНОГО бара, не цепь во
# времени. Точка c гаснет раньше, чем цена реально доходит до
# фрактала Ганса (станция «1» на схеме Шефа).
#
# Канон смерти точки (ТЗ Студии «Шесть Пальцев» + Шеф, 19.07):
#   1. СТРУКТУРНЫЙ СЛОМ — цена пробила zero_point_price против
#      направления точки.
#   2. TWR НЕЙТРАЛЕН — 5-периодная застряла между 13 и 34
#      (импульс угас во флэте). Требует TWR_BOLSHOY_PALEC_V1
#      (patch_twr_bolshoy_palec.py) — применить ДО этого патча.
# Подпитка той же стороной (новый BDB туда же + GREEN/SQUAT бар) —
# точка не умирает, zero_point_price/таймер обновляются.
#
# Код, без LLM. Читает/пишет trading_state["iskra"].
# proverit_tochku() зовётся из council.py/tester_express.py на
# каждом баре между кандидатами — следующий патч (гейт Совета)
# подключит её к wake_council. Здесь — только сам орган проверки.
#
# ИДЕМПОТЕНТНОСТЬ: маркер TOCHKA_ZHIVA_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Биржа" / "hooks.py"
MARKER = "TOCHKA_ZHIVA_V1"


ANCHOR_STATE = '''_DEFAULT_STATE = {
    "version": 1,
    "updated": None,
    "iskra": {
        "t1_status":        "NOT_FOUND",
        "zero_point_price": None,
        "history_dna":      "",
    },
    "positions": [],
}'''

ANCHOR_STATE_REPLACEMENT = '''_DEFAULT_STATE = {
    "version": 1,
    "updated": None,
    "iskra": {
        "t1_status":        "NOT_FOUND",
        "zero_point_price": None,
        "history_dna":      "",
        # TOCHKA_ZHIVA_V1: точка c живёт между барами, не гаснет
        # снимком одного бара. alive — жива ли прямо сейчас.
        # rodilas_na_bare — bar_time последнего обновления/рождения
        # (подпитка той же стороной двигает эту метку вперёд).
        "alive":            False,
        "rodilas_na_bare":  None,
    },
    "positions": [],
}'''


NEW_FUNCTION = '''

# ═══════════════════════════════════════════════════════════
# ''' + MARKER + ''' — точка c живёт между барами (§5р.6)
# ═══════════════════════════════════════════════════════════
# Три станции канона (c → 1 → 2) разнесены во времени (дни на D1).
# Раньше "found" Искры было снимком ТЕКУЩЕГО бара — точка гасла
# раньше, чем реально доходило дело до фрактала Ганса, и Совет на
# станцию «1» просто не просыпался (Ганса никто не спрашивал).
#
# Теперь точка ХРАНИТСЯ в trading_state["iskra"] и живёт, пока не
# умрёт по одному из двух честных признаков:
#   1. СТРУКТУРНЫЙ СЛОМ — цена пробила zero_point_price против
#      направления (дно/потолок разворота пробит вглубь).
#   2. TWR НЕЙТРАЛЕН — 5-периодная SMA(close) застряла между 13 и 34
#      (Новый Хаос гл.9) — импульс разворота угас во флэте.
# Подпитка той же стороной: новый BDB туда же направление +
# GREEN/SQUAT бар подтверждения → точка НЕ умирает, только
# zero_point_price/таймер обновляются (новая энергия того же знака).
#
# Код, без LLM — экономим токены Шефа на каждом баре.
# ═══════════════════════════════════════════════════════════

def proverit_tochku(md: dict) -> dict:
    """
    Кодовая (без LLM) проверка живости точки c на текущем баре.
    Читает/пишет trading_state["iskra"]. Зовётся на КАЖДОМ баре
    между кандидатами (тем же местом, что _settle_bar/_vesti_poziciyu
    в tester_express.py — дёшево на пустом столе).

    Возвращает {"alive": bool, "reason": str, "changed": bool}.
    "changed" — точка поменяла состояние на этом баре (для ленты).
    """
    tstate = load_trading_state()
    isk = tstate.setdefault("iskra", {})
    alive = bool(isk.get("alive"))
    zp    = isk.get("zero_point_price")
    napr  = isk.get("trend_direction") or isk.get("napravlenie")

    if not alive or zp is None or napr not in ("BULL", "BEAR"):
        return {"alive": False, "reason": "точки нет", "changed": False}

    price = md.get("price", {}) or {}
    low   = price.get("low")
    high  = price.get("high")
    twr   = md.get("twr", {}) or {}
    db    = md.get("divergent_bar", {}) or {}
    mfi_type = (md.get("mfi", {}) or {}).get("type")

    # ── 1. подпитка той же стороной — ПРОВЕРЯЕТСЯ ПЕРВОЙ ──
    # Порядок важен (найдено тестом при отладке патча): пробой
    # zero_point_price свежим баром той же стороны с GREEN/SQUAT —
    # это НЕ слом, это новая, более глубокая версия ТОЙ ЖЕ точки.
    # Слом — только когда пробой ничем не подтверждён.
    if db.get("direction") == napr and mfi_type in ("GREEN", "SQUAT"):
        novaya_zp = None
        if napr == "BULL" and low is not None:
            novaya_zp = min(zp, low)      # новое, более глубокое дно
        elif napr == "BEAR" and high is not None:
            novaya_zp = max(zp, high)     # новый, более высокий потолок
        if novaya_zp is not None and novaya_zp != zp:
            isk["zero_point_price"] = novaya_zp
            isk["rodilas_na_bare"]  = md.get("bar_time")
            save_trading_state(tstate)
            return {"alive": True,
                    "reason": f"подпитка {mfi_type}: точка обновлена → {novaya_zp}",
                    "changed": True}

    # ── 2. структурный слом (пробой БЕЗ подтверждения — не подпитка) ──
    slomana = False
    if napr == "BULL" and low is not None and low < zp:
        slomana = True
    elif napr == "BEAR" and high is not None and high > zp:
        slomana = True
    if slomana:
        isk["alive"] = False
        save_trading_state(tstate)
        return {"alive": False,
                "reason": f"структурный слом: цена пробила {zp}",
                "changed": True}

    # ── 3. TWR нейтрален (импульс угас) ──
    if twr.get("neutral") is True:
        isk["alive"] = False
        save_trading_state(tstate)
        return {"alive": False,
                "reason": "TWR нейтрален — ритм угас во флэте",
                "changed": True}

    return {"alive": True, "reason": "жива", "changed": False}

# ''' + MARKER + ''' - marker
'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    if ANCHOR_STATE not in src:
        raise SystemExit("❌ якорь _DEFAULT_STATE не найден — "
                          "файл разошёлся с ожидаемым, патч НЕ применён")

    anchor_fn = '''def gate_hans(chain_data: dict) -> bool:'''
    if anchor_fn not in src:
        raise SystemExit("❌ якорь gate_hans не найден — патч НЕ применён")

    src = src.replace(ANCHOR_STATE, ANCHOR_STATE_REPLACEMENT, 1)
    src = src.replace(anchor_fn, NEW_FUNCTION.strip("\n") + "\n\n\n" + anchor_fn, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_tochka")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
