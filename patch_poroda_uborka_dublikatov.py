# patch_poroda_uborka_dublikatov.py
# PORODA_UBORKA_V1 · чистка двух наслоившихся патчей породы + Workshop_ID
# ─────────────────────────────────────────────────────────────
# Закон (Шеф, 27.06): форма рождения даёт ТОЛЬКО личность (слой 1).
# Workshop_ID/Роль/Квартал/Коронная фраза — прописка (слой 2), их в форме
# не должно быть вообще. Порода (резидент/хранитель/воркер) — личность,
# она остаётся, но ОДНА, внутри блока "Цифровая ДНК", без дублей.
#
# На диске Шефа стоят ДВА патча друг на друге:
#   PORODA_PRI_ROZHDENII_V1   — отдельный блок ⟁ "Порода" (скрытый, ниже)
#   DNK_PORODA_VMESTO_ROLI_V1 — порода внутри ДНК, рядом с Workshop_ID
# Из-за этого: current_poroda/poroda_btns объявлены ДВАЖДЫ,
# update_poroda_buttons определена ДВАЖДЫ, Workshop_ID жив, квартал агента
# жив, мёртвый poroda_block_ref/_poroda_block остался.
#
# Этот патч сносит ВСЁ это и ставит ОДНУ чистую породу внутри ДНК-блока,
# без Workshop_ID, без квартала агента, без мёртвого скрытого блока ⟁.
#
# Идемпотентно. Бэкап в .bak_poroda_uborka.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "PORODA_UBORKA_V1"
TARGET = Path(__file__).resolve().parent / "ui_registry.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_registry.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    # ── 1) Объявления виджетов: убираем workshop_widget + первый current_poroda/poroda_btns ──
    old_decl = (
        '                  workshop_widget = {"w": None}\n'
        '                  current_poroda = {"value": ""}  # DNK_PORODA_VMESTO_ROLI_V1\n'
        '                  poroda_btns = {}\n'
    )
    new_decl = (
        '                  current_poroda = {"value": ""}  # PORODA_UBORKA_V1\n'
        '                  poroda_btns = {}\n'
    )
    if old_decl not in src:
        print("✗ шаг 1: не нашёл объявление workshop_widget/current_poroda — стоп")
        sys.exit(1)
    src = src.replace(old_decl, new_decl, 1)

    # ── 2) Убираем agent_quarter_widget из объявлений (прописка) ──
    old_q = '                  agent_quarter_widget = {"w": None} # Quarter агента\n'
    if old_q not in src:
        print("✗ шаг 2: не нашёл объявление agent_quarter_widget — стоп")
        sys.exit(1)
    src = src.replace(old_q, '', 1)

    # ── 3) Убираем ВЕСЬ дублирующий скрытый блок ⟁ "Порода" целиком ──
    old_hidden_block = '''                  # ── PORODA_PRI_ROZHDENII_V1: порода (резидент/хранитель/воркер) ──
                  current_poroda = {"value": ""}
                  poroda_btns = {}
                  poroda_block_ref = {"el": None}

                  with ui.element("div").classes("reg-block") as _poroda_block:
                    poroda_block_ref["el"] = _poroda_block
                    _poroda_block.set_visibility(False)
                    with ui.element("div").classes("reg-block-header"):
                        ui.html('<div class="icon">⟁</div>')
                        ui.html("<h3>Порода</h3>")
                        ui.html('<div class="tag">Род, навсегда · §2.1</div>')
                    with ui.element("div").classes("reg-block-body"):
                        with ui.row().classes("w-full gap-1"):
                            _PORODA_LABELS = {"резидент": "Резидент · один", "хранитель": "Хранитель · штучный", "воркер": "Воркер · много"}
                            for por in ("резидент", "хранитель", "воркер"):
                                def make_poroda_click(p=por):
                                    def on_click():
                                        current_poroda["value"] = p
                                        update_poroda_buttons()
                                    return on_click
                                pbtn = ui.button(
                                    _PORODA_LABELS[por], on_click=make_poroda_click(por)
                                ).classes("rar-btn").props("flat unelevated no-caps")
                                poroda_btns[por] = pbtn

                  # ── Image upload ──'''
    new_hidden_block = '''                  # ── Image upload ──'''
    if old_hidden_block not in src:
        print("✗ шаг 3: не нашёл скрытый блок ⟁ Порода — стоп")
        sys.exit(1)
    src = src.replace(old_hidden_block, new_hidden_block, 1)

    # ── 4) Убираем дублирующую update_poroda_buttons (вторую из двух) ──
    old_dup_func = '''                def update_poroda_buttons():
                    for p, b in poroda_btns.items():
                        b.classes(remove="active-mythic")
                        if p == current_poroda["value"]:
                            b.classes(add="active-mythic")

                def update_poroda_buttons():
                    for p, b in poroda_btns.items():
                        b.classes(remove="active-mythic")
                        if p == current_poroda["value"]:
                            b.classes(add="active-mythic")

                def update_rarity_buttons():'''
    new_func = '''                def update_poroda_buttons():
                    for p, b in poroda_btns.items():
                        b.classes(remove="active-mythic")
                        if p == current_poroda["value"]:
                            b.classes(add="active-mythic")

                def update_rarity_buttons():'''
    if old_dup_func not in src:
        print("✗ шаг 4: не нашёл дублированную update_poroda_buttons — стоп")
        sys.exit(1)
    src = src.replace(old_dup_func, new_func, 1)

    # ── 5) update_type_blocks: убираем ссылку на мёртвый poroda_block_ref ──
    old_utb = '''                def update_type_blocks():
                    t = current_obj_type["value"]
                    if poroda_block_ref["el"]:
                        poroda_block_ref["el"].set_visibility(t == "agent")
                    for tid, btn in type_btns.items():'''
    new_utb = '''                def update_type_blocks():
                    t = current_obj_type["value"]
                    for tid, btn in type_btns.items():'''
    if old_utb not in src:
        print("✗ шаг 5: не нашёл update_type_blocks с poroda_block_ref — стоп")
        sys.exit(1)
    src = src.replace(old_utb, new_utb, 1)

    # ── 6) Блок "Цех и порода" в ДНК → чистая порода без Workshop_ID/квартала ──
    old_dna_block = '''                        # Цех и порода — DNK_PORODA_VMESTO_ROLI_V1
                        with ui.grid(columns=2).classes("w-full gap-3 mb-3"):
                            with ui.column().classes("w-full gap-0"):
                                _WORKSHOP_QUARTER = {"residents": "Высотка", "turbo": "Квартал Мастеров", "social_mix": "Квартал Мастеров", "video_long": "Квартал Мастеров", "video_shorts": "Квартал Мастеров", "web_story": "Квартал Мастеров", "clipmakers": "Квартал Мастеров", "advertising": "Квартал Мастеров", "emo_card": "Квартал Мастеров", "logo_design": "Квартал Мастеров", "market_hit": "Квартал Мастеров", "living_book": "Квартал Мастеров", "trading": "Торговый Квартал", "hram": "Храм"}
                                def on_workshop_change(e):
                                    ws = e.value or ""
                                    # Автозаполнение квартала: манифест цеха → словарь → дефолт
                                    if agent_quarter_widget["w"] and ws:
                                        _cart = None
                                        try:
                                            from studio.modules_registry import get_cartridge
                                            _cart = get_cartridge(ws)
                                        except Exception:
                                            _cart = None
                                        auto_q = (_cart or {}).get("quarter") or _WORKSHOP_QUARTER.get(ws, "Квартал Мастеров")
                                        agent_quarter_widget["w"].value = auto_q
                                        agent_quarter_widget["w"].update()

                                workshop_widget["w"] = ui.select(
                                    label="Workshop_ID (Цех)",
                                    options={v: v if v else "— выбрать цех —" for v in get_workshop_options()},
                                    on_change=on_workshop_change,
                                ).classes("w-full")

                            with ui.column().classes("w-full gap-0"):
                                ui.html('<div style="font-size:0.72rem;color:var(--r-text-dim);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">Порода · §2.1</div>')
                                with ui.row().classes("w-full gap-1"):
                                    _PORODA_LABELS = {"резидент": "Резидент", "хранитель": "Хранитель", "воркер": "Воркер"}
                                    for por in ("резидент", "хранитель", "воркер"):
                                        def make_poroda_click(p=por):
                                            def on_click():
                                                current_poroda["value"] = p
                                                update_poroda_buttons()
                                            return on_click
                                        pbtn = ui.button(
                                            _PORODA_LABELS[por], on_click=make_poroda_click(por)
                                        ).classes("rar-btn").props("flat unelevated no-caps")
                                        poroda_btns[por] = pbtn
'''
    new_dna_block = '''                        # Порода — PORODA_UBORKA_V1 (закон §2.1, личность слой 1, без прописки)
                        ui.html('<div style="font-size:0.72rem;color:var(--r-text-dim);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Порода · резидент один на город / хранитель штучный / воркер много</div>')
                        with ui.row().classes("w-full gap-1 mb-3"):
                            _PORODA_LABELS = {"резидент": "Резидент", "хранитель": "Хранитель", "воркер": "Воркер"}
                            for por in ("резидент", "хранитель", "воркер"):
                                def make_poroda_click(p=por):
                                    def on_click():
                                        current_poroda["value"] = p
                                        update_poroda_buttons()
                                    return on_click
                                pbtn = ui.button(
                                    _PORODA_LABELS[por], on_click=make_poroda_click(por)
                                ).classes("rar-btn").props("flat unelevated no-caps")
                                poroda_btns[por] = pbtn
'''
    if old_dna_block not in src:
        print("✗ шаг 6: не нашёл блок 'Цех и порода' в ДНК — стоп")
        sys.exit(1)
    src = src.replace(old_dna_block, new_dna_block, 1)

    # ── 7) Убираем "Квартал агента" блок целиком (прописка) ──
    old_quarter = '''                        # Квартал агента (автозаполняется по цеху)
                        quarter_opts_agent = {"": "— выбрать квартал —"}
                        quarter_opts_agent.update({
                            "Высотка": "Высотка",
                            "Квартал Мастеров": "Квартал Мастеров",
                            "Торговый Квартал": "Торговый Квартал",
                        })
                        agent_quarter_widget["w"] = ui.select(
                            label="Квартал города",
                            options=quarter_opts_agent,
                        ).classes("w-full mb-3")

'''
    if old_quarter not in src:
        print("✗ шаг 7: не нашёл блок 'Квартал агента' — стоп")
        sys.exit(1)
    src = src.replace(old_quarter, '', 1)

    # ── 8) collect_form: убираем Quarter/Workshop_ID/hram-автозаполнение, оставляем одну строку породы ──
    old_collect = '''                    if t == "agent":
                        if agent_quarter_widget["w"]: obj["Quarter"] = agent_quarter_widget["w"].value or ""
                        if workshop_widget["w"]: obj["Workshop_ID"] = workshop_widget["w"].value or ""
                        # PATCH: цех Храм → предназначение "хранитель" (летит в 3_guardians)
                        if (obj.get("Workshop_ID") or "") == "hram" and not (obj.get("Profession") or "").strip():
                            obj["Profession"] = "хранитель"
                        obj["порода"] = current_poroda["value"]  # DNK_PORODA_VMESTO_ROLI_V1
                        if anchor_points_widget["w"]: obj["Anchor_Points"] = anchor_points_widget["w"].value or ""'''
    new_collect = '''                    if t == "agent":
                        obj["порода"] = current_poroda["value"]  # PORODA_UBORKA_V1
                        if anchor_points_widget["w"]: obj["Anchor_Points"] = anchor_points_widget["w"].value or ""'''
    if old_collect not in src:
        print("✗ шаг 8: не нашёл сборку Quarter/Workshop_ID в collect_form — стоп")
        sys.exit(1)
    src = src.replace(old_collect, new_collect, 1)

    # ── 9) Убираем дублирующую строку obj["порода"] в начале collect_form (PORODA_PRI_ROZHDENII_V1) ──
    old_dup_obj = '''                    obj = {
                        "Rarity": current_rarity["value"],
                        "Object_Type_Class": current_obj_type["value"],  # agent/location/asset
                        "порода": current_poroda["value"] if current_obj_type["value"] == "agent" else "",  # PORODA_PRI_ROZHDENII_V1
                    }'''
    new_dup_obj = '''                    obj = {
                        "Rarity": current_rarity["value"],
                        "Object_Type_Class": current_obj_type["value"],  # agent/location/asset
                    }'''
    if old_dup_obj not in src:
        print("✗ шаг 9: не нашёл начальную сборку obj с дублем породы — стоп")
        sys.exit(1)
    src = src.replace(old_dup_obj, new_dup_obj, 1)

    # ── 10) populate_form: убираем дубль восстановления породы в начале + Quarter/Workshop_ID в агенте ──
    old_pop_start = '''                    current_rarity["value"] = obj.get("Rarity", "")
                    update_rarity_buttons()
                    current_poroda["value"] = obj.get("порода", "")  # PORODA_PRI_ROZHDENII_V1
                    update_poroda_buttons()

                    # Тип объекта'''
    new_pop_start = '''                    current_rarity["value"] = obj.get("Rarity", "")
                    update_rarity_buttons()

                    # Тип объекта'''
    if old_pop_start not in src:
        print("✗ шаг 10a: не нашёл начало populate_form с дублем породы — стоп")
        sys.exit(1)
    src = src.replace(old_pop_start, new_pop_start, 1)

    old_pop_agent = '''                    if t == "agent":
                        if agent_quarter_widget["w"]: agent_quarter_widget["w"].value = obj.get("Quarter", "")
                        if workshop_widget["w"]: workshop_widget["w"].value = obj.get("Workshop_ID", "")
                        current_poroda["value"] = obj.get("порода", "")  # DNK_PORODA_VMESTO_ROLI_V1
                        update_poroda_buttons()
                        if anchor_points_widget["w"]: anchor_points_widget["w"].value = obj.get("Anchor_Points", "")'''
    new_pop_agent = '''                    if t == "agent":
                        current_poroda["value"] = obj.get("порода", "")  # PORODA_UBORKA_V1
                        update_poroda_buttons()
                        if anchor_points_widget["w"]: anchor_points_widget["w"].value = obj.get("Anchor_Points", "")'''
    if old_pop_agent not in src:
        print("✗ шаг 10b: не нашёл populate_form агента с Quarter/Workshop_ID — стоп")
        sys.exit(1)
    src = src.replace(old_pop_agent, new_pop_agent, 1)

    # ── 11) clear_form: убираем дубль сброса породы в начале + workshop_widget из списка ──
    old_clear_start = '''                    current_rarity["value"] = ""
                    current_obj_type["value"] = ""
                    current_poroda["value"] = ""  # PORODA_PRI_ROZHDENII_V1
                    update_rarity_buttons()
                    update_poroda_buttons()
                    update_type_blocks()'''
    new_clear_start = '''                    current_rarity["value"] = ""
                    current_obj_type["value"] = ""
                    update_rarity_buttons()
                    update_type_blocks()'''
    if old_clear_start not in src:
        print("✗ шаг 11a: не нашёл начало clear_form с дублем сброса породы — стоп")
        sys.exit(1)
    src = src.replace(old_clear_start, new_clear_start, 1)

    old_clear_mid = '''                    current_poroda["value"] = ""  # DNK_PORODA_VMESTO_ROLI_V1
                    update_poroda_buttons()
                    for w in [workshop_widget,
                              anchor_points_widget, home_story_widget,
                              pull_vector_widget, hidden_taste_widget, trigger_keywords_widget]:
                        if w["w"]: w["w"].value = ""'''
    new_clear_mid = '''                    current_poroda["value"] = ""  # PORODA_UBORKA_V1
                    update_poroda_buttons()
                    for w in [anchor_points_widget, home_story_widget,
                              pull_vector_widget, hidden_taste_widget, trigger_keywords_widget]:
                        if w["w"]: w["w"].value = ""'''
    if old_clear_mid not in src:
        print("✗ шаг 11b: не нашёл сброс workshop_widget в clear_form — стоп")
        sys.exit(1)
    src = src.replace(old_clear_mid, new_clear_mid, 1)

    old_clear_q = '''                    if loc_quarter_widget["w"]: loc_quarter_widget["w"].value = ""
                    if agent_quarter_widget["w"]: agent_quarter_widget["w"].value = ""'''
    new_clear_q = '''                    if loc_quarter_widget["w"]: loc_quarter_widget["w"].value = ""'''
    if old_clear_q not in src:
        print("✗ шаг 11c: не нашёл сброс agent_quarter_widget в clear_form — стоп")
        sys.exit(1)
    src = src.replace(old_clear_q, new_clear_q, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис после всех правок: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_poroda_uborka").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_poroda_uborka"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: дубли породы убраны, Workshop_ID/квартал агента убраны, осталась ОДНА чистая порода в ДНК")


if __name__ == "__main__":
    main()
