# -*- coding: utf-8 -*-
# PATCH_GOROD_MAYAK_V1 — Маяк в городе + библиотекарь получает выход
"""
Делает:

  1. ЗАВОДИТ ПОСТ МАЯКА в реестре города:
       GRONDHEIM_CITY/посты/mayak/пост.json
     Маяк — общегородской, не академический. Хранителя ему не надо:
     он светит сам, это сооружение, а не должность.

  2. ДАЁТ БИБЛИОТЕКАРЮ ВЫХОД НАРУЖУ.
     Академия/bibliotekar.py получает функцию iskat_shire() — когда
     на полках пусто или спрашивают про внешний мир, библиотекарь
     идёт на Маяк и приносит оттуда. Полки при этом всегда первее:
     сперва своё, потом чужое.

  3. ПРОВЕРЯЕТ .env — есть ли TAVILY_KEY. Нет — честно скажет, что
     маяк тёмный, и подскажет строку.

Идемпотентно: маркер PATCH_GOROD_MAYAK_V1 — второй прогон молчит.
Бэкап перед правкой, ast.parse после.

ПЕРЕД ЗАПУСКОМ положи ГОРОД/mayak.py

Запуск ИЗ КОРНЯ РЕПО:
    python patch_gorod_mayak_v1.py

`шесть·проверено·до·корня`
"""
import ast
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.cwd()
BIB = ROOT / "Академия" / "bibliotekar.py"
POSTY = ROOT / "GRONDHEIM_CITY" / "посты"
ENV = ROOT / ".env"

MARKER = "# PATCH_GOROD_MAYAK_V1"


# ── ШАГ 1: пост маяка ──────────────────────────────────────

