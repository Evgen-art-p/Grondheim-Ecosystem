# -*- coding: utf-8 -*-
# ARKHIV_KABINET_V1 — КАБИНЕТ АРХИВА ГОРОДА
"""
АРХИВ ГОРОДА · КАБИНЕТ · /arkhiv

СТИЛЬ — калька Академии (ui_akademia.py), та же сетка/хедер/стол/
правая колонка. Академия самостоятельный модуль и не импортирует
Архив, поэтому CSS — копия, не ссылка (Закон Двух Стандартов).

ЧЕМ ОТЛИЧАЕТСЯ ОТ АКАДЕМИИ (слово Шефа):
  Академия — до 10 парт, много вакансий. Архив — ОДИН пост, Хранитель.
  Пост — честная вакансия (закон rezidenty.py: личность не прикручена
  к роли), кто сядет — решает Брат через менеджера резидентов, этот
  файл никого не назначает сам. Поэтому вместо сетки мест — один
  пузырёк в шапке: клик по нему «включает» Хранителя — открывает
  аватар и чат. Пусто — пузырёк вакантный, клик честно об этом скажет.

  Справа — не книги, а АРХИВНЫЕ ЗАПИСИ (документы/чертежи/переписка/
  медиа/прочее), тот же загрузчик-на-полку, что был у библиотеки.

  Кнопка «Библиотека» ведёт по-настоящему в Академию (не заглушка —
  соседний модуль уже построен). «Выход на Маяк» здесь не отдельная
  кнопка — это встроенное поведение khranitel_arkhiva.sprosit(): архив
  пуст по запросу -> Хранитель сам выходит на Маяк за внешним миром
  (тот же механизм, что у библиотекаря Академии).

`шесть·проверено·до·корня`
"""
import os
import sys
import json
import base64  # PATCH_ARKHIV_VIZUAL_V1: кодируем картинку в data URL для мультимодального вызова
from pathlib import Path
from datetime import datetime, timezone

from nicegui import ui, app

# BELYY_SHRIFT_V1: читаемость на тёмном — см.
# postavit_belyy_shrift.py. Красим только то, что
# рисует Quasar своей светлой темой внутри наших
# тёмных карточек.
_BELYY_SHRIFT = r"""
/* BELYY_SHRIFT_V1 — читаемость на тёмном.
   Карточки диалогов рисуем мы (тёмные), а подписи внутри — Quasar по
   своей СВЕТЛОЙ теме. Отсюда тёмно-серые буквы на чёрном: в окне
   перевозки так пропадали имена жителей у галочек.
   Красим только то, что отдано Quasar'у. Кнопки и наши собственные
   раскрашенные надписи не трогаем — у них цвет задан руками. */
.q-dialog .q-card,
.q-dialog .q-card .q-item__label,
.q-dialog .q-card label,
.q-checkbox__label,
.q-radio__label,
.q-toggle__label,
.q-field__native,
.q-field__input,
.q-field__label,
.q-field__prefix,
.q-field__suffix,
.q-item__label,
.q-tab__label,
.q-select__dropdown-icon,
.q-menu .q-item,
.q-menu .q-item__label {
  color: rgba(255,255,255,0.92) !important;
}

/* Подсказка в пустом поле — белая, но приглушённая: она не должна
   спорить с тем, что человек уже вписал. */
.q-field__native::placeholder,
.q-field__input::placeholder,
.q-placeholder::placeholder {
  color: rgba(255,255,255,0.45) !important;
}

/* Выпадающий список Quasar рисует НЕ внутри нашей карточки, а
   отдельным слоем поверх страницы — своей темой. Без этого он
   оставался светлым пятном с белым текстом на белом. */
.q-menu {
  background: #0d1117 !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}
"""


# ARKHIV_MODEL_SEL_V1: тот же каталог, что в кабинете Брата (ui_brat.py).
_OPENROUTER_MODEL_ENV = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
MODELS_CATALOG = [
    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},
    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},
    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},
    {"id": "openai/gpt-4o-mini-2024-07-18",              "name": "GPT-4o mini",      "price": "$0,15 / $0,60"},
    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},
    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},
]
DEFAULT_MODEL = _OPENROUTER_MODEL_ENV or MODELS_CATALOG[0]["id"]

# ═══════════════════════════════════════════════════════════
# PATCH_ARKHIV_VIZUAL_V1 -- визуальный разбор изображения. НЕ
# редактирование -- только анализ. Самодостаточная функция (свой
# os.getenv) -- Закон Двух Стандартов, копия не ссылка.
# ═══════════════════════════════════════════════════════════
_KARTINKA_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                  ".webp": "image/webp", ".gif": "image/gif"}


async def _analiz_kartinki(path: Path, model: str = "", vopros: str = "") -> str:
    """Мультимодальный вызов той же LLM: картинка вместо/вместе с текстом
    в content сообщения. Честно про ошибки."""
    _key = os.getenv("OPENROUTER_API_KEY", "")
    if not _key:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    try:
        data = path.read_bytes()
    except Exception as e:
        return f"⚠ не прочитать файл: {e}"
    mime = _KARTINKA_MIME.get(path.suffix.lower(), "image/png")
    url = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    vopros = vopros or "Опиши, что на изображении, коротко и по делу."
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": vopros},
            {"type": "image_url", "image_url": {"url": url}},
        ],
    }]
    import httpx
    # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
    # из некоторых регионов -- та же настройка, что и в остальном городе.
    _proxy = os.getenv("PROXY_URL", "") or None
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ разбор не удался: {e}"

