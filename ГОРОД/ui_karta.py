# ui_karta.py
# PATCH_KARTA_KARKAS — каркас карты-иерархии (зрение Брата)
"""
КАРТА-ИЕРАРХИЯ — кабинет города, зрение Брата (объект №1).
Route: /karta · открывается как полноэкранный кабинет, по образцу ui_brat.py.

Брат — дверь №1, его связь со всей экосистемой. Карта — его обзор:
дерево города сверху вниз, кто есть, кто к чему принадлежит.

СЕЙЧАС — ТОЛЬКО КАРКАС:
  • статичное дерево (Брат → 4 этажа, под ними пусто — город молод)
  • НЕТ живого скана паспортов (сборщик каталогов — ступень 3, ещё не построен)
  • НЕТ кликов вглубь, НЕТ погоды, НЕТ чисел
  • scan_hierarchy() — ШОВ под будущий сборщик: сейчас отдаёт каркас,
    потом начнёт обходить паспорта-кусочки. Карта не заметит подмены.

Палитра и сетка — по образцу кабинета Брата (золото #c9a84c, glass, app-container).
Новый город · ни нитки из -2.
`шесть·проверено·до·корня`
"""
from nicegui import ui


# ═══════════════════════════════════════════════════════════
# ШОВ ПОД СБОРЩИК (ступень 3) — сейчас отдаёт каркас.
# Когда родится сборщик каталогов, эта функция начнёт обходить
# паспорта-кусочки по дереву города. Карта переключится сама —
# структура ответа уже та, что нужна.
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# ЖИВОЙ СКАН ЖИТЕЛЕЙ (Страница → Брат). Брат СВЯЗЫВАЕТ, не ДЕРЖИТ.
# Только паспорт-лицо в корне папки профессии. В дом не спускаемся.
# Путь от __file__ (корень репы), не от рабочей папки.
# ═══════════════════════════════════════════════════════════
from pathlib import Path as _Path
import json as _json

_ROOT = _Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: файл в ГОРОД/, корень репо — на уровень выше
ZHITELI_DIR = _ROOT / "GRONDHEIM_CITY" / "жители"
GUARDIANS_DIR = _ROOT / "GRONDHEIM_CITY" / "Hexagon" / "3_guardians"

_VETKA_BY_WORKSHOP = {"hram": "hram", "trading": "trading", "living_book": "living_book"}
_VETKA_BY_RANK = {"хранитель": "hram", "трейдер": "trading"}
_VETKA_DEFAULT = "masters"


def _vetka_for(p):
    wid = (p.get("Workshop_ID") or "").strip().lower()
    if wid in _VETKA_BY_WORKSHOP:
        return _VETKA_BY_WORKSHOP[wid]
    rank = (p.get("Social_Rank") or "").strip().lower()
    if rank in _VETKA_BY_RANK:
        return _VETKA_BY_RANK[rank]
    role = (p.get("предназначение") or "").strip().lower()
    if "хранит" in role:
        return "hram"
    if "трейд" in role or "торг" in role:
        return "trading"
    return _VETKA_DEFAULT


def _name_of(p):
    return p.get("Official_Name") or p.get("имя") or p.get("id") or "?"


def _note_of(p):
    prof = (p.get("Profession") or p.get("предназначение") or p.get("Social_Rank") or "—").strip().rstrip(".")
    rare = (p.get("Rarity") or p.get("редкость") or "").strip()
    return f"{prof} · {rare}" if rare else prof


def _scan_zhiteli():
    found = []
    for base in (ZHITELI_DIR, GUARDIANS_DIR):
        if not base.exists():
            continue
        for prof_dir in base.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                if item.is_file() and item.suffix == ".json":
                    try:
                        found.append(_json.loads(item.read_text(encoding="utf-8")))
                    except Exception:
                        pass
    return found


def _zhitel_node(p):
    return {"id": p.get("ID_Object") or p.get("id") or _name_of(p),
            "label": _name_of(p), "icon": "⬡", "kind": "ядро",
            "note": _note_of(p), "gate": None, "children": []}


def _podvesit(tree, zhiteli):
    by_id = {ch.get("id"): ch for ch in tree.get("children", [])}
    for p in zhiteli:
        v = by_id.get(_vetka_for(p))
        if v is not None:
            v.setdefault("children", []).append(_zhitel_node(p))
    return tree


