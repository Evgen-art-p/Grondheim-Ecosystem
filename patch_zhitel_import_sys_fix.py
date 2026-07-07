# -*- coding: utf-8 -*-
"""
PATCH: ЖИТЕЛЬ · ИСПРАВЛЕНИЕ import sys — тихий баг, найденный Pylance.
Маркер: ZHITEL_IMPORT_SYS_FIX_V1

БАГ (реальный, не ложная тревога линтера): patch_zhitel_panel.py и
patch_zhitel_tekushaya_lokacia.py используют `sys.path` внутри функций
(_mesto_podpis, page_zhitel), но НЕ добавили `import sys` в начало
файла — в отличие от аналогичного патча для ui_grondheim.py, где это
было сделано правильно.

ПОЧЕМУ ЭТО ОПАСНО, А НЕ ПРОСТО ОШИБКА ЗАПУСКА: обе функции оборачивают
sys.path-код в `try/except Exception: pass` (задумано для мягкого
отката, если sostoyanie.py не найден). Но NameError от неопределённого
`sys` тоже подпадает под `except Exception` — и ТИХО глотается.
Функция не падает, а молча откатывается на "дома"/статичную прописку.

ПРОВЕРЕНО ЖИВЬЁМ ДО ПАТЧА: sostoyanie.gde_ya() напрямую возвращает
{'дома': False, 'локация': '0014_EXCHANGE'} (Вера на смене), но
_mesto_podpis() внутри модуля всё равно вернул "ДОМА · Биржа" —
заголовок карточки врал, и живой фон тоже не переключался.

ЧТО ДЕЛАЕТ: добавляет `import sys` в начало файла (рядом с os/asyncio).

Идемпотентен: если "import sys" уже есть — не трогает.

Запуск из корня репо:  python patch_zhitel_import_sys_fix.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
TARGET = REPO / "жители" / "ui_zhitel.py"

ANCHOR = "import json\nimport os\nimport asyncio\n"
INSERT = "import json\nimport os\nimport sys\nimport asyncio\n"


def install():
    print("═══ PATCH ZHITEL_IMPORT_SYS_FIX_V1 — правка забытого import sys ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    # уже есть top-level import sys?
    for line in src.split("\n")[:50]:
        if line.strip() == "import sys":
            print("  ○ import sys уже стоит — не трогаю")
            return True

    if ANCHOR not in src:
        print("  ✖ якорь (блок импортов) не найден в ожидаемом виде — "
              "файл менялся руками. Покажи первые 50 строк ui_zhitel.py.")
        return False

    src = src.replace(ANCHOR, INSERT, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ добавлен: import sys")
    print("  ✔ синтаксис чист")
    print("\n  Теперь _mesto_podpis() и page_zhitel() реально видят live")
    print("  место жителя, а не тихо откатываются на 'дома'.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
