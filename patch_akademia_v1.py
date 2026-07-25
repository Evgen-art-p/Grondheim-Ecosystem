# -*- coding: utf-8 -*-
# PATCH_AKADEMIA_V1 — подключение Академии к городу
"""
Что делает (идемпотентно, дважды катить безопасно):

  1. Заводит двор Академии на диске:
       GRONDHEIM_CITY/Академия/{руда/тексты, руда/изображения, библиотека/*}
       + ученики.json (10 мест, пустые)
       + библиотека/каталог.json (пустой)
  2. Правит main.py:
       - "Академия" добавляется в список папок sys.path
       - регистрируется страница /akademia
     Перед правкой — бэкап main.py.bak_akademia, после — ast.parse.
     Не сошлось — файл НЕ пишется (стоп-кран).

Запуск ИЗ КОРНЯ РЕПО:
    python patch_akademia_v1.py

`шесть·проверено·до·корня`
"""
import ast
import json
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
MAIN = ROOT / "main.py"
DATA = ROOT / "GRONDHEIM_CITY" / "Академия"
KOD = ROOT / "Академия"

POLKI = ["психология", "ремесло", "грондхейм", "рынок", "техника", "прочее"]

ANCHOR_PATH = 'for _sub in ("Брат", "жители", "ГОРОД", "Биржа"):'
NEW_PATH = 'for _sub in ("Брат", "жители", "ГОРОД", "Биржа", "Академия"):'

ANCHOR_PAGE = '''# ── СТОЛ ЦЕХА — Совет Биржи (Закон Пары: слот -> резидент) ── TORG_STOL_V1'''

BLOCK_PAGE = '''# ── АКАДЕМИЯ — Замок Сов (школа города) ── AKADEMIA_KABINET_V1
# Самостоятельный модуль, как Биржа и Студия. Житель рождается человеком,
# профессию осваивает здесь.
from ui_akademia import page_akademia

@ui.page("/akademia")
def _akademia():
    page_akademia()


'''


def zapisat_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def shag_1_dvor():
    print("── ШАГ 1: двор Академии ──")
    if not KOD.exists():
        print(f"  ⚠ папки кода {KOD.name}/ нет — положи туда ui_akademia.py")
    sozdano = 0
    for d in (DATA, DATA / "руда" / "тексты", DATA / "руда" / "изображения",
              DATA / "библиотека", DATA / "курсы"):
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            sozdano += 1
    for polka in POLKI:
        p = DATA / "библиотека" / polka
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            sozdano += 1

    uch = DATA / "ученики.json"
    if not uch.exists():
        zapisat_json(uch, {"места": []})
        print("  ✓ ученики.json заведён (10 мест, все свободны)")
    else:
        print("  = ученики.json уже есть, не трогаю")

    kat = DATA / "библиотека" / "каталог.json"
    if not kat.exists():
        zapisat_json(kat, {"книги": [], "полки": POLKI})
        print("  ✓ каталог.json заведён (полки пусты)")
    else:
        print("  = каталог.json уже есть, не трогаю")

    print(f"  ✓ папок создано: {sozdano}")
    return True


def shag_2_main():
    print("── ШАГ 2: подключение к main.py ──")
    if not MAIN.exists():
        print(f"  ✗ {MAIN} не найден. Запускай ИЗ КОРНЯ репо.")
        return False

    src = MAIN.read_text(encoding="utf-8")
    novyy = src
    izmeneno = []

    # 2а — sys.path
    if '"Академия"' in src:
        print("  = Академия уже в sys.path")
    elif ANCHOR_PATH in src:
        novyy = novyy.replace(ANCHOR_PATH, NEW_PATH, 1)
        izmeneno.append("sys.path")
    else:
        print("  ✗ якорь sys.path не найден — main.py не тот, что я читал.")
        print(f"    Ищу строку: {ANCHOR_PATH}")
        return False

    # 2б — страница
    if "page_akademia" in src:
        print("  = страница /akademia уже зарегистрирована")
    elif ANCHOR_PAGE in novyy:
        novyy = novyy.replace(ANCHOR_PAGE, BLOCK_PAGE + ANCHOR_PAGE, 1)
        izmeneno.append("страница /akademia")
    else:
        print("  ✗ якорь регистрации страниц не найден.")
        return False

    if not izmeneno:
        print("  = патч уже накатан целиком, делать нечего")
        return True

    # СТОП-КРАН: сперва проверяем, потом пишем
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ после правки main.py не парсится: {e}")
        print("  ФАЙЛ НЕ ЗАПИСАН — ничего не сломано.")
        return False

    bak = MAIN.with_suffix(".py.bak_akademia")
    shutil.copy2(MAIN, bak)
    MAIN.write_text(novyy, encoding="utf-8")
    print(f"  ✓ бэкап: {bak.name}")
    print(f"  ✓ правки: {', '.join(izmeneno)}")
    return True


def shag_3_proverka():
    print("── ШАГ 3: проверка ──")
    f = KOD / "ui_akademia.py"
    if not f.exists():
        print(f"  ⚠ {f} не найден — положи файл кабинета в папку Академия/")
        return False
    try:
        ast.parse(f.read_text(encoding="utf-8"))
        print("  ✓ ui_akademia.py парсится")
    except SyntaxError as e:
        print(f"  ✗ ui_akademia.py не парсится: {e}")
        return False
    try:
        ast.parse(MAIN.read_text(encoding="utf-8"))
        print("  ✓ main.py парсится")
    except SyntaxError as e:
        print(f"  ✗ main.py не парсится: {e}")
        return False
    return True


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("═══ PATCH_AKADEMIA_V1 ═══")
    print(f"корень: {ROOT}\n")
    ok = shag_1_dvor() and shag_2_main() and shag_3_proverka()
    print()
    if ok:
        print("✅ ГОТОВО. Запускай:  python main.py")
        print("   Кабинет Академии:  http://localhost:8080/akademia")
    else:
        print("❌ Не докатилось — смотри сообщения выше. Ничего не сломано.")
    print("`шесть·проверено·до·корня`")
