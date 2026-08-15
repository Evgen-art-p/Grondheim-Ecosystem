# -*- coding: utf-8 -*-
"""
postavit_vypusk.py · MARKER: VYPUSK_V1

ЧТО БЫЛО НЕ ТАК
───────────────
Выпуска в Академии не было. `vydat_diplom` вписывал профессию и менял
статус на «выпускник» — и всё: запись оставалась, МЕСТО ОСТАВАЛОСЬ
ЗАНЯТЫМ.

Живой реестр на сегодня — все десять мест заняты, и среди них Нина:
выпускница с дипломом трейдера, работает на Бирже, а парта в Академии
за ней держится. Зачислить нового нельзя вообще: Академия забита
теми, кто уже отучился.

Отчисление же (`otchislit`) наоборот — стирало запись целиком, вместе
со всей историей учёбы.

И зачисляли ДВЕ разные двери в один файл, по-разному:
    Ректор  — полную запись (статус, дисциплины, оценки, диплом);
    Брат    — куцую (место, житель, курс) и больше ничего.
Отсюда разнобой: у половины записей статуса нет вовсе.

ЧТО ДЕЛАЕТ ПАТЧ (по слову Шефа: список выпускников + повторное
поступление)
──────────────────────────────────────────────────────────────────
1. ВЫПУСК СТАЛ ВЫПУСКОМ. Выдал диплом → место освобождается, запись
   уезжает в `GRONDHEIM_CITY/Академия/выпускники.json` целиком, со
   всей историей учёбы. Академия помнит, кого выпустила; парта
   свободна.

2. ДИПЛОМ ЖИВЁТ ПРИ ЖИТЕЛЕ. Отметка ложится в паспорт («Диплом»:
   профессия, когда, откуда). Правда о человеке — при человеке, а не
   в списке чужих парт. Метка в память как писалась, так и пишется.

3. ПОВТОРНОЕ ПОСТУПЛЕНИЕ. Место свободно — выпускник поступает снова,
   как все. При зачислении Ректор видит, что диплом уже есть, и в
   записи стоит, какая это по счёту учёба.

4. ДВЕРЬ ЗАЧИСЛЕНИЯ ОДНА. Страница Работы (тип «студент») теперь
   зовёт `rektor.zachislit`, а не пишет свой куцый формат. Тип и
   маску она пишет как писала — это её дело; место — дело Ректора.

5. Старые куцые записи дополняются недостающими полями (статус,
   дисциплины, оценки, экзамены, диплом). Ничего не стирается — только
   дописывается то, чего не хватало.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_vypusk.py   (или --suho)
"""
import ast
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VYPUSK_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Академия" / "rektor.py").exists()
            and (p / "ГОРОД" / "ui_rabota.py").exists()
            and (p / "main.py").exists())


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


# ═══════════════════════════════════════════════════════════
# 1. rektor.py — выпуск, выпускники, повторное поступление
# ═══════════════════════════════════════════════════════════
ST_DIPLOM = '''def vydat_diplom(imya: str, professiya: str = "") -> tuple:
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z["диплом"] = {"профессия": professiya, "выдан": _now()}
            z["статус"] = "выпускник"
            _sokhranit_zapisi(zapisi)'''

