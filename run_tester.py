#!/usr/bin/env python3
# run_tester.py
# ─────────────────────────────────────────────────────────────
# Обёртка в КОРНЕ репозитория — чтобы не набирать "Биржа" в консоли
# (кириллица в PowerShell то не вводится, то не отображается).
# Кладёшь этот файл рядом с main.py, в самый корень Grondheim-Ecosystem.
#
# ЗАПУСК (из корня, PowerShell, всё копируется одной строкой):
#   python run_tester.py test_data/XAUUSD_H4.csv XAUUSD H4 --signals 1
#
# Все остальные флаги tester_express.py работают так же:
#   --loose, --learn, --warmup N, --point N
#
# Путь к CSV пиши так же, как раньше писал бы из папки Биржа —
# "test_data/..." (без "Биржа/" впереди). Обёртка сама знает, где
# искать: путь считается ОТНОСИТЕЛЬНО папки Биржа, не текущей папки.
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

print("=== run_tester.py, версия v2 (с --list) ===")
print(f"Реально запущен файл: {Path(__file__).resolve()}")

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"

if not _BIRZHA.exists():
    print(f"ОШИБКА: не нашёл папку Биржа рядом с этим файлом ({_BIRZHA})")
    print("Убедись, что run_tester.py лежит в корне репозитория "
          "(там же, где main.py).")
    sys.exit(1)

# кириллическая папка кладётся в sys.path программно — без единого
# набора кириллицы в консоли, отсюда и весь смысл этого файла
sys.path.insert(0, str(_BIRZHA))

# UTF-8 на вывод — чтобы русский текст в логе не превращался в
# кракозябры, даже если PowerShell сидит на старой кодовой странице.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass  # старый Python без reconfigure — не критично, работаем как есть

import tester_express  # noqa: E402  (импорт после правки sys.path — так и надо)

if __name__ == "__main__":
    # --list (или запуск вообще без аргументов) — просто показать, что
    # реально лежит в Биржа/test_data, ничего не запуская. Полезно,
    # когда не помнишь точное имя файла или получил "CSV не найден".
    if len(sys.argv) < 2 or sys.argv[1] in ("--list", "-l"):
        _td = _BIRZHA / "test_data"
        print(f"Смотрю сюда: {_td}")
        print("")
        if not _td.exists():
            print("Папки test_data вообще нет.")
        else:
            files = sorted(_td.rglob("*"))
            csvs = [f for f in files if f.is_file() and f.suffix.lower() == ".csv"]
            if not csvs:
                print("CSV-файлов не нашёл. Вот что там есть целиком:")
                for f in files:
                    print(f"  {f.relative_to(_td)}")
            else:
                print("Нашёл эти CSV (используй путь ПОСЛЕ 'test_data/' как есть):")
                for f in csvs:
                    rel = f.relative_to(_td)
                    print(f"  test_data/{rel}")
        print("")
        print("Пример запуска после того как увидишь нужное имя:")
        print("  python run_tester.py test_data/ИМЯ_ФАЙЛА.csv XAUUSD H4 --signals 1")
        sys.exit(0)

    tester_express.main()
