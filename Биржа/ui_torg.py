# -*- coding: utf-8 -*-
# TORG_STOL_V1
"""
СТОЛ ЦЕХА · /torg/{tseh_id} (по умолчанию торговый_хаос)

LAYOUT ОДИН В ОДИН СО СТАРЫМ /exchange (studio/economy/ui_exchange.py):
  HEADER — пузырьки трейдеров (клик переключает активного)
  LEFT   — загрузчик + список файлов
  STAGE  — тулбар (РЫНОК + тест/реал) + чат + отчёт-вьюер
  RIGHT  — аватар активного + панель показателей

ГЛАВНОЕ ОТЛИЧИЕ ОТ СТАРОГО ГОРОДА: пузырьки — НЕ захардкоженный список
TRADING_COUNCIL. Читаются из list_nositeli(tseh_id) — Закон Пары.
Родится "скальперы" — эта же страница (/torg/скальперы) обслужит его
без единой правки кода. Вакансия — пузырёк тусклый, без аватара.

ЧЕСТНОСТЬ ЭТОЙ ВЕРСИИ (стол первого слоя, не полный старый Совет):
  Кнопка РЫНОК зовёт КАЛИБРОВКУ (kalibrovka.kalibrovat_ceh) — это
  РЕАЛЬНЫЙ работающий механизм (режим+план по настоящей торговой
  сессии), не бутафория. Но это ещё не полный Совет старого города
  (там был Вильямс-математика + LLM-трейдеры + исполнение ордеров) —
  это заложено СЛЕДУЮЩИМИ камнями (стол.json, run_slot, промпты).
  Тумблер тест/реал — честный: тест даёт руками выбрать час UTC
  (проверить любую сессию не дожидаясь часов), реал — берёт время сейчас.
  Рынок спит — стол честно говорит "рынок спит", не выдумывает бар.

`шесть·проверено·до·корня`
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from nicegui import ui, app

_HERE = Path(__file__).resolve().parent          # Биржа/
_REPO = _HERE.parent                              # корень репо
for _p in (_REPO, _HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cartridge_registry as reg
import kalibrovka as kal
import kalibrovka_core as core

CITY = _REPO / "GRONDHEIM_CITY"


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _avatar_url_for(papka: str, static_prefix: str) -> str:
    """Тот же приём, что в ui_zhitel._avatar_url — папка/имя статики."""
    dom = Path(papka)
    p = _read_json(dom / "passport.json") or {}
    av = p.get("avatar", "")
    if av and (dom / av).exists():
        return f"/{static_prefix}/{dom.name}/{av}"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (dom / ("avatar" + ext)).exists():
            return f"/{static_prefix}/{dom.name}/avatar{ext}"
    return ""


TORG_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
:root{ --bg:#050510; --glass:rgba(13,17,23,0.60); --stroke:rgba(255,255,255,0.10); }
html,body{ height:100%; margin:0; }
body{ width:100vw; height:100vh; overflow:hidden !important; background:#050510 !important;
  font-family:Inter,system-ui,sans-serif; }
.nicegui-content{ overflow:hidden !important; height:100% !important; }
.torg-container{ position:fixed; inset:0; display:grid; width:100vw; height:100vh;
  grid-template-columns:280px 1fr 280px; grid-template-rows:84px 1fr;
  grid-template-areas:"header header header" "left stage right"; gap:10px; padding:10px;
  box-sizing:border-box; }
.area-header{ grid-area:header; } .area-left{ grid-area:left; min-height:0; }
.area-stage{ grid-area:stage; min-height:0; } .area-right{ grid-area:right; min-height:0; }
.glass{ background:var(--glass); border:1px solid var(--stroke); border-radius:18px;
  backdrop-filter:blur(10px); }

.squad-deck{ height:100%; }
.torg-bubble{ position:relative; width:46px; height:46px; border-radius:50%; cursor:pointer;
  background-size:cover; background-position:center; background-color:rgba(255,255,255,0.05);
  border:2px solid rgba(255,255,255,0.12); display:flex; align-items:center; justify-content:center;
  font-size:10px; font-weight:800; color:rgba(255,255,255,0.4); flex-shrink:0;
  transition: all 0.15s; }
.torg-bubble.vacant{ border-style:dashed; opacity:0.4; }
.torg-bubble.occupied{ border-color:rgba(201,168,76,0.4); color:transparent; }
.torg-bubble.active{ border-color:#c9a84c; box-shadow:0 0 14px rgba(201,168,76,0.5); transform:scale(1.1); }
.torg-bubble-label{ position:absolute; bottom:-16px; left:50%; transform:translateX(-50%);
  font-size:8px; color:rgba(255,255,255,0.4); white-space:nowrap; }

.left-col,.stage-col,.right-col{ height:100%; display:flex; flex-direction:column; gap:10px; min-height:0; }
.panel-title{ padding:8px 16px; font-weight:900; letter-spacing:.1em; text-transform:uppercase;
  font-size:11px; color:rgba(255,255,255,0.85); border-bottom:1px solid rgba(255,255,255,0.08); }

.torg-toolbar{ display:flex; gap:8px; align-items:center; padding:10px; flex-shrink:0;
  border-bottom:1px solid rgba(255,255,255,0.08); flex-wrap:wrap; }
.torg-market-btn{ padding:8px 18px; border-radius:8px;
  background:linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10)) !important;
  border:1px solid rgba(0,255,136,0.35); color:rgba(255,255,255,0.9); font-weight:700; }

.torg-chat{ flex:1; overflow-y:auto; padding:12px; display:flex; flex-direction:column; gap:8px; min-height:0; }
.torg-msg{ padding:8px 12px; border-radius:10px; background:rgba(255,255,255,0.04); font-size:0.8rem;
  color:rgba(255,255,255,0.85); max-width:85%; }
.torg-msg.user{ align-self:flex-end; background:rgba(201,168,76,0.12); }

.torg-viewer{ flex:1.2; overflow-y:auto; padding:14px 18px; font-size:0.82rem; line-height:1.6;
  color:rgba(255,255,255,0.8); border-top:1px solid rgba(255,255,255,0.06); white-space:pre-wrap; }

.zavatar{ position:relative; width:100%; aspect-ratio:1/1; border-radius:18px; overflow:hidden;
  background-size:cover; background-position:center; background-color:rgba(255,255,255,0.04);
  flex-shrink:0; }
.zavatar-cap{ position:absolute; left:0; right:0; bottom:0; padding:10px 12px;
  background:linear-gradient(transparent, rgba(0,0,0,0.75)); }
.zavatar-cap .nm{ font-weight:900; color:#c9a84c; font-size:1rem; }
.zavatar-cap .role{ font-size:0.65rem; color:rgba(255,255,255,0.6); text-transform:uppercase; }

.zpok{ padding:10px 16px; display:flex; flex-direction:column; gap:9px; }
.zpok-row{ display:flex; flex-direction:column; gap:3px; }
.zpok-lab{ display:flex; justify-content:space-between; font-size:0.56rem;
  text-transform:uppercase; letter-spacing:0.08em; color:rgba(255,255,255,0.5); }
.zpok-lab b{ color:rgba(255,255,255,0.85); font-weight:700; }
.zpok-bar{ height:6px; border-radius:4px; background:rgba(255,255,255,0.08); overflow:hidden;
  position:relative; }
.zpok-bar--zaryad .zpok-fill{ position:absolute; top:0; bottom:0; }
.zpok-mid{ position:absolute; left:50%; top:-2px; bottom:-2px; width:1px;
  background:rgba(255,255,255,0.4); z-index:2; }
.zpok-fill{ height:100%; border-radius:4px; }
.zpok-dna{ font-size:0.55rem; color:rgba(255,255,255,0.45); font-family:'JetBrains Mono',monospace;
  line-height:1.6; padding-top:4px; border-top:1px solid rgba(255,255,255,0.06); }

.file-list{ padding:4px 8px; font-size:0.7rem; color:rgba(255,255,255,0.5); }
.torg-empty{ opacity:0.5; text-align:center; padding:24px 12px; font-size:0.8rem; }
"""


def _bar_html(charge: float) -> str:
    mut = abs(charge)
    half = min(1.0, mut) * 50
    left = 50 if charge >= 0 else 50 - half
    znak = "+" if charge >= 0 else "\u2212"
    zcolor = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    if mut < 0.25:
        optika, ocolor = "\u0447\u0438\u0441\u0442\u043e", "rgba(80,250,123,0.9)"
    elif mut < 0.55:
        optika, ocolor = "\u0440\u043e\u0432\u043d\u043e", "rgba(201,168,76,0.9)"
    elif mut < 0.8:
        optika, ocolor = "\u0448\u0442\u044b\u0440\u0438\u0442", "rgba(255,160,60,0.9)"
    else:
        optika, ocolor = "\u043a\u043e\u043b\u0431\u0430\u0441\u0438\u0442", "rgba(255,80,80,0.9)"
    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">\u0437\u0430\u0440\u044f\u0434<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar zpok-bar--zaryad"><div class="zpok-mid"></div>'
        f'<div class="zpok-fill" style="left:{left}%; width:{half}%; background:{zcolor};"></div></div></div>'
        f'<div class="zpok-row"><div class="zpok-lab">\u043e\u043f\u0442\u0438\u043a\u0430<b style="color:{ocolor};">{optika}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" style="width:{int((1-mut)*100)}%; background:{ocolor};"></div></div></div>'
        '</div>'
    )


