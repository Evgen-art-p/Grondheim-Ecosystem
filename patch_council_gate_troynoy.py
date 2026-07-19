#!/usr/bin/env python3
# patch_council_gate_troynoy.py
# ─────────────────────────────────────────────────────────────
# COUNCIL_GATE_TROYNOY_V1 · 20.07
#
# ТЗ Студии «Шесть Пальцев» (Лока) + Шеф, 20.07 — «слияние·сит·разрешено».
#
# Раньше ворота Совета были ОДНИМ условием: свежий спуск Искры на
# ЭТОМ баре (COUNCIL_BY_DESCENT_V1). §5р.6: точка c транзитна, живёт
# 1-несколько баров — а фрактал Ганса (станция «1») или Большой
# палец Авантюриста могут случиться днями позже на D1. Совет на эти
# бары просто не просыпался.
#
# Теперь ТРИ триггера (любой ОДИН достаточен):
#   А. Свежий спуск Искры на этом баре (descent.found) — как раньше.
#   Б. Точка ЖИВА (TOCHKA_ZHIVA_V1) И на этом баре пробит фрактал
#      Ганса (дешёвая линза _hans_breakout из hooks.py, БЕЗ LLM).
#   В. Точка ЖИВА И на этом баре сработал Большой палец Авантюриста
#      (TWR_BOLSHOY_PALEC_V1, thumb_trade.triggered — БЕЗ LLM).
#
# Дешёвая проверка (Б/В) идёт ДО дорогого созыва сенсоров/трейдеров:
# Искра (голова) уже отработала выше (нужна для её голоса в любом
# случае), но ворота теперь читают И её свежий спуск, И память точки.
#
# wake_council() получил два НОВЫХ необязательных параметра:
#   window — уже прочитанное окно баров (тестер передаёт своё честное
#            окно по дате, чтобы не тянуть терминал повторно).
#   point  — шаг цены (нужен вместе с window для build_market_data).
# Живой режим (кнопка РЫНОК, window=None) — цена/бары тянутся сами
# через pull_bars, как раньше делала Искра.
#
# ЗАВИСИМОСТИ: применить ПОСЛЕ patch_twr_bolshoy_palec.py (нужен
# md["thumb_trade"]) и patch_tochka_zhiva.py (нужна proverit_tochku).
#
# ИДЕМПОТЕНТНОСТЬ: маркер COUNCIL_GATE_TROYNOY_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Биржа" / "council.py"
MARKER = "COUNCIL_GATE_TROYNOY_V1"


NEW_FUNCTION = '''

# ═══════════════════════════════════════════════════════════
# ''' + MARKER + ''' — дешёвая проверка триггеров Б/В (без LLM)
# ═══════════════════════════════════════════════════════════

def _deshyovaya_proverka_tochki(symbol: str, timeframe: str,
                                window=None, point=None) -> dict:
    """
    Код, без LLM. Строит md (переданным окном ИЛИ тянет бары сама —
    живой режим), спрашивает proverit_tochku() (TOCHKA_ZHIVA_V1) и,
    если точка жива, ищет ДВА дешёвых триггера на ЭТОМ баре:
      фрактал Ганса вне пасти (_hans_breakout, уже есть в hooks.py)
      Большой палец Авантюриста (md["thumb_trade"], TWR_BOLSHOY_PALEC_V1)

    Возвращает {"trigger": bool, "kind": "fractal"|"thumb"|None,
                "napravlenie": str|None, "tochka": {...}}.
    Пустой/недоступный md — честное "нет триггера", не ошибка.
    """
    from hooks import proverit_tochku, _hans_breakout
    from williams_core import build_market_data

    bars = window
    _point = point
    if bars is None:
        from mt5_feed import pull_bars
        bars, _point = pull_bars(symbol, timeframe, 300)

    if not bars or _point is None:
        return {"trigger": False, "kind": None, "napravlenie": None,
                "tochka": {"alive": False, "reason": "нет баров"}}

    md = build_market_data(bars, symbol=symbol, timeframe=timeframe,
                           point=_point)
    if not md:
        return {"trigger": False, "kind": None, "napravlenie": None,
                "tochka": {"alive": False, "reason": "пустой md"}}

    tochka = proverit_tochku(md)
    if not tochka.get("alive"):
        return {"trigger": False, "kind": None, "napravlenie": None,
                "tochka": tochka}

    # Триггер Б — фрактал Ганса пробит вне пасти на ЭТОМ баре
    hans_dir = _hans_breakout(md, bars)
    if hans_dir is not None:
        return {"trigger": True, "kind": "fractal",
                "napravlenie": hans_dir, "tochka": tochka}

    # Триггер В — Большой палец Авантюриста сработал на ЭТОМ баре
    thumb = md.get("thumb_trade", {}) or {}
    if thumb.get("triggered"):
        return {"trigger": True, "kind": "thumb",
                "napravlenie": thumb.get("direction"), "tochka": tochka}

    return {"trigger": False, "kind": None, "napravlenie": None,
            "tochka": tochka}

# ''' + MARKER + ''' - marker
'''


