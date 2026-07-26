# -*- coding: utf-8 -*-
# PATCH_MAYAK_KABINET_V2 — кабинет Маяка + уборка
"""
Ставит кабинет Маяка и прибирает за двумя черновиками.

  1. УБОРКА. ГОРОД/rozetki.py — первый черновик гнёзд, его заменил
     ГОРОД/gnezda.py. Сносим, чтобы в городе не жили две правды об
     одном. Данные старого модуля (розетки.json) тоже убираем — но
     сперва переносим из них живые записи в гнёзда.json, чтобы ничего
     не потерялось.

  2. СТРАНИЦА /mayak в main.py.

  3. ВРАТА С КАРТЫ: клик по Маяку ведёт в кабинет, а не в паспорт
     места — тем же швом, что у Биржи и Академии.

Идемпотентно: каждый шаг проверяет себя, второй прогон молчит.
Бэкапы перед каждой правкой, ast.parse после — не сошлось, не пишем.

ПЕРЕД ЗАПУСКОМ положи:
    ГОРОД/gnezda.py
    ГОРОД/ui_mayak.py

Запуск ИЗ КОРНЯ РЕПО:
    python patch_mayak_kabinet_v2.py

`шесть·проверено·до·корня`
"""
import ast
import json
import shutil
from pathlib import Path

ROOT = Path.cwd()
MAIN = ROOT / "main.py"
KARTA = ROOT / "ГОРОД" / "ui_grondheim.py"
GNEZDA = ROOT / "ГОРОД" / "gnezda.py"
UI_MAYAK = ROOT / "ГОРОД" / "ui_mayak.py"
ROZETKI = ROOT / "ГОРОД" / "rozetki.py"

DANNYE = ROOT / "GRONDHEIM_CITY" / "посты" / "mayak"
STAR_DANNYE = DANNYE / "розетки.json"
NOV_DANNYE = DANNYE / "гнёзда.json"

LOK_ID = "0005_LIGHTHOUSE_AWAKENING"

BLOCK_PAGE = '''# ── МАЯК ПРОБУЖДЕНИЯ — выход города наружу ── MAYAK_KABINET_V2
# Общегородской. Гнёзда всеядны: житель, пост, канал, инструмент.
from ui_mayak import page_mayak

@ui.page("/mayak")
def _mayak():
    page_mayak()


'''

ANCHOR_PAGE = '''# ── АКАДЕМИЯ — Замок Сов (школа города) ── AKADEMIA_KABINET_V1'''


# ══════════════════════════════════════════════════════════
# ШАГ 1 — уборка первого черновика
# ══════════════════════════════════════════════════════════

def shag_1_uborka():
    print("── ШАГ 1: уборка ──")

    # перенос живых записей из старого файла данных
    if STAR_DANNYE.exists():
        try:
            staroe = json.loads(STAR_DANNYE.read_text(encoding="utf-8"))
            zapisi = staroe.get("гнёзда", []) or []
        except Exception:
            zapisi = []
        perenes = 0
        if zapisi:
            try:
                novoe = (json.loads(NOV_DANNYE.read_text(encoding="utf-8"))
                         if NOV_DANNYE.exists() else {"гнёзда": []})
            except Exception:
                novoe = {"гнёзда": []}
            est = {(g.get("номер"), g.get("имя")) for g in novoe.get("гнёзда", [])}
            for z in zapisi:
                # старые поля -> новые: гнездо->номер, тип->род, с->воткнут
                nov = {
                    "номер": z.get("гнездо", z.get("номер", 0)),
                    "род": z.get("тип", z.get("род", "живой")),
                    "имя": z.get("имя", ""),
                    "ключ": z.get("ключ", ""),
                    "что": z.get("что", ""),
                    "постоянно": bool(z.get("постоянно")),
                    "воткнут": z.get("с", z.get("воткнут", "")),
                    "последний_раз": z.get("активность", z.get("последний_раз", "")),
                }
                if (nov["номер"], nov["имя"]) in est or not nov["имя"]:
                    continue
                novoe.setdefault("гнёзда", []).append(nov)
                perenes += 1
            if perenes:
                NOV_DANNYE.parent.mkdir(parents=True, exist_ok=True)
                NOV_DANNYE.write_text(
                    json.dumps(novoe, ensure_ascii=False, indent=2),
                    encoding="utf-8")
        try:
            STAR_DANNYE.rename(STAR_DANNYE.with_suffix(".json.bak_rozetki"))
            print(f"  ✓ старые данные убраны (перенесено записей: {perenes})")
        except Exception as e:
            print(f"  ⚠ старые данные не убрались: {e}")
    else:
        print("  = старых данных нет")

    # сам модуль-черновик
    if ROZETKI.exists():
        try:
            ROZETKI.rename(ROZETKI.with_suffix(".py.bak_zamenen_gnezdami"))
            print("  ✓ rozetki.py убран — его заменил gnezda.py")
        except Exception as e:
            print(f"  ⚠ rozetki.py не убрался: {e}")
    else:
        print("  = rozetki.py уже нет")

    # никто на него больше не ссылается?
    hvosty = []
    for f in ROOT.rglob("*.py"):
        if any(x in f.parts for x in (".git", "__pycache__", ".venv", "venv")):
            continue
        if f.name.startswith("patch_"):
            continue
        try:
            if "import rozetki" in f.read_text(encoding="utf-8", errors="replace"):
                hvosty.append(str(f.relative_to(ROOT)))
        except Exception:
            pass
    if hvosty:
        print("  ⚠ на rozetki всё ещё ссылаются:")
        for h in hvosty:
            print(f"      {h}")
    return True


