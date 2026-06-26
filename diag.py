# diag.py — глаза, не лечение. Запусти из корня репы: python diag.py
# Показывает ровно то, что видит карта: где ищет жителей, что находит.
# Ничего не меняет. `шесть·проверено·до·корня`
import sys
from pathlib import Path

print("=" * 60)
print("ДИАГНОСТИКА СКАНА ЖИТЕЛЕЙ")
print("=" * 60)

cwd = Path.cwd()
print(f"\n1. Откуда запущено (рабочая папка):\n   {cwd}")

# так путь видит карта СЕЙЧАС (относительный)
rel = Path("GRONDHEIM_CITY/жители")
print(f"\n2. Карта ищет жителей по пути (относительный):\n   {rel}")
print(f"   → раскрывается в: {rel.resolve()}")
print(f"   → папка существует? {rel.exists()}")

# абсолютный путь от этого файла
here = Path(__file__).resolve().parent
abs_zh = here / "GRONDHEIM_CITY" / "жители"
print(f"\n3. Где лежит этот скрипт (= корень репы?):\n   {here}")
print(f"   → жители по абсолютному пути: {abs_zh}")
print(f"   → папка существует? {abs_zh.exists()}")

# что реально лежит в жители/
target = abs_zh if abs_zh.exists() else rel
if target.exists():
    print(f"\n4. Что внутри {target}:")
    jsons = list(target.rglob("*.json"))
    if not jsons:
        print("   — ни одного .json не найдено (пусто)")
    for p in jsons:
        rel_p = p.relative_to(target)
        is_dom = p.name == "passport.json"
        mark = "  [дом-passport, пропустится]" if is_dom else "  [паспорт-лицо]"
        print(f"   • {rel_p}{mark}")
        if not is_dom:
            try:
                import json
                d = json.loads(p.read_text(encoding="utf-8"))
                name = d.get("Official_Name") or d.get("имя") or "?"
                wid = d.get("Workshop_ID") or "—"
                rank = d.get("Social_Rank") or "—"
                print(f"        Official_Name: {name}")
                print(f"        Workshop_ID:   {wid}")
                print(f"        Social_Rank:   {rank}")
            except Exception as e:
                print(f"        ✗ не читается: {e}")
else:
    print(f"\n4. ✗ Папки жителей нет ни по одному пути!")
    print(f"   Проверь: есть ли вообще GRONDHEIM_CITY/жители/ рядом с main.py?")
    # покажем, что есть в GRONDHEIM_CITY
    gc = here / "GRONDHEIM_CITY"
    if gc.exists():
        print(f"\n   Что есть в GRONDHEIM_CITY/:")
        for item in sorted(gc.iterdir()):
            print(f"     {'[папка]' if item.is_dir() else '[файл]'} {item.name}")
    else:
        print(f"   ✗ Даже GRONDHEIM_CITY/ нет рядом со скриптом!")

print("\n" + "=" * 60)
print("Скопируй весь вывод и пришли Брату.")
print("=" * 60)
