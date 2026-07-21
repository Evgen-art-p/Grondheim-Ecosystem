#!/usr/bin/env python3
# arkhivirovat_bak.py
# ─────────────────────────────────────────────────────────────
# ШАГ 1 ЧИСТКИ ТОРГОВОГО ЦЕХА (см. ПЛАН_АУДИТА_ЦЕХА.md §2.1, §8 Этап 1).
#
# Не удаляет. ПЕРЕНОСИТ все *.bak* файлы торгового цеха в отдельную
# папку-архив рядом с корнем репы, с манифестом (что куда переехало,
# когда, какого размера). Ничего не теряется — можно откатить руками
# по манифесту в любой момент.
#
# ЧТО АРХИВИРУЕТ (ровно то, что перечислено в плане §2.1):
#   GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/**/*.bak*
#   GRONDHEIM_CITY/Биржа/цеха/контора/слоты/**/*.bak*
# Данные (дневники, atlas, pnl-архивы) НЕ трогает — решение Шефа §2.3.
#
# ИДЕМПОТЕНТНОСТЬ: файл, который уже переехал, второй раз не найдётся
# на старом месте — повторный запуск просто скажет "нечего архивировать".
# Каждый запуск — свой архив с меткой времени, старые архивы не трогает.
#
# ЗАПУСК (из корня репо):
#   py arkhivirovat_bak.py            — реально переносит
#   py arkhivirovat_bak.py --dry-run  — только показывает, что нашёл,
#                                        ничего не трогает
# ─────────────────────────────────────────────────────────────

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_ROOT = Path(__file__).resolve().parent

# Папки цеха, которые чистим (относительно корня репы)
_TARGET_DIRS = [
    _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты",
    _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора" / "слоты",
]

# Что считаем .bak-мусором — любой файл, в имени которого есть ".bak"
_BAK_MARKER = ".bak"


def find_bak_files():
    found = []
    for base in _TARGET_DIRS:
        if not base.exists():
            print(f"[пропуск] нет папки: {base.relative_to(_ROOT)}")
            continue
        for p in base.rglob("*"):
            if p.is_file() and _BAK_MARKER in p.name:
                found.append(p)
    return sorted(found)


def main():
    dry_run = "--dry-run" in sys.argv[1:]

    files = find_bak_files()

    if not files:
        print("Нечего архивировать — .bak-файлов не найдено (уже чисто).")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_root = _ROOT / "_АРХИВ_ЧИСТКИ" / f"torgovyy_tsekh_bak_{stamp}"

    print(f"Найдено .bak-файлов: {len(files)}")
    total_bytes = 0
    manifest = {
        "created": datetime.now().isoformat(),
        "dry_run": dry_run,
        "archive_root": str(archive_root.relative_to(_ROOT)) if not dry_run else None,
        "files": [],
    }

    for src in files:
        rel = src.relative_to(_ROOT)
        size = src.stat().st_size
        total_bytes += size
        print(f"  {size:7d} B  {rel}")
        manifest["files"].append({
            "relative_path": str(rel),
            "size_bytes": size,
        })

    print(f"\nВсего: {len(files)} файлов, {total_bytes:,} байт".replace(",", " "))

    if dry_run:
        print("\n[DRY-RUN] Ничего не перенесено. Запусти без --dry-run, чтобы реально архивировать.")
        return

    archive_root.mkdir(parents=True, exist_ok=True)

    moved = 0
    for src in files:
        rel = src.relative_to(_ROOT)
        dst = archive_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved += 1

    manifest_path = archive_root / "МАНИФЕСТ_ПЕРЕНОСА.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nГотово. Перенесено {moved} файлов в:")
    print(f"  {archive_root.relative_to(_ROOT)}")
    print(f"Манифест: {manifest_path.relative_to(_ROOT)}")
    print("\nСтруктура папок внутри цеха сохранена как есть (относительные пути),")
    print("откатить можно вручную по манифесту в любой момент.")


if __name__ == "__main__":
    main()
