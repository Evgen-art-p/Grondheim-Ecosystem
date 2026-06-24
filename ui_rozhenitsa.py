# ui_rozhenitsa.py
# PATCH_ROZHENITSA_DOC — Страница Жизни нового города (ступень 2)
"""
СТРАНИЦА ЖИЗНИ — бланк паспорта-ядра. Route: /rozhenitsa
Открывается как кабинет, по образцу ui_brat.py (золото, glass).

ЧТО ДЕЛАЕТ (ступень 2 — ДОКУМЕНТООБОРОТ ПАСПОРТА):
  Заполнил бланк → родился ОДИН passport.json — первый кирпичик жителя.
  Ядро: кто · пол · для чего · ДНК · якорь · состояние.

ЧЕГО НЕ ДЕЛАЕТ (намеренно, по уговору с Шефом):
  • НЕ создаёт папки и слои (core/resonance/sensory/archive) — это ступень 5
  • НЕ пишет историю — она в домашнем промпте (home), отдельно, потом
  • НЕ подмешивает маски — маски от иерархии, не сейчас
  • НЕ хардкодит предназначение — свободное поле (картридж), справочник = ступень 4

ДНК — по образцу старой Страницы Жизни (-2), она внесена хорошо.
Паспорт — ОДИН файл-лицо (кирпич цельный, не дробим).
Новый город · ни нитки из -2.
`шесть·проверено·до·корня`
"""
import json
import uuid
from pathlib import Path
from datetime import datetime

from nicegui import ui


# ═══════════════════════════════════════════════════════════
# ДНК-СТАТИКА — натура. Образец из старой Страницы (-2), хорош.
# (id, label, описание, default)
# ═══════════════════════════════════════════════════════════
DNA_STATIC_PARAMS = [
    ("Stubbornness",        "Упрямство",         "Сопротивление чужой воле (0=послушный, 1=непреклонный)",   0.5),
    ("Aesthetic_Threshold", "Проф. гордость",    "Фильтр качества (0.98=перфекционист, бракует всё)",        0.7),
    ("Social_Filter",       "Социальный фильтр", "Вежливость (0.1=резкий и прямой, 0.9=дипломатичный)",      0.6),
    ("Empathy",             "Эмпатия",           "Чувствительность к реакциям других",                       0.5),
    ("Autonomy_Level",      "Уровень свободы",   "Право отходить от шаблона ради высшего блага",              0.5),
    ("Resonance_Frequency", "Частота резонанса", "Лёгкость синхронизации с другими",                         0.5),
]

# ── Динамика — состояние при рождении (в покое). Не из формы. ──
DNA_DYNAMIC_BIRTH = {
    "Respect":        1.0,   # уважение
    "Patience":       1.0,   # терпение
    "Internal_Light": 0.8,   # внутренний свет
    "Charge":         0.0,   # ЗАРЯД −1..+1 · рождается в покое (новый город)
}

# Куда падают паспорта-кирпичи. Сборщик (ступень 3) обойдёт эту папку.
PASPORTA_DIR = Path("GRONDHEIM_CITY/паспорта")


# ═══════════════════════════════════════════════════════════
# РОЖДЕНИЕ ДОКУМЕНТА — только passport.json, ничего больше
# ═══════════════════════════════════════════════════════════

