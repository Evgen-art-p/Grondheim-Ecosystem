# -*- coding: utf-8 -*-
# AKADEMIA_KABINET_V1 — КАБИНЕТ АКАДЕМИИ (первый слой: экран)
"""
АКАДЕМИЯ · КАБИНЕТ · /akademia

СТИЛЬ — ВЕСЬ ОТ БИРЖИ (слово Шефа). Та же сетка (300 / центр / 260),
тот же хедер-пузырьки, та же левая колонка с загрузчиком, тот же стол
(тулбар + чат + отчёт-вьюер + плавающая консоль), та же правая колонка
(аватар + панели под ним). CSS снят с ui_torg.py один в один — Академия
самостоятельный модуль и не импортирует Биржу, поэтому копия, не ссылка
(Закон Двух Стандартов: внутри своё, на границе общее).

ЧТО ЭТО ЗА СЛОЙ (честно):
  Слой 1 — ЭКРАН. Пузырьки студентов, приёмка руды (текст + изображения),
  загрузчик библиотеки, навигация. Всё, что рисуется и живёт.
  Труба урока (просев -> вывод -> маяк -> метка) и разговор с учеником
  СЮДА НЕ ВШИТЫ. Их варим отдельным слоем, когда Шеф посмотрит экран.
  Пустая кнопка честнее вранья: где не построено — так и написано.

ПУЗЫРЬКИ = МЕСТА, до 10 (слово Шефа). Кто на месте — читается сканом
GRONDHEIM_CITY/Академия/ученики.json (Закон Картриджа: не держим реестр
в коде, спрашиваем данные). Пусто = честная вакансия, не ошибка.

`шесть·проверено·до·корня`
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

from nicegui import ui, app

_HERE = Path(__file__).resolve().parent           # Академия/
_REPO = _HERE.parent                              # корень репо
for _p in (_REPO, _HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ── ДАННЫЕ АКАДЕМИИ (не код) ────────────────────────────────
KVARTAL = "Академия"
_DATA      = _REPO / "GRONDHEIM_CITY" / KVARTAL
_UCHENIKI  = _DATA / "ученики.json"
_RUDA      = _DATA / "руда"
_BIBLIO    = _DATA / "библиотека"
_KATALOG   = _BIBLIO / "каталог.json"

_KOVCHEG   = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"
_LOKACII   = _REPO / "GRONDHEIM_CITY" / "локации"

ZDANIE = "0008_OWL_CASTLE"      # Замок Сов — дом Академии
MEST   = 10                     # мест за партами, слово Шефа

# полки библиотеки — как в старом городе
POLKI = ["психология", "ремесло", "грондхейм", "рынок", "техника", "прочее"]

# что принимает загрузчик руды
TEKST_EXT = {".txt", ".md", ".rtf"}
KARTINKA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

_STATIC = "akad-static"
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
    """Академия заводит свой двор сама — не падаем на пустом городе."""
    for d in (_DATA, _RUDA, _RUDA / "тексты", _RUDA / "изображения", _BIBLIO):
        d.mkdir(parents=True, exist_ok=True)
    for polka in POLKI:
        (_BIBLIO / polka).mkdir(parents=True, exist_ok=True)
    if not _KATALOG.exists():
        _write_json(_KATALOG, {"книги": [], "полки": POLKI})
    if not _UCHENIKI.exists():
        _write_json(_UCHENIKI, {"места": []})


def _dom_zhitelya(imya: str) -> Path:
    return _KOVCHEG / imya


def _avatar_url(dom: Path) -> str:
    """Фото жителя — как в кабинете Биржи и жителя, один способ на город."""
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


def _bg_url() -> str:
    """Фон кабинета — картинка Замка Сов. Нет image.* — честно пусто."""
    dom = _LOKACII / ZDANIE
    if not dom.exists():
        return ""
    if not _BG_MOUNTED["done"]:
        try:
            app.add_static_files("/akad-bg", str(_LOKACII))
        except Exception:
            pass
        _BG_MOUNTED["done"] = True
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if (dom / ("image" + ext)).exists():
            return f"/akad-bg/{ZDANIE}/image{ext}"
    return ""


def _build_mesta() -> list:
    """Десять мест за партами. Кто сидит — из ученики.json, не из кода.

    Формат записи: {"место": 1, "житель": "Илья", "курс": "..."}
    Место без записи — вакансия, это нормальное состояние новой школы.
    """
    zapisi = (_read_json(_UCHENIKI, {}) or {}).get("места", []) or []
    po_mestu = {}
    for z in zapisi:
        try:
            n = int(z.get("место", 0))
        except (TypeError, ValueError):
            continue
        if 1 <= n <= MEST:
            po_mestu[n] = z

    out = []
    for n in range(1, MEST + 1):
        z = po_mestu.get(n)
        imya = (z or {}).get("житель", "")
        dom = _dom_zhitelya(imya) if imya else None
        est = bool(dom and dom.exists())
        if est:
            try:
                app.add_static_files(f"/{_STATIC}/{dom.name}", str(dom))
            except Exception:
                pass
        out.append({
            "место": n,
            "имя": imya if est else "",
            "дом": dom if est else None,
            "курс": (z or {}).get("курс", ""),
            "занято": est,
        })
    return out


def _mesto_row(mesta: list, n: int):
    for m in mesta:
        if m["место"] == n:
            return m
    return None


def _bar_html(charge: float) -> str:
    """Заряд/оптика — тот же вид, что в кабинете жителя и на Бирже."""
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
# СТИЛЬ — снят с Биржи один в один
# ═══════════════════════════════════════════════════════════

AKAD_CSS = r"""
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
.avatar:hover{ border-color: rgba(0,204,255,0.40); transform: scale(1.05); }
.avatar.active{
  border-color: rgba(0,204,255,0.75);
  box-shadow: 0 0 0 2px rgba(0,204,255,0.25) inset, 0 0 30px rgba(0,204,255,0.35);
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
.viewer{ border-color: rgba(0,204,255,0.30); }

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
  border-radius: 40px !important; border: 2px solid rgba(0,204,255,0.55) !important;
  background: linear-gradient(135deg, rgba(0,204,255,0.30), rgba(189,0,255,0.25)) !important;
  color: rgba(255,255,255,0.98) !important; font-weight: 900 !important;
  padding: 12px 24px !important; cursor: pointer !important;
}

