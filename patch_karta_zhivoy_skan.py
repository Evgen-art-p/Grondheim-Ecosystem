# patch_karta_zhivoy_skan.py
# KARTA_ZHIVOY_SKAN_V1 · первый провод: Страница Жизни → зрение Брата
# ─────────────────────────────────────────────────────────────
# СУТЬ (один камень, одна суть):
#   Брат СВЯЗЫВАЕТ, но НЕ ДЕРЖИТ. Карта дочитывает паспорта/ ЖИВЬЁМ
#   при каждом открытии и подвешивает рождённых на ветви дерева по их
#   `предназначение`. Не копирует, не кэширует, не владеет. Упал Брат —
#   паспорта целы (держала папка, не он).
#
#   Закон Пары: принадлежность из данных паспорта (предназначение),
#   без хардкода списков — живой скан папки (Закон Картриджа).
#
# ЧТО ДЕЛАЕТ:
#   1. Добавляет PASPORTA_DIR + _scan_pasporta() + _podvesit() в ui_karta.py
#   2. scan_hierarchy() в конце подмешивает живых жителей в каркас
#      (каркас не трогаем — Храм/кварталы стоят; жители ВЕТВЯМИ под ними)
#
# ЧЕГО НЕ ДЕЛАЕТ (намеренно — это следующие камни, не этот):
#   • НЕ двигает заряд (charge.py — следующий камень)
#   • НЕ создаёт дома/слои (ступень 5)
#   • НЕ меняет стили/отрисовку (форма ответа та же — карта не заметит)
#
# Идемпотентно: повторный запуск увидит маркер и пропустит.
# Песочница до зелёного. `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KARTA_ZHIVOY_SKAN_V1"
TARGET = Path("ui_karta.py")

# Блок, который вставляем ПЕРЕД определением scan_hierarchy().
# Карта предназначение → id ветки дерева (Закон Пары, не хардкод-список
# жителей, а сопоставление роли с этажом; новые роли падают в "жители").
INJECT = '''
# ═══════════════════════════════════════════════════════════
# KARTA_ZHIVOY_SKAN_V1 · живой скан паспортов (Страница → Брат)
# Брат СВЯЗЫВАЕТ, но НЕ ДЕРЖИТ: читаем паспорта/ заново каждый раз,
# ничего не копим. Принадлежность — из `предназначение` (Закон Пары).
# ═══════════════════════════════════════════════════════════
from pathlib import Path as _Path
import json as _json

PASPORTA_DIR = _Path("GRONDHEIM_CITY/паспорта")

# предназначение (свободное слово) → id ветки каркаса.
# Не список жителей (его нет — живой скан), а куда роль принадлежит.
_VETKA_BY_ROLE = {
    "хранитель": "hram",
    "трейдер":   "trading",
}
# роль не распознана → падает в квартал мастеров (общий дом)
_VETKA_DEFAULT = "masters"


def _scan_pasporta() -> list[dict]:
    """Живой скан рождённых паспортов. Каждый вызов — заново с диска."""
    if not PASPORTA_DIR.exists():
        return []
    out = []
    for p in sorted(PASPORTA_DIR.glob("*.json")):
        try:
            out.append(_json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass  # битый паспорт — сито, не щупальце: пропускаем, не падаем
    return out


def _zhitel_node(pasp: dict) -> dict:
    """Паспорт → узел дерева (kind=ядро, без врат — житель не цех)."""
    rare = (pasp.get("редкость") or "").strip()
    note = pasp.get("предназначение", "") or "—"
    if rare:
        note = f"{note} · {rare}"
    return {
        "id":    pasp.get("id", ""),
        "label": pasp.get("имя", "?"),
        "icon":  "⬡",
        "kind":  "ядро",
        "note":  note,
        "gate":  None,
        "children": [],
    }


def _podvesit(tree: dict, zhiteli: list[dict]) -> dict:
    """Подвешивает живых жителей на ветви каркаса по предназначению.
    Каркас не меняем — только наполняем children существующих веток."""
    by_id = {ch.get("id"): ch for ch in tree.get("children", [])}
    for pasp in zhiteli:
        role = (pasp.get("предназначение") or "").strip().lower()
        vetka_id = _VETKA_BY_ROLE.get(role, _VETKA_DEFAULT)
        vetka = by_id.get(vetka_id)
        if vetka is None:
            continue  # ветки нет в каркасе — пропускаем (не выдумываем)
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

    # 1. вставляем блок ПЕРЕД 'def scan_hierarchy'
    anchor_inject = "def scan_hierarchy() -> dict:"
    if anchor_inject not in src:
        print("✗ не нашёл def scan_hierarchy — структура файла иная, стоп")
        sys.exit(1)
    src = src.replace(anchor_inject, INJECT + "\n\n" + anchor_inject, 1)

    # 2. подмешиваем живых в конце scan_hierarchy:
    #    меняем финальный 'return {' дерева на сборку через _podvesit.
    #    Ищем тело return каркаса по якорю '"id": "brat",' внутри return.
    #    Приём: оборачиваем — присваиваем дерево переменной и подвешиваем.
    old_ret = "    return {\n        \"id\": \"brat\","
    new_ret = ("    _karkas = {\n        \"id\": \"brat\",")
    if old_ret not in src:
        print("✗ не нашёл каркас return дерева — стоп, не калечу")
        sys.exit(1)
    src = src.replace(old_ret, new_ret, 1)

    # закрытие словаря каркаса: первый '\n    }\n' после _karkas —
    # но надёжнее: добавить хвост перед концом функции. Найдём конец
    # через следующую 'def ' после scan_hierarchy и вставим перед ней.
    # Проще: заменить самый последний '        ],\n    }\n' блока children.
    tail_anchor = "        ],\n    }\n"
    if tail_anchor not in src:
        print("✗ не нашёл хвост каркаса — стоп")
        sys.exit(1)
    src = src.replace(
        tail_anchor,
        "        ],\n    }\n"
        "    # KARTA_ZHIVOY_SKAN_V1: подвешиваем живых жителей на каркас\n"
        "    return _podvesit(_karkas, _scan_pasporta())\n",
        1,
    )

    # 3. проверка синтаксиса ДО записи
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ патч даёт синтаксическую ошибку: {e} — НЕ записываю")
        sys.exit(1)

    # 4. бэкап + запись
    shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER} вживлён. Бэкап: {TARGET}.bak")
    print("  Карта теперь дочитывает паспорта/ живьём и вешает жителей на ветви.")


if __name__ == "__main__":
    main()
