# ui_grondheim.py
# PATCH_GRONDHEIM_VISUAL_MAP — визуальная карта города (зрение Брата, образ)
"""
ГОРОД — визуальная карта Грондхейма. Route: /grondheim.

Устройство канваса — калька старого кабинета студии (-2, ui_cabinet.py):
drag+zoom через чистый JS, локации — абсолютные прямоугольники на картинке,
координаты — пиксель в пиксель с art-макетом (Map_X/Y/W/H).

ДВЕ СЦЕНЫ (дерево сцен, не один бесконечный canvas):
  СЦЕНА 1 "grondheim"   — общая карта города (grondheim.png, 2761×1504)
                           Храмовый комплекс  → клик → сцена "hram"
                           Деловой центр      → плоский, без перехода
                           Портовый узел      → плоский, без перехода
  СЦЕНА 2 "hram"        — храмовый комплекс (hram_kompleks.png, 2760×1504)
                           Гексагон → лист, без перехода
                           Ковчег   → лист, без перехода

Локация = недвижимое. Координата живёт в ПАСПОРТЕ локации (здесь как данные
сцены), не в жителе и не в маске. Маска (роль) и локация (место) — разные
оси, не сцеплены. Житель к этой карте пока не привязан — это шаг отдельный
(через sensory_memory, последнее перемещение), не сегодня.

Кнопки внутри карты — минимум навигации, не функционал:
  "← назад"  со сцены "hram" → сцена "grondheim"
  "← назад"  со сцены "grondheim" → /brat (кабинет Брата)

Палитра и устройство стиля — по образцу ui_brat.py / ui_karta.py
(золото #c9a84c, glass, тёмный фон).
`шесть·проверено·до·корня`
"""
from nicegui import ui

# ═══════════════════════════════════════════════════════════
# ДАННЫЕ СЦЕН — координаты локаций (пиксель в пиксель с картинкой)
# ═══════════════════════════════════════════════════════════

SCENES = {
    "grondheim": {
        "image": "/karta_static/grondheim.png",
        "width": 2761,
        "height": 1504,
        "title": "ГРОНДХЕЙМ",
        "back_to": "/brat",
        "locations": [
            {
                "id": "temple_complex",
                "label": "Храмовый комплекс",
                "x": 114, "y": 148, "w": 2481, "h": 1190,
                "goto_scene": "hram",
            },
            {
                "id": "business_center",
                "label": "Деловой центр",
                "x": 0, "y": 0, "w": 2760, "h": 245,
                "goto_scene": None,
            },
            {
                "id": "port_node",
                "label": "Портовый узел",
                "x": 0, "y": 331, "w": 2760, "h": 1173,
                "goto_scene": None,
            },
        ],
    },
    "hram": {
        "image": "/karta_static/hram_kompleks.png",
        "width": 2760,
        "height": 1504,
        "title": "ХРАМОВЫЙ КОМПЛЕКС",
        "back_to": "grondheim",  # имя сцены — переход внутри карты, не URL
        "locations": [
            {
                "id": "hexagon",
                "label": "Гексагон",
                "x": 413, "y": 299, "w": 1008, "h": 726,
                "goto_scene": None,
            },
            {
                "id": "ark",
                "label": "Ковчег",
                "x": 1624, "y": 299, "w": 791, "h": 726,
                "goto_scene": None,
            },
        ],
    },
}

DEFAULT_SCENE = "grondheim"


# ═══════════════════════════════════════════════════════════
# СТИЛИ
# ═══════════════════════════════════════════════════════════

GRONDHEIM_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');

.grond-root{
  position: fixed; inset: 0;
  background: #050510;
  font-family: Inter, system-ui, sans-serif;
  color: #fff;
  overflow: hidden;
}