.chat-msg-user{ background: rgba(0, 204, 255, 0.1);
  border-left: 3px solid rgba(0, 204, 255, 0.6); padding: 8px 12px;
  margin: 8px 0; border-radius: 0 8px 8px 0; }
.chat-msg-assistant{ background: rgba(0, 255, 136, 0.08);
  border-left: 3px solid rgba(0, 255, 136, 0.6); padding: 8px 12px;
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

.akad-btn{
  padding:6px 14px; border-radius:7px; font-size:12px; font-weight:700;
  cursor:pointer; display:flex; align-items:center;
  background:rgba(255,255,255,0.03); color:rgba(255,255,255,0.55);
  border:1px solid rgba(255,255,255,0.10);
}

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

def page_akademia() -> None:
    """Кабинет Академии — Замок Сов изнутри."""

    _ensure_dirs()
    mesta = _build_mesta()

    # первое занятое место — активное; нет никого — первое место
    _first = next((m["место"] for m in mesta if m["занято"]), 1)

    state = {
        "активное_место": _first,
        "чат": [],
        "руда": [],          # что принял загрузчик за эту сессию
        "отчёт": "",
    }

    chat_ref   = {"element": None}
    viewer_ref = {"element": None}
    ruda_ref   = {"element": None, "uploader": None}
    knigi_ref  = {"uploader": None, "полка": None}
    avatar_ref = {"element": None}
    vitals_ref = {"element": None}
    biblio_ref = {"element": None}
    input_ref  = {"element": None}
    bubbles    = {"elements": {}}

    ui.add_head_html(f"<style>{AKAD_CSS}</style>")
    _bg = _bg_url()
    ui.html(f'<div id="bg"{f" style=\"background-image:url(\'{_bg}\');\"" if _bg else ""}></div>')

    # ── чат ────────────────────────────────────────────────
    def update_chat():
        if not chat_ref["element"]:
            return
        chat_ref["element"].clear()
        with chat_ref["element"]:
            if not state["чат"]:
                ui.html('<div class="chat-msg-system">SYSTEM: Замок Сов открыт. '
                        'Всегда тих. Ждёт тех, кто задаёт вопросы.</div>')
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

    # ── аватар студента (правая колонка) ───────────────────
    def update_avatar():
        if not avatar_ref["element"]:
            return
        m = _mesto_row(mesta, state["активное_место"])
        avatar_ref["element"].clear()
        with avatar_ref["element"]:
            av = _avatar_url(m["дом"]) if (m and m["занято"]) else ""
            img = (f'<img src="{av}" style="width:100%;height:100%;object-fit:cover;'
                   f'border-radius:12px;opacity:0.85;" onerror="this.style.display=\'none\'">'
                   if av else "")
            imya = m["имя"] if (m and m["занято"]) else "—"
            kurs = (m or {}).get("курс", "") or "курс не назначен"
            note = "" if (m and m["занято"]) else (
                '<div style="font-size:0.65rem;color:rgba(255,80,80,0.6);">'
                'место свободно</div>')
            ui.html(f'''
                <div style="position:relative; width:100%; height:100%; min-height:200px;">
                    {img}
                    <div style="position:absolute; bottom:0; left:0; right:0;
                                padding:15px; background:linear-gradient(transparent, rgba(0,0,0,0.8));
                                border-radius:0 0 12px 12px;">
                        <div style="font-size:0.65rem; color:rgba(255,255,255,0.5);
                                    letter-spacing:0.15em;">СТУДЕНТ · МЕСТО {m["место"] if m else "—"}</div>
                        <div style="font-size:1.3rem; font-weight:700; color:#00ff88;">{imya}</div>
                        <div style="font-size:0.8rem; color:rgba(255,255,255,0.8);">{kurs}</div>
                        {note}
                    </div>
                </div>
            ''')

    def update_vitals():
        if not vitals_ref["element"]:
            return
        vitals_ref["element"].clear()
        m = _mesto_row(mesta, state["активное_место"])
        with vitals_ref["element"]:
            if m and m["занято"]:
                p = _read_json(m["дом"] / "passport.json", {}) or {}
                ui.html(_bar_html(float(p.get("_charge", 0.0) or 0.0)))
            else:
                ui.html('<div style="color:rgba(255,255,255,0.3); font-size:10px; '
                        'padding:8px 16px;">— место свободно, показывать нечего —</div>')

    def update_bubbles():
        for n, el in bubbles["elements"].items():
            m = _mesto_row(mesta, n)
            base = "avatar" if (m and m["занято"]) else "avatar vacant"
            el.classes(replace=base)
            if n == state["активное_место"]:
                el.classes(add="active")

    def switch_mesto(n: int):
        m = _mesto_row(mesta, n)
        state["активное_место"] = n
        update_avatar()
        update_vitals()
        update_bubbles()
        if m and m["занято"]:
            p = _read_json(m["дом"] / "passport.json", {}) or {}
            dna = p.get("DNA_Static", {}) or {}
            ruchki = " · ".join(f"{k}: {v}" for k, v in dna.items()) or "—"
            update_viewer(
                f"# {m['имя']} · место {n}\n\n"
                f"**Курс:** {m['курс'] or '*не назначен*'}\n\n"
                f"**Натура:** {ruchki}\n\n"
                f"**Род:** {p.get('Hidden_History','—')}\n\n"
                f"---\n\n*Учёба ещё не подключена — это первый слой, экран.*"
            )
        else:
            ui.notify(f"Место {n} свободно — сюда ещё никого не записали", type="warning")
            update_viewer(f"# Место {n}\n\n*Свободно. Запись студента — отдельная дверь, "
                          f"её ещё нет.*")

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
                cvet = "rgba(189,0,255,0.9)" if r["вид"] == "изображение" else "rgba(0,204,255,0.9)"
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
        """Приёмка руды. Текст — на просев. Изображение — на разбор.

        РАЗБОР НЕ ВШИТ (первый слой): файл честно ложится на диск и
        показывается в списке. Чтобы читать график глазами, нужен голос,
        который видит картинки — это отдельный слой и отдельное решение
        Шефа. Пустого «проанализировано» здесь не будет.
        """
        imya = e.name
        ext = Path(imya).suffix.lower()
        if ext in TEKST_EXT:
            vid, papka = "текст", _RUDA / "тексты"
        elif ext in KARTINKA_EXT:
            vid, papka = "изображение", _RUDA / "изображения"
        else:
            ui.notify(f"{imya}: не текст и не изображение — не приму", type="warning")
            return
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать файл: {ce}", type="negative")
            return
        papka.mkdir(parents=True, exist_ok=True)
        dest = papka / imya
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не сохранить: {we}", type="negative")
            return

        kb = len(data) / 1024
        state["руда"].append({
            "имя": imya, "вид": vid, "путь": str(dest),
            "размер": f"{kb:.0f} КБ",
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        update_ruda_list()

        if vid == "текст":
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"📄 Принял «{imya}» — лёг в руду на просев."})
            ui.notify(f"📄 Принято на просев: {imya}", type="positive")
        else:
            state["чат"].append({
                "role": "assistant", "кто": "ЗАГРУЗЧИК",
                "content": (f"🖼 Принял «{imya}». Лежит в руде. "
                            f"Разбор глазами пока не подключён — это следующий слой.")})
            ui.notify(f"🖼 Изображение принято: {imya}", type="info")
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

    # ── ЗАГРУЗЧИК БИБЛИОТЕКИ (правая колонка, под аватаром) ─
    def update_biblio_info():
        if not biblio_ref["element"]:
            return
        kat = _read_json(_KATALOG, {"книги": []}) or {"книги": []}
        knigi = kat.get("книги", [])
        po_polkam = {}
        for k in knigi:
            po_polkam[k.get("полка", "прочее")] = po_polkam.get(k.get("полка", "прочее"), 0) + 1
        biblio_ref["element"].clear()
        with biblio_ref["element"]:
            if not knigi:
                ui.html('<div style="color:rgba(255,255,255,0.35);font-size:10px;'
                        'padding:8px 16px;">Полки пусты — ни одной книги</div>')
                return
            stroki = " · ".join(f"{p}: {n}" for p, n in po_polkam.items())
            ui.html(f'<div style="color:rgba(255,255,255,0.5);font-size:9px;'
                    f'padding:8px 16px;line-height:1.6;font-family:\'JetBrains Mono\',monospace;">'
                    f'книг всего: <b style="color:rgba(0,204,255,0.9);">{len(knigi)}</b><br>{stroki}</div>')

    async def handle_kniga(e):
        """Книга на полку + запись в каталог. Обложку (о чём, глубина)
        Шеф правит в каталоге руками — код за него не сочиняет."""
        imya = e.name
        polka = (knigi_ref["полка"].value if knigi_ref["полка"] else "прочее") or "прочее"
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать книгу: {ce}", type="negative")
            return
        dest_dir = _BIBLIO / polka
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / imya
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не положить на полку: {we}", type="negative")
            return

        kat = _read_json(_KATALOG, {"книги": [], "полки": POLKI}) or {"книги": [], "полки": POLKI}
        knigi = kat.setdefault("книги", [])
        rel = f"{polka}/{imya}"
        book_id = Path(imya).stem.lower().replace(" ", "_")[:40]
        zapis = {
            "id": book_id,
            "название": Path(imya).stem,
            "полка": polka,
            "файл": rel,
            "глубина": "basic",      # обложку уточняет Шеф руками
            "теги": [],
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        est = next((i for i, b in enumerate(knigi) if b.get("файл") == rel), None)
        if est is not None:
            knigi[est] = zapis
        else:
            knigi.append(zapis)
        kat["полки"] = POLKI
        _write_json(_KATALOG, kat)

        update_biblio_info()
        state["чат"].append({
            "role": "assistant", "кто": "БИБЛИОТЕКА",
            "content": (f"📚 «{zapis['название']}» встала на полку «{polka}». "
                        f"Глубина пока basic — поправь в каталоге, если книга тяжёлая.")})
        update_chat()
        ui.notify(f"📚 На полку «{polka}»: {zapis['название']}", type="positive")
        up = knigi_ref.get("uploader")
        if up:
            try:
                up.reset()
            except Exception:
                pass

    # ── навигация ──────────────────────────────────────────
    def idti_v_biblioteku():
        ui.notify("Отдельная Библиотека ещё не построена — заглушка", type="info")

    def idti_domoy():
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — некого вести домой", type="warning")
            return
        p = _read_json(m["дом"] / "passport.json", {}) or {}
        zid = p.get("ID_Object", "")
        ui.navigate.to(f"/zhitel/{zid}" if zid else "/zhitel")

    def idti_v_gorod():
        ui.navigate.to("/grondheim")

    # ── чат с учеником (честная заглушка первого слоя) ─────
    async def send_message():
        if not input_ref["element"]:
            return
        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        input_ref["element"].value = ""
        state["чат"].append({"role": "user", "content": msg})
        update_chat()

        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            state["чат"].append({
                "role": "assistant", "кто": "СИСТЕМА",
                "content": "Место свободно — отвечать некому. Запиши сюда студента."})
        else:
            state["чат"].append({
                "role": "assistant", "кто": m["имя"],
                "content": ("живой разговор с учеником — следующий слой. "
                            "Сейчас стоит только экран, и врать я не буду.")})
        update_chat()

    # ═══ LAYOUT — калька Биржи ═══════════════════════════════
    with ui.element("div").classes("app-container"):

        # ── ШАПКА: пузырьки студентов + кнопки ──
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass squad-deck").style(
                "display:flex; align-items:center; width:100%; gap:8px; padding:0 12px;"
            ):
                with ui.element("div").style(
                    "display:flex; align-items:center; gap:6px; flex-wrap:wrap; "
                    "justify-content:center; flex:1;"
                ):
                    for m in mesta:
                        n = m["место"]
                        cls = f'avatar {"active" if n == state["активное_место"] else ""} ' \
                              f'{"" if m["занято"] else "vacant"}'
                        b = ui.element("div").classes(cls)
                        if m["занято"]:
                            av = _avatar_url(m["дом"])
                            if av:
                                b.style(f"background-image:url('{av}');")
                        b.on("click", lambda e, k=n: switch_mesto(k))
                        with b:
                            if not m["занято"]:
                                ui.label(str(n)).style("font-size: 9px")
                        bubbles["elements"][n] = b

                with ui.row().style("gap:6px; align-items:center;"):
                    _b1 = ui.element("div").classes("akad-btn")
                    _b1.on("click", lambda: idti_v_biblioteku())
                    with _b1:
                        ui.html("📚 БИБЛИОТЕКА")
                    _b2 = ui.element("div").classes("akad-btn")
                    _b2.on("click", lambda: idti_domoy())
                    with _b2:
                        ui.html("🏠 ДОМОЙ")
                    _b3 = ui.element("div").classes("akad-btn")
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
                            'font-size:9px;line-height:1.5;">текст → на просев · '
                            'изображение → на разбор</div>')
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
                                'letter-spacing:.14em;font-weight:900;">АКАДЕМИЯ · ЗАМОК СОВ</div>')
                    with ui.row().style("gap:8px; justify-content:flex-end;"):
                        ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")).props("flat").style(
                            "padding:6px 14px; border-radius:8px; font-size:12px; "
                            "background:rgba(99,130,255,0.08); border:1px solid rgba(99,130,255,0.25); "
                            "color:rgba(180,190,220,0.8);")

                with ui.element("div").classes("stage-content"):
                    with ui.element("div").classes("split-view"):
                        chat_ref["element"] = ui.element("div").classes("chat-log")
                        with chat_ref["element"]:
                            ui.html('<div class="chat-msg-system">SYSTEM: Замок Сов открыт.</div>')
                        viewer_ref["element"] = ui.element("div").classes("viewer")
                        with viewer_ref["element"]:
                            ui.label("Карточка студента появится здесь")

                with ui.element("div").classes("floating-console"):
                    input_ref["element"] = ui.input(placeholder="Сообщение ученику...").props(
                        "borderless").style("flex:1")
                    input_ref["element"].on("keydown.enter", send_message)
                    ui.button("SEND", on_click=send_message).classes("send-button")

        # ── ПРАВАЯ: аватар + загрузчик библиотеки ──
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
                    ui.html('<div class="panel-title">БИБЛИОТЕКА</div>')
                    knigi_ref["полка"] = ui.select(
                        POLKI, value="психология", label="полка"
                    ).props("dense outlined dark").style(
                        "margin:8px 16px 4px 16px; font-size:11px;")
                    knigi_ref["uploader"] = ui.upload(
                        on_upload=handle_kniga, multiple=True, auto_upload=True,
                    ).props("flat color=purple").style("margin: 0 8px 6px 8px;")
                    biblio_ref["element"] = ui.element("div")
                    update_biblio_info()

    # первичная отрисовка
    update_chat()
    update_bubbles()
    switch_mesto(state["активное_место"])


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/akademia")
    def _akad_page():
        page_akademia()
    ui.run(title="Академия · Грондхейм", port=8105, reload=False)

# AKADEMIA_KABINET_V1 — маркер идемпотентности
