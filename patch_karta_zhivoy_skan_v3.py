# patch_karta_zhivoy_skan_v3.py
# KARTA_ZHIVOY_SKAN_V3 · провод Страница → Брат, по РЕАЛЬНОМУ формату города
# ─────────────────────────────────────────────────────────────
# V2 — исправляет V1, который строился на формате рожаницы (паспорта/,
# "предназначение"), а город рождает реестром (ui_registry): жители/,
# "Workshop_ID", "Official_Name". Снято с живого паспорта Лии.
#
# СУТЬ: Брат СВЯЗЫВАЕТ, не ДЕРЖИТ. Карта дочитывает жителей живьём
# при каждом открытии. Принадлежность — из паспорта (Workshop_ID),
# Закон Пары. Двуязычно: понимает ОБА формата (реестр + рожаница).
#
# РЕАЛЬНАЯ СТРУКТУРА (снято с репы):
#   жители/{Profession}/{Official_Name}.json   ← паспорт-лицо (берём ЕГО)
#   жители/{Profession}/{Official_Name}/        ← дом жителя
#       passport.json + core/resonance/sensory/archive  ← НЕ считать паспортом
#
# Ключи паспорта (формат реестра):
#   Official_Name · Workshop_ID(hram/trading/..) · Social_Rank · Rarity · Profession
# Фоллбэк (формат рожаницы): имя · предназначение
#
# Идемпотентно. Песочница до зелёного. `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KARTA_ZHIVOY_SKAN_V3"
TARGET = Path("ui_karta.py")

INJECT = '''
# ═══════════════════════════════════════════════════════════
# KARTA_ZHIVOY_SKAN_V3 · живой скан жителей (Страница → Брат)
# Брат СВЯЗЫВАЕТ, не ДЕРЖИТ: читаем жителей/ заново каждый раз.
# Принадлежность — из паспорта (Workshop_ID), Закон Пары.
# Двуязычно: формат реестра (Official_Name/Workshop_ID) + рожаницы.
# ═══════════════════════════════════════════════════════════
from pathlib import Path as _Path
import json as _json

# Путь от РАСПОЛОЖЕНИЯ этого файла (= корень репы), НЕ от рабочей папки.
# Лечит «запуск не из корня»: откуда ни стартуй main.py — жители найдутся.
_ROOT = _Path(__file__).resolve().parent
ZHITELI_DIR = _ROOT / "GRONDHEIM_CITY" / "жители"
GUARDIANS_DIR = _ROOT / "GRONDHEIM_CITY" / "Hexagon" / "3_guardians"  # хранители

# Workshop_ID / роль → id ветки каркаса. Не список жителей (живой скан),
# а куда принадлежность ведёт. Неизвестное → masters (общий дом).
_VETKA_BY_WORKSHOP = {
    "hram":        "hram",
    "trading":     "trading",
    "living_book": "living_book",
}
_VETKA_BY_RANK = {       # фоллбэк по Social_Rank, если нет Workshop_ID
    "хранитель": "hram",
    "трейдер":   "trading",
}
_VETKA_DEFAULT = "masters"

# имена внутренних файлов дома — НЕ паспорта-лица (чтоб не считать дважды)
_DOM_FILES = {"passport.json"}


def _vetka_for(pasp: dict) -> str:
    """Куда житель принадлежит на карте. Workshop_ID → Social_Rank → дефолт."""
    wid = (pasp.get("Workshop_ID") or "").strip().lower()
    if wid in _VETKA_BY_WORKSHOP:
        return _VETKA_BY_WORKSHOP[wid]
    rank = (pasp.get("Social_Rank") or "").strip().lower()
    if rank in _VETKA_BY_RANK:
        return _VETKA_BY_RANK[rank]
    # фоллбэк на формат рожаницы
    role = (pasp.get("предназначение") or "").strip().lower()
    if "хранит" in role:
        return "hram"
    if "трейд" in role or "торг" in role:
        return "trading"
    return _VETKA_DEFAULT


def _name_of(pasp: dict) -> str:
    return (pasp.get("Official_Name")
            or pasp.get("имя")
            or pasp.get("id")
            or "?")


def _note_of(pasp: dict) -> str:
    prof = (pasp.get("Profession") or pasp.get("предназначение")
            or pasp.get("Social_Rank") or "—")
    rare = (pasp.get("Rarity") or pasp.get("редкость") or "").strip()
    prof = prof.strip().rstrip(".")
    return f"{prof} · {rare}" if rare else prof


def _scan_zhiteli() -> list[dict]:
    """Живой скан жителей. Рекурсивно по жители/ + guardians.
    Берём паспорт-ЛИЦО (внешний {имя}.json), внутренний дом passport.json
    пропускаем — это один житель, не два."""
    found = []
    for base in (ZHITELI_DIR, GUARDIANS_DIR):
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.json")):
            if p.name in _DOM_FILES:
                continue  # внутренний паспорт дома — пропускаем (двойник)
            try:
                found.append(_json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                pass  # битый — сито, не щупальце
    return found


def _zhitel_node(pasp: dict) -> dict:
    return {
        "id":    pasp.get("ID_Object") or pasp.get("id") or _name_of(pasp),
        "label": _name_of(pasp),
        "icon":  "⬡",
        "kind":  "ядро",
        "note":  _note_of(pasp),
        "gate":  None,
        "children": [],
    }


def _podvesit(tree: dict, zhiteli: list[dict]) -> dict:
    """Вешает живых жителей на ветви каркаса по принадлежности.
    Каркас не меняем — наполняем children существующих веток."""
    by_id = {ch.get("id"): ch for ch in tree.get("children", [])}
    for pasp in zhiteli:
        vetka = by_id.get(_vetka_for(pasp))
        if vetka is None:
            continue
        vetka.setdefault("children", []).append(_zhitel_node(pasp))
    return tree
'''


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускай из корня Grondheim-Ecosystem")
        sys.exit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю (идемпотентно)")
        return

    # защита: если V1 был накачен — откатить к бэкапу сначала
    if "KARTA_ZHIVOY_SKAN_V1" in src:
        bak = TARGET.with_suffix(".py.bak")
        if bak.exists():
            print("⚠ обнаружен V1 — откатываю к бэкапу перед V2")
            src = bak.read_text(encoding="utf-8")
        else:
            print("✗ V1 накачен, но бэкапа нет — останови и проверь руками")
            sys.exit(1)

    anchor = "def scan_hierarchy() -> dict:"
    if anchor not in src:
        print("✗ не нашёл def scan_hierarchy — структура иная, стоп")
        sys.exit(1)
    src = src.replace(anchor, INJECT + "\n\n" + anchor, 1)

    old_ret = "    return {\n        \"id\": \"brat\","
    if old_ret not in src:
        print("✗ не нашёл каркас return — стоп, не калечу")
        sys.exit(1)
    src = src.replace(old_ret, "    _karkas = {\n        \"id\": \"brat\",", 1)

    tail = "        ],\n    }\n"
    if tail not in src:
        print("✗ не нашёл хвост каркаса — стоп")
        sys.exit(1)
    src = src.replace(
        tail,
        "        ],\n    }\n"
        "    # KARTA_ZHIVOY_SKAN_V3: живые жители на каркас\n"
        "    return _podvesit(_karkas, _scan_zhiteli())\n",
        1,
    )

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксическая ошибка: {e} — НЕ записываю")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER} вживлён.")
    print("  Карта дочитывает жители/ живьём по Workshop_ID. Лия → Храм.")


if __name__ == "__main__":
    main()
