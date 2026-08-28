# -*- coding: utf-8 -*-
# STRANICA_CEHA_ODIN_V_ODIN_V1
"""
РАБОЧАЯ СТРАНИЦА ЦЕХА — один в один со старой.

CSS взят из studio/workshop/styles.py (IDENTITY_BUREAU_CSS) ДОСЛОВНО.
Классы, сетка, цвета, размеры — те же: app-container, squad-deck,
avatar, left-col, client-panel, asset-bay, settings-panel,
stage-monitor, stage-toolbar, split-view, chat-log, viewer,
floating-console, right-col, right-top-slot, runs-panel, neon-btn.

Изменён один путь: фон #bg берётся из /studia_media/bg_main.jpg
(положи картинку в GRONDHEIM_CITY/Студия/приёмная/).

Устройство новое: имён цехов внутри нет, всё из манифеста.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from nicegui import ui, app

KOREN = Path(__file__).resolve().parent.parent
STUDIYA = KOREN / "GRONDHEIM_CITY" / "Студия"
KOVCHEG = KOREN / "GRONDHEIM_CITY" / "жители" / "ковчег"

for _put, _url in ((STUDIYA / "приёмная", "/studia_media"),
                   (KOVCHEG, "/kovcheg")):
    try:
        _put.mkdir(parents=True, exist_ok=True)
        app.add_static_files(_url, str(_put))
    except Exception:
        pass

IDENTITY_BUREAU_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

:root{
  --bg: #050510;
  --text: #ffffff;
  --muted: #8899a6;
  --glass: rgba(13, 17, 23, 0.60);
  --stroke: rgba(255,255,255,0.10);
  --g: #00ff88;
  --b: #00ccff;
  --p: #bd00ff;
  --orange: #ff9500;
}

html, body { height: 100%; margin: 0; }
body{
  width:100vw;
  height:100vh;
  overflow:hidden !important;
  background: transparent !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

#bg{
  position: fixed;
  inset: 0;
  z-index: -1;
  background-image: url('/studia_media/bg_main.jpg');
  background-size: cover;
  background-position: center;
}
#bg::after{
  content:'';
  position:absolute;
  inset:0;
  background: radial-gradient(1000px 700px at 20% 10%, rgba(189,0,255,0.12), transparent 60%),
              radial-gradient(900px 650px at 80% 25%, rgba(0,204,255,0.10), transparent 55%),
              rgba(0,0,0,0.40);
  backdrop-filter: blur(10px);
}

.app-container{
  position: fixed;
  inset: 0;
  display: grid;
  width: 100vw;
  height: 100vh;
  grid-template-columns: 300px 1fr 260px;
  grid-template-rows: 80px 1fr;
  grid-template-areas:
    "header header header"
    "left   stage  right";
  gap: 20px;
  padding: 20px;
  box-sizing: border-box;
}

.area-header{ grid-area: header; }
.area-left{ grid-area: left; min-height:0; }
.area-stage{ grid-area: stage; min-height:0; position: relative; overflow: hidden; }
.area-right{ grid-area: right; min-height:0; }

.glass{
  background: var(--glass);
  border: 1px solid var(--stroke);
  border-radius: 20px;
  backdrop-filter: blur(16px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.45);
  min-height: 0;
}

.squad-deck{
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px 16px;
  gap: 15px;
  overflow-x: auto;
}

.avatar{
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 2px solid rgba(255,255,255,0.14);
  background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.16), rgba(255,255,255,0.04));
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  color: rgba(255,255,255,0.92);
  font-weight: 800;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.avatar:hover{ border-color: rgba(0,204,255,0.40); transform: scale(1.05); }
.avatar.active{
  border-color: rgba(0,204,255,0.75);
  box-shadow: 0 0 0 2px rgba(0,204,255,0.25) inset, 0 0 30px rgba(0,204,255,0.35);
}
.avatar.working{
  border-color: rgba(255,149,0,0.75);
  animation: pulse 1.5s ease-in-out infinite;
}
.avatar.done{
  border-color: rgba(0,255,136,0.75);
  box-shadow: 0 0 0 2px rgba(0,255,136,0.25) inset, 0 0 30px rgba(0,255,136,0.35);
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

.left-col{ height: 100%; display: flex; flex-direction: column; gap: 12px; min-height: 0; }

.client-panel{ flex-shrink: 0; overflow: hidden; }
.asset-bay{ height: 120px; flex-shrink: 0; overflow: hidden; }
.settings-panel{ flex-grow: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.panel-title{
  padding: 12px 16px;
  color: rgba(255,255,255,0.92);
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
  font-size: 11px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.panel-body{ padding: 12px 16px; min-height: 0; overflow: auto; }

.setting-row{ margin-bottom: 14px; }
.setting-label{
  color: rgba(255,255,255,0.70);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.file-list{ padding: 8px 12px; max-height: 50px; overflow-y: auto; font-family: monospace; font-size: 11px; }

.right-col{ height: 100%; display: flex; flex-direction: column; justify-content: flex-end; gap: 12px; }
.right-top-slot{
  flex-shrink: 0;
  height: 240px;
  border-radius: 20px;
  border: 1px dashed rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.04);
  display: grid;
  place-items: center;
  color: rgba(255,255,255,0.55);
  font-size: 11px;
  padding: 12px;
  text-align: center;
  overflow: hidden;
}

.runs-panel{
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.runs-list{
  padding: 8px 12px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.run-item{
  padding: 8px 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.run-item:hover{
  background: rgba(0,204,255,0.08);
  border-color: rgba(0,204,255,0.25);
}
.run-item-name{
  font-size: 10px;
  color: rgba(255,255,255,0.75);
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.run-item-delete{
  font-size: 12px;
  cursor: pointer;
  color: rgba(255,255,255,0.3);
  transition: color 0.2s;
  flex-shrink: 0;
}
.run-item-delete:hover{
  color: rgba(255,80,80,0.9);
}

.neon-btn{
  height: 56px;
  width: 100%;
  border-radius: 18px;
  background: transparent;
  color: rgba(255,255,255,0.92);
  border: 1px solid rgba(255,255,255,0.10);
  font-weight: 900;
  letter-spacing: .10em;
  cursor: pointer;
  transition: all 0.3s ease;
}
.neon-btn:disabled{ opacity: 0.4; cursor: not-allowed; }

.neon-btn.g{
  border-color: rgba(0,255,136,0.35);
  background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10));
}
.neon-btn.g:hover:not(:disabled){ background: linear-gradient(135deg, rgba(0,255,136,0.25), rgba(0,204,255,0.15)); }

.neon-btn.b{
  border-color: rgba(0,204,255,0.35);
  background: linear-gradient(135deg, rgba(0,204,255,0.15), rgba(189,0,255,0.10));
}
.neon-btn.b:hover:not(:disabled){ background: linear-gradient(135deg, rgba(0,204,255,0.25), rgba(189,0,255,0.15)); }

.neon-btn.p{
  border-color: rgba(189,0,255,0.35);
  background: linear-gradient(135deg, rgba(189,0,255,0.15), rgba(0,204,255,0.10));
}
.neon-btn.p:hover:not(:disabled){ background: linear-gradient(135deg, rgba(189,0,255,0.25), rgba(0,204,255,0.15)); }

.stage-monitor{ height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.stage-toolbar{
  height: 60px;
  display: grid;
  grid-template-columns: 200px 1fr 200px;
  align-items: center;
  padding: 0 12px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  flex-shrink: 0;
  background: rgba(13, 17, 23, 0.95);
  backdrop-filter: blur(16px);
  z-index: 10;
}

.monitor-utils{ display:flex; gap: 12px; }
.stage-content{
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 18px;
  padding-bottom: 130px;
}

.split-view{ height: 100%; display: flex; gap: 18px; min-height: 0; overflow: hidden; }
.chat-log, .viewer{
  flex: 1;
  min-height: 0;
  min-width: 0;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 14px;
  font-family: monospace;
  font-size: 13px;
  color: rgba(255,255,255,0.86);
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
}
.viewer{ border-color: rgba(0,204,255,0.30); }

.floating-console{
  position: absolute;
  left: 50%;
  bottom: 20px;
  transform: translateX(-50%);
  width: min(820px, calc(100% - 80px));
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 50px;
  background: rgba(13, 17, 23, 0.85);
  border: 1px solid rgba(255,255,255,0.15);
  backdrop-filter: blur(20px);
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}

.floating-console input{
  width: 100%;
  border-radius: 40px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.06);
  padding: 12px 16px;
  color: rgba(255,255,255,0.92);
  outline: none;
  font-family: monospace;
}

.send-button{
  border-radius: 40px !important;
  border: 2px solid rgba(0,204,255,0.55) !important;
  background: linear-gradient(135deg, rgba(0,204,255,0.30), rgba(189,0,255,0.25)) !important;
  color: rgba(255,255,255,0.98) !important;
  font-weight: 900 !important;
  padding: 12px 24px !important;
  cursor: pointer !important;
}

.util-btn {
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  background: rgba(189, 0, 255, 0.15);
  border: 1px solid rgba(189, 0, 255, 0.5);
  color: rgba(189, 0, 255, 1);
  transition: all 0.2s;
}
.util-btn:hover {
  background: rgba(189, 0, 255, 0.25);
}

.chat-msg-user {
  background: rgba(0, 204, 255, 0.1);
  border-left: 3px solid rgba(0, 204, 255, 0.6);
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 0 8px 8px 0;
}
.chat-msg-assistant {
  background: rgba(0, 255, 136, 0.08);
  border-left: 3px solid rgba(0, 255, 136, 0.6);
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 0 8px 8px 0;
}
.chat-msg-system {
  color: rgba(255,255,255,0.5);
  font-style: italic;
  padding: 4px 0;
}

.uploaded-file {
  padding: 6px 10px;
  background: rgba(189,0,255,0.15);
  border: 1px solid rgba(189,0,255,0.3);
  border-radius: 6px;
  margin: 3px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.uploaded-file img {
  max-width: 40px;
  max-height: 40px;
  border-radius: 4px;
  margin-right: 8px;
}

.client-badge{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(0,204,255,0.12);
  border: 1px solid rgba(0,204,255,0.30);
  border-radius: 6px;
  font-size: 10px;
  color: rgba(0,204,255,0.90);
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-top: 6px;
}

/* Белый текст в селектах и инпутах */
.q-field__native,
.q-field__input,
.q-select__dropdown-icon {
  color: rgba(255,255,255,0.9) !important;
}

/* ═══ NUCLEAR ANTI-STRETCH ═══
   NiceGUI/Quasar вставляет wrapper div-ы между элементами.
   Эти правила ловят ВСЕ div-ы внутри stage и не дают им растянуться.
*/
.area-stage { overflow: hidden !important; }
.area-stage > * { overflow: hidden !important; min-height: 0 !important; max-height: 100% !important; }

.stage-monitor { overflow: hidden !important; height: 100% !important; }
.stage-monitor > * { min-height: 0 !important; }

.stage-toolbar { flex-shrink: 0 !important; overflow: hidden !important; }

.stage-content { flex: 1 1 0 !important; min-height: 0 !important; overflow: hidden !important; max-height: calc(100% - 60px) !important; }
.stage-content > * { min-height: 0 !important; max-height: 100% !important; overflow: hidden !important; }

.split-view { height: 100% !important; min-height: 0 !important; overflow: hidden !important; }
.split-view > * { min-height: 0 !important; overflow: hidden !important; }

.chat-log, .viewer {
  flex: 1 1 0 !important;
  min-height: 0 !important;
  max-height: 100% !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* NiceGUI nicegui-content wrapper */
.nicegui-content { overflow: hidden !important; height: 100% !important; }
"""


