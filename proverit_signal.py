#!/usr/bin/env python3
# proverit_signal.py
# ─────────────────────────────────────────────────────────────
# Обёртка в КОРНЕ репозитория — тот же приём, что run_tester.py для
# tester_express.py: не даёт набирать "Биржа" в консоли (кириллица
# в PowerShell то не вводится, то не отображается).
#
# Зовёт Биржа/test_idivergence_bar.py — чистый счёт Искры (сколько
# раз сработала формула) + бэктест Авантюриста (вход/стоп/R) на этом
# же сигнале. Ноль LLM, ноль Совета, только сам сигнал и его цена.
#
# ЗАПУСК (из корня, PowerShell, всё копируется одной строкой):
#   python proverit_signal.py ИМЯ_ФАЙЛА.csv XAUUSD 0.01
#
# Путь к CSV пиши БЕЗ "Биржа/test_data/" впереди — обёртка сама
# знает, где искать. Если файл в другой подпапке test_data (или уже
# с полным путём) — тоже сработает, ищется в обоих вариантах.
#
# Необязательные флаги — те же, что у test_idivergence_bar.py:
#   --start YYYY.MM.DD --end YYYY.MM.DD
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

print("=== proverit_signal.py — обёртка без кириллицы в консоли ===")

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"

if not _BIRZHA.exists():
    print(f"ОШИБКА: не нашёл папку Биржа рядом с этим файлом ({_BIRZHA})")
    print("Убедись, что proverit_signal.py лежит в корне репозитория "
         "(там же, где main.py).")
    sys.exit(1)

# кириллическая папка кладётся в sys.path программно — без единого
# набора кириллицы в консоли, отсюда и весь смысл этого файла
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
    print("  python proverit_signal.py ИМЯ_ФАЙЛА.csv XAUUSD 0.01")
    sys.exit(0)

# ── резолвим путь к CSV: пробуем как дано, потом внутри test_data ──
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
    print("\nЗапусти 'python proverit_signal.py --list', чтобы увидеть, что есть.")
    sys.exit(1)

# ── зовём test_idivergence_bar.py с уже готовым путём ──
import test_idivergence_bar as tib  # noqa: E402  (импорт после правки sys.path)

# подменяем argv на то, что реально ждёт test_idivergence_bar.main()
sys.argv = [sys.argv[0], str(csv_path)] + sys.argv[2:]
tib.main()
