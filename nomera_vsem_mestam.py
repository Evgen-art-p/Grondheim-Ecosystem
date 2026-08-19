# -*- coding: utf-8 -*-
"""
nomera_vsem_mestam.py · MARKER: NOMERA_VSEM_V1

ЗАЧЕМ
─────
Механизм уже общий: любая НОВАЯ вакансия в любом квартале получает
номер сама (MAGIC_PRI_MESTE_V2). Но четыре поста заведены раньше и
остались без номеров — вчерашняя разовая правка ставила их только
местам со слотом цеха:

    bibliotekar        Оле     magic=None
    khranitel_arkhiva  Лока    magic=None
    mayak              София   magic=None
    rektor             Джем    magic=None

Разнобой: у одних мест номер есть, у других нет.

НУЖЕН ЛИ ИМ НОМЕР — ЧЕСТНО
──────────────────────────
Сегодня магик служит одному: после закрытия сделки найти человека и
отдать ему вывод судьи. У Оле и Джема сделок не бывает, так что
дыры сейчас нет.

Но у номера есть и второй смысл — найти человека ПО МЕСТУ вообще. Для
мест со слотом это работает через цех+слот; для постов без слота —
только через номер. Появятся у медийщиков свои исходы (отклик на
публикацию, оценка работы) — путь «номер → человек» понадобится
точно так же, и лучше, чтобы он уже был.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Раздаёт номера местам, у которых их нет, — по той же руке
   `magic_dlya_slota`, что и у новых вакансий: следующий свободный,
   столкнуться не могут.
2. Тем, кто на этих местах сидит, обновляет маску из поста — тем же
   ходом, что при приёме на работу (`_maska_po_postu`). Двух правд о
   найме не заводим.

Идемпотентен, .bak рядом. Уже пронумерованные места не трогает.
Запуск: py nomera_vsem_mestam.py   (или --suho)
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "NOMERA_VSEM_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "ГОРОД" / "rabota.py").exists() and (p / "main.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")

    sys.path[:0] = [str(koren / "ГОРОД"), str(koren / "Биржа"), str(koren)]
    try:
        import rabota as R
    except Exception as e:
        print(f"✗ ГОРОД/rabota.py не поднялся: {e}")
        return 1
    if not hasattr(R, "magic_dlya_slota"):
        print("✗ Нет руки magic_dlya_slota — накати сперва")
        print("  magic_ostayotsya_pri_meste.py")
        return 1

    posty = koren / "GRONDHEIM_CITY" / "посты"
    if not posty.exists():
        print("✗ Постов нет")
        return 1

    print("\nРаздаю номера местам, у которых их нет:")
    vydano = 0
    for d in sorted(posty.iterdir()):
        f = d / "пост.json"
        if not f.exists():
            continue
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠ {d.name}: не читается ({e})")
            continue
        if p.get("magic"):
            print(f"  · {d.name}: уже {p['magic']}")
            continue

        magic = R.magic_dlya_slota(p.get("слот") or "")
        p["magic"] = magic
        if not SUHO:
            shutil.copy2(f, f.with_suffix(
                f".json.bak_nomera_{datetime.now():%Y%m%d_%H%M%S}"))
            f.write_text(json.dumps(p, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        kto = ((p.get("кто_сидит") or {}).get("имя") or "").strip()
        print(f"  ✓ {d.name}: magic {magic}"
              + (f" · сидит {kto}" if kto else " · вакансия"))
        vydano += 1

        # сидящему — маску из поста, тем же ходом, что при приёме
        if kto and not SUHO:
            try:
                ok = R._maska_po_postu(kto, p)
                print(f"      маска {kto}: {'обновлена' if ok else 'не вышла'}")
            except Exception as e:
                print(f"      ⚠ маска {kto}: {e}")

    if SUHO:
        print(f"\n· выдал бы {vydano} номеров (сухой прогон)")
        return 0

    print(f"\n✓ выдано номеров: {vydano}")

    # ── что стало ──
    print("\nВсе места города:")
    try:
        import cartridge_registry as cr
    except Exception:
        cr = None
    for d in sorted(posty.iterdir()):
        f = d / "пост.json"
        if not f.exists():
            continue
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        m = p.get("magic")
        kto = ((p.get("кто_сидит") or {}).get("имя") or "— вакансия —")
        nayden = ""
        if cr and m:
            z = cr.resolve_by_magic(m)
            imya = (z or {}).get("имя")
            nayden = ("  ✓" if imya == kto else
                      f"  ⚠ по номеру: {imya or 'никто'}")
        print(f"  {d.name:22} magic={str(m):8} {kto}{nayden}")

    print("\nТеперь у всякого места в городе есть номер — независимо от")
    print("квартала. Медийщиков заведёшь — получат сразу при создании")
    print("вакансии, без единого патча.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