def _shassi():
    put = STUDIYA / "конвейер.py"
    if not put.exists():
        return None
    spec = importlib.util.spec_from_file_location("_konveyer", put)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _zhitel(ceh: str, slot: str) -> dict:
    """Кто на посту. Страница аватаров не держит — спрашивает город."""
    try:
        if str(KOREN / "ГОРОД") not in sys.path:
            sys.path.insert(0, str(KOREN / "ГОРОД"))
        import rabota
        import rezidenty
        pid = rabota.id_dlya_slota(ceh, slot)
        pasport, dom = rezidenty.lichnost_na_postu(pid)
        if not pasport:
            return {}
        kart = ""
        if dom is not None:
            for f in ("avatar.png", "image.png", "image.jpeg", "avatar.jpg"):
                if (dom / f).exists():
                    kart = f"/kovcheg/{dom.name}/{f}"
                    break
        return {"имя": pasport.get("Official_Name", ""), "картинка": kart}
    except Exception:
        return {}


def _progony(m: dict, skolko: int = 10) -> list:
    put = Path(m["_папка"]) / "журналы" / "прогоны.jsonl"
    if not put.exists():
        return []
    out = []
    for s in put.read_text(encoding="utf-8").splitlines()[-skolko:]:
        try:
            out.append(json.loads(s))
        except Exception:
            pass
    return list(reversed(out))


