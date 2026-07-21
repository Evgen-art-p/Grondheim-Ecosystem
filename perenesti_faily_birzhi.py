#!/usr/bin/env python3
# perenesti_faily_birzhi.py
# ─────────────────────────────────────────────────────────────
# Переносит файлы биржи из корня репо в правильные папки (решение
# Шефа 22.07): мозг биржи (движок) → Биржа/, цех → GRONDHEIM_CITY/
# Биржа/цеха/торговый_хаос/, общие данные картриджа → GRONDHEIM_CITY/
# Биржа/. Заодно правит пути внутри файлов, которые предполагали,
# что лежат в корне репо — иначе на новом месте упадут.
#
# ИДЕМПОТЕНТНО: если файл уже перенесён (нет в корне) — пропускает.
# Если файл в корне не найден и на новом месте тоже нет — пропускает
# с пометкой (значит уже удалён раньше или никогда не было).
# НЕ трогает run_tester.py (специально остаётся в корне) и
# test_idivergence_bar.py (сюда не входит — переносится отдельно,
# путей не требует).
#
# ЗАПУСК (из корня репо, один раз):
#   py perenesti_faily_birzhi.py            — реально переносит
#   py perenesti_faily_birzhi.py --dry-run  — только показывает план
# ─────────────────────────────────────────────────────────────

import sys
import ast
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_ROOT = Path(__file__).resolve().parent

_DVIZHOK = _ROOT / "Биржа"
_TSEH = _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
_KARTRIDZH = _ROOT / "GRONDHEIM_CITY" / "Биржа"

# ── план: (файл_в_корне, папка_назначения, патч_или_None) ──

def _patch_zigzag_chart(text: str) -> str:
    old = ('_BIRZHA = _ROOT / "Биржа"\n'
           'if not _BIRZHA.exists():\n'
           '    print(f"ОШИБКА: не нашёл папку Биржа рядом с этим файлом ({_BIRZHA})")\n'
           '    sys.exit(1)\n'
           'sys.path.insert(0, str(_BIRZHA))')
    new = ('_BIRZHA = _ROOT / "Биржа"\n'
           'if not _BIRZHA.exists():\n'
           '    _BIRZHA = _ROOT   # PERENOS_V_DVIZHOK_V1: файл теперь может жить прямо в Биржа/\n'
           'sys.path.insert(0, str(_BIRZHA))')
    if old not in text:
        raise ValueError("не нашёл ожидаемый блок путей в zigzag_chart.py — "
                         "файл уже другой, проверь руками")
    return text.replace(old, new)


def _patch_tseh_repo(text: str, label: str) -> str:
    old = "REPO = Path(__file__).resolve().parent"
    new = ("REPO = Path(__file__).resolve().parents[4]   "
          "# PERENOS_V_TSEH_V1: файл теперь в цеха/торговый_хаос/")
    if old not in text:
        raise ValueError(f"не нашёл строку REPO в {label} — проверь руками")
    return text.replace(old, new)


def _patch_ochistit_pozicii(text: str) -> str:
    old = 'STATE = Path("GRONDHEIM_CITY") / "Биржа" / "данные" / "trading_state.json"'
    new = ('STATE = Path(__file__).resolve().parent / "данные" / "trading_state.json"\n'
          '# PERENOS_V_KARTRIDZH_V1: файл теперь лежит прямо в GRONDHEIM_CITY/Биржа/,\n'
          '# рядом с папкой данные/ — путь больше не зависит от того, откуда запущен.')
    if old not in text:
        raise ValueError("не нашёл строку STATE в ochistit_pozicii.py — проверь руками")
    return text.replace(old, new)


def _patch_kartridzh_root(text: str, label: str) -> str:
    old = "ROOT = Path(__file__).resolve().parent"
    new = ("ROOT = Path(__file__).resolve().parents[2]   "
          "# PERENOS_V_KARTRIDZH_V1: файл теперь в GRONDHEIM_CITY/Биржа/, "
          "ROOT остаётся корнем репо")
    if old not in text:
        raise ValueError(f"не нашёл строку ROOT в {label} — проверь руками")
    return text.replace(old, new)


_PLAN = [
    ("konec_volny_C.py",        _DVIZHOK,   None),
    ("test_idivergence_bar.py", _DVIZHOK,   None),
    ("zigzag_chart.py",         _DVIZHOK,   _patch_zigzag_chart),
    ("proverka_vasya_wave.py",  _TSEH,      lambda t: _patch_tseh_repo(t, "proverka_vasya_wave.py")),
    ("schetchik_vasya3.py",     _TSEH,      lambda t: _patch_tseh_repo(t, "schetchik_vasya3.py")),
    ("voronka_bdb2.py",         _TSEH,      lambda t: _patch_tseh_repo(t, "voronka_bdb2.py")),
    ("ochistit_pozicii.py",     _KARTRIDZH, _patch_ochistit_pozicii),
    ("otchet.py",               _KARTRIDZH, lambda t: _patch_kartridzh_root(t, "otchet.py")),
    ("razvedka_slepka.py",      _KARTRIDZH, lambda t: _patch_kartridzh_root(t, "razvedka_slepka.py")),
]


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    print(f"{'[DRY-RUN] ' if dry_run else ''}Перенос файлов биржи из корня\n")

    moved = 0
    skipped = 0
    errors = 0

    for filename, dest_dir, patch_fn in _PLAN:
        src = _ROOT / filename
        dst = dest_dir / filename

        if not src.exists():
            if dst.exists():
                print(f"  ✓ {filename} — уже перенесён ({dst.relative_to(_ROOT)})")
                skipped += 1
            else:
                print(f"  ?  {filename} — нет ни в корне, ни на месте назначения, пропускаю")
                skipped += 1
            continue

        text = src.read_text(encoding="utf-8")

        if patch_fn is not None:
            try:
                text = patch_fn(text)
            except ValueError as e:
                print(f"  ✗ {filename} — ОШИБКА ПАТЧА: {e}")
                errors += 1
                continue

        # честная проверка синтаксиса перед записью — не портим файл
        try:
            ast.parse(text)
        except SyntaxError as e:
            print(f"  ✗ {filename} — патч сломал синтаксис: {e}")
            errors += 1
            continue

        print(f"  → {filename}  →  {dst.relative_to(_ROOT)}"
              f"{' (пути поправлены)' if patch_fn else ''}")

        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dst.write_text(text, encoding="utf-8")
            src.unlink()
        moved += 1

    print(f"\n{'Будет перенесено' if dry_run else 'Перенесено'}: {moved}   "
          f"пропущено: {skipped}   ошибок: {errors}")
    if dry_run:
        print("Запусти без --dry-run, чтобы реально перенести.")
    elif errors == 0 and moved > 0:
        print("Готово. Проверь запуском файлов с нового места, если сомневаешься.")


if __name__ == "__main__":
    main()
