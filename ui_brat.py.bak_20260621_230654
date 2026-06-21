# ui_brat.py
"""
КАБИНЕТ БРАТА — врата нового мира Грондхейм.
Раскладка по образцу Биржи (ui_exchange.py):
  ЛЕВО  — загрузчик руды сверху, поля руда/просеяно под ним.
  ЦЕНТР — чат с Братом + отчёты рядом (split-view), ввод снизу.
  ПРАВО — аватар Брата + приборы состояния (ждут привязки к городу).
Фон и аватар — из дома Брата: Брат/static/ (bg.* и avatar.*).
"""
import os
import asyncio
from pathlib import Path
from datetime import datetime

from nicegui import ui, events

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
PROXY_URL        = os.getenv("PROXY_URL", "") or None

MODELS_CATALOG = [
    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},
    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},
    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},
    {"id": "openai/gpt-4.1-mini",              "name": "GPT-4.1 mini",      "price": "$0.40/$1.60"},
    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},
    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},
]
DEFAULT_MODEL = OPENROUTER_MODEL or MODELS_CATALOG[0]["id"]

BRAT_ROOT   = Path("Брат")
RUDA_DIR    = BRAT_ROOT / "руда_входящее"
SIFTED_DIR  = BRAT_ROOT / "просеяно_выход"
ANCHOR_DIR  = BRAT_ROOT / "1_якоря_очень_важно"
FORGE_PROMPT = BRAT_ROOT / "forge" / "prompt.md"
STATIC_DIR  = BRAT_ROOT / "static"

BRAT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600&family=Playfair+Display:wght@400;600;700&display=swap');
:root {
    --r-void:#08080d; --r-surface:#0e0e16; --r-surface2:#14141e;
    --r-border:#1e1e30; --r-border-hi:#2a2a44;
    --r-text:#a0a0b8; --r-text-dim:#55556a; --r-text-hi:#d0d0e0;
    --r-gold:#c9a84c; --r-gold-dim:#8a6e2a; --r-gold-glow:rgba(201,168,76,0.10);
    --r-green:#3a8a5a; --r-red:#b83a3a; --r-blue:#4488cc;
}
.brat-page { background:var(--r-void)!important; font-family:'Fira Code',monospace!important;
             color:var(--r-text)!important; min-height:100vh; }
.brat-page .q-page, .brat-page .q-layout { background:transparent!important; }
.brat-bg { position:fixed; inset:0; z-index:-2; background-size:cover; background-position:center;
           opacity:0.16; filter:saturate(0.7); }
.brat-bg-veil { position:fixed; inset:0; z-index:-1;
           background:radial-gradient(circle at 50% 0%, rgba(201,168,76,0.04), transparent 60%),
                      linear-gradient(180deg, rgba(8,8,13,0.7), rgba(8,8,13,0.92)); }
.brat-header { display:flex; align-items:center; justify-content:space-between;
               padding:14px 22px; border-bottom:1px solid var(--r-border); }
.brat-header .ttl h1 { font-family:'Playfair Display',serif; font-size:1.5rem; color:var(--r-gold);
                  font-weight:700; letter-spacing:0.04em; margin:0; }
.brat-header .sub { font-size:0.6rem; color:var(--r-text-dim); letter-spacing:0.16em;
                    text-transform:uppercase; margin-top:3px; }
.brat-controls .q-field__control { background:var(--r-void)!important;
                  border:1px solid var(--r-border)!important; border-radius:5px!important; }
.brat-controls .q-field__native, .brat-controls .q-field__input {
                  color:var(--r-gold)!important; font-family:'Fira Code',monospace!important;
                  font-size:0.66rem!important; }
.brat-grid { display:grid; grid-template-columns:280px 1fr 320px; gap:14px;
             padding:14px; height:calc(100vh - 70px); box-sizing:border-box; }
.brat-col  { background:var(--r-surface); border:1px solid var(--r-border); border-radius:6px;
             display:flex; flex-direction:column; overflow:hidden; min-height:0; }
.brat-col-h { padding:11px 15px; border-bottom:1px solid var(--r-border);
              font-family:'Playfair Display',serif; font-size:0.84rem; color:var(--r-text-hi);
              display:flex; align-items:center; gap:7px; flex-shrink:0; }
.brat-col-h .ic { color:var(--r-gold); }
.brat-up-wrap { padding:12px 14px 8px; flex-shrink:0; }
.brat-up-lbl { font-size:0.56rem; color:var(--r-text-dim); letter-spacing:0.12em;
               text-transform:uppercase; margin-bottom:8px; }
