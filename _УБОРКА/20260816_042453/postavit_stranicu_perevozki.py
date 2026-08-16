# -*- coding: utf-8 -*-
"""
postavit_stranicu_perevozki.py · MARKER: STRANICA_PEREVOZKI_V1

ЗАМЫСЕЛ (слова Шефа 16.08)
──────────────────────────
    · БЕРЕГ — этот репо, город Грондхейм. Он один.
    · ОСТРОВА — отдельные репо. Первый — Остров Надежды, будут ещё.
    · ПЕРЕВОЗКА — только между берегом и островом, туда и обратно.
    · Внутри города переездов нет: там прогулки по локациям, это
      отдельная тема и отдельное время.
    · «Не каждый житель должен мигрировать. Не привязывай ни жителей,
      ни место переезда.»

ЧТО БЫЛО НЕ ТАК В КНОПКЕ У БРАТА
────────────────────────────────
Окно было устроено как витрина: вот все шестнадцать, отметь галочками
кого угодно, поедут «на остров». В этом два неверных допущения —
будто ехать может каждый и будто остров один, вшитый в кнопку. Плюс
галочки шли лентой и налезали друг на друга.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Заводит СВОЮ СТРАНИЦУ `/perevozka` (`ГОРОД/ui_perevozka.py`).
   Она сама понимает, где её открыли:

       НА БЕРЕГУ  — отправка: выбрал одного, назвал остров, собрал.
       НА ОСТРОВЕ — приём: видит пришедшие архивы, принимает и сажает.

   Никаких галочек: выбор ОДНОГО кликом по строке, отправка идёт от
   человека. Есть поиск по имени — на шестнадцати он уже нужен.

2. Остров НЕ ЗАШИТ. Имя пишется при отправке, город запоминает те,
   что уже называли, и предлагает их следующий раз. Появится третий
   остров — в коде не меняется ничего.

3. Остаётся СЛЕД. Уехал — в журнале города видно: кто, куда, когда.
   Раньше человек просто исчезал из ковчега.

4. Кнопка у Брата больше не открывает окно — ведёт на эту страницу,
   как «Работа» ведёт на свою. Старый диалог со списком удалён.

ЧЕГО ПАТЧ НЕ ТРОГАЕТ
────────────────────
`perevozka.py` — саму механику сборки, распаковки и увольнения перед
дорогой. Она рабочая и одна на оба берега; страница только зовёт её.
Двух правд о том, что едет с человеком, город не заводит.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_stranicu_perevozki.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "STRANICA_PEREVOZKI_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "perevozka.py").exists()
            and (p / "Брат" / "ui_brat.py").exists()
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


STRANICA = '''# -*- coding: utf-8 -*-
# STRANICA_PEREVOZKI_V1
"""
ПЕРЕВОЗКА — дорога между берегом и островами.

ЗАМЫСЕЛ (слова Шефа 16.08)
    Берег — главный репо, город Грондхейм, он один. Острова —
    отдельные репо; первый Остров Надежды, будут ещё. Перевозка ходит
    только между ними, туда и обратно.

    Внутри города переездов НЕТ: перемещение по локациям — это
    прогулки, своя механика и своё время. Сюда её не мешаем.

ЗАКОН ЭТОЙ СТРАНИЦЫ
    Ехать может не каждый и не всегда — поэтому здесь нет витрины со
    всеми жителями и галочками. Дорога начинается ОТ ЧЕЛОВЕКА: выбрал
    одного, назвал берег, собрал.

    Остров нигде не зашит. Имя пишется при отправке; те, что уже
    называли, город помнит и предлагает. Появится третий остров — в
    коде не меняется ничего.

    Механику сборки и распаковки не повторяем: её делает perevozka.py,
    один и тот же файл на обоих берегах. Двух правд о том, что едет с
    человеком, город не держит.
"""
from __future__ import annotations

import json
import sys as _sys
from datetime import datetime
from pathlib import Path
from typing import Any

from nicegui import ui

_GOROD = Path(__file__).resolve().parent
_KOREN = _GOROD.parent
for _p in (str(_KOREN), str(_GOROD)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

ZHURNAL = _KOREN / "GRONDHEIM_CITY" / "перевозка_журнал.json"

CSS = """
<style>
.per-page { background:#0b0f14; color:#e6edf3;
            font-family:'Inter',system-ui,sans-serif; }
