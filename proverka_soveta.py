# -*- coding: utf-8 -*-
"""
proverka_soveta.py
────────────────────────────────────────────────────────────────────
ВЕСЬ СОВЕТ РАЗОМ: кто сидит за каждым слотом, с каким магиком, с какой
температурой, и у кого ещё жив труп из -2.

Ничего не пишет. Имя ASCII (PowerShell ест «Б»).
Из КОРНЯ репы:  python proverka_soveta.py
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
CEHA = ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха"


def main() -> int:
    birzha = next((p.parent for p in ROOT.glob("*/nositel.py")), None)
    if birzha is None:
        print("!! нет nositel.py — сначала patch_etalon_avana_v1.py")
        return 1
    sys.path.insert(0, str(birzha))
    import nositel as N

    print("=" * 72)
    print("СОВЕТ БИРЖИ — кто за столом")
    print("=" * 72)
    print(f"{'СЛОТ':<22} {'НОСИТЕЛЬ':<12} {'MAGIC':<8} {'t°':<6} ДУША")
    print("-" * 72)

    trupov = 0
    pusto = 0
    zhivyh = 0

    for brain in sorted(CEHA.glob("*/слоты/*/мозг.py")):
        ceh = brain.parents[2].name
        slot = brain.parent.name
        src = brain.read_text(encoding="utf-8")

        # различаем ДВА трупа: мёртвая ДУША (лечится клоном) и мёртвый
        # ПИШУЩИЙ конец — sync_to_dna / Оле (осознанно оставлен: чем судить
        # сенсора, который не торгует, — решение Шефа, не механика).
        # ищем САМ ИМПОРТ, а не упоминание: в комментариях патча слова
        # «format_soul_for_agent» встречаются легально (там описано, что БЫЛО).
        # Первая версия проверки ловила собственный комментарий — и врала.
        trup_dushi = "import format_soul_for_agent" in src
        trup_pera = ("import sync_to_dna" in src) or ("import remember" in src)
        trup = trup_dushi
        d = N.dusha_slota(ceh, slot)

        if d:
            imya = d["носитель"]["имя"]
            magic = d.get("magic") or "—"
            t = N.temperatura_slota(ceh, slot)
            dusha = "ЖИВАЯ" if d["душа"] else "пусто"
            if d["душа"]:
                zhivyh += 1
        else:
            imya, magic, t, dusha = "— вакансия —", "—", None, "—"
            pusto += 1

        if trup_dushi:
            trupov += 1
            dusha += " ⚠ДУША МЁРТВАЯ (клон не взял!)"
        elif trup_pera:
            dusha += " · перо спит (sync_to_dna)"

        print(f"{ceh + '/' + slot:<22} {imya:<12} {str(magic):<8} "
              f"{str(t or '—'):<6} {dusha}")

    print("-" * 72)
    print(f"живых душ: {zhivyh}   вакансий: {pusto}   "
          f"мозгов с МЁРТВОЙ душой: {trupov}")
    if trupov:
        print("\n⚠ МЁРТВАЯ ДУША — клон не взял этот мозг. Гони "
              "patch_klon_dushi_v2.py и покажи мне его отчёт.")
    print("\n«перо спит» — это НЕ поломка: мёртвый sync_to_dna у сенсоров.")
    print("Их ПИШУЩИЙ конец сознательно не построен: чем судить Моржа,")
    print("который не торгует? Решение Шефа, не механика.")
    print("=" * 72)
    print("\nПишущий конец: у ТРЕЙДЕРОВ (magic есть) — работает через hooks.")
    print("У сенсоров magic нет и быть не должно: позиций не держат.")
    print("Их «опыт» — отдельный разговор с Шефом.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
