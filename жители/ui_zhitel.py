# ui_zhitel.py
"""
КОВЧЕГ — кабинет жителя в состоянии прибытия (под Братом).
Route: /zhitel/{zid}  (zid = ID_Object из паспорта, напр. 0001_Liya_Heat)

Ковчег — не место, а СОСТОЯНИЕ: житель/гость приземлился, но ещё не
прописан. Один кабинет на всех (окно-рамка), грузит САМУ ЛИЧНОСТЬ из
якоря (passport = кишки жителя: кто он, история, натура), не «папку-дом».
Фон — ковчега (Шеф закинет в GRONDHEIM_CITY/ковчег/bg.*).

Раскладка — калька кабинета Брата (ui_brat.py): app-container grid,
area-left / area-stage / area-right, золото #c9a84c, glass.

  ЛЕВО  — загрузчик (руда жителю) + список файлов.
  ЦЕНТР — два поля: ЧАТ с жителем + ОТЧЁТЫ (состояние/просев). Ввод внизу.
  ПРАВО — аватар жителя + приборы состояния.

ОКНО общее, НАПОЛНЕНИЕ из дома конкретного жителя (паспорт, аватар, ядро).
Движок (dvizhok.py) живёт в доме жителя — кабинет подключит ПОТОМ (глубже).

ФОН ПО МАСКЕ (шов под будущее):
  _bg_for_mask(dom) сейчас отдаёт общий фон. Когда у жителя появятся
  папки маски/{дом,работа,школа}/ со своим bg.* — функция начнёт брать
  фон активной маски. Кабинет не заметит подмены (как scan_hierarchy карты).

Новый город · ни нитки из -2.
`шесть·проверено·до·корня`
"""
import json
import os
import asyncio
from pathlib import Path
from datetime import datetime

from nicegui import ui

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from dvizhok import Dvizhok  # DVIZHOK_V_KABINET_V1: личный движок жителя

OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
PROXY_URL        = os.getenv("PROXY_URL", "") or None


async def call_zhitel_llm(messages, model=None):
    """Тот же паттерн, что у Брата (ui_brat.py) — один способ говорить с LLM."""
    if not OPENROUTER_KEY:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    use_model = model or OPENROUTER_MODEL
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
        return f"⚠ Ошибка вызова {model or use_model}: {e}"


def _otsenit_tonus_silu(text: str) -> tuple:
    """Простые правила: тонус (плюс/минус/ровно) и сила (0..1) сообщения.
    Не классификатор LLM — быстрые правила по словам и пунктуации."""
    t = (text or "").strip()
    if not t:
        return "ровно", 0.1

    low = t.lower()
    SLOVA_PLUS = ("спасибо", "молодец", "хорошо", "отлично", "люблю", "рад",
                  "круто", "класс", "умница", "горжусь", "красиво", "правильно")
    SLOVA_MINUS = ("плохо", "зря", "ошибка", "виновата", "глупо", "не так",
                   "стыдно", "жаль", "грустно", "больно", "обидно", "злюсь",
                   "не должна", "нельзя", "хватит", "достаточно")

    has_plus = any(w in low for w in SLOVA_PLUS)
    has_minus = any(w in low for w in SLOVA_MINUS)
    if has_minus and not has_plus:
        tonus = "минус"
    elif has_plus and not has_minus:
        tonus = "плюс"
    else:
        tonus = "ровно"

    # сила: длина + крик (заглавные) + восклицания/вопросы
    dlina = min(1.0, len(t) / 200.0)
    bukv = [c for c in t if c.isalpha()]
    kapslok = (sum(1 for c in bukv if c.isupper()) / len(bukv)) if bukv else 0.0
    vosklic = min(1.0, (t.count("!") + t.count("?")) / 3.0)
    sila = min(1.0, 0.3 + dlina * 0.4 + kapslok * 0.3 + vosklic * 0.3)

    return tonus, round(sila, 2)

_ROOT = Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: файл в жители/, корень репо — на уровень выше
ZHITELI_DIR = _ROOT / "GRONDHEIM_CITY" / "жители"
GUARDIANS_DIR = _ROOT / "GRONDHEIM_CITY" / "Hexagon" / "3_guardians"


# ═══════════════════════════════════════════════════════════
# НАЙТИ ДОМ ЖИТЕЛЯ по id (живой скан, как карта — не держим список)
# ═══════════════════════════════════════════════════════════

