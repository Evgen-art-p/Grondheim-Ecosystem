# -*- coding: utf-8 -*-
"""
patch_tester_settle_tail_v1.py
────────────────────────────────────────────────────────────────────
ЧИНИТ (§8 разбора): последняя из N пойманных сделок не закрывается
в прогоне. Тестер ловит n_signals срабатываний; последняя сделка
открывается на ПОСЛЕДНЕМ кандидате, и цикл рвётся по `caught >= n_signals`
РАНЬШЕ, чем рынок дошёл до её стопа/колокола. Досеттливать её уже нечем —
следующего кандидата нет. Итог: «ловлю 4» даёт 4 открытия и до 3 закрытий,
хвостовая висит открытой по краю окна.

ЛЕЧЕНИЕ: после цикла обработки кандидатов (до finally) — ДОБОР ХВОСТА.
Ведём открытые позиции бар-за-баром от последнего кандидата вперёд, пока
все не закроются (стоп / exit_bell / воля), либо пока не кончится история.
Используем те же _settle_bar (полное окно 300) и _feed_check_closures, что
и основной цикл — та же физика, та же лента. _settle_bar дёшев на пустом
столе; ранний выход по _table_snapshot() гасит лишние прокаты.

ЗАВИСИМОСТЬ: сам ФАКТ закрытия (state/pnl/Атлас) этот патч обеспечивает
независимо. ВИДИМОСТЬ «🔴 ЗАКРЫТА» в кабинете даёт patch_tester_closures_
pnl_path_v1 (лента читает тот же файл, что пишет settle). Применяй оба —
они дополняют друг друга.

Идемпотентно. Маркер TESTER_SETTLE_TAIL_V1. Бэкап рядом (.bak).
Запуск из КОРНЯ репы (Windows/PowerShell):
    python patch_tester_settle_tail_v1.py
"""
from __future__ import annotations
import sys
from pathlib import Path

MARKER = "TESTER_SETTLE_TAIL_V1"
TARGET = Path("Биржа") / "tester_express.py"

# Якорь: последняя строка ветки else цикла кандидатов + пустая + finally.
OLD = (
    '                f"живьём судит строже — это её право. Честный ответ кухни.")\n'
    '\n'
    '    finally:'
)

TAIL = (
    '                f"живьём судит строже — это её право. Честный ответ кухни.")\n'
    '\n'
    '        # ' + MARKER + ' · Брат + Шеф · ХВОСТ СЕССИИ\n'
    '        # Последняя из N пойманных сделок открывается на последнем\n'
    '        # кандидате, а цикл рвётся по n_signals раньше, чем рынок дошёл\n'
    '        # до её стопа/колокола. Досеттливаем: ведём открытые позиции\n'
    '        # бар-за-баром от последнего кандидата вперёд, пока все не\n'
    '        # закроются (или пока не кончится история). Физика и лента — те\n'
    '        # же, что в основном цикле. _settle_bar дёшев на пустом столе.\n'
    '        if _table_snapshot():\n'
    '            out("")\n'
    '            out("🔚 Досеттливаю хвост: веду открытые позиции до закрытия...")\n'
    '            for _b in range(_last_settled + 1, total):\n'
    '                _settle_bar(bars_all[max(0, _b - 299):_b + 1],\n'
    '                            symbol, timeframe, point)\n'
    '                _last_settled = _b\n'
    '                _feed_check_closures(_b)\n'
    '                if not _table_snapshot():\n'
    '                    out(f"✓ хвост закрыт на баре {_b}.")\n'
    '                    break\n'
    '            else:\n'
    '                out(f"⚠️ хвост докатан до конца истории (бар {total - 1}) — "\n'
    '                    f"часть позиций не встретила стоп/колокол в этом окне.")\n'
    '\n'
    '    finally:'
)


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти из КОРНЯ репы "
              f"(там, где папка «Биржа»).")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if OLD not in src:
        print("✗ не нашёл точку вставки (ветка else цикла кандидатов перед "
              "finally).")
        print("  Возможно, run_tester уже правился вручную. Проверь конец "
              "цикла `for idx, (i, side) in enumerate(candidates)` в "
              "Биржа/tester_express.py — добор хвоста ставится сразу после "
              "него, до finally.")
        return 2

    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")
    else:
        print(f"• бэкап уже был: {bak} (не перезаписываю)")

    TARGET.write_text(src.replace(OLD, TAIL, 1), encoding="utf-8")
    print(f"✓ {TARGET}: добавлен добор хвоста сессии — последняя сделка "
          f"закрывается в прогоне.")
    print(f"  Маркер идемпотентности: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
