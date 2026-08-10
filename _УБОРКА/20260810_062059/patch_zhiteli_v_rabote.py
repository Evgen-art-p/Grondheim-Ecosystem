# -*- coding: utf-8 -*-
# ZHITELI_V_RABOTE_V1
"""
ЖИТЕЛИ — В ТУ ЖЕ ДВЕРЬ. Тип и коронная фраза переезжают на Страницу Работы.

    python patch_zhiteli_v_rabote.py --suho    посмотреть
    python patch_zhiteli_v_rabote.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_zhiteli.

ЗАЧЕМ

    Кнопку «Роль» мы убрали, и вместе с ней стало неоткуда ставить тип
    жителя и коронную фразу. Ты сказал — впихнуть в «Работу». Впихиваю.

ЧТО ПОЯВЛЯЕТСЯ

    Наверху страницы переключатель: МЕСТА | ЖИТЕЛИ.

    МЕСТА — всё как было: локации, картриджи, вакансии, приём и
    увольнение.

    ЖИТЕЛИ — список всех, поиск тот же. Выбрал человека — справа его
    карточка: кто он (резидент, хранитель, воркер, студент), коронная
    фраза, и строкой — где он сейчас работает, если работает.

    Двух дверей больше нет: одна кнопка, две стороны одного дела —
    люди и места.

ЧЕГО ПАТЧ НЕ ТРОГАЕТ
    Механизм постов, локации, приём и увольнение. Только страница.
    Тип пишется туда же, куда писала «Роль» — в паспорт; фраза — в
    маску работы. Ничего нового на диске не заводится.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
STRANICA = KOREN / "ГОРОД" / "ui_rabota.py"
MARKER = "# ZHITELI_V_RABOTE_V1 - marker"
BAK = ".bak_zhiteli"

# ── 1. помощники: паспорт и маска ─────────────────────────────
STAROE_HELP = '''def page_rabota():
'''
NOVOE_HELP = '''# ZHITELI_V_RABOTE_V1: тип и фраза живут там же, где жили при «Роли» —
# тип в паспорте, фраза в маске работы. Новых тетрадей не заводим.
TIPY = ["резидент", "хранитель", "воркер", "студент"]


def _pasport(imya: str):
    dom = R.dom_zhitelya(imya)
    if dom is None:
        return None, None
    p = dom / "passport.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")), dom
    except Exception:
        return None, dom


def _maska(dom: Path) -> dict:
    try:
        return json.loads((dom / "маски" / "работа" / "mask.json").read_text(
            encoding="utf-8"))
    except Exception:
        return {}


def _sohranit_zhitelya(imya: str, tip: str, fraza: str) -> tuple:
    p, dom = _pasport(imya)
    if p is None or dom is None:
        return False, "жителя не нашёл"
    try:
        if tip:
            p["тип"] = tip
        (dom / "passport.json").write_text(
            json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
        mp = dom / "маски" / "работа" / "mask.json"
        mp.parent.mkdir(parents=True, exist_ok=True)
        m = _maska(dom)
        m["_активна"] = True
        m["Core_Phrase"] = fraza
        mp.write_text(json.dumps(m, ensure_ascii=False, indent=2),
                      encoding="utf-8")
        return True, "записано"
    except Exception as e:
        return False, str(e)


def page_rabota():
'''

# ── 2. состояние: режим ───────────────────────────────────────
STAROE_SOST = '''    sost: dict[str, Any] = {"vybrano": None, "poisk": "", "filtr": "все"}
'''
NOVOE_SOST = '''    sost: dict[str, Any] = {"vybrano": None, "poisk": "", "filtr": "все",
                            "rezhim": "места", "zhitel": None}
'''

# ── 3. переключатель в шапке ──────────────────────────────────
STAROE_SHAPKA = '''        refs["schet"] = ui.html("")
        ui.element("div").style("flex:1")
'''
NOVOE_SHAPKA = '''        refs["schet"] = ui.html("")
        # ZHITELI_V_RABOTE_V1: одна дверь, две стороны дела.
        with ui.row().style("gap:4px; margin-left:10px;"):
            for _r in ("места", "жители"):
                def _rezhim(r=_r):
                    sost["rezhim"] = r
                    sost["vybrano"] = None
                    sost["zhitel"] = None
                    risovat_derevo()
                    risovat_kartu()
                ui.button(_r.upper(), on_click=_rezhim).props(
                    "flat no-caps").style(
                    "font-size:0.7rem; padding:3px 12px; border-radius:12px; "
                    "color:rgba(139,233,253,0.9); "
                    "background:rgba(139,233,253,0.10);")
        ui.element("div").style("flex:1")
'''

# ── 4. левая колонка: жители вместо дерева ────────────────────
STAROE_DEREVO = '''    def risovat_derevo():
        obnovit_schet()
        refs["derevo"].clear()
'''
NOVOE_DEREVO = '''    def risovat_zhiteley():
        """Список жителей города. Тот же поиск, что и по местам."""
        refs["derevo"].clear()
        gde = {}
        for m in R.mesta():
            if m["кто_сидит"]:
                gde[m["кто_сидит"]] = m["название"]
        q = sost["poisk"]
        with refs["derevo"]:
            imena = [i for i in _zhiteli() if not q or q in i.lower()]
            if not imena:
                ui.label("никого не нашлось").style(
                    "color:rgba(255,255,255,0.35); font-size:0.78rem;")
                return
            for imya in imena:
                rabota = gde.get(imya, "")
                hvost = rabota or "— без места —"
                cvet = ("rgba(80,250,123,0.85)" if rabota
                        else "rgba(255,255,255,0.5)")

                def _vyb(imya=imya):
                    sost["zhitel"] = imya
                    risovat_kartu()

                ui.button(f"{imya:<16} {hvost}", on_click=_vyb).props(
                    "flat no-caps").style(
                    f"width:100%; text-align:left; font-family:monospace; "
                    f"font-size:0.74rem; color:{cvet}; padding:5px 10px; "
                    f"border-radius:8px; background:rgba(255,255,255,0.04); "
                    f"margin-bottom:3px;")

    def risovat_derevo():
        obnovit_schet()
        if sost["rezhim"] == "жители":
            risovat_zhiteley()
            return
        refs["derevo"].clear()
'''

# ── 5. правая колонка: карточка жителя ────────────────────────
STAROE_KARTA = '''    def risovat_kartu():
        refs["karta"].clear()
        m = sost["vybrano"]
'''
NOVOE_KARTA = '''    def risovat_kartu_zhitelya():
        refs["karta"].clear()
        imya = sost["zhitel"]
        with refs["karta"]:
            if imya is None:
                ui.label("Выбери человека слева.").style(
                    "color:rgba(255,255,255,0.4); font-size:0.82rem;")
                return
            p, dom = _pasport(imya)
            if p is None:
                ui.label(f"Паспорт {imya} не читается.").style(
                    "color:rgba(255,180,60,0.85); font-size:0.8rem;")
                return
            maska = _maska(dom)
            ui.html(f'<div style="font-weight:800; font-size:0.92rem; '
                    f'letter-spacing:0.06em; margin-bottom:2px;">{imya}</div>'
                    f'<div style="color:rgba(255,255,255,0.35); '
                    f'font-size:0.68rem; font-family:monospace; '
                    f'margin-bottom:12px;">{p.get("ID_Object","")}</div>')

            rab = p.get("Работа") or {}
            if rab:
                ui.label(f'Работает: {rab.get("должность","")} · '
                         f'{rab.get("где","")}').style(
                    "color:rgba(80,250,123,0.8); font-size:0.78rem; "
                    "margin-bottom:8px;")
            else:
                ui.label("Места пока нет — посадить можно во вкладке МЕСТА.").style(
                    "color:rgba(255,255,255,0.4); font-size:0.78rem; "
                    "margin-bottom:8px;")

            _tek = p.get("тип") or ""
            sel = ui.select({t: t for t in TIPY},
                            value=_tek if _tek in TIPY else None,
                            label="Кто он").props("dark dense outlined").style(
                "width:100%; font-size:0.78rem; margin-bottom:6px;")
            fr = ui.input("Коронная фраза",
                          value=maska.get("Core_Phrase", "")).props(
                "dark dense outlined").style(
                "width:100%; font-size:0.78rem;")

            def _sohr():
                ok, msg = _sohranit_zhitelya(imya, (sel.value or "").strip(),
                                             (fr.value or "").strip())
                ui.notify(("🪑 " if ok else "⚠ ") + msg,
                          color="positive" if ok else "negative")
                risovat_derevo()
                risovat_kartu()

            ui.button("сохранить", on_click=_sohr).props(
                "flat no-caps").style(
                "margin-top:12px; padding:7px 18px; border-radius:8px; "
                "font-weight:700; font-size:0.78rem; color:#fff; "
                "background:linear-gradient(135deg,rgba(120,168,201,0.30),"
                "rgba(120,168,201,0.18)); "
                "border:1px solid rgba(120,168,201,0.55);")

    def risovat_kartu():
        if sost["rezhim"] == "жители":
            risovat_kartu_zhitelya()
            return
        refs["karta"].clear()
        m = sost["vybrano"]
'''

STEZHKI = (
    ("помощники по жителям", STAROE_HELP, NOVOE_HELP),
    ("режим в состоянии", STAROE_SOST, NOVOE_SOST),
    ("переключатель в шапке", STAROE_SHAPKA, NOVOE_SHAPKA),
    ("список жителей слева", STAROE_DEREVO, NOVOE_DEREVO),
    ("карточка жителя справа", STAROE_KARTA, NOVOE_KARTA),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("=" * 58)
    print("ЖИТЕЛИ В РАБОТЕ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("=" * 58)

    if not STRANICA.exists():
        print("x нет ГОРОД/ui_rabota.py — сперва поставь страницу")
        return 1

    tekst = STRANICA.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x якорь «{nazv}» найден {n} раз — файл не трогаю")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_rabota.py"):
        return 1

    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_zhiteli_v_rabote.py")
        return 0

    shutil.copy2(STRANICA, STRANICA.with_suffix(STRANICA.suffix + BAK))
    STRANICA.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_rabota.py{BAK})")
    print("\nНаверху страницы: МЕСТА | ЖИТЕЛИ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
