# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ХРАМ В СПИСКЕ ЦЕХОВ                                   ║
║                                                              ║
║  Беда: в выпадашке «Цех» нет Храма → негде выбрать,          ║
║  чтобы родить хранителя.                                     ║
║                                                              ║
║  Чиним:                                                      ║
║    • WORKSHOP_OPTIONS += "hram"  (Храм в списке цехов)       ║
║    • ROLE_OPTIONS_MAP["hram"] = роли-хранители              ║
║    • _WORKSHOP_QUARTER["hram"] = "Храм"                     ║
║                                                              ║
║  Теперь: выбрал цех «hram» → в ролях хранители →            ║
║  родил → летит в Hexagon/3_guardians/ (патч hranitel).      ║
║  Идемпотентно. `шесть·проверено·до·корня`                    ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path("ui_registry.py")
MARK = "# PATCH_HRAM_V_CEHI_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def main():
    if not TARGET.exists():
        fail("ui_registry.py не найден — запускай из корня Grondheim-Ecosystem")
    src = TARGET.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ] ⊙ Храм уже в списке цехов — пропускаю")
        return

    changed = 0

    # ── 1. WORKSHOP_OPTIONS: добавить "hram" первым (после residents) ──
    old_ws = (
        'WORKSHOP_OPTIONS = [\n'
        '    "", "residents", "turbo",\n'
    )
    new_ws = (
        'WORKSHOP_OPTIONS = [\n'
        '    "", "residents", "hram", "turbo",  # PATCH: Храм в цехах\n'
    )
    if old_ws in src:
        src = src.replace(old_ws, new_ws, 1)
        changed += 1
        print("[ПАТЧ] ✓ Храм добавлен в WORKSHOP_OPTIONS")
    else:
        print("[ПАТЧ] ⚠ WORKSHOP_OPTIONS не совпал — проверю свежий")

    # ── 2. Роли-хранители: новый список + в ROLE_OPTIONS_MAP ──
    # Вставляем HRAM_ROLE_OPTIONS перед ROLE_OPTIONS_MAP
    anchor_map = 'ROLE_OPTIONS_MAP = {\n'
    if anchor_map not in src:
        fail("ROLE_OPTIONS_MAP не найден — покажи свежий файл")

    hram_roles = (
        '# ── PATCH: роли Храма — хранители (есть в Hexagon/3_guardians) ──\n'
        'HRAM_ROLE_OPTIONS = [\n'
        '    "", "хранитель", "хранительница",\n'
        '    "lia", "key", "finch", "victor", "yust",\n'
        ']\n'
        '\n'
        'ROLE_OPTIONS_MAP = {\n'
        '    "hram":         HRAM_ROLE_OPTIONS,  # PATCH: Храм → хранители\n'
    )
    src = src.replace(anchor_map, hram_roles, 1)
    changed += 1
    print("[ПАТЧ] ✓ HRAM_ROLE_OPTIONS добавлены, Храм → хранители в ROLE_OPTIONS_MAP")

    # ── 3. _WORKSHOP_QUARTER: Храм → квартал "Храм" ──
    # Чтобы автозаполнение квартала не падало в "Квартал Мастеров"
    if '"trading": "Торговый Квартал"}' in src:
        src = src.replace(
            '"trading": "Торговый Квартал"}',
            '"trading": "Торговый Квартал", "hram": "Храм"}',
            1,
        )
        changed += 1
        print("[ПАТЧ] ✓ Храм → квартал «Храм» в _WORKSHOP_QUARTER")
    else:
        print("[ПАТЧ] ⚠ _WORKSHOP_QUARTER не совпал — квартал Храма не авто (не критично)")

    # ── 4. чтобы хранитель из Храма летел в 3_guardians ──
    # Патч hranitel_v_hram ловит по Profession. Тут добавим: если цех hram —
    # предназначение становится "хранитель" автоматически при рождении.
    # Ищем сбор obj в save_object: добавим строку после Workshop_ID.
    # (мягко — через Profession, который уже ловится)
    # Это делаем только если есть строка сбора Workshop_ID.
    if 'obj["Workshop_ID"] = workshop_widget["w"].value or ""' in src:
        old_line = '                        if workshop_widget["w"]: obj["Workshop_ID"] = workshop_widget["w"].value or ""'
        if old_line in src:
            new_line = (
                old_line + '\n'
                '                        # PATCH: цех Храм → предназначение "хранитель" (летит в 3_guardians)\n'
                '                        if (obj.get("Workshop_ID") or "") == "hram" and not (obj.get("Profession") or "").strip():\n'
                '                            obj["Profession"] = "хранитель"'
            )
            src = src.replace(old_line, new_line, 1)
            changed += 1
            print("[ПАТЧ] ✓ цех Храм → авто-предназначение «хранитель»")
        else:
            print("[ПАТЧ] ⚠ строка Workshop_ID с отступом не совпала — впиши Profession='хранитель' вручную")
    else:
        print("[ПАТЧ] ⚠ сбор Workshop_ID не найден — впиши Profession='хранитель' вручную")

    # метка
    src = src.replace('import json\n', f'import json\n{MARK}\n', 1)
    if MARK not in src:
        src = MARK + "\n" + src

    if changed == 0:
        fail("ничего не совпало — покажи свежий ui_registry.py")

    TARGET.write_text(src, encoding="utf-8")
    print()
    print(f"[ПАТЧ] ✓ Готово ({changed} правок). Храм в списке цехов.")
    print("       В форме: Цех → выбери «hram» → роль «хранитель» →")
    print("       родил → летит в GRONDHEIM_CITY/Hexagon/3_guardians/{имя}/")


if __name__ == "__main__":
    main()
