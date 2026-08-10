# -*- coding: utf-8 -*-
# LOKACIYA_DAYOT_MESTA_V1
"""
ВАКАНСИЮ ДАЁТ ЛОКАЦИЯ.

    python patch_lokaciya_daet_mesta.py --suho    посмотреть
    python patch_lokaciya_daet_mesta.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копии рядом: .bak_lokaciya.
Ложится поверх стандарта и Страницы Работы.

ЧТО БЫЛО НЕ ТАК

    Я считал места от цехов: обошёл манифесты — получил слоты. Здания
    при этом были ни при чём, а посты вроде ректора висели сами по
    себе, ничьи.

    Слово Шефа: вакансию обеспечивает ЛОКАЦИЯ. Маяк, Архив, Замок
    Совы, Биржа. Нет локации — нет и вакансии.

СТАНОВИТСЯ

    Считаем от локаций. У каждой два источника мест:

      1. КАРТРИДЖ, который в ней стоит. В манифесте цеха уже написано
         здание (у торгового хаоса — 0014_EXCHANGE) и квартал. Слоты
         этого цеха и есть вакансии здания. Нет картриджа — этих мест
         нет.

      2. СВОИ МЕСТА локации, без всякого картриджа — ректор, хранитель,
         библиотекарь. Так решил Шеф: локация может давать места и
         сама.

    Локация без того и другого честно стоит пустой: «вакансий не
    предлагает». Появился картридж — места появились сами, ничего
    заводить руками не надо.

    Поле «где» в бланке перестаёт быть текстом. У слотового места оно
    приходит из здания картриджа и руками не правится. У своего места
    локации — выбирается из списка локаций города.

СШИВКА СТАРОГО

    Три трейдерских поста несут «где: Биржа · торговый квартал» —
    словами, а не адресом. Меняю на 0014_EXCHANGE, чтобы Биржа их
    видела. Хранитель архива стоит без здания вовсе — привязываю к
    Архиву. Что не опознаю — оставлю как есть и покажу в списке
    «без локации», чтобы ты сам решил.
"""
import argparse
import ast
import json
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
GOROD = KOREN / "ГОРОД"
RABOTA = GOROD / "rabota.py"
STRANICA = GOROD / "ui_rabota.py"
CITY = KOREN / "GRONDHEIM_CITY"
MARKER = "# LOKACIYA_DAYOT_MESTA_V1 - marker"
BAK = ".bak_lokaciya"

# ── 1. сканер: считаем от локаций ─────────────────────────────
STAROE_SKANER = '''def _mesta_novogo_goroda() -> list:
    out = []
    if not CITY.exists():
        return out
    for kv in sorted(CITY.iterdir()):
        ceha = kv / "цеха"
        if not ceha.is_dir():
            continue
        for cd in sorted(ceha.iterdir()):
            mf = cd / "manifest.json"
            if not mf.exists():
                continue
            m = _chitat(mf) or {}
            for s in m.get("слоты", []) or []:
                slot = s.get("слот")
                if slot:
                    out.append({"квартал": kv.name, "цех": cd.name,
                                "слот": slot, "роль": s.get("роль", ""),
                                "откуда": "город"})
    return out
'''

NOVOE_SKANER = '''LOKACII = CITY / "локации"


def lokacii() -> dict:
    """Локации города: id → имя. Списков не держим — читаем папку."""
    out = {}
    if not LOKACII.exists():
        return out
    for d in sorted(LOKACII.iterdir()):
        p = _chitat(d / "passport.json")
        if p is None and not d.is_dir():
            continue
        out[d.name] = (p or {}).get("Official_Name", d.name)
    return out


def kartridzhi() -> list:
    """Картриджи города с их зданием. LOKACIYA_DAYOT_MESTA_V1: манифест
    цеха сам говорит, в каком здании стоит — привязка уже была, просто
    записана со стороны цеха."""
    out = []
    if not CITY.exists():
        return out
    for kv in sorted(CITY.iterdir()):
        ceha = kv / "цеха"
        if not ceha.is_dir():
            continue
        for cd in sorted(ceha.iterdir()):
            mf = cd / "manifest.json"
            if not mf.exists():
                continue
            m = _chitat(mf) or {}
            out.append({"цех": cd.name, "папка_квартала": kv.name,
                        "здание": m.get("здание", ""),
                        "квартал": m.get("квартал", ""),
                        "слоты": m.get("слоты", []) or []})
    return out


def _mesta_novogo_goroda() -> list:
    """Слоты картриджей — вакансии тех ЗДАНИЙ, где картриджи стоят."""
    out = []
    for k in kartridzhi():
        for s in k["слоты"]:
            slot = s.get("слот")
            if slot:
                out.append({"локация": k["здание"] or k["квартал"],
                            "квартал": k["папка_квартала"], "цех": k["цех"],
                            "слот": slot, "роль": s.get("роль", ""),
                            "откуда": "картридж"})
    return out
'''

