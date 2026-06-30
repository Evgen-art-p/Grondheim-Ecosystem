# ui_grondheim.py
# PATCH_KARTA_ZERKALO — карта-зеркало: читает паспорта локаций из папки
"""
ГОРОД — визуальная карта Грондхейма. Route: /grondheim.

КАРТА = ЗЕРКАЛО ДАННЫХ. Читает паспорта из GRONDHEIM_CITY/локации/{id}/
passport.json и рисует КАЖДУЮ локацию своим прямоугольником по
Map_X/Y/W/H. Сколько локаций родил в Странице Жизни — столько на карте.
Никаких зашитых зон в коде (раньше были три прямоугольника-района —
убраны: район это область, а кликается реальный объект-локация).

КЛИК по любому прямоугольнику -> ведёт В саму локацию (emitEvent
'grond-open' с id локации). Все локации — реальные объекты с паспортами:
Студия -> Студия, Биржа -> Биржа, Высотка -> Высотка.

МЕХАНИКА drag+zoom — КАЛЬКА рабочей карты старого кабинета (-2):
<script> в body (НЕ ui.run_javascript), фикс. scale=0.55, ожидание DOM
через setTimeout, клик через emitEvent. Проверено живьём в -2.

Картинка: /karta_static/grondheim.png (2761x1504), маршрут /karta_static
регистрирует main.py на ГОРОД/static/.

"<- назад" -> /brat.
шесть·проверено·до·корня
"""
import json
from pathlib import Path
from nicegui import ui

# ── Источник данных: папка локаций (от корня запуска = корень репо) ──
LOKACII_DIR = Path("GRONDHEIM_CITY/локации")

# Картинка-фон города и её натуральный размер (сетка координат паспортов)
CITY_IMAGE = "/karta_static/grondheim.png"
CITY_W = 2761
CITY_H = 1504

# Город целиком (0000) — не рисуем прямоугольником, он сам весь холст
CITY_SELF_ID = "0000_CITY_GRONDHEIM"


def load_locations() -> list:
    """Скан папки локаций -> список словарей для карты.

    Пропускаем: сам город (0000, он весь холст) и локации без вменяемых
    координат (w/h меньше 10px — рисовать нечего). Остальное — на карту,
    каждая своим прямоугольником из Map_X/Y/W/H.
    """
    out = []
    if not LOKACII_DIR.exists():
        return out
    for d in sorted(LOKACII_DIR.iterdir()):
        if not d.is_dir():
            continue
        p = d / "passport.json"
        if not p.exists():
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        lid = obj.get("ID_Object", d.name)
        if lid == CITY_SELF_ID:
            continue
        try:
            x = int(obj.get("Map_X", 0)); y = int(obj.get("Map_Y", 0))
            w = int(obj.get("Map_W", 0)); h = int(obj.get("Map_H", 0))
        except (ValueError, TypeError):
            continue
        if w < 10 or h < 10:
            continue
        out.append({
            "id": lid,
            "name": obj.get("Official_Name", lid),
            "x": x, "y": y, "w": w, "h": h,
        })
    return out


GRONDHEIM_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

