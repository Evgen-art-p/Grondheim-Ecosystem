# -*- coding: utf-8 -*-
# patch_vasily_ispolnitel_watch_v1.py
# ─────────────────────────────────────────────────────────────
# VASILY_NABLYUDENIE_V1 · Патч 3 из 3 — ИСПОЛНИТЕЛЬ ДОНОСИТ ЗАСАДУ
#
# Патч 2 построил приёмник засады в hooks._persist_trading_state:
# он ищет в execution_log записи с action=="WATCH" и magic==100003.
# Но Исполнитель их туда не кладёт: _build_execution_log_facts несёт
# только verdict/direction/entry/stop, БЕЗ action и БЕЗ watch_opora.
# Васин WATCH сейчас утонул бы молча.
#
# Этот патч учит руку-факты Исполнителя доносить два поля для Васи:
#   action      — чтобы приёмник отличил WATCH от ENTER;
#   watch_opora — координата опоры засады (иначе засада пуста).
#
# Защита чисел не нарушена: watch_opora — подпись трейдера (из табло),
# как entry/stop. Мы её НЕ выдумываем, а прокидываем как есть.
#
# Идемпотентность: маркер VASILY_ISP_WATCH_V1. ast.parse перед записью.
# Запуск: python patch_vasily_ispolnitel_watch_v1.py   (из корня репо)
# ─────────────────────────────────────────────────────────────
from pathlib import Path
import ast
import sys
import shutil
from datetime import datetime

REPO = Path(__file__).resolve().parent
BRAIN = (REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
         / "слоты" / "исполнитель" / "мозг.py")
MARKER = "VASILY_ISP_WATCH_V1"


def fail(msg):
    print(f"✗ {msg}")
    return 1


def main():
    if not BRAIN.exists():
        return fail(f"не нашёл мозг Исполнителя: {BRAIN}\n"
                    f"  запусти из КОРНЯ репо")

    src = BRAIN.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — мозг Исполнителя не трогаю")
        return 0

    # ═══════════════════════════════════════════════════════════
    # ВРЕЗКА: _build_execution_log_facts — добавить action и watch_opora.
    # Якорь — тело словаря лога (уникальная строка "status": ...).
    # ═══════════════════════════════════════════════════════════
    ankor = '''        log.append({
            "trader":  TRADER_NAME[key],
            "magic":   MAGIC[key],
            "verdict": "APPROVED" if approved else "REJECTED",
            "direction": v.get("direction") if approved else None,
            "entry":   v.get("entry") if approved else None,
            "stop":    v.get("stop") if approved else None,
            "lot":     v.get("lot") if approved else None,
            "status":  "PAPER" if approved else "SKIPPED",
            "pnl":     None,
        })'''

    if ankor not in src:
        return fail("якорь не найден (тело _build_execution_log_facts). "
                    "Файл изменился после a34e858 — патч НЕ применён.")

    zamena = '''        # VASILY_ISP_WATCH_V1: засада Консерватора — своя природа.
        # WATCH не APPROVED и не REJECTED: трейдер назвал координаты и
        # ждёт созревания структуры. Доносим action + опору, чтобы
        # приёмник (hooks._persist_trading_state) родил WATCHING.
        _action = (v.get("action") or "").upper().strip()
        _is_watch = (_action == "WATCH")
        log.append({
            "trader":  TRADER_NAME[key],
            "magic":   MAGIC[key],
            "action":  _action or None,
            "verdict": "APPROVED" if approved else "REJECTED",
            "direction": (v.get("direction")
                          if (approved or _is_watch) else None),
            "entry":   (v.get("entry") if (approved or _is_watch) else None),
            "stop":    (v.get("stop") if (approved or _is_watch) else None),
            "lot":     (v.get("lot") if (approved or _is_watch) else None),
            # координата засады — только у Васи, только при WATCH
            "watch_opora": (v.get("watch_opora") if _is_watch else None),
            "status":  "PAPER" if (approved or _is_watch) else "SKIPPED",
            "pnl":     None,
        })'''

    src = src.replace(ankor, zamena, 1)

    # ── маркер в конец файла ──
    src = src.rstrip() + f"\n\n# {MARKER} — маркер идемпотентности\n"

    # ═══ ast.parse ДО записи ═══
    try:
        ast.parse(src)
    except SyntaxError as e:
        return fail(f"ast.parse НЕ прошёл — НЕ пишу файл.\n  {e}")

    bak = BRAIN.with_suffix(
        ".py.bak_vasily_watch_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(BRAIN, bak)
    BRAIN.write_text(src, encoding="utf-8")

    print(f"✓ VASILY_ISP_WATCH_V1 вписан в мозг Исполнителя")
    print(f"  бэкап: {bak.name}")
    print(f"  Исполнитель теперь доносит action + watch_opora для засады Васи.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