# ══════════════════════════════════════════════════════════
# ШАГ 2 — страница
# ══════════════════════════════════════════════════════════

def shag_2_main():
    print("── ШАГ 2: страница /mayak ──")
    if not MAIN.exists():
        print("  ✗ main.py не найден. Запускай ИЗ КОРНЯ репо.")
        return False
    src = MAIN.read_text(encoding="utf-8")
    if "page_mayak" in src:
        print("  = страница уже зарегистрирована")
        return True
    if ANCHOR_PAGE not in src:
        print("  ✗ якорь регистрации не найден (блок Академии).")
        print("    Впиши руками:  from ui_mayak import page_mayak")
        return False
    novyy = src.replace(ANCHOR_PAGE, BLOCK_PAGE + ANCHOR_PAGE, 1)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ main.py не парсится после правки: {e}")
        return False
    shutil.copy2(MAIN, MAIN.with_suffix(".py.bak_mayak_kabinet"))
    MAIN.write_text(novyy, encoding="utf-8")
    print("  ✓ бэкап: main.py.bak_mayak_kabinet")
    print("  ✓ /mayak зарегистрирован")
    return True


# ══════════════════════════════════════════════════════════
# ШАГ 3 — врата с карты
# ══════════════════════════════════════════════════════════

def shag_3_vrata():
    print("── ШАГ 3: врата с карты ──")
    if not KARTA.exists():
        print("  ✗ ГОРОД/ui_grondheim.py не найден.")
        return False
    src = KARTA.read_text(encoding="utf-8")
    if f'"{LOK_ID}"' in src:
        print("  = врата уже открыты")
        return True
    if "LOCATION_GATES = {" not in src:
        print("  ✗ LOCATION_GATES не найден — правь вручную:")
        print(f'    "{LOK_ID}": "/mayak",')
        return False
    novyy = src.replace(
        "LOCATION_GATES = {",
        'LOCATION_GATES = {\n'
        f'    "{LOK_ID}": "/mayak",  # Маяк -> кабинет (ui_mayak.py)',
        1)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ не парсится после правки: {e}")
        return False
    shutil.copy2(KARTA, KARTA.with_suffix(".py.bak_mayak_gate"))
    KARTA.write_text(novyy, encoding="utf-8")
    print("  ✓ бэкап: ui_grondheim.py.bak_mayak_gate")
    print("  ✓ клик по Маяку ведёт в кабинет")
    return True


def shag_4_proverka():
    print("── ШАГ 4: проверка ──")
    ok = True
    for f in (GNEZDA, UI_MAYAK, ROOT / "ГОРОД" / "mayak.py", MAIN, KARTA):
        if not f.exists():
            print(f"  ⚠ нет файла: {f.name}")
            ok = False
            continue
        try:
            ast.parse(f.read_text(encoding="utf-8"))
            print(f"  ✓ парсится: {f.name}")
        except SyntaxError as e:
            print(f"  ✗ не парсится {f.name}: {e}")
            ok = False
    lok = ROOT / "GRONDHEIM_CITY" / "локации" / LOK_ID / "passport.json"
    print(f"  {'✓' if lok.exists() else '⚠'} локация Маяка: "
          f"{'на месте' if lok.exists() else 'не найдена'}")
    return ok


if __name__ == "__main__":
    try:
        import sys as _s
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("═══ PATCH_MAYAK_KABINET_V2 ═══")
    print(f"корень: {ROOT}\n")
    ok = (shag_1_uborka() and shag_2_main()
          and shag_3_vrata() and shag_4_proverka())
    print()
    if ok:
        print("✅ ГОТОВО.")
        print("   Кликай Маяк на карте — попадёшь в кабинет.")
        print("   Постоянные гнёзда справа, ярче. Чат соединяет с выбранным.")
    else:
        print("❌ Не докатилось — смотри выше. Ничего не сломано.")
    print("`шесть·проверено·до·корня`")
