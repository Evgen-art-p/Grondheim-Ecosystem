# -*- coding: utf-8 -*-
# KOMMONY_V_PASPORTAH_V1 — досброс редкости там, где её забыли
"""
РЕДКОСТЬ В ПАСПОРТАХ — ДОСБРОС

ЧТО НАШЛОСЬ 10.09 при сверке с живой репой. Решение Шефа 09.09 —
все жители Common — исполнено НАПОЛОВИНУ. Патч `vse_kommony.py`
накачен и сработал верно, но правит он только реестр:

    00_REGISTRY_NFT/catalog.json   agent: Common ×19   ✅
    ковчег/*/passport.json         Rare ×10, Epic ×5, Mythic ×4   ❌

Редкость лежит В ДВУХ местах, а сбросили в одном. Получилась ровно
та болезнь, от которой лечит Закон Рычага: один предмет — два
разных значения, и какое правда, зависит от того, кто спросил.

Опаснее то, что в промпт жителю душа собирается ИЗ ПАСПОРТА. То
есть в реестре он давно Common, а сам про себя читает «Mythic» —
и говорит соответственно.

ЧТО ДЕЛАЕТ ПАТЧ. Ставит `Rarity: Common` в паспортах ковчега — и
только там, где сейчас стоит другое. Ничего больше в паспорте не
трогает: ни Social_Rank, ни имена, ни печать, ни ключ.

Места не трогает вовсе: локация не растёт и ничего не добивается —
она стоит, и стоит для всех. Ей Mythic по праву.

БЕЗОПАСНОСТЬ: .bak_common рядом с каждым правленым паспортом,
идемпотентен (второй прогон скажет «нечего менять»), формат JSON
сохраняется тем же отступом, `--suho` не трогает диск.

    python sbrosit_redkost_v_pasportah.py --suho
    python sbrosit_redkost_v_pasportah.py

`шесть·проверено·до·корня`
"""
import json
import shutil
import sys
from pathlib import Path

SUHO = "--suho" in sys.argv
NADO = "Common"

_REPO = Path(__file__).resolve().parent
KOVCHEG = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"
KATALOG = _REPO / "00_REGISTRY_NFT" / "catalog.json"


def _chitat(p: Path):
    for kod in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return json.loads(p.read_text(encoding=kod))
        except Exception:
            continue
    return None


def proverit_katalog():
    """Только смотрим: каталог правит vse_kommony.py, не мы."""
    if not KATALOG.exists():
        print("  каталога нет — пропускаю проверку")
        return
    kat = _chitat(KATALOG)
    if not isinstance(kat, list):
        return
    ne_common = [x.get("Official_Name") for x in kat
                 if x.get("Object_Type_Class") == "agent"
                 and x.get("Rarity") != NADO]
    if ne_common:
        print(f"  ! в каталоге ещё не Common: {ne_common}")
        print("    — прогони сперва vse_kommony.py, он про каталог")
    else:
        print("  каталог: у всех жителей Common ✓")


def main():
    print()
    print("РЕДКОСТЬ В ПАСПОРТАХ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    if not KOVCHEG.exists():
        print("!! ковчега нет — запускать из корня репы")
        return

    print("1. КАТАЛОГ (только смотрю):")
    proverit_katalog()

    print()
    print("2. ПАСПОРТА:")
    tronuto, uzhe = 0, 0
    for d in sorted(KOVCHEG.iterdir()):
        if not d.is_dir():
            continue
        p = d / "passport.json"
        if not p.exists():
            continue
        pasp = _chitat(p)
        if not isinstance(pasp, dict):
            print(f"  {d.name}: паспорт не прочитался — пропускаю")
            continue
        bylo = pasp.get("Rarity")
        if bylo == NADO:
            uzhe += 1
            continue
        pasp["Rarity"] = NADO
        if not SUHO:
            shutil.copy2(p, p.with_suffix(".json.bak_common"))
            p.write_text(json.dumps(pasp, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        print(f"  {d.name}: {bylo} → {NADO}")
        tronuto += 1

    print()
    if uzhe:
        print(f"  уже были Common: {uzhe}")
    if not tronuto:
        print("Нечего менять — все паспорта уже Common.")
    elif SUHO:
        print(f"Сухой прогон: тронул бы {tronuto}, на диске ничего не менял.")
    else:
        print(f"Поправлено паспортов: {tronuto}. Бэкапы — .bak_common")
    print()


if __name__ == "__main__":
    main()
