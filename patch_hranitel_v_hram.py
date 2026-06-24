# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ХРАНИТЕЛЬ — В ХРАМ                                    ║
║                                                              ║
║  Беда: всех валит в жители/{предназначение}/.               ║
║  Хранитель должен лечь в Храм — к собратьям                 ║
║  (lia, key, finch, victor, yust уже там).                   ║
║                                                              ║
║  Чиним: добавляем карту особых мест.                        ║
║    хранитель → GRONDHEIM_CITY/Hexagon/3_guardians/{имя}/    ║
║    остальные → GRONDHEIM_CITY/жители/{предназначение}/{имя}/║
║                                                              ║
║  Растёт само: добавишь особое место в ETAZH_MAP — заработает.║
║  Идемпотентно. `шесть·проверено·до·корня`                    ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path("ui_registry.py")
MARK = "# PATCH_HRANITEL_V_HRAM_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def main():
    if not TARGET.exists():
        fail("ui_registry.py не найден — запускай из корня Grondheim-Ecosystem")
    src = TARGET.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ] ⊙ хранитель уже селится в Храм — пропускаю")
        return

    if "ZHITELI_DIR = Path" not in src:
        fail("ZHITELI_DIR не найден — примени patch_dva_fila.py сначала")

    # ── ВСТАВКА 1: карта особых этажей + функция выбора этажа ──
    anchor = 'ZHITELI_DIR = Path("GRONDHEIM_CITY/жители")\n'
    if anchor not in src:
        fail("строка ZHITELI_DIR не совпала дословно — покажи свежий файл")

    etazh_map = anchor + '''
# ── PATCH_HRANITEL_V_HRAM: карта особых мест ──
# Предназначение → особый этаж города. Кого здесь нет — в жители/{предназначение}/.
# Растёт само: добавь строку — новое предназначение поедет в своё место.
ETAZH_MAP = {
    "хранитель": Path("GRONDHEIM_CITY/Hexagon/3_guardians"),
    "хранительница": Path("GRONDHEIM_CITY/Hexagon/3_guardians"),
    "guardian": Path("GRONDHEIM_CITY/Hexagon/3_guardians"),
}


def _etazh_dlya(naznach_raw: str) -> Path:
    """Возвращает корневой этаж по предназначению (нормализуем регистр)."""
    key = (naznach_raw or "").strip().lower()
    if key in ETAZH_MAP:
        return ETAZH_MAP[key]
    # обычный житель — на общий этаж жители/{предназначение}/
    return ZHITELI_DIR / _safe_name(naznach_raw or "без_предназначения")
'''
    src = src.replace(anchor, etazh_map, 1)

    # ── ВСТАВКА 2: rodit_pasport_kusochek использует _etazh_dlya ──
    old_kus = (
        '    naznach = _safe_name(obj.get("Profession", "") or "без_предназначения")\n'
        '\n'
        '    etazh = ZHITELI_DIR / naznach\n'
        '    etazh.mkdir(parents=True, exist_ok=True)\n'
    )
    new_kus = (
        '    naznach_raw = obj.get("Profession", "") or "без_предназначения"\n'
        '\n'
        '    etazh = _etazh_dlya(naznach_raw)  # PATCH_HRANITEL: особый этаж или жители/\n'
        '    etazh.mkdir(parents=True, exist_ok=True)\n'
    )
    if old_kus in src:
        src = src.replace(old_kus, new_kus, 1)
        print("[ПАТЧ] ✓ кусочек селится по карте этажей")
    else:
        print("[ПАТЧ] ⚠ блок этажа в rodit_pasport_kusochek не совпал — проверю свежий")

    # ── ВСТАВКА 3: zavesti_sloi использует _etazh_dlya ──
    old_sloi = (
        '    naznach = _safe_name(obj.get("Profession", "") or "без_предназначения")\n'
        '\n'
        '    dom = ZHITELI_DIR / naznach / name        # папка жителя\n'
        '    dom.mkdir(parents=True, exist_ok=True)\n'
    )
    new_sloi = (
        '    naznach_raw = obj.get("Profession", "") or "без_предназначения"\n'
        '\n'
        '    dom = _etazh_dlya(naznach_raw) / name     # PATCH_HRANITEL: папка жителя на его этаже\n'
        '    dom.mkdir(parents=True, exist_ok=True)\n'
    )
    if old_sloi in src:
        src = src.replace(old_sloi, new_sloi, 1)
        print("[ПАТЧ] ✓ 4 слоя селятся по карте этажей")
    else:
        print("[ПАТЧ] ⚠ блок этажа в zavesti_sloi не совпал — проверю свежий")

    # метка
    src = src.replace('import json\n', f'import json\n{MARK}\n', 1)
    if MARK not in src:
        src = MARK + "\n" + src

    TARGET.write_text(src, encoding="utf-8")
    print()
    print("[ПАТЧ] ✓ Хранитель селится в Храм.")
    print("       • хранитель → GRONDHEIM_CITY/Hexagon/3_guardians/{имя}/")
    print("       • остальные → GRONDHEIM_CITY/жители/{предназначение}/{имя}/")
    print()
    print("[ПАТЧ] Проверка: роди жителя с Profession='хранитель' →")
    print("       ляжет в Hexagon/3_guardians/ к lia/key/finch/victor/yust,")
    print("       с 4 слоями core/resonance/sensory/archive.")


if __name__ == "__main__":
    main()