def shag_1_post():
    print("── ШАГ 1: пост Маяка ──")
    d = POSTY / "mayak"
    mf = d / "пост.json"
    if mf.exists():
        print("  = пост уже заведён")
        return True
    d.mkdir(parents=True, exist_ok=True)
    mf.write_text(json.dumps({
        "id": "mayak",
        "название": "Маяк Пробуждения",
        "где": "",          # прирастёт к локации сам, когда Шеф её заведёт
        "движок": "mayak",
        "общегородской": True,
        "_note": ("Точка связи города с внешним миром. Провайдер Tavily. "
                  "Хранитель не нужен — это сооружение, не должность."),
        "заведён": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  ✓ пост заведён: GRONDHEIM_CITY/посты/mayak/")
    return True


# ── ШАГ 2: библиотекарь получает выход наружу ───────────────

ANCHOR_BIB = '''def est_bibliotekar() -> bool:'''

BLOCK_BIB = '''# PATCH_GOROD_MAYAK_V1 — библиотекарь умеет выйти за стены
# Полки ВСЕГДА первее: сперва смотрим своё, наружу идём только когда
# на полке пусто или спрашивают про внешний мир. Маяк общегородской —
# библиотека им пользуется, но не владеет.

async def iskat_shire(zapros: str, skolko: int = 4) -> str:
    """Сходить на Маяк за тем, чего нет на полках.

    Возвращает готовый кусок для промпта. Маяк тёмный (нет ключа) —
    вернёт это словами, и библиотекарь честно скажет, что за стены
    выйти не может, вместо выдуманных ссылок.
    """
    try:
        import mayak
    except ImportError:
        return "(Маяка в городе нет — модуль ГОРОД/mayak.py не найден)"
    try:
        rez = await mayak.poisk(zapros, skolko)
        try:
            mayak.zapisat_vizit("библиотекарь", zapros, rez.get("ok", False))
        except Exception:
            pass
        return mayak.dlya_promta(rez, skolko)
    except Exception as e:
        return f"(Маяк не отозвался: {e})"


def mayak_gorit() -> bool:
    """Горит ли Маяк — можно ли вообще выходить наружу."""
    try:
        import mayak
        return mayak.gorit()
    except Exception:
        return False


def est_bibliotekar() -> bool:'''

# ── правим sprosit(): полки пусты -> идём на Маяк ────────────

ANCHOR_SPROSIT = '''    promt, imya = sobrat_promt(vopros, dlya_kogo)
    if not promt:
        return ("⚠ Библиотекаря в городе пока нет — пост свободен. "
                "Посади кого-нибудь через Брата: Роль → библиотекарь.")
    if not OPENROUTER_KEY:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."'''

BLOCK_SPROSIT = '''    promt, imya = sobrat_promt(vopros, dlya_kogo)
    if not promt:
        return ("⚠ Библиотекаря в городе пока нет — пост свободен. "
                "Посади кого-нибудь через Брата: Роль → библиотекарь.")
    if not OPENROUTER_KEY:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."

    # PATCH_GOROD_MAYAK_V1: на полках пусто — выходим на Маяк.
    # Порядок жёсткий: СВОЁ первее. Наружу только когда дома нечего дать.
    if not nayti_knigi(vopros) and mayak_gorit():
        _snaruzhi = await iskat_shire(vopros)
        promt += ("\\n\\n=== ТЫ СХОДИЛ(А) НА МАЯК ПРОБУЖДЕНИЯ ===\\n"
                  "На полках по этому запросу пусто, и ты вышел(шла) за стены. "
                  "Вот что принёс луч из внешнего мира:\\n"
                  f"{_snaruzhi}\\n"
                  "Скажи прямо, что на полках этого нет и что это принесено "
                  "снаружи. Не выдавай найденное за книгу библиотеки.\\n")'''


def shag_2_bibliotekar():
    print("── ШАГ 2: выход наружу библиотекарю ──")
    if not BIB.exists():
        print(f"  ✗ {BIB} не найден — сначала положи Академия/bibliotekar.py")
        return False
    src = BIB.read_text(encoding="utf-8")
    if MARKER in src:
        print("  = патч уже накатан")
        return True

    novyy = src
    for imya, ank, blok in (
        ("iskat_shire() + mayak_gorit()", ANCHOR_BIB, BLOCK_BIB),
        ("полки пусты -> Маяк", ANCHOR_SPROSIT, BLOCK_SPROSIT),
    ):
        if ank not in novyy:
            print(f"  ✗ якорь не найден: {imya}")
            return False
        novyy = novyy.replace(ank, blok, 1)
        print(f"  ✓ {imya}")

    # ГОРОД уже в sys.path у bibliotekar.py — проверим на всякий
    if '"ГОРОД"' not in novyy:
        print("  ⚠ ГОРОД не в sys.path bibliotekar.py — маяк может не найтись")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ после правки не парсится: {e}")
        print("  ФАЙЛ НЕ ЗАПИСАН.")
        return False

    bak = BIB.with_suffix(".py.bak_mayak")
    shutil.copy2(BIB, bak)
    BIB.write_text(novyy, encoding="utf-8")
    print(f"  ✓ бэкап: {bak.name}")
    return True


# ── ШАГ 3: ключ провайдера ──────────────────────────────────

def shag_3_klyuch():
    print("── ШАГ 3: ключ провайдера ──")
    if not ENV.exists():
        print("  ⚠ .env не найден. Заведи его в корне и впиши:")
        print("      TAVILY_KEY=твой_ключ")
        return True
    txt = ENV.read_text(encoding="utf-8", errors="replace")
    if "TAVILY_KEY" in txt:
        znach = ""
        for line in txt.splitlines():
            if line.strip().startswith("TAVILY_KEY"):
                znach = line.split("=", 1)[1].strip() if "=" in line else ""
        if znach:
            print("  ✓ TAVILY_KEY на месте — Маяк будет гореть")
        else:
            print("  ⚠ TAVILY_KEY есть, но пустой — Маяк тёмный")
            print("     Ключ берётся здесь: https://app.tavily.com")
    else:
        print("  ⚠ TAVILY_KEY в .env нет. Допиши строкой:")
        print("      TAVILY_KEY=твой_ключ")
        print("     Ключ берётся здесь: https://app.tavily.com")
    return True


def shag_4_proverka():
    print("── ШАГ 4: проверка ──")
    ok = True
    for f in (ROOT / "ГОРОД" / "mayak.py", BIB):
        if not f.exists():
            print(f"  ⚠ нет файла: {f}")
            ok = False
            continue
        try:
            ast.parse(f.read_text(encoding="utf-8"))
            print(f"  ✓ парсится: {f.name}")
        except SyntaxError as e:
            print(f"  ✗ не парсится {f.name}: {e}")
            ok = False
    return ok


if __name__ == "__main__":
    try:
        import sys as _s
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("═══ PATCH_GOROD_MAYAK_V1 ═══")
    print(f"корень: {ROOT}\n")
    ok = (shag_1_post() and shag_2_bibliotekar()
          and shag_3_klyuch() and shag_4_proverka())
    print()
    if ok:
        print("✅ ГОТОВО.")
        print("   Маяк общегородской — зовут его все одинаково.")
        print("   Библиотекарь выходит наружу, когда на полках пусто.")
        print("   Заведёшь локацию с «маяк» в имени — прирастёт сам.")
    else:
        print("❌ Не докатилось — смотри выше. Ничего не сломано.")
    print("`шесть·проверено·до·корня`")