# ── 2. mesta(): локация у каждого места ───────────────────────
STAROE_MESTA = '''            out.append({
                "id": p.get("id", d.name),
                "название": p.get("название", d.name),
                "квартал": p.get("квартал", ""),
                "цех": p.get("цех", ""),
                "слот": p.get("слот", ""),
                "кто_сидит": ((p.get("кто_сидит") or {}).get("имя") or ""),
                "есть_пост": True,
                "откуда": "пост",
            })
'''
NOVOE_MESTA = '''            out.append({
                "id": p.get("id", d.name),
                "название": p.get("название", d.name),
                # LOKACIYA_DAYOT_MESTA_V1: место всегда чьё-то. Пусто —
                # значит осиротело, и это надо видеть, а не прятать.
                "локация": p.get("локация") or p.get("где", ""),
                "квартал": p.get("квартал", ""),
                "цех": p.get("цех", ""),
                "слот": p.get("слот", ""),
                "кто_сидит": ((p.get("кто_сидит") or {}).get("имя") or ""),
                "есть_пост": True,
                "откуда": "пост",
            })
'''

STAROE_MESTA2 = '''        out.append({
            "id": pid,
            "название": m.get("роль") or f'{m["цех"]} · {m["слот"]}',
            "квартал": m["квартал"], "цех": m["цех"], "слот": m["слот"],
            "кто_сидит": "", "есть_пост": False, "откуда": m["откуда"],
        })
    return out
'''
NOVOE_MESTA2 = '''        out.append({
            "id": pid,
            "название": m.get("роль") or f'{m["цех"]} · {m["слот"]}',
            "локация": m.get("локация", ""),
            "квартал": m["квартал"], "цех": m["цех"], "слот": m["слот"],
            "кто_сидит": "", "есть_пост": False, "откуда": m["откуда"],
        })
    return out


def po_lokaciyam() -> list:
    """Город глазами локаций: что каждая предлагает.

    LOKACIYA_DAYOT_MESTA_V1: считаем ОТ ЗДАНИЙ. У локации два источника
    мест — картридж, который в ней стоит, и её собственные места
    (ректор, хранитель — без всякого картриджа, так решил Шеф).
    Пусто и там и там — локация честно ничего не предлагает.
    """
    loc = lokacii()
    vse = mesta()
    itog = []
    for lid, imya in loc.items():
        moi = [m for m in vse if (m.get("локация") or "") == lid]
        itog.append({"id": lid, "название": imya, "места": moi,
                     "занято": sum(1 for m in moi if m["кто_сидит"]),
                     "свободно": sum(1 for m in moi if m["есть_пост"]
                                     and not m["кто_сидит"])})
    siroty = [m for m in vse if (m.get("локация") or "") not in loc]
    if siroty:
        itog.append({"id": "", "название": "— без локации —",
                     "места": siroty,
                     "занято": sum(1 for m in siroty if m["кто_сидит"]),
                     "свободно": sum(1 for m in siroty if m["есть_пост"]
                                     and not m["кто_сидит"])})
    return itog
'''

# ── 3. бланк знает про локацию ────────────────────────────────
STAROE_POLYA = '''POLYA_BLANKA = ("название", "где", "квартал", "цех", "слот", "чем_занят",
                "обязанности", "судья", "требования", "условия", "движок")
'''
NOVOE_POLYA = '''POLYA_BLANKA = ("название", "локация", "где", "квартал", "цех", "слот",
                "чем_занят", "обязанности", "судья", "требования",
                "условия", "движок")
'''

