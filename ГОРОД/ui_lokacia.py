# ui_lokacia.py
# PATCH_STRANICA_LOKACII — страница локации (сестра кабинета жителя)
"""
ЛОКАЦИЯ — страница места. Route: /lokacia/{lid}
(lid = ID_Object из паспорта, напр. 0006_CREATOR_TOWER)

Локация — НЕДВИЖИМОЕ. Не дышит, нет движка, нет чата, нет памяти.
Поэтому страница — НЕ кабинет с диалогом (как у жителя), а РАСКРЫТЫЙ
ПАСПОРТ: окно показывает место целиком — кто оно, история, что чувствуешь
внутри, район/соцпрофиль, связи, поведение, кто здесь бывает.

ОКНО — то же, что у жителя (ui_zhitel.py): app-container grid, glass,
золото #c9a84c. Чтобы город был ЕДИНЫМ, а не из разных кусков. Разница
только в наполнении: житель дышит (чат+движок), локация покоится (паспорт).

  ЛЕВО  — образ места (картинка) + быстрые факты (район, ранг, ёмкость).
  ЦЕНТР — раскрытый паспорт: история, сенсорика, поведение, связи.
  ПРАВО — соцпрофиль места + сценарии взаимодействия + кто бывает.

Данные: GRONDHEIM_CITY/локации/{id}/passport.json (плоский паспорт).
Картинка места (если есть): та же папка, image.* → /lokacia-static/{id}/image.*

"← Город" → /grondheim (карта).  "← Брат" → /brat.
шесть·проверено·до·корня
"""
import json
from pathlib import Path
from nicegui import ui

_ROOT = Path(__file__).resolve().parent.parent  # файл в ГОРОД/, корень репо — выше
LOKACII_DIR = _ROOT / "GRONDHEIM_CITY" / "локации"


# ═══════════════════════════════════════════════════════════
# НАЙТИ ЛОКАЦИЮ по id (живой скан, как карта — не держим список)
# ═══════════════════════════════════════════════════════════