_HERE = Path(__file__).resolve().parent           # Архив/
_REPO = _HERE.parent                              # корень репо
for _p in (_REPO, _REPO / "ГОРОД", _HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ── ДАННЫЕ АРХИВА (не код) ───────────────────────────────────
KVARTAL = "Архив"
_DATA    = _REPO / "GRONDHEIM_CITY" / KVARTAL
_RUDA    = _DATA / "руда"
_ARKHIV  = _DATA / "архив"
_KATALOG = _ARKHIV / "каталог.json"

_KOVCHEG = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"
_LOKACII = _REPO / "GRONDHEIM_CITY" / "локации"

# ЗДАНИЕ: локация «Архив Города». Номер поправь, если Шеф перенумерует
# папку локации — сейчас 0015 (следующий свободный после 0014_EXCHANGE).
ZDANIE = "0015_GRONDHEIM_ARCHIVE"

# Пост заводится пустой вакансией — ровно как «библиотекарь» в
# Академии. Личность НЕ прикручена к роли (закон rezidenty.py): кто
# сядет на пост — решает Брат через менеджера резидентов, не этот файл.
POST_ID = "khranitel_arkhiva"

RAZDELY = ["документы", "чертежи", "переписка", "медиа", "прочее"]

TEKST_EXT = {".txt", ".md", ".rtf"}
KARTINKA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

_STATIC = "arkhiv-static"
_BG_MOUNTED = {"done": False}


# ═══════════════════════════════════════════════════════════
# ДИСК — читаем честно, пустое отдаём пустым
# ═══════════════════════════════════════════════════════════

def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ensure_dirs():
    """Архив заводит свой двор сам — не падаем на пустом городе.

    Заводим ТОЛЬКО пост-вакансию (khranitel_arkhiva), если его ещё нет
    на диске. Кто на него сядет — решает Брат через rezidenty.posadit(),
    отдельно и когда угодно. Роль и личность здесь развязаны (закон
    rezidenty.py) — этот файл никого не назначает сам.
    """
    for d in (_DATA, _RUDA, _RUDA / "тексты", _RUDA / "изображения", _ARKHIV):
        d.mkdir(parents=True, exist_ok=True)
    for razdel in RAZDELY:
        (_ARKHIV / razdel).mkdir(parents=True, exist_ok=True)
    if not _KATALOG.exists():
        _write_json(_KATALOG, {"записи": [], "разделы": RAZDELY})

    try:
        import rezidenty
        if not rezidenty.get_post(POST_ID):
            rezidenty.zavesti_post(POST_ID, "Хранитель Архива",
                                   gde=ZDANIE, dvizhok="khranitel_arkhiva")
    except Exception:
        pass  # честная тишина — кабинет откроется вакансией, не упадёт


def _keeper_imya() -> str:
    try:
        import rezidenty
        return rezidenty.kto_na_postu(POST_ID)
    except Exception:
        return ""


def _keeper_dom() -> Path | None:
    try:
        import rezidenty
        return rezidenty.dom_zhitelya(_keeper_imya())
    except Exception:
        return None


def _avatar_url(dom: Path) -> str:
    """Фото Хранителя — тот же способ, что в остальном городе."""
    if not dom or not dom.exists():
        return ""
    p = _read_json(dom / "passport.json", {}) or {}
    av = p.get("avatar", "")
    if av and (dom / av).exists():
        return f"/{_STATIC}/{dom.name}/{av}"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (dom / ("avatar" + ext)).exists():
            return f"/{_STATIC}/{dom.name}/avatar{ext}"
    return ""


def _mount_avatar_static(dom: Path):
    if not dom or not dom.exists():
        return
    try:
        app.add_static_files(f"/{_STATIC}/{dom.name}", str(dom))
    except Exception:
        pass


def _bg_url() -> str:
    """Фон кабинета — картинка Архива Города. Нет image.* — честно пусто
    (сейчас так и есть, картинка ещё не залита в паспорт локации)."""
    dom = _LOKACII / ZDANIE
    if not dom.exists():
        return ""
    if not _BG_MOUNTED["done"]:
        try:
            app.add_static_files("/arkhiv-bg", str(_LOKACII))
        except Exception:
            pass
        _BG_MOUNTED["done"] = True
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if (dom / ("image" + ext)).exists():
            return f"/arkhiv-bg/{ZDANIE}/image{ext}"
    return ""


def _bar_html(charge: float) -> str:
    """Заряд/оптика — тот же вид, что во всём городе."""
    mut = abs(charge)
    half = min(1.0, mut) * 50
    left = 50 if charge >= 0 else 50 - half
    znak = "+" if charge >= 0 else "\u2212"
    zcolor = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    if mut < 0.25:
        optika, ocolor = "чисто", "rgba(80,250,123,0.9)"
    elif mut < 0.55:
        optika, ocolor = "ровно", "rgba(201,168,76,0.9)"
    elif mut < 0.8:
        optika, ocolor = "штырит", "rgba(255,160,60,0.9)"
    else:
        optika, ocolor = "колбасит", "rgba(255,80,80,0.9)"
    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar zpok-bar--zaryad"><div class="zpok-mid"></div>'
        f'<div class="zpok-fill" style="left:{left}%; width:{half}%; background:{zcolor};"></div></div></div>'
        f'<div class="zpok-row"><div class="zpok-lab">оптика<b style="color:{ocolor};">{optika}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" style="width:{int((1-mut)*100)}%; '
        f'background:{ocolor};"></div></div></div>'
        '</div>'
    )


# ═══════════════════════════════════════════════════════════
# СТИЛЬ — снят с Академии один в один
# ═══════════════════════════════════════════════════════════

