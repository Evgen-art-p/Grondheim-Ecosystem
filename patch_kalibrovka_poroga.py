#!/usr/bin/env python3
# patch_kalibrovka_poroga.py
# ─────────────────────────────────────────────────────────────
# KALIBROVKA_POROGA_V1 · 20.07
#
# ТЗ Студии «Шесть Пальцев» по факту с реального золота (24811 баров,
# средняя жизнь точки 2.3 бара — критически мало): TWR убил 387 точек,
# структурный слом — 91, подпитка спасла всего 13. Два калиброванных
# исправления:
#
#   1. СЛОМ СТРОГО ПО CLOSE (не по High/Low). Дикий рынок часто колет
#      уровень тенью бара и закрывается обратно — раньше такой прокол
#      мгновенно убивал честную структуру. Теперь смерть засчитывается
#      только если ЗАКРЫТИЕ бара ушло за zero_point_price против
#      направления — тень (High/Low) больше не считается сломом.
#
#   2. TWR ТРЕБУЕТ 3 БАРА НЕЙТРАЛИ ПОДРЯД (не один). Счётчик
#      neutral_bars_count живёт в trading_state["iskra"] — считает,
#      сколько баров подряд Ритм (5/13/34) держит нейтральное
#      состояние. Смерть — только когда счётчик дошёл до 3. Любой
#      бар, где Ритм вышел из нейтрали, сбрасывает счётчик в ноль.
#
# ЗАВИСИМОСТЬ: применить ПОСЛЕ patch_tochka_napravlenie.py (якоря
# ниже — это текст ПОСЛЕ того патча, с "direction" в возвратах).
#
# ИДЕМПОТЕНТНОСТЬ: маркер KALIBROVKA_POROGA_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Биржа" / "hooks.py"
MARKER = "KALIBROVKA_POROGA_V1"

_TWR_NEUTRAL_KILL_BARS = 3   # ТЗ Студии: "3-4 бара подряд" — беру нижнюю
                              # границу диапазона, легко подвинуть одной
                              # константой, если 3 окажется всё ещё мало


# ── якорь 1: цена — нужен close, не только low/high ──

ANCHOR_PRICE = '''    price = md.get("price", {}) or {}
    low   = price.get("low")
    high  = price.get("high")
    twr   = md.get("twr", {}) or {}'''

REPLACEMENT_PRICE = '''    price = md.get("price", {}) or {}
    low   = price.get("low")
    high  = price.get("high")
    close = price.get("close")   # ''' + MARKER + ''': слом — строго по Close
    twr   = md.get("twr", {}) or {}'''


# ── якорь 2: структурный слом — переводим с low/high на close ──

ANCHOR_SLOM = '''    # ── 2. структурный слом (пробой БЕЗ подтверждения — не подпитка) ──
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
                "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1'''

REPLACEMENT_SLOM = '''    # ── 2. структурный слом — СТРОГО ПО CLOSE (''' + MARKER + '''):
    # тень (High/Low) может кольнуть уровень и вернуться — это шум
    # дикого рынка, не слом структуры. Слом — только если ЗАКРЫТИЕ
    # бара ушло за zero_point_price против направления точки.
    slomana = False
    if napr == "BULL" and close is not None and close < zp:
        slomana = True
    elif napr == "BEAR" and close is not None and close > zp:
        slomana = True
    if slomana:
        isk["alive"] = False
        isk["neutral_bars_count"] = 0   # ''' + MARKER + ''': точка умерла — счётчик обнулить
        save_trading_state(tstate)
        return {"alive": False,
                "reason": f"структурный слом (close): цена закрылась за {zp}",
                "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1'''


# ── якорь 3: TWR — вводим счётчик подряд-нейтральных баров ──

ANCHOR_TWR = '''    # ── 3. TWR нейтрален (импульс угас) ──
    if twr.get("neutral") is True:
        isk["alive"] = False
        save_trading_state(tstate)
        return {"alive": False,
                "reason": "TWR нейтрален — ритм угас во флэте",
                "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1

    return {"alive": True, "reason": "жива", "changed": False, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1'''

REPLACEMENT_TWR = '''    # ── 3. TWR нейтрален — требует ''' + str(_TWR_NEUTRAL_KILL_BARS) + ''' БАРА ПОДРЯД
    # (''' + MARKER + '''): один нейтральный бар — обычная заминка,
    # не повод хоронить структуру. Смерть — только если Ритм держит
    # нейтраль ''' + str(_TWR_NEUTRAL_KILL_BARS) + ''' бара(ов) подряд. Любой выход из нейтрали
    # (свежий строй появился) — счётчик сбрасывается в ноль.
    if twr.get("neutral") is True:
        _n = int(isk.get("neutral_bars_count", 0) or 0) + 1
        isk["neutral_bars_count"] = _n
        if _n >= ''' + str(_TWR_NEUTRAL_KILL_BARS) + ''':
            isk["alive"] = False
            isk["neutral_bars_count"] = 0
            save_trading_state(tstate)
            return {"alive": False,
                    "reason": f"TWR нейтрален {_n} бар(а) подряд — ритм угас во флэте",
                    "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1
        save_trading_state(tstate)
        return {"alive": True,
                "reason": f"TWR нейтрален {_n}/''' + str(_TWR_NEUTRAL_KILL_BARS) + ''' — ещё жива, считаю",
                "changed": False, "direction": napr}
    else:
        if isk.get("neutral_bars_count"):
            isk["neutral_bars_count"] = 0   # строй вернулся — счётчик сброшен
            save_trading_state(tstate)

    return {"alive": True, "reason": "жива", "changed": False, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    for anchor, name in [(ANCHOR_PRICE, "блок price/low/high/twr"),
                          (ANCHOR_SLOM, "структурный слом"),
                          (ANCHOR_TWR, "TWR-проверка")]:
        if anchor not in src:
            raise SystemExit(f"❌ якорь не найден ({name}) — файл разошёлся "
                              f"с ожидаемым (наложен ли patch_tochka_napravlenie.py?), "
                              f"патч НЕ применён")

    src = src.replace(ANCHOR_PRICE, REPLACEMENT_PRICE, 1)
    src = src.replace(ANCHOR_SLOM, REPLACEMENT_SLOM, 1)
    src = src.replace(ANCHOR_TWR, REPLACEMENT_TWR, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_kalibrovka")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён (TWR-порог: {_TWR_NEUTRAL_KILL_BARS} бара подряд, "
          f"слом: строго по Close)")


if __name__ == "__main__":
    main()