def find_lokacia(lid: str):
    """Паспорт локации по ID_Object. Возвращает (паспорт, путь_папки) или (None, None)."""
    if not LOKACII_DIR.exists():
        return None, None
    # прямой путь по имени папки
    direct = LOKACII_DIR / lid / "passport.json"
    if direct.exists():
        try:
            return json.loads(direct.read_text(encoding="utf-8")), (LOKACII_DIR / lid)
        except Exception:
            pass
    # перебор (если имя папки ≠ ID_Object)
    for d in LOKACII_DIR.iterdir():
        if not d.is_dir():
            continue
        pf = d / "passport.json"
        if not pf.exists():
            continue
        try:
            p = json.loads(pf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(p.get("ID_Object", "")) == str(lid):
            return p, d
    return None, None


def list_lokacii():
    """Все локации (для выбора, если lid не задан)."""
    out = []
    if not LOKACII_DIR.exists():
        return out
    for d in sorted(LOKACII_DIR.iterdir()):
        if not d.is_dir():
            continue
        pf = d / "passport.json"
        if not pf.exists():
            continue
        try:
            out.append(json.loads(pf.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def _image_url(dom: Path, p: dict) -> str:
    """Картинка места, если лежит в папке локации."""
    if dom is None:
        return ""
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (dom / ("image" + ext)).exists():
            return f"/lokacia-static/{dom.name}/image{ext}"
    return ""


LOKACIA_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
:root{ --bg:#050510; --glass:rgba(13,17,23,0.60); --stroke:rgba(255,255,255,0.10); --gold:#c9a84c; }
html,body{ height:100%; margin:0; }
body{ width:100vw; height:100vh; overflow:hidden !important; background:transparent !important;
  font-family:Inter,system-ui,sans-serif; }
#lbg{ position:fixed; inset:0; z-index:-1; background-size:cover; background-position:center; background-color:#050510; }
#lbg::after{ content:''; position:absolute; inset:0;
  background: radial-gradient(1000px 700px at 20% 10%, rgba(201,168,76,0.10), transparent 60%),
              radial-gradient(900px 650px at 80% 25%, rgba(201,168,76,0.06), transparent 55%),
              rgba(0,0,0,0.50); backdrop-filter:blur(8px); }
.app-container{ position:fixed; inset:0; display:grid; width:100vw; height:100vh;
  grid-template-columns:320px 1fr 300px; grid-template-rows:80px 1fr;
  grid-template-areas:"header header header" "left stage right"; gap:20px; padding:20px; box-sizing:border-box; }
.area-header{ grid-area:header; } .area-left{ grid-area:left; min-height:0; }
.area-stage{ grid-area:stage; min-height:0; position:relative; overflow:hidden; }
.area-right{ grid-area:right; min-height:0; }
.glass{ background:var(--glass); border:1px solid var(--stroke); border-radius:20px;
  backdrop-filter:blur(16px); box-shadow:0 20px 60px rgba(0,0,0,0.45); min-height:0; }
.lhead{ height:100%; display:flex; align-items:center; gap:14px; padding:0 18px; }
.lhead-name{ font-size:1.2rem; font-weight:900; letter-spacing:0.1em; color:var(--gold); }
.lhead-sub{ font-size:0.6rem; color:rgba(255,255,255,0.4); letter-spacing:0.12em; text-transform:uppercase; }
.lback{ padding:8px 20px; border-radius:10px;
  background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08));
  border:1px solid rgba(201,168,76,0.35); color:#fff; font-size:0.82rem; }
.panel-title{ padding:12px 16px; color:rgba(255,255,255,0.92); font-weight:900; letter-spacing:.12em;
  text-transform:uppercase; font-size:11px; border-bottom:1px solid rgba(255,255,255,0.08); }
.left-col,.right-col{ height:100%; display:flex; flex-direction:column; gap:12px; min-height:0; }
.limage{ flex-shrink:0; height:260px; border-radius:20px; border:1px solid rgba(255,255,255,0.10);
  background:rgba(255,255,255,0.04); display:grid; place-items:center; overflow:hidden; position:relative; }
.limage img{ width:100%; height:100%; object-fit:cover; border-radius:19px; }
.limage-cap{ position:absolute; bottom:0; left:0; right:0; padding:12px;
  background:linear-gradient(transparent,rgba(0,0,0,0.85)); }
.limage-cap .nm{ font-size:1.0rem; font-weight:800; color:var(--gold); }
.limage-cap .rl{ font-size:0.55rem; color:rgba(255,255,255,0.55); text-transform:uppercase; letter-spacing:0.08em; }
.facts{ flex:1; min-height:0; overflow:auto; padding:14px 16px; }
.fact{ display:flex; justify-content:space-between; gap:10px; padding:7px 0;
  border-bottom:1px solid rgba(255,255,255,0.06); font-size:0.78rem; }
.fact .k{ color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.06em; font-size:0.62rem; }
.fact .v{ color:rgba(255,255,255,0.92); text-align:right; }
.stage-scroll{ height:100%; overflow-y:auto; padding:22px 26px; }
.stage-scroll h2{ color:var(--gold); font-size:0.7rem; letter-spacing:0.14em; text-transform:uppercase;
  margin:22px 0 8px; font-weight:800; }
.stage-scroll h2:first-child{ margin-top:0; }
.stage-scroll p{ color:rgba(255,255,255,0.86); font-size:0.92rem; line-height:1.6; margin:0 0 6px; }
.stage-scroll .empty{ color:rgba(255,255,255,0.3); font-style:italic; }
.tagrow{ display:flex; flex-wrap:wrap; gap:6px; margin-top:4px; }
.tag{ font-size:0.68rem; padding:3px 10px; border-radius:20px;
  background:rgba(201,168,76,0.10); border:1px solid rgba(201,168,76,0.30); color:rgba(230,210,150,0.95); }
.scripts{ flex:1; min-height:0; overflow:auto; padding:10px 14px; }
.script-item{ font-size:0.8rem; color:rgba(255,255,255,0.82); padding:7px 10px; margin:5px 0;
  border-radius:10px; background:rgba(255,255,255,0.04); border-left:3px solid rgba(201,168,76,0.5); }
.lcore{ padding:12px 16px; font-size:0.72rem; color:rgba(255,255,255,0.6); font-style:italic; line-height:1.5; }
.nicegui-content{ overflow:hidden !important; height:100% !important; }
"""


def _fact(k, v):
    if v is None or v == "" or v == 0:
        return ""
    return f'<div class="fact"><span class="k">{k}</span><span class="v">{v}</span></div>'


def page_lokacia(lid: str = ""):
    p, dom = find_lokacia(lid) if lid else (None, None)

    # статика картинки места
    try:
        from nicegui import app
        if dom is not None and dom.exists():
            app.add_static_files(f"/lokacia-static/{dom.name}", str(dom))
    except Exception:
        pass

    ui.add_head_html(f"<style>{LOKACIA_CSS}</style>")
    ui.html('<div id="lbg"></div>')

    # ── локация не найдена → список выбора ──
    if p is None:
        with ui.element("div").style("position:fixed; inset:0; display:grid; place-items:center;"):
            with ui.element("div").classes("glass").style("padding:30px; max-width:440px;"):
                ui.html('<div class="lhead-name">ЛОКАЦИИ ГРОНДХЕЙМА</div>'
                        '<div class="lhead-sub" style="margin-bottom:16px;">какое место открыть?</div>')
                locs = list_lokacii()
                for z in locs:
                    nm = z.get("Official_Name", "?")
                    zi = z.get("ID_Object", "")
                    if zi == "0000_CITY_GRONDHEIM":
                        continue
                    ui.button(nm, on_click=lambda zi=zi: ui.navigate.to(f"/lokacia/{zi}")) \
                        .props("flat no-caps").style(
                        "width:100%; text-align:left; margin:4px 0; padding:10px 14px; border-radius:10px;"
                        "background:rgba(201,168,76,0.10); border:1px solid rgba(201,168,76,0.30); color:#fff;")
                if not locs:
                    ui.html('<div style="color:rgba(255,255,255,0.4);">— локаций ещё нет — '
                            'роди их в Странице Жизни —</div>')
                ui.button("← Город", on_click=lambda: ui.navigate.to("/grondheim")) \
                    .props("flat").style("margin-top:14px; color:rgba(255,255,255,0.5);")
        return

    name = p.get("Official_Name", "?")
    district = p.get("District", "")
    rank = p.get("Social_Rank", "")
    profession = p.get("Profession", "")
    seal = p.get("Creator_Seal", "")

    # ── ОКНО ──
    with ui.element("div").classes("app-container"):

        # HEADER
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass lhead"):
                _sub = " · ".join(x for x in [district, rank] if x) or "локация"
                ui.html(f'<div><div class="lhead-name">{name}</div>'
                        f'<div class="lhead-sub">{_sub}</div></div>')
                ui.element("div").style("flex:1")
                ui.button("← Город", on_click=lambda: ui.navigate.to("/grondheim")) \
                    .props("flat no-caps").classes("lback").style("margin-right:8px;")
                ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")) \
                    .props("flat no-caps").classes("lback")

        # LEFT — образ места + быстрые факты
        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):
                with ui.element("div").classes("limage"):
                    img = _image_url(dom, p)
                    if img:
                        ui.html(f'<img src="{img}" onerror="this.style.display=\'none\'">')
                    else:
                        ui.html('<div style="font-size:3rem; color:rgba(201,168,76,0.5);">🏛️</div>')
                    ui.html(f'<div class="limage-cap"><div class="nm">{name}</div>'
                            f'<div class="rl">{profession or "место"}</div></div>')
                with ui.element("div").classes("glass").style("flex:1; overflow:hidden; display:flex; flex-direction:column;"):
                    ui.html('<div class="panel-title">факты места</div>')
                    facts_html = "".join([
                        _fact("Район", district),
                        _fact("Ранг", rank),
                        _fact("Доступ", p.get("Access_Level")),
                        _fact("Вмещает", p.get("Capacity")),
                        _fact("Размер", p.get("Scale")),
                        _fact("Свет", p.get("Lighting")),
                        _fact("Редкость", p.get("Rarity")),
                        _fact("ID", p.get("ID_Object")),
                    ])
                    ui.html(f'<div class="facts">{facts_html or "<div class=empty>—</div>"}</div>')

        # STAGE — раскрытый паспорт
        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("glass").style("height:100%; overflow:hidden;"):
                blocks = []

                def block(title, val):
                    if val:
                        safe = str(val).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                        blocks.append(f'<h2>{title}</h2><p>{safe}</p>')

                block("Что это за место", p.get("Visual_Base"))
                block("Особая примета", p.get("Unique_Mark"))
                block("Из чего сделано", p.get("Material_Texture"))
                block("Скрытая история", p.get("Hidden_History"))
                block("Что чувствуешь внутри", p.get("Sensory_Response"))
                block("Как место живёт", p.get("Object_Behavior"))
                block("Зона ответственности", p.get("Area_of_Responsibility"))
                block("Связь с миром", p.get("Domain_Connection"))
                block("С кем связано", p.get("Relationships"))

                # теги стиля
                tags = p.get("Style_Tags", "")
                tags_html = ""
                if tags:
                    items = [t.strip() for t in str(tags).replace(",", " ").split() if t.strip()]
                    if items:
                        chips = "".join(f'<span class="tag">{t}</span>' for t in items)
                        tags_html = f'<h2>Атмосфера</h2><div class="tagrow">{chips}</div>'

                body = "".join(blocks) + tags_html
                if not body:
                    body = '<p class="empty">Паспорт пуст — место ещё не описано.</p>'
                if seal:
                    body += f'<h2>Печать создателя</h2><p style="color:var(--gold);font-style:italic;">«{seal}»</p>'

                ui.html(f'<div class="stage-scroll">{body}</div>')

        # RIGHT — сценарии + связи + кто бывает
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                # сценарии взаимодействия
                with ui.element("div").classes("glass").style("flex:1; overflow:hidden; display:flex; flex-direction:column;"):
                    ui.html('<div class="panel-title">что здесь делают</div>')
                    scripts = p.get("Interaction_Scripts", [])
                    if isinstance(scripts, str):
                        scripts = [s.strip() for s in scripts.split(",") if s.strip()]
                    if scripts:
                        items = "".join(f'<div class="script-item">{str(s)}</div>' for s in scripts)
                        ui.html(f'<div class="scripts">{items}</div>')
                    else:
                        ui.html('<div class="scripts"><div style="opacity:0.4;font-size:0.75rem;">— сценариев нет —</div></div>')

                # соседние места
                with ui.element("div").classes("glass").style("flex-shrink:0;"):
                    ui.html('<div class="panel-title">соседние места</div>')
                    conns = p.get("Location_Connections", "")
                    if conns:
                        ui.html(f'<div class="lcore" style="font-style:normal;">{conns}</div>')
                    else:
                        ui.html('<div class="lcore">— связи не указаны —</div>')

                # кто здесь бывает (задел: пока жители не привязаны к локации)
                with ui.element("div").classes("glass").style("flex-shrink:0;"):
                    ui.html('<div class="panel-title">кто здесь бывает</div>')
                    ui.html('<div class="lcore" style="opacity:0.6;">— пока никто не прописан сюда —<br>'
                            'появятся, когда жители получат прописку в этом месте</div>')


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/lokacia/{lid}")
    def _l(lid: str = ""):
        page_lokacia(lid)
    @ui.page("/lokacia")
    def _l0():
        page_lokacia("")
    ui.run(title="Локация · Грондхейм", port=8105, reload=False)
