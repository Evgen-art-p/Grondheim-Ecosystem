# ui_rozhenitsa.py
# PATCH_ROZHENITSA_DOC_V2 — Страница Жизни (ступень 2, полный образец)
"""
СТРАНИЦА ЖИЗНИ — паспорт-якорь. Route: /rozhenitsa
По образцу старой Страницы (-2): шесть блоков, фото, редкость, ДНК, Печать.

ПАСПОРТ = ЯКОРЬ ЦЕЛИКОМ. Всё что в нём — дно личности, доступное при нуле
заряда. Кто он ровный. Когда ядро оживёт (ступень 5) — паспорт ляжет в core/.

РАЗНИЦА СО СТАРОЙ: рождается ОДИН passport.json (кусочек), НЕ дописывается
в общую кучу catalog.json. Один житель = один файл-лицо.

ЧЕГО НЕ ДЕЛАЕТ (по уговору): не создаёт папки-слои (ступень 5),
не подмешивает маски (от иерархии). Предназначение свободным словом (картридж).

Печать Создателя: фраза хешируется SHA-256, в паспорт уходит ТОЛЬКО хеш.
Новый город · ни нитки из -2. `шесть·проверено·до·корня`
"""
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime

from nicegui import ui, events


PASPORTA_DIR = Path("GRONDHEIM_CITY/паспорта")
IMAGES_DIR   = PASPORTA_DIR / "images"

DNA_STATIC_PARAMS = [
    ("Stubbornness",        "Упрямство",         "Сопротивление чужой воле",   0.5),
    ("Aesthetic_Threshold", "Проф. гордость",    "Фильтр качества",            0.7),
    ("Social_Filter",       "Социальный фильтр", "Вежливость / прямота",       0.6),
    ("Empathy",             "Эмпатия",           "Чувствительность к другим",  0.5),
    ("Autonomy_Level",      "Уровень свободы",   "Право отходить от шаблона",   0.5),
    ("Resonance_Frequency", "Частота резонанса", "Лёгкость синхронизации",     0.5),
]

DNA_DYNAMIC_BIRTH = {
    "Respect": 1.0, "Patience": 1.0, "Internal_Light": 0.8,
    "Charge": 0.0,
}

RARITIES = [
    ("Common", "#6a7a8a"), ("Rare", "#4488cc"), ("Epic", "#8855cc"),
    ("Legendary", "#d08a30"), ("Mythic", "#c9a84c"),
]

BLOCKS = [
    {"icon": "①", "title": "Идентификация", "tag": "Обязательно", "fields": [
        ("ID_Object",        "input",  "GRND_CHAR_001"),
        ("Official_Name",    "input",  "Имя или название"),
        ("Object_Type",      "select", ["", "Character", "Location", "Artifact", "Institution", "Event"]),
        ("Author_Signature", "input",  "Подпись создателя"),
    ]},
    {"icon": "②", "title": "Социальный профиль", "tag": "Государство", "fields": [
        ("Social_Rank",  "select", ["", "Хозяин", "Хозяйка", "Хранитель", "Мастер", "Мастерица", "Специалист", "Гражданин", "Гражданка"]),
        ("Profession",   "input",  "Предназначение: сценарист · трейдер · хранитель..."),
        ("Area_of_Responsibility", "input", "За что отвечает в мире"),
        ("Access_Level", "slider", (1, 10, 5)),
    ]},
    {"icon": "③", "title": "Физическое воплощение", "tag": "Визуал", "fields": [
        ("Visual_Base",      "textarea", "Описание внешности или формы..."),
        ("Unique_Mark",      "input",    "Родинка, шрам, метка..."),
        ("Material_Texture", "input",    "Материал / текстура"),
    ]},
    {"icon": "④", "title": "Глубинная суть", "tag": "Скрытое · тоже якорь", "fields": [
        ("Hidden_History",    "textarea", "Легенда объекта..."),
        ("Sensory_Response",  "textarea", "Что чувствует при взаимодействии..."),
        ("Domain_Connection", "input",    "К чему привязан по праву рождения"),
        ("Relationships",     "textarea", "Связи с другими (ID и тип связи)"),
    ]},
    {"icon": "⑤", "title": "Динамика", "tag": "Техника", "fields": [
        ("Object_Behavior",     "textarea", "Режимы, реакции на события..."),
        ("Interaction_Scripts", "textarea", "Доступные действия (через запятую)"),
    ]},
    {"icon": "⑥", "title": "Печать Создателя", "tag": "Только для тебя · хешируется", "fields": [
        ("Creator_Seal", "textarea", "Секретная фраза. НЕ хранится — только её SHA-256 хеш."),
    ]},
]

