# -*- coding: utf-8 -*-
"""
postavit_vremya_v_kabinet.py · MARKER: VREMYA_V_KABINETE_V1

ТРЕБУЕТ: postavit_mashinu_vremeni.py.

ЧТО ДЕЛАЕТ, ПРОСТЫМИ СЛОВАМИ
────────────────────────────
Машина времени была в консоли — теперь она в кабинете, кнопками.

Включаешь ТЕСТЕР — рядом с тумблером появляется полоска:

    ⏮  ◀◀   ◀   ▶   ▶▶  ⏭     стоим: 2024.03.15 20:00

    ◀ ▶     шаг на один бар назад/вперёд
    ◀◀ ▶▶   шаг на десять
    ⏮       в начало истории
    ⏭       в конец (курсор снят, как было раньше)

Шагает по этажу того трейдера, чей пузырёк сейчас нажат: у Нины
свой этаж, у Веры свой. Кадр справа перерисовывается сам после
каждого шага — то есть жмёшь ▶ и сразу видишь следующий бар её
глазами.

Пока курсор стоит, в этой точке истории стоит ВЕСЬ город. Жмёшь
РЫНОК — трейдеры видят ровно то, что видишь ты, и решают по этому.
Переключился на РЕАЛ — курсор снимается сам, чтобы живой рынок не
остался стоять в прошлом.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_vremya_v_kabinet.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VREMYA_V_KABINETE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ui_torg.py").exists()
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


# ── 1. руки шага (рядом с pokazat_kadr, чтобы кадр был под рукой) ──
ST_RUKI = '''    def pokazat_kadr(put=None):'''

NOV_RUKI = '''    # ── VREMYA_V_KABINETE_V1: шаг по истории ──────────────────
    def _para_dlya_shaga() -> tuple:
        """По чьему этажу шагаем. По активному трейдеру: у каждого
        свой рабочий этаж, и шаг должен быть в его барах."""
        s, t, _chey, _net = _para_aktivnogo()
        if s and t:
            return s, t
        return _aktivnyy_rynok()

    def _vremya_vid():
        """Обновить надпись «стоим: …»."""
        el = toolbar_refs.get("moment_label")
        if el is None:
            return
        try:
            import istoriya
            m = istoriya.gde_stoim()
        except Exception:
            m = ""
        el.text = f"стоим: {m}" if m else "конец истории"

    def _shagnut(skolko):
        """Шаг по истории. skolko=None — в конец (снять курсор)."""
        if state.get("mode") != "tester":
            ui.notify("Шаг по истории есть только в ТЕСТЕРЕ", type="warning")
            return
        symbol, tf = _para_dlya_shaga()
        if not symbol or not tf:
            ui.notify("Не пойму, по какому этажу шагать — "
                      "выбери трейдера или актив слева", type="warning")
            return
        try:
            import istoriya
            if skolko is None:
                istoriya.postavit("")
                ui.notify("⏭ конец истории", type="info")
            elif skolko == "начало":
                pervyy, _ = istoriya.dokuda_est(symbol, tf)
                if not pervyy:
                    ui.notify(f"Нет истории {symbol} {tf} в test_data",
                              type="warning")
                    return
                istoriya.postavit(pervyy)
                ui.notify(f"⏮ {pervyy}", type="info")
            else:
                m = istoriya.shag(tf, int(skolko), symbol=symbol)
                if not m:
                    ui.notify(f"Нет истории {symbol} {tf} в test_data",
                              type="warning")
                    return
        except Exception as e:
            ui.notify(f"Шаг не вышел: {e}", type="negative")
            return
        _vremya_vid()
        try:
            pokazat_kadr()          # сразу видно следующий бар
        except Exception as e:
            print(f"[ВРЕМЯ] кадр не перерисовался: {e}")

    def pokazat_kadr(put=None):'''

# ── 2. кнопки в тулбар, сразу после тумблера ТЕСТЕР ──
ST_KNOPKI = '''                        toolbar_refs["bars_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")'''

NOV_KNOPKI = '''                        # VREMYA_V_KABINETE_V1: шаг по истории. Видно
                        # только в ТЕСТЕРЕ — в реале времени не крутят.
                        toolbar_refs["vremya_panel"] = ui.element("div").style(
                            "display:none;align-items:center;gap:4px;"
                            "margin-left:8px;padding-left:8px;"
                            "border-left:1px solid rgba(255,255,255,0.1);")
                        with toolbar_refs["vremya_panel"]:
                            _knopki = (("⏮", "начало", "в начало истории"),
                                       ("◀◀", -10, "назад 10 баров"),
                                       ("◀", -1, "назад 1 бар"),
                                       ("▶", 1, "вперёд 1 бар"),
                                       ("▶▶", 10, "вперёд 10 баров"),
                                       ("⏭", None, "в конец, курсор снять"))
                            for _znak, _skolko, _podskazka in _knopki:
                                _b = ui.element("div").style(
                                    "padding:5px 9px;border-radius:6px;"
                                    "font-size:12px;cursor:pointer;"
                                    "background:rgba(255,255,255,0.04);"
                                    "color:rgba(255,255,255,0.7);"
                                    "border:1px solid rgba(255,255,255,0.1);")
                                _b.on("click",
                                      lambda s=_skolko: _shagnut(s))
                                _b.tooltip(_podskazka)
                                with _b:
                                    ui.html(_znak)
                            toolbar_refs["moment_label"] = ui.label(
                                "конец истории").style(
                                "color:rgba(139,233,253,0.75);font-size:11px;"
                                "margin-left:6px;white-space:nowrap;")
                        toolbar_refs["bars_label"] = ui.element("div").style("display:none;align-items:center;gap:5px;")'''

# ── 3. показывать панель только в тестере + снимать курсор в реале ──
ST_MODE = '''        for key in ("bars_input", "stop_btn", "bars_label",
                    "learn_btn"):   # TORG_LEARN_SWITCH_V1'''

NOV_MODE = '''        # VREMYA_V_KABINETE_V1: ушли в РЕАЛ — снимаем курсор истории,
        # иначе живой рынок останется стоять в прошлом и будет тихо
        # показывать вчерашние бары как сегодняшние.
        if not is_tester:
            try:
                import istoriya
                if istoriya.gde_stoim():
                    istoriya.postavit("")
                    print("[ВРЕМЯ] курсор истории снят — вернулись в реал")
            except Exception:
                pass
        try:
            _vremya_vid()
        except Exception:
            pass
        for key in ("bars_input", "stop_btn", "bars_label",
                    "learn_btn", "vremya_panel"):   # TORG_LEARN_SWITCH_V1'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ui_torg = koren / "Биржа" / "ui_torg.py"
    istoriya = koren / "Биржа" / "istoriya.py"

    if not istoriya.exists():
        print("✗ Нет Биржа/istoriya.py — накати сперва "
              "postavit_mashinu_vremeni.py")
        return 1

    t = ui_torg.read_text(encoding="utf-8")
    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if "VZGLYAD_KAZHDOGO_V1" not in t:
        print("✗ Нет взгляда каждого — накати сперва "
              "postavit_vzglyad_kazhdogo.py")
        return 1

    yakorya = [("руки шага", ST_RUKI, NOV_RUKI),
               ("кнопки", ST_KNOPKI, NOV_KNOPKI),
               ("режим", ST_MODE, NOV_MODE)]
    beda = [imya for imya, st, _ in yakorya if t.count(st) != 1]
    if beda:
        print(f"✗ якоря не найдены дословно: {', '.join(beda)}")
        return 1

    novyy = t
    for _, st, nov in yakorya:
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

    bak = ui_torg.with_suffix(
        f".py.bak_vremya_kab_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(ui_torg, bak)
    ui_torg.write_text(novyy, encoding="utf-8")
    print(f"✓ кабинет поправлен (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(ui_torg), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nКак пользоваться:")
    print("  1. Жми ТЕСТЕР — рядом появится ⏮ ◀◀ ◀ ▶ ▶▶ ⏭ и «стоим: …»")
    print("  2. Кликни пузырёк трейдера — шаг пойдёт по ЕГО этажу")
    print("  3. Жми ▶ — кадр справа сразу перерисуется на следующий бар")
    print("  4. Нашёл интересное место — жми РЫНОК:")
    print("     трейдеры увидят ровно то, что видишь ты")
    print("\nВернёшься в РЕАЛ — курсор снимется сам.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
