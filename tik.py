# tik.py — СУТОЧНЫЙ ТИК. Город выдыхает.
# ─────────────────────────────────────────────────────────────
# SUTOCHNY_TIK_V1. Проходит по всем жителям, остужает заряд за время
# тишины и ОСАЖДАЕТ результат в паспорт.
#
# Зачем руками: у города пока НЕТ своего цикла — main.py только рисует
# страницы, ни таймера, ни ночи. Пока цикла нет — тик жмёт Шеф.
# Когда Биржа заработает в полную — привяжем к сессиям (решение Шефа).
#
# Гонять можно сколько угодно: если время не шло, ничего не изменится.
#
# Запуск из корня репо:
#   python tik.py           — показать и остудить
#   python tik.py --tiho    — только цифры, без разговоров
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "жители"))
from dvizhok import Dvizhok   # noqa: E402

CITY = ROOT / "GRONDHEIM_CITY"
SKIP = {".git", "__pycache__", ".venv", "venv", "node_modules",
        "_ARCHIVE", "_OLD", ".vscode"}


def nayti_doma():
    """Живой скан. Житель = паспорт + натура. У локаций натуры нет."""
    out = []
    for pp in CITY.rglob("passport.json"):
        if any(x in SKIP for x in pp.parts):
            continue
        try:
            p = json.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(p, dict) and p.get("DNA_Static"):
            out.append(pp.parent)
    return sorted(set(out))


def main():
    tiho = "--tiho" in sys.argv

    if not tiho:
        print()
        print("  ГОРОД ВЫДЫХАЕТ — суточный тик")
        print("  " + "─" * 60)

    doma = nayti_doma()
    if not doma:
        print("  ⚠ жителей не нашёл"); sys.exit(1)

    print()
    print(f"  {'житель':14s} {'было':>8s} {'стало':>8s} {'тишины':>9s} {'':>3s}")
    print("  " + "─" * 50)

    dvinulos = 0
    for dom in doma:
        try:
            d = Dvizhok(dom)
        except Exception as ex:
            print(f"  {dom.name[:14]:14s}  ⚠ {ex}")
            continue

        imya = d.p.get("Official_Name") or dom.name
        r = d.ostyt_po_vremeni()

        if not r["остыл"]:
            print(f"  {str(imya)[:14]:14s} {r['было']:>+8.3f} {'—':>8s} "
                  f"{'—':>9s}   ({r['причина']})")
            continue

        d.sохранить()   # осадка на диск — ВОТ ЗДЕСЬ, честно
        dvinulos += 1

        znak = ""
        if abs(r["было"]) > 0.8 and abs(r["стало"]) <= 0.8:
            znak = "  ← архив закрылся, отпустило"
        elif abs(r["стало"]) < 0.001:
            znak = "  ← покой"

        sutok = r["часов"] / 24.0
        print(f"  {str(imya)[:14]:14s} {r['было']:>+8.3f} {r['стало']:>+8.3f} "
              f"{sutok:>8.1f}д{znak}")

    print()
    print(f"  выдохнули: {dvinulos} из {len(doma)}")
    if not tiho:
        print()
        print("  Заряд тает по времени: полураспад = сутки × (1 + упрямство).")
        print("  Упрямый держит дольше — так и должно быть.")
        print()


if __name__ == "__main__":
    main()
