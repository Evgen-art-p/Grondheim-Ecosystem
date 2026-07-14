# razvedka_slepka.py — КТО ПИШЕТ ПОЗИЦИЮ БЕЗ СЛЕПКА?
# ─────────────────────────────────────────────────────────────
# БОЛЕЗНЬ (лог Шефа, 13.07):
#   [МАЯК] стол_входа: {}
#   [МАЯК] ⛔ ВЫХОД: слепка нет или pnl_r=None
#
# Судья сенсоров молча выходит на КАЖДОЙ сделке → черновиков нет →
# метка не родится НИКОГДА. Труба построена, вода идёт, кран на
# выходе перекрыт.
#
# ЧТО УЖЕ ЗНАЮ (проверено по репе):
#   · hooks.py:668 ПИШЕТ "стол_входа" в позицию (SLEPOK_IZ_CHAIN_V1)
#   · hooks.py:644 — ЕДИНСТВЕННЫЙ append в positions во всём hooks
#   · council.py НЕ ЗОВЁТ on_after_agent → _persist_trading_state
#     в тестерном пути, похоже, НЕ ВЫЗЫВАЕТСЯ ВООБЩЕ
#   · а в логе позиция носит ключи iskra_zero_point и symbol,
#     которых на 644 НЕ ПИШУТ
#   ⇒ ЕСТЬ ВТОРОЙ ПИСАТЕЛЬ ПОЗИЦИЙ. Найти его.
#
# Скрипт НИЧЕГО НЕ МЕНЯЕТ. Читает диск и говорит правду.
#
# Запуск из корня репо:  python razvedka_slepka.py
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP = {".git", "__pycache__", ".venv", "venv", "node_modules", "_ARCHIVE", "_OLD"}

# следы, по которым узнаём писателя позиции
SLEDY = {
    "iskra_zero_point": "поле из ЛОГА, которого нет в hooks.py:644",
    "стол_входа":       "СЛЕПОК (кто пишет / кто читает)",
    "_persist_trading_state": "функция со слепком",
    "on_after_agent":   "хук, который её зовёт",
    "save_trading_state": "кто вообще пишет состояние",
}


def _fajly():
    for p in ROOT.rglob("*.py"):
        if any(x in SKIP for x in p.parts):
            continue
        if p.name.endswith((".bak", ".bak2")) or ".bak_" in p.name:
            continue
        yield p


print()
print("  РАЗВЕДКА СЛЕПКА — кто пишет позицию без стола?")
print("  " + "─" * 62)

# ── 1. Кто оставляет следы ──────────────────────────────────
for sled, zachem in SLEDY.items():
    print()
    print(f"  ── «{sled}» ──  ({zachem})")
    nashli = False
    for p in _fajly():
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for n, line in enumerate(txt.splitlines(), 1):
            if sled in line:
                rel = p.relative_to(ROOT)
                print(f"     {rel}:{n}")
                print(f"        {line.strip()[:76]}")
                nashli = True
    if not nashli:
        print("     ✗ НЕ НАЙДЕНО НИГДЕ")

# ── 2. ВСЕ, кто добавляет позицию ───────────────────────────
print()
print("  " + "─" * 62)
print("  ── ВСЕ, КТО ДОБАВЛЯЕТ ПОЗИЦИЮ (append/positions=) ──")
pat = re.compile(r'positions.*\.append|\[["\']positions["\']\]\s*=|'
                 r'positions\s*=\s*\[|"status":\s*"OPEN"')
for p in _fajly():
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for n, line in enumerate(txt.splitlines(), 1):
        if pat.search(line):
            print(f"     {p.relative_to(ROOT)}:{n}")
            print(f"        {line.strip()[:76]}")

# ── 3. ЖИВОЕ СОСТОЯНИЕ — что реально в позиции ──────────────
print()
print("  " + "─" * 62)
print("  ── ЖИВОЙ trading_state.json ──")
sp = ROOT / "GRONDHEIM_CITY" / "Биржа" / "данные" / "trading_state.json"
if not sp.exists():
    print(f"     ✗ нет файла {sp}")
else:
    try:
        st = json.loads(sp.read_text(encoding="utf-8"))
        ps = st.get("positions", []) or []
        print(f"     позиций сейчас: {len(ps)}")
        for i, pos in enumerate(ps, 1):
            print(f"     [{i}] ключи: {list(pos.keys())}")
            est = "стол_входа" in pos
            print(f"         стол_входа: "
                  f"{'ЕСТЬ ✓' if est else '✗ НЕТ — ВОТ ОНА, БОЛЕЗНЬ'}")
            if est:
                print(f"         {pos['стол_входа']}")
    except Exception as ex:
        print(f"     ⚠ не читается: {ex}")

# ── 4. ГДЕ ЖИВЁТ ИСПОЛНИТЕЛЬ (A09) ──────────────────────────
print()
print("  " + "─" * 62)
print("  ── МОЗГ ИСПОЛНИТЕЛЯ (A09) — он строит ордера ──")
naydeno = []
for p in ROOT.rglob("мозг.py"):
    if any(x in SKIP for x in p.parts):
        continue
    if "A09" in str(p) or "A05" in str(p):
        naydeno.append(p)
if not naydeno:
    print("     ✗ мозг A09 не найден — где Исполнитель?")
    for p in ROOT.rglob("мозг.py"):
        if any(x in SKIP for x in p.parts):
            continue
        print(f"     (есть: {p.relative_to(ROOT)})")
else:
    for p in naydeno:
        txt = p.read_text(encoding="utf-8")
        pishet = "positions" in txt or "save_trading_state" in txt
        print(f"     {p.relative_to(ROOT)}")
        print(f"        пишет позиции: {'ДА ← ВОТ ОН' if pishet else 'нет'}")
        for n, line in enumerate(txt.splitlines(), 1):
            if ("positions" in line or "iskra_zero_point" in line
                    or "save_trading_state" in line):
                print(f"        :{n}  {line.strip()[:70]}")

print()
print("  " + "─" * 62)
print("  Скинь этот вывод Брату. Гадать не буду — диск не спорит.")
print()