# стили кнопок панели — как в старой, дословно
_BRIEF = ("padding: 8px 18px; border-radius: 8px; "
          "background: linear-gradient(135deg, rgba(189,0,255,0.15), "
          "rgba(0,204,255,0.10)) !important; "
          "border: 1px solid rgba(189,0,255,0.35); "
          "color: rgba(255,255,255,0.9); font-weight: 700;")
_LOAD = ("padding: 8px 18px; border-radius: 8px; "
         "background: linear-gradient(135deg, rgba(0,204,255,0.15), "
         "rgba(189,0,255,0.10)) !important; "
         "border: 1px solid rgba(0,204,255,0.35); "
         "color: rgba(255,255,255,0.9); font-weight: 700;")
_ASSETS = ("padding: 8px 18px; border-radius: 8px; "
           "background: linear-gradient(135deg, rgba(255,210,0,0.12), "
           "rgba(255,140,0,0.08)) !important; "
           "border: 1px solid rgba(255,210,0,0.30); "
           "color: rgba(255,255,255,0.9); font-weight: 700;")
_CONT = ("padding:6px 14px; border-radius:8px; font-size:0.72rem; "
         "font-weight:700; letter-spacing:0.06em; "
         "border:1px solid rgba(255,210,0,0.35); "
         "color:rgba(255,210,0,0.85); background:rgba(255,210,0,0.07);")
