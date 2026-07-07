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
import sys
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


def _izvlech_memory_request(text: str) -> str:
    """PATCH_ZHITEL_VSPOMINAET: первая строка MEMORY_REQUEST: <запрос> из ответа жителя."""
    for line in (text or "").splitlines():
        if "MEMORY_REQUEST:" in line:
            return line.split("MEMORY_REQUEST:", 1)[1].strip()
    return ""


def _ubrat_memory_request(text: str) -> str:
    """PATCH_ZHITEL_VSPOMINAET: технические строки MEMORY_REQUEST вычищаются из видимого ответа."""
    lines = [l for l in (text or "").splitlines() if "MEMORY_REQUEST:" not in l]
    return "\n".join(lines).strip()

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

# PATCH_FON_PO_PROPISKE: тот же путь, что LOKACII_DIR в ui_lokacia.py — не
# импортируем оттуда (ui_lokacia сам импортирует нас, цикл).
LOKACII_DIR = _ROOT / "GRONDHEIM_CITY" / "локации"


def _bg_for_mask(dom: Path, mask: str = None, propiska: str = None) -> str:
    """Путь фона кабинета. Порядок: активная маска → жильё жителя →
    прописка (образ локации) → КОВЧЕГ → дефолт.
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
    # PATCH_FON_PO_PROPISKE: 3. прописка — берём тот же image.*, что локация
    # показывает на своей странице (/lokacia/{id}). Отдельный bg.*
    # заводить не нужно — образ места один на всех, кто там бывает.
    if propiska:
        loc_dir = LOKACII_DIR / propiska
        if loc_dir.exists():
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                cand = loc_dir / ("image" + ext)
                if cand.exists():
                    return f"/lokacia-static/{propiska}/image{ext}"
    # 4. КОВЧЕГ — общий фон прибытия (нет маски, нет своего жилья, нет прописки)
    if KOVCHEG_DIR.exists():
        for ext in (".jpg", ".png", ".jpeg", ".webp"):
            cand = KOVCHEG_DIR / ("bg" + ext)
            if cand.exists():
                return "/kovcheg-static/bg" + ext
    return ""   # дефолт — тёмный градиент с золотом (CSS).


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

/* ZHITEL_PANEL_ZHIVAYA_V1 — плашка локации + показатели */
.zloc-strip{ flex-shrink:0; display:flex; flex-direction:column; gap:0;
  border-radius:14px; border:1px solid rgba(255,255,255,0.08);
  background:rgba(255,255,255,0.03); overflow:hidden; }
.zloc-thumb{ width:100%; aspect-ratio:1/1; flex-shrink:0;
  background-size:cover; background-position:center;
  border-bottom:1px solid rgba(201,168,76,0.25); }
.zloc-meta{ min-width:0; padding:10px 12px; text-align:center; }
.zloc-zag{ font-size:0.8rem; font-weight:800; color:#c9a84c;
  text-transform:uppercase; letter-spacing:0.06em; }
.zloc-pod{ font-size:0.58rem; color:rgba(255,255,255,0.5);
  letter-spacing:0.04em; margin-top:3px; }
.zpok{ padding:10px 16px; display:flex; flex-direction:column; gap:9px; }
.zpok-row{ display:flex; flex-direction:column; gap:3px; }
.zpok-lab{ display:flex; justify-content:space-between; font-size:0.56rem;
  text-transform:uppercase; letter-spacing:0.08em; color:rgba(255,255,255,0.5); }
.zpok-lab b{ color:rgba(255,255,255,0.85); font-weight:700; }
.zpok-bar{ height:6px; border-radius:4px; background:rgba(255,255,255,0.08);
  overflow:hidden; }
.zpok-fill{ height:100%; border-radius:4px; }
.zpok-bar--zaryad{ position:relative; }
.zpok-bar--zaryad .zpok-fill{ position:absolute; top:0; bottom:0; }
.zpok-mid{ position:absolute; left:50%; top:-2px; bottom:-2px; width:1px;
  background:rgba(255,255,255,0.4); z-index:2; }
.zpok-dna{ font-size:0.55rem; color:rgba(255,255,255,0.45);
  font-family:'JetBrains Mono',monospace; line-height:1.6;
  padding-top:4px; border-top:1px solid rgba(255,255,255,0.06); }
"""


def _lokacia_thumb(loc_id: str) -> str:
    """Мини-образ локации где житель сейчас. image.* той же локации,
    что даёт фон. Нет — пусто (плашка не рисуется, не пустой квадрат)."""
    if not loc_id:
        return ""
    loc_dir = LOKACII_DIR / loc_id
    if not loc_dir.exists():
        return ""
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (loc_dir / ("image" + ext)).exists():
            return f"/lokacia-static/{loc_id}/image{ext}"
    return ""


