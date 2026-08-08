# -*- coding: utf-8 -*-
# VAKANSIYA_TREYDERA_V1
"""
ВАКАНСИЯ ТРЕЙДЕРА — чтобы работа была в паспорте, а не только в маске.

    python vakansiya_treydera.py --suho      посмотреть
    python vakansiya_treydera.py             завести вакансию Брута
    python vakansiya_treydera.py --vse       завести все три
    python vakansiya_treydera.py --posadit   и посадить того, кто в слоте

Запускать из КОРНЯ репо.

ЗАЧЕМ
    В городе есть два разных способа сказать «он тут работает»:

      СЛОТ  — рабочее место в цехе. Кто в нём сидит, решает Закон
              Пары через маску резидента. Это про КВАРТАЛ.
      ПОСТ  — должность города: Ректор, Библиотекарь, Хранитель. Она
              лежит у жителя В ПАСПОРТЕ (поле «Посты») и едет с ним
              куда угодно: домой, в Академию, к Ректору.

    У трейдеров было только первое. Значит вне Биржи житель не знал,
    что он трейдер: в Академии он просто студент, дома просто житель.
    А по твоему же слову — «живой слот с мозгом это трейдер, и он
    обычный житель города». Обычный житель носит работу с собой.

ЧТО ДЕЛАЕТ
    1. Заводит пост на диске — папка `GRONDHEIM_CITY/посты/{id}/` с
       `пост.json`. Ровно так же, как заведены Ректор и Библиотекарь.
    2. С ключом --posadit находит, кто сидит в слоте (Закон Пары), и
       сажает его на пост — то есть пишет работу ему В ПАСПОРТ.

    Заведено уже — не трогает. Занято другим — не вышибает.

ТРИ ВАКАНСИИ, А НЕ ОДНА
    Роли разные по существу, а не по темпераменту: пробой, ранний,
    откат — три разных места входа на одной структуре. Поэтому и
    вакансии три, каждая со своим названием.
"""
import argparse
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
GOROD = KOREN / "ГОРОД"
CEH = "торговый_хаос"

# id поста · название · слот в цехе · чем занят
VAKANSII = [
    ("treyder_proboy", "Трейдер-пробой (Биржа)", "A06",
     "входит по пробою — разворотный бар на конце коррекции"),
    ("treyder_ranniy", "Трейдер-ранний (Биржа)", "A07",
     "входит рано — на первой волне нового движения"),
    ("treyder_otkat", "Трейдер-откат (Биржа)", "A08",
     "входит на первом откате к волне 1 — канон Котина"),
]

GDE = "Биржа · торговый квартал"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vse", action="store_true", help="все три роли")
    ap.add_argument("--posadit", action="store_true",
                    help="и посадить того, кто сидит в слоте")
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    if not GOROD.exists():
        print("✗ не вижу папку ГОРОД — запускай из КОРНЯ репо")
        return 1
    sys.path.insert(0, str(GOROD))

    try:
        import rezidenty as R
    except Exception as e:
        print(f"✗ rezidenty.py не завёлся: {e}")
        return 1

    try:
        import cartridge_registry as reg
    except Exception:
        reg = None

    nuzhno = VAKANSII if a.vse else VAKANSII[:1]

    print("═" * 56)
    print("ВАКАНСИИ ТРЕЙДЕРА" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 56)

    for post_id, nazvanie, slot, chem in nuzhno:
        print(f"\n{nazvanie}   (слот {slot})")
        print(f"  чем занят: {chem}")

        if a.suho:
            est = (R.POSTY_DIR / post_id / "пост.json").exists()
            print(f"  пост: {'уже заведён' if est else 'будет заведён'}")
        else:
            ok, soobsh = R.zavesti_post(post_id, nazvanie, gde=GDE,
                                        dvizhok="")   # движок живёт в слоте
            print(f"  пост: {soobsh}" if ok else f"  ✗ пост: {soobsh}")
            if not ok:
                continue

        # кто сидит в слоте — по Закону Пары
        kto = ""
        if reg is not None:
            try:
                r = reg.resolve_para(CEH, slot, "Биржа") or {}
                kto = r.get("имя") or r.get("name") or ""
            except Exception:
                kto = ""
        print(f"  в слоте: {kto or '— вакансия'}")

        if not a.posadit:
            continue
        if not kto:
            print("  сажать некого — слот пуст")
            continue
        if a.suho:
            print(f"  посадил бы: {kto}")
            continue

        zanyal = R.kto_na_postu(post_id)
        if zanyal and zanyal != kto:
            print(f"  ⚠ пост занят: {zanyal} — чужое не вышибаю")
            continue
        ok, soobsh = R.posadit(post_id, kto)
        print(f"  {kto} → {soobsh}" if ok else f"  ✗ {soobsh}")

    print("\n" + "─" * 56)
    print("ЧТО ЭТО ДАЛО")
    print("  Работа переехала В ПАСПОРТ жителя (поле «Посты»).")
    print("  Теперь он знает, что он трейдер, не только на Бирже:")
    print("  дома, в Академии и у Ректора — везде, где читают паспорт.")
    if not a.posadit:
        print("\n  Вакансия заведена, но пустая. Посадить того, кто в слоте:")
        print("      python vakansiya_treydera.py --posadit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