STAROE_BLANK = '''        "название": "",
        "где": "",
'''
NOVOE_BLANK = '''        "название": "",
        # LOKACIYA_DAYOT_MESTA_V1: место даёт локация, и она у места одна.
        "локация": "",
        "где": "",
'''

RABOTA_STEZHKI = (
    ("поля бланка", STAROE_POLYA, NOVOE_POLYA),
    ("локация в бланке", STAROE_BLANK, NOVOE_BLANK),
    ("сканер от локаций", STAROE_SKANER, NOVOE_SKANER),
    ("локация у поста", STAROE_MESTA, NOVOE_MESTA),
    ("локация у слота + взгляд по локациям", STAROE_MESTA2, NOVOE_MESTA2),
)

# ── 4. страница: дерево от локаций ────────────────────────────
STAROE_DEREVO = '''        po_kvartalam: dict = {}
        for m in v:
            po_kvartalam.setdefault(m["квартал"] or "(без квартала)",
                                    {}).setdefault(m["цех"] or "(город)",
                                                   []).append(m)
        with refs["derevo"]:
            for kv in sorted(po_kvartalam):
                ceha = po_kvartalam[kv]
                vsego = sum(len(x) for x in ceha.values())
                # свёрнуто по умолчанию — иначе сотня мест не листается
                with ui.expansion(f"{kv}  ·  {vsego}",
                                  value=bool(sost["poisk"])).style(
                        "width:100%; font-size:0.8rem;"):
                    for ceh in sorted(ceha):
                        ui.html(f'<div class="rab-podpis">{ceh}</div>')
                        for m in sorted(ceha[ceh], key=lambda x: x["слот"]):
'''
NOVOE_DEREVO = '''        # LOKACIYA_DAYOT_MESTA_V1: дерево идёт ОТ ЛОКАЦИЙ. Локация →
        # картридж, который в ней стоит → место. Свои места локации
        # (ректор, хранитель) лежат там же, под пометкой «без цеха».
        vidno = {m["id"] for m in v}
        with refs["derevo"]:
            for L in R.po_lokaciyam():
                moi = [m for m in L["места"] if m["id"] in vidno]
                if not moi and sost["poisk"]:
                    continue
                if not moi:
                    ui.html(f'<div class="rab-podpis">{L["название"]} '
                            f'— вакансий не предлагает</div>')
                    continue
                ceha: dict = {}
                for m in moi:
                    ceha.setdefault(m["цех"] or "(места локации)", []).append(m)
                with ui.expansion(
                        f'{L["название"]}  ·  {len(moi)}'
                        f'  (занято {L["занято"]})',
                        value=bool(sost["poisk"])).style(
                        "width:100%; font-size:0.8rem;"):
                    for ceh in sorted(ceha):
                        ui.html(f'<div class="rab-podpis">{ceh}</div>')
                        for m in sorted(ceha[ceh], key=lambda x: x["слот"]):
'''

# ── 5. карточка: локация вместо текстового «где» ──────────────
STAROE_POLYA_UI = '''POLYA = [
    ("название", "Название должности"),
    ("где", "Где (локация — привяжем позже)"),
    ("квартал", "Квартал"),
'''
NOVOE_POLYA_UI = '''POLYA = [
    ("название", "Название должности"),
    ("квартал", "Квартал"),
'''

STAROE_KARTA = '''            polya_ui = {}
'''
NOVOE_KARTA = '''            # LOKACIYA_DAYOT_MESTA_V1: локация первой строкой. У места
            # от картриджа она приходит из здания цеха и не правится —
            # иначе руками разведём здание и картридж.
            loc = R.lokacii()
            m_loc = post.get("локация") or m.get("локация") or ""
            ot_kartridzha = bool(m.get("цех"))
            ui.html('<div class="rab-podpis">локация — она и даёт это место</div>')
            if ot_kartridzha:
                ui.label(f'{loc.get(m_loc, m_loc or "— здание не указано —")}'
                         f'   ·   из картриджа {m.get("цех")}').style(
                    "color:rgba(139,233,253,0.8); font-size:0.8rem; "
                    "margin-bottom:8px;")
                sel_loc = None
            else:
                _opts = {"": "— не выбрана —"}
                _opts.update(loc)
                sel_loc = ui.select(_opts, value=m_loc if m_loc in loc else "").props(
                    "dark dense outlined").style(
                    "width:100%; font-size:0.78rem; margin-bottom:8px;")

            polya_ui = {}
'''

