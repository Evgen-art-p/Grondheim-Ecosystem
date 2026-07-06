# patch_propiska_zhilye.py
"""
Хвост (найден 06.07): диалог «Прописка» в кабинете Брата показывал
ВСЕ локации без разбора — публичные наравне с жилыми. Требует
patch_tip_lokacii.py (проставляет "тип" в паспорта локаций).

Что делает патч в Брат/ui_brat.py:
  Фильтрует список локаций в do_propiska() — оставляет только
  "тип": "жилая". Публичные места (площади, храмы, рынки) больше
  не предлагаются как варианты прописки.

Запуск из КОРНЯ репо (ПОСЛЕ patch_tip_lokacii.py и
patch_propiska_brat.py):
    python patch_propiska_zhilye.py

Идемпотентен — если маркер PATCH_PROPISKA_ZHILYE уже стоит в файле,
скрипт не тронет его повторно.

Бэкап: Брат/ui_brat.py.bak_propiska_zhilye
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
TARGET = _ROOT / "Брат" / "ui_brat.py"
MARKER = "PATCH_PROPISKA_ZHILYE"
REQUIRED_MARKER = "PATCH_PROPISKA_BRAT"


def main():
    if not TARGET.exists():
        print(f"✗ не найден: {TARGET}")
        print("  запускай из корня репо (там же, где main.py)")
        return

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"— уже применён ({MARKER} найден в {TARGET.name}) — пропускаю")
        return

    if REQUIRED_MARKER not in src:
        print(f"✗ {REQUIRED_MARKER} не найден — сначала накати patch_propiska_brat.py")
        return

    anchor = (
        '        lokacii = [l for l in list_lokacii() if l.get("ID_Object") != "0000_CITY_GRONDHEIM"]\n'
    )
    if anchor not in src:
        print("✗ не нашёл строку списка локаций — файл изменился, откатываю")
        return

    replacement = (
        f'        # {MARKER} — прописываем только в жилое, не в публичные места\n'
        '        lokacii = [l for l in list_lokacii()\n'
        '                   if l.get("ID_Object") != "0000_CITY_GRONDHEIM"\n'
        '                   and l.get("тип", "") == "жилая"]\n'
    )
    src = src.replace(anchor, replacement, 1)

    backup = TARGET.with_name(TARGET.name + ".bak_propiska_zhilye")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ патч применён: {TARGET}")
    print(f"✓ бэкап:         {backup}")
    print("— диалог «Прописка» теперь показывает только локации с тип=жилая.")
    print("— проверь: python main.py → /brat → «Прописка»")


if __name__ == "__main__":
    main()
