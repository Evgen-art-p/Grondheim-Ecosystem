# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ФОТО В ДОМ ЖИТЕЛЯ (через новый город)                ║
║                                                              ║
║  Было: save_image → 00_REGISTRY_NFT/images/ (старый реестр).║
║  Стало: фото → GRONDHEIM_CITY/_входящие_фото/ → при рождении║
║         переезжает в дом жителя как avatar.{ext}.           ║
║                                                              ║
║  Старый реестр НЕ рубим — просто перестаём кормить.         ║
║  Новые фото идут в новый город. Старый images/ — мёртвый.  ║
║                                                              ║
║  Почему через временную: фото грузится при ВЫБОРЕ файла,    ║
║  а дом известен при СОХРАНЕНИИ. Временная — мост.           ║
║                                                              ║
║  Идемпотентно. `шесть·проверено·до·корня`                    ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path("ui_registry.py")
MARK = "# PATCH_FOTO_V_DOM_NEW_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def main():
    if not TARGET.exists():
        fail("ui_registry.py не найден — запускай из корня Grondheim-Ecosystem")
    src = TARGET.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ] ⊙ фото уже едет в дом нового города — пропускаю")
        return

    if "def zavesti_sloi" not in src:
        fail("zavesti_sloi не найдена — примени patch_4_sloya.py сначала")

    # ── 1. Временная папка фото нового города — рядом с ZHITELI_DIR ──
    anchor_dir = 'ZHITELI_DIR = Path("GRONDHEIM_CITY/жители")\n'
    if anchor_dir not in src:
        fail("ZHITELI_DIR не найден — примени patch_dva_fila сначала")
    new_dir = anchor_dir + 'VHODYASHIE_FOTO = Path("GRONDHEIM_CITY/_входящие_фото")  # PATCH_FOTO_NEW: мост\n'
    src = src.replace(anchor_dir, new_dir, 1)

    # ── 2. save_image кладёт в новый город (не в старый реестр) ──
    old_save = (
        'def save_image(file_content: bytes, filename: str) -> str:\n'
        '    """Сохраняет картинку под оригинальным именем для реестра NFT."""\n'
        '    # Оставляем только чистое имя файла (на случай, если прилетел путь)\n'
        '    img_name = Path(filename).name \n'
        '    img_path = IMAGES_DIR / img_name\n'
        '    \n'
        '    # Записываем байты картинки на диск\n'
        '    img_path.write_bytes(file_content)\n'
        '    \n'
        '    # Возвращает путь, который сохранится в catalog.json \n'
        '    return str(img_path)\n'
    )
    new_save = (
        'def save_image(file_content: bytes, filename: str) -> str:\n'
        '    """PATCH_FOTO_NEW: фото во ВРЕМЕННУЮ папку нового города.\n'
        '    При рождении (zavesti_sloi) переедет в дом жителя как avatar.\n'
        '    Старый 00_REGISTRY_NFT/images/ больше не кормим."""\n'
        '    img_name = Path(filename).name\n'
        '    VHODYASHIE_FOTO.mkdir(parents=True, exist_ok=True)\n'
        '    img_path = VHODYASHIE_FOTO / img_name\n'
        '    img_path.write_bytes(file_content)\n'
        '    return str(img_path)\n'
    )
    if old_save in src:
        src = src.replace(old_save, new_save, 1)
        print("[ПАТЧ] ✓ save_image → GRONDHEIM_CITY/_входящие_фото/ (новый город)")
    else:
        fail("save_image не совпала дословно — покажи свежий ui_registry.py")

    # ── 3. zavesti_sloi: переносит фото из временной в дом как avatar ──
    anchor_sloi = (
        '    # маркер: слои заведены\n'
        '    mark = dom / "_слои_заведены.txt"\n'
        '    mark.write_text("core · resonance · sensory · archive\\nпамять пустая (ступень 5)",\n'
        '                    encoding="utf-8")\n'
        '\n'
        '    return str(dom)\n'
    )
    if anchor_sloi not in src:
        fail("конец zavesti_sloi не найден дословно — покажи свежий файл")

    foto_block = (
        '    # маркер: слои заведены\n'
        '    mark = dom / "_слои_заведены.txt"\n'
        '    mark.write_text("core · resonance · sensory · archive\\nпамять пустая (ступень 5)",\n'
        '                    encoding="utf-8")\n'
        '\n'
        '    # ── PATCH_FOTO_NEW: фото из временной → в дом жителя (avatar) ──\n'
        '    try:\n'
        '        import shutil as _sh\n'
        '        _src = obj.get("_image_path", "") or ""\n'
        '        if _src and Path(_src).exists():\n'
        '            _ext = Path(_src).suffix or ".png"\n'
        '            _dst = dom / f"avatar{_ext}"\n'
        '            _sh.copyfile(_src, _dst)\n'
        '            obj["_image_path"] = str(_dst)   # паспорт теперь смотрит в дом\n'
        '            obj["avatar"] = f"avatar{_ext}"\n'
        '            # чистим временную (фото переехало в дом)\n'
        '            try:\n'
        '                Path(_src).unlink(missing_ok=True)\n'
        '            except Exception:\n'
        '                pass\n'
        '            # перепишем паспорт с путём аватара в доме\n'
        '            _pj = json.dumps(obj, ensure_ascii=False, indent=2)\n'
        '            (dom / "passport.json").write_text(_pj, encoding="utf-8")\n'
        '            (dom / "core" / "anchor.json").write_text(_pj, encoding="utf-8")\n'
        '    except Exception:\n'
        '        pass  # нет фото — дом всё равно полный (паспорт + слои)\n'
        '\n'
        '    return str(dom)\n'
    )
    src = src.replace(anchor_sloi, foto_block, 1)
    print("[ПАТЧ] ✓ zavesti_sloi переносит фото в дом как avatar")

    # метка
    src = src.replace('import json\n', f'import json\n{MARK}\n', 1)
    if MARK not in src:
        src = MARK + "\n" + src

    TARGET.write_text(src, encoding="utf-8")
    print()
    print("[ПАТЧ] ✓ Готово. Фото едет в дом жителя.")
    print("       • грузишь фото → GRONDHEIM_CITY/_входящие_фото/ (мост)")
    print("       • рождаешь → фото переезжает в дом/avatar.{ext}")
    print("       • временное чистится")
    print("       • старый 00_REGISTRY_NFT/images/ больше не кормим")
    print()
    print("[ПАТЧ] Дом жителя теперь полный:")
    print("       passport.json · avatar · core/ resonance/ sensory/ archive/")


if __name__ == "__main__":
    main()
