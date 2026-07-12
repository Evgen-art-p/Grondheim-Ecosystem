# -*- coding: utf-8 -*-
"""
proverka_ucheby.py
────────────────────────────────────────────────────────────────────
ДИАГНОСТИКА УЧЁБЫ. Почему заряд/якоря не двинулись после прогона.

Не гадаем — смотрим диск:
  1. КАКИЕ ПАТЧИ РЕАЛЬНО СТОЯТ (по маркерам в файлах). Если суда сенсоров
     или двух ярусов нет — поведение будет другим, и это не баг.
  2. ЗАРЯД, ЯКОРЯ, ЧЕРНОВИКИ каждого из девяти — как есть в паспорте.
  3. КОГДА паспорт последний раз ПИСАЛСЯ (mtime). Если он не менялся с
     момента прогона — запись не дошла вообще. Если менялся — дошла, и
     проблема в другом месте (например, в UI, который не перечитывает).

Ничего не пишет. Имя ASCII (PowerShell ест «Б»).
Из КОРНЯ репы:  python proverka_ucheby.py
"""
from __future__ import annotations
import io
import json
import sys
from datetime import datetime
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

# маркер → (файл, что он значит)
PATCHES = [
    ("MAGIC_IN_MASK_V1",            "Биржа/cartridge_registry.py", "магик в маске"),
    ("DVIZHOK_STOL_CHISTO_VYVOD_V1", "жители/dvizhok.py",          "рука опыта"),
    ("DVIZHOK_YAKORYA_YADRO_V1",    "жители/dvizhok.py",           "якоря/ядро"),
    ("NOSITEL_BRIDGE_V1",           "Биржа/nositel.py",            "мост (дверь)"),
    ("JUDGE_TRADER_NOSITEL_V1",     "Биржа/hooks.py",              "СУД ТРЕЙДЕРА (нога опыта)"),
    ("TESTER_STERILE_OPYT_V1",      "Биржа/tester_express.py",     "стерильность тестера"),
    ("TORG_LEARN_SWITCH_V1",        "Биржа/ui_torg.py",            "тумблер УЧИТЬ"),
    ("NATURA_V_TEMPERATURU_V1",     "Биржа/nositel.py",            "натура→температура"),
    ("KLON_DUSHI_V1",               "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A06/мозг.py",
                                                                   "клон души (A06)"),
    ("SUD_SENSOROV_V2",             "Биржа/hooks.py",              "СУД СЕНСОРОВ"),
    ("YAKORYA_DVA_YARUSA_V1",       "жители/dvizhok.py",           "два яруса якорей"),
    ("PRIBORY_TREJDEROV_V1",        "Биржа/ui_torg.py",            "приборы A06-A09"),
]

ZHITELI = [
    ("Вера", "A01"), ("Морж", "A02"), ("Паник", "A03"), ("Ганс", "A04"),
    ("Арчи", "архивариус"), ("Брут", "A06"), ("Илья", "A07"),
    ("Василий", "A08"), ("Сергей", "исполнитель"),
]


def yak_spisok(raw):
    return [x.strip() for x in (raw or "").replace("\\n", "\n").split("\n") if x.strip()]


def main() -> int:
    print("=" * 74)
    print("ДИАГНОСТИКА УЧЁБЫ — что РЕАЛЬНО на диске")
    print("=" * 74)

    # ── 1. патчи ─────────────────────────────────────────────
    print("\nПАТЧИ (по маркерам в файлах):")
    print("-" * 74)
    net = []
    for marker, rel, opis in PATCHES:
        f = ROOT / rel
        if not f.exists():
            print(f"  ?? {opis:<30} файла нет: {rel}")
            continue
        src = f.read_text(encoding="utf-8", errors="replace")
        if marker in src:
            print(f"  OK {opis:<30} {marker}")
        else:
            print(f"  !! {opis:<30} НЕ СТОИТ ({marker})")
            net.append((marker, opis))

    if net:
        print("\n  ⚠ НЕ ПРОГНАННЫЕ ПАТЧИ — это объясняет поведение:")
        for m, o in net:
            print(f"      · {o}")

    # ── 2. жители: заряд/якоря/черновики + mtime ─────────────
    print("\n" + "=" * 74)
    print("ЖИТЕЛИ — как есть в паспорте")
    print("-" * 74)
    print(f"{'КТО':<10} {'СЛОТ':<12} {'ЗАРЯД':>8} {'ЯКОРЕЙ':>7} {'ЧЕРН':>5}  ПАСПОРТ ПИСАЛСЯ")
    print("-" * 74)

    kovcheg = ROOT / "GRONDHEIM_CITY" / "жители" / "ковчег"
    dvinulis = []
    for imya, slot in ZHITELI:
        pp = kovcheg / imya / "passport.json"
        if not pp.exists():
            print(f"{imya:<10} {slot:<12} {'—':>8} {'—':>7} {'—':>5}  паспорта нет")
            continue
        try:
            p = json.loads(pp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"{imya:<10} {slot:<12}  паспорт не читается: {e}")
            continue
        charge = p.get("_charge")
        cts = p.get("_charge_ts", "")
        yak = len(yak_spisok(p.get("Anchor_Points", "")))
        ch = len(p.get("Draft_Anchors") or [])
        mt = datetime.fromtimestamp(pp.stat().st_mtime).strftime("%d.%m %H:%M:%S")
        zn = f"{charge:+.3f}" if isinstance(charge, (int, float)) else "нет"
        print(f"{imya:<10} {slot:<12} {zn:>8} {yak:>7} {ch:>5}  {mt}")
        if isinstance(charge, (int, float)) and abs(charge) > 0.0001:
            dvinulis.append((imya, charge, cts))

    # ── 3. вывод ─────────────────────────────────────────────
    print("=" * 74)
    if dvinulis:
        print("\nЗАРЯД ДВИНУЛСЯ У:")
        for imya, c, ts in dvinulis:
            print(f"   {imya}: {c:+.3f}   (когда: {ts or '—'})")
        print("\n→ ЗНАЧИТ ЗАПИСЬ ДОШЛА до паспорта. Если в кабинете цифры")
        print("  прежние — проблема в UI (не перечитывает), а не в мосте.")
    else:
        print("\nЗАРЯД НИ У КОГО НЕ ДВИНУЛСЯ (все нули или поля нет).")
        print("→ ЗНАЧИТ ЗАПИСЬ НЕ ДОШЛА. Смотри список патчей выше:")
        print("  · нет JUDGE_TRADER_NOSITEL_V1 → судья не построен;")
        print("  · нет TORG_LEARN_SWITCH_V1    → кабинет не шлёт learn=True;")
        print("  · всё стоит, а заряд ноль     → зовём меня, копаем дальше.")

    print("\nПОДСКАЗКА ПРО ЧЕРНОВИКИ: если стоит YAKORYA_DVA_YARUSA_V1, то")
    print("ПЕРВЫЙ минус ложится в ЧЕРНОВИК (колонка ЧЕРН), а НЕ в якоря —")
    print("это правильно, а не поломка. В якоря он уйдёт на ТРЕТЬЕМ повторе.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
