# patch_pylance_gigiena.py
# ─────────────────────────────────────────────────────────────
# PYLANCE_GIGIENA_V1 — ТИПЫ НЕ ВРУТ. И СИРОТА УЕЗЖАЕТ.
#
# Три жалобы Pylance от Шефа (14.07). Разобраны по одной — все три
# ПРАВДА, но НИ ОДНА не роняет рантайм. Гигиена, не пожар.
#
# ── ЖАЛОБА 1: nositel.UCHIT «не является известным атрибутом» ──
# ⚠ ЭТО НЕ ОШИБКА PYLANCE. ЭТО НАСТОЯЩАЯ МИНА.
#
#   Биржа/nositel.py  — 655 строк, ЖИВОЙ, UCHIT есть (:226)
#   nositel.py в КОРНЕ — 319 строк, СИРОТА, UCHIT НЕТ
#
#   Два файла с одним именем. Pylance при `import nositel` видит
#   КОРНЕВОЙ (он ближе к корню проекта) и не находит UCHIT.
#   Python в рантайме подхватывает ПРАВИЛЬНЫЙ (тестер лежит рядом).
#
#   СЕГОДНЯ ПОВЕЗЛО. Завтра порядок sys.path изменится — и всё
#   сломается МОЛЧА. Это ШЕСТОЙ кран того же класса за трое суток:
#   магик (5 копий) · слепок (2 писателя) · bdb_dir (2 читателя) ·
#   ведение (не позвано) · рука (обещана, не написана) ·
#   СИРОТА-nositel (2 файла, один мёртвый).
#
#   ЛЕЧЕНИЕ: сироту в _OLD/. Не удаляем — переселяем.
#   Патч СНАЧАЛА проверяет, что его никто не импортирует.
#
# ── ЖАЛОБА 2: williams_core:517 — direction может быть None ──
#   `_angulation_angle(direction: str)`, а direction — Optional.
#   Мой недосмотр в REZINKA_DZHASTIN_V1.
#   ⚠ Это код МЁРТВОГО угла — bdb_strong его больше не спрашивает
#     (затвор теперь резинка). Висит «чтобы видно было, что он врал».
#   Чиним тип, но не воскрешаем.
#
# ── ЖАЛОБА 3: dvizhok:384 — `pattern: str = None` ──
#   Мой недосмотр в TRI_ETAZHA_V1. Должно быть Optional[str].
#   В рантайме работает (порог 3 сработал, метки родились) — но тип
#   СОВРАЛ, и это ровно то, за что я сам же ругаю чужой код.
#
# ИДЕМПОТЕНТЕН. BACKUP: *.bak_pylance
# Запуск из корня репо:  python patch_pylance_gigiena.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "Биржа" / "williams_core.py"
DV   = ROOT / "жители" / "dvizhok.py"
SIROTA = ROOT / "nositel.py"
OLD  = ROOT / "_OLD"
MARK = "PYLANCE_GIGIENA_V1"

SKIP = {".git", "__pycache__", ".venv", "venv", "node_modules", "_OLD"}


# ═══════════════════════════════════════════════════════════
# 1 — СИРОТА nositel.py
# ═══════════════════════════════════════════════════════════

def _sirota():
    if not SIROTA.exists():
        print("  ✓ сироты в корне нет — уже чисто")
        return

    zhivoy = ROOT / "Биржа" / "nositel.py"
    if not zhivoy.exists():
        print("  ⚠ Биржа/nositel.py НЕ НАЙДЕН — корневой может быть живым!")
        print("    НЕ ТРОГАЮ. Разберись глазами.")
        return

    s_root = SIROTA.read_text(encoding="utf-8", errors="ignore")
    s_live = zhivoy.read_text(encoding="utf-8", errors="ignore")

    print(f"     корневой: {len(s_root.splitlines())} строк, "
          f"UCHIT={'ЕСТЬ' if 'UCHIT' in s_root else 'НЕТ'}")
    print(f"     Биржа/:   {len(s_live.splitlines())} строк, "
          f"UCHIT={'ЕСТЬ' if 'UCHIT' in s_live else 'НЕТ'}")

    # ── ПРОВЕРКА: не зовёт ли кто-то ИМЕННО корневой? ──
    # Тот, кто лежит В КОРНЕ и делает `import nositel`, получит СИРОТУ.
    opasnye = []
    for p in ROOT.rglob("*.py"):
        if any(x in SKIP for x in p.parts):
            continue
        if p.name.startswith("patch_") or p.resolve() == SIROTA.resolve():
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(r"^\s*(import nositel|from nositel import)", txt, re.M):
            # кто лежит в корне — тот возьмёт сироту
            if p.parent.resolve() == ROOT.resolve():
                opasnye.append(p)

    if opasnye:
        print("  ⚠ КОРНЕВОЙ nositel КТО-ТО ИМПОРТИРУЕТ ИЗ КОРНЯ:")
        for p in opasnye:
            print(f"       {p.relative_to(ROOT)}")
        print("    НЕ ТРОГАЮ — можно оторвать живое. Скажи мне.")
        return

    OLD.mkdir(exist_ok=True)
    cel = OLD / "nositel_KORNEVOY_sirota.py"
    if cel.exists():
        print(f"  ✓ сирота уже в _OLD — просто убираю дубль из корня")
        SIROTA.unlink()
        return

    shutil.move(str(SIROTA), str(cel))
    print(f"  ✓ сирота переехал: _OLD/{cel.name}")
    print("    Pylance перестанет путаться. Мина обезврежена.")


