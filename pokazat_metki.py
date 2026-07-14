# pokazat_metki.py — ПЕРВЫЕ ВЫВОДЫ В ИСТОРИИ ГРОНДХЕЙМА.
# ─────────────────────────────────────────────────────────────
# 14.07 нога Опыта ПРОТЕКЛА впервые: судья рассудил, черновики легли,
# порог 3 сработал, метки родились. Это первые выводы, которые житель
# города заработал СВОИМИ деньгами — не вписанные при рождении.
#
# Ничего не пишет. Только показывает три этажа каждого.
#
# Запуск из корня репо:  python pokazat_metki.py
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CITY = ROOT / "GRONDHEIM_CITY"
SKIP = {".git", "__pycache__", "_ARCHIVE", "_OLD", ".venv"}


def doma():
    out = []
    for pp in CITY.rglob("passport.json"):
        if any(x in SKIP for x in pp.parts):
            continue
        try:
            p = json.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(p, dict) and p.get("DNA_Static"):
            out.append((pp.parent, p))
    return sorted(out, key=lambda x: x[1].get("Official_Name", ""))


def chitat(path):
    try:
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            return d if isinstance(d, list) else []
    except Exception:
        pass
    return []


print()
print("  ПЕРВЫЕ ВЫВОДЫ В ИСТОРИИ ГРОНДХЕЙМА")
print("  " + "─" * 66)

vsego_m = vsego_y = 0

for dom, p in doma():
    imya = p.get("Official_Name") or dom.name
    metki  = chitat(dom / "2_метки" / "metki.json")
    mayaki = chitat(dom / "3_маяки" / "mayaki.json")
    rod = [l for l in (p.get("Anchor_Points", "") or "")
           .replace("\\n", "\n").split("\n") if l.strip()]
    charge = p.get("_charge")

    if not metki and not mayaki:
        continue      # кто не жил — того не показываем

    vsego_m += len(metki)
    vsego_y += len(mayaki)

    print()
    print("  " + "═" * 66)
    z = f"{charge:+.3f}" if charge is not None else "—"
    print(f"  {imya}   ·   род: {len(rod)}   метки: {len(metki)}   "
          f"маяки: {len(mayaki)}   заряд: {z}")
    print("  " + "═" * 66)

    if metki:
        print()
        print("  ── МЕТКИ (устойчивое — прошли порог 3) ──")
        for m in metki:
            otk = m.get("откуда", "?")
            print()
            print(f"     [{otk}]  повторов: {m.get('раз')}   "
                  f"паттерн: {m.get('паттерн')}")
            print(f"     {m.get('текст', '')}")

    if mayaki:
        print()
        print("  ── МАЯКИ (черновики — ещё не дозрели) ──")
        for d in mayaki:
            raz = d.get("раз", 1)
            print(f"     [{raz}/3]  {str(d.get('текст',''))[:70]}")
            print(f"              паттерн: {d.get('паттерн')}")

print()
print("  " + "─" * 66)
print(f"  ВСЕГО:  метки: {vsego_m}   маяки: {vsego_y}")
print()
if vsego_m:
    print("  Это выводы, ОПЛАЧЕННЫЕ ИХ ДЕНЬГАМИ. Не вписанные при рождении.")
    print("  Порог 3 сработал: черновик → черновик → черновик → МЕТКА.")
else:
    print("  Меток пока нет — только черновики. Нужно больше повторов.")
print()
