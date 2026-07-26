# -*- coding: utf-8 -*-
# MAYAK_MODULE_V1
"""
MAYAK_MODULE_V1 — Маяк перестаёт быть парой файлов внутри ГОРОД/ и
становится отдельным модулем, как Биржа и Академия:

    Маяк/
        mayak.py       (переехал из ГОРОД/mayak.py)
        ui_mayak.py    (переехал из ГОРОД/ui_mayak.py)
        ui_mayak.py.bak  (если был — переезжает вместе с ui_mayak.py)
        города/        (пусто, задел на будущее — с README)
        острова/       (пусто, задел на будущее — с README)

Зависимости не трогаем: ui_mayak.py тянет gnezda.py и rezidenty.py —
они остаются в ГОРОД/, потому что ГОРОД/ всё равно в sys.path (main.py),
и "import gnezda" / "import rezidenty" продолжат резолвиться без правок
внутри самих файлов.

main.py правится в одном месте: "Маяк" добавляется в список подпапок,
которые main.py кладёт в sys.path — по образцу, как там уже лежат
"Брат", "жители", "ГОРОД", "Биржа", "Академия".

Идемпотентно: если Маяк/mayak.py уже существует — патч молча выходит.
Бэкап .bak по main.py делается один раз, при первом применении.

Запуск из корня репо:  python patch_mayak_module_v1.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
GOROD = ROOT / "ГОРОД"
MAYAK = ROOT / "Маяк"
MAIN_PY = ROOT / "main.py"

MARKER = "MAYAK_MODULE_V1"

FILES_TO_MOVE = ["mayak.py", "ui_mayak.py", "ui_mayak.py.bak"]

SUBDIRS_WITH_README = {
    "города": (
        "# Города\n\n"
        "Задел на будущее: другие города Грондхейма, до которых достаёт\n"
        "свет Маяка. Пока пусто — наполняется по мере роста мира.\n"
    ),
    "острова": (
        "# Острова\n\n"
        "Задел на будущее: отдельные острова/спутники — миры за пределами\n"
        "основного Грондхейма, но всё ещё в луче Маяка. Пока пусто.\n"
    ),
}


def main():
    if (MAYAK / "mayak.py").exists():
        print(f"✓ {MARKER} уже применён — Маяк/mayak.py на месте, патч не нужен")
        return

    if not GOROD.exists():
        print(f"⚠ не найдена папка {GOROD} — запускай из корня репо")
        sys.exit(1)
    if not MAIN_PY.exists():
        print(f"⚠ не найден {MAIN_PY} — запускай из корня репо")
        sys.exit(1)

    missing = [f for f in FILES_TO_MOVE[:2] if not (GOROD / f).exists()]
    if missing:
        print(f"⚠ не нашёл в {GOROD}: {missing} — структура изменилась с момента патча")
        sys.exit(1)

    # ── 1) создать Маяк/ и подпапки с README ─────────────────────
    MAYAK.mkdir(exist_ok=True)
    for name, readme_text in SUBDIRS_WITH_README.items():
        d = MAYAK / name
        d.mkdir(exist_ok=True)
        readme = d / "README.md"
        if not readme.exists():
            readme.write_text(readme_text, encoding="utf-8")
    print(f"✓ создано: {MAYAK} (+ города/, острова/ с README)")

    # ── 2) перенести файлы (git mv по смыслу — просто move) ─────
    for fname in FILES_TO_MOVE:
        src = GOROD / fname
        if not src.exists():
            continue  # ui_mayak.py.bak — не у всех есть, это нормально
        dst = MAYAK / fname
        shutil.move(str(src), str(dst))
        print(f"✓ перенесено: {src} -> {dst}")

    # ── 3) main.py: добавить "Маяк" в список подпапок sys.path ──
    text = MAIN_PY.read_text(encoding="utf-8")
    old_tuple = 'for _sub in ("Брат", "жители", "ГОРОД", "Биржа", "Академия"):'
    new_tuple = 'for _sub in ("Брат", "жители", "ГОРОД", "Биржа", "Академия", "Маяк"):'
    if old_tuple not in text:
        print("⚠ не нашёл строку sys.path в main.py — структура main.py изменилась,")
        print("  файлы уже перенесены, но main.py правь руками:")
        print(f'  добавь "Маяк" в кортеж _sub рядом с "ГОРОД", "Биржа", "Академия"')
        sys.exit(1)
    bak = MAIN_PY.with_suffix(MAIN_PY.suffix + ".bak")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    text = text.replace(old_tuple, new_tuple, 1)
    MAIN_PY.write_text(text, encoding="utf-8")
    print(f"✓ main.py: \"Маяк\" добавлен в sys.path (бэкап: {bak})")

    print()
    print("Готово. gnezda.py и rezidenty.py остались в ГОРОД/ — это нормально,")
    print("ui_mayak.py их видит через sys.path, как и раньше.")
    print(f"# {MARKER}")


if __name__ == "__main__":
    main()

# MAYAK_MODULE_V1 — маркер идемпотентности