ARKHIV_CSS = r"""
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
  width:100vw; height:100vh; overflow:hidden !important;
  background: transparent !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

#bg{ position: fixed; inset: 0; z-index: -1; background-size: cover;
     background-position: center; background-color: #050510; }
#bg::after{ content:''; position:absolute; inset:0; background: rgba(5,5,16,0.88); }

.app-container{
  position: fixed; inset: 0; display: grid;
  width: 100vw; height: 100vh;
  grid-template-columns: 300px 1fr 260px;
  grid-template-rows: 80px 1fr;
  grid-template-areas:
    "header header header"
    "left   stage  right";
  gap: 20px; padding: 20px; box-sizing: border-box;
}

.area-header{ grid-area: header; }
.area-left{ grid-area: left; min-height:0; }
.area-stage{ grid-area: stage; min-height:0; position: relative; overflow: hidden; }
.area-right{ grid-area: right; min-height:0; }

.glass{
  background: var(--glass); border: 1px solid var(--stroke);
  border-radius: 20px; backdrop-filter: blur(16px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.45); min-height: 0;
}

.squad-deck{
  height: 100%; display: flex; justify-content: center; align-items: center;
  padding: 10px 16px; gap: 15px; overflow-x: auto;
}

.avatar{
  width: 44px; height: 44px; border-radius: 999px;
  border: 2px solid rgba(255,255,255,0.14);
  background-size: cover; background-position: center 18%;
  background-color: rgba(255,255,255,0.05);
  flex: 0 0 auto; display: grid; place-items: center;
  color: rgba(255,255,255,0.92); font-weight: 800; font-size: 11px;
  cursor: pointer; transition: all 0.3s ease; position: relative;
}
.avatar:hover{ border-color: rgba(201,168,76,0.40); transform: scale(1.05); }
.avatar.active{
  border-color: rgba(201,168,76,0.75);
  box-shadow: 0 0 0 2px rgba(201,168,76,0.25) inset, 0 0 30px rgba(201,168,76,0.35);
}
.avatar.vacant{ border-style: dashed; opacity: 0.4; cursor: default; }

.left-col{ height: 100%; display: flex; flex-direction: column; gap: 12px; min-height: 0; }
.asset-bay{ height: auto; max-height: 360px; flex-shrink: 0; overflow: visible; }

.panel-title{
  padding: 12px 16px; color: rgba(255,255,255,0.92); font-weight: 900;
  letter-spacing: .12em; text-transform: uppercase; font-size: 11px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.file-list{ padding: 8px 12px; max-height: 300px; overflow-y: auto;
            font-family: monospace; font-size: 11px; }

.right-col{ height: 100%; display: flex; flex-direction: column;
            justify-content: flex-start; gap: 12px; }
.right-top-slot{
  flex-shrink: 0; height: 240px; border-radius: 20px;
  border: 1px dashed rgba(255,255,255,0.14); background: rgba(255,255,255,0.04);
  display: grid; place-items: center; color: rgba(255,255,255,0.55);
  font-size: 11px; padding: 12px; text-align: center; overflow: hidden;
}

.stage-monitor{ height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.stage-toolbar{
  height: 60px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 12px; border-bottom: 1px solid rgba(255,255,255,0.08);
  flex-shrink: 0; background: rgba(13, 17, 23, 0.95);
  backdrop-filter: blur(16px); z-index: 10;
}
.stage-content{ flex: 1; min-height: 0; overflow: hidden; padding: 18px; padding-bottom: 130px; }

.split-view{ height: 100%; display: flex; gap: 18px; min-height: 0; overflow: hidden; }
.chat-log, .viewer{
  flex: 1; min-height: 0; min-width: 0; border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.03);
  overflow-y: auto; overflow-x: hidden; padding: 14px;
  font-family: monospace; font-size: 13px; color: rgba(255,255,255,0.86);
  white-space: pre-wrap; word-wrap: break-word; word-break: break-word;
}
.viewer{ border-color: rgba(201,168,76,0.30); }

.floating-console{
  position: absolute; left: 50%; bottom: 20px; transform: translateX(-50%);
  width: min(820px, calc(100% - 80px)); z-index: 50;
  display: flex; align-items: center; gap: 8px; padding: 10px 12px;
  border-radius: 50px; background: rgba(13, 17, 23, 0.85);
  border: 1px solid rgba(255,255,255,0.15); backdrop-filter: blur(20px);
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}
.floating-console input{
  width: 100%; border-radius: 40px; border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.06); padding: 12px 16px;
  color: rgba(255,255,255,0.92); outline: none; font-family: monospace;
}
.send-button{
  border-radius: 40px !important; border: 2px solid rgba(201,168,76,0.55) !important;
  background: linear-gradient(135deg, rgba(201,168,76,0.30), rgba(189,0,255,0.20)) !important;
  color: rgba(255,255,255,0.98) !important; font-weight: 900 !important;
  padding: 12px 24px !important; cursor: pointer !important;
}

.chat-msg-user{ background: rgba(201, 168, 76, 0.10);
  border-left: 3px solid rgba(201, 168, 76, 0.6); padding: 8px 12px;
  margin: 8px 0; border-radius: 0 8px 8px 0; }
.chat-msg-assistant{ background: rgba(189, 0, 255, 0.08);
  border-left: 3px solid rgba(189, 0, 255, 0.5); padding: 8px 12px;
  margin: 8px 0; border-radius: 0 8px 8px 0; }
.chat-msg-system{ color: rgba(255,255,255,0.5); font-style: italic; padding: 4px 0; }

.zpok{ padding:10px 16px; display:flex; flex-direction:column; gap:9px; }
.zpok-row{ display:flex; flex-direction:column; gap:3px; }
.zpok-lab{ display:flex; justify-content:space-between; font-size:0.56rem;
  text-transform:uppercase; letter-spacing:0.08em; color:rgba(255,255,255,0.5); }
.zpok-lab b{ color:rgba(255,255,255,0.85); font-weight:700; }
.zpok-bar{ height:6px; border-radius:4px; background:rgba(255,255,255,0.08);
  overflow:hidden; position:relative; }
.zpok-bar--zaryad .zpok-fill{ position:absolute; top:0; bottom:0; }
.zpok-mid{ position:absolute; left:50%; top:-2px; bottom:-2px; width:1px;
  background:rgba(255,255,255,0.4); z-index:2; }
.zpok-fill{ height:100%; border-radius:4px; }

.arkhiv-btn{
  padding:6px 14px; border-radius:7px; font-size:12px; font-weight:700;
  cursor:pointer; display:flex; align-items:center;
  background:rgba(255,255,255,0.03); color:rgba(255,255,255,0.55);
  border:1px solid rgba(255,255,255,0.10);
}

/* ARKHIV_MODEL_SEL_V1 — калька .brat-model-sel из ui_brat.py */
.zmodel-sel .q-field__control{ background:rgba(255,255,255,0.06)!important;
  border:1px solid rgba(255,255,255,0.12)!important; border-radius:10px!important; }

.nicegui-content { overflow: hidden !important; height: 100% !important; }
.area-stage { overflow: hidden !important; }
.area-stage > * { overflow: hidden !important; min-height: 0 !important; max-height: 100% !important; }
.stage-monitor { overflow: hidden !important; height: 100% !important; }
.stage-monitor > * { min-height: 0 !important; }
.stage-toolbar { flex-shrink: 0 !important; overflow: hidden !important; }
.stage-content { flex: 1 1 0 !important; min-height: 0 !important; overflow: hidden !important;
                 max-height: calc(100% - 60px) !important; }
.stage-content > * { min-height: 0 !important; max-height: 100% !important; overflow: hidden !important; }
.split-view { height: 100% !important; min-height: 0 !important; overflow: hidden !important; }
.split-view > * { min-height: 0 !important; overflow: hidden !important; }
.chat-log, .viewer { flex: 1 1 0 !important; min-height: 0 !important; max-height: 100% !important;
                     overflow-y: auto !important; overflow-x: hidden !important; }
"""


