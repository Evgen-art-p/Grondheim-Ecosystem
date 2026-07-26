# -*- coding: utf-8 -*-
# ARKHIV_MAIN_ROUTE_V1
"""
ARKHIV_MAIN_ROUTE_V1 — регистрирует кабинет Архива Города в main.py:
  1) добавляет "Архив" в список подпапок для sys.path (рядом с
     "Биржа", "Академия", "Маяк")
  2) добавляет страницу /arkhiv (по образцу /akademia)

Перед запуском положи в репо:
    Архив/khranitel_arkhiva.py
    Архив/ui_arkhiv.py

Идемпотентно: если /arkhiv уже зарегистрирован — патч молча выходит.
Бэкап .bak делается один раз.

Запуск из корня репо:  python patch_arkhiv_main_route.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
MAIN_PY = ROOT / "main.py"
MARKER = "ARKHIV_MAIN_ROUTE_V1"


def main():
    if not MAIN_PY.exists():
        print(f"⚠ не найден {MAIN_PY} — запускай из корня репо")
        sys.exit(1)

    text = MAIN_PY.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже применён — патч не нужен")
        return

    if not (ROOT / "Архив" / "ui_arkhiv.py").exists():
        print("⚠ не найден Архив/ui_arkhiv.py — сначала положи файлы модуля,")
        print("  потом накатывай этот патч")
        sys.exit(1)

    # ── 1) sys.path: добавить "Архив" ────────────────────────
    old_tuple_variants = [
        'for _sub in ("Брат", "жители", "ГОРОД", "Биржа", "Академия", "Маяк"):',
        'for _sub in ("Брат", "жители", "ГОРОД", "Биржа", "Академия"):',
    ]
    old_tuple = next((v for v in old_tuple_variants if v in text), None)
    if old_tuple is None:
        print("⚠ не нашёл строку sys.path в main.py — правь руками:")
        print('  добавь "Архив" в кортеж _sub')
        sys.exit(1)
    if "Архив" not in old_tuple:
        new_tuple = old_tuple[:-2] + ', "Архив"):'
        text = text.replace(old_tuple, new_tuple, 1)

    # ── 2) страница /arkhiv — блок после /akademia ───────────
    anchor = (
        "from ui_akademia import page_akademia\n\n"
        "@ui.page(\"/akademia\")\n"
        "def _akademia():\n"
        "    page_akademia()\n"
    )
    if anchor not in text:
        print("⚠ не нашёл блок регистрации /akademia в main.py — структура")
        print("  main.py изменилась. Добавь страницу /arkhiv руками:")
        print('  from ui_arkhiv import page_arkhiv')
        print('  @ui.page("/arkhiv")')
        print('  def _arkhiv():')
        print('      page_arkhiv()')
        sys.exit(1)

    blok = (
        anchor + "\n\n"
        f"# ── АРХИВ ГОРОДА — Хранитель (сейчас Лока) ── {MARKER}\n"
        "# Самостоятельный модуль, как Академия и Биржа.\n"
        "from ui_arkhiv import page_arkhiv\n\n"
        "@ui.page(\"/arkhiv\")\n"
        "def _arkhiv():\n"
        "    page_arkhiv()\n"
    )
    text = text.replace(anchor, blok, 1)

    bak = MAIN_PY.with_suffix(MAIN_PY.suffix + ".bak")
    if not bak.exists():
        bak.write_text(MAIN_PY.read_text(encoding="utf-8"), encoding="utf-8")
    MAIN_PY.write_text(text, encoding="utf-8")
    print(f"✓ main.py: страница /arkhiv зарегистрирована (бэкап: {bak})")
    print(f"# {MARKER}")


if __name__ == "__main__":
    main()

# ARKHIV_MAIN_ROUTE_V1 — маркер идемпотентности