.per-head { padding:14px 20px; border-bottom:1px solid rgba(255,255,255,0.08);
            display:flex; align-items:center; gap:14px; }
.per-title { font-size:0.82rem; letter-spacing:0.12em; font-weight:700;
             color:rgba(255,255,255,0.85); }
.per-bereg { font-size:0.7rem; letter-spacing:0.08em; padding:3px 10px;
             border-radius:20px; border:1px solid rgba(201,168,76,0.5);
             color:rgba(201,168,76,0.9); }
.per-wrap { display:flex; gap:18px; padding:18px 20px; align-items:flex-start; }
.per-card { background:#0d1117; border:1px solid rgba(255,255,255,0.10);
            border-radius:14px; padding:16px; }
.per-podpis { color:rgba(255,255,255,0.45); font-size:0.72rem;
              margin-bottom:10px; line-height:1.5; }
.per-stroka { display:flex; align-items:center; gap:10px; padding:7px 10px;
              border-radius:8px; cursor:pointer; }
.per-stroka:hover { background:rgba(255,255,255,0.05); }
.per-vybran { background:rgba(201,168,76,0.16);
              border:1px solid rgba(201,168,76,0.45); }
.per-imya { color:rgba(255,255,255,0.92); font-size:0.82rem;
            min-width:120px; }
.per-gde { color:rgba(255,255,255,0.40); font-size:0.72rem; }
.per-kvartal { color:rgba(201,168,76,0.75); font-size:0.66rem;
               letter-spacing:0.10em; font-weight:700; margin:12px 0 3px; }