# ═══════════════════════════════════════════════════════════
# СТРАНИЦА
# ═══════════════════════════════════════════════════════════

def page_arkhiv() -> None:
    """Кабинет Архива Города — изнутри."""

    _ensure_dirs()
    imya = _keeper_imya()
    dom = _keeper_dom()
    zanyato = bool(imya and dom)
    if zanyato:
        _mount_avatar_static(dom)

    state = {
        "активен": False,   # ARKHIV_BUBBLE_V1: клик по пузырьку включает Хранителя
        "чат": [],
        "руда": [],
        "отчёт": "",
        "model": DEFAULT_MODEL,
    }

    def on_model_change(e):
        state["model"] = e.value

    chat_ref    = {"element": None}
    viewer_ref  = {"element": None}
    ruda_ref    = {"element": None, "uploader": None}
    zapisi_ref  = {"uploader": None, "раздел": None}
    avatar_ref  = {"element": None}
    vitals_ref  = {"element": None}
    arkhiv_ref  = {"element": None}
    input_ref   = {"element": None}
    bubble_ref  = {"element": None}

    ui.add_head_html(f"<style>{ARKHIV_CSS}</style>")
    ui.add_head_html("<style>" + _BELYY_SHRIFT + "</style>")   # BELYY_SHRIFT_V1
    _bg = _bg_url()
    ui.html(f'<div id="bg"{f" style=\"background-image:url(\'{_bg}\');\"" if _bg else ""}></div>')

    # ── чат ────────────────────────────────────────────────
    def update_chat():
        if not chat_ref["element"]:
            return
        chat_ref["element"].clear()
        with chat_ref["element"]:
            if not state["чат"]:
                if state["активен"]:
                    ui.html('<div class="chat-msg-system">SYSTEM: Архив открыт. '
                            'Тихо, как и всегда. Спрашивай — ответит честно.</div>')
                else:
                    ui.html('<div class="chat-msg-system">SYSTEM: дверь заперта. '
                            'Кликни по пузырьку Хранителя, чтобы позвать его.</div>')
                return
            for m in state["чат"]:
                if m.get("role") == "user":
                    ui.html(f'<div class="chat-msg-user"><b>ШЕФ:</b> {m.get("content","")}</div>')
                else:
                    who = m.get("кто", "СИСТЕМА")
                    ui.html(f'<div class="chat-msg-assistant"><b>{who}:</b> {m.get("content","")}</div>')

    def update_viewer(md: str):
        if not viewer_ref["element"]:
            return
        state["отчёт"] = md
        viewer_ref["element"].clear()
        with viewer_ref["element"]:
            ui.markdown(md)

    # ── аватар Хранителя (правая колонка) ───────────────────
    def update_avatar():
        if not avatar_ref["element"]:
            return
        avatar_ref["element"].clear()
        with avatar_ref["element"]:
            if state["активен"] and zanyato:
                av = _avatar_url(dom)
                if av:
                    ui.html(f'<img src="{av}" style="width:100%;height:100%;'
                            f'object-fit:cover;border-radius:19px;opacity:0.9;" '
                            f'onerror="this.style.display=\'none\'">')
                else:
                    ui.html('<div style="font-size:3rem; color:rgba(201,168,76,0.35);">⬡</div>')
            else:
                ui.html('<div style="font-size:0.75rem; color:rgba(255,255,255,0.35); '
                        'text-align:center; padding:0 16px;">кликни по пузырьку —<br>'
                        'Хранитель откроет дверь</div>')

    def update_vitals():
        if not vitals_ref["element"]:
            return
        vitals_ref["element"].clear()
        with vitals_ref["element"]:
            if state["активен"] and zanyato:
                p = _read_json(dom / "passport.json", {}) or {}
                ui.html(
                    f'<div style="padding:12px 16px 4px 16px;">'
                    f'<div style="font-size:0.6rem;color:rgba(255,255,255,0.45);'
                    f'letter-spacing:0.14em;text-transform:uppercase;">'
                    f'хранитель архива</div>'
                    f'<div style="font-size:1.15rem;font-weight:800;color:#c9a84c;'
                    f'line-height:1.3;">{imya}</div></div>')
                ui.html(_bar_html(float(p.get("_charge", 0.0) or 0.0)))
            elif zanyato:
                ui.html(
                    f'<div style="padding:12px 16px;">'
                    f'<div style="font-size:0.6rem;color:rgba(255,255,255,0.45);'
                    f'letter-spacing:0.14em;text-transform:uppercase;">пост</div>'
                    f'<div style="font-size:0.8rem;color:rgba(255,255,255,0.5);'
                    f'margin-top:2px;">{imya} — за дверью, не окликнута</div></div>')
            else:
                ui.html(
                    '<div style="padding:12px 16px;">'
                    '<div style="font-size:0.6rem;color:rgba(255,255,255,0.45);'
                    'letter-spacing:0.14em;text-transform:uppercase;">пост</div>'
                    '<div style="font-size:0.8rem;color:rgba(255,80,80,0.55);'
                    'margin-top:2px;">вакансия — Хранителя нет</div></div>')

    def update_bubble():
        if not bubble_ref["element"]:
            return
        base = "avatar" if zanyato else "avatar vacant"
        bubble_ref["element"].classes(replace=base)
        if state["активен"]:
            bubble_ref["element"].classes(add="active")

    def toggle_khranitel():
        if not zanyato:
            ui.notify("Пост свободен — сажать некого", type="warning")
            return
        state["активен"] = not state["активен"]
        update_avatar()
        update_vitals()
        update_bubble()
        update_chat()
        if state["активен"]:
            p = _read_json(dom / "passport.json", {}) or {}
            update_viewer(
                f"# {imya} · Хранитель Архива\n\n"
                f"**Место:** {ZDANIE}\n\n"
                f"**О ней:** {p.get('Hidden_History', '—')[:400]}\n\n"
                f"---\n\n*Спроси про архив, или прямо: «это живое или пластик?»*"
            )
        else:
            update_viewer("# Архив\n\n*Дверь закрыта.*")

    # ── ЗАГРУЗЧИК РУДЫ (левая колонка): текст + изображения ─
    def update_ruda_list():
        if not ruda_ref["element"]:
            return
        ruda_ref["element"].clear()
        with ruda_ref["element"]:
            if not state["руда"]:
                ui.label("Руда пуста").style("color: rgba(255,255,255,0.4); font-size:11px;")
                return
            for r in state["руда"]:
                ikona = "🖼" if r["вид"] == "изображение" else "📄"
                cvet = "rgba(189,0,255,0.9)" if r["вид"] == "изображение" else "rgba(201,168,76,0.9)"
                ui.html(f'''
                  <div style="padding:7px 10px;margin:3px 0;border-radius:7px;
                              background:rgba(255,255,255,0.02);
                              border:1px solid rgba(255,255,255,0.07);
                              font-family:'JetBrains Mono',monospace;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                      <span style="color:{cvet};font-size:11px;font-weight:700;">{ikona} {r["вид"]}</span>
                      <span style="color:rgba(255,255,255,0.4);font-size:9px;">{r["размер"]}</span>
                    </div>
                    <div style="color:rgba(255,255,255,0.6);font-size:9px;margin-top:2px;
                                word-break:break-all;">{r["имя"]}</div>
                  </div>''')

    async def handle_ruda(e):
        """Приёмка руды на просев — до того, как ляжет в архив."""
        imya_f = e.name
        ext = Path(imya_f).suffix.lower()
        if ext in TEKST_EXT:
            vid, papka = "текст", _RUDA / "тексты"
        elif ext in KARTINKA_EXT:
            vid, papka = "изображение", _RUDA / "изображения"
        else:
            ui.notify(f"{imya_f}: не текст и не изображение — не приму", type="warning")
            return
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать файл: {ce}", type="negative")
            return
        papka.mkdir(parents=True, exist_ok=True)
        dest = papka / imya_f
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не сохранить: {we}", type="negative")
            return

        kb = len(data) / 1024
        state["руда"].append({
            "имя": imya_f, "вид": vid, "путь": str(dest),
            "размер": f"{kb:.0f} КБ",
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        update_ruda_list()
        if vid != "изображение":
            state["чат"].append({
                "role": "assistant", "кто": "ЗАГРУЗЧИК",
                "content": f"📄 Принял «{imya_f}» — лежит на просеве, "
                          f"в архив не легло само (Хранитель решает руками)."})
            update_chat()
            ui.notify(f"Принято на просев: {imya_f}", type="positive")
        else:
            # PATCH_ARKHIV_VIZUAL_V1: реальный разбор вместо простого приёма
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"🖼 Принял «{imya_f}» — смотрю…"})
            ui.notify(f"🖼 Принято: {imya_f} — смотрю...", type="info")
            update_chat()
            razbor = await _analiz_kartinki(
                dest, state.get("model"),
                "Опиши, что на изображении: структура, детали, текст если "
                "есть. Коротко и по делу, не выдумывай того, чего не видно.")
            # PATCH_ARKHIV_KATALOG_PERSIST_V1: разбор уходит в каталог
            # черновиком -- не только в чат, который забудется через ход.
            try:
                import khranitel_arkhiva as _khr2
                _khr2.dobavit_v_katalog({
                    "название": Path(imya_f).stem,
                    "раздел": "медиа",
                    "теги": ["автозагрузка", "изображение"],
                    "файл": f"изображения/{imya_f}",
                    "описание": razbor,
                    "статус": "черновик — принято автоматически, не проверено Хранителем",
                    "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
                _zapisano = True
            except Exception:
                _zapisano = False
            _hvost = ("записано в каталог черновиком — Хранитель проверит"
                     if _zapisano else
                     "в архив не легло само — Хранитель решает руками")
            state["чат"][-1] = {"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                "content": f"🖼 «{imya_f}»: {razbor} ({_hvost})"}
            ui.notify(f"🖼 разобрано: {imya_f}", type="positive")
            update_chat()

        up = ruda_ref.get("uploader")
        if up:
            try:
                up.reset()
            except Exception:
                pass

    def clear_ruda():
        state["руда"] = []
        update_ruda_list()
        ui.notify("Список очищен (файлы на диске остались)", type="info")

    # ── ЗАГРУЗЧИК АРХИВА (правая колонка, под аватаром) ─────
    def update_arkhiv_info():
        if not arkhiv_ref["element"]:
            return
        kat = _read_json(_KATALOG, {"записи": []}) or {"записи": []}
        zapisi = kat.get("записи", [])
        po_razdelam = {}
        for z in zapisi:
            po_razdelam[z.get("раздел", "прочее")] = po_razdelam.get(z.get("раздел", "прочее"), 0) + 1
        arkhiv_ref["element"].clear()
        with arkhiv_ref["element"]:
            if not zapisi:
                ui.html('<div style="color:rgba(255,255,255,0.35);font-size:10px;'
                        'padding:8px 16px;">Архив пуст — ни одной записи</div>')
                return
            stroki = " · ".join(f"{p}: {n}" for p, n in po_razdelam.items())
            ui.html(f'<div style="color:rgba(255,255,255,0.5);font-size:9px;'
                    f'padding:8px 16px;line-height:1.6;font-family:\'JetBrains Mono\',monospace;">'
                    f'записей всего: <b style="color:rgba(201,168,76,0.9);">{len(zapisi)}</b><br>{stroki}</div>')

    async def handle_zapis(e):
        """Запись в архив + каталог. Глубину/оценку Шеф или Хранитель
        правят руками — код за них не сочиняет.

        ARKHIV_PRAVYY_VIZUAL_V1: картинку разбираем по-настоящему —
        тем же вызовом, что и левый загрузчик руды. Без этого файл
        ложился слепым: ни тегов, ни описания, никто не мог узнать,
        что на нём, не открыв руками."""
        imya_f = e.name
        razdel = (zapisi_ref["раздел"].value if zapisi_ref["раздел"] else "прочее") or "прочее"
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать файл: {ce}", type="negative")
            return
        dest_dir = _ARKHIV / razdel
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / imya_f
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не положить в архив: {we}", type="negative")
            return

        is_kartinka = Path(imya_f).suffix.lower() in KARTINKA_EXT
        opisanie = ""
        if is_kartinka:
            state["чат"].append({"role": "assistant", "кто": "АРХИВ",
                                 "content": f"🖼 «{imya_f}» — смотрю…"})
            ui.notify(f"🖼 смотрю: {imya_f}", type="info")
            update_chat()
            opisanie = await _analiz_kartinki(
                dest, state.get("model"),
                "Опиши, что на изображении: структура, детали, текст если "
                "есть. Коротко и по делу, не выдумывай того, чего не видно.")

        kat = _read_json(_KATALOG, {"записи": [], "разделы": RAZDELY}) or {"записи": [], "разделы": RAZDELY}
        zapisi = kat.setdefault("записи", [])
        rel = f"{razdel}/{imya_f}"
        zap_id = Path(imya_f).stem.lower().replace(" ", "_")[:40]
        zapis = {
            "id": zap_id,
            "название": Path(imya_f).stem,
            "раздел": razdel,
            "файл": rel,
            "теги": (["изображение"] if is_kartinka else []),
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        if opisanie:
            zapis["описание"] = opisanie
        est = next((i for i, z in enumerate(zapisi) if z.get("файл") == rel), None)
        if est is not None:
            zapisi[est] = zapis
        else:
            zapisi.append(zapis)
        kat["разделы"] = RAZDELY
        _write_json(_KATALOG, kat)

        update_arkhiv_info()
        if is_kartinka and opisanie:
            _soobshchenie = f"🖼 «{zapis['название']}»: {opisanie}"
        else:
            _soobshchenie = f"🗄 «{zapis['название']}» легло в раздел «{razdel}»."
        if is_kartinka:
            state["чат"][-1] = {"role": "assistant", "кто": "АРХИВ",
                                "content": _soobshchenie}
        else:
            state["чат"].append({"role": "assistant", "кто": "АРХИВ",
                                 "content": _soobshchenie})
        update_chat()
        ui.notify(f"В архив, раздел «{razdel}»: {zapis['название']}", type="positive")
        up = zapisi_ref.get("uploader")
        if up:
            try:
                up.reset()
            except Exception:
                pass

    # ── навигация ──────────────────────────────────────────
    def otkryt_pamyati():
        """PAMYATI_GORODA_V1: Архив как ДОСТУП, а не как склад.

        Ничего к себе не тащим: спрашиваем реестр памятей, он обходит
        папку `Архив/памяти/` и отдаёт только то, что в этом городе
        реально есть. Выбранное показываем в правом окне.
        """
        try:
            import sys as _sys
            _p = str(Path(__file__).resolve().parent)
            if _p not in _sys.path:
                _sys.path.insert(0, _p)
            import pamyat as _pam
        except Exception as e:
            ui.notify(f"⚠ реестр памятей не поднялся: {e}", color="negative")
            return

        spisok = _pam.vse()
        if not spisok:
            ui.notify("Памятей не нашёл — в этом городе пока пусто",
                      color="warning")
            return

        with ui.dialog() as dlg, ui.card().style(
            "background:#0d1117; border:1px solid rgba(201,168,76,0.30); "
            "border-radius:16px; min-width:420px; padding:20px;"
        ):
            ui.html('<div style="color:rgba(255,255,255,0.92); '
                    'font-weight:800; letter-spacing:0.10em; '
                    'font-size:0.9rem; margin-bottom:4px;">'
                    '🧠 ПАМЯТИ ГОРОДА</div>')
            ui.html('<div style="color:rgba(255,255,255,0.45); '
                    'font-size:0.72rem; margin-bottom:12px;">'
                    'Архив ничего из этого у себя не держит — он знает, '
                    'где лежит, и показывает.</div>')

            def _otkryt(p):
                zapisi = _pam.zapisi(p["ключ"], 200)
                stroki = [f'# {p["имя"]}', "",
                          f'*записей: {len(zapisi)}*', ""]
                if not zapisi:
                    stroki.append("*пусто — память есть, а записей ещё нет*")
                for z in zapisi:
                    kogda = z.get("когда") or "—"
                    otkuda = f'  ·  `{z.get("откуда","")}`' if z.get("откуда") else ""
                    stroki.append(f'**{kogda}**{otkuda}  \n{z.get("что","")}')
                    stroki.append("")
                update_viewer("\n".join(stroki))
                dlg.close()

            for p in spisok:
                ui.button(p["имя"], on_click=lambda p=p: _otkryt(p)).props(
                    "flat no-caps").style(
                    "width:100%; text-align:left; padding:8px 12px; "
                    "border-radius:8px; margin-bottom:4px; font-size:0.8rem; "
                    "color:rgba(255,255,255,0.85); "
                    "background:rgba(255,255,255,0.04);")

            ui.button("закрыть", on_click=dlg.close).props("flat").style(
                "margin-top:8px; color:rgba(255,255,255,0.4); "
                "font-size:0.75rem;")
        dlg.open()

    def idti_v_biblioteku():
        ui.navigate.to("/akademia", new_tab=True)

    def idti_v_gorod():
        ui.navigate.to("/grondheim", new_tab=True)

    def idti_k_khranitelyu():
        if not zanyato:
            ui.notify("Пост свободен — вести некого", type="warning")
            return
        p = _read_json(dom / "passport.json", {}) or {}
        zid = p.get("ID_Object", "")
        ui.navigate.to(f"/zhitel/{zid}" if zid else "/zhitel")

    # ── чат с Хранителем ────────────────────────────────────
    async def send_message():
        if not input_ref["element"]:
            return
        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        if not state["активен"]:
            ui.notify("Сначала кликни по пузырьку — дверь заперта", type="warning")
            return
        input_ref["element"].value = ""
        state["чат"].append({"role": "user", "content": msg})
        update_chat()

        try:
            import khranitel_arkhiva as _khr
        except Exception as _e:
            state["чат"].append({
                "role": "assistant", "кто": "СИСТЕМА",
                "content": f"движок Хранителя не поднялся: {_e}"})
            update_chat()
            return

        _imya_khr = ""
        try:
            _promt, _imya_khr = _khr.sobrat_promt(msg, "Шеф")
        except Exception:
            _promt = ""

        if not _promt:
            state["чат"].append({
                "role": "assistant", "кто": "СИСТЕМА",
                "content": ("Хранителя Архива в городе пока нет — пост свободен. "
                            "Посади кого-нибудь: Брат → Роль → хранитель архива.")})
            update_chat()
            return

        state["чат"].append({"role": "assistant", "кто": _imya_khr,
                             "content": "…смотрит в архив"})
        update_chat()
        try:
            _otvet = await _khr.sprosit(msg, state["чат"][:-2], "Шеф",
                                        model=state.get("model"))
        except Exception as _e:
            _otvet = f"⚠ Хранитель не отозвался: {_e}"
        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": _imya_khr,
                             "content": _otvet})
        update_chat()

    # ═══ LAYOUT — калька Академии/Биржи ═══════════════════════
    with ui.element("div").classes("app-container"):

        # ── ШАПКА: один пузырёк Хранителя + кнопки ──
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass squad-deck").style(
                "display:flex; align-items:center; width:100%; gap:8px; padding:0 12px;"
            ):
                with ui.element("div").style(
                    "display:flex; align-items:center; gap:6px; flex-wrap:wrap; "
                    "justify-content:center; flex:1;"
                ):
                    bubble_ref["element"] = ui.element("div").classes(
                        "avatar" if zanyato else "avatar vacant")
                    if zanyato:
                        av = _avatar_url(dom)
                        if av:
                            bubble_ref["element"].style(f"background-image:url('{av}');")
                    bubble_ref["element"].on("click", lambda: toggle_khranitel())
                    with bubble_ref["element"]:
                        if not zanyato:
                            ui.label("?").style("font-size: 9px")

                with ui.row().style("gap:6px; align-items:center;"):
                    with ui.element("div").classes("zmodel-sel").style("margin-right:6px;"):
                        _opts = {m["id"]: f'{m["name"]} ({m["price"]})' for m in MODELS_CATALOG}
                        ui.select(_opts, value=state["model"], on_change=on_model_change) \
                            .props('dense borderless dark options-dense').style("min-width:180px;")
                    _b1 = ui.element("div").classes("arkhiv-btn")
                    _b1.on("click", lambda: idti_v_biblioteku())
                    with _b1:
                        ui.html("📚 БИБЛИОТЕКА")
                    _b2 = ui.element("div").classes("arkhiv-btn")
                    _b2.on("click", lambda: idti_k_khranitelyu())
                    with _b2:
                        ui.html("🏠 ДОМ ХРАНИТЕЛЯ")
                    # PAMYATI_GORODA_V1: окно во все памяти города
                    _b0 = ui.element("div").classes("arkhiv-btn")
                    _b0.on("click", lambda: otkryt_pamyati())
                    with _b0:
                        ui.html("🧠 ПАМЯТИ")
                    _b3 = ui.element("div").classes("arkhiv-btn")
                    _b3.on("click", lambda: idti_v_gorod())
                    with _b3:
                        ui.html("🏙 ГОРОД")

        # ── ЛЕВАЯ: загрузчик руды ──
        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):
                with ui.element("div").classes("glass asset-bay"):
                    with ui.row().style(
                        "width:100%; justify-content:space-between; align-items:center; "
                        "padding:8px 16px 6px 16px; border-bottom:1px solid rgba(255,255,255,0.08);"
                    ):
                        ui.label("ЗАГРУЗЧИК").style(
                            "color:rgba(255,255,255,0.92); font-weight:900; letter-spacing:.12em; "
                            "text-transform:uppercase; font-size:11px;")
                        ui.button("CLEAR", on_click=clear_ruda).props("flat dense size=xs").style(
                            "color:rgba(255,80,80,0.5); font-size:9px;")
                    ui.html('<div style="padding:4px 16px 6px 16px;color:rgba(255,255,255,0.35);'
                            'font-size:9px;line-height:1.5;">на просев, до того как Хранитель '
                            'решит класть ли в архив</div>')
                    ruda_ref["uploader"] = ui.upload(
                        on_upload=handle_ruda, multiple=True, auto_upload=True,
                    ).props("flat color=cyan").style("margin: 0 8px 8px 8px;")
                    ruda_ref["element"] = ui.element("div").classes("file-list").style(
                        "max-height:300px; overflow-y:auto; overflow-x:hidden; padding:4px 8px;")
                    update_ruda_list()

        # ── ЦЕНТР: тулбар + чат/отчёт + консоль ──
        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("glass stage-monitor").style("height:100%; overflow:hidden;"):
                with ui.element("div").classes("stage-toolbar"):
                    with ui.element("div").style("display:flex; gap:6px; align-items:center;"):
                        ui.html('<div style="color:rgba(255,255,255,0.55);font-size:11px;'
                                'letter-spacing:.14em;font-weight:900;">АРХИВ ГОРОДА</div>')
                    with ui.row().style("gap:8px; justify-content:flex-end;"):
                        ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat", new_tab=True)).props("flat").style(
                            "padding:6px 14px; border-radius:8px; font-size:12px; "
                            "background:rgba(201,168,76,0.08); border:1px solid rgba(201,168,76,0.25); "
                            "color:rgba(220,200,160,0.8);")

                with ui.element("div").classes("stage-content"):
                    with ui.element("div").classes("split-view"):
                        chat_ref["element"] = ui.element("div").classes("chat-log")
                        with chat_ref["element"]:
                            ui.html('<div class="chat-msg-system">SYSTEM: дверь заперта. '
                                    'Кликни по пузырьку Хранителя.</div>')
                        viewer_ref["element"] = ui.element("div").classes("viewer")
                        with viewer_ref["element"]:
                            ui.label("Карточка появится здесь")

                with ui.element("div").classes("floating-console"):
                    input_ref["element"] = ui.input(placeholder="Сообщение Хранителю...").props(
                        "borderless").style("flex:1")
                    input_ref["element"].on("keydown.enter", send_message)
                    ui.button("SEND", on_click=send_message).classes("send-button")

        # ── ПРАВАЯ: аватар + загрузчик архива ──
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                avatar_ref["element"] = ui.element("div").classes("right-top-slot")
                update_avatar()

                with ui.element("div").classes("glass").style(
                        "margin-top:12px; flex-shrink:0; overflow:hidden;"):
                    vitals_ref["element"] = ui.element("div")
                    update_vitals()

                with ui.element("div").classes("glass").style(
                        "margin-top:12px; flex-shrink:0; overflow:hidden;"):
                    ui.html('<div class="panel-title">АРХИВ</div>')
                    zapisi_ref["раздел"] = ui.select(
                        RAZDELY, value=RAZDELY[0], label="раздел"
                    ).props("dense outlined dark").style(
                        "margin:8px 16px 4px 16px; font-size:11px;")
                    zapisi_ref["uploader"] = ui.upload(
                        on_upload=handle_zapis, multiple=True, auto_upload=True,
                    ).props("flat color=purple").style("margin: 0 8px 6px 8px;")
                    arkhiv_ref["element"] = ui.element("div")
                    update_arkhiv_info()

    # первичная отрисовка
    update_chat()
    update_bubble()


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/arkhiv")
    def _arkhiv_page():
        page_arkhiv()
    ui.run(title="Архив · Грондхейм", port=8106, reload=False)

# ARKHIV_KABINET_V1 — маркер идемпотентности

# SVOYO_OKNO_V1 - marker

# PAMYATI_GORODA_V1 - marker