.grond-root{
  position: fixed; inset: 0;
  background: #050508;
  font-family: Inter, system-ui, sans-serif;
  color: #fff;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.grond-header{
  padding: 14px 22px;
  display: flex; align-items: center; gap: 18px;
  background: linear-gradient(to bottom, rgba(5,5,16,0.92), rgba(5,5,16,0.4) 70%, transparent);
  flex-shrink: 0; z-index: 5;
}
.grond-title{ font-size: 1.15rem; font-weight: 900; letter-spacing: 0.14em; color: #c9a84c; }
.grond-sub{ font-size: 0.6rem; color: rgba(255,255,255,0.4); letter-spacing: 0.1em; text-transform: uppercase; }
.grond-back{
  margin-left: auto;
  padding: 7px 18px; border-radius: 10px;
  background: linear-gradient(135deg, rgba(201,168,76,0.16), rgba(201,168,76,0.08));
  border: 1px solid rgba(201,168,76,0.35);
  color:#fff; font-weight:400; font-size:0.78rem; cursor:pointer; text-transform:none;
}
.grond-back:hover{ background: linear-gradient(135deg, rgba(201,168,76,0.26), rgba(201,168,76,0.15)); }

.grond-viewport{
  flex: 1; overflow: hidden;
  cursor: grab; user-select: none; touch-action: none;
  position: relative;
}
.grond-viewport:active{ cursor: grabbing; }

.grond-canvas{
  position: absolute; top: 0; left: 0;
  transform-origin: 0 0;
  background-color: #050508;
  background-repeat: no-repeat;
  background-position: 0 0;
}

.grond-sector{
  position: absolute; border-radius: 8px;
  border: 2px solid rgba(0,140,160,0.9);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem; font-weight: 700;
  letter-spacing: 0.1em; text-transform: uppercase;
  padding: 8px 14px;
  background: transparent;
  color: rgba(160,220,230,0.95);
  text-shadow: 0 1px 4px rgba(0,0,0,0.95);
  box-sizing: border-box;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  overflow: hidden;
}
.grond-sector:hover{
  border-color: rgba(0,220,240,1);
  background: rgba(0,140,160,0.12);
}

.grond-hint{
  position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
  font-size: 0.58rem; color: rgba(255,255,255,0.32);
  letter-spacing: 0.08em; text-transform: uppercase;
  pointer-events: none; z-index: 5;
}
.grond-empty{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  font-size: 0.85rem; color: rgba(255,255,255,0.5);
  letter-spacing: 0.06em; text-align: center; pointer-events: none; z-index: 5;
}
"""

GRONDHEIM_JS = """
<script>
function initGrondMap() {
  const vp = document.querySelector('.grond-viewport');
  if(!vp) { setTimeout(initGrondMap, 100); return; }

  let scale=0.55, pos={x:0,y:0}, dragging=false, dragStart={x:0,y:0};

  function applyTransform(){
    const c=vp.querySelector('.grond-canvas');
    if(c) c.style.transform=`translate(${pos.x}px,${pos.y}px) scale(${scale})`;
  }

  vp.addEventListener('wheel',e=>{
    e.preventDefault();
    const s=e.deltaY*-0.001;
    let ns=Math.min(Math.max(0.15,scale+s),2.5);
    if(ns===scale) return;
    const r=vp.getBoundingClientRect();
    const mx=e.clientX-r.left, my=e.clientY-r.top;
    pos.x=mx-((mx-pos.x)*(ns/scale));
    pos.y=my-((my-pos.y)*(ns/scale));
    scale=ns; applyTransform();
  },{passive:false});

  vp.addEventListener('pointerdown',e=>{
    if(e.target.closest('.grond-sector')) return;
    dragging=true;
    dragStart={x:e.clientX-pos.x,y:e.clientY-pos.y};
    vp.setPointerCapture(e.pointerId);
  });

  window.addEventListener('pointermove',e=>{
    if(!dragging) return;
    pos.x=e.clientX-dragStart.x; pos.y=e.clientY-dragStart.y;
    applyTransform();
  });

  window.addEventListener('pointerup',()=>{ dragging=false; });

  const r=vp.getBoundingClientRect();
  const c=vp.querySelector('.grond-canvas');
  if(c){
    const cw=parseFloat(c.style.width)||c.offsetWidth;
    const ch=parseFloat(c.style.height)||c.offsetHeight;
    pos.x=(r.width - cw*scale)/2;
    pos.y=(r.height - ch*scale)/2;
  }
  applyTransform();

  window.grondOpen = function(locId){ emitEvent('grond-open', locId); };
}

window.grondReinit = function(){ setTimeout(initGrondMap, 80); };

if(document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGrondMap);
} else {
  setTimeout(initGrondMap, 200);
}
</script>
"""


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "\\'"))


def _canvas_html(locations: list) -> str:
    sectors = ""
    for loc in locations:
        sectors += (
            '<div class="grond-sector" onclick="window.grondOpen && window.grondOpen(\'%s\')" '
            'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;">%s</div>'
            % (_esc(loc["id"]), loc["x"], loc["y"], loc["w"], loc["h"], _esc(loc["name"]))
        )
    empty = ""
    if not locations:
        empty = ('<div class="grond-empty">Локаций пока нет.<br>'
                 'Роди их в Странице Жизни — появятся на карте.</div>')
    return (
        '<div class="grond-canvas" style="width:%dpx;height:%dpx;'
        'background-image:url(\'%s\');background-size:%dpx %dpx;">%s</div>%s'
        % (CITY_W, CITY_H, CITY_IMAGE, CITY_W, CITY_H, sectors, empty)
    )


def page_grondheim():
    ui.add_head_html(f"<style>{GRONDHEIM_CSS}</style>")
    root_ref = {}

    def render():
        root_ref["el"].clear()
        locations = load_locations()
        with root_ref["el"]:
            with ui.element("div").classes("grond-header"):
                ui.html(
                    f'<div><div class="grond-title">ГРОНДХЕЙМ</div>'
                    f'<div class="grond-sub">зрение Брата · {len(locations)} локаций</div></div>'
                )
                ui.button("← назад", on_click=lambda: ui.navigate.to("/brat")) \
                    .props("flat").classes("grond-back")

            with ui.element("div").classes("grond-viewport"):
                ui.html(_canvas_html(locations))

            ui.html('<div class="grond-hint">колесо — масштаб · перетаскивание — обзор · клик — войти в локацию</div>')

    with ui.element("div").classes("grond-root") as root:
        root_ref["el"] = root
        render()

    ui.add_body_html(GRONDHEIM_JS)

    def on_open(e):
        loc_id = e.args
        if loc_id:
            # клик по локации -> открыть её страницу (ui_lokacia.py)
            ui.navigate.to(f"/lokacia/{loc_id}")

    ui.on("grond-open", on_open)


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/grondheim")
    def _grondheim_page():
        page_grondheim()
    ui.run(title="Город · Грондхейм", port=8103, reload=False)
