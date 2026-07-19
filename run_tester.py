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
    tester_express.main()
