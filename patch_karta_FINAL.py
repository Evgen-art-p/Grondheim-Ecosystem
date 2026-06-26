# patch_karta_FINAL.py
# KARTA_ZHIVOY_SKAN_FINAL · замена начисто, по диагностике с диска Шефа
# ─────────────────────────────────────────────────────────────
# Диагностика показала ПРАВДУ:
#   • путь верный, папка есть, паспорт Лии читается, Workshop_ID=hram ✓
#   • НО дом содержит КОПИЮ паспорта в core/anchor.json (тоже hram!)
#     + resonance/sensory с мусором → старый скан удвоил бы Лию + хлам
#
# Этот патч НЕ накатывается поверх — он ЗАМЕНЯЕТ начисто:
#   1. срезает любые прошлые мои вставки (V1/V2/V3 — что бы ни наслоилось)
#   2. ставит ОДИН верный скан со строгим правилом:
#      читать ТОЛЬКО паспорт-лицо в КОРНЕ папки профессии
#      (жители/{профессия}/{имя}.json), в дом НЕ спускаться.
#
# Путь — от __file__ (корень репы), не от рабочей папки.
# Идемпотентно. `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import re
import shutil
import sys
from pathlib import Path

MARKER = "KARTA_ZHIVOY_SKAN_FINAL"
TARGET = Path(__file__).resolve().parent / "ui_karta.py"

