# -*- coding: utf-8 -*-
"""
patch_birzha_memory_paths.py
─────────────────────────────────────────────────────────────
ОХВАТ ПАМЯТИ БИРЖИ · закрытие «нити, что торчит наружу»

Болезнь: три пути памяти цеха в Биржа/hooks.py записаны ОТНОСИТЕЛЬНО.
При запуске тестера из корня репо Python плодит старые папки-мусор
(studio/…, economy/…) прямо в новом городе.

Лечение (идемпотентно, безопасно, деньги-критичные данные не теряем):
  1. Перевод ATLAS_PATH / STATE_PATH / PNL_PATH на АБСОЛЮТНЫЕ через _REPO,
     под единую площадь GRONDHEIM_CITY/Биржа/данные/ (Закон Меток).
  2. Перенос уже накопленных данных из старых мест — история цела.
  3. Уборка старых папок-мусора (studio/, economy/) после переноса.

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_birzha_memory_paths.py

Повторный запуск безопасен: маркер MEMORY_PATHS_V1 → скажет «уже пропатчено».
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOOKS = REPO / "Биржа" / "hooks.py"
MARKER = "# MEMORY_PATHS_V1 — маркер идемпотентности"

# ── Новая единая площадь памяти цеха ──────────────────────────
NEW_DIR = REPO / "GRONDHEIM_CITY" / "Биржа" / "данные"

# ── Старые (относительные) → новые (абсолютные) блоки для замены ─
# Точечная хирургия: меняем ровно три строки-объявления.
REPLACEMENTS = [
    (
        'ATLAS_PATH = Path("economy/data/atlas_trading.jsonl")',
        'ATLAS_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "данные" / "atlas_trading.jsonl"',
    ),
    (
        'STATE_PATH = Path("studio/modules/trading/state/trading_state.json")',
        'STATE_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "данные" / "trading_state.json"',
    ),
    (
        'PNL_PATH = Path("economy/data/trading_pnl.jsonl")',
        'PNL_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "данные" / "trading_pnl.jsonl"',
    ),
]

# ── Миграция: (старый файл-мусор) → (новое имя в новой площади) ──
MIGRATIONS = [
    (REPO / "studio" / "modules" / "trading" / "state" / "trading_state.json",
     NEW_DIR / "trading_state.json"),
    (REPO / "economy" / "data" / "atlas_trading.jsonl",
     NEW_DIR / "atlas_trading.jsonl"),
    (REPO / "economy" / "data" / "trading_pnl.jsonl",
     NEW_DIR / "trading_pnl.jsonl"),
]

# ── Папки-мусор к уборке (после успешного переноса) ───────────
JUNK_DIRS = [
    REPO / "studio" / "modules" / "trading" / "state",
    REPO / "economy" / "data",
]


def _patch_source() -> bool:
    """Правит три строки в hooks.py. True — если что-то изменилось."""
    if not HOOKS.exists():
        print(f"[ПАТЧ] ❌ Не найден {HOOKS} — запусти из корня репо.")
        raise SystemExit(1)

    src = HOOKS.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ hooks.py уже пропатчен (MEMORY_PATHS_V1) — пропускаю правку кода.")
        return False

    changed = 0
    for old, new in REPLACEMENTS:
        if old in src:
            src = src.replace(old, new)
            changed += 1
            print(f"[ПАТЧ] 🔧 путь переклеен: …{old.split('(')[0].strip()}")
        elif new in src:
            print(f"[ПАТЧ] ↺ путь уже абсолютный: {new.split('/')[-1].rstrip(chr(34))}")
        else:
            print(f"[ПАТЧ] ⚠️  не найдена строка (проверь вручную):\n         {old}")

    if changed == 0:
        print("[ПАТЧ] ⚠️  ни одной из трёх строк не найдено в ожидаемом виде.")
        print("        Возможно файл уже правился руками — миграцию всё равно выполню.")

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    HOOKS.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] 💾 hooks.py сохранён (переклеено путей: {changed}).")
    return True


def _migrate_data():
    """Переносит накопленные данные в новую площадь. Историю не теряем."""
    NEW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[ДАННЫЕ] 📁 Площадь памяти: {NEW_DIR}")

    for old, new in MIGRATIONS:
        if not old.exists():
            print(f"[ДАННЫЕ] ○ нет старого файла (нечего переносить): {old.name}")
            continue
        if new.exists():
            # Новый уже есть — не затираем живое. Старый оставим как .old для ручной сверки.
            backup = old.with_suffix(old.suffix + ".old")
            shutil.move(str(old), str(backup))
            print(f"[ДАННЫЕ] ⚠️  {new.name} уже существует — старый сохранён как {backup.name} (сверь руками).")
            continue
        shutil.move(str(old), str(new))
        print(f"[ДАННЫЕ] ✅ перенесён: {old.name} → {new}")


def _cleanup_junk():
    """Убирает пустые папки-мусор из корня репо."""
    for d in JUNK_DIRS:
        if not d.exists():
            continue
        # Удаляем только если внутри не осталось значимых файлов
        leftovers = [p for p in d.rglob("*") if p.is_file()]
        if leftovers:
            print(f"[УБОРКА] ⚠️  {d} не пуста ({len(leftovers)} файлов) — оставляю, глянь руками:")
            for p in leftovers[:10]:
                print(f"            {p.relative_to(REPO)}")
            continue
        shutil.rmtree(d, ignore_errors=True)
        print(f"[УБОРКА] 🧹 удалена пустая папка-мусор: {d.relative_to(REPO)}")

    # Схлопываем осиротевшие родительские каталоги, если пусты
    for parent in [REPO / "studio" / "modules" / "trading",
                   REPO / "studio" / "modules",
                   REPO / "studio",
                   REPO / "economy"]:
        try:
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                print(f"[УБОРКА] 🧹 удалён пустой каталог: {parent.relative_to(REPO)}")
        except OSError:
            pass


def main():
    print("═" * 60)
    print("  ОХВАТ ПАМЯТИ БИРЖИ · MEMORY_PATHS_V1")
    print("═" * 60)
    _patch_source()
    _migrate_data()
    _cleanup_junk()
    print("═" * 60)
    print("  ✅ ГОТОВО. Пути памяти под своим кварталом, мусор убран.")
    print(f"     Новая площадь: GRONDHEIM_CITY/Биржа/данные/")
    print("═" * 60)


if __name__ == "__main__":
    main()