.grond-head{
  position: absolute; top: 0; left: 0; right: 0; z-index: 5;
  display:flex; align-items:center; gap:16px;
  padding: 18px 24px;
  background: linear-gradient(to bottom, rgba(5,5,16,0.85), transparent);
  pointer-events: none;
}
.grond-head > *{ pointer-events: auto; }
.grond-title{
  font-size: 1.1rem; font-weight: 900; letter-spacing: 0.14em;
  color: #c9a84c;
}
.grond-sub{
  font-size: 0.6rem; color: rgba(255,255,255,0.4);
  letter-spacing: 0.1em; text-transform: uppercase;
}
.grond-back{
  padding: 7px 18px; border-radius: 10px;
  background: linear-gradient(135deg, rgba(201,168,76,0.16), rgba(201,168,76,0.08));
  border: 1px solid rgba(201,168,76,0.35);
  color:#fff; font-weight:400; font-size:0.78rem; cursor:pointer;
  text-transform:none;
}
.grond-back:hover{ background: linear-gradient(135deg, rgba(201,168,76,0.26), rgba(201,168,76,0.15)); }

/* вьюпорт — окно, в котором двигается полотно */
.grond-viewport{
  position: absolute; inset: 0;
  overflow: hidden;
  cursor: grab;
  touch-action: none;
}
.grond-viewport.dragging{ cursor: grabbing; }

/* полотно — фиксированный размер картинки, двигается transform'ом */
.grond-canvas{
  position: absolute; top: 0; left: 0;
  transform-origin: 0 0;
  background-size: cover;
  background-repeat: no-repeat;
}

/* сектор-локация — абсолютный прямоугольник на полотне */
.grond-sector{
  position: absolute;
  border: 1px solid rgba(201,168,76,0.45);
  background: rgba(201,168,76,0.04);
  border-radius: 4px;
  display:flex; align-items:flex-start; justify-content:flex-start;
  padding: 10px 14px;
  box-sizing: border-box;
  transition: background 0.15s, border-color 0.15s;
}
.grond-sector.clickable{
  cursor: pointer;
  pointer-events: auto;
}
.grond-sector.clickable:hover{
  background: rgba(201,168,76,0.13);
  border-color: rgba(201,168,76,0.85);
}
.grond-sector.flat{
  pointer-events: none;
}
.grond-sector-label{
  font-size: 13px; font-weight: 700; letter-spacing: 0.04em;
  color: rgba(255,255,255,0.85);
  text-shadow: 0 1px 4px rgba(0,0,0,0.8);
  white-space: nowrap;
}