STAROE_SOBRAT = '''            def _sobrat() -> dict:
                d = {k: (polya_ui[k].value or "").strip() for k, _ in POLYA}
'''
NOVOE_SOBRAT = '''            def _sobrat() -> dict:
                d = {k: (polya_ui[k].value or "").strip() for k, _ in POLYA}
                d["локация"] = (m_loc if sel_loc is None
                                else (sel_loc.value or "").strip())
'''

STRANICA_STEZHKI = (
    ("поля карточки", STAROE_POLYA_UI, NOVOE_POLYA_UI),
    ("локация в карточке", STAROE_KARTA, NOVOE_KARTA),
    ("локация в бланке при сохранении", STAROE_SOBRAT, NOVOE_SOBRAT),
    ("дерево от локаций", STAROE_DEREVO, NOVOE_DEREVO),
)

# ── 6. сшивка старых постов с локациями ───────────────────────
SSHIVKA_LOK = {
    "treyder_proboy": "0014_EXCHANGE",
    "treyder_ranniy": "0014_EXCHANGE",
    "treyder_otkat": "0014_EXCHANGE",
    "bibliotekar": "0008_OWL_CASTLE",
    "rektor": "0008_OWL_CASTLE",
    "khranitel_mayaka": "0005_LIGHTHOUSE_AWAKENING",
    "khranitel_arkhiva": "0015_GRONDHEIM_ARCHIVE",
}


def sshit(suho: bool):
    posty = CITY / "посты"
    if not posty.exists():
        print("  постов нет")
        return
    est = {d.name for d in (CITY / "локации").iterdir()} if (
        CITY / "локации").exists() else set()
    for d in sorted(posty.iterdir()):
        f = d / "пост.json"
        if not f.exists():
            continue
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            print(f"  ✗ {d.name}: не читается")
            continue
        if p.get("локация") in est:
            print(f"  {d.name}: уже при локации")
            continue
        lid = SSHIVKA_LOK.get(d.name, "")
        if lid not in est:
            gde = (p.get("где") or "").strip()
            lid = gde if gde in est else ""
        if not lid:
            print(f"  ⚠ {d.name}: локацию не опознал — покажу «без локации»")
            continue
        p["локация"] = lid
        if suho:
            print(f"  {d.name}: ✓ привяжется к {lid}")
            continue
        f.write_text(json.dumps(p, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print(f"  {d.name}: ✓ привязан к {lid}")


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def pravit(put: Path, stezhki, suho: bool) -> bool:
    if not put.exists():
        print(f"  ✗ нет {put.name} — сперва поставь стандарт и страницу")
        return False
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {put.name}: уже накатано")
        return True
    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  ✗ {put.name}: якорь «{nazv}» найден {n} раз — не трогаю")
            return False
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv} — заменено")
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, put.name):
        return False
    if suho:
        print(f"  {put.name}: ✓ готов")
        return True
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {put.name}: ✓ накатано")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("═" * 62)
    print("ЛОКАЦИЯ ДАЁТ МЕСТА" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 62)

    ok = True
    print("\nмеханизм:")
    ok &= pravit(RABOTA, RABOTA_STEZHKI, a.suho)
    print("\nстраница:")
    ok &= pravit(STRANICA, STRANICA_STEZHKI, a.suho)
    print("\nсшивка постов с локациями:")
    sshit(a.suho)

    if not ok:
        print("\n⚠ что-то не легло — дальше не иду")
        return 1
    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_lokaciya_daet_mesta.py")
        return 0
    print("\n" + "─" * 62)
    print("Открой /rabota: слева теперь ЛОКАЦИИ. Внутри каждой —")
    print("картриджи, которые в ней стоят, и её собственные места.")
    print("Пустая локация так и написана: вакансий не предлагает.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