def find_dom(zid: str):
    """Дом жителя по ID_Object. Возвращает (паспорт, путь_дома) или (None, None).

    FIND_DOM_KOVCHEG_V1: реальная структура рождения (ROZHDENIE_TONKOE_V1) —
    паспорт ВНУТРИ папки дома, не рядом как отдельный файл:
        жители/ковчег/{имя}/passport.json
    Старый паттерн (паспорт-лицо рядом с папкой) больше не строится при
    рождении — оставлен только для GUARDIANS_DIR на случай старого формата.
    """
    # ZHITELI_DIR (ковчег и будущие районы) — паспорт ВНУТРИ папки-дома
    if ZHITELI_DIR.exists():
        for prof_dir in ZHITELI_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for dom_dir in prof_dir.iterdir():
                if not dom_dir.is_dir():
                    continue
                passport_file = dom_dir / "passport.json"
                if not passport_file.exists():
                    continue
                try:
                    p = json.loads(passport_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if str(p.get("ID_Object", "")) == str(zid):
                    return p, dom_dir

    # GUARDIANS_DIR — старый паттерн (паспорт-лицо рядом с папкой), не трогаем
    if GUARDIANS_DIR.exists():
        for prof_dir in GUARDIANS_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                if item.is_file() and item.suffix == ".json":
                    try:
                        p = json.loads(item.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if str(p.get("ID_Object", "")) == str(zid):
                        dom = item.with_suffix("")
                        if not dom.is_dir():
                            dom = prof_dir / item.stem
                        return p, dom
    return None, None


def list_zhiteli():
    """Все жители (для выбора, если zid не задан). Паспорта-лица.
    FIND_DOM_KOVCHEG_V1: та же логика поиска, что и в find_dom."""
    out = []
    if ZHITELI_DIR.exists():
        for prof_dir in ZHITELI_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for dom_dir in prof_dir.iterdir():
                if not dom_dir.is_dir():
                    continue
                passport_file = dom_dir / "passport.json"
                if not passport_file.exists():
                    continue
                try:
                    p = json.loads(passport_file.read_text(encoding="utf-8"))
                    out.append(p)
                except Exception:
                    pass
    if GUARDIANS_DIR.exists():
        for prof_dir in GUARDIANS_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            for item in prof_dir.iterdir():
                if item.is_file() and item.suffix == ".json":
                    try:
                        p = json.loads(item.read_text(encoding="utf-8"))
                        out.append(p)
                    except Exception:
                        pass
    return out


# ═══════════════════════════════════════════════════════════
# ФОН ПО МАСКЕ — шов под будущее.
# Сейчас: общий фон (масок-папок ещё нет). Потом: фон активной маски.
# ═══════════════════════════════════════════════════════════

# КОВЧЕГ — общий дом прибытия. Пока у жителя нет своей маски/жилья,
# он "в ковчеге" → фон кабинета берётся из ковчега. Не пустой градиент,
# а место прибытия по смыслу. (Ковчег-как-локация-с-маяком — замысел, позже.)
KOVCHEG_DIR = _ROOT / "GRONDHEIM_CITY" / "ковчег"


def _bg_for_mask(dom: Path, mask: str = None) -> str:
    """Путь фона кабинета. Порядок: активная маска → жильё жителя → КОВЧЕГ → дефолт.
    ШОВ: маски/{mask}/bg.* оживёт, когда появятся маски с фонами."""
    # 1. фон активной маски (будущее: маски/работа/bg.*, маски/дом/bg.* ...)
    if dom is not None and mask:
        for ext in (".jpg", ".png", ".jpeg", ".webp"):
            cand = dom / "маски" / mask / ("bg" + ext)
            if cand.exists():
                return f"/zhitel-static/{dom.name}/маски/{mask}/bg{ext}"
    # 2. фон в корне дома жителя (если положен)
    if dom is not None:
        for ext in (".jpg", ".png", ".jpeg", ".webp"):
            cand = dom / ("bg" + ext)
            if cand.exists():
                return f"/zhitel-static/{dom.name}/bg{ext}"
    # 3. КОВЧЕГ — общий фон прибытия (нет маски, нет своего жилья)
    if KOVCHEG_DIR.exists():
        for ext in (".jpg", ".png", ".jpeg", ".webp"):
            cand = KOVCHEG_DIR / ("bg" + ext)
            if cand.exists():
                return "/kovcheg-static/bg" + ext
    return ""   # дефолт — тёмный градиент с золотом (CSS). Здесь будет ковчег.


def _avatar_url(dom: Path, p: dict) -> str:
    if dom is None:
        return ""
    av = p.get("avatar", "")
    if av and (dom / av).exists():
        return f"/zhitel-static/{dom.name}/{av}"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (dom / ("avatar" + ext)).exists():
            return f"/zhitel-static/{dom.name}/avatar{ext}"
    return ""


ZHITEL_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
:root{ --bg:#050510; --glass:rgba(13,17,23,0.60); --stroke:rgba(255,255,255,0.10); }
html,body{ height:100%; margin:0; }
body{ width:100vw; height:100vh; overflow:hidden !important; background:transparent !important;
  font-family:Inter,system-ui,sans-serif; }
#zbg{ position:fixed; inset:0; z-index:-1; background-size:cover; background-position:center; background-color:#050510; }
#zbg::after{ content:''; position:absolute; inset:0;
  background: radial-gradient(1000px 700px at 20% 10%, rgba(201,168,76,0.10), transparent 60%),
              radial-gradient(900px 650px at 80% 25%, rgba(201,168,76,0.06), transparent 55%),
              rgba(0,0,0,0.45); backdrop-filter:blur(8px); }
.app-container{ position:fixed; inset:0; display:grid; width:100vw; height:100vh;
  grid-template-columns:300px 1fr 260px; grid-template-rows:80px 1fr;
  grid-template-areas:"header header header" "left stage right"; gap:20px; padding:20px; box-sizing:border-box; }
.area-header{ grid-area:header; } .area-left{ grid-area:left; min-height:0; }
.area-stage{ grid-area:stage; min-height:0; position:relative; overflow:hidden; }
.area-right{ grid-area:right; min-height:0; }
.glass{ background:var(--glass); border:1px solid var(--stroke); border-radius:20px;
  backdrop-filter:blur(16px); box-shadow:0 20px 60px rgba(0,0,0,0.45); min-height:0; }
.zhead{ height:100%; display:flex; align-items:center; gap:14px; padding:0 18px; }
.zhead-name{ font-size:1.2rem; font-weight:900; letter-spacing:0.1em; color:#c9a84c; }
.zhead-sub{ font-size:0.6rem; color:rgba(255,255,255,0.4); letter-spacing:0.12em; text-transform:uppercase; }
.zback{ padding:8px 20px; border-radius:10px;
  background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08));
  border:1px solid rgba(201,168,76,0.35); color:#fff; font-size:0.82rem; }
.panel-title{ padding:12px 16px; color:rgba(255,255,255,0.92); font-weight:900; letter-spacing:.12em;
  text-transform:uppercase; font-size:11px; border-bottom:1px solid rgba(255,255,255,0.08); }
.left-col{ height:100%; display:flex; flex-direction:column; gap:12px; min-height:0; }
.file-list{ padding:8px 12px; font-family:monospace; font-size:11px; overflow:auto; }
.stage-monitor{ height:100%; display:flex; flex-direction:column; overflow:hidden; }
.stage-content{ flex:1; min-height:0; overflow:hidden; padding:18px; padding-bottom:90px; }
.split-view{ height:100%; display:flex; gap:18px; min-height:0; }
.chat-col,.report-col{ flex:1; min-height:0; min-width:0; display:flex; flex-direction:column; }
.col-cap{ font-size:0.62rem; color:rgba(255,255,255,0.4); letter-spacing:0.1em;
  text-transform:uppercase; margin-bottom:6px; padding-left:4px; }
.chat-log,.viewer{ flex:1; min-height:0; border-radius:18px; border:1px solid rgba(255,255,255,0.08);
  background:rgba(255,255,255,0.03); overflow-y:auto; padding:14px; font-family:monospace;
  font-size:13px; color:rgba(255,255,255,0.86); white-space:pre-wrap; word-break:break-word; }
.viewer{ border-color:rgba(201,168,76,0.30); }
.chat-msg-user{ background:rgba(160,160,184,0.08); border-left:3px solid rgba(160,160,184,0.5);
  padding:8px 12px; margin:8px 0; border-radius:0 8px 8px 0; }
.chat-msg-zhitel{ background:rgba(201,168,76,0.08); border-left:3px solid rgba(201,168,76,0.6);
  padding:8px 12px; margin:8px 0; border-radius:0 8px 8px 0; }
.chat-msg-system{ color:rgba(255,255,255,0.5); font-style:italic; padding:4px 0; }
.floating-console{ position:absolute; left:50%; bottom:20px; transform:translateX(-50%);
  width:min(820px,calc(100% - 80px)); z-index:50; display:flex; align-items:center; gap:8px;
  padding:10px 12px; border-radius:50px; background:rgba(13,17,23,0.85);
  border:1px solid rgba(255,255,255,0.15); backdrop-filter:blur(20px); }
.floating-console input{ width:100%; border-radius:40px; border:1px solid rgba(255,255,255,0.10);
  background:rgba(255,255,255,0.06); padding:12px 16px; color:rgba(255,255,255,0.92); outline:none; font-family:monospace; }
.send-button{ border-radius:40px !important; border:2px solid rgba(201,168,76,0.55) !important;
  background:linear-gradient(135deg,rgba(201,168,76,0.30),rgba(201,168,76,0.18)) !important;
  color:#fff !important; font-weight:900 !important; padding:12px 24px !important; }
.right-col{ height:100%; display:flex; flex-direction:column; gap:12px; }
.zavatar{ flex-shrink:0; height:240px; border-radius:20px; border:1px solid rgba(255,255,255,0.10);
  background:rgba(255,255,255,0.04); display:grid; place-items:center; overflow:hidden; position:relative; }
.zavatar img{ width:100%; height:100%; object-fit:cover; border-radius:19px; }
.zavatar-cap{ position:absolute; bottom:0; left:0; right:0; padding:12px;
  background:linear-gradient(transparent,rgba(0,0,0,0.85)); }
.zavatar-cap .nm{ font-size:1.0rem; font-weight:800; color:#c9a84c; }
.zavatar-cap .role{ font-size:0.55rem; color:rgba(255,255,255,0.55); text-transform:uppercase; letter-spacing:0.08em; }
.runs-panel{ flex:1; min-height:0; display:flex; flex-direction:column; overflow:hidden; }
.zcore{ padding:12px 16px; font-size:0.72rem; color:rgba(255,255,255,0.6); font-style:italic; line-height:1.5; }
.nicegui-content{ overflow:hidden !important; height:100% !important; }
"""


def page_zhitel(zid: str = ""):
    p, dom = find_dom(zid) if zid else (None, None)

    # статика дома жителя + ковчега (общий фон прибытия)
    try:
        from nicegui import app
        if dom is not None and dom.exists():
            app.add_static_files(f"/zhitel-static/{dom.name}", str(dom))
        if KOVCHEG_DIR.exists():
            app.add_static_files("/kovcheg-static", str(KOVCHEG_DIR))
    except Exception:
        pass

    ui.add_head_html(f"<style>{ZHITEL_CSS}</style>")

    # ФОН по маске (шов): пока активной маски нет → общий/дефолт
    bg = _bg_for_mask(dom, mask=None)
    if bg:
        ui.add_head_html(f"<style>#zbg{{background-image:url('{bg}')!important;}}</style>")
    ui.html('<div id="zbg"></div>')

    if p is None:
        # житель не найден — список выбора
        with ui.element("div").style("position:fixed; inset:0; display:grid; place-items:center;"):
            with ui.element("div").classes("glass").style("padding:30px; max-width:420px;"):
                ui.html('<div class="zhead-name">КАБИНЕТ ЖИТЕЛЯ</div>'
                        '<div class="zhead-sub" style="margin-bottom:16px;">кого открыть?</div>')
                for z in list_zhiteli():
                    nm = z.get("Official_Name", "?")
                    zi = z.get("ID_Object", "")
                    ui.button(nm, on_click=lambda zi=zi: ui.navigate.to(f"/zhitel/{zi}")) \
                        .props("flat no-caps").style(
                        "width:100%; text-align:left; margin:4px 0; padding:10px 14px; border-radius:10px;"
                        "background:rgba(201,168,76,0.10); border:1px solid rgba(201,168,76,0.30); color:#fff;")
                if not list_zhiteli():
                    ui.html('<div style="color:rgba(255,255,255,0.4);">— жителей ещё нет —</div>')
                ui.button("← к Брату", on_click=lambda: ui.navigate.to("/brat")) \
                    .props("flat").style("margin-top:14px; color:rgba(255,255,255,0.5);")
        return

    name = p.get("Official_Name", "?")
    rank = p.get("Social_Rank", "") or p.get("Profession", "")
    core_phrase = p.get("Core_Phrase", "")
    state = {"chat": [], "model": ""}
    refs = {"chat": None, "viewer": None, "input": None, "files": None}

    def update_chat():
        el = refs["chat"]
        if not el: return
        el.clear()
        with el:
            if not state["chat"]:
                ui.html(f'<div class="chat-msg-system">{name} здесь. Скажи слово.</div>')
            for m in state["chat"]:
                esc = m["content"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                cls = "chat-msg-user" if m["role"]=="user" else "chat-msg-zhitel"
                who = "ШЕФ" if m["role"]=="user" else name
                ui.html(f'<div class="{cls}"><b>{who}:</b> {esc}</div>')

    def update_viewer():
        # ЯКОРЬ — кишки жителя. Грузим САМУ личность, не папку.
        el = refs["viewer"]
        if not el: return
        el.clear()
        with el:
            parts = ["### Якорь — кто она\n"]
            hist = p.get("Hidden_History", "")
            if hist:
                parts.append(f"**Скрытая история.** {hist}\n")
            sens = p.get("Sensory_Response", "")
            if sens:
                parts.append(f"**Что чувствует.** {sens}\n")
            anch = p.get("Anchor_Points", "")
            if anch:
                parts.append(f"**Якоря.** {anch}\n")
            taste = p.get("Hidden_Taste", "")
            if taste:
                parts.append(f"**Скрытый вкус.** {taste}\n")
            pull = p.get("Pull_Vector", "")
            if pull:
                parts.append(f"**Тянет к.** {pull}\n")
            dna = p.get("DNA_Static", {})
            if dna:
                dna_str = " · ".join(f"{k.split('_')[0]} {v}" for k, v in dna.items())
                parts.append(f"**Натура.** {dna_str}\n")
            if len(parts) == 1:
                parts.append("_якорь пуст — кишки ещё не вписаны_")
            ui.markdown("\n".join(parts))

    def update_files():
        el = refs["files"]
        if not el: return
        el.clear()
        with el:
            ui.html('<div style="opacity:0.4; font-size:11px; padding:4px;">— руды нет —</div>')

    async def send():
        inp = refs["input"]
        if not inp or state.get("waiting"):
            return
        t = (inp.value or "").strip()
        if not t:
            return
        state["chat"].append({"role":"user","content":t})
        inp.set_value("")
        update_chat()
        state["waiting"] = True
        await asyncio.sleep(0.03)

        # ── DVIZHOK_V_KABINET_V1: реальный вдох, если дом найден ──
        stol = None
        dvizhok = None
        if dom is not None and (dom / "passport.json").exists():
            try:
                dvizhok = Dvizhok(dom)
                tonus, sila = _otsenit_tonus_silu(t)
                vdoh_res = dvizhok.vdoh(kontekst="общение", sila=sila,
                                        svezhest=1.0, tonus=tonus)
                stol = dvizhok.vydoh_stol(fakt=t, vdoh_result=vdoh_res)
            except Exception as _e:
                stol = None

        if stol is not None:
            if stol.get('ядро'):
                soul = (
                    f"Ты — {stol['кто_я']}, житель Грондхейма. Говоришь от первого лица, "
                    f"живым голосом, не как ассистент.\n"
                    f"Твоё ядро (коронная фраза): «{stol['ядро']}»\n"
                )
            else:
                soul = (
                    f"Ты — {stol['кто_я']}, житель Грондхейма. "
                    f"Говоришь от первого лица, живым голосом, не как ассистент.\n"
                )
            # YAKORYA_V_SOUL_V1: личность — то же, что правая колонка
            # кабинета показывает Шефу. Пустые поля пропускаем, чтобы
            # не раздувать промпт строками без содержания.
            if stol.get('история'):
                soul += f"Твоя скрытая история: {stol['история']}\n"
            if stol.get('чувство'):
                soul += f"Как ты чувствуешь мир: {stol['чувство']}\n"
            if stol.get('якоря'):
                soul += f"Твои незыблемые якоря: {stol['якоря']}\n"
            if stol.get('скрытый_вкус'):
                soul += f"Твой скрытый вкус (эстетика): {stol['скрытый_вкус']}\n"
            if stol.get('тянет_к'):
                soul += f"Тебя тянет к: {stol['тянет_к']}\n"
            if stol.get('натура'):
                _nat = stol['натура']
                if isinstance(_nat, dict) and _nat:
                    _nat_str = " · ".join(f"{k.split('_')[0]} {v}" for k, v in _nat.items())
                    soul += f"Твоя натура (черты характера): {_nat_str}\n"

            soul += (
                f"Сейчас твой заряд (внутреннее состояние): {stol['заряд']} "
                f"(от -1 до 1; отрицательный — тревога/обида, положительный — тепло/радость, "
                f"0 — покой).\n"
                f"Тебе открыты слои памяти: {', '.join(stol['открыто'])}.\n"
                f"Отвечай коротко, по-человечески, исходя из своей личности выше и текущего "
                f"заряда — не упоминай слова 'заряд' или 'слои' напрямую, просто веди себя в тон."
            )
            messages = [{"role": "system", "content": soul}]
            for m in state["chat"][-12:]:
                role = "user" if m["role"] == "user" else "assistant"
                messages.append({"role": role, "content": m["content"]})
            reply = await call_zhitel_llm(messages, state.get("model"))
            try:
                dvizhok.sохранить()
            except Exception:
                pass
        else:
            reply = "(дом не найден или паспорт пуст — движок не дышит. Кабинет-каркас.)"

        state["chat"].append({"role": "zhitel", "content": reply})
        state["waiting"] = False
        update_chat()

    with ui.element("div").classes("app-container"):
        # HEADER
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass zhead"):
                _sost = "ковчег · прибытие" if not p.get("прописка") else (rank or "житель")
                ui.html(f'<div><div class="zhead-name">{name}</div>'
                        f'<div class="zhead-sub">{_sost}</div></div>')
                ui.element("div").style("flex:1")
                ui.button("карта", on_click=lambda: ui.navigate.to("/karta")) \
                    .props("flat no-caps").classes("zback").style("margin-right:8px;")
                ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")) \
                    .props("flat no-caps").classes("zback")

        # LEFT — загрузчик
        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):
                with ui.element("div").classes("glass").style("flex:1; overflow:hidden;"):
                    ui.html('<div class="panel-title">⛏ руда — входящее</div>')
                    ui.upload(multiple=True, auto_upload=True).props("flat color=amber").style("margin:8px;")
                    refs["files"] = ui.element("div").classes("file-list")
                    update_files()

        # STAGE — два поля: чат + отчёты
        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("glass stage-monitor"):
                with ui.element("div").classes("stage-content"):
                    with ui.element("div").classes("split-view"):
                        with ui.element("div").classes("chat-col"):
                            ui.html('<div class="col-cap">чат</div>')
                            refs["chat"] = ui.element("div").classes("chat-log")
                            update_chat()
                        with ui.element("div").classes("report-col"):
                            ui.html('<div class="col-cap">отчёты</div>')
                            refs["viewer"] = ui.element("div").classes("viewer")
                            update_viewer()
                with ui.element("div").classes("floating-console"):
                    refs["input"] = ui.input(placeholder=f"скажи {name}...").props("borderless").style("flex:1")
                    refs["input"].on("keydown.enter", lambda e: asyncio.create_task(send()))  # DVIZHOK_V_KABINET_V1
                    ui.button("ОТПРАВИТЬ", on_click=send).classes("send-button")

        # RIGHT — аватар + приборы
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                with ui.element("div").classes("zavatar"):
                    av = _avatar_url(dom, p)
                    if av:
                        ui.html(f'<img src="{av}" onerror="this.style.display=\'none\'">')
                    else:
                        ui.html('<div style="font-size:3rem; color:rgba(201,168,76,0.5);">⬡</div>')
                    ui.html(f'<div class="zavatar-cap"><div class="nm">{name}</div>'
                            f'<div class="role">{rank}</div></div>')
                with ui.element("div").classes("glass runs-panel"):
                    ui.html('<div class="panel-title">ковчег · прибытие</div>')
                    if core_phrase:
                        ui.html(f'<div class="zcore">«{core_phrase}»</div>')
                    _propiska = p.get("прописка")
                    if not _propiska:
                        ui.html('<div class="zcore" style="opacity:0.7;">⬡ в ковчеге — '
                                'приземлилась, ждёт прописки. Город ещё не принял.</div>')
                    else:
                        ui.html(f'<div class="zcore" style="opacity:0.7;">⬡ прописана: {_propiska}</div>')


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/zhitel/{zid}")
    def _z(zid: str = ""):
        page_zhitel(zid)
    @ui.page("/zhitel")
    def _z0():
        page_zhitel("")
    ui.run(title="Кабинет жителя", port=8104, reload=False)