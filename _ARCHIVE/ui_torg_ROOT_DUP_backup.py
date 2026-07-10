# -*- coding: utf-8 -*-
# TORG_STOL_V2 — реальный CSS воркшопа (IDENTITY_BUREAU_CSS), фон Биржи
"""
СТОЛ ЦЕХА · /torg/{tseh_id}

Визуал — ОДИН В ОДИН старый /exchange: перенесён настоящий
IDENTITY_BUREAU_CSS (studio/workshop/styles.py), тот самый выстраданный
стиль. Классы: app-container, squad-deck, avatar, asset-bay,
stage-monitor, split-view, chat-log, viewer, floating-console, neon-btn.
Фон — локация Биржи (0014_EXCHANGE/image.*), не bg_main.

Данные — через Закон Пары (list_nositeli), НЕ захардкоженный список.
Кнопка РЫНОК — реальная Калибровка. Живой чат/Вильямс/ордера — след. камни.
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from nicegui import ui, app

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
for _p in (_REPO, _HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cartridge_registry as reg
import kalibrovka as kal

CITY = _REPO / "GRONDHEIM_CITY"


def _read_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def _avatar_url_for(papka, static_prefix):
    dom = Path(papka)
    p = _read_json(dom / "passport.json") or {}
    av = p.get("avatar", "")
    if av and (dom / av).exists():
        return f"/{static_prefix}/{dom.name}/{av}"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (dom / ("avatar" + ext)).exists():
            return f"/{static_prefix}/{dom.name}/avatar{ext}"
    return ""


def _lokacia_bg(loc_id):
    """Фон Биржи — image.* локации 0014_EXCHANGE (или пусто)."""
    if not loc_id:
        return ""
    d = CITY / "локации" / loc_id
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (d / ("image" + ext)).exists():
            return f"/torg-loc-bg/{loc_id}/image{ext}"
    return ""


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
  background-image: url('__BG_URL__');
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


def _bar_html(charge):
    mut = abs(charge)
    half = min(1.0, mut) * 50
    left = 50 if charge >= 0 else 50 - half
    znak = "+" if charge >= 0 else "\u2212"
    zc = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    if mut < 0.25: opt, oc = "\u0447\u0438\u0441\u0442\u043e", "rgba(80,250,123,0.9)"
    elif mut < 0.55: opt, oc = "\u0440\u043e\u0432\u043d\u043e", "rgba(201,168,76,0.9)"
    elif mut < 0.8: opt, oc = "\u0448\u0442\u044b\u0440\u0438\u0442", "rgba(255,160,60,0.9)"
    else: opt, oc = "\u043a\u043e\u043b\u0431\u0430\u0441\u0438\u0442", "rgba(255,80,80,0.9)"
    return (
        '<div style="padding:10px 14px;display:flex;flex-direction:column;gap:8px;">'
        f'<div style="display:flex;justify-content:space-between;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;color:rgba(255,255,255,0.5);">\u0437\u0430\u0440\u044f\u0434<b style="color:#fff;">{znak}{mut:.2f}</b></div>'
        f'<div style="height:6px;border-radius:4px;background:rgba(255,255,255,0.08);position:relative;"><div style="position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:rgba(255,255,255,0.4);"></div><div style="position:absolute;top:0;bottom:0;left:{left}%;width:{half}%;background:{zc};border-radius:4px;"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;color:rgba(255,255,255,0.5);">\u043e\u043f\u0442\u0438\u043a\u0430<b style="color:{oc};">{opt}</b></div>'
        f'<div style="height:6px;border-radius:4px;background:rgba(255,255,255,0.08);overflow:hidden;"><div style="height:100%;width:{int((1-mut)*100)}%;background:{oc};border-radius:4px;"></div></div>'
        '</div>'
    )


def page_torg(tseh_id="\u0442\u043e\u0440\u0433\u043e\u0432\u044b\u0439_\u0445\u0430\u043e\u0441"):
    ceh = reg.get_ceh(tseh_id, "\u0411\u0438\u0440\u0436\u0430")
    if ceh is None:
        ui.label(f"\u0446\u0435\u0445 {tseh_id} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d")
        return

    static_prefix = f"torg-static-{tseh_id}"
    rows = reg.list_nositeli(tseh_id, "\u0411\u0438\u0440\u0436\u0430")
    for row in rows:
        n = row["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"]
        if n:
            try:
                app.add_static_files(f"/{static_prefix}/{Path(n['\u043f\u0430\u043f\u043a\u0430']).name}", n["\u043f\u0430\u043f\u043a\u0430"])
            except Exception:
                pass

    # фон Биржи (здание цеха из манифеста)
    zdanie = ceh.get("\u0437\u0434\u0430\u043d\u0438\u0435") or "0014_EXCHANGE"
    loc_dir = CITY / "\u043b\u043e\u043a\u0430\u0446\u0438\u0438" / zdanie
    if loc_dir.exists():
        try:
            app.add_static_files(f"/torg-loc-bg/{zdanie}", str(loc_dir))
        except Exception:
            pass
    bg_url = _lokacia_bg(zdanie)

    state = {"active": next((r["\u0441\u043b\u043e\u0442"] for r in rows if r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"]), None), "reports": {}, "mode": "real", "hour": 12}
    refs = {"avatars": {}, "viewer": None, "right": None, "hour": None}

    def _row(slot):
        return next((r for r in rows if r["\u0441\u043b\u043e\u0442"] == slot), None)

    def _now():
        if state["mode"] == "test":
            return datetime.now(timezone.utc).replace(hour=int(state["hour"]), minute=0)
        return datetime.now(timezone.utc)

    def upd_avatars():
        for slot, el in refs["avatars"].items():
            r = _row(slot); n = r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"] if r else None
            cls = "avatar"
            if slot == state["active"]: cls += " active"
            if n: cls += " done"
            el.classes(replace=cls)
            if n:
                av = _avatar_url_for(n["\u043f\u0430\u043f\u043a\u0430"], static_prefix)
                if av:
                    el.style(f"background-image:url('{av}');background-size:cover;background-position:center;")

    def upd_right():
        refs["right"].clear()
        r = _row(state["active"]) if state["active"] else None
        n = r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"] if r else None
        with refs["right"]:
            with ui.element("div").classes("right-col"):
                with ui.element("div").classes("right-top-slot"):
                    if n:
                        av = _avatar_url_for(n["\u043f\u0430\u043f\u043a\u0430"], static_prefix)
                        if av:
                            ui.html(f'<img src="{av}" style="width:100%;height:100%;object-fit:cover;border-radius:18px;" onerror="this.style.display=\'none\'">')
                        ui.html(f'<div style="position:absolute;bottom:8px;left:12px;font-weight:900;color:#00ccff;">{n["\u0438\u043c\u044f"]}</div>')
                    else:
                        ui.html(f'\u0432\u0430\u043a\u0430\u043d\u0441\u0438\u044f<br>{r["\u0440\u043e\u043b\u044c"] if r else ""}')
                if n:
                    p = _read_json(Path(n["\u043f\u0430\u043f\u043a\u0430"]) / "passport.json") or {}
                    with ui.element("div").classes("glass"):
                        ui.html(_bar_html(float(p.get("_charge", 0.0) or 0.0)))

    def upd_viewer():
        refs["viewer"].clear()
        txt = state["reports"].get(state["active"], "") if state["active"] else ""
        with refs["viewer"]:
            ui.html(txt.replace("\n", "<br>") if txt else "\u043d\u0430\u0436\u043c\u0438 \u0420\u042b\u041d\u041e\u041a")

    def switch(slot):
        state["active"] = slot; upd_avatars(); upd_right(); upd_viewer()

    def run_market():
        res = kal.kalibrovat_ceh(tseh_id, now_utc=_now(), stamp=(state["mode"] == "real"))
        sess = res.get("\u0441\u0435\u0441\u0441\u0438\u044f", "?")
        if not res.get("\u0435\u0434\u0438\u043d\u0438\u0446\u044b"):
            ui.notify(f"\u0420\u044b\u043d\u043e\u043a: {sess}", type="warning")
            for r in rows:
                if r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"]:
                    state["reports"][r["\u0441\u043b\u043e\u0442"]] = f"\u26aa \u0440\u044b\u043d\u043e\u043a \u0441\u043f\u0438\u0442 ({sess})"
            upd_viewer(); return
        for e in res["\u0435\u0434\u0438\u043d\u0438\u0446\u044b"]:
            nam = e.get("\u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0438\u044f")
            state["reports"][e["\u0441\u043b\u043e\u0442"]] = (
                f"# {e['\u043a\u0442\u043e']} ({e['\u0440\u043e\u043b\u044c']})\n\n"
                f"\u0421\u0435\u0441\u0441\u0438\u044f: {sess} \u00b7 \u0420\u0435\u0436\u0438\u043c: {e['\u0440\u0435\u0436\u0438\u043c']} (\u043c\u0443\u0442\u044c {e['\u043c\u0443\u0442\u044c']})\n\n"
                + ("\n".join(f"\u2014 {x}" for x in nam) if nam else "(RECOVERY)"))
        ui.notify(f"\u0421\u0435\u0441\u0441\u0438\u044f {sess}: {len(res['\u0435\u0434\u0438\u043d\u0438\u0446\u044b'])}", type="positive")
        upd_viewer()

    def set_mode(m):
        state["mode"] = m; refs["hour"].set_visibility(m == "test")

    ui.add_head_html(f"<style>{IDENTITY_BUREAU_CSS}</style>")
    if bg_url:
        ui.add_body_html(f'<div id="bg" style="background-image:url(\'{bg_url}\');"></div>')
    else:
        ui.add_body_html('<div id="bg"></div>')

    with ui.element("div").classes("app-container"):
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass squad-deck"):
                for r in rows:
                    a = ui.element("div").classes("avatar")
                    a.on("click", lambda e, s=r["\u0441\u043b\u043e\u0442"]: switch(s))
                    with a:
                        ui.label(r["\u0441\u043b\u043e\u0442"])
                    refs["avatars"][r["\u0441\u043b\u043e\u0442"]] = a

        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):
                with ui.element("div").classes("glass asset-bay"):
                    ui.html('<div class="panel-title">\u0417\u0430\u0433\u0440\u0443\u0437\u0447\u0438\u043a</div>')
                    ui.upload(multiple=True, auto_upload=True).props("flat color=cyan").style("margin:6px;")
                with ui.element("div").classes("glass settings-panel"):
                    ui.html('<div class="panel-title">\u0418\u0441\u0442\u043e\u0440\u0438\u044f</div>')
                    ui.html('<div class="file-list">\u2014 \u043f\u0443\u0441\u0442\u043e \u2014</div>')

        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("glass stage-monitor"):
                with ui.element("div").classes("stage-toolbar"):
                    with ui.element("div").classes("monitor-utils"):
                        ui.button("\U0001F4E1 \u0420\u042b\u041d\u041e\u041a", on_click=run_market).props("flat").classes("neon-btn g").style("height:40px;width:auto;padding:0 18px;")
                    with ui.element("div"):
                        ui.toggle({"real": "\u0440\u0435\u0430\u043b", "test": "\u0442\u0435\u0441\u0442"}, value="real", on_change=lambda e: set_mode(e.value)).props("dense")
                    hr = ui.row().style("align-items:center;gap:4px;justify-self:end;")
                    with hr:
                        ui.label("UTC:").style("font-size:10px;color:rgba(255,255,255,0.5);")
                        ui.number(value=12, min=0, max=23).bind_value(state, "hour").style("width:56px;")
                    hr.set_visibility(False); refs["hour"] = hr
                with ui.element("div").classes("stage-content"):
                    with ui.element("div").classes("split-view"):
                        refs["viewer"] = ui.element("div").classes("viewer")
                with ui.element("div").classes("floating-console"):
                    ui.input(placeholder="\u0441\u043a\u0430\u0436\u0438...").style("flex:1;")
                    ui.button("SEND").props("flat")

        refs["right"] = ui.element("div").classes("area-right")

    upd_avatars(); upd_right(); upd_viewer()