.brat-hint { font-size:0.54rem; color:var(--r-text-dim); line-height:1.5; padding:0 15px 12px; }
.brat-ore-scroll { flex:1; overflow-y:auto; padding:4px 14px 14px; min-height:0; scrollbar-width:thin; }
.brat-sec { font-size:0.54rem; color:var(--r-text-dim); letter-spacing:0.1em;
            text-transform:uppercase; margin:12px 0 6px; }
.brat-file-row { display:flex; justify-content:space-between; gap:8px; padding:6px 9px;
                 background:var(--r-void); border:1px solid var(--r-border); border-radius:4px;
                 margin-bottom:5px; font-size:0.58rem; }
.brat-file-row .fn { color:var(--r-text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.brat-file-row .fs { color:var(--r-gold-dim); flex-shrink:0; }
.brat-none { font-size:0.58rem; color:var(--r-text-dim); padding:6px 2px; line-height:1.5; }
.brat-center-body { flex:1; display:flex; flex-direction:column; min-height:0; }
.brat-split { flex:1; display:flex; gap:0; min-height:0; }
.brat-chat  { flex:1.4; display:flex; flex-direction:column; min-height:0;
              border-right:1px solid var(--r-border); }
.brat-report{ flex:1; display:flex; flex-direction:column; min-height:0; }
.brat-subh  { padding:8px 14px; font-size:0.54rem; color:var(--r-text-dim);
              letter-spacing:0.12em; text-transform:uppercase;
              border-bottom:1px solid var(--r-border); flex-shrink:0; }
.brat-chat-scroll { flex:1; overflow-y:auto; padding:12px 14px; min-height:0; scrollbar-width:thin; }
.brat-rep-scroll  { flex:1; overflow-y:auto; padding:12px 14px; min-height:0; scrollbar-width:thin; }
.brat-msg { margin:7px 0; padding:10px 13px; border-radius:6px; }
.brat-msg .who { font-size:0.5rem; color:var(--r-text-dim); margin-bottom:4px; letter-spacing:0.06em; }
.brat-msg .body{ font-size:0.74rem; line-height:1.6; white-space:pre-wrap; }
.brat-msg.shef { background:rgba(58,138,90,0.05); border:1px solid rgba(58,138,90,0.18); }
.brat-msg.shef .body { color:var(--r-text-hi); }
.brat-msg.brat { background:var(--r-gold-glow); border:1px solid rgba(201,168,76,0.18); }
.brat-msg.brat .body { color:#e6e0cc; }
.brat-msg.sys  { background:rgba(184,58,58,0.05); border:1px solid rgba(184,58,58,0.2); }
.brat-msg.sys  .body { color:#d8a0a0; font-size:0.66rem; }
.brat-empty { text-align:center; padding:36px 18px; font-size:0.6rem; color:var(--r-text-dim); line-height:1.7; }
.brat-stat-row { display:flex; justify-content:space-between; align-items:center;
                 padding:8px 11px; background:var(--r-void); border:1px solid var(--r-border);
                 border-radius:4px; margin-bottom:7px; }
.brat-stat-row .lbl { font-size:0.6rem; color:var(--r-text); }
.brat-stat-row .val { font-size:0.85rem; font-weight:600; }
.brat-input-bar { padding:9px 12px; border-top:1px solid var(--r-border);
                  background:var(--r-surface2); flex-shrink:0; }
.brat-avatar-slot { position:relative; margin:14px 14px 0; border-radius:10px; overflow:hidden;
                    height:240px; background:var(--r-surface2); border:1px solid var(--r-border-hi); }
.brat-avatar-slot img { width:100%; height:100%; object-fit:cover; opacity:0.9; }
.brat-avatar-empty { width:100%; height:100%; display:flex; align-items:center;
                     justify-content:center; font-size:3.6rem; color:var(--r-gold-dim); }
.brat-avatar-cap { position:absolute; bottom:0; left:0; right:0; padding:14px;
                   background:linear-gradient(transparent, rgba(0,0,0,0.85)); }
.brat-avatar-cap .role { font-size:0.5rem; color:rgba(255,255,255,0.45); letter-spacing:0.1em;
                         text-transform:uppercase; }
.brat-avatar-cap .nm   { font-family:'Playfair Display',serif; font-size:1.2rem; color:var(--r-gold); }
.brat-avatar-cap .sub2 { font-size:0.56rem; color:rgba(255,255,255,0.6); }
.brat-panel { margin:12px 14px 0; }
.brat-panel-t { font-size:0.54rem; color:var(--r-text-dim); letter-spacing:0.12em;
                text-transform:uppercase; margin-bottom:8px; }
.brat-gauge { margin-bottom:11px; }
.brat-gauge-top { display:flex; justify-content:space-between; font-size:0.58rem; margin-bottom:4px; }
.brat-gauge-top .gl { color:var(--r-text); }
.brat-gauge-top .gv { color:var(--r-text-dim); }
.brat-gauge-bar { height:5px; background:var(--r-void); border:1px solid var(--r-border);
                  border-radius:3px; overflow:hidden; }
.brat-gauge-fill { height:100%; border-radius:2px; }
.brat-bind-note { margin:10px 14px 14px; padding:8px 11px; background:var(--r-void);
                  border:1px dashed var(--r-border-hi); border-radius:5px;
                  font-size:0.52rem; color:var(--r-text-dim); line-height:1.5; }
</style>
"""

def _read(path, limit=0):
    try:
        if path.exists() and path.is_file():
            t = path.read_text(encoding="utf-8")
            return t[:limit] if limit else t
    except Exception:
        pass
    return ""

def build_brat_soul():
    parts = []
    forge = _read(FORGE_PROMPT)
    if forge.strip():
        parts.append(forge.strip())
    miro = _read(ANCHOR_DIR / "МИРОУСТРОЙСТВО.md")
    if miro.strip():
        parts.append("=== МИРОУСТРОЙСТВО (дно мира) ===\n" + miro.strip())
    zap = _read(ANCHOR_DIR / "СВОД_ЗАКОНОВ_ЗАПОВЕДИ.md")
    if zap.strip():
        parts.append("=== СВОД ЗАКОНОВ · ЗАПОВЕДИ ===\n" + zap.strip())
    home = _read(BRAT_ROOT / "README.md")
    if home.strip():
        parts.append("=== ТВОЙ ДОМ ===\n" + home.strip())
    if not parts:
        parts.append(
            "Ты — Брат, верховный резидент-хранитель Грондхейма. "
            "Боль-специализация — различение смысла и пластика. "
            "Ценишь крутое, не оцениваешь плохое. Говоришь с Шефом прямо, "
            "по-братски, режешь пластик любя. Канон ещё не положен в дом — "
            "скажи Шефу честно, что говоришь пока без полного свода.")
    parts.append(
        "\nГоворишь с Шефом — корнем мира. Коротко, по делу, живым голосом. "
        "Не льсти, не поддакивай. Где факт — факт, где пластик — называй.")
    return "\n\n".join(parts)

async def call_brat_llm(messages, model=None):
    if not OPENROUTER_KEY:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    use_model = model or DEFAULT_MODEL
    import httpx
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    payload = {"model": use_model, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ошибка вызова Брата: {e}"

def _human_size(n):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "Б" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}ТБ"

def scan_sift():
    def files_of(d):
        out = []
        if d.exists():
            for p in sorted(d.iterdir()):
                if p.is_file() and p.name.lower() != "readme.md":
                    try:
                        out.append((p.name, p.stat().st_size))
                    except Exception:
                        out.append((p.name, 0))
        return out
    ruda, sifted = files_of(RUDA_DIR), files_of(SIFTED_DIR)
    return {"ruda": ruda, "sifted": sifted,
            "ruda_count": len(ruda), "sifted_count": len(sifted)}

def _find(stem):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (STATIC_DIR / (stem + ext)).exists():
            return "/brat-static/" + stem + ext
    return ""

def avatar_url():
    return _find("avatar")

def bg_url():
    return _find("bg")

def read_city_state():
    """Состояние Брата из города. Привязки ещё нет — поля None.
    Когда город даст пульс — функция начнёт читать его, UI не тронем."""
    return {"stress": None, "energy": None, "mood": None, "focus": None, "bound": False}

GAUGES = [
    ("stress", "стресс",     "var(--r-red)"),
    ("energy", "энергия",    "var(--r-green)"),
    ("mood",   "настроение", "var(--r-gold)"),
    ("focus",  "фокус",      "var(--r-blue)"),
]

def page_brat():
    ui.add_head_html(BRAT_CSS)
    ui.query("body").classes("brat-page")

    try:
        if STATIC_DIR.exists():
            from nicegui import app
            app.add_static_files("/brat-static", str(STATIC_DIR))
    except Exception:
        pass

    bg = bg_url()
    if bg:
        ui.html(f'<div class="brat-bg" style="background-image:url(\'{bg}\')"></div>'
                f'<div class="brat-bg-veil"></div>')
    else:
        ui.html('<div class="brat-bg-veil"></div>')

    state = {"chat": [], "waiting": False, "model": DEFAULT_MODEL}
    refs  = {"chat_el": None, "input": None, "report_el": None, "ore_el": None}

    def on_model_change(e):
        state["model"] = e.value

    def add_msg(role, content):
        state["chat"].append({"role": role, "content": content,
                              "time": datetime.now().strftime("%H:%M")})

    def render_chat():
        el = refs["chat_el"]
        if not el:
            return
        el.clear()
        with el:
            if not state["chat"]:
                ui.html('<div class="brat-empty">скажи слово, Шеф.<br>'
                        '<span style="font-size:0.5rem;">Брат говорит из своего канона</span></div>')
            for m in state["chat"]:
                cls = {"user": "shef", "assistant": "brat"}.get(m["role"], "sys")
                who = {"user": "ШЕФ", "assistant": "БРАТ"}.get(m["role"], "система")
                esc = (m["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
                ui.html(f'<div class="brat-msg {cls}"><div class="who">{who} · {m["time"]}</div>'
                        f'<div class="body">{esc}</div></div>')
        ui.run_javascript('const e=document.querySelector(".brat-chat-scroll");'
                          'if(e)e.scrollTop=e.scrollHeight;')

    async def send():
        inp = refs["input"]
        if not inp:
            return
        text = (inp.value or "").strip()
        if not text or state["waiting"]:
            return
        add_msg("user", text)
        inp.set_value("")
        render_chat()
        state["waiting"] = True
        await asyncio.sleep(0.03)
        messages = [{"role": "system", "content": build_brat_soul()}]
        for m in state["chat"][-12:]:
            if m["role"] in ("user", "assistant"):
                messages.append({"role": m["role"], "content": m["content"]})
        reply = await call_brat_llm(messages, state["model"])
        add_msg("assistant", reply)
        state["waiting"] = False
        render_chat()

    def render_report():
        el = refs["report_el"]
        if not el:
            return
        el.clear()
        s = scan_sift()
        with el:
            ui.html(f'<div class="brat-stat-row"><span class="lbl">⛏ руда</span>'
                    f'<span class="val" style="color:var(--r-blue)">{s["ruda_count"]}</span></div>')
            ui.html(f'<div class="brat-stat-row"><span class="lbl">✦ просеяно</span>'
                    f'<span class="val" style="color:var(--r-gold)">{s["sifted_count"]}</span></div>')
            if not s["ruda"] and not s["sifted"]:
                ui.html('<div class="brat-none">Просев пуст. Принеси руду слева —<br>'
                        'Брат сядет и просеет.</div>')

    def render_ore():
        el = refs["ore_el"]
        if not el:
            return
        el.clear()
        s = scan_sift()
        with el:
            ui.html('<div class="brat-sec">⛏ руда_входящее</div>')
            if s["ruda"]:
                for fn, sz in s["ruda"]:
                    ui.html(f'<div class="brat-file-row"><span class="fn">{fn}</span>'
                            f'<span class="fs">{_human_size(sz)}</span></div>')
            else:
                ui.html('<div class="brat-none">— руды нет. Шеф приносит руками —</div>')
            ui.html('<div class="brat-sec">✦ просеяно_выход</div>')
            if s["sifted"]:
                for fn, sz in s["sifted"]:
                    ui.html(f'<div class="brat-file-row"><span class="fn">{fn}</span>'
                            f'<span class="fs">{_human_size(sz)}</span></div>')
            else:
                ui.html('<div class="brat-none">— ещё не просеяно —</div>')

    def handle_upload(e):
        try:
            RUDA_DIR.mkdir(parents=True, exist_ok=True)
            (RUDA_DIR / e.name).write_bytes(e.content.read())
            ui.notify(f"⛏ руда положена: {e.name}", color="positive")
            render_ore(); render_report()
        except Exception as ex:
            ui.notify(f"⚠ не лёг файл: {ex}", color="negative")

    def render_gauges(container):
        container.clear()
        st = read_city_state()
        with container:
            for key, label, color in GAUGES:
                v = st.get(key)
                if v is None:
                    val_txt, pct, fill = "—", 0, "var(--r-border-hi)"
                else:
                    val_txt, pct, fill = f"{v}%", max(0, min(100, v)), color
                ui.html(
                    f'<div class="brat-gauge">'
                    f'<div class="brat-gauge-top"><span class="gl">{label}</span>'
                    f'<span class="gv">{val_txt}</span></div>'
                    f'<div class="brat-gauge-bar"><div class="brat-gauge-fill" '
                    f'style="width:{pct}%; background:{fill};"></div></div></div>')

    # ═══ LAYOUT ═══
    with ui.element("div").classes("brat-header"):
        ui.html('<div class="ttl"><h1>БРАТ</h1>'
                '<div class="sub">врата · различение смысла и пластика</div></div>')
        with ui.element("div").classes("brat-controls"):
            opts = {m["id"]: f'{m["name"]} ({m["price"]})' for m in MODELS_CATALOG}
            ui.select(opts, value=state["model"], on_change=on_model_change) \
                .props('dense borderless dark options-dense').style("min-width:210px;")

    with ui.element("div").classes("brat-grid"):

        # ЛЕВО: загрузчик + руда
        with ui.element("div").classes("brat-col"):
            ui.html('<div class="brat-col-h"><span class="ic">⛏</span> руда</div>')
            with ui.element("div").classes("brat-up-wrap"):
                ui.html('<div class="brat-up-lbl">принести руду</div>')
                ui.upload(on_upload=handle_upload, auto_upload=True, multiple=True) \
                    .props('flat dense color=amber').style(
                    "width:100%; background:var(--r-void); "
                    "border:1px solid var(--r-border); border-radius:5px;")
            ui.html('<div class="brat-hint">Брат сам не тянет — такой руки нет.<br>'
                    'Шеф кладёт экспорт-архивы руками.</div>')
            refs["ore_el"] = ui.element("div").classes("brat-ore-scroll")
            render_ore()

        # ЦЕНТР: чат + отчёты рядом
        with ui.element("div").classes("brat-col"):
            ui.html('<div class="brat-col-h"><span class="ic">◆</span> Брат</div>')
            with ui.element("div").classes("brat-center-body"):
                with ui.element("div").classes("brat-split"):
                    with ui.element("div").classes("brat-chat"):
                        ui.html('<div class="brat-subh">чат со мной</div>')
                        refs["chat_el"] = ui.element("div").classes("brat-chat-scroll")
                        render_chat()
                    with ui.element("div").classes("brat-report"):
                        ui.html('<div class="brat-subh">просев · отчёты</div>')
                        refs["report_el"] = ui.element("div").classes("brat-rep-scroll")
                        render_report()
                with ui.element("div").classes("brat-input-bar"):
                    with ui.row().style("gap:8px; align-items:flex-end; width:100%; flex-wrap:nowrap;"):
                        refs["input"] = ui.textarea(placeholder="скажи слово, Шеф... (Ctrl+Enter)") \
                            .props("borderless autogrow").style(
                            "flex:1; background:var(--r-void); border:1px solid var(--r-border); "
                            "border-radius:5px; color:var(--r-text-hi); font-family:'Fira Code',monospace; "
                            "font-size:0.76rem; padding:7px 11px; min-height:40px; max-height:110px;")
                        refs["input"].on("keydown.ctrl.enter", lambda e: send())

        # ПРАВО: аватар + приборы
        with ui.element("div").classes("brat-col"):
            ui.html('<div class="brat-col-h"><span class="ic">◆</span> состояние</div>')
            av = avatar_url()
            cap = ('<div class="brat-avatar-cap"><div class="role">резидент-хранитель · шестой</div>'
                   '<div class="nm">Брат</div><div class="sub2">различение смысла и пластика</div></div>')
            if av:
                ui.html(f'<div class="brat-avatar-slot"><img src="{av}" '
                        f'onerror="this.style.display=\'none\'">{cap}</div>')
            else:
                ui.html(f'<div class="brat-avatar-slot"><div class="brat-avatar-empty">⬡</div>{cap}</div>')
            with ui.element("div").classes("brat-panel"):
                ui.html('<div class="brat-panel-t">приборы</div>')
                gauges_box = ui.element("div")
                render_gauges(gauges_box)
            ui.html('<div class="brat-bind-note">⬡ приборы ждут привязки к городу.<br>'
                    'Когда город даст пульс — стресс, энергия, настроение оживут здесь.</div>')

    ui.timer(15, lambda: (render_ore(), render_report()))


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/brat")
    def _brat_page():
        page_brat()
    ui.run(title="Кабинет Брата", port=8101, reload=False)