def scan_hierarchy() -> dict:
    """
    Возвращает дерево иерархии города.

    СЕЙЧАС: статичный каркас — то, что уже стоит в новом городе.
    ПОТОМ: обход паспортов (passport.json) по дереву папок,
           принадлежность из пути. Сигнатура и форма ответа не изменятся.

    Узел: {id, label, icon, kind, gate, children[]}
      kind:  единица | этаж | квартал | цех | ядро | локация
      gate:  путь врат (если есть проход из кабинета) или None
    """
    _karkas = {
        "id": "brat",
        "label": "БРАТ",
        "icon": "⬡",
        "kind": "единица",
        "note": "объект №1 · дверь · связь со всей экосистемой",
        "gate": None,
        "children": [
            {
                "id": "hram", "label": "ХРАМ", "icon": "🏛",
                "kind": "этаж", "note": "хранители равновесия",
                "gate": "/hram/index.html",      # врата живы (узел 1)
                "children": [],                   # хранителей ещё нет
            },
            {
                "id": "trading", "label": "ТОРГОВЫЙ КВАРТАЛ", "icon": "⚔",
                "kind": "квартал", "note": "первым поедет, по образцу",
                "gate": None,                     # врата ждут
                "children": [],
            },
            {
                "id": "masters", "label": "КВАРТАЛ МАСТЕРОВ", "icon": "🔨",
                "kind": "квартал", "note": "цеха студии, по очереди",
                "gate": None,
                "children": [],
            },
            {
                "id": "living_book", "label": "ЖИВАЯ КНИГА", "icon": "📖",
                "kind": "квартал", "note": "память-рукопись",
                "gate": None,
                "children": [],
            },
        ],
    }
    return _podvesit(_karkas, _scan_zhiteli())


# ═══════════════════════════════════════════════════════════
# СТИЛИ — по образцу кабинета Брата (золото, glass, тёмный фон)
# ═══════════════════════════════════════════════════════════

KARTA_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');

.karta-root{
  position: fixed; inset: 0;
  background: #050510;
  font-family: Inter, system-ui, sans-serif;
  color: #fff;
  overflow: auto;
  padding: 28px;
  box-sizing: border-box;
}
.karta-root::after{
  content:''; position: fixed; inset:0; z-index:-1;
  background: radial-gradient(1000px 700px at 20% 10%, rgba(201,168,76,0.10), transparent 60%),
              radial-gradient(900px 650px at 80% 25%, rgba(201,168,76,0.06), transparent 55%),
              rgba(0,0,0,0.40);
}

.karta-head{
  display:flex; align-items:center; gap:16px; margin-bottom: 28px;
}
.karta-title{
  font-size: 1.4rem; font-weight: 900; letter-spacing: 0.14em;
  color: #c9a84c;
}
.karta-sub{
  font-size: 0.62rem; color: rgba(255,255,255,0.4);
  letter-spacing: 0.1em; text-transform: uppercase;
}
.karta-back{
  margin-left:auto;
  padding: 8px 20px; border-radius: 10px;
  background: linear-gradient(135deg, rgba(201,168,76,0.15), rgba(201,168,76,0.08));
  border: 1px solid rgba(201,168,76,0.35);
  color:#fff; font-weight:400; font-size:0.82rem; cursor:pointer;
  text-transform:none;
}
.karta-back:hover{ background: linear-gradient(135deg, rgba(201,168,76,0.24), rgba(201,168,76,0.14)); }

/* дерево */
.tree{ max-width: 760px; }
.node{ margin-bottom: 10px; }

.node-card{
  display:flex; align-items:center; gap:12px;
  padding: 14px 18px;
  border-radius: 14px;
  background: rgba(13,17,23,0.60);
  border: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(16px);
}
.node-unit{
  border-color: rgba(201,168,76,0.55);
  background: linear-gradient(135deg, rgba(201,168,76,0.14), rgba(13,17,23,0.6));
}
.node-icon{ font-size: 1.4rem; }
.node-body{ flex:1; min-width:0; }
.node-label{ font-size: 0.95rem; font-weight: 800; letter-spacing: 0.04em; }
.node-unit .node-label{ color:#c9a84c; }
.node-note{ font-size: 0.62rem; color: rgba(255,255,255,0.45); margin-top:2px; }
.node-kind{
  font-size: 0.55rem; padding: 2px 9px; border-radius: 10px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);
  color: rgba(255,255,255,0.55); text-transform: uppercase; letter-spacing: 0.08em;
  flex-shrink:0;
}
.node-gate{
  font-size: 0.58rem; padding: 3px 11px; border-radius: 10px;
  background: rgba(0,255,136,0.10); border: 1px solid rgba(0,255,136,0.35);
  color: rgba(0,255,136,0.85); cursor: pointer; flex-shrink:0;
  text-transform: none;
}
.node-gate-off{
  font-size: 0.58rem; padding: 3px 11px; border-radius: 10px;
  background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.14);
  color: rgba(255,255,255,0.30); flex-shrink:0;
}