_SEAL_KEY = "Creator_Seal"


def rodit_pasport(data: dict, dna: dict, anchor: dict, image_bytes=None, image_name="") -> Path:
    PASPORTA_DIR.mkdir(parents=True, exist_ok=True)
    pid = (data.get("ID_Object") or "").strip() or f"chel_{uuid.uuid4().hex[:8]}"

    seal = (data.pop(_SEAL_KEY, "") or "").strip()
    seal_hash = hashlib.sha256(seal.encode("utf-8")).hexdigest() if seal else ""

    image_path = ""
    if image_bytes:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(image_name).suffix or ".png"
        img_file = IMAGES_DIR / f"{pid}{ext}"
        img_file.write_bytes(image_bytes)
        image_path = str(img_file)

    pasport = {
        "ID_Object": pid,
        "творец":    "Шеф",
        "рождён":    datetime.now().isoformat(timespec="seconds"),
        "Rarity":    data.get("Rarity", ""),
        **{k: v for k, v in data.items() if k not in ("ID_Object", "Rarity")},
        "днк_статика": dna,
        "состояние":   dict(DNA_DYNAMIC_BIRTH),
        "якорь":       anchor,
        "image":       image_path,
        "_Creator_Seal_Hash": seal_hash,
        "_кирпич":     "паспорт = якорь целиком · ступень 2",
        "_слои_заведены": False,
    }
    out = PASPORTA_DIR / f"{pid}.json"
    out.write_text(json.dumps(pasport, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def skan_pasporta() -> list[dict]:
    if not PASPORTA_DIR.exists():
        return []
    out = []
    for p in sorted(PASPORTA_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


ROZH_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
.rozh-root{ position:fixed; inset:0; background:#08080d; color:#a0a0b8;
  font-family:Inter,system-ui,sans-serif; overflow:auto; padding:26px; box-sizing:border-box; }
.rozh-head{ display:flex; align-items:center; gap:16px; margin-bottom:22px; }
.rozh-title{ font-size:1.4rem; font-weight:900; letter-spacing:0.14em; color:#c9a84c; }
.rozh-sub{ font-size:0.62rem; color:#55556a; letter-spacing:0.1em; text-transform:uppercase; }
.rozh-back{ margin-left:auto; padding:8px 20px; border-radius:8px;
  background:rgba(201,168,76,0.12); border:1px solid rgba(201,168,76,0.35);
  color:#d0d0e0; font-weight:400; font-size:0.82rem; text-transform:none; }
.rozh-wrap{ display:grid; grid-template-columns: 1fr 300px; gap:18px; max-width:1060px; }
.block{ background:#0e0e16; border:1px solid #1e1e30; border-radius:12px;
  padding:16px 18px; margin-bottom:14px; }
.block-head{ display:flex; align-items:center; gap:10px; margin-bottom:12px; }
.block-icon{ font-size:1.1rem; color:#c9a84c; }
.block-title{ font-size:0.92rem; font-weight:800; color:#d0d0e0; }
.block-tag{ margin-left:auto; font-size:0.55rem; padding:2px 9px; border-radius:10px;
  background:rgba(201,168,76,0.10); color:#8a6e2a; border:1px solid rgba(201,168,76,0.2);
  text-transform:uppercase; letter-spacing:0.06em; }
.dna-row{ display:flex; align-items:center; gap:12px; margin-bottom:5px; }
.dna-label{ font-size:0.72rem; color:#a0a0b8; width:130px; flex-shrink:0; }
.dna-val{ font-size:0.72rem; color:#c9a84c; width:34px; text-align:right; }
.rarity-row{ display:flex; gap:8px; flex-wrap:wrap; }
.rar-btn{ padding:6px 16px !important; border-radius:8px !important; font-size:0.75rem !important;
  font-weight:700 !important; text-transform:none !important; }
.born-item{ padding:10px 12px; border-radius:10px; background:#0e0e16;
  border:1px solid #1e1e30; margin-bottom:8px; display:flex; gap:10px; align-items:center; }
.born-ava{ width:34px; height:34px; border-radius:8px; object-fit:cover; flex-shrink:0; background:#14141e; }
.born-name{ font-size:0.85rem; font-weight:700; color:#d0d0e0; }
.born-meta{ font-size:0.58rem; color:#55556a; margin-top:2px; }
.rozh-foot{ margin-top:14px; padding:12px 16px; border-radius:10px; background:#0e0e16;
  border:1px dashed #2a2a44; font-size:0.62rem; color:#55556a; line-height:1.6; }
"""


def page_rozhenitsa():
    ui.add_head_html(f"<style>{ROZH_CSS}</style>")
    try:
        from nicegui import app
        if IMAGES_DIR.exists():
            app.add_static_files("/pasporta-img", str(IMAGES_DIR))
    except Exception:
        pass

    vals: dict = {}
    dna  = {pid: dflt for (pid, _, _, dflt) in DNA_STATIC_PARAMS}
    anchor = {"коронная_фраза": "", "вектор_тяги": "", "скрытый_вкус": "", "триггеры": ""}
    rarity = {"value": ""}
    photo = {"bytes": None, "name": ""}
    refs = {"born": None, "rar_btns": {}}

    def set_field(key, value):
        vals[key] = value

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
                img = p.get("image", "")
                ava = (f'<img class="born-ava" src="/pasporta-img/{Path(img).name}">'
                       if img else '<div class="born-ava"></div>')
                ui.html(f'<div class="born-item">{ava}<div>'
                        f'<div class="born-name">{p.get("Official_Name","?")}</div>'
                        f'<div class="born-meta">{p.get("Profession","—")} · '
                        f'{p.get("Rarity","")} · {p.get("ID_Object","")}</div></div></div>')

    def on_upload(e: events.UploadEventArguments):
        photo["bytes"] = e.content.read()
        photo["name"] = e.name
        ui.notify(f"Фото: {e.name}", color="positive")

    def pick_rarity(name):
        rarity["value"] = name
        for n, btn in refs["rar_btns"].items():
            color = dict(RARITIES)[n]
            active = (n == name)
            btn.style(f'border:1px solid {color}; color:{color}; '
                      f'background:{"rgba(201,168,76,0.14)" if active else "transparent"};')

    def rodit():
        if not (vals.get("Official_Name", "") or "").strip():
            ui.notify("Имя — обязательно.", color="warning"); return
        if not (vals.get("Profession", "") or "").strip():
            ui.notify("Предназначение (Профессия) — обязательно.", color="warning"); return
        data = dict(vals)
        data["Rarity"] = rarity["value"]
        a = dict(anchor)
        a["триггеры"] = [t.strip() for t in (a.get("триггеры", "") or "").split(",") if t.strip()]
        path = rodit_pasport(data, dict(dna), a, photo["bytes"], photo["name"])
        ui.notify(f"Рождён паспорт-якорь: {path.name}", color="positive")
        photo["bytes"] = None; photo["name"] = ""
        update_born()

    with ui.element("div").classes("rozh-root"):
        with ui.element("div").classes("rozh-head"):
            ui.html('<div><div class="rozh-title">СТРАНИЦА ЖИЗНИ</div>'
                    '<div class="rozh-sub">паспорт = якорь целиком · кусочек</div></div>')
            ui.button("← в кабинет", on_click=lambda: ui.navigate.to("/brat")) \
                .props("flat").classes("rozh-back")

        with ui.element("div").classes("rozh-wrap"):
            with ui.element("div"):
                # редкость
                with ui.element("div").classes("block"):
                    ui.html('<div class="block-head"><span class="block-icon">★</span>'
                            '<span class="block-title">Редкость</span></div>')
                    with ui.element("div").classes("rarity-row"):
                        for name, color in RARITIES:
                            b = ui.button(name, on_click=lambda n=name: pick_rarity(n)) \
                                .props("flat no-caps").classes("rar-btn") \
                                .style(f"border:1px solid {color}; color:{color}; background:transparent;")
                            refs["rar_btns"][name] = b

                # фото
                with ui.element("div").classes("block"):
                    ui.html('<div class="block-head"><span class="block-icon">▣</span>'
                            '<span class="block-title">Фото</span>'
                            '<span class="block-tag">визуал</span></div>')
                    ui.upload(on_upload=on_upload, auto_upload=True) \
                        .props("flat color=amber dense").style("width:100%")

                # шесть блоков
                for blk in BLOCKS:
                    with ui.element("div").classes("block"):
                        ui.html(f'<div class="block-head"><span class="block-icon">{blk["icon"]}</span>'
                                f'<span class="block-title">{blk["title"]}</span>'
                                f'<span class="block-tag">{blk["tag"]}</span></div>')
                        for key, kind, spec in blk["fields"]:
                            if kind == "input":
                                ui.input(key, placeholder=spec,
                                         on_change=lambda e, k=key: set_field(k, e.value)) \
                                    .props("dark dense").classes("w-full")
                            elif kind == "textarea":
                                ui.textarea(key, placeholder=spec,
                                            on_change=lambda e, k=key: set_field(k, e.value)) \
                                    .props("dark dense").classes("w-full")
                            elif kind == "select":
                                ui.select(spec, label=key,
                                          on_change=lambda e, k=key: set_field(k, e.value)) \
                                    .props("dark dense").classes("w-full")
                            elif kind == "slider":
                                lo, hi, df = spec
                                set_field(key, df)
                                with ui.element("div").classes("dna-row"):
                                    ui.html(f'<span class="dna-label">{key}</span>')
                                    vb = ui.html(f'<span class="dna-val">{df}</span>')
                                    def mk(k=key, vb=vb):
                                        def on(e):
                                            set_field(k, int(e.value))
                                            vb.content = f'<span class="dna-val">{int(e.value)}</span>'
                                        return on
                                    ui.slider(min=lo, max=hi, step=1, value=df, on_change=mk()) \
                                        .props("dark").style("flex:1")

                # ДНК
                with ui.element("div").classes("block"):
                    ui.html('<div class="block-head"><span class="block-icon">🧬</span>'
                            '<span class="block-title">ДНК · натура</span>'
                            '<span class="block-tag">вносится раз</span></div>')
                    for pid, label, descr, dflt in DNA_STATIC_PARAMS:
                        with ui.element("div").classes("dna-row"):
                            ui.html(f'<span class="dna-label" title="{descr}">{label}</span>')
                            vb = ui.html(f'<span class="dna-val">{dflt:.2f}</span>')
                            def mk(pid=pid, vb=vb):
                                def on(e):
                                    dna[pid] = float(e.value)
                                    vb.content = f'<span class="dna-val">{float(e.value):.2f}</span>'
                                return on
                            ui.slider(min=0, max=1, step=0.05, value=dflt, on_change=mk()) \
                                .props("dark").style("flex:1")

                # якорь-резонанс
                with ui.element("div").classes("block"):
                    ui.html('<div class="block-head"><span class="block-icon">⚓</span>'
                            '<span class="block-title">Якорь · резонанс</span>'
                            '<span class="block-tag">доступно при нуле</span></div>')
                    ui.input("Коронная фраза",
                             on_change=lambda e: anchor.update(коронная_фраза=e.value)).props("dark dense").classes("w-full")
                    ui.input("Вектор тяги (куда тянет)",
                             on_change=lambda e: anchor.update(вектор_тяги=e.value)).props("dark dense").classes("w-full")
                    ui.input("Скрытый вкус",
                             on_change=lambda e: anchor.update(скрытый_вкус=e.value)).props("dark dense").classes("w-full")
                    ui.input("Триггеры памяти (через запятую)",
                             on_change=lambda e: anchor.update(триггеры=e.value)).props("dark dense").classes("w-full")

                ui.button("РОДИТЬ ПАСПОРТ-ЯКОРЬ", on_click=rodit).props("flat").style(
                    "margin-top:8px; width:100%; padding:14px; border-radius:12px;"
                    "background:linear-gradient(135deg,rgba(201,168,76,0.25),rgba(201,168,76,0.12));"
                    "border:1px solid rgba(201,168,76,0.5); color:#fff; font-weight:800; letter-spacing:0.1em;")

                ui.html('<div class="rozh-foot">⬡ Паспорт = ЯКОРЬ целиком · доступен при нуле заряда.<br>'
                        'Рождается ОДИН passport.json (кусочек) в GRONDHEIM_CITY/паспорта/.<br>'
                        'Папки-слои НЕ заводятся (ступень 5). Печать → только SHA-256 хеш.</div>')

            with ui.element("div"):
                with ui.element("div").classes("block"):
                    ui.html('<div class="block-head"><span class="block-icon">⬡</span>'
                            '<span class="block-title">Рождённые</span></div>')
                    refs["born"] = ui.element("div")
                    update_born()


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/rozhenitsa")
    def _rozh_page():
        page_rozhenitsa()
    ui.run(title="Страница Жизни · Грондхейм", port=8103, reload=False)
