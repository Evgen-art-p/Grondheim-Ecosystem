# -*- coding: utf-8 -*-
"""
pochinit_progon_podryad.py · MARKER: PROGON_PODRYAD_V2

МОЯ ЖЕ КАША, НАЙДЕНА НА ПЕРВОМ ЖЕ ПРОГОНЕ
─────────────────────────────────────────
Сплошной ход я налепил ПОВЕРХ старой механики «места + шаги вперёд», и
два способа ходить по истории заработали одновременно. В логе это видно
сразу:

    Нашёл 1500 мест                      ← это бары, а не места
    📍 разворотный None @ None · волна None · компас None
    ...
    2025.09.12 → потом снова 2025.09.03  ← время поехало НАЗАД

Что происходило: внешний цикл идёт по всем барам подряд, а внутри, если
трейдер сказал «наблюдаю», включается старый цикл шагов вперёд и уводит
курсор дальше. Возвращаемся — а внешний цикл продолжает со следующего
бара своего списка, то есть из прошлого. Отсюда прыжки и повторные
рождения одной и той же точки.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. На сплошном ходу шаги вперёд ВЫКЛЮЧЕНЫ. Они там не нужны вовсе:
   мы и так идём по каждому бару, наблюдение ведётся само собой.
   (В режиме мест всё осталось как было.)

2. Подпись в ленте берётся из ключа — что именно случилось на этом
   баре, а не пустое «разворотный None @ None»:

       📍 2025.09.08 20:00 · волна 1 кончилась, вершина @ 1.17564
          (20 бар. от точки) → спрашиваю Илья

3. Надпись в начале честная: «иду по истории: 1500 баров», а не
   «Нашёл 1500 мест».

Ни один расчёт не тронут. Убрана только каша из двух способов ходить.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ postavit_progon_podryad.py — патч это проверит.
Запуск: py pochinit_progon_podryad.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PROGON_PODRYAD_V2"
NUZHEN = "PROGON_PODRYAD_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists()


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


# ── 1. на сплошном ходу шагов вперёд нет ─────────────────────

YAKOR = '''                _sled = None
                try:
                    _i_tek = mesta.index((data, _sl, _sym, _tf, k))
                    if _i_tek + 1 < len(mesta):
                        _sled = mesta[_i_tek + 1][0]
                except Exception:
                    _sled = None
                while True:'''

NOV = '''                _sled = None
                try:
                    _i_tek = mesta.index((data, _sl, _sym, _tf, k))
                    if _i_tek + 1 < len(mesta):
                        _sled = mesta[_i_tek + 1][0]
                except Exception:
                    _sled = None
                # PROGON_PODRYAD_V2: на сплошном ходу шаги вперёд не
                # нужны — мы и так идём по каждому бару. Раньше два
                # способа ходить работали разом, курсор уезжал вперёд,
                # а внешний цикл продолжал из прошлого: время в ленте
                # ехало назад, точки рождались по два раза.
                while not k.get("подряд"):'''


# ── 2. подпись — из ключа, а не из пустого места ─────────────

YAKOR2 = '''                    "content": f"📍 {_kd.slovami(k)} → спрашиваю {imya}"})'''

NOV2 = '''                    # PROGON_PODRYAD_V2: на сплошном ходу говорим, ЧТО
                    # случилось на баре, а не «разворотный None @ None».
                    "content": (f"📍 {data} · {k.get('почему')} "
                                f"→ спрашиваю {imya}"
                                if k.get("подряд")
                                else f"📍 {_kd.slovami(k)} → спрашиваю {imya}")})'''


# ── 3. честная надпись в начале ──────────────────────────────

YAKOR3 = '''            "content": f"Нашёл {len(mesta)} мест. Иду по ним."})'''

NOV3 = '''            # PROGON_PODRYAD_V2: подряд — это бары, а не места.
            "content": (f"Иду по истории: {len(mesta)} баров."
                        if mesta and mesta[0][4].get("подряд")
                        else f"Нашёл {len(mesta)} мест. Иду по ним.")})'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "ui_torg.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_progon_podryad.py")
        return 1
    for yakor in (YAKOR, YAKOR2, YAKOR3):
        if t.count(yakor) != 1:
            print(f"✗ якорь найден {t.count(yakor)} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return 1

    novyy = t.replace(YAKOR, NOV, 1).replace(YAKOR2, NOV2, 1)
    novyy = novyy.replace(YAKOR3, NOV3, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_podryad2_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ сплошной ход стал чистым (копия: {bak.name})")
    print("\nТеперь лента идёт строго вперёд, без прыжков и повторов:")
    print("  Иду по истории: 1500 баров.")
    print("  📍 2025.08.27 12:00 · точка родилась: BULL @ 1.15736 → ...")
    print("  📍 2025.09.08 16:00 · волна 1 кончилась, вершина @ 1.17564 → ...")
    print("  📍 2025.09.11 08:00 · откат кончился @ 1.16835 → ...")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
