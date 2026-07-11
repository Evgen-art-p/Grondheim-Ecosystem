# -*- coding: utf-8 -*-
"""
patch_tester_closures_pnl_path_v1.py
────────────────────────────────────────────────────────────────────
ЧИНИТ: «сделки не закрывает» — в кабинете Биржи открытия (🟢 ОТКРЫТА)
идут, а закрытий (🔴 ЗАКРЫТА) нет НИКОГДА.

КОРЕНЬ (дрейф путей после переезда в новый город):
  • hooks._settle_positions ПИШЕТ закрытия в
        _REPO / GRONDHEIM_CITY / Биржа / данные / trading_pnl.jsonl   (PNL_PATH)
  • tester_express._read_last_closures ЧИТАЛ ленту из
        economy/data/trading_pnl.jsonl   (старый относительный путь студии)

  В старой студии приложение стартовало с CWD = studio/, и относительный
  economy/data/... честно резолвился в тот же файл. В новом городе CWD =
  корень репы — этот относительный путь указывает в НИКУДА (файла нет,
  туда никто не пишет). Поэтому лента закрытий всегда пустая.

  Позиции при этом РЕАЛЬНО закрываются: settle отрабатывает, в консоли
  идут строки «[SETTLE] 🛑 ... закрыт» / «[SETTLE] 🔔 ...», trading_state
  обновляется. Слеп только фид кабинета.

ЛЕЧЕНИЕ (DRY, чтоб пути не разъехались снова):
  _read_last_closures импортирует PNL_PATH из hooks и читает ИМЕННО его.
  Один источник правды — hooks.PNL_PATH.

Идемпотентно. Делает .bak рядом. Запускать из КОРНЯ репы:
    python patch_tester_closures_pnl_path_v1.py
"""
from __future__ import annotations
import sys
from pathlib import Path

MARKER = "TESTER_PNL_PATH_FROM_HOOKS_V1"
TARGET = Path("Биржа") / "tester_express.py"

OLD = (
    "    from pathlib import Path as _P\n"
    "    import json as _j\n"
    "    p = _P('economy/data/trading_pnl.jsonl')\n"
)
NEW = (
    "    from pathlib import Path as _P\n"
    "    import json as _j\n"
    "    from hooks import PNL_PATH   # " + MARKER + ": читаем ТОТ ЖЕ файл, что пишет settle\n"
    "    p = _P(PNL_PATH)\n"
)


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти скрипт из КОРНЯ репы "
              f"(там, где папка «Биржа»).")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if OLD not in src:
        print("✗ не нашёл ожидаемый блок _read_last_closures со старым путём "
              "'economy/data/trading_pnl.jsonl'.")
        print("  Возможно, код уже правился вручную. Проверь функцию "
              "_read_last_closures в Биржа/tester_express.py — она должна "
              "читать hooks.PNL_PATH, а не относительный economy/data/...")
        return 2

    # бэкап рядом
    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")
    else:
        print(f"• бэкап уже был: {bak} (не перезаписываю)")

    patched = src.replace(OLD, NEW, 1)
    TARGET.write_text(patched, encoding="utf-8")
    print(f"✓ {TARGET}: _read_last_closures теперь читает hooks.PNL_PATH.")
    print("  Лента закрытий (🔴 ЗАКРЫТА) снова смотрит в тот же файл, "
          "куда settle пишет.")
    print(f"  Маркер идемпотентности: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
