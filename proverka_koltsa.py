# -*- coding: utf-8 -*-
"""
proverka_koltsa.py
────────────────────────────────────────────────────────────────────
ПРОВЕРКА КОЛЬЦА на Илье (A07) после patch_etalon_avana_v1.

Показывает ФАКТ, а не галочку:
  • кто сидит за столом A07 и с каким магиком (из маски, не из константы);
  • ЧТО РЕАЛЬНО УХОДИТ В МОДЕЛЬ — душа Ильи целиком, как её увидит LLM;
  • суд по Котину на живых числах (без LLM);
  • нет ли мёртвых импортов studio.* в мозге A07.

НИЧЕГО НЕ ПИШЕТ в паспорт Ильи (проверка чтением). Имя файла — ASCII:
PowerShell на машине Шефа ест букву «Б» при вставке.

Из КОРНЯ репы:  python proverka_koltsa.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
OK, BAD = "OK ", "!! "


def main() -> int:
    print("=" * 64)
    print("PROVERKA KOLTSA — Илья за столом A07")
    print("=" * 64)
    fails = 0

    birzha = next((p.parent for p in ROOT.glob("*/nositel.py")), None)
    if birzha is None:
        print(BAD + "нет nositel.py — сначала patch_etalon_avana_v1.py")
        return 1
    sys.path.insert(0, str(birzha))
    print(OK + f"дверь моста: {birzha.name}/nositel.py")

    import nositel as N

    # ── мозг A07: труп вычищен? ──────────────────────────────────
    brain = next((p for p in ROOT.glob("*/*/*/*/слоты/A07/мозг.py")), None)
    if brain is None:
        print(BAD + "не нашёл мозг A07")
        fails += 1
    else:
        src = brain.read_text(encoding="utf-8")
        if "studio.grondheim_memory" in src:
            print(BAD + "в мозге A07 ЖИВ мёртвый импорт studio.grondheim_memory")
            fails += 1
        else:
            print(OK + "мозг A07: импорты трупа из -2 вычищены")
        if "_MY_MAGIC = 100002" in src:
            print(BAD + "в мозге A07 жива константа _MY_MAGIC (копия магика)")
            fails += 1
        else:
            print(OK + "мозг A07: магик берётся из маски, не константой")

    # ── читающий конец ───────────────────────────────────────────
    print("-" * 64)
    d = N.dusha_slota("торговый_хаос", "A07")
    if not d:
        print(BAD + "A07 → носителя нет!")
        return 1
    n = d["носитель"]
    print(f">>> ЗА СТОЛОМ A07: {n['имя']} ({n['id']}), magic {d['magic']}")
    if n["имя"] != "Илья":
        print(BAD + "это не Илья!")
        fails += 1
    if not d["душа"]:
        print(BAD + "душа ПУСТА — трейдер снова голый")
        fails += 1
    print("-" * 64)
    print("ЧТО УХОДИТ В МОДЕЛЬ ПЕРЕД РЕШЕНИЕМ (душа носителя):")
    print()
    for line in d["душа"].split("\n"):
        print("   " + line)

    # ── суд (без записи) ─────────────────────────────────────────
    print("-" * 64)
    print("СУД ПО КОТИНУ — считает КОД, не LLM (проба, ничего не пишет):")
    probe = [
        ("SHORT", "BULL", -1.0, "минус ПРОТИВ ветра"),
        ("LONG", "BULL", -0.8, "минус по ветру (рутина)"),
        ("LONG", "BULL", 2.6, "крупный плюс по ветру"),
    ]
    for dir_, bias, r, why in probe:
        v = N.sudit_po_kotinu(dir_, bias, r, None, "2010.05.13")
        print(f"   {why:<26} → {v or '(рутина — в опыт не идёт)'}")

    print("=" * 64)
    if fails:
        print(f"ИТОГ: {fails} проблем(ы).")
        return 1
    print("ИТОГ: КОЛЬЦО ЗАМКНУТО.")
    print("Илья читает свой опыт перед сделкой и допишет вывод после неё.")
    print("Дальше: прогон тестера — и смотрим, растут ли его якоря.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
