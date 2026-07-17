# -*- coding: utf-8 -*-
"""
patch_ubrat_nadpis_birzha.py
════════════════════════════════════════════════════════════════════
УБРАТЬ НАДПИСЬ «БИРЖА · СОВЕТ» — НАЕЗЖАЛА НА КНОПКУ ОЧИСТКИ

Шеф (по скрину): кнопка «🧹 ОЧИСТИТЬ» заехала на надпись «📊 БИРЖА ·
СОВЕТ» в тулбаре. Предложил либо перенести надпись наверх к пузырькам,
либо убрать вовсе.

РЕШЕНИЕ (простой путь, наименьший риск): убрать надпись целиком —
страница и так подписана вкладками (РЫНОК/РЕАЛ/ТЕСТЕР) и хедером с
пузырьками состава Совета, отдельный заголовок посередине избыточен.

ИДЕМПОТЕНТЕН (маркер UBRAT_NADPIS_BIRZHA_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_ubrat_nadpis_birzha.py
"""
import io
import sys
from pathlib import Path

MARKER = "UBRAT_NADPIS_BIRZHA_V1"


def find_ui_torg() -> Path:
    for p in (Path("Биржа") / "ui_torg.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "ui_torg.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден ui_torg.py — запусти из корня")
    sys.exit(1)


def main():
    path = find_ui_torg()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src

    old = (
        '                    with ui.element("div").style("display:flex; '
        'gap:6px; align-items:center; justify-content:center;"):\n'
        '                        ui.label("📊 БИРЖА · СОВЕТ").style(\n'
        '                            "color:rgba(0,204,255,0.7); font-weight:800; '
        'font-size:0.8rem; letter-spacing:0.08em;")\n'
    )
    if old not in src:
        print("[ПАТЧ] ✗ якорь надписи не найден — файл изменён?")
        sys.exit(2)

    new = (
        '                    # ' + MARKER + ': надпись «БИРЖА · СОВЕТ» убрана —\n'
        '                    # наезжала на кнопку ОЧИСТИТЬ, и была избыточна\n'
        '                    # (страница подписана вкладками и хедером Совета).\n'
    )
    src = src.replace(old, new, 1)

    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ правка ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_ubrat_nadpis")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Надпись убрана. Тулбар посвободнее, кнопка не наезжает.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
