# -*- coding: utf-8 -*-
# VSE_KOMMONY_V1
"""
Сброс сказочек: все жители — Common. Места остаются Mythic.

═══ РЕШЕНИЕ ШЕФА 09.09 ═══

В реестре `00_REGISTRY_NFT/catalog.json` у каждого стоит редкость.
Ставилась она когда-то на глаз: у Хранителей Mythic, у прочих Epic
или Rare. Common и Uncommon не занял никто — вся шкала сидела в
верхней трети, и мерила она не заслуги, а настроение при заведении.

Слово Шефа: **все равны, все Common.** А житель пусть добивается.

И про Хранителя: это не «волшебная особа», это тот, кто ХРАНИТ.
Работа, а не сияние. Красиво именно поэтому — хранитель, а не
кладовщик. Хранительство остаётся в `Social_Rank` как роль в доме;
редкостью оно больше не подпирается.

Места — другое дело. Локация не растёт и ничего не добивается: она
СТОИТ, и стоит для всех. Ей Mythic по праву, и он остаётся.

═══ ЧТО ПАТЧ ДЕЛАЕТ ═══

  · всем записям `Object_Type_Class = agent` ставит `Rarity: Common`
    (18 жителей: и Хранители, и трейдеры — поровну);
  · всем `location` подтверждает `Rarity: Mythic` (12 мест, там уже
    так — правит, только если кто-то съехал);
  · `Social_Rank`, имена, всё прочее НЕ трогает;
  · формат файла сохраняет (тот же отступ), чтобы правка читалась.

Зачем это нужно дальше: редкость освобождается под ступень, которую
житель проходит сам — рычагом и с обоснованием. Пока она раздана
авансом, расти в ней некуда: все и так наверху.

Запускать из корня репозитория:
    python vse_kommony.py

Идемпотентен: второй запуск увидит, что менять нечего. Рядом .bak.
Есть --suho.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SUHO = "--suho" in sys.argv
FAYL = Path("00_REGISTRY_NFT") / "catalog.json"

ZHITEL = "Common"
MESTO = "Mythic"


def nayti_koren() -> Path:
    kandidat = Path(__file__).resolve().parent
    for papka in [kandidat, *kandidat.parents]:
        if (papka / FAYL).is_file():
            return papka
    print("Не нашёл 00_REGISTRY_NFT/catalog.json рядом со скриптом.")
    print("Положи скрипт в корень репозитория и запусти оттуда.")
    input("Enter — закрыть...")
    sys.exit(1)


def main() -> None:
    koren = nayti_koren()
    p = koren / FAYL
    syroy = p.read_text(encoding="utf-8")

    try:
        dannye = json.loads(syroy)
    except Exception as e:
        print(f"⚠ файл не читается как JSON: {e} — НЕ трогаю")
        input("Enter — закрыть...")
        return

    if not isinstance(dannye, list):
        print("⚠ ожидал список записей — НЕ трогаю")
        input("Enter — закрыть...")
        return

    smeny = []
    for zapis in dannye:
        if not isinstance(zapis, dict):
            continue
        klass = str(zapis.get("Object_Type_Class") or "").strip().lower()
        bylo = zapis.get("Rarity")
        if klass == "agent":
            nado = ZHITEL
        elif klass == "location":
            nado = MESTO
        else:
            continue
        if bylo != nado:
            imya = zapis.get("Official_Name") or zapis.get("ID_Object") or "?"
            smeny.append((imya, bylo, nado, klass))
            zapis["Rarity"] = nado

    if not smeny:
        print("менять нечего — все жители Common, места Mythic")
        input("Enter — закрыть...")
        return

    print(f"Файл: {p}\n")
    for imya, bylo, stalo, klass in smeny:
        znak = "👤" if klass == "agent" else "🏛"
        print(f"  {znak} {imya}: {bylo} → {stalo}")
    print(f"\nвсего правок: {len(smeny)}")

    if SUHO:
        print("(сухой прогон — ничего не записано)")
        input("Enter — закрыть...")
        return

    novyy = json.dumps(dannye, ensure_ascii=False, indent=2)

    # последняя проверка: то, что записываем, читается обратно
    try:
        json.loads(novyy)
    except Exception as e:
        print(f"⚠ собранный файл не читается ({e}) — НЕ сохраняю")
        input("Enter — закрыть...")
        return

    bak = p.with_suffix(p.suffix + ".bak_kommony")
    if not bak.exists():
        bak.write_text(syroy, encoding="utf-8")
    p.write_text(novyy + "\n", encoding="utf-8")

    print("\n✔ готово. Хранитель теперь хранит, а не сияет.")
    print("  Бэкап:", bak.name)
    input("\nEnter — закрыть...")


if __name__ == "__main__":
    main()