def _lokacia_name(loc_id: str) -> str:
    """Имя локации из её паспорта (для подписи). Нет — сам id."""
    if not loc_id:
        return ""
    import json as _j
    pp = LOKACII_DIR / loc_id / "passport.json"
    if pp.exists():
        try:
            return _j.loads(pp.read_text(encoding="utf-8")).get("Official_Name", loc_id)
        except Exception:
            pass
    return loc_id


def _mesto_podpis(dom, loc_id: str, p: dict):
    """Живой заголовок места: ГДЕ житель сейчас (sostoyanie.gde_ya).
    Возвращает (заголовок, подпись). Не хардкод 'ковчег'."""
    imya_loc = _lokacia_name(loc_id) if loc_id else ""
    doma = True
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo) not in sys.path:
            sys.path.insert(0, str(_repo))
        import sostoyanie as _sost
        r = _sost.gde_ya(dom)
        doma = r.get("дома", True)
    except Exception:
        pass
    if not loc_id:
        return ("В КОВЧЕГЕ", "приземлилась, ждёт прописки")
    if doma:
        return (f"ДОМА · {imya_loc}", "по месту прописки")
    return (f"НА МЕСТЕ · {imya_loc}", "сейчас здесь")


def _pokazateli_html(p: dict) -> str:
    """Живые показатели жителя из паспорта: заряд, оптика, натура.
    Как в старом кабинете — под аватаром жизненные показатели."""
    try:
        charge = float(p.get("_charge", 0.0) or 0.0)
    except (TypeError, ValueError):
        charge = 0.0
    mut = abs(charge)
    # оптика словом (та же шкала, что kalibrovka_core)
    if mut < 0.25:
        optika, ocolor = "чисто", "rgba(80,250,123,0.9)"
    elif mut < 0.55:
        optika, ocolor = "ровно", "rgba(201,168,76,0.9)"
    elif mut < 0.8:
        optika, ocolor = "штырит", "rgba(255,160,60,0.9)"
    else:
        optika, ocolor = "колбасит", "rgba(255,80,80,0.9)"
    # ZHITEL_ZARYAD_BIPOLAR_V1: полоса ДВУСТОРОННЯЯ — ноль в центре,
    # плюс растёт вправо, минус растёт влево (не только модуль вправо)
    znak = "+" if charge >= 0 else "−"
    zcolor = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    _half = min(1.0, mut) * 50  # половина шкалы = сила 0..1 -> 0..50%
    zleft = 50 if charge >= 0 else 50 - _half
    zwidth = _half

    dna = p.get("DNA_Static", {}) or {}
    dna_str = " · ".join(f"{k.split('_')[0]} {v}" for k, v in dna.items())

    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar zpok-bar--zaryad"><div class="zpok-mid"></div>'
        f'<div class="zpok-fill" '
        f'style="left:{zleft}%; width:{zwidth}%; background:{zcolor};"></div></div></div>'
        f'<div class="zpok-row"><div class="zpok-lab">оптика<b style="color:{ocolor};">{optika}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" '
        f'style="width:{int((1-mut)*100)}%; background:{ocolor};"></div></div></div>'
        + (f'<div class="zpok-dna">{dna_str}</div>' if dna_str else '')
        + '</div>'
    )


