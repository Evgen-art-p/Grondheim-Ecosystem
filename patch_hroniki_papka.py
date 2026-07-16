# -*- coding: utf-8 -*-
"""
patch_hroniki_papka.py
════════════════════════════════════════════════════════════════════
ОТЧЁТЫ ТЕСТЕРА → В ОТДЕЛЬНУЮ ПАПКУ «хроники»

БОЛЕЗНЬ (шеф, скрин): tester_express.py пишет отчёт .with_name() —
РЯДОМ С CSV, прямо в test_data. В итоге входные котировки (CSV) и
выходные отчёты (_tester_*.txt) валяются в одной куче.

ЛЕЧЕНИЕ: отчёты уходят в Биржа/хроники/ (создаётся автоматически).
test_data остаётся чистой — только исходные котировки.
Имя файла прежнее: {symbol}_tester_{ГГГГММДД_ЧЧММСС}.txt
Медийщики будущего берут летопись из папки хроники — отдельной,
не замусоренной исходниками.

Путь: _HERE (папка Биржа, где лежит tester_express.py) / "хроники".

ИДЕМПОТЕНТЕН (маркер HRONIKI_PAPKA_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_hroniki_papka.py
"""
import io
import sys
from pathlib import Path

MARKER = "HRONIKI_PAPKA_V1"


def find_target() -> Path:
    for p in (Path("Биржа") / "tester_express.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "tester_express.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден Биржа/tester_express.py — запусти из корня")
    sys.exit(1)


def main():
    path = find_target()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    anchor = (
        '    # ── отчёт-файл рядом с CSV ──\n'
        '    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")\n'
        '    report_path = Path(full_path).with_name(\n'
        '        f"{Path(full_path).stem}_tester_{stamp}.txt")\n'
    )
    if anchor not in src:
        print("[ПАТЧ] ✗ якорь отчёт-файла не найден — покажи строки 213-217")
        sys.exit(2)

    zamena = (
        '    # ' + MARKER + ': отчёты уходят в ОТДЕЛЬНУЮ папку хроники,\n'
        '    # не в test_data к котировкам. Медийщики берут летопись отсюда.\n'
        '    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")\n'
        '    _hroniki_dir = _HERE / "хроники"\n'
        '    _hroniki_dir.mkdir(parents=True, exist_ok=True)\n'
        '    report_path = _hroniki_dir / f"{Path(full_path).stem}_tester_{stamp}.txt"\n'
    )
    orig = src
    src = src.replace(anchor, zamena, 1)

    bak = path.with_suffix(".py.bak_hroniki")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Отчёты теперь уходят в Биржа/хроники/")
    print("[ПАТЧ]    test_data остаётся чистой — только котировки.")
    print("[ПАТЧ]    Папка создаётся сама при первом прогоне.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
