#!/usr/bin/env python3
# proverit_fraktal.py
# ─────────────────────────────────────────────────────────────
# Обёртка в КОРНЕ репозитория — тот же приём, что run_tester.py и
# proverit_signal.py: не даёт набирать "Биржа" в PowerShell.
#
# Зовёт Биржа/test_fractal_trigger.py — фрактал-триггер для Брута
# (момент подтверждения + живая точка + долгое ожидание ордера,
# см. ИСКРА_ПЕРЕДЕЛКА_СПЕК.md правки 21-24). Ноль LLM, ноль Совета.
#
# ЗАПУСК (из корня, одна строка):
#   python proverit_fraktal.py ИМЯ_ФАЙЛА.csv
#   python proverit_fraktal.py ИМЯ_ФАЙЛА.csv --start 2020.01.01 --spread 2.0
#   python proverit_fraktal.py --list
#
# Путь к CSV пиши БЕЗ "Биржа/test_data/" впереди — обёртка сама
# знает, где искать.
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

print("=== proverit_fraktal.py — обёртка без кириллицы в консоли ===")

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"

if not _BIRZHA.exists():
    print(f"ОШИБКА: не нашёл папку Биржа рядом с этим файлом ({_BIRZHA})")
    print("Убедись, что proverit_fraktal.py лежит в корне репозитория "
         "(там же, где main.py).")
    sys.exit(1)

sys.path.insert(0, str(_BIRZHA))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

if len(sys.argv) < 2 or sys.argv[1] in ("--list", "-l"):
    _td = _BIRZHA / "test_data"
    print(f"Смотрю сюда: {_td}\n")
    if not _td.exists():
        print("Папки test_data вообще нет.")
    else:
        csvs = sorted(f for f in _td.rglob("*.csv") if f.is_file())
        if not csvs:
            print("CSV-файлов не нашёл.")
        else:
            print("Нашёл эти CSV (используй имя файла как есть, без пути):")
            for f in csvs:
                print(f"  {f.relative_to(_td)}")
    print("\nПример запуска:")
    print("  python proverit_fraktal.py ИМЯ_ФАЙЛА.csv")
    print("  python proverit_fraktal.py ИМЯ_ФАЙЛА.csv --wave1-scale  (эксперимент)")
    sys.exit(0)

raw_csv = sys.argv[1]
candidates = [
    Path(raw_csv),
    _BIRZHA / "test_data" / raw_csv,
    _BIRZHA / raw_csv,
]
csv_path = next((c for c in candidates if c.exists()), None)
if csv_path is None:
    print(f"CSV не найден: {raw_csv}")
    print("Проверил тут:")
    for c in candidates:
        print(f"  {c}")
    print("\nЗапусти 'python proverit_fraktal.py --list', чтобы увидеть, что есть.")
    sys.exit(1)

import test_fractal_trigger as tft  # noqa: E402

sys.argv = [sys.argv[0], str(csv_path)] + sys.argv[2:]
tft.main()