# Новый блок скана — кладётся ПЕРЕД scan_hierarchy.
SCAN_BLOCK = '''# ═══════════════════════════════════════════════════════════
# KARTA_ZHIVOY_SKAN_FINAL · живой скан жителей (Страница → Брат)
# Брат СВЯЗЫВАЕТ, не ДЕРЖИТ: читаем жителей заново каждый раз.
# СТРОГО: только паспорт-лицо в КОРНЕ папки профессии. В дом
# (passport.json, core/resonance/sensory/archive) НЕ спускаемся —
# иначе копия паспорта в core/ удвоит жителя (урок диагностики).
# Путь — от __file__ (корень репы), не от рабочей папки.
# ═══════════════════════════════════════════════════════════
from pathlib import Path as _Path
import json as _json

_ROOT = _Path(__file__).resolve().parent
ZHITELI_DIR = _ROOT / "GRONDHEIM_CITY" / "жители"
GUARDIANS_DIR = _ROOT / "GRONDHEIM_CITY" / "Hexagon" / "3_guardians"

# имена папок-слоёв дома — в них НЕ заходим
_DOM_SLOI = {"core", "resonance", "sensory", "archive"}

_VETKA_BY_WORKSHOP = {"hram": "hram", "trading": "trading", "living_book": "living_book"}
_VETKA_BY_RANK = {"хранитель": "hram", "трейдер": "trading"}
_VETKA_DEFAULT = "masters"


def _vetka_for(p):
    wid = (p.get("Workshop_ID") or "").strip().lower()
    if wid in _VETKA_BY_WORKSHOP:
        return _VETKA_BY_WORKSHOP[wid]
    rank = (p.get("Social_Rank") or "").strip().lower()
    if rank in _VETKA_BY_RANK:
        return _VETKA_BY_RANK[rank]
    role = (p.get("предназначение") or "").strip().lower()
    if "хранит" in role:
        return "hram"
    if "трейд" in role or "торг" in role:
        return "trading"
    return _VETKA_DEFAULT


def _name_of(p):
    return p.get("Official_Name") or p.get("имя") or p.get("id") or "?"


def _note_of(p):
    prof = (p.get("Profession") or p.get("предназначение") or p.get("Social_Rank") or "—").strip().rstrip(".")
    rare = (p.get("Rarity") or p.get("редкость") or "").strip()
    return f"{prof} · {rare}" if rare else prof


def _scan_zhiteli():
    """Только паспорта-ЛИЦА в корне папок профессий. Дом не трогаем.
    Структура: жители/{профессия}/{имя}.json  ← берём
               жители/{профессия}/{имя}/...     ← дом, пропускаем."""
    found = []
    for base in (ZHITELI_DIR, GUARDIANS_DIR):
        if not base.exists():
            continue
        # base/{профессия}/ — внутри каждой профессии берём *.json В КОРНЕ
        for prof_dir in base.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                # только файлы .json прямо в папке профессии (паспорт-лицо),
                # папки-дома (item.is_dir()) пропускаем целиком
                if item.is_file() and item.suffix == ".json":
                    try:
                        found.append(_json.loads(item.read_text(encoding="utf-8")))
                    except Exception:
                        pass
    return found


def _zhitel_node(p):
    return {
        "id": p.get("ID_Object") or p.get("id") or _name_of(p),
        "label": _name_of(p),
        "icon": "⬡",
        "kind": "ядро",
        "note": _note_of(p),
        "gate": None,
        "children": [],
    }


def _podvesit(tree, zhiteli):
    by_id = {ch.get("id"): ch for ch in tree.get("children", [])}
    for p in zhiteli:
        v = by_id.get(_vetka_for(p))
        if v is None:
            continue
        v.setdefault("children", []).append(_zhitel_node(p))
    return tree


'''


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET}")
        sys.exit(1)

    src = TARGET.read_text(encoding="utf-8")

    # 1. ВСЕГДА восстанавливаем чистый каркас, если есть .bak от прошлых патчей
    bak = TARGET.with_suffix(".py.bak")
    if any(m in src for m in ("KARTA_ZHIVOY_SKAN_V1", "KARTA_ZHIVOY_SKAN_V2",
                               "KARTA_ZHIVOY_SKAN_V3", MARKER)):
        if bak.exists():
            print("⚠ нашёл прошлые версии скана — беру чистый каркас из .bak")
            src = bak.read_text(encoding="utf-8")
        else:
            print("⚠ прошлые версии есть, но .bak нет — чищу вставки по месту")
            # срезаем наш блок: от маркера-комментаря до scan_hierarchy
            src = re.sub(
                r"# ═+\n# KARTA_ZHIVOY_SKAN_V\d.*?(?=def scan_hierarchy)",
                "", src, flags=re.DOTALL)
            # возвращаем _karkas → return и убираем хвост _podvesit
            src = src.replace('    _karkas = {\n        "id": "brat",',
                              '    return {\n        "id": "brat",')
            src = re.sub(r"    # KARTA_ZHIVOY_SKAN_V\d.*\n    return _podvesit\(_karkas, _scan_zhiteli\(\)\)\n",
                         "", src)

    # теперь src — чистый каркас. Проверим, что он валиден и есть якорь.
    anchor = "def scan_hierarchy() -> dict:"
    if anchor not in src:
        print("✗ в каркасе нет scan_hierarchy — структура неожиданная, стоп")
        sys.exit(1)

    # 2. вставляем чистый SCAN_BLOCK перед scan_hierarchy
    src = src.replace(anchor, SCAN_BLOCK + anchor, 1)

    # 3. меняем return каркаса на сборку с живыми
    old_ret = '    return {\n        "id": "brat",'
    if old_ret not in src:
        print("✗ не нашёл return каркаса в чистом файле — стоп")
        sys.exit(1)
    src = src.replace(old_ret, '    _karkas = {\n        "id": "brat",', 1)

    tail = "        ],\n    }\n"
    if tail not in src:
        print("✗ не нашёл хвост каркаса — стоп")
        sys.exit(1)
    src = src.replace(
        tail,
        "        ],\n    }\n"
        "    # KARTA_ZHIVOY_SKAN_FINAL: живые жители на каркас\n"
        "    return _podvesit(_karkas, _scan_zhiteli())\n",
        1,
    )

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e} — НЕ записываю")
        sys.exit(1)

    # бэкап чистого каркаса (если ещё нет)
    if not bak.exists():
        shutil.copy2(TARGET, bak)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER} поставлен начисто.")
    print("  Скан читает только паспорта-лица. Дом не трогает. Лия → Храм, один раз.")


if __name__ == "__main__":
    main()
