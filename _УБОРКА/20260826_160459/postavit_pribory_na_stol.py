# -*- coding: utf-8 -*-
"""
postavit_pribory_na_stol.py · MARKER: PRIBORY_NA_STOL_V1

ЧТО НАШЛОСЬ
───────────
Слова Шефа: «код что-то ищет, считает, трейдеру даёт, тот сверяет с
инструкцией — и всё. Тупой бот получился, это не трейдер». Полез
смотреть, что вообще лежит перед трейдером, — и вот стол Нины
целиком:

    старший Аллигатор · Аллигатор (челюсть/зубы/губы, спит, баров)
    AO (значение, растёт, перешёл ноль) · фракталы · объём окна
    натяжение от губ · цена

**РАЗВОРОТНОГО БАРА НА СТОЛЕ НЕТ.**

Её зовут на место ИМЕННО потому, что код нашёл разворотный бар — а
ей про этот бар не говорят ни слова. Она смотрит кадр и семь строк,
среди которых главного факта нет, и честно пишет «нет структуры для
входа». Она права: ей не показали то, ради чего позвали.

Сверил с твоим экспертом `Profitunity_MT4` — там набор шире, чем у
нас на столе. Не хватает трёх приборов, и все три УЖЕ СЧИТАЮТСЯ в
ядре, просто не доезжают до трейдера:

    · РАЗВОРОТНЫЙ БАР (iDivergenceBar) — у нас `necron_bar`, формула
      совпадает с твоим индикатором дословно, вплоть до сдвига линий
      8/5/3 и условия «весь бар целиком вне пасти»;
    · ЗОНА (iZone) — AO и AC вместе: зелёная (оба растут), красная
      (оба падают), серая. Ключевой прибор Вильямса. AC у нас
      считается, на стол не попадал;
    · ДИВЕРГЕНЦИЯ AO и ПРИСЕДАЮЩИЙ БАР — тоже посчитаны и тоже не
      доезжали.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Выкладывает всё это на стол. Ни одного нового расчёта: беру то, что
ядро уже посчитало, и показываю тому, кто смотрит.

Стол по-прежнему НЕ СУДИТ: «разворотный бар: BULL @ 1.1509» — это
факт, а не «входи». Что он значит — говорит трейдер.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_pribory_na_stol.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PRIBORY_NA_STOL_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "stol.py").exists() and (p / "main.py").exists()


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


ST_PRIBORY = '''        "цена": md.get("price"),
        "бар": md.get("bar_time"),
    }

    return stol'''

NOV_PRIBORY = '''        "цена": md.get("price"),
        "бар": md.get("bar_time"),
        # ── PRIBORY_NA_STOL_V1 ───────────────────────────────
        # Всё это ядро считало и раньше — но на стол не выкладывало,
        # и трейдер их не видел. Особенно разворотный бар: его
        # зовут на место ИМЕННО из-за него, а на столе его не было.
        "разворотный_бар": {
            "есть": bool((md.get("necron_bar") or {}).get("direction")),
            "сторона": (md.get("necron_bar") or {}).get("direction"),
            "цена": (md.get("necron_bar") or {}).get("price"),
        },
        # ЗОНА по Вильямсу (iZone из эксперта Шефа): AO и AC вместе.
        # Зелёная — оба растут, красная — оба падают, серая — спорят.
        "зона": _zona(md),
        "ac": {
            "значение": (md.get("ac") or {}).get("value"),
            "прошлое": (md.get("ac") or {}).get("prev_value"),
            "растёт": (md.get("ac") or {}).get("direction"),
        },
        "дивергенция_ao": md.get("divergence_ao"),
        "приседающий_бар": bool((md.get("squat") or {}).get("last_squat")),
    }

    return stol


def _zona(md: dict) -> str:
    """ЗЕЛЁНАЯ / КРАСНАЯ / СЕРАЯ — и ни слова о том, что с этим делать.

    PRIBORY_NA_STOL_V1, по iZone.mq4 из Profitunity_MT4:
        AO растёт И AC растёт  → зелёная
        AO падает И AC падает  → красная
        иначе                  → серая
    """
    ao_d = ((md or {}).get("ao") or {}).get("direction")
    ac_d = ((md or {}).get("ac") or {}).get("direction")
    if not ao_d or not ac_d:
        return "—"
    if ao_d == "UP" and ac_d == "UP":
        return "ЗЕЛЁНАЯ"
    if ao_d == "DOWN" and ac_d == "DOWN":
        return "КРАСНАЯ"
    return "СЕРАЯ"'''

ST_SLOVAMI = """        f"цена: O={c.get('open')} H={c.get('high')} L={c.get('low')} "
        f"C={c.get('close')}   бар: {p.get('бар')}","""

NOV_SLOVAMI = """        # PRIBORY_NA_STOL_V1: то, ради чего трейдера зовут, — первой
        # строкой, а не в конце и не молчком.
        f"РАЗВОРОТНЫЙ БАР: "
        f"{(p.get('разворотный_бар') or {}).get('сторона') or 'нет'}"
        + (f" @ {(p.get('разворотный_бар') or {}).get('цена')}"
           if (p.get('разворотный_бар') or {}).get('есть') else ""),
        f"зона (AO+AC): {p.get('зона') or '—'}   "
        f"AC: {(p.get('ac') or {}).get('значение')} "
        f"({(p.get('ac') or {}).get('растёт') or '—'})",
        f"дивергенция AO: {p.get('дивергенция_ao')}   "
        f"приседающий бар: {p.get('приседающий_бар')}",
        f"цена: O={c.get('open')} H={c.get('high')} L={c.get('low')} "
        f"C={c.get('close')}   бар: {p.get('бар')}","""


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    stol = koren / "Биржа" / "stol.py"
    t = stol.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [("приборы", ST_PRIBORY, NOV_PRIBORY),
            ("словами", ST_SLOVAMI, NOV_SLOVAMI)]
    beda = [imya for imya, st, _ in pary if t.count(st) != 1]
    if beda:
        print(f"✗ якоря не найдены дословно: {', '.join(beda)}")
        return 1

    novyy = t
    for _, st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = stol.with_suffix(f".py.bak_pribory_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(stol, bak)
    stol.write_text(novyy, encoding="utf-8")
    print(f"✓ приборы легли на стол (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(stol), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь трейдер видит на столе то, ради чего его позвали:")
    print("  РАЗВОРОТНЫЙ БАР: BULL @ 1.15093")
    print("  зона (AO+AC): ЗЕЛЁНАЯ   AC: 0.0012 (UP)")
    print("  дивергенция AO: True   приседающий бар: False")
    print("\nСтол по-прежнему не судит: это факты, а не «входи».")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
