# ui_grondheim.py
# PATCH_GRONDHEIM_VISUAL_MAP — визуальная карта города (ГОРОД, зрение Брата)
"""
ГОРОД — визуальная карта Грондхейма. Route: /grondheim.

МЕХАНИКА — ТОЧНАЯ КАЛЬКА рабочей карты старого кабинета студии (-2,
ui_cabinet.py + css.py): cab-map-viewport / cab-map-canvas / cab-map-sector,
drag+zoom через <script> в body (НЕ ui.run_javascript), фикс. стартовый
scale=0.55, ожидание DOM через setTimeout. Проверено живьём в -2 —
механику не переписываю, только данные мои (две сцены).

ДВЕ СЦЕНЫ (переключаются без перезагрузки страницы):
  СЦЕНА 1 "grondheim"  — общая карта (grondheim.png, 2761x1504)
      Храмовый комплекс -> клик -> сцена "hram"
      Деловой центр, Портовый узел -> плоские
  СЦЕНА 2 "hram"       — храмовый комплекс (hram_kompleks.png, 2760x1504)
      Гексагон, Ковчег -> листья

Картинки: /karta_static/grondheim.png, /karta_static/hram_kompleks.png
(маршрут /karta_static регистрирует main.py на ГОРОД/static/).

"<- назад": со сцены "hram" -> "grondheim"; со сцены "grondheim" -> /brat.
шесть·проверено·до·корня
"""
from nicegui import ui

SCENES = {
    "grondheim": {
        "image": "/karta_static/grondheim.png",
        "width": 2761, "height": 1504,
        "title": "ГРОНДХЕЙМ", "back_to": "/brat",
        "locations": [
            {"id": "temple_complex", "name": "Храмовый комплекс",
             "x": 114, "y": 148, "w": 2481, "h": 1190, "goto": "hram"},
            {"id": "business_center", "name": "Деловой центр",
             "x": 0, "y": 0, "w": 2760, "h": 245, "goto": None},
            {"id": "port_node", "name": "Портовый узел",
             "x": 0, "y": 331, "w": 2760, "h": 1173, "goto": None},
        ],
    },
    "hram": {
        "image": "/karta_static/hram_kompleks.png",
        "width": 2760, "height": 1504,
        "title": "ХРАМОВЫЙ КОМПЛЕКС", "back_to": "grondheim",
        "locations": [
            {"id": "hexagon", "name": "Гексагон",
             "x": 413, "y": 299, "w": 1008, "h": 726, "goto": None},
            {"id": "ark", "name": "Ковчег",
             "x": 1624, "y": 299, "w": 791, "h": 726, "goto": None},
        ],
    },
}

DEFAULT_SCENE = "grondheim"

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
  transition: border-color 0.15s, background 0.15s;
}
.grond-sector.clickable{ cursor: pointer; }
.grond-sector.clickable:hover{
  border-color: rgba(0,220,240,1);
  background: rgba(0,140,160,0.12);
}

.grond-hint{
  position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
  font-size: 0.58rem; color: rgba(255,255,255,0.32);
  letter-spacing: 0.08em; text-transform: uppercase;
  pointer-events: none; z-index: 5;
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
    if(e.target.closest('.grond-sector.clickable')) return;
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

  window.grondGoto = function(sceneKey){ emitEvent('grond-goto', sceneKey); };
}

window.grondReinit = function(){ setTimeout(initGrondMap, 80); };

if(document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGrondMap);
} else {
  setTimeout(initGrondMap, 200);
}
</script>
"""


def _canvas_html(scene: dict) -> str:
    sectors = ""
    for loc in scene["locations"]:
        clickable = bool(loc.get("goto"))
        cls = "grond-sector clickable" if clickable else "grond-sector"
        onclick = (" onclick=\"window.grondGoto && window.grondGoto('%s')\"" % loc["goto"]
                   if clickable else "")
        sectors += (
            '<div class="%s"%s style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;">%s</div>'
            % (cls, onclick, loc["x"], loc["y"], loc["w"], loc["h"], loc["name"])
        )
    return (
        '<div class="grond-canvas" style="width:%dpx;height:%dpx;'
        'background-image:url(\'%s\');background-size:%dpx %dpx;">%s</div>'
        % (scene["width"], scene["height"], scene["image"],
           scene["width"], scene["height"], sectors)
    )


def page_grondheim():
    ui.add_head_html(f"<style>{GRONDHEIM_CSS}</style>")

    state = {"scene": DEFAULT_SCENE}
    root_ref = {}

    def render():
        root_ref["el"].clear()
        scene = SCENES[state["scene"]]

        with root_ref["el"]:
            with ui.element("div").classes("grond-header"):
                ui.html(
                    f'<div><div class="grond-title">{scene["title"]}</div>'
                    f'<div class="grond-sub">зрение Брата · карта</div></div>'
                )

                def go_back():
                    bt = scene["back_to"]
                    if bt in SCENES:
                        state["scene"] = bt
                        render()
                        ui.run_javascript("if(window.grondReinit) window.grondReinit();")
                    else:
                        ui.navigate.to(bt)

                ui.button("← назад", on_click=go_back).props("flat").classes("grond-back")

            with ui.element("div").classes("grond-viewport"):
                ui.html(_canvas_html(scene))

            ui.html('<div class="grond-hint">колесо — масштаб · перетаскивание — обзор</div>')

    with ui.element("div").classes("grond-root") as root:
        root_ref["el"] = root
        render()

    ui.add_body_html(GRONDHEIM_JS)

    def on_goto(e):
        target = e.args
        if target and target in SCENES:
            state["scene"] = target
            render()
            ui.run_javascript("if(window.grondReinit) window.grondReinit();")

    ui.on("grond-goto", on_goto)


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/grondheim")
    def _grondheim_page():
        page_grondheim()
    ui.run(title="Город · Грондхейм", port=8103, reload=False)