ANCHOR_SIGNATURE = '''def wake_council(symbol: str, timeframe: str,
                 on_event: Optional[Callable] = None) -> dict:'''

ANCHOR_SIGNATURE_REPLACEMENT = '''def wake_council(symbol: str, timeframe: str,
                 on_event: Optional[Callable] = None,
                 window=None, point=None) -> dict:'''


ANCHOR_GATE = '''    descent = ri.get("descent", {}) or {}
    if not descent.get("found"):
        _emit({"type": "council_idle",
               "why": "спуск не нашёл точку — Совет не собирается",
               "descent": descent})
        summary["idle"] = True
        return summary'''

ANCHOR_GATE_REPLACEMENT = '''    descent = ri.get("descent", {}) or {}
    _svezhy_spusk = bool(descent.get("found"))

    # ''' + MARKER + ''': Триггер А не сработал — пробуем Б/В.
    # Дешёвая проверка (без LLM): точка жива И (фрактал Ганса ИЛИ
    # Большой палец) прямо на ЭТОМ баре.
    _cheap = None
    if not _svezhy_spusk:
        _cheap = _deshyovaya_proverka_tochki(symbol, timeframe,
                                             window=window, point=point)

    if not _svezhy_spusk and not (_cheap and _cheap.get("trigger")):
        _tochka_info = (_cheap or {}).get("tochka", {})
        _emit({"type": "council_idle",
               "why": ("спуск не нашёл точку, точка не жива/триггера нет "
                      f"({_tochka_info.get('reason', '?')})"),
               "descent": descent, "tochka": _tochka_info})
        summary["idle"] = True
        return summary

    if not _svezhy_spusk and _cheap and _cheap.get("trigger"):
        print(f"[СОВЕТ] 🎯 Триггер {_cheap['kind']} на живой точке "
              f"(родилась: {_cheap['tochka'].get('reason','?')}) — "
              f"будим Совет БЕЗ свежего спуска Искры")
        _emit({"type": "council_triggered_by_point",
               "kind": _cheap["kind"], "napravlenie": _cheap["napravlenie"],
               "tochka": _cheap["tochka"]})'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    for anchor, name in [(ANCHOR_SIGNATURE, "сигнатура wake_council"),
                          (ANCHOR_GATE, "гейт по спуску")]:
        if anchor not in src:
            raise SystemExit(f"❌ якорь не найден ({name}) — файл разошёлся "
                              f"с ожидаемым, патч НЕ применён")

    src = src.replace(ANCHOR_SIGNATURE, ANCHOR_SIGNATURE_REPLACEMENT, 1)
    src = src.replace(ANCHOR_GATE, ANCHOR_GATE_REPLACEMENT, 1)

    # функцию-помощник вставляем перед wake_council (после ANCHOR_SIGNATURE
    # уже заменённой сигнатуры найти проще исходный маркер class docstring
    # начала функции — вставим прямо перед новой сигнатурой)
    src = src.replace(ANCHOR_SIGNATURE_REPLACEMENT,
                      NEW_FUNCTION.strip("\n") + "\n\n\n" + ANCHOR_SIGNATURE_REPLACEMENT,
                      1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_gate3")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
