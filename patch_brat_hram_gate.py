# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ВРАТА ХРАМА — оживить кнопку в кабинете Брата         ║
║  Узел 1 стройки нового города · Grondheim-Ecosystem         ║
║                                                              ║
║  Что делает:                                                 ║
║    1. Раздаёт веб-Храм статикой:                            ║
║       app.add_static_files("/hram", "GRONDHEIM_CITY/Hexagon")║
║    2. Кнопка «Храм» → ui.navigate.to("/hram/index.html")    ║
║       Просто перекидывает на страницу Храма. Назад — браузер.║
║                                                              ║
║  Сам Храм (Hexagon) НЕ трогаем — ни строчки.                ║
║  Связей со старым городом (-2) НЕТ. Всё внутри нового.       ║
║                                                              ║
║  Идемпотентно: повторный запуск ничего не дублирует.        ║
║  `шесть·проверено·до·корня`                                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path("ui_brat.py")
MARK = "# PATCH_HRAM_GATE_APPLIED"


def fail(msg: str):
    print(f"[ПАТЧ] ✗ {msg}")
    sys.exit(1)


def main():
    if not TARGET.exists():
        fail(f"не найден {TARGET} — запускай из корня репо Grondheim-Ecosystem")

    src = TARGET.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ] ⊙ Врата Храма уже оживлены — пропускаю (идемпотентно)")
        return

    # ── Якорь 1: блок раздачи статики /brat-static ──
    # К нему добавляем раздачу Храма /hram (тем же приёмом, рядом)
    static_anchor = 'app.add_static_files("/brat-static", str(STATIC_DIR))'
    if static_anchor not in src:
        fail("якорь раздачи /brat-static не найден — файл изменился, покажи свежий")

    static_block_old = (
        '    try:\n'
        '        if STATIC_DIR.exists():\n'
        '            from nicegui import app\n'
        '            app.add_static_files("/brat-static", str(STATIC_DIR))\n'
        '    except Exception:\n'
        '        pass\n'
    )
    if static_block_old not in src:
        fail("блок try/except раздачи статики не совпал дословно — покажи свежий файл")

    static_block_new = (
        static_block_old +
        '\n'
        '    # ── PATCH_HRAM_GATE: раздаём веб-Храм статикой того же города ──\n'
        '    # Храм (Hexagon) живёт по адресу /hram на том же порту.\n'
        '    # Ни строчки в самом Храме не трогаем — только даём дверь.\n'
        '    try:\n'
        '        from nicegui import app as _app_hram\n'
        '        _hram_dir = Path("GRONDHEIM_CITY/Hexagon")\n'
        '        if _hram_dir.exists():\n'
        '            _app_hram.add_static_files("/hram", str(_hram_dir))\n'
        '    except Exception:\n'
        '        pass\n'
    )
    src = src.replace(static_block_old, static_block_new, 1)

    # ── Якорь 2: пустая кнопка «Храм» ──
    btn_old = 'ui.button("Храм").props("flat").classes("brat-gate")'
    if src.count(btn_old) != 1:
        fail(f"кнопка «Храм» встречается {src.count(btn_old)}× — нужна ровно 1")

    btn_new = (
        'ui.button("Храм",\n'
        '                                  on_click=lambda: ui.navigate.to("/hram/index.html")\n'
        '                                  ).props("flat").classes("brat-gate")  # PATCH_HRAM_GATE'
    )
    src = src.replace(btn_old, btn_new, 1)

    # ── Метка модуля (надёжный якорь из docstring) ──
    mark_anchor = 'КАБИНЕТ БРАТА'
    if mark_anchor in src:
        src = src.replace(
            mark_anchor,
            f'КАБИНЕТ БРАТА  {MARK}',
            1,
        )
    else:
        # запасной якорь — первая строка
        src = src.replace('# ui_brat.py', f'# ui_brat.py  {MARK}', 1)

    TARGET.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ Врата Храма оживлены")
    print("       • раздача:  /hram → GRONDHEIM_CITY/Hexagon (статика того же города)")
    print("       • кнопка:   «Храм» → переход на /hram/index.html")
    print("       • Храм сам — не тронут, ни строчки")
    print("       • связей со старым городом нет")
    print()
    print("[ПАТЧ] Проверка: python main.py → открой /brat → жми «Храм»")
    print("       Должно перекинуть на страницу Храма (экран «ищи...»).")
    print("       Назад — кнопкой браузера.")


if __name__ == "__main__":
    main()
