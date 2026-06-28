# patch_find_dom_kovcheg.py
# FIND_DOM_KOVCHEG_V1 · find_dom/list_zhiteli ищут паспорт в реальном месте
# ─────────────────────────────────────────────────────────────
# Баг (найден 28.06): find_dom искал паспорт-лицо как ОТДЕЛЬНЫЙ .json-файл
# рядом с папкой дома (старый паттерн жители/{профессия}/{имя}.json +
# жители/{профессия}/{имя}/). Но рождение (ROZHDENIE_TONKOE_V1, zavesti_sloi
# в ui_registry.py) реально кладёт паспорт ВНУТРИ папки дома:
#   жители/ковчег/{имя}/passport.json
# Эти два паттерна не совпадали — find_dom().iterdir() видел только папки
# на уровне ковчег/, а .json внутри них не проверял. Поэтому ни один реально
# рождённый житель не находился по ссылке /zhitel/{id} — "никто не открывается".
#
# Чинит ТОЛЬКО поиск в ZHITELI_DIR (ковчег и будущие районы) — структура
# реально такая: {база}/{подпапка}/{имя}/passport.json. GUARDIANS_DIR
# (Hexagon/3_guardians) НЕ трогаем — неизвестно, в каком формате там
# реально лежат хранители, чинить то, что не подтверждено сломанным,
# не будем.
#
# Делает в ui_zhitel.py:
#   1. find_dom(): для ZHITELI_DIR смотрит passport.json ВНУТРИ каждой
#      папки-дома (на уровень глубже), не рядом как отдельный файл.
#      GUARDIANS_DIR — старый код без изменений (на случай старого формата).
#   2. list_zhiteli(): та же правка симметрично.
#
# Идемпотентно. Бэкап в .bak_find_dom_kovcheg.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "FIND_DOM_KOVCHEG_V1"
TARGET = Path(__file__).resolve().parent / "ui_zhitel.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_zhitel.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    # ── 1) find_dom: чинит поиск для ZHITELI_DIR (паспорт внутри папки дома) ──
    old_find = '''def find_dom(zid: str):
    """Дом жителя по ID_Object. Возвращает (паспорт, путь_дома) или (None, None).
    Дом = папка рядом с паспортом-лицом, где лежат слои core/.../passport.json."""
    for base in (ZHITELI_DIR, GUARDIANS_DIR):
        if not base.exists():
            continue
        for prof_dir in base.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                if item.is_file() and item.suffix == ".json":
                    try:
                        p = json.loads(item.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if str(p.get("ID_Object", "")) == str(zid):
                        # дом — папка тем же именем (без .json)
                        dom = item.with_suffix("")
                        if not dom.is_dir():
                            dom = prof_dir / item.stem
                        return p, dom
    return None, None'''

    new_find = '''def find_dom(zid: str):
    """Дом жителя по ID_Object. Возвращает (паспорт, путь_дома) или (None, None).

    FIND_DOM_KOVCHEG_V1: реальная структура рождения (ROZHDENIE_TONKOE_V1) —
    паспорт ВНУТРИ папки дома, не рядом как отдельный файл:
        жители/ковчег/{имя}/passport.json
    Старый паттерн (паспорт-лицо рядом с папкой) больше не строится при
    рождении — оставлен только для GUARDIANS_DIR на случай старого формата.
    """
    # ZHITELI_DIR (ковчег и будущие районы) — паспорт ВНУТРИ папки-дома
    if ZHITELI_DIR.exists():
        for prof_dir in ZHITELI_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for dom_dir in prof_dir.iterdir():
                if not dom_dir.is_dir():
                    continue
                passport_file = dom_dir / "passport.json"
                if not passport_file.exists():
                    continue
                try:
                    p = json.loads(passport_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if str(p.get("ID_Object", "")) == str(zid):
                    return p, dom_dir

    # GUARDIANS_DIR — старый паттерн (паспорт-лицо рядом с папкой), не трогаем
    if GUARDIANS_DIR.exists():
        for prof_dir in GUARDIANS_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                if item.is_file() and item.suffix == ".json":
                    try:
                        p = json.loads(item.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if str(p.get("ID_Object", "")) == str(zid):
                        dom = item.with_suffix("")
                        if not dom.is_dir():
                            dom = prof_dir / item.stem
                        return p, dom
    return None, None'''

    if old_find not in src:
        print("✗ шаг 1: не нашёл def find_dom — стоп")
        sys.exit(1)
    src = src.replace(old_find, new_find, 1)

    # ── 2) list_zhiteli: та же правка симметрично ──
    old_list = '''def list_zhiteli():
    """Все жители (для выбора, если zid не задан). Паспорта-лица."""
    out = []
    for base in (ZHITELI_DIR, GUARDIANS_DIR):
        if not base.exists():
            continue
        for prof_dir in base.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                if item.is_file() and item.suffix == ".json":
                    try:
                        p = json.loads(item.read_text(encoding="utf-8"))
                        out.append(p)
                    except Exception:
                        pass
    return out'''

    new_list = '''def list_zhiteli():
    """Все жители (для выбора, если zid не задан). Паспорта-лица.
    FIND_DOM_KOVCHEG_V1: та же логика поиска, что и в find_dom."""
    out = []
    if ZHITELI_DIR.exists():
        for prof_dir in ZHITELI_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for dom_dir in prof_dir.iterdir():
                if not dom_dir.is_dir():
                    continue
                passport_file = dom_dir / "passport.json"
                if not passport_file.exists():
                    continue
                try:
                    p = json.loads(passport_file.read_text(encoding="utf-8"))
                    out.append(p)
                except Exception:
                    pass
    if GUARDIANS_DIR.exists():
        for prof_dir in GUARDIANS_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                if item.is_file() and item.suffix == ".json":
                    try:
                        p = json.loads(item.read_text(encoding="utf-8"))
                        out.append(p)
                    except Exception:
                        pass
    return out'''

    if old_list not in src:
        print("✗ шаг 2: не нашёл def list_zhiteli — стоп")
        sys.exit(1)
    src = src.replace(old_list, new_list, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_find_dom_kovcheg").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_find_dom_kovcheg"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: find_dom/list_zhiteli ищут паспорт там, где он реально лежит")


if __name__ == "__main__":
    main()
