# -*- coding: utf-8 -*-
"""
PATCH: ЖИТЕЛЬ · СЛОВА ОПТИКИ — живая шкала интенсивности.
Маркер: ZHITEL_OPTIKA_SLOVA_V2

Шеф поймал: "мутит" звучит как тошнота (двусмысленность со здоровьем),
хотя показатель ВООБЩЕ не про знак — только про силу качнувшего
(плюс или минус, неважно). Финальные слова, подобранные Шефом:

  чисто → ровно → ШТЫРИТ → КОЛБАСИТ

"штырит" — сильно тронуло. "колбасит" точнее старого "залито": не
"что-то случилось снаружи", а "самого несёт изнутри" — вернее по сути
показателя (заряд — внутреннее состояние, не внешнее событие).

Идемпотентен: маркер в файле → не трогаем.
Требует: patch_zhitel_panel.py (слова "мутит"/"залито" существуют).

Запуск из корня репо:  python patch_zhitel_optika_slova.py
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

OLD_1 = '        optika, ocolor = "мутит", "rgba(255,160,60,0.9)"'
NEW_1 = '        optika, ocolor = "штырит", "rgba(255,160,60,0.9)"'

OLD_2 = '        optika, ocolor = "залито", "rgba(255,80,80,0.9)"'
NEW_2 = '        optika, ocolor = "колбасит", "rgba(255,80,80,0.9)"'


def install():
    print("═══ PATCH ZHITEL_OPTIKA_SLOVA_V2 — штырит / колбасит ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "ZHITEL_OPTIKA_SLOVA" in src or ('"штырит"' in src and '"колбасит"' in src):
        print("  ○ уже накатано — не трогаю")
        return True

    if OLD_1 not in src or OLD_2 not in src:
        print("  ✖ якорь не найден — слова уже другие или файл менялся. "
              "Покажи текущий блок оптики.")
        return False

    src = src.replace(OLD_1, NEW_1)
    src = src.replace(OLD_2, NEW_2)
    src += "\n# ZHITEL_OPTIKA_SLOVA_V2 — маркер идемпотентности\n"

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ мутит → штырит")
    print("  ✔ залито → колбасит")
    print("  ✔ синтаксис чист")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