def page_torg(tseh_id: str = "\u0442\u043e\u0440\u0433\u043e\u0432\u044b\u0439_\u0445\u0430\u043e\u0441") -> None:
    ceh = reg.get_ceh(tseh_id, "\u0411\u0438\u0440\u0436\u0430")
    if ceh is None:
        ui.add_head_html(f"<style>{TORG_CSS}</style>")
        with ui.element("div").classes("torg-empty"):
            ui.html(f"\u0446\u0435\u0445 \u00ab{tseh_id}\u00bb \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d")
        return

    static_prefix = f"torg-static-{tseh_id}"
    rows = reg.list_nositeli(tseh_id, "\u0411\u0438\u0440\u0436\u0430")
    for row in rows:
        n = row["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"]
        if n:
            try:
                app.add_static_files(f"/{static_prefix}/{Path(n['\u043f\u0430\u043f\u043a\u0430']).name}",
                                    n["\u043f\u0430\u043f\u043a\u0430"])
            except Exception:
                pass

    state = {
        "active_slot": next((r["\u0441\u043b\u043e\u0442"] for r in rows if r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"]), None),
        "chat": [],
        "reports": {},
        "mode": "real",
        "test_hour": 12,
    }
    refs = {"bubbles": {}, "chat": None, "viewer": None, "right": None, "hour_row": None}

    def _row_by_slot(slot):
        for r in rows:
            if r["\u0441\u043b\u043e\u0442"] == slot:
                return r
        return None

    def _now_utc():
        if state["mode"] == "test":
            return datetime.now(timezone.utc).replace(hour=int(state["test_hour"]), minute=0, second=0)
        return datetime.now(timezone.utc)

    def _update_bubbles():
        for slot, el in refs["bubbles"].items():
            r = _row_by_slot(slot)
            n = r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"] if r else None
            cls = "torg-bubble "
            cls += "active " if slot == state["active_slot"] else ""
            cls += "occupied" if n else "vacant"
            style = ""
            if n:
                av = _avatar_url_for(n["\u043f\u0430\u043f\u043a\u0430"], static_prefix)
                if av:
                    style = f"background-image:url('{av}');"
            el.classes(replace=cls)
            el.style(style)

    def _update_right():
        refs["right"].clear()
        r = _row_by_slot(state["active_slot"]) if state["active_slot"] else None
        n = r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"] if r else None
        with refs["right"]:
            with ui.element("div").classes("right-col"):
                with ui.element("div").classes("zavatar"):
                    if n:
                        av = _avatar_url_for(n["\u043f\u0430\u043f\u043a\u0430"], static_prefix)
                        if av:
                            ui.html(f'<img src="{av}" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display=\'none\'">')
                        ui.html(f'<div class="zavatar-cap"><div class="nm">{n["\u0438\u043c\u044f"]}</div>'
                               f'<div class="role">{r["\u0440\u043e\u043b\u044c"]} \u00b7 {r["\u0441\u043b\u043e\u0442"]}</div></div>')
                    else:
                        ui.html('<div style="display:flex;align-items:center;justify-content:center;height:100%;'
                               'font-size:2.5rem;color:rgba(201,168,76,0.3);">\u2b21</div>')
                        if r:
                            ui.html(f'<div class="zavatar-cap"><div class="nm" style="color:rgba(255,255,255,0.4);">\u0432\u0430\u043a\u0430\u043d\u0441\u0438\u044f</div>'
                                   f'<div class="role">{r["\u0440\u043e\u043b\u044c"]} \u00b7 {r["\u0441\u043b\u043e\u0442"]}</div></div>')
                if n:
                    p = _read_json(Path(n["\u043f\u0430\u043f\u043a\u0430"]) / "passport.json") or {}
                    charge = float(p.get("_charge", 0.0) or 0.0)
                    with ui.element("div").classes("glass"):
                        ui.html(_bar_html(charge))

    def _update_viewer():
        slot = state["active_slot"]
        txt = state["reports"].get(slot, "") if slot else ""
        refs["viewer"].clear()
        with refs["viewer"]:
            if txt:
                ui.html(txt.replace("\n", "<br>"))
            else:
                r = _row_by_slot(slot) if slot else None
                if r and r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"]:
                    ui.html('<div class="torg-empty">\u043d\u0430\u0436\u043c\u0438 \u0420\u042b\u041d\u041e\u041a \u2014 '
                           '\u0443\u0432\u0438\u0434\u0438\u0448\u044c \u043e\u0442\u0447\u0451\u0442</div>')
                else:
                    ui.html('<div class="torg-empty">\u0432\u044b\u0431\u0435\u0440\u0438 \u0437\u0430\u043d\u044f\u0442\u043e\u0433\u043e '
                           '\u0442\u0440\u0435\u0439\u0434\u0435\u0440\u0430</div>')

    def switch_active(slot):
        state["active_slot"] = slot
        _update_bubbles()
        _update_right()
        _update_viewer()

    def run_market():
        now = _now_utc()
        result = kal.kalibrovat_ceh(tseh_id, now_utc=now, stamp=(state["mode"] == "real"))
        sessiya = result.get("\u0441\u0435\u0441\u0441\u0438\u044f", "?")
        if not result.get("\u0435\u0434\u0438\u043d\u0438\u0446\u044b"):
            ui.notify(f"\u0420\u044b\u043d\u043e\u043a: {sessiya} \u2014 \u043d\u0435\u043a\u043e\u0433\u043e \u043a\u0430\u043b\u0438\u0431\u0440\u043e\u0432\u0430\u0442\u044c "
                     f"(\u0432\u0430\u043a\u0430\u043d\u0441\u0438\u0438 \u0438\u043b\u0438 \u0440\u044b\u043d\u043e\u043a \u0441\u043f\u0438\u0442)", type="warning")
            for r in rows:
                if r["\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c"]:
                    state["reports"][r["\u0441\u043b\u043e\u0442"]] = f"\u26aa \u0440\u044b\u043d\u043e\u043a \u0441\u043f\u0438\u0442 ({sessiya})"
            _update_viewer()
            return
        for e in result["\u0435\u0434\u0438\u043d\u0438\u0446\u044b"]:
            nam = e.get("\u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0438\u044f")
            txt = (f"# {e['\u043a\u0442\u043e']} ({e['\u0440\u043e\u043b\u044c']})\n\n"
                  f"**\u0421\u0435\u0441\u0441\u0438\u044f:** {sessiya}  \u00b7  **\u0420\u0435\u0436\u0438\u043c:** {e['\u0440\u0435\u0436\u0438\u043c']} "
                  f"(\u043c\u0443\u0442\u044c {e['\u043c\u0443\u0442\u044c']})\n\n"
                  + ("\n".join(f"\u2014 {x}" for x in nam) if nam else "*(RECOVERY \u2014 \u0441\u0435\u0441\u0441\u0438\u044e \u043f\u0440\u043e\u043f\u0443\u0441\u043a\u0430\u0435\u0442)*"))
            state["reports"][e["\u0441\u043b\u043e\u0442"]] = txt
        ui.notify(f"\u0421\u0435\u0441\u0441\u0438\u044f {sessiya} \u2014 \u043e\u0442\u043a\u0430\u043b\u0438\u0431\u0440\u043e\u0432\u0430\u043d\u043e "
                 f"{len(result['\u0435\u0434\u0438\u043d\u0438\u0446\u044b'])}", type="positive")
        _update_viewer()

    def set_mode(mode):
        state["mode"] = mode
        refs["hour_row"].set_visibility(mode == "test")

    def send_message():
        pass  # \u0448\u043e\u0432 \u043f\u043e\u0434 \u0436\u0438\u0432\u043e\u0439 \u0447\u0430\u0442 (\u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u043a\u0430\u043c\u0435\u043d\u044c)

    ui.add_head_html(f"<style>{TORG_CSS}</style>")

    with ui.element("div").classes("torg-container"):
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass squad-deck").style(
                "display:flex; align-items:center; padding:0 16px; gap:14px;"):
                ui.html(f'<div style="font-weight:900;color:#c9a84c;font-size:0.85rem;'
                       f'text-transform:uppercase;letter-spacing:0.08em;">{ceh.get("\u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435","?")}</div>')
                with ui.element("div").style("display:flex;gap:16px;flex:1;justify-content:center;"):
                    for r in rows:
                        b = ui.element("div").classes("torg-bubble")
                        b.on("click", lambda e, s=r["\u0441\u043b\u043e\u0442"]: switch_active(s))
                        with b:
                            ui.html(f'<div class="torg-bubble-label">{r["\u0441\u043b\u043e\u0442"]}</div>')
                        refs["bubbles"][r["\u0441\u043b\u043e\u0442"]] = b
                ui.button("\u2190 \u0411\u0438\u0440\u0436\u0430", on_click=lambda: ui.navigate.to("/grondheim")).props("flat")

        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col glass"):
                ui.html('<div class="panel-title">\u0417\u0410\u0413\u0420\u0423\u0417\u0427\u0418\u041a</div>')
                ui.upload(multiple=True, auto_upload=True).props("flat color=amber").style("margin:8px;")
                ui.html('<div class="file-list">\u2014 \u0438\u0441\u0442\u043e\u0440\u0438\u044f \u0434\u043b\u044f \u0442\u0435\u0441\u0442\u0435\u0440\u0430 \u2014</div>')

        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("stage-col glass"):
                with ui.element("div").classes("torg-toolbar"):
                    ui.button("\U0001F4E1 \u0420\u042b\u041d\u041e\u041a", on_click=run_market).classes("torg-market-btn")
                    ui.toggle({"real": "\u0440\u0435\u0430\u043b", "test": "\u0442\u0435\u0441\u0442"}, value="real",
                             on_change=lambda e: set_mode(e.value)).props("dense")
                    hour_row = ui.row().style("align-items:center;gap:6px;")
                    with hour_row:
                        ui.label("UTC \u0447\u0430\u0441:").style("font-size:0.7rem;color:rgba(255,255,255,0.5);")
                        ui.number(value=12, min=0, max=23).bind_value(state, "test_hour").style("width:60px;")
                    hour_row.set_visibility(False)
                    refs["hour_row"] = hour_row
                refs["viewer"] = ui.element("div").classes("torg-viewer")
                with ui.row().style("padding:8px;gap:8px;flex-shrink:0;"):
                    msg_in = ui.input(placeholder="\u0441\u043a\u0430\u0436\u0438...").style("flex:1;")
                    ui.button("SEND", on_click=send_message)

        refs["right"] = ui.element("div").classes("area-right")

    _update_bubbles()
    _update_right()
    _update_viewer()