def rodit_pasport(core: dict) -> Path:
    """
    Рожает ОДИН паспорт-кирпич. Только документ.
    Папки/слои НЕ создаёт — это ступень 5 (ядра оживают).
    Возвращает путь к рождённому passport.json.
    """
    PASPORTA_DIR.mkdir(parents=True, exist_ok=True)

    pid = core.get("id") or f"chel_{uuid.uuid4().hex[:8]}"
    core["id"] = pid

    pasport = {
        # КТО
        "id":            pid,
        "имя":           core.get("имя", ""),
        "пол":           core.get("пол", ""),
        "творец":        "Шеф",
        "рождён":        datetime.now().isoformat(timespec="seconds"),
        "редкость":      core.get("редкость", ""),
        # ДЛЯ ЧЕГО (предназначение — свободный картридж)
        "предназначение": core.get("предназначение", ""),
        # ДНК (натура)
        "днк_статика":   core.get("днк_статика", {}),
        # СОСТОЯНИЕ (при рождении, в покое)
        "состояние":     dict(DNA_DYNAMIC_BIRTH),
        # ЯКОРЬ (доступно при нуле — кто он ровный)
        "якорь": {
            "коронная_фраза": core.get("коронная_фраза", ""),
            "факты":          core.get("факты", []),
        },
        # служебное
        "_кирпич":       "ядро · ступень 2 · история в home, маски от иерархии",
        "_слои_заведены": False,   # ступень 5 поставит True, когда оживёт
    }

    out = PASPORTA_DIR / f"{pid}.json"
    out.write_text(json.dumps(pasport, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def skan_pasporta() -> list[dict]:
    """Список рождённых паспортов (для правой колонки). Живой скан папки."""
    if not PASPORTA_DIR.exists():
        return []
    out = []
    for p in sorted(PASPORTA_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


# ═══════════════════════════════════════════════════════════
# СТИЛИ — по образцу кабинета Брата
# ═══════════════════════════════════════════════════════════
ROZH_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
.rozh-root{ position:fixed; inset:0; background:#050510; color:#fff;
  font-family:Inter,system-ui,sans-serif; overflow:auto; padding:28px; box-sizing:border-box; }
.rozh-root::after{ content:''; position:fixed; inset:0; z-index:-1;
  background: radial-gradient(1000px 700px at 20% 10%, rgba(201,168,76,0.10), transparent 60%),
              radial-gradient(900px 650px at 80% 25%, rgba(201,168,76,0.06), transparent 55%),
              rgba(0,0,0,0.40); }
.rozh-head{ display:flex; align-items:center; gap:16px; margin-bottom:24px; }
.rozh-title{ font-size:1.4rem; font-weight:900; letter-spacing:0.14em; color:#c9a84c; }
.rozh-sub{ font-size:0.62rem; color:rgba(255,255,255,0.4); letter-spacing:0.1em; text-transform:uppercase; }
.rozh-back{ margin-left:auto; padding:8px 20px; border-radius:10px;
  background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08));
  border:1px solid rgba(201,168,76,0.35); color:#fff; font-weight:400; font-size:0.82rem; text-transform:none; }
.rozh-grid{ display:grid; grid-template-columns: 1fr 320px; gap:20px; max-width:1000px; }
.rozh-card{ background:rgba(13,17,23,0.60); border:1px solid rgba(255,255,255,0.10);
  border-radius:16px; backdrop-filter:blur(16px); padding:20px 22px; }
.rozh-section{ font-size:0.7rem; font-weight:900; letter-spacing:0.12em; text-transform:uppercase;
  color:#c9a84c; margin:18px 0 10px; border-bottom:1px solid rgba(201,168,76,0.2); padding-bottom:6px; }
.rozh-section:first-child{ margin-top:0; }
.rozh-hint{ font-size:0.62rem; color:rgba(255,255,255,0.4); margin-bottom:10px; line-height:1.5; }
.dna-row{ display:flex; align-items:center; gap:12px; margin-bottom:6px; }
.dna-label{ font-size:0.72rem; color:rgba(255,255,255,0.75); width:130px; flex-shrink:0; }
.dna-val{ font-size:0.72rem; color:#c9a84c; width:34px; text-align:right; }
.born-list{ display:flex; flex-direction:column; gap:8px; }
.born-item{ padding:10px 12px; border-radius:10px; background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.08); }
.born-name{ font-size:0.85rem; font-weight:700; color:#fff; }
.born-meta{ font-size:0.6rem; color:rgba(255,255,255,0.45); margin-top:2px; }
.rozh-foot{ margin-top:18px; padding:12px 16px; border-radius:10px; background:rgba(255,255,255,0.03);
  border:1px dashed rgba(255,255,255,0.14); font-size:0.62rem; color:rgba(255,255,255,0.4); line-height:1.6; }
"""


def page_rozhenitsa():
    ui.add_head_html(f"<style>{ROZH_CSS}</style>")

    # состояние формы
    f = {
        "имя": "", "пол": "", "предназначение": "", "редкость": "",
        "коронная_фраза": "", "факты": "",
        "днк": {pid: dflt for (pid, _, _, dflt) in DNA_STATIC_PARAMS},
    }
    refs = {"born": None}

    def update_born():
        el = refs["born"]
        if not el:
            return
        el.clear()
        with el:
            people = skan_pasporta()
            if not people:
                ui.html('<div style="opacity:0.4;font-size:0.7rem;">— ещё никто не рождён —</div>')
            for p in people:
                naznach = p.get("предназначение", "") or "—"
                pol = p.get("пол", "") or "—"
                ui.html(f'<div class="born-item"><div class="born-name">{p.get("имя","?")}</div>'
                        f'<div class="born-meta">{naznach} · {pol} · {p.get("id","")}</div></div>')

    def rodit():
        if not f["имя"].strip():
            ui.notify("Имя — обязательно. Кто рождается?", color="warning")
            return
        if not f["предназначение"].strip():
            ui.notify("Для чего нужен? Впиши предназначение.", color="warning")
            return
        core = {
            "имя": f["имя"].strip(),
            "пол": f["пол"].strip(),
            "предназначение": f["предназначение"].strip(),
            "редкость": f["редкость"].strip(),
            "коронная_фраза": f["коронная_фраза"].strip(),
            "факты": [x.strip() for x in f["факты"].split("\n") if x.strip()],
            "днк_статика": dict(f["днк"]),
        }
        path = rodit_pasport(core)
        ui.notify(f"Рождён паспорт: {path.name}", color="positive")
        update_born()

    with ui.element("div").classes("rozh-root"):
        with ui.element("div").classes("rozh-head"):
            ui.html('<div><div class="rozh-title">СТРАНИЦА ЖИЗНИ</div>'
                    '<div class="rozh-sub">бланк паспорта · ядро · первый кирпичик</div></div>')
            ui.button("← в кабинет", on_click=lambda: ui.navigate.to("/brat")) \
                .props("flat").classes("rozh-back")

        with ui.element("div").classes("rozh-grid"):
            # ── ЛЕВО: бланк ──
            with ui.element("div").classes("rozh-card"):
                ui.html('<div class="rozh-section">кто он</div>')
                ui.input("Имя", on_change=lambda e: f.update(имя=e.value)).props("dark dense").classes("w-full")
                ui.select(["", "мужской", "женский", "иное"], label="Пол",
                          on_change=lambda e: f.update(пол=e.value)).props("dark dense").classes("w-full")
                ui.select(["", "Common", "Rare", "Epic", "Legendary", "Mythic"], label="Редкость",
                          on_change=lambda e: f.update(редкость=e.value)).props("dark dense").classes("w-full")

                ui.html('<div class="rozh-section">для чего нужен</div>')
                ui.html('<div class="rozh-hint">Предназначение — свободным словом. '
                        'Сценарист · трейдер · резидент · хранитель · …<br>'
                        'Справочник профессий придёт ступенью 4 — пока картридж.</div>')
                ui.input("Предназначение",
                         on_change=lambda e: f.update(предназначение=e.value)).props("dark dense").classes("w-full")

                ui.html('<div class="rozh-section">днк · натура</div>')
                ui.html('<div class="rozh-hint">Вносится раз. Под любой маской — та же натура.</div>')
                for pid, label, descr, dflt in DNA_STATIC_PARAMS:
                    with ui.element("div").classes("dna-row"):
                        ui.html(f'<span class="dna-label" title="{descr}">{label}</span>')
                        valbox = ui.html(f'<span class="dna-val">{dflt:.2f}</span>')
                        def mk(pid=pid, valbox=valbox):
                            def on(e):
                                f["днк"][pid] = float(e.value)
                                valbox.content = f'<span class="dna-val">{float(e.value):.2f}</span>'
                            return on
                        ui.slider(min=0, max=1, step=0.05, value=dflt,
                                  on_change=mk()).props("dark").style("flex:1")

                ui.html('<div class="rozh-section">якорь · дно (доступно при нуле)</div>')
                ui.html('<div class="rozh-hint">Кто он, когда ровный. Не дрейфует.</div>')
                ui.input("Коронная фраза",
                         on_change=lambda e: f.update(коронная_фраза=e.value)).props("dark dense").classes("w-full")
                ui.textarea("Якорные факты (по одному в строке, 3-5)",
                            on_change=lambda e: f.update(факты=e.value)).props("dark dense").classes("w-full")

                ui.button("РОДИТЬ ПАСПОРТ", on_click=rodit).props("flat").style(
                    "margin-top:18px; width:100%; padding:14px; border-radius:12px;"
                    "background:linear-gradient(135deg,rgba(201,168,76,0.25),rgba(201,168,76,0.12));"
                    "border:1px solid rgba(201,168,76,0.5); color:#fff; font-weight:800; letter-spacing:0.1em;")

                ui.html('<div class="rozh-foot">⬡ Рождается ОДИН passport.json — кирпич ядра.<br>'
                        'Папки и слои (core/resonance/sensory/archive) — НЕ сейчас, это ступень 5.<br>'
                        'История — в домашнем промпте, отдельно. Маски — от иерархии, потом.</div>')

            # ── ПРАВО: рождённые ──
            with ui.element("div").classes("rozh-card"):
                ui.html('<div class="rozh-section">рождённые</div>')
                refs["born"] = ui.element("div").classes("born-list")
                update_born()


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/rozhenitsa")
    def _rozh_page():
        page_rozhenitsa()
    ui.run(title="Страница Жизни · Грондхейм", port=8103, reload=False)
