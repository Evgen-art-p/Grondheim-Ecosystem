# -*- coding: utf-8 -*-
"""
peredvinut_lokacii.py · MARKER: KARTA_15_08_V3

ЧТО ДЕЛАЕТ
──────────
Ставит локациям новые координаты на карте города — по списку Шефа
(файл «Новый город»).

ВАЖНОЕ УТОЧНЕНИЕ ПРО МЕСТО ПРАВКИ
─────────────────────────────────
Шеф просил поправить `ГОРОД/ui_grondheim.py`. Координат там нет и не
должно быть: карта — ЗЕРКАЛО. Она сканирует папку локаций и рисует
каждую по её собственным Map_X/Y/W/H из паспорта. Правка в самой
карте стёрлась бы при первом же чтении паспортов.

Поэтому патч правит ПАСПОРТА:
    GRONDHEIM_CITY/локации/{id}/passport.json

Карту не трогает вообще — она подхватит новое сама.

ПРО ЖИТЕЛЕЙ (проверено, переезжать их не надо)
──────────────────────────────────────────────
Житель привязан к ИД ЛОКАЦИИ, а не к точке на карте: `sostoyanie.gde_ya`
отдаёт «где я» либо из state.json (если житель куда-то ушёл), либо по
прописке. Карта потом рисует его точкой ВНУТРИ прямоугольника его
локации. Значит здание переехало — жильцы переехали вместе с ним, сами.

Кто где сейчас (16 жителей, все с пропиской, бездомных нет):
    Торговый квартал — Андрей, Брут, Василий, Вера, Ганс, Илья, Морж, Паник
    Высотка          — Арчи, Джем, Лока, Оле, Сергей
    Квартал мастеров — Нина, Синди, София

ЧТО ПРОВЕРЕНО ДО ЗАПИСИ
───────────────────────
    · ни одна локация не вылезает за холст (2761×1504);
    · прямоугольники не накладываются друг на друга. В присланном
      списке у Торгового квартала стоял Y=984 — он оказывался целиком
      внутри Квартала мастеров; Шеф поправил на Y=280. Проверка на
      вложение осталась в патче: она и поймала эту опечатку;
    · жители влезают в новые размеры (самое тесное — Торговый
      квартал: 8 человек в один ряд, нужно 23px по высоте, есть 105).

Идемпотентен, .bak рядом на каждый паспорт, пишет только изменения.
Запуск: py peredvinut_lokacii.py   (или --suho)
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KARTA_15_08_V3"
SUHO = "--suho" in sys.argv

# id локации -> (имя у Шефа, X, Y, W, H)
NOVYE = {
    "0015_GRONDHEIM_ARCHIVE":    ("Архив",               261, 232, 121, 224),
    "0014_EXCHANGE":             ("Биржа",              2140, 292, 134,  76),
    "0006_CREATOR_TOWER":        ("Высотка",            1397, 153,  93, 233),
    "0011_LIBRARY_OF_MEANINGS":  ("Библиотека смыслов",  884, 271, 105, 210),
    "0008_OWL_CASTLE":           ("Замок Сов (Академия)", 458,  63, 380, 420),
    "0004_MASTER_QUARTER":       ("Квартал мастеров",    388, 979, 992, 525),
    "0013_TRADING_QUARTER":      ("Торговый квартал",   1028, 280, 288, 105),
    "0005_LIGHTHOUSE_AWAKENING": ("Маяк",               2555, 411,  94, 253),
    "0002_RESONANCE_SQUARE":     ("Площадь резонанса",   476, 752, 467, 145),
}

HOLST_W, HOLST_H = 2761, 1504


def _eto_koren(p: Path) -> bool:
    return ((p / "GRONDHEIM_CITY" / "локации").is_dir()
            and (p / "ГОРОД" / "ui_grondheim.py").exists())


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


def proverki() -> tuple:
    """Считаем ДО записи. Возвращает (можно ли писать, сколько пересечений).

    За холст — ошибка, писать нельзя. Пересечение — НЕ ошибка: город
    вправе иметь квартал внутри квартала. Но сказать об этом надо,
    иначе Шеф узнает о нём глазами на карте.
    """
    ok = True
    for lid, (imya, x, y, w, h) in NOVYE.items():
        if x < 0 or y < 0 or x + w > HOLST_W or y + h > HOLST_H:
            print(f"  ✗ {imya}: вылезает за холст "
                  f"({x + w}×{y + h} при {HOLST_W}×{HOLST_H})")
            ok = False
    ids = list(NOVYE)
    nalozheniy = 0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = NOVYE[ids[i]], NOVYE[ids[j]]
            ax, ay, aw, ah = a[1:]
            bx, by, bw, bh = b[1:]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                nalozheniy += 1
                vlozhen = (ax >= bx and ay >= by
                           and ax + aw <= bx + bw and ay + ah <= by + bh)
                vlozhen2 = (bx >= ax and by >= ay
                            and bx + bw <= ax + aw and by + bh <= ay + ah)
                if vlozhen or vlozhen2:
                    vnutri, snaruzhi = (a[0], b[0]) if vlozhen else (b[0], a[0])
                    print(f"  ⚠ {vnutri} лежит ЦЕЛИКОМ внутри "
                          f"{snaruzhi} — это не ошибка, но проверь, "
                          f"так ли задумано")
                else:
                    print(f"  ⚠ {a[0]} и {b[0]} налезают друг на друга")
    return ok, nalozheniy


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    lok_dir = koren / "GRONDHEIM_CITY" / "локации"

    print("\nПроверяю новые координаты до записи:")
    ok, nalozheniy = proverki()
    if not ok:
        print("\n✗ Координаты не сходятся — ничего не трогаю.")
        return 1
    print(f"  ✓ всё внутри холста"
          + ("" if not nalozheniy else
             f" · пересечений: {nalozheniy} (см. выше)"))

    print("\nПередвигаю:")
    tronuto, propuscheno = 0, []
    for lid, (imya, x, y, w, h) in NOVYE.items():
        f = lok_dir / lid / "passport.json"
        if not f.exists():
            propuscheno.append(f"{imya} (нет паспорта {lid})")
            continue
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            propuscheno.append(f"{imya} (паспорт не читается: {e})")
            continue

        bylo = (p.get("Map_X"), p.get("Map_Y"), p.get("Map_W"), p.get("Map_H"))
        stalo = (x, y, w, h)
        if bylo == stalo:
            print(f"  · {imya}: уже там")
            continue

        p["Map_X"], p["Map_Y"], p["Map_W"], p["Map_H"] = x, y, w, h
        p["Map_Updated"] = f"{datetime.now():%Y-%m-%d}"
        p["Map_Marker"] = MARKER
        if SUHO:
            print(f"  · {imya}: {bylo} → {stalo} (сухой прогон)")
            continue
        shutil.copy2(f, f.with_suffix(
            f".json.bak_karta_{datetime.now():%Y%m%d_%H%M%S}"))
        f.write_text(json.dumps(p, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print(f"  ✓ {imya}: {bylo} → {stalo}")
        tronuto += 1

    if propuscheno:
        print("\n⚠ не тронуто:")
        for s in propuscheno:
            print(f"    {s}")

    # ── кто где живёт: показать, а не двигать ──
    print("\nЖители (их двигать не надо — они привязаны к локации, "
          "не к точке):")
    try:
        if str(koren) not in sys.path:
            sys.path.insert(0, str(koren))
        import sostoyanie as sost
        po_lokaciyam = {}
        bezdomnye = []
        for pp in sorted((koren / "GRONDHEIM_CITY" / "жители")
                         .glob("*/*/passport.json")):
            dom = pp.parent
            try:
                z = json.loads(pp.read_text(encoding="utf-8"))
            except Exception:
                continue
            imya = z.get("Official_Name", dom.name)
            loc = sost.gde_ya(dom).get("локация")
            if not loc:
                bezdomnye.append(imya)
            else:
                po_lokaciyam.setdefault(loc, []).append(imya)
        for loc, lyudi in sorted(po_lokaciyam.items()):
            nazvanie = NOVYE.get(loc, (loc,))[0]
            print(f"  {nazvanie:22} {len(lyudi)} чел: {', '.join(lyudi)}")
            # влезут ли точками в новый прямоугольник
            if loc in NOVYE:
                _, _, _, w, h = NOVYE[loc]
                dot, gap, pad = 13, 4, 6
                v_ryad = max(1, (w - 2 * pad) // (dot + gap))
                ryadov = (len(lyudi) + v_ryad - 1) // v_ryad
                nuzhno = pad + ryadov * (dot + gap)
                if nuzhno > h:
                    print(f"      ⚠ точки вылезут: нужно {nuzhno}px "
                          f"по высоте, есть {h}px")
        if bezdomnye:
            print(f"  ⚠ без прописки (на карте не рисуются): "
                  f"{', '.join(bezdomnye)}")
    except Exception as e:
        print(f"  ⚠ не смог прочитать жителей: {e}")

    if not SUHO:
        print(f"\n✓ передвинуто локаций: {tronuto}")
        print("Карту править не пришлось — она читает паспорта сама.")
        print("Открой /grondheim и обнови страницу.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
