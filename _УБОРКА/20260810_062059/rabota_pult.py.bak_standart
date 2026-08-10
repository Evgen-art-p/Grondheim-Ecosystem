# -*- coding: utf-8 -*-
# RABOTA_PULT_V1
"""
ПУЛЬТ РАБОТЫ — смотреть, принимать, увольнять. Из корня репо.

    python rabota_pult.py                      кто где сидит
    python rabota_pult.py --zavesti            завести документы мест
    python rabota_pult.py --prinyat A06 Брут   принять на место
    python rabota_pult.py --uvolit A06         уволить с места
    python rabota_pult.py --uvolit A06 --pochemu "ушёл учиться"

Цех по умолчанию — торговый_хаос, другой задаётся ключом --ceh.
Кнопки в кабинете Брата придут следом; пульт останется как есть —
он же и проверка, что механизм работает без всякого UI.
"""
import argparse
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
sys.path.insert(0, str(KOREN / "Биржа"))

import rabota as R   # noqa: E402

# заготовки бланка для трёх мест Биржи: что можно заполнить, не
# придумывая — остальное Шеф допишет на Странице Работы.
ZAGOTOVKI = {
    "A06": {"название": "Трейдер-пробой",
            "чем_занят": "входит по пробою",
            "судья": "рынок"},
    "A07": {"название": "Трейдер-ранний",
            "чем_занят": "входит рано, на первой волне движения",
            "судья": "рынок"},
    "A08": {"название": "Трейдер-откат",
            "чем_занят": "входит на откате к первой волне",
            "судья": "рынок"},
}


def pokazat(ceh: str):
    print("═" * 60)
    print("МЕСТА БИРЖИ")
    print("═" * 60)
    for m in R.spisok():
        if ceh and m["цех"] != ceh:
            continue
        kto = m["кто_сидит"] or "— свободно"
        dok = "документ есть" if m["документ"] else "документа нет"
        mozg = "" if m["мозг"] else "  (мозга в слоте нет)"
        print(f"  {m['слот']}  {m['роль'] or m['название']:<22} "
              f"{kto:<16} {dok}{mozg}")
    print("─" * 60)
    print("принять:  python rabota_pult.py --prinyat A06 Имя")
    print("уволить:  python rabota_pult.py --uvolit A06")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ceh", default="торговый_хаос")
    ap.add_argument("--zavesti", action="store_true")
    ap.add_argument("--prinyat", nargs=2, metavar=("СЛОТ", "ИМЯ"))
    ap.add_argument("--uvolit", metavar="СЛОТ")
    ap.add_argument("--pochemu", default="")
    a = ap.parse_args()

    if a.zavesti:
        for m in R.spisok():
            if m["цех"] != a.ceh:
                continue
            polya = dict(ZAGOTOVKI.get(m["слот"], {}))
            polya.setdefault("название", m["роль"] or m["слот"])
            ok, msg = R.zavesti(a.ceh, m["слот"], polya)
            print(f"  {m['слот']}: {msg}" if ok else f"  ✗ {m['слот']}: {msg}")
        print()

    if a.prinyat:
        slot, imya = a.prinyat
        ok, msg = R.prinyat(a.ceh, slot, imya, pochemu=a.pochemu)
        print(("✓ " if ok else "✗ ") + msg)
        print()

    if a.uvolit:
        ok, msg = R.uvolit(a.ceh, a.uvolit, pochemu=a.pochemu)
        print(("✓ " if ok else "✗ ") + msg)
        print()

    pokazat(a.ceh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
