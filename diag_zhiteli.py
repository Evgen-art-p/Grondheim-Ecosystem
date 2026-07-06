# diag_zhiteli.py
"""
Диагностика: почему list_zhiteli() не находит жителей.
Повторяет ТОЧНО ту же логику, что ui_zhitel.py, но печатает
каждый шаг — где именно рвётся факт.

Запуск из КОРНЯ репо:
    python diag_zhiteli.py
"""
from pathlib import Path
import json
import sys

print(f"Текущая рабочая папка (cwd): {Path.cwd()}")
print(f"Расположение самого diag_zhiteli.py: {Path(__file__).resolve().parent}")
print()

_ROOT = Path(__file__).resolve().parent
ZHITELI_DIR = _ROOT / "GRONDHEIM_CITY" / "жители"

print(f"Ищу ZHITELI_DIR: {ZHITELI_DIR}")
print(f"Существует ли ZHITELI_DIR: {ZHITELI_DIR.exists()}")
print()

if not ZHITELI_DIR.exists():
    print("✗ ОСТАНОВКА: папка GRONDHEIM_CITY/жители не найдена по этому пути.")
    print("  Проверь: она реально лежит по адресу выше?")
    sys.exit(1)

print("Содержимое ZHITELI_DIR (профили/подпапки):")
prof_dirs = list(ZHITELI_DIR.iterdir())
if not prof_dirs:
    print("  ✗ ПУСТО — в жители/ вообще нет подпапок.")
for prof_dir in prof_dirs:
    marker = "[папка]" if prof_dir.is_dir() else "[файл]"
    print(f"  {marker} {prof_dir.name!r}")
print()

найдено_жителей = 0
for prof_dir in prof_dirs:
    if not prof_dir.is_dir():
        continue
    print(f"Захожу в профиль {prof_dir.name!r}:")
    dom_dirs = list(prof_dir.iterdir())
    if not dom_dirs:
        print(f"  ✗ ПУСТО — внутри {prof_dir.name!r} нет подпапок домов.")
    for dom_dir in dom_dirs:
        marker = "[папка]" if dom_dir.is_dir() else "[файл]"
        print(f"    {marker} {dom_dir.name!r}")
        if not dom_dir.is_dir():
            continue
        passport_file = dom_dir / "passport.json"
        print(f"      passport.json существует: {passport_file.exists()}")
        if not passport_file.exists():
            continue
        try:
            p = json.loads(passport_file.read_text(encoding="utf-8"))
            имя = p.get("Official_Name", "?")
            print(f"      ✓ ПРОЧИТАН: Official_Name={имя!r}, ID_Object={p.get('ID_Object', '?')!r}")
            найдено_жителей += 1
        except Exception as e:
            print(f"      ✗ ОШИБКА ЧТЕНИЯ JSON: {type(e).__name__}: {e}")
    print()

print("═" * 50)
print(f"ИТОГО найдено жителей: {найдено_жителей}")
if найдено_жителей == 0:
    print("✗ list_zhiteli() у тебя тоже вернёт пустой список — по тем же причинам, что выше.")
else:
    print("✓ Жители реально на диске и читаются. Если кабинет всё равно пишет")
    print("  «никого нет» — проблема не в файлах, а в том, ЧТО ИМЕННО импортирует")
    print("  ui_brat.py (возможно, другой ui_zhitel.py откуда-то ещё). Пришли этот вывод.")