_ZAVOD = ("padding:6px 10px; border-radius:8px; font-size:1rem; "
          "border:1px solid rgba(255,140,0,0.3); "
          "color:rgba(255,140,0,0.8); background:rgba(255,140,0,0.07);")
_KARTR = ("padding:6px 10px; border-radius:8px; font-size:1rem; "
          "border:1px solid rgba(140,108,255,0.3); "
          "color:rgba(140,108,255,0.8); background:rgba(140,108,255,0.07);")
_WORD = ("padding: 8px 14px; border-radius: 8px; "
         "background: linear-gradient(135deg, rgba(0,255,136,0.12), "
         "rgba(0,204,255,0.08)) !important; "
         "border: 1px solid rgba(0,255,136,0.30); "
         "color: rgba(255,255,255,0.85); font-weight: 700; font-size: 12px;")
_PDF = ("padding: 8px 14px; border-radius: 8px; "
        "background: linear-gradient(135deg, rgba(255,149,0,0.12), "
        "rgba(255,80,80,0.08)) !important; "
        "border: 1px solid rgba(255,149,0,0.30); "
        "color: rgba(255,255,255,0.85); font-weight: 700; font-size: 12px;")


def page_studia(ceh_imya: str = "", naryad: str = "") -> None:
    ui.add_head_html("<style>" + IDENTITY_BUREAU_CSS + "</style>")
    ui.html('<div id="bg"></div>')

    K = _shassi()
    if K is None:
        ui.label("Шасси не найдено: GRONDHEIM_CITY/Студия/конвейер.py")
        return
    if not ceh_imya:
        try:
            if str(KOREN / "ГОРОД") not in sys.path:
                sys.path.insert(0, str(KOREN / "ГОРОД"))
            import rabota
            ceha = [k["цех"] for k in rabota.kartridzhi()
                    if k.get("папка_квартала") == "Студия"
                    and k.get("вид") != "контора"]
            ceh_imya = ceha[0] if ceha else ""
        except Exception:
            pass
    try:
        m = K.ceh("Студия", ceh_imya)
        volny = K.truba(m)
    except SystemExit as e:
        ui.label(f"Цех не собрался: {e}").style("color:#ff5050;")
        return

    mesta = [s for v in volny for s in v]
    po_slotu = {s["слот"]: s for s in mesta}

    state: dict[str, Any] = {
        "active_worker": mesta[0]["слот"] if mesta else "",
        "chat_history": {},
        "results": {},
        "sostoyaniya": {},
        "stol": {},
        "pipeline_running": False,
        "master_brief": naryad or "",
        "settings": {"format": "9:16", "duration": 15,
                     "style": "Stylized 3D Realism"},
        "viewer_content": ("# MASTER BRIEF\n\n" + naryad) if naryad
                          else "Waiting for input...",
    }
    avatars_ref: dict = {"elements": {}}
    refs: dict = {}

    # ══════════ РАЗМЕТКА — те же классы, что в старой ══════════
    with ui.element("div").classes("app-container"):

        # ─── HEADER: squad deck ───────────────────────────────
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass squad-deck").style(
                    "display:flex; align-items:center; width:100%; gap:8px; "
                    "padding:0 8px; position:relative;"):
                with ui.element("div").style(
                        "display:flex; align-items:center; gap:6px; "
                        "flex-wrap:wrap; justify-content:center; flex:1;"):
                    for s in mesta:
                        zh = _zhitel(ceh_imya, s["слот"])
                        av = ui.element("div").classes(
                            "avatar" + (" active"
                                        if s["слот"] == state["active_worker"]
                                        else ""))
                        av.on("click",
                              lambda e, w=s["слот"]: switch_worker(w))
                        with av:
                            if zh.get("картинка"):
                                ui.html(
                                    f'<img src="{zh["картинка"]}" '
                                    f'style="position:absolute; inset:0; '
                                    f'width:100%; height:100%; '
                                    f'object-fit:cover; opacity:0.6; '
                                    f'border-radius:12px;">')
                            ui.label(s["слот"]).style(
                                "font-size: 10px; position:relative;")
                        av.tooltip(f'{s["слот"]} · {s.get("роль","")} · '
                                   + (zh.get("имя") or "вакантно"))
                        avatars_ref["elements"][s["слот"]] = av

        # ─── LEFT ─────────────────────────────────────────────
        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):

                with ui.element("div").classes("glass client-panel"):
                    with ui.row().style(
                            "width:100%; justify-content:space-between; "
                            "align-items:center; padding:10px 14px;"):
                        refs["client_badge"] = ui.element("div")
                        with refs["client_badge"]:
                            ui.html('<div class="client-badge">'
                                    '🧪 SANDBOX</div>')
                        ui.button("🧠").props("flat dense").style(
                            "color: rgba(189,0,255,0.8); "
                            "border: 1px solid rgba(189,0,255,0.3); "
                            "border-radius: 6px; min-width: 34px; "
                            "height: 26px; font-size: 14px;").tooltip(
                            "память клиента — второй камень")

                with ui.element("div").classes("glass asset-bay"):
                    with ui.row().style(
                            "width:100%; justify-content:space-between; "
                            "align-items:center; padding:8px 16px 6px 16px; "
                            "border-bottom:1px solid rgba(255,255,255,0.08);"):
                        ui.label("ASSET BAY").style(
                            "color: rgba(255,255,255,0.92); font-weight: 900; "
                            "letter-spacing: .12em; text-transform: uppercase; "
                            "font-size: 11px;")
                        ui.button("CLEAR").props("flat dense size=xs").style(
                            "color: rgba(255,80,80,0.5); font-size: 9px; "
                            "letter-spacing: 0.05em;")
                    refs["files"] = ui.element("div").classes("file-list")
                    with refs["files"]:
                        ui.label("No files").style(
                            "color: rgba(255,255,255,0.4)")

                with ui.element("div").classes("glass settings-panel"):
                    ui.html('<div class="panel-title">PROJECT SETTINGS</div>')
                    with ui.element("div").classes("panel-body"):
                        with ui.element("div").classes("setting-row"):
                            ui.html('<div class="setting-label">'
                                    '📐 Format</div>')
                            ui.select(["9:16", "16:9", "1:1"], value="9:16",
                                      on_change=lambda e:
                                      state["settings"].update(
                                          {"format": e.value})
                                      ).style("width: 100%")
                        with ui.element("div").classes("setting-row"):
                            ui.html('<div class="setting-label">'
                                    '⏱️ Duration (sec)</div>')
                            ui.number(value=15, min=5, max=300,
                                      on_change=lambda e:
                                      state["settings"].update(
                                          {"duration": int(e.value or 30)})
                                      ).style("width: 100%")
                        with ui.element("div").classes("setting-row"):
                            ui.html('<div class="setting-label">'
                                    '🎨 Style</div>')
                            ui.select(["Stylized 3D Realism", "Cinematic",
                                       "Minimalist", "Cyberpunk",
                                       "Documentary", "Commercial"],
                                      value="Stylized 3D Realism",
                                      on_change=lambda e:
                                      state["settings"].update(
                                          {"style": e.value})
                                      ).style("width: 100%")
                        ui.html('<div class="setting-label" '
                                'style="margin-top:14px;">🔧 ТРУБА</div>')
                        refs["truba"] = ui.element("div")

        # ─── STAGE ────────────────────────────────────────────
        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("glass stage-monitor").style(
                    "height:100%; overflow:hidden;"):

                with ui.element("div").classes("stage-toolbar").style(
                        "flex-shrink:0;"):
                    with ui.element("div").style(
                            "display:flex; gap:6px; align-items:center;"):
                        ui.button("📋 BRIEF").props("flat").style(
                            _BRIEF).tooltip("второй камень")
                        ui.button("📂 LOAD").props("flat").style(
                            _LOAD).tooltip("второй камень")
                        ui.button("🗂 ASSETS").props("flat").style(
                            _ASSETS).tooltip("второй камень")
                    with ui.element("div").style(
                            "display:flex; gap:6px; align-items:center; "
                            "justify-content:center;"):
                        ui.button("▶ CONTINUE").props("flat no-caps").style(
                            _CONT).tooltip("третий камень")
                        ui.button("🏭").props("flat").style(
                            _ZAVOD).tooltip("контора: монтаж — третий камень")
                        ui.button("🔌", on_click=lambda: ui.navigate.to(
                            "/ceha", new_tab=True)).props("flat").style(
                            _KARTR).tooltip("Менеджер картриджей")
                    with ui.row().style(
                            "gap: 8px; justify-content: flex-end;"):
                        ui.button("WORD").props("flat").style(
                            _WORD).tooltip("третий камень")
                        ui.button("PDF").props("flat").style(
                            _PDF).tooltip("третий камень")

                with ui.element("div").classes("stage-content").style(
                        "flex:1; min-height:0; overflow:hidden;"):
                    with ui.element("div").classes("split-view").style(
                            "height:100%; min-height:0; overflow:hidden;"):
                        refs["chat"] = ui.element("div").classes(
                            "chat-log").style(
                            "flex:1; min-height:0; overflow-y:auto; "
                            "overflow-x:hidden;")
                        refs["viewer"] = ui.element("div").classes(
                            "viewer").style(
                            "flex:1; min-height:0; overflow-y:auto; "
                            "overflow-x:hidden;")

                with ui.element("div").classes("floating-console"):
                    ui.button("💾").props("flat dense").classes(
                        "util-btn").style("min-width: 40px")
                    ui.button("🗑️", on_click=lambda: clear_chat()).props(
                        "flat dense").classes("util-btn").style(
                        "min-width: 40px")
                    refs["input"] = ui.input(
                        placeholder="Type message...").props(
                        "borderless").style("flex: 1")
                    refs["input"].on("keydown.enter", lambda: send_message())
                    ui.button("SEND", on_click=lambda: send_message()
                              ).classes("send-button")

        # ─── RIGHT ────────────────────────────────────────────
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                refs["status"] = ui.element("div").classes("right-top-slot")
                with ui.element("div").classes("glass runs-panel"):
                    ui.html('<div class="panel-title">📁 RUNS</div>')
                    refs["runs"] = ui.element("div").classes("runs-list")
                refs["full"] = ui.button("⚡ TURBO").classes(
                    "neon-btn g").props("flat")
                refs["from"] = ui.button("▶ FROM CURRENT").classes(
                    "neon-btn b").props("flat")
                refs["anchor"] = ui.button("⚓ ANCHOR").classes(
                    "neon-btn p").props("flat")

    # ══════════ ОБНОВЛЕНИЯ ══════════

    def update_avatar_states():
        for w, av in avatars_ref["elements"].items():
            av.classes(remove="active working done")
            st = state["sostoyaniya"].get(w, {}).get("что")
            if st == "идёт":
                av.classes(add="working")
            elif st == "готово":
                av.classes(add="done")
            if w == state["active_worker"]:
                av.classes(add="active")

    def update_status():
        w = state["active_worker"]
        s = po_slotu.get(w, {})
        zh = _zhitel(ceh_imya, w)
        refs["status"].clear()
        with refs["status"]:
            img = (f'<img src="{zh["картинка"]}" style="width:100%; '
                   f'height:100%; object-fit:cover; border-radius:12px; '
                   f'opacity:0.85;" onerror="this.style.display=\'none\'">'
                   if zh.get("картинка") else "")
            ui.html(f"""
                <div style="position: relative; width: 100%; height: 100%;
                            min-height: 200px;">
                    {img}
                    <div style="position: absolute; bottom: 0; left: 0;
                                right: 0; padding: 15px;
                                background: linear-gradient(transparent,
                                            rgba(0,0,0,0.8));
                                border-radius: 0 0 12px 12px;">
                        <div style="font-size: 0.65rem;
                                    color: rgba(255,255,255,0.5);
                                    letter-spacing: 0.15em;">ACTIVE AGENT</div>
                        <div style="font-size: 1.3rem; font-weight: 700;
                                    color: #00ff88;">{w}</div>
                        <div style="font-size: 0.8rem;
                                    color: rgba(255,255,255,0.8);">
                                    {s.get("роль","")}</div>
                        <div style="font-size: 0.75rem;
                                    color: rgba(0,204,255,0.8);">
                                    {zh.get("имя") or "вакантно"}</div>
                    </div>
                </div>
            """)

    def update_chat_display():
        refs["chat"].clear()
        w = state["active_worker"]
        with refs["chat"]:
            ui.html('<div class="chat-msg-system">SYSTEM: Ready</div>')
            for msg in state["chat_history"].get(w, []):
                kl = ("chat-msg-user" if msg["role"] == "user"
                      else "chat-msg-assistant")
                ui.html(f'<div class="{kl}">{msg["content"]}</div>')

    def update_viewer(content=None):
        if content is not None:
            state["viewer_content"] = content
        refs["viewer"].clear()
        with refs["viewer"]:
            v = state["viewer_content"]
            if isinstance(v, str):
                ui.markdown(v) if v.startswith("#") else ui.html(
                    f'<div style="white-space:pre-wrap;">{v}</div>')
            else:
                ui.code(json.dumps(v, ensure_ascii=False,
                                   indent=2)[:14000]).style("font-size:11px;")

    def update_truba():
        refs["truba"].clear()
        with refs["truba"]:
            for i, volna in enumerate(volny, 1):
                for s in volna:
                    st = state["sostoyaniya"].get(s["слот"], {})
                    cvet = {"идёт": "#ffd200", "готово": "#00ff88",
                            "беда": "#ff5050"}.get(
                        st.get("что"), "rgba(255,255,255,0.45)")
                    hvost = ""
                    if st.get("что") == "готово":
                        hvost = f'  {st.get("сек",0):.0f}s'
                    elif st.get("что") == "идёт":
                        hvost = "  …"
                    znak = "∥" if len(volna) > 1 else " "
                    el = ui.label(f'{i}{znak} {s["слот"]} '
                                  f'{s.get("роль","")}{hvost}')
                    el.style(f"color:{cvet}; font-size:11px; "
                             f"font-family:'JetBrains Mono',monospace; "
                             f"display:block; margin:2px 0; cursor:pointer;")
                    el.on("click", lambda e, w=s["слот"]: switch_worker(w))

    def update_runs_display():
        refs["runs"].clear()
        with refs["runs"]:
            zapisi = _progony(m)
            if not zapisi:
                ui.label("Нет run'ов").style(
                    "color: rgba(255,255,255,0.3); font-size: 11px;")
                return
            for z in zapisi:
                tema = (z.get("наряд") or {}).get("тема", "—")
                sek = sum(x.get("секунд", 0) for x in z.get("места", []))
                with ui.element("div").classes("run-item"):
                    ui.label(f'{z.get("ts","")[5:16]} ({sek:.0f}s)'
                             ).classes("run-item-name").on(
                        "click", lambda e, zz=z: update_viewer(zz))
                    ui.label(tema[:18]).style(
                        "color:rgba(255,255,255,0.35); font-size:10px;")

    def switch_worker(w: str):
        state["active_worker"] = w
        update_avatar_states()
        update_status()
        update_chat_display()
        got = state["results"].get(w)
        if got is not None:
            update_viewer(got)

    def clear_chat():
        state["chat_history"][state["active_worker"]] = []
        update_chat_display()

    async def send_message():
        msg = (refs["input"].value or "").strip()
        if not msg:
            return
        refs["input"].value = ""
        w = state["active_worker"]
        s = po_slotu[w]
        state["chat_history"].setdefault(w, []).append(
            {"role": "user", "content": msg})
        update_chat_display()
        ui.notify(f"Отправлено к {w}...", type="info")
        from llm import chat
        try:
            istoriya = state["chat_history"][w][:-1]
            otvet = await asyncio.to_thread(
                chat, system=K.bumaga(m, s), user=msg,
                knowledge=K.znaniya(m, s), history=istoriya)
        except Exception as e:
            otvet = f"[ошибка] {e}"
        state["chat_history"][w].append(
            {"role": "assistant", "content": otvet})
        update_chat_display()

    async def run_pipeline(from_worker: str = "", with_chat: bool = False):
        if state["pipeline_running"]:
            ui.notify("Пайплайн уже запущен!", type="warning")
            return
        state["pipeline_running"] = True
        for b in ("full", "from", "anchor"):
            refs[b].disable()

        s_volny = 0
        if from_worker:
            if not state["stol"]:
                ui.notify("Стол пуст — сперва полный прогон", type="warning")
                state["pipeline_running"] = False
                for b in ("full", "from", "anchor"):
                    refs[b].enable()
                return
            for i, v in enumerate(volny):
                if any(x["слот"] == from_worker for x in v):
                    s_volny = i
                    break
            stol = dict(state["stol"])
        else:
            stol = {"наряд": {"тема": state["master_brief"] or "проба",
                              "площадка": "YouTube Shorts",
                              "формат": state["settings"]["format"],
                              "длительность": state["settings"]["duration"],
                              "стиль": state["settings"]["style"]}}
            state["sostoyaniya"] = {}
            state["results"] = {}

        from llm import chat
        zhurnal = []
        for nomer in range(s_volny, len(volny)):
            for s in volny[nomer]:
                state["sostoyaniya"][s["слот"]] = {"что": "идёт"}
                update_truba(); update_avatar_states()
                t0 = datetime.now()
                try:
                    vhod = {k: stol.get(k) for k in s.get("берёт", [])}
                    user = ("Вот что тебе пришло:\n\n"
                            + json.dumps(vhod, ensure_ascii=False, indent=2))
                    if with_chat and s["слот"] == from_worker:
                        h = state["chat_history"].get(s["слот"], [])
                        if h:
                            user += ("\n\nИ вот о чём мы говорили:\n"
                                     + "\n".join(f'{x["role"]}: '
                                                 f'{x["content"]}' for x in h))
                    otvet = await asyncio.to_thread(
                        chat, system=K.bumaga(m, s), user=user,
                        knowledge=K.znaniya(m, s))
                    d = K.razobrat(otvet)
                    moyo = d.get("моё", {}) or {}
                    dal, ne_dal = [], []
                    for k in s.get("даёт", []):
                        if k in moyo:
                            stol[k] = moyo[k]
                            dal.append(k)
                        else:
                            ne_dal.append(k)
                    sek = (datetime.now() - t0).total_seconds()
                    state["sostoyaniya"][s["слот"]] = {
                        "что": "готово", "сек": sek, "дал": dal,
                        "не_дал": ne_dal}
                    state["results"][s["слот"]] = moyo or otvet[:4000]
                    zhurnal.append({"слот": s["слот"],
                                    "роль": s.get("роль", ""),
                                    "волна": nomer + 1,
                                    "секунд": round(sek, 1),
                                    "дал": dal, "не_дал": ne_dal,
                                    "знаний": len(s.get("знания", []))})
                    if s["слот"] == state["active_worker"]:
                        update_viewer(moyo or otvet)
                except Exception as e:
                    state["sostoyaniya"][s["слот"]] = {"что": "беда"}
                    zhurnal.append({"слот": s["слот"], "беда": str(e)[:200]})
                    ui.notify(f'{s["слот"]}: {e}', type="negative")
                update_truba(); update_avatar_states()

        state["stol"] = stol
        try:
            K.zapisat(m, stol.get("наряд", {}), stol, zhurnal, False)
        except Exception:
            pass
        d = stol.get("допуск") or {}
        if d.get("статус"):
            ui.notify(f'Приёмка: {d["статус"]}',
                      type="positive" if d["статус"] == "APPROVED"
                      else "warning")
        else:
            ui.notify("Прогон закончен", type="positive")
        update_runs_display()
        state["pipeline_running"] = False
        for b in ("full", "from", "anchor"):
            refs[b].enable()

    refs["full"].on_click(lambda: run_pipeline())
    refs["from"].on_click(lambda: run_pipeline(state["active_worker"]))
    refs["anchor"].on_click(
        lambda: run_pipeline(state["active_worker"], True))

    update_avatar_states()
    update_status()
    update_chat_display()
    update_viewer()
    update_truba()
    update_runs_display()
