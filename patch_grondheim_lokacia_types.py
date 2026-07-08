# -*- coding: utf-8 -*-
"""
Патч: ГОРОД/ui_grondheim.py + ГОРОД/ui_lokacia.py — reportArgumentType.

ДВЕ РАЗНЫЕ ПРИЧИНЫ, ОБЕ ЧЕСТНЫЕ (не типовая случайность, не костыль):

1) ui_grondheim.py, строка 321:
     def _canvas_html(locations: list, zhiteli: list = None) -> str:
   Параметр типизирован как `list`, а по умолчанию стоит `None` —
   несовпадение типа с default-значением. Тело функции (`zhiteli = zhiteli
   or []`) уже честно чинит None — сигнатура просто не отражала это.
   Правка: `zhiteli: list | None = None`.

2) ui_lokacia.py, строка 237:
     img = _image_url(dom, p)
   `dom` приходит из find_lokacia(), который возвращает `Path | None`
   (правило: обе части пары либо есть, либо обе None). Сама функция
   _image_url() УЖЕ обрабатывает None:
     def _image_url(dom: Path, p: dict) -> str:
         if dom is None: return ""
   Только сигнатура не отражала то, что функция и так умеет. Правка:
   `dom: Path | None`.

Идемпотентен: повторный запуск ничего не меняет и не падает.
"""
import sys
import py_compile
import shutil
from pathlib import Path
from datetime import datetime

FILES = [
    {
        "path": Path("ГОРОД/ui_grondheim.py"),
        "old": "def _canvas_html(locations: list, zhiteli: list = None) -> str:",
        "new": "def _canvas_html(locations: list, zhiteli: \"list | None\" = None) -> str:",
        "marker": 'zhiteli: "list | None" = None',
    },
    {
        "path": Path("ГОРОД/ui_lokacia.py"),
        "old": 'def _image_url(dom: Path, p: dict) -> str:',
        "new": 'def _image_url(dom: "Path | None", p: dict) -> str:',
        "marker": 'dom: "Path | None"',
    },
]


def patch_one(spec: dict) -> None:
    target = spec["path"]
    if not target.exists():
        print(f"НЕ НАЙДЕН: {target} (запусти из корня Grondheim-Ecosystem)")
        sys.exit(1)

    src = target.read_text(encoding="utf-8")

    if spec["marker"] in src:
        print(f"{target}: уже применено — идемпотентность держит, ничего не меняю.")
        return

    if spec["old"] not in src:
        print(f"{target}: НЕ НАЙДЕН ожидаемый фрагмент — файл изменился с момента диагностики.")
        print("Ничего не трогаю, чтобы не сломать вслепую.")
        sys.exit(1)

    backup = target.with_suffix(f".py.bak_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(target, backup)
    print(f"Бэкап: {backup}")

    new_src = src.replace(spec["old"], spec["new"])
    target.write_text(new_src, encoding="utf-8")

    py_compile.compile(str(target), doraise=True)
    print(f"{target}: синтаксис цел (py_compile прошёл).")


def main():
    for spec in FILES:
        patch_one(spec)
    print("Готово.")


if __name__ == "__main__":
    main()