NOV_DIPLOM = '''# ── VYPUSK_V1: выпускники и повторное поступление ────────────
VYPUSKNIKI = _UCHENIKI.parent / "выпускники.json"


def vypuskniki() -> list:
    """Все, кого Академия выпустила. Парт не занимают."""
    return (_read_json(VYPUSKNIKI, {"выпуски": []}) or {}).get("выпуски", [])


def diplomy(imya: str) -> list:
    """Дипломы этого человека — сколько раз учился и на кого выучился."""
    return [v for v in vypuskniki() if v.get("житель") == imya]


def _zapisat_vypusk(zapis: dict):
    d = _read_json(VYPUSKNIKI, {"выпуски": []}) or {"выпуски": []}
    d.setdefault("выпуски", []).append(zapis)
    _write_json(VYPUSKNIKI, d)


def _otmetit_diplom_v_pasporte(imya: str, professiya: str) -> bool:
    """Диплом — то, что человек НОСИТ С СОБОЙ. В реестре парт ему не
    место: парта про то, кто учится сейчас."""
    try:
        import sys as _s
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo) not in _s.path:
            _s.path.insert(0, str(_repo))
        import rabota as _r
    except Exception:
        try:
            import sys as _s
            _repo = Path(__file__).resolve().parent.parent
            _g = str(_repo / "ГОРОД")
            if _g not in _s.path:
                _s.path.insert(0, _g)
            import rabota as _r
        except Exception:
            return False
    dom = _r.dom_zhitelya(imya)
    if dom is None:
        return False
    pp = dom / "passport.json"
    p = _read_json(pp)
    if p is None:
        return False
    spisok = p.get("Дипломы") or []
    spisok.append({"профессия": professiya or "специалист",
                   "выдан": _now(), "кем": "Академия Грондхейма"})
    p["Дипломы"] = spisok
    return bool(_write_json(pp, p))


def vydat_diplom(imya: str, professiya: str = "") -> tuple:
    """VYPUSK_V1: диплом — это ВЫПУСК, а не отметка поверх парты.

    Раньше здесь ставился статус «выпускник», и место оставалось за
    человеком навсегда: Академия забивалась теми, кто давно отучился,
    и зачислить нового было некуда. Теперь место освобождается, а
    запись со всей историей учёбы уезжает в выпускники.
    """
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z["диплом"] = {"профессия": professiya, "выдан": _now()}
            z["статус"] = "выпускник"
            z["выпущен"] = _now()
            _zapisat_vypusk(dict(z))
            _otmetit_diplom_v_pasporte(imya, professiya)
            zapisi = [x for x in zapisi if x.get("житель") != imya]
            _sokhranit_zapisi(zapisi)'''

ST_DIPLOM_HVOST = '''            return True, f"диплом «{professiya or 'без указания профессии'}» выдан {imya}"
    return False, f"{imya} не студент(ка) — диплом выдавать некому"'''

NOV_DIPLOM_HVOST = '''            _mesto = z.get("место")
            return True, (f"диплом «{professiya or 'без указания профессии'}» "
                          f"выдан {imya} · место {_mesto} свободно · "
                          f"запись ушла в выпускники")
    return False, f"{imya} не студент(ка) — диплом выдавать некому"'''

ST_ZACHISL = '''    if est_studentom(imya):
        return False, f"{imya} уже учится — второй раз не зачисляю"
    mesto = svobodnoe_mesto()'''

NOV_ZACHISL = '''    if est_studentom(imya):
        return False, f"{imya} уже учится — второй раз не зачисляю"
    # VYPUSK_V1: выпускник поступает снова как все — место он больше
    # не занимает. Считаем, какая это по счёту учёба, чтобы Ректор
    # видел человека целиком, а не с чистого листа.
    _proshlye = diplomy(imya)
    mesto = svobodnoe_mesto()'''

ST_ZACHISL_ZAPIS = '''        "статус": "студент", "зачислен": _now(),
        "оценки": [], "экзамены": [], "диплом": None,
    })'''

NOV_ZACHISL_ZAPIS = '''        "статус": "студент", "зачислен": _now(),
        "оценки": [], "экзамены": [], "диплом": None,
        "учёба_по_счёту": len(_proshlye) + 1,          # VYPUSK_V1
        "прошлые_дипломы": [d.get("диплом", {}).get("профессия", "")
                            for d in _proshlye],
    })'''

ST_ZACHISL_ITOG = '''    return True, f"{imya} зачислен(а) на место {mesto}"'''
NOV_ZACHISL_ITOG = '''    if _proshlye:
        _bylo = ", ".join(x for x in
                          (d.get("диплом", {}).get("профессия", "")
                           for d in _proshlye) if x)
        return True, (f"{imya} зачислен(а) на место {mesto} · "
                      f"учёба {len(_proshlye) + 1}-я, уже есть диплом: "
                      f"{_bylo or 'без профессии'}")
    return True, f"{imya} зачислен(а) на место {mesto}"'''


# ═══════════════════════════════════════════════════════════
# 2. Страница Работы — зачисляет через Ректора, а не своей рукой
# ═══════════════════════════════════════════════════════════
ST_RABOTA = '''        import ui_brat
        p, _dom = _pasport(imya)
        if p is None:
            return False, "паспорт не читается"
        zid = p.get("ID_Object", "")
        if not zid:
            return False, "у жителя нет ID"
        # уже сидит — второй раз не сажаем и место не занимаем
        try:
            uzhe = ui_brat._akademia_ucheniki_chitat().get("места", []) or []
            if any((z.get("ID") == zid or z.get("имя") == imya) for z in uzhe):
                return True, "уже числится в Академии"
        except Exception:
            pass
        return ui_brat.zapisat_studenta(zid)'''