# ═══════════════════════════════════════════════════════════
# 2 — ТИПЫ
# ═══════════════════════════════════════════════════════════

def _tipy_core() -> bool:
    if not CORE.exists():
        print("  ⚠ williams_core не найден")
        return False
    src = CORE.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ williams_core уже пропатчен")
        return True

    bak = CORE.with_suffix(".py.bak_pylance")
    if not bak.exists():
        shutil.copy2(CORE, bak)

    # _angulation_angle: direction может быть None
    staroe = ("def _angulation_angle(bars: list, teeth_series: list, cross_idx: int,\n"
              "                      i: int, direction: str,\n"
              "                      point: Optional[float]) -> Optional[float]:")
    novoe = ("def _angulation_angle(bars: list, teeth_series: list, cross_idx: int,\n"
             "                      i: int, direction: Optional[str],\n"
             "                      point: Optional[float]) -> Optional[float]:\n"
             "    # PYLANCE_GIGIENA_V1: direction реально бывает None (нет\n"
             "    # направления — не от чего мерить). Тип врал.\n"
             "    #\n"
             "    # ⚠ ЭТО КОД МЁРТВОГО ОРГАНА. Угол выброшен из затвора\n"
             "    # (REZINKA_DZHASTIN_V1) — bdb_strong его больше не\n"
             "    # спрашивает. Книга Моржа §3: «ГЛАВНОЕ — НЕ СЧИТАТЬ УГОЛ.»\n"
             "    # Оставлен в раскладке как факт: пусть видно, что он врал\n"
             "    # (медиана 0.9° при максимуме 179.9°).")
    if staroe in src:
        src = src.replace(staroe, novoe, 1)
        print("  ✓ _angulation_angle: direction → Optional[str]")
    else:
        print("  ⚠ сигнатура _angulation_angle не найдена — пропускаю")

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: типы не врут (Optional там, где None).\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ.")
        return False

    CORE.write_text(src, encoding="utf-8")
    return True


def _tipy_dvizhok() -> bool:
    if not DV.exists():
        print("  ⚠ dvizhok не найден")
        return False
    src = DV.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ dvizhok уже пропатчен")
        return True

    bak = DV.with_suffix(".py.bak_pylance")
    if not bak.exists():
        shutil.copy2(DV, bak)

    # Optional должен быть импортирован
    if "from typing import" not in src:
        # ставим после первого блока import
        m = re.search(r"^import .+$", src, re.M)
        if m:
            src = src.replace(m.group(0),
                              m.group(0) + "\nfrom typing import Optional"
                              "   # PYLANCE_GIGIENA_V1", 1)
            print("  ✓ добавлен импорт Optional")
    elif "Optional" not in src.split("\n\n")[0]:
        m = re.search(r"^from typing import (.+)$", src, re.M)
        if m and "Optional" not in m.group(1):
            src = src.replace(m.group(0),
                              f"from typing import {m.group(1)}, Optional", 1)
            print("  ✓ Optional добавлен в typing")

    # pattern: str = None  →  Optional[str]
    staroe = "                      pattern: str = None, otkuda: str = \"рынок\") -> dict:"
    novoe = ("                      pattern: Optional[str] = None,   # PYLANCE_GIGIENA_V1\n"
             "                      otkuda: str = \"рынок\") -> dict:")
    n = 0
    if staroe in src:
        src = src.replace(staroe, novoe, 1)
        n += 1

    # на всякий — любые другие `: str = None`
    for m in list(re.finditer(r"(\w+): str = None", src)):
        src = src.replace(m.group(0), f"{m.group(1)}: Optional[str] = None", 1)
        n += 1

    print(f"  ✓ типы Optional поправлены: {n} мест(а)")

    src = src.replace("# `шесть·проверено·до·корня`",
                      f"# {MARK}: pattern: Optional[str] — тип больше не врёт.\n"
                      "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ.")
        return False

    DV.write_text(src, encoding="utf-8")
    return True


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГИГИЕНА PYLANCE — типы не врут, сирота уезжает" + " " * 20 + "║")
    print("║  PYLANCE_GIGIENA_V1 · идемпотентен" + " " * 33 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  Три жалобы. Все три ПРАВДА. Ни одна не роняет рантайм.")
    print()

    print("── 1. СИРОТА nositel.py (⚠ НАСТОЯЩАЯ МИНА) ──")
    _sirota()

    print()
    print("── 2. williams_core: direction: Optional[str] ──")
    _tipy_core()

    print()
    print("── 3. dvizhok: pattern: Optional[str] ──")
    _tipy_dvizhok()

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО" + " " * 60 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ГЛАВНОЕ — НЕ ТИПЫ, А СИРОТА:")
    print("    Два nositel.py с одним именем. Python СЕГОДНЯ выбрал")
    print("    правильный. Завтра порядок sys.path изменится —")
    print("    и всё сломается МОЛЧА, без единой ошибки.")
    print()
    print("    Это ШЕСТОЙ кран того же класса за трое суток:")
    print("      магик (5 копий) · слепок (2 писателя) · bdb_dir (2 читателя)")
    print("      · ведение (не позвано) · рука (обещана, не написана)")
    print("      · СИРОТА (2 файла, один мёртвый)")
    print()
    print("    Урок один: ЛЕЧИШЬ СУЩНОСТЬ — НАЙДИ ВСЕХ, КТО ЕЁ ЧИТАЕТ.")
    print()
    print("  Перезапусти VS Code — Pylance перечитает пути.")
    print()


if __name__ == "__main__":
    main()
