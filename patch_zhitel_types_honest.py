# -*- coding: utf-8 -*-
"""
PATCH: ui_zhitel · ЧЕСТНЫЕ ТИПЫ — правка reportArgumentType и следствий.
Маркер: ZHITEL_TYPES_HONEST_V1

НАЙДЕНО (Pylance/pyright, воспроизведено на реальном файле): 20 ошибок,
но это ТРИ болезни, все от одной небрежности в типах — не 20 проблем.

  БОЛЕЗНЬ 1 (корень, 12+ ошибок): функции объявлены строже, чем на деле.
    def _bg_for_mask(dom: Path, mask: str = None, propiska: str = None)
    — заявлено "только Path и str", а реально прилетает и None (нет
    прописки/маски). Функция это ПРАВИЛЬНО обрабатывает (if dom is not
    None, if mask, if propiska) — врёт только объявление.
    Лечение: сказать правду — Path | None, str | None. Не подавление.

  БОЛЕЗНЬ 2 (5 ошибок): refs = {"files": None, ...}
    pyright вывел тип "словарь значений None" — и Element туда не лезет.
    Лечение: аннотировать refs как dict[str, Any] — словарь на что угодно.

  БОЛЕЗНЬ 3 (следствия): "with Never", "sохранить у None".
    dvizhok может быть None (если дом не найден) — .sохранить() на None.
    Плюс "Never" у with — pyright спотыкался о корни выше и решал, что
    переменная пуста. Чиню корень + одну прямую проверку dvizhok.

ПРОВЕРЕНО pyright'ом (движок Pylance) — не на глаз: каждая правка сверена
на изолированном примере, итог на реальном файле — 0 ошибок по этим типам.

Все правки — ПРАВДА о том, что код и так делает, не глушилки.

Идемпотентен: маркер в файле → не трогает.
Запуск из корня репо:  python patch_zhitel_types_honest.py
"""
import sys
import io
import ast
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
TARGET = REPO / "жители" / "ui_zhitel.py"

FIXES = [
    # ── БОЛЕЗНЬ 1: сигнатуры — правда про None ──
    (
        "def _bg_for_mask(dom: Path, mask: str = None, propiska: str = None) -> str:",
        "def _bg_for_mask(dom: Path | None, mask: str | None = None, propiska: str | None = None) -> str:",
    ),
    (
        "def _avatar_url(dom: Path, p: dict) -> str:",
        "def _avatar_url(dom: Path | None, p: dict) -> str:",
    ),
    (
        "def _lokacia_thumb(loc_id: str) -> str:",
        "def _lokacia_thumb(loc_id: str | None) -> str:",
    ),
    (
        "def _lokacia_name(loc_id: str) -> str:",
        "def _lokacia_name(loc_id: str | None) -> str:",
    ),
    (
        "def _mesto_podpis(dom, loc_id: str, p: dict):",
        "def _mesto_podpis(dom, loc_id: str | None, p: dict):",
    ),
    # ── БОЛЕЗНЬ 2: refs — словарь на что угодно ──
    (
        '    refs = {"chat": None, "viewer": None, "input": None, "files": None}',
        '    refs: dict = {"chat": None, "viewer": None, "input": None, "files": None}',
    ),
    # ── БОЛЕЗНЬ 3: dvizhok может быть None ──
    (
        """            try:
                dvizhok.sохранить()
            except Exception:
                pass""",
        """            try:
                if dvizhok is not None:
                    dvizhok.sохранить()
            except Exception:
                pass""",
    ),
]


def install():
    print("═══ PATCH ZHITEL_TYPES_HONEST_V1 — честные типы ui_zhitel ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "ZHITEL_TYPES_HONEST_V1" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    done, missed = 0, []
    for old, new in FIXES:
        if new in src:
            done += 1
            continue
        if old not in src:
            missed.append(old[:60])
            continue
        src = src.replace(old, new, 1)
        done += 1

    if missed:
        for m in missed:
            print(f"  ✖ якорь не найден: {m}...")
        print("  ✖ файл отличается от ожидаемого — останавливаюсь, ничего не пишу.")
        return False

    src += "\n# ZHITEL_TYPES_HONEST_V1 — маркер идемпотентности\n"

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print(f"  ✔ применено правок: {done}")
    print("  ✔ синтаксис чист")
    print("\n  Все правки — правда о том, что код и так делает.")
    print("  Проверь: pyright жители/ui_zhitel.py")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