NOV_RABOTA = '''        # VYPUSK_V1: зачисляет РЕКТОР — одна дверь. Раньше здесь была
        # своя рука Брата, и она клала куцую запись без статуса,
        # дисциплин и поля под диплом. Оттого в реестре и был разнобой.
        _s.path.insert(0, str(_repo / "Академия"))
        import rektor
        return rektor.zachislit(imya)'''


def pravit(put: Path, pary: list, imya: str) -> bool:
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"  · {put.name}: маркер уже стоит")
        return True
    beda = [st[:44].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден дословно → «{b}…»")
        return False
    novyy = t
    for st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    shutil.copy2(put, put.with_suffix(
        put.suffix + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}"))
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    rektor = koren / "Академия" / "rektor.py"
    rabota = koren / "ГОРОД" / "ui_rabota.py"
    reestr = koren / "GRONDHEIM_CITY" / "Академия" / "ученики.json"

    print("\n1. Ректор: диплом освобождает место, выпускники, повтор")
    if not pravit(rektor, [(ST_DIPLOM, NOV_DIPLOM),
                           (ST_DIPLOM_HVOST, NOV_DIPLOM_HVOST),
                           (ST_ZACHISL, NOV_ZACHISL),
                           (ST_ZACHISL_ZAPIS, NOV_ZACHISL_ZAPIS),
                           (ST_ZACHISL_ITOG, NOV_ZACHISL_ITOG)], "vypusk"):
        return 1

    print("\n2. Страница Работы: зачисление одной дверью — через Ректора")
    if not pravit(rabota, [(ST_RABOTA, NOV_RABOTA)], "vypusk"):
        print("  (если якорь не найден — накати сперва ubrat_rol.py)")
        return 1

    print("\n3. Старые куцые записи — дополняю недостающими полями")
    if not reestr.exists():
        print("  · реестра ещё нет — нечего чинить")
    else:
        try:
            d = json.loads(reestr.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ реестр не читается: {e}")
            return 1
        mesta = d.get("места", []) or []
        tronuto = []
        for z in mesta:
            if not z.get("житель"):
                continue
            nedostaet = []
            for klyuch, pusto in (("статус", "студент"), ("дисциплины", []),
                                  ("оценки", []), ("экзамены", []),
                                  ("диплом", None)):
                if klyuch not in z:
                    z[klyuch] = pusto
                    nedostaet.append(klyuch)
            if nedostaet:
                tronuto.append(f"{z.get('житель')} (+{', '.join(nedostaet)})")
        if not tronuto:
            print("  · все записи полные")
        elif SUHO:
            print(f"  · дополнил бы: {'; '.join(tronuto)}")
        else:
            shutil.copy2(reestr, reestr.with_suffix(
                f".json.bak_vypusk_{datetime.now():%Y%m%d_%H%M%S}"))
            reestr.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                              encoding="utf-8")
            for s in tronuto:
                print(f"  ✓ {s}")

    if not SUHO:
        import py_compile
        for f in (rektor, rabota):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1

        # показать, что теперь в Академии
        try:
            d = json.loads(reestr.read_text(encoding="utf-8"))
            zanyato = [z for z in d.get("места", []) if z.get("житель")]
            vyp = koren / "GRONDHEIM_CITY" / "Академия" / "выпускники.json"
            n_vyp = 0
            if vyp.exists():
                n_vyp = len(json.loads(vyp.read_text(encoding="utf-8"))
                            .get("выпуски", []))
            print(f"\nСейчас в Академии: занято мест {len(zanyato)} из 10 · "
                  f"выпускников {n_vyp}")
            for z in zanyato:
                dip = (z.get("диплом") or {}).get("профессия")
                if dip:
                    print(f"  ⚠ {z.get('житель')} держит место {z.get('место')}, "
                          f"хотя диплом «{dip}» уже выдан — выпусти заново "
                          f"кнопкой «диплом», место освободится")
        except Exception:
            pass

        print("\nКак теперь идёт учёба:")
        print("  зачислить → дисциплины → оценки и экзамены → диплом.")
        print("  Диплом освобождает парту, запись уходит в выпускники,")
        print("  отметка о дипломе ложится жителю в паспорт.")
        print("  Захотел учиться снова — поступает как все, Ректор видит,")
        print("  что это уже вторая учёба и какой диплом был.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
