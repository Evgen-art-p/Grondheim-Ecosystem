# patch_tip_lokacii.py
"""
Хвост (найден 06.07): «Прописка» показывала ВСЕ локации подряд,
включая Площадь Резонанса — публичное место, роутер энергии
города, не дом. Шеф лично прописал туда Локу, потому что выбор
был доступен в списке — не по злому умыслу кода, а потому что
у локации нет поля "тип" вообще.

Причина: назначение локации сейчас живёт только в свободном тексте
(Profession/Area_of_Responsibility) — код не может из него сделать
вывод программно, нужен явный, читаемый ключ.

Этот скрипт — РАЗОВАЯ МИГРАЦИЯ данных (не патч кода): проставляет
"тип" в паспорта уже существующих локаций по их реальному
назначению, которое сам Шеф уже описал в лоре:

  0002_RESONANCE_SQUARE — публичная (роутер энергии, не дом)
  0004_MASTER_QUARTER   — жилая (лофты мастеров, "дом для всех агентов")
  0006_CREATOR_TOWER    — жилая (дом Творца)
  0013_TRADING_QUARTER  — жилая ("дом трейдеров Грондхейма")

Новые локации, рождённые позже, должны получать "тип" явно при
рождении (Страница Жизни) — это отдельная правка формы, здесь не
делается, только миграция уже существующих четырёх.

Запуск из КОРНЯ репо:
    python patch_tip_lokacii.py

Идемпотентен — если у локации уже стоит нужный "тип", не трогает её.
`шесть·проверено·до·корня`
"""
from pathlib import Path
import json

_ROOT = Path(__file__).resolve().parent
LOK_DIR = _ROOT / "GRONDHEIM_CITY" / "локации"

TIPY = {
    "0002_RESONANCE_SQUARE": "публичная",
    "0004_MASTER_QUARTER":   "жилая",
    "0006_CREATOR_TOWER":    "жилая",
    "0013_TRADING_QUARTER":  "жилая",
}


def main():
    if not LOK_DIR.exists():
        print(f"✗ не найден: {LOK_DIR}")
        print("  запускай из корня репо (там же, где main.py)")
        return

    changed, skipped, missing = [], [], []

    for lid, tip in TIPY.items():
        pf = LOK_DIR / lid / "passport.json"
        if not pf.exists():
            missing.append(lid)
            continue
        try:
            p = json.loads(pf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"✗ {lid}: не смог прочитать ({e})")
            continue
        if p.get("тип") == tip:
            skipped.append(lid)
            continue
        p["тип"] = tip
        pf.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
        changed.append((lid, tip))

    print(f"✓ проставлено: {len(changed)}")
    for lid, tip in changed:
        print(f"    {lid} → тип: {tip}")
    if skipped:
        print(f"— уже стояло верно: {len(skipped)} ({', '.join(skipped)})")
    if missing:
        print(f"⚠ не найдены в каталоге (пропущены): {', '.join(missing)}")


if __name__ == "__main__":
    main()