/* ветви — отступ детей */
.children{
  margin-left: 28px; margin-top: 10px;
  padding-left: 18px;
  border-left: 1px solid rgba(201,168,76,0.20);
}
.empty-branch{
  font-size: 0.6rem; color: rgba(255,255,255,0.28);
  padding: 6px 0; font-style: italic;
}

.karta-foot{
  margin-top: 30px; max-width: 760px;
  padding: 12px 16px; border-radius: 10px;
  background: rgba(255,255,255,0.03);
  border: 1px dashed rgba(255,255,255,0.14);
  font-size: 0.62rem; color: rgba(255,255,255,0.4); line-height: 1.6;
}
"""


# ═══════════════════════════════════════════════════════════
# ОТРИСОВКА — рекурсивный обход дерева
# ═══════════════════════════════════════════════════════════

def _render_node(node: dict, is_unit: bool = False):
    card_cls = "node-card node-unit" if is_unit else "node-card"
    gate = node.get("gate")
    note = node.get("note", "")

    with ui.element("div").classes("node"):
        with ui.element("div").classes(card_cls):
            ui.html(f'<span class="node-icon">{node.get("icon","·")}</span>')
            with ui.element("div").classes("node-body"):
                ui.html(f'<div class="node-label">{node.get("label","")}</div>')
                if note:
                    ui.html(f'<div class="node-note">{note}</div>')
            ui.html(f'<span class="node-kind">{node.get("kind","")}</span>')
            if node.get("kind") == "ядро" and node.get("id"):
                # ЖИТЕЛЬ — клик ведёт в его кабинет /zhitel/{id}
                _zid = node.get("id")
                ui.button("открыть →", on_click=lambda z=_zid: ui.navigate.to(f"/zhitel/{z}")) \
                    .props("flat").classes("node-gate")
            elif gate:
                ui.button("войти →", on_click=lambda g=gate: ui.navigate.to(g)) \
                    .props("flat").classes("node-gate")
            else:
                ui.html('<span class="node-gate-off">врата ждут</span>')

        children = node.get("children", [])
        if node.get("kind") in ("единица", "этаж", "квартал", "цех"):
            with ui.element("div").classes("children"):
                if children:
                    for ch in children:
                        _render_node(ch)
                else:
                    ui.html('<div class="empty-branch">— пусто · жители ещё не рождены —</div>')


def page_karta():
    ui.add_head_html(f"<style>{KARTA_CSS}</style>")

    with ui.element("div").classes("karta-root"):
        # шапка
        with ui.element("div").classes("karta-head"):
            ui.html('<div><div class="karta-title">КАРТА ГОРОДА</div>'
                    '<div class="karta-sub">иерархия · зрение Брата</div></div>')
            ui.button("← в кабинет", on_click=lambda: ui.navigate.to("/brat")) \
                .props("flat").classes("karta-back")

        # дерево
        tree = scan_hierarchy()
        with ui.element("div").classes("tree"):
            _render_node(tree, is_unit=True)

        # подвал — живой счётчик: сколько жителей видит Брат
        try:
            _n = len(_scan_zhiteli())
            _foot = (f"⬡ Брат видит <b>{_n}</b> жит. — карта дочитывает их живьём из домов. "
                     f"Клик «открыть →» ведёт в кабинет жителя.<br>"
                     f"Кварталы и врата растут по мере рождения. "
                     f"Брат связывает, но не держит — паспорта живут в домах, не в нём.")
        except Exception:
            _foot = "⬡ Карта — зрение Брата. Жители появляются ветвями по мере рождения."
        ui.html(f'<div class="karta-foot">{_foot}</div>')


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/karta")
    def _karta_page():
        page_karta()
    ui.run(title="Карта города · Грондхейм", port=8102, reload=False)