def page_zhitel(zid: str = ""):
    p, dom = find_dom(zid) if zid else (None, None)
    propiska = p.get("прописка") if p else None  # запасной вариант — дом

    # PATCH_ZHITEL_TEKUSHAYA_LOKACIA: фон карточки — по ЖИВОМУ месту
    # (sostoyanie.gde_ya), не по вечной прописке. Житель на сессии —
    # видим Биржу, не Торговый Квартал. Сам замысел: карта переносит
    # "в ту локацию где он есть", не в дом по умолчанию.
    tekushaya_lokacia = propiska
    if dom is not None:
        try:
            _repo = Path(__file__).resolve().parent.parent
            if str(_repo) not in sys.path:
                sys.path.insert(0, str(_repo))
            import sostoyanie as _sost
            _r = _sost.gde_ya(dom)
            if _r.get("локация"):
                tekushaya_lokacia = _r["локация"]
        except Exception:
            pass  # sostoyanie нет — тихий откат на прописку, как было

    # статика дома жителя + ковчега (общий фон прибытия) + ТЕКУЩЕЙ локации
    try:
        from nicegui import app
        if dom is not None and dom.exists():
            app.add_static_files(f"/zhitel-static/{dom.name}", str(dom))
        if KOVCHEG_DIR.exists():
            app.add_static_files("/kovcheg-static", str(KOVCHEG_DIR))
        if tekushaya_lokacia:  # своя статика, не ждём захода на /lokacia/{id}
            _loc_dir = LOKACII_DIR / tekushaya_lokacia
            if _loc_dir.exists():
                app.add_static_files(f"/lokacia-static/{tekushaya_lokacia}", str(_loc_dir))
    except Exception:
        pass

    ui.add_head_html(f"<style>{ZHITEL_CSS}</style>")

    # ФОН по маске → ТЕКУЩЕМУ месту (не прописке!) → ковчегу
    bg = _bg_for_mask(dom, mask=None, propiska=tekushaya_lokacia)
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
            parts = ["### Якорь — кто он?\n"]
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
            if stol.get('дом'):  # PATCH_DOM_V_DUSHU: дом несёшь в себе ВСЕГДА
                soul += f"Твой дом, который ты носишь в себе всегда: {stol['дом']}\n"
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
            # PATCH_ZHITEL_VSPOMINAET: воля жителя — подсказка. Не «заряд открыл —
            # на, читай», а сам решает, что и когда поднять из памяти.
            soul += (
                "\nУ тебя есть своя память — события прошлых разговоров. Если "
                "что-то кажется знакомым, но не помнишь точно — напиши в ответе "
                "отдельной строкой MEMORY_REQUEST: <что вспомнить> и тебе "
                "поднимется это из твоей памяти."
            )
            messages = [{"role": "system", "content": soul}]
            for m in state["chat"][-12:]:
                role = "user" if m["role"] == "user" else "assistant"
                messages.append({"role": role, "content": m["content"]})
            reply = await call_zhitel_llm(messages, state.get("model"))
            # PATCH_ZHITEL_VSPOMINAET: житель сам решил вспомнить — один подъём за ход,
            # без петель. Шеф видит только финальный ответ.
            _mem_q = _izvlech_memory_request(reply)
            if _mem_q and dvizhok is not None:
                try:
                    _naydeno = dvizhok.vspomnit(_mem_q)
                except Exception:
                    _naydeno = ""
                _vtoroy = list(messages)
                _vtoroy.append({"role": "assistant", "content": reply})
                if _naydeno:
                    _vtoroy.append({"role": "user", "content": (
                        f"(Из твоей памяти поднято по запросу «{_mem_q}»:\n"
                        f"{_naydeno}\n"
                        f"Ответь заново, уже помня это, живым голосом. "
                        f"Механизм памяти не упоминай.)")})
                else:
                    _vtoroy.append({"role": "user", "content": (
                        f"(В твоей памяти по запросу «{_mem_q}» ничего не нашлось — "
                        f"этого следа нет. Ответь заново честно, не выдумывая. "
                        f"Механизм памяти не упоминай.)")})
                reply = await call_zhitel_llm(_vtoroy, state.get("model"))
            reply = _ubrat_memory_request(reply) or reply
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
                ui.button("карта", on_click=lambda: ui.navigate.to("/grondheim")) \
                    .props("flat no-caps").classes("zback").style("margin-right:8px;")
                ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")) \
                    .props("flat no-caps").classes("zback")

        # LEFT — загрузчик
        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):
                with ui.element("div").classes("glass").style("flex:1; overflow:hidden;"):
                    ui.html('<div class="panel-title">⛏ руда — входящее</div>')
                    ui.upload(multiple=True, auto_upload=True).props("flat color=amber").style("margin:8px;")
                    # ZHITEL_LOC_VLEVO_V1: аватарка локации где житель сейчас —
                    # под загрузчиком руды, над списком файлов
                    _loc_thumb_l = _lokacia_thumb(tekushaya_lokacia)
                    if _loc_thumb_l:
                        _lz, _lp = _mesto_podpis(dom, tekushaya_lokacia, p)
                        ui.html(
                            f'<div class="zloc-strip" style="margin:8px;">'
                            f'<div class="zloc-thumb" style="background-image:url(\'{_loc_thumb_l}\');"></div>'
                            f'<div class="zloc-meta"><div class="zloc-zag">{_lz}</div>'
                            f'<div class="zloc-pod">{_lp}</div></div></div>'
                        )
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

        # RIGHT — аватар + ЖИВЫЕ показатели (ZHITEL_PANEL_ZHIVAYA_V1)
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

                # место (заголовок) для панели показателей — считаем здесь,
                # сама плашка локации переехала ВЛЕВО (ZHITEL_LOC_VLEVO_V1)
                _mesto_zag, _mesto_pod = _mesto_podpis(dom, tekushaya_lokacia, p)

                # ЖИВЫЕ ПОКАЗАТЕЛИ агента (как в старом кабинете — под точкой)
                with ui.element("div").classes("glass runs-panel"):
                    ui.html(f'<div class="panel-title">{_mesto_zag}</div>')
                    ui.html(_pokazateli_html(p))
                    if core_phrase:
                        ui.html(f'<div class="zcore">«{core_phrase}»</div>')


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/zhitel/{zid}")
    def _z(zid: str = ""):
        page_zhitel(zid)
    @ui.page("/zhitel")
    def _z0():
        page_zhitel("")
    ui.run(title="Кабинет жителя", port=8104, reload=False)
# ZHITEL_KARTA_BIG_LOC_V1 — маркер идемпотентности

# ZHITEL_OPTIKA_SLOVA_V2 — маркер идемпотентности