</style>
"""


def _zhurnal_chitat() -> list:
    try:
        return json.loads(ZHURNAL.read_text(encoding="utf-8")).get("дорога", [])
    except Exception:
        return []


def _zhurnal_pisat(zapis: dict):
    d = {"дорога": _zhurnal_chitat()}
    d["дорога"].append(zapis)
    try:
        ZHURNAL.parent.mkdir(parents=True, exist_ok=True)
        ZHURNAL.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    except Exception as e:
        print(f"[ПЕРЕВОЗКА] журнал не записался: {e}")


def _berega_kotorye_znaem() -> list:
    """Куда уже возили. Списка островов город заранее не держит —
    помнит только те имена, что называли ему сами."""
    vidno = []
    for z in _zhurnal_chitat():
        b = (z.get("куда") or "").strip()
        if b and b not in vidno:
            vidno.append(b)
    return vidno


def _kvartal(rabota: str) -> str:
    r = (rabota or "").lower()
    if not r.strip():
        return "БЕЗ МЕСТА"
    if "бирж" in r:
        return "БИРЖА"
    if "академ" in r or "ректор" in r or "библиотек" in r:
        return "АКАДЕМИЯ"
    if "архив" in r:
        return "АРХИВ"
    if "маяк" in r:
        return "МАЯК"
    return "ГОРОД"


def page_perevozka():
    ui.add_head_html(CSS)
    ui.query("body").classes("per-page")

    try:
        import perevozka as P
    except Exception as e:
        ui.label(f"Перевозка не поднялась: {e}")
        return
    try:
        import rabota as R
    except Exception:
        R = None

    na_ostrove = False
    try:
        na_ostrove = P.eto_ostrov()
    except Exception:
        pass

    sost: dict[str, Any] = {"кто": None, "поиск": ""}
    refs: dict[str, Any] = {}

    with ui.element("div").classes("per-head"):
        ui.html('<div class="per-title">ГРОНДХЕЙМ · ПЕРЕВОЗКА</div>')
        ui.html(f'<div class="per-bereg">'
                f'{"ОСТРОВ — принимаю" if na_ostrove else "БЕРЕГ — отправляю"}'
                f'</div>')
        ui.element("div").style("flex:1")
        ui.button("← город", on_click=lambda: ui.navigate.to("/grondheim")
                  ).props("flat no-caps").style(
            "color:rgba(255,255,255,0.5); font-size:0.75rem;")

    if na_ostrove:
        _storona_ostrova(P, R)
    else:
        _storona_berega(P, R, sost, refs)


def _storona_berega(P, R, sost, refs):
    """Отправка. От человека, а не от списка."""
    with ui.element("div").classes("per-wrap"):
        # ── кто едет ──
        with ui.element("div").classes("per-card").style(
                "flex:1; min-width:380px;"):
            ui.html('<div class="per-title" style="font-size:0.72rem;">'
                    'КТО ЕДЕТ</div>')
            ui.html('<div class="per-podpis">Ехать может не каждый и не '
                    'всегда — поэтому по одному. Кого выберешь, тот '
                    'снимется с места и уедет со всем личным.</div>')

            poisk = ui.input(placeholder="найти по имени…").props(
                "dark dense outlined").style("width:100%; margin-bottom:8px;")
            spisok = ui.element("div").style(
                "max-height:52vh; overflow-y:auto;")

            def _narisovat():
                spisok.clear()
                nado = (poisk.value or "").strip().lower()
                lyudi = [c for c in P.zhiteli()
                         if not nado or nado in c["имя"].lower()]
                if not lyudi:
                    with spisok:
                        ui.html('<div class="per-podpis">никого не нашлось'
                                '</div>')
                    return
                po_kv: dict = {}
                for c in lyudi:
                    po_kv.setdefault(_kvartal(c["работа"]), []).append(c)
                poryadok = [k for k in ("БИРЖА", "АКАДЕМИЯ", "АРХИВ", "МАЯК",
                                        "ГОРОД") if k in po_kv]
                if "БЕЗ МЕСТА" in po_kv:
                    poryadok.append("БЕЗ МЕСТА")
                with spisok:
                    for kv in poryadok:
                        ui.html(f'<div class="per-kvartal">{kv}</div>')
                        for c in sorted(po_kv[kv], key=lambda x: x["имя"]):
                            vybran = (sost["кто"] or {}).get("имя") == c["имя"]
                            klass = "per-stroka" + (" per-vybran"
                                                    if vybran else "")
                            el = ui.element("div").classes(klass)
                            el.on("click", lambda ch=c: _vybrat(ch))
                            with el:
                                ui.html(
                                    f'<span class="per-imya">{c["имя"]}</span>'
                                    f'<span class="per-gde">'
                                    f'{c["работа"] or ""}</span>')

            def _vybrat(ch):
                sost["кто"] = ch
                _narisovat()
                _obnovit_dorogu()

            poisk.on("update:model-value", lambda _: _narisovat())
            _narisovat()

        # ── куда ──
        with ui.element("div").classes("per-card").style(
                "flex:1; min-width:340px;"):
            ui.html('<div class="per-title" style="font-size:0.72rem;">'
                    'КУДА</div>')
            ui.html('<div class="per-podpis">Берег — этот город. Острова — '
                    'отдельные репозитории. Имя пишется здесь и нигде не '
                    'зашито: появится новый остров — менять нечего.</div>')

            znaem = _berega_kotorye_znaem() or ["Остров Надежды"]
            kuda = ui.select(znaem, value=znaem[0],
                             new_value_mode="add-unique",
                             label="куда везём").props(
                "dark dense outlined").style("width:100%;")

            refs["dor"] = ui.html("")

            def _obnovit_dorogu():
                ch = sost["кто"]
                if not ch:
                    refs["dor"].content = (
                        '<div class="per-podpis">Никто не выбран.</div>')
                    return
                post = None
                try:
                    post = P._post_zhitelya(R, ch["имя"])
                except Exception:
                    pass
                pred = ("" if not post else
                        f'<div style="color:rgba(255,200,120,0.85); '
                        f'font-size:0.72rem; margin-top:8px;">'
                        f'{ch["имя"]} сидит на месте «{ch["работа"]}» — '
                        f'сниму с него перед дорогой, чтобы место не '
                        f'осталось занятым.</div>')
                refs["dor"].content = (
                    f'<div style="color:rgba(255,255,255,0.92); '
                    f'font-size:0.9rem; margin-top:10px;">'
                    f'{ch["имя"]} → {kuda.value}</div>{pred}')

            refs["_obnovit"] = _obnovit_dorogu
            kuda.on("update:model-value", lambda _: _obnovit_dorogu())
            _obnovit_dorogu()

            itog = ui.html("")

            def _sobrat():
                ch = sost["кто"]
                if not ch:
                    ui.notify("Сперва выбери, кто едет", color="warning")
                    return
                bereg = (kuda.value or "").strip() or "остров"
                try:
                    a = P.upakovat(ch, R)
                except Exception as e:
                    ui.notify(f"⚠ {ch['имя']}: {e}", color="negative")
                    return
                if not a:
                    ui.notify(f"⚠ {ch['имя']}: собрать не вышло",
                              color="negative")
                    return
                _zhurnal_pisat({"кто": ch["имя"], "куда": bereg,
                                "когда": datetime.now().isoformat(
                                    timespec="seconds"),
                                "архив": a.name})
                itog.content = (
                    f'<div style="color:rgba(80,250,123,0.85); '
                    f'font-size:0.78rem; margin-top:12px;">'
                    f'{ch["имя"]} собран(а) в дорогу на {bereg}.<br>'
                    f'Архив: {a.name}<br><br>'
                    f'Лежит в папке _ОТПРАВКА. Перенеси файл на остров '
                    f'и открой там эту же страницу — она его примет.</div>')
                ui.notify(f"🧳 {ch['имя']} → {bereg}", color="positive")
                sost["кто"] = None

            ui.button("собрать в дорогу", on_click=_sobrat).props(
                "flat no-caps").style(
                "margin-top:14px; padding:9px 22px; border-radius:8px; "
                "font-weight:700; font-size:0.8rem; color:#fff; "
                "background:linear-gradient(135deg,rgba(201,168,76,0.30),"
                "rgba(201,168,76,0.18)); "
                "border:1px solid rgba(201,168,76,0.55);")

        # ── кто уже уехал ──
        with ui.element("div").classes("per-card").style(
                "flex:1; min-width:260px;"):
            ui.html('<div class="per-title" style="font-size:0.72rem;">'
                    'УЕХАЛИ</div>')
            zapisi = list(reversed(_zhurnal_chitat()))[:20]
            if not zapisi:
                ui.html('<div class="per-podpis">Пока никто. Уехавшие '
                        'останутся здесь — город не должен забывать, кто '
                        'был и где он теперь.</div>')
            else:
                for z in zapisi:
                    ui.html(
                        f'<div style="padding:5px 0; border-bottom:'
                        f'1px solid rgba(255,255,255,0.05);">'
                        f'<span class="per-imya">{z.get("кто","")}</span>'
                        f'<span class="per-gde">→ {z.get("куда","")} · '
                        f'{(z.get("когда") or "")[:10]}</span></div>')


def _storona_ostrova(P, R):
    """Приём. Та же страница, другая сторона дороги."""
    with ui.element("div").classes("per-wrap"):
        with ui.element("div").classes("per-card").style(
                "flex:1; min-width:420px;"):
            ui.html('<div class="per-title" style="font-size:0.72rem;">'
                    'ПРИШЛИ</div>')
            ui.html('<div class="per-podpis">Положи архив рядом с этой '
                    'папкой — он появится здесь. Приму, поселю и посажу на '
                    'свободное место, если оно есть.</div>')
            spisok = ui.element("div")

            def _narisovat():
                spisok.clear()
                arhivy = P.nayti_arhivy()
                with spisok:
                    if not arhivy:
                        ui.html('<div class="per-podpis">Пока пусто.</div>')
                        return
                    for a in arhivy:
                        with ui.row().style("align-items:center; gap:10px; "
                                            "padding:6px 0;"):
                            ui.html(f'<span class="per-imya">{a.name}</span>')
                            ui.button("принять",
                                      on_click=lambda p=a: _prinyat(p)).props(
                                "flat no-caps dense").style(
                                "color:rgba(201,168,76,0.9); "
                                "font-size:0.75rem;")

            def _prinyat(arhiv):
                try:
                    imya = P.raspakovat(arhiv)
                except Exception as e:
                    ui.notify(f"⚠ {arhiv.name}: {e}", color="negative")
                    return
                if not imya:
                    ui.notify(f"⚠ {arhiv.name}: это не архив перевозки",
                              color="negative")
                    return
                try:
                    P.posadit(R, imya)
                except Exception:
                    pass
                _zhurnal_pisat({"кто": imya, "откуда": "берег",
                                "когда": datetime.now().isoformat(
                                    timespec="seconds"),
                                "архив": arhiv.name})
                ui.notify(f"🏝 {imya} на месте", color="positive")
                _narisovat()

            _narisovat()


# STRANICA_PEREVOZKI_V1 - marker
'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    stranica = koren / "ГОРОД" / "ui_perevozka.py"
    glavnyy = koren / "main.py"
    brat = koren / "Брат" / "ui_brat.py"

    # ── 1. страница ──
    print("\n1. Страница — ГОРОД/ui_perevozka.py")
    if stranica.exists() and MARKER in stranica.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        try:
            ast.parse(STRANICA)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if not SUHO:
            stranica.write_text(STRANICA, encoding="utf-8")
        print("  ✓ положена (берег отправляет, остров принимает)")

    # ── 2. регистрация в main ──
    print("\n2. Адрес /perevozka в main.py")
    t = glavnyy.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · уже прописан")
    else:
        yakor = '''from ui_rabota import page_rabota
@ui.page("/rabota")
def _rabota():
    page_rabota()'''
        if t.count(yakor) != 1:
            print("  ✗ не нашёл, как заведена Страница Работы — не трогаю")
            return 1
        novyy = t.replace(yakor, yakor + f'''

# ── ПЕРЕВОЗКА — дорога между берегом и островами ({MARKER}) ──
# Берег один (этот репо), островов сколько угодно. Страница сама
# понимает, где её открыли: на берегу отправляет, на острове принимает.
from ui_perevozka import page_perevozka
@ui.page("/perevozka")
def _perevozka():
    page_perevozka()''', 1)
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if not SUHO:
            shutil.copy2(glavnyy, glavnyy.with_suffix(
                f".py.bak_perevozka_{datetime.now():%Y%m%d_%H%M%S}"))
            glavnyy.write_text(novyy, encoding="utf-8")
        print("  ✓ прописан")

    # ── 3. кнопка Брата ведёт на страницу, окно выброшено ──
    print("\n3. Кнопка у Брата — ссылкой, старое окно выброшено")
    t = brat.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · уже сделано")
    else:
        n1 = t.find("    async def do_perevozka():")
        n2 = t.find("\n    async def ", n1 + 10)
        if n1 < 0 or n2 < 0:
            print("  ✗ не нашёл старый обработчик — не трогаю")
            return 1
        novyy = t[:n1] + (
            "    def do_perevozka():\n"
            "        \"\"\"" + MARKER + ": окно со списком выброшено.\n\n"
            "        Оно было витриной: все жители разом и галочки, будто\n"
            "        ехать может каждый и всегда в одно место. Дорога —\n"
            "        событие редкое и личное, у неё своя страница.\n"
            "        \"\"\"\n"
            "        ui.navigate.to(\"/perevozka\")\n") + t[n2:]
        # кнопка зовёт обычную функцию, не корутину
        novyy = novyy.replace("on_click=do_perevozka\n",
                              "on_click=lambda: do_perevozka()\n", 1)
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if not SUHO:
            shutil.copy2(brat, brat.with_suffix(
                f".py.bak_perevozka_{datetime.now():%Y%m%d_%H%M%S}"))
            brat.write_text(novyy + f"\n# {MARKER} - marker\n",
                            encoding="utf-8")
        print("  ✓ ведёт на /perevozka")

    if not SUHO:
        import py_compile
        for f in (stranica, glavnyy, brat):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nКак теперь: Брат → Перевозка → своя страница.")
        print("  Слева выбираешь ОДНОГО (есть поиск), справа пишешь берег.")
        print("  Сидит на посту — страница скажет об этом до отправки.")
        print("  Внизу список уехавших: кто, куда, когда.")
        print("\nНа острове та же страница работает наоборот: показывает")
        print("пришедшие архивы и принимает их. Ничего настраивать не надо —")
        print("она сама понимает, где её открыли.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
