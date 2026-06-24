# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: 4 СЛОЯ — папки жителя ложатся в core/resonance/       ║
║         sensory/archive на его этаже                         ║
║                                                              ║
║  Что делает:                                                 ║
║    1. Добавляет zavesti_sloi() — заводит 4 слоя-папки        ║
║       рядом с паспортом-кусочком, на этаже по предназначению.║
║    2. Зовёт её из save_object после рождения кусочка.        ║
║                                                              ║
║  4 слоя (наш закон):                                         ║
║    🦴 core      — якорь (паспорт ложится сюда)              ║
║    🩸 resonance — связи (пусто, живёт)                      ║
║    ⚡ sensory   — оперативка (пусто, живёт)                 ║
║    🌑 archive   — глубина (пусто, копится)                  ║
║                                                              ║
║  Память ПУСТАЯ — слои только заводятся (наполнение=ступень 5)║
║  Старую generate_agent_files НЕ трогаем (спит под if False). ║
║  Идемпотентно. `шесть·проверено·до·корня`                    ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path("ui_registry.py")
MARK = "# PATCH_4_SLOYA_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def main():
    if not TARGET.exists():
        fail("ui_registry.py не найден — запускай из корня Grondheim-Ecosystem")
    src = TARGET.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ] ⊙ 4 слоя уже включены — пропускаю (идемпотентно)")
        return

    # Нужна функция rodit_pasport_kusochek (от предыдущего патча dva_fila)
    if "def rodit_pasport_kusochek" not in src:
        fail("не найдена rodit_pasport_kusochek — сначала примени patch_dva_fila.py")

    # ── ВСТАВКА 1: функция zavesti_sloi после rodit_pasport_kusochek ──
    # Якорь — конец функции kусочка (строка 'return str(out)' внутри неё).
    # Ищем её и вставляем новую функцию следом.
    anchor = (
        '    out = etazh / f"{name}.json"\n'
        '    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")\n'
        '    return str(out)\n'
    )
    if anchor not in src:
        fail("конец rodit_pasport_kusochek не найден дословно — покажи свежий ui_registry.py")

    new_func = anchor + '''

# ── PATCH_4_SLOYA: заводим 4 слоя памяти на этаже жителя ──
# core/resonance/sensory/archive. Память ПУСТАЯ — слои только заводятся.
# Кусочек {имя}.json становится папкой {имя}/ с паспортом и слоями.
def zavesti_sloi(obj: dict) -> str:
    """
    Заводит 4 слоя-папки жителя на его этаже (по предназначению).
    Превращает плоский кусочек в папку:
        жители/{предназначение}/{имя}/
            passport.json   ← ядро (= core, якорь)
            core/  resonance/  sensory/  archive/
    Память пустая (наполнение — ступень 5). Возвращает путь папки.
    """
    name = _safe_name(obj.get("Official_Name", ""))
    if name == "без_имени":
        return ""
    naznach = _safe_name(obj.get("Profession", "") or "без_предназначения")

    dom = ZHITELI_DIR / naznach / name        # папка жителя
    dom.mkdir(parents=True, exist_ok=True)

    # 4 слоя — наш закон
    for sloy in ("core", "resonance", "sensory", "archive"):
        (dom / sloy).mkdir(parents=True, exist_ok=True)

    # passport.json (ядро) — рядом и копией в core/ (паспорт = якорь = core)
    pasport_json = json.dumps(obj, ensure_ascii=False, indent=2)
    (dom / "passport.json").write_text(pasport_json, encoding="utf-8")
    (dom / "core" / "anchor.json").write_text(pasport_json, encoding="utf-8")

    # пустые заготовки слоёв (память придёт на ступени 5)
    (dom / "resonance" / "emotional_weights.json").write_text("{}", encoding="utf-8")
    (dom / "resonance" / "event_log.jsonl").write_text("", encoding="utf-8")
    (dom / "sensory" / "sensory_memory.json").write_text(
        json.dumps({"entries": [], "_note": "оперативка · пусто при рождении"},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (dom / "archive" / "archive.jsonl").write_text("", encoding="utf-8")

    # маркер: слои заведены
    mark = dom / "_слои_заведены.txt"
    mark.write_text("core · resonance · sensory · archive\\nпамять пустая (ступень 5)",
                    encoding="utf-8")

    return str(dom)
'''
    src = src.replace(anchor, new_func, 1)

    # ── ВСТАВКА 2: вызвать zavesti_sloi после кусочка в save_object ──
    # Якорь — строка вызова кусочка (от прошлого патча).
    kus_call = None
    for ln in src.splitlines():
        if ln.strip() == '_kus = rodit_pasport_kusochek(obj)':
            kus_call = ln
            break
    if kus_call is None:
        fail("вызов rodit_pasport_kusochek в save_object не найден — примени patch_dva_fila сначала")

    indent = kus_call[:len(kus_call) - len(kus_call.lstrip())]
    add_lines = [
        '_kus = rodit_pasport_kusochek(obj)',
        '# PATCH_4_SLOYA: заводим 4 слоя на этаже жителя',
        'try:',
        '    _dom = zavesti_sloi(obj)',
        '    if _dom:',
        '        ui.notify(f"4 слоя заведены: {_dom}", type="positive", timeout=4000)',
        'except Exception as _e2:',
        '    ui.notify(f"⚠ слои не завелись: {_e2}", type="warning")',
    ]
    new_call = "\n".join(indent + l for l in add_lines)
    src = src.replace(kus_call, new_call, 1)

    # метка
    src = src.replace('import json\n', f'import json\n{MARK}\n', 1)
    if MARK not in src:
        src = MARK + "\n" + src

    TARGET.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ 4 слоя включены.")
    print("       • zavesti_sloi() — core/resonance/sensory/archive")
    print("       • папка жителя: жители/{предназначение}/{имя}/")
    print("       • passport.json + копия в core/anchor.json")
    print("       • слои пустые (память — ступень 5)")
    print()
    print("[ПАТЧ] Проверка: роди Васю (Profession='трейдер') →")
    print("       жители/трейдер/Вася/ с папками core/resonance/sensory/archive")


if __name__ == "__main__":
    main()