/* подсказка масштаба — низ экрана */
.grond-hint{
  position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%);
  z-index: 5;
  font-size: 0.6rem; color: rgba(255,255,255,0.35);
  letter-spacing: 0.06em; text-transform: uppercase;
  pointer-events: none;
}
"""


# ═══════════════════════════════════════════════════════════
# ОТРИСОВКА
# ═══════════════════════════════════════════════════════════

def _render_scene(scene_key: str, container_id: str):
    scene = SCENES[scene_key]

    sectors_html = ""
    for loc in scene["locations"]:
        clickable = bool(loc.get("goto_scene"))
        cls = "grond-sector clickable" if clickable else "grond-sector flat"
        onclick = (
            f' onclick="window.__grondGoto && window.__grondGoto(\'{loc["goto_scene"]}\')"'
            if clickable else ""
        )
        sectors_html += (
            f'<div class="{cls}" data-loc-id="{loc["id"]}"{onclick} '
            f'style="left:{loc["x"]}px; top:{loc["y"]}px; '
            f'width:{loc["w"]}px; height:{loc["h"]}px;">'
            f'<span class="grond-sector-label">{loc["label"]}</span>'
            f'</div>'
        )

    canvas_html = (
        f'<div class="grond-canvas" id="{container_id}_canvas" '
        f'style="width:{scene["width"]}px; height:{scene["height"]}px; '
        f'background-image:url(\'{scene["image"]}\');">'
        f'{sectors_html}'
        f'</div>'
    )

    ui.html(canvas_html)


def _viewport_script(container_id: str, scene_width: int, scene_height: int):
    """JS drag + zoom — по устройству старого cab-map-viewport (-2)."""
    ui.run_javascript(f"""
        (function() {{
            const vp = document.getElementById('{container_id}_viewport');
            const canvas = document.getElementById('{container_id}_canvas');
            if (!vp || !canvas) return;

            const sceneW = {scene_width}, sceneH = {scene_height};

            function fitScale() {{
                const r = vp.getBoundingClientRect();
                const sx = r.width / sceneW, sy = r.height / sceneH;
                return Math.min(sx, sy, 1) * 0.96;
            }}

            let scale = fitScale();
            let tx = (vp.getBoundingClientRect().width  - sceneW * scale) / 2;
            let ty = (vp.getBoundingClientRect().height - sceneH * scale) / 2;

            function apply() {{
                canvas.style.transform =
                    `translate(${{tx}}px, ${{ty}}px) scale(${{scale}})`;
            }}
            apply();

            let dragging = false, lastX = 0, lastY = 0;

            vp.addEventListener('pointerdown', (e) => {{
                if (e.target.closest('.grond-sector.clickable')) return;
                dragging = true; lastX = e.clientX; lastY = e.clientY;
                vp.classList.add('dragging');
                vp.setPointerCapture(e.pointerId);
            }});
            vp.addEventListener('pointermove', (e) => {{
                if (!dragging) return;
                tx += e.clientX - lastX; ty += e.clientY - lastY;
                lastX = e.clientX; lastY = e.clientY;
                apply();
            }});
            vp.addEventListener('pointerup', () => {{
                dragging = false; vp.classList.remove('dragging');
            }});
            vp.addEventListener('pointercancel', () => {{
                dragging = false; vp.classList.remove('dragging');
            }});

            vp.addEventListener('wheel', (e) => {{
                e.preventDefault();
                const r = vp.getBoundingClientRect();
                const mx = e.clientX - r.left, my = e.clientY - r.top;
                const old = scale;
                const factor = e.deltaY < 0 ? 1.12 : 0.89;
                scale = Math.min(2.5, Math.max(0.15, scale * factor));
                tx = mx - (mx - tx) * (scale / old);
                ty = my - (my - ty) * (scale / old);
                apply();
            }}, {{ passive: false }});
        }})();
    """)


def _goto_scene_script(view_state_holder):
    """Регистрирует window.__grondGoto — клик по кликабельному сектору
    шлёт событие в NiceGUI без отдельной кнопки."""
    ui.run_javascript("""
        window.__grondGoto = function(sceneKey) {
            window.dispatchEvent(new CustomEvent('grond-goto', {detail: sceneKey}));
        };
    """)


def page_grondheim():
    ui.add_head_html(f"<style>{GRONDHEIM_CSS}</style>")

    state = {"scene": DEFAULT_SCENE}
    root_ref = {}

    def render():
        root_ref["el"].clear()
        scene_key = state["scene"]
        scene = SCENES[scene_key]
        container_id = f"grond_{scene_key}"

        with root_ref["el"]:
            # шапка
            with ui.element("div").classes("grond-head"):
                ui.html(
                    f'<div><div class="grond-title">{scene["title"]}</div>'
                    f'<div class="grond-sub">зрение Брата · карта</div></div>'
                )

                def go_back():
                    bt = scene["back_to"]
                    if bt in SCENES:
                        state["scene"] = bt
                        render()
                    else:
                        ui.navigate.to(bt)

                ui.button("← назад", on_click=go_back).props("flat").classes("grond-back")

            # вьюпорт + полотно
            with ui.element("div").classes("grond-viewport").props(
                f'id="{container_id}_viewport"'
            ):
                _render_scene(scene_key, container_id)

            ui.html('<div class="grond-hint">колесо — масштаб · перетаскивание — обзор</div>')

        _viewport_script(container_id, scene["width"], scene["height"])
        _goto_scene_script(state)

    with ui.element("div").classes("grond-root") as root:
        root_ref["el"] = root
        render()

    def on_goto(e):
        target = e.args
        if target and target in SCENES:
            state["scene"] = target
            render()

    ui.on("grond-goto", on_goto)


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/grondheim")
    def _grondheim_page():
        page_grondheim()
    ui.run(title="Город · Грондхейм", port=8103, reload=False)
