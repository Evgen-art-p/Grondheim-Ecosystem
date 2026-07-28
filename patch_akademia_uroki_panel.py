# PATCH_AKADEMIA_UROKI_PANEL_V1
"""
PATCH_AKADEMIA_UROKI_PANEL_V1 -- панель «УРОКИ» в кабинете Академии.

Слово Шефа: "захожу в кабинет академии, у меня видно список тем,
уроков, нажимаю урок -- появляется в отчётах, справа от чата, как
везде, читает студент."

ЧТО ДЕЛАЕТ:
  - новая панель в левой колонке, под кнопками "Прочитать"/"Осмыслить":
    список всех дисциплин (GRONDHEIM_CITY/Академия/дисциплины/*/*/
    manifest.json) и их уроков -- живой скан диска (положишь новую
    дисциплину/урок -- появится сама, код не трогаем);
  - клик по уроку -- текст .md показывается в ТОМ ЖЕ viewer
    ("отчёты"), что и карточка студента -- тот же UI-элемент;
  - кнопка "📖 Дать читать" -- активный студент читает показанный
    урок своей натурой, ответ идёт в чат, впечатление сохраняется в
    его личную память (dvizhok, kontekst="учёба") -- через уже
    существующие _dvizhok_dlya()/_zvat_llm_akademii()
    (patch_akademia_stol_chtenie.py).

Требует: patch_akademia_stol_chtenie.py уже применён (использует его
_dvizhok_dlya и _zvat_llm_akademii, не дублирует).

Идемпотентно: если маркер PATCH_AKADEMIA_UROKI_PANEL_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_akademia_uroki_panel.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_akademia.py')
MARKER = 'PATCH_AKADEMIA_UROKI_PANEL_V1'

OLD_MODULE_ANCHOR = '''def _dvizhok_dlya(dom: Path):
    """Поднимает rezidenty + Dvizhok жителя из кабинета Академии --
    своя точка входа в sys.path, не трогаем общий список модуля
    (Закон Двух Стандартов: свой самодостаточный ход)."""
    _repo2 = Path(__file__).resolve().parent.parent
    for _pp in (_repo2, _repo2 / "ГОРОД", _repo2 / "жители"):
        if str(_pp) not in sys.path:
            sys.path.insert(0, str(_pp))
    import rezidenty
    from dvizhok import Dvizhok
    return rezidenty, Dvizhok'''

NOVYI_MODULE_ANCHOR = '''def _dvizhok_dlya(dom: Path):
    """Поднимает rezidenty + Dvizhok жителя из кабинета Академии --
    своя точка входа в sys.path, не трогаем общий список модуля
    (Закон Двух Стандартов: свой самодостаточный ход)."""
    _repo2 = Path(__file__).resolve().parent.parent
    for _pp in (_repo2, _repo2 / "ГОРОД", _repo2 / "жители"):
        if str(_pp) not in sys.path:
            sys.path.insert(0, str(_pp))
    import rezidenty
    from dvizhok import Dvizhok
    return rezidenty, Dvizhok


# ═══════════════════════════════════════════════════════════
# PATCH_AKADEMIA_UROKI_PANEL_V1 -- список дисциплин/уроков, живой
# скан диска. Ни одной дисциплины -- честный пустой список, не падаем.
# ═══════════════════════════════════════════════════════════
_DISTSIPLINY_DIR = _DATA / "дисциплины"


def _vse_distsipliny() -> list:
    """Все дисциплины по всем направлениям -- плоский список для UI.
    Дисциплин нет -- пустой список, честно."""
    out = []
    if not _DISTSIPLINY_DIR.exists():
        return out
    for napr_dir in sorted(_DISTSIPLINY_DIR.iterdir()):
        if not napr_dir.is_dir():
            continue
        for d in sorted(napr_dir.iterdir()):
            if not d.is_dir():
                continue
            man = _read_json(d / "manifest.json")
            if man:
                man["_путь"] = str(d)
                man.setdefault("направление", napr_dir.name)
                out.append(man)
    return out


def _urok_soderzhimoe(distsiplina_put: str, urok_rel: str) -> str:
    fp = Path(distsiplina_put) / urok_rel
    try:
        return fp.read_text(encoding="utf-8")
    except Exception:
        return ""'''

OLD_REFS_ANCHOR = '''    chat_ref   = {"element": None}
    viewer_ref = {"element": None}
    ruda_ref   = {"element": None, "uploader": None}
    knigi_ref  = {"uploader": None, "полка": None}'''

NOVYI_REFS_ANCHOR = '''    chat_ref   = {"element": None}
    viewer_ref = {"element": None}
    ruda_ref   = {"element": None, "uploader": None}
    uroki_ref  = {"element": None}  # PATCH_AKADEMIA_UROKI_PANEL_V1
    knigi_ref  = {"uploader": None, "полка": None}'''

OLD_NESTED_ANCHOR = '''    def clear_ruda():
        state["руда"] = []
        update_ruda_list()
        ui.notify("Список очищен (файлы на диске остались)", type="info")'''

NOVYI_NESTED_ANCHOR = '''    def clear_ruda():
        state["руда"] = []
        update_ruda_list()
        ui.notify("Список очищен (файлы на диске остались)", type="info")

    # ── PATCH_AKADEMIA_UROKI_PANEL_V1 ────────────────────────
    state["текущий_урок"] = {"текст": "", "название": ""}

    def pokazat_urok(dist: dict, urok_rel: str, label: str):
        text = _urok_soderzhimoe(dist["_путь"], urok_rel)
        if not text.strip():
            ui.notify(f"«{label}» пуст или не читается", type="warning")
            return
        title = f'{dist.get("название", dist.get("id",""))} — {label}'
        state["текущий_урок"] = {"текст": text, "название": title}
        update_viewer(f"# {dist.get('название', dist.get('id',''))}\\n\\n"
                     f"## {label}\\n\\n{text}")

    def update_uroki_panel():
        if not uroki_ref["element"]:
            return
        uroki_ref["element"].clear()
        with uroki_ref["element"]:
            distsipliny = _vse_distsipliny()
            if not distsipliny:
                ui.html('<div style="color:rgba(255,255,255,0.35);font-size:10px;'
                        'padding:8px 12px;">Дисциплин пока нет</div>')
                return
            for dist in distsipliny:
                nazv = dist.get("название", dist.get("id", "?"))
                napr = dist.get("направление", "")
                ui.html(f'<div style="padding:6px 10px 2px 10px;font-size:10px;'
                        f'font-weight:800;color:rgba(0,204,255,0.85);'
                        f'text-transform:uppercase;letter-spacing:.06em;">'
                        f'{nazv} <span style="color:rgba(255,255,255,0.35);'
                        f'font-weight:400;">· {napr}</span></div>')
                uroki = dist.get("уроки", []) or []
                if not uroki:
                    ui.html('<div style="color:rgba(255,255,255,0.3);font-size:9px;'
                            'padding:2px 14px 6px 14px;">— уроков нет —</div>')
                    continue
                for urok_rel in uroki:
                    label = Path(urok_rel).stem
                    def _click(d=dist, u=urok_rel, lbl=label):
                        pokazat_urok(d, u, lbl)
                    ui.button(label, on_click=_click).props("flat no-caps dense").style(
                        "width:calc(100% - 8px); margin:1px 4px; text-align:left; "
                        "font-size:10px; color:rgba(255,255,255,0.7); "
                        "padding:4px 10px; border-radius:6px; "
                        "background:rgba(255,255,255,0.02);")

    async def do_chtenie_uroka():
        """Активный студент читает ПОКАЗАННЫЙ урок своей натурой.
        Впечатление сохраняется в его личную память (dvizhok,
        kontekst="учёба") -- через уже существующие _dvizhok_dlya()/
        _zvat_llm_akademii() (patch_akademia_stol_chtenie.py)."""
        urok = state.get("текущий_урок") or {}
        text = (urok.get("текст") or "").strip()
        if not text:
            ui.notify("Сначала выбери урок слева", type="warning")
            return
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — читать некому", type="warning")
            return
        imya, dom = m["имя"], m["дом"]
        try:
            rezidenty, Dvizhok = _dvizhok_dlya(dom)
            dv = Dvizhok(dom)
        except Exception as e:
            ui.notify(f"⚠ движок не дышит: {e}", type="negative")
            return
        p = _read_json(dom / "passport.json", {}) or {}
        try:
            dusha = rezidenty.sobrat_dushu(p)
        except Exception:
            dusha = f"Ты — {imya}, житель Грондхейма. Говоришь от первого лица.\\n"

        state["чат"].append({"role": "assistant", "кто": "УРОК",
                             "content": f"📖 {imya} читает «{urok['название']}»…"})
        update_chat()

        vopros = (f"Ты сейчас в Академии, изучаешь урок.\\n\\n"
                 f"{text}\\n\\n"
                 f"Прочитай своей натурой, вынеси концентрат — 5-8 строк, "
                 f"суть плюс твой личный отклик через свою натуру.")
        messages = [{"role": "system", "content": dusha},
                   {"role": "user", "content": vopros}]
        vyzhimka = await _zvat_llm_akademii(messages, state.get("model"))
        if not vyzhimka or vyzhimka.startswith("⚠"):
            ui.notify(f"⚠ {(vyzhimka or 'пустой ответ')[:90]}", type="negative")
            return

        try:
            vdoh_res = dv.vdoh(kontekst="учёба", sila=0.8, svezhest=1.0, tonus="плюс")
            dv.vydoh_stol(fakt=f"[Академия] «{urok['название']}»: {vyzhimka.strip()}",
                          vdoh_result=vdoh_res)
            dv.sохранить()
        except Exception:
            pass

        state["чат"].append({"role": "assistant", "кто": imya,
                             "content": f"📖 «{urok['название']}» — {vyzhimka.strip()}"})
        ui.notify(f"✦ {imya} прочитал(а): {urok['название']}", type="positive")
        update_chat()'''

OLD_LAYOUT_ANCHOR = '''                    ui.button("🪞 Осмыслить", on_click=do_prosev_akademii).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:rgba(160,160,220,0.12) !important; "
                        "border:1px solid rgba(160,160,220,0.35) !important; color:#c8c8ec !important;")

        # ── ЦЕНТР: тулбар + чат/отчёт + консоль ──'''

NOVYI_LAYOUT_ANCHOR = '''                    ui.button("🪞 Осмыслить", on_click=do_prosev_akademii).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:rgba(160,160,220,0.12) !important; "
                        "border:1px solid rgba(160,160,220,0.35) !important; color:#c8c8ec !important;")

                # PATCH_AKADEMIA_UROKI_PANEL_V1
                with ui.element("div").classes("glass").style(
                        "flex:1; min-height:0; overflow:hidden; display:flex; flex-direction:column;"):
                    ui.label("УРОКИ").style(
                        "color:rgba(255,255,255,0.92); font-weight:900; letter-spacing:.12em; "
                        "text-transform:uppercase; font-size:11px; padding:12px 16px 6px 16px;")
                    uroki_ref["element"] = ui.element("div").style(
                        "flex:1; min-height:0; overflow-y:auto; padding-bottom:6px;")
                    update_uroki_panel()
                    ui.button("📖 Дать читать (активный студент)", on_click=do_chtenie_uroka) \\
                        .props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:6px 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.78rem; letter-spacing:0.04em; "
                        "background:rgba(0,204,255,0.15) !important; "
                        "border:1px solid rgba(0,204,255,0.45) !important; color:#8adfff !important;")

        # ── ЦЕНТР: тулбар + чат/отчёт + консоль ──'''

REPLACEMENTS = [
    (OLD_MODULE_ANCHOR, NOVYI_MODULE_ANCHOR),
    (OLD_REFS_ANCHOR, NOVYI_REFS_ANCHOR),
    (OLD_NESTED_ANCHOR, NOVYI_NESTED_ANCHOR),
    (OLD_LAYOUT_ANCHOR, NOVYI_LAYOUT_ANCHOR),
]

REPLACE_ALL = [
]


def main():
    if not TARGET.exists():
        print(f"⚠ не найден {TARGET} — запускай из корня репо")
        sys.exit(1)
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже стоит в {TARGET} — патч не нужен")
        return
    for old, new in REPLACEMENTS:
        if old not in text:
            print("⚠ не нашёл кусок для замены — файл изменился с момента патча:")
            print(old[:200])
            sys.exit(1)
        if text.count(old) > 1:
            print("⚠ кусок встречается больше одного раза — небезопасно патчить:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new, 1)
    for old, new in REPLACE_ALL:
        if old not in text:
            print("⚠ не нашёл кусок для повсеместной замены — файл изменился:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new)
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_uroki_panel")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
