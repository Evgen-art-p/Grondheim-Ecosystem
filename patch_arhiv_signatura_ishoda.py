# -*- coding: utf-8 -*-
"""
patch_arhiv_signatura_ishoda.py
════════════════════════════════════════════════════════════════════
АРХИВАРИУС ВСЕГДА ПИШЕТ «0 СЛУЧАЕВ» — НАЙДЕНА НАСТОЯЩАЯ ПРИЧИНА

БОЛЕЗНЬ: Архивариус (build_digest) ищет похожие случаи ПО СИГНАТУРЕ
сенсоров (t1_status, morj_status, panic_phase, fractal_valid) —
сравнивает entry.get(k) == v для каждого поля.

Но ДВЕ записи в Атлас несут РАЗНОЕ:
  • TRADER_REJECTED (_log_rejections) — несёт ПОЛНУЮ сигнатуру,
    но у неё НЕТ исхода (pnl) — сделки не было.
  • POSITION_CLOSED (_settle_positions) — несёт ИСХОД (pnl, pnl_r),
    но НЕ несёт сигнатуру ВООБЩЕ (только trader/reason/pnl/symbol/tf).

Единственные записи с исходом (закрытые сделки) физически не могут
совпасть ни с одним запросом сигнатуры — у них просто нет этих полей.
Поэтому `closed_trades` (сделки с известным исходом в выборке) всегда
0, `success_rate` всегда 0.0, и Архивариус честно говорит «0 случаев» —
даже после сотен реальных закрытых сделок.

ЛЕЧЕНИЕ: позиция УЖЕ хранит сигнатуру входа в `стол_входа` (вложенные
словари iskra/morj/panic/hans — видно в каждом логе МАЯКА). Разворачиваем
её в плоские поля при записи POSITION_CLOSED — теми же именами, что
ждёт build_digest. Семантически даже вернее, чем у REJECTED: это
сигнатура НА МОМЕНТ ВХОДА, а не на момент закрытия.

ИДЕМПОТЕНТЕН (маркер ARKHIV_SIGNATURA_ISHODA_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_arhiv_signatura_ishoda.py
"""
import io
import sys
from pathlib import Path

MARKER = "ARKHIV_SIGNATURA_ISHODA_V1"


def find_hooks() -> Path:
    for p in (Path("Биржа") / "hooks.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "hooks.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден hooks.py — запусти из корня")
    sys.exit(1)


def main():
    path = find_hooks()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src

    old = (
        '        _write_atlas({\n'
        '            "event":       "POSITION_CLOSED",\n'
        '            "trader":      pos.get("trader"),\n'
        '            "close_reason": reason,\n'
        '            "pnl":         pnl_price,\n'
        '            "pnl_r":       pnl_r,\n'
        '            "symbol":      symbol,\n'
        '            "timeframe":   timeframe,\n'
        '        })\n'
    )
    if old not in src:
        print("[ПАТЧ] ✗ якорь записи POSITION_CLOSED не найден — "
              "покажи строки вокруг _write_atlas событие POSITION_CLOSED")
        sys.exit(2)

    new = (
        '        # ' + MARKER + ': сигнатура сенсоров НА МОМЕНТ ВХОДА,\n'
        '        # разворачиваем из "стол_входа" (уже хранится на позиции) —\n'
        '        # без неё закрытые сделки никогда не совпадали ни с одним\n'
        '        # запросом Архивариуса (у них не было полей для сравнения).\n'
        '        _svh = pos.get("стол_входа") or {}\n'
        '        _write_atlas({\n'
        '            "event":       "POSITION_CLOSED",\n'
        '            "trader":      pos.get("trader"),\n'
        '            "close_reason": reason,\n'
        '            "pnl":         pnl_price,\n'
        '            "pnl_r":       pnl_r,\n'
        '            "symbol":      symbol,\n'
        '            "timeframe":   timeframe,\n'
        '            "t1_status":     (_svh.get("iskra") or {}).get("t1_status"),\n'
        '            "morj_status":   (_svh.get("morj") or {}).get("morj_status"),\n'
        '            "panic_phase":   (_svh.get("panic") or {}).get("panic_phase"),\n'
        '            "fractal_valid": (_svh.get("hans") or {}).get("fractal_valid"),\n'
        '        })\n'
    )
    src = src.replace(old, new, 1)

    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ правка ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_arhiv_signatura")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Закрытые сделки теперь несут сигнатуру сенсоров.")
    print("[ПАТЧ]    Архивариус наконец сможет находить случаи с исходом —")
    print("[ПАТЧ]    не только отказы. Старые записи в atlas_trading.jsonl")
    print("[ПАТЧ]    без сигнатуры останутся неучтёнными — это хвост,")
    print("[ПАТЧ]    новые сделки будут матчиться честно.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
