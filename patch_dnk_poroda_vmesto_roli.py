# patch_dnk_poroda_vmesto_roli.py
# DNK_PORODA_VMESTO_ROLI_V1 · в блоке "Цифровая ДНК": убрать Роль (A01...) и
# Коронную фразу, на место Роли — порода (резидент/хранитель/воркер)
# ─────────────────────────────────────────────────────────────
# Закон (Шеф, 27.06): "роль А01 и тд — убери. где воркшоп там можно
# хранитель резидент или воркер — три надписи." Порода садится РЯДОМ
# с Workshop_ID, не отдельным блоком ниже.
#
# Делает в ui_registry.py:
#   1. Убирает role_widget (селект "Роль" A01.../хранитель...) из ДНК-блока.
#   2. На его месте — три кнопки породы (резидент/хранитель/воркер).
#   3. Убирает core_phrase_widget ("Коронная фраза").
#   4. on_workshop_change больше не трогает role_widget (его нет).
#   5. collect_form/populate_form/clear_form — Turbo_Role и Core_Phrase
#      больше не собираются/не восстанавливаются; вместо Turbo_Role
#      пишется obj["порода"].
#
# Можно накатывать НЕЗАВИСИМО от patch_poroda_pri_rozhdenii.py — если тот
# уже стоял (блок ⟁ "Порода" отдельно внизу), этот патч его не трогает,
# просто появится второй способ задать породу. Рекомендуется накатывать
# на ЧИСТЫЙ файл (без patch_poroda_pri_rozhdenii.py), чтобы порода жила
# в одном месте — рядом с Workshop_ID, как просил Шеф.
#
# Идемпотентно. Бэкап в .bak_dnk_poroda. `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "DNK_PORODA_VMESTO_ROLI_V1"
TARGET = Path(__file__).resolve().parent / "ui_registry.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_registry.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    changed = False

    # ── 1) Блок "Цех и роль" → "Цех и порода". Заменяем правую колонку
    #       (role_widget select) на три кнопки породы. ──
    old_pair = '''                        # Цех и роль
                        with ui.grid(columns=2).classes("w-full gap-3 mb-3"):
                            with ui.column().classes("w-full gap-0"):
                                _WORKSHOP_QUARTER = {"residents": "Высотка", "turbo": "Квартал Мастеров", "social_mix": "Квартал Мастеров", "video_long": "Квартал Мастеров", "video_shorts": "Квартал Мастеров", "web_story": "Квартал Мастеров", "clipmakers": "Квартал Мастеров", "advertising": "Квартал Мастеров", "emo_card": "Квартал Мастеров", "logo_design": "Квартал Мастеров", "market_hit": "Квартал Мастеров", "living_book": "Квартал Мастеров", "trading": "Торговый Квартал", "hram": "Храм"}
                                def on_workshop_change(e):
                                    ws = e.value or ""
                                    # ЗАКОН КАРТРИДЖА: роли — из phases манифеста цеха
                                    opts = get_role_options(ws)
                                    new_options = {v: v if v else "— не задана —" for v in opts}
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
                                    if role_widget["w"]:
                                        role_widget["w"].options = new_options
                                        role_widget["w"].value = ""
                                        role_widget["w"].update()

                                workshop_widget["w"] = ui.select(
                                    label="Workshop_ID (Цех)",
                                    options={v: v if v else "— выбрать цех —" for v in get_workshop_options()},
                                    on_change=on_workshop_change,
                                ).classes("w-full")

                            with ui.column().classes("w-full gap-0"):
                                role_widget["w"] = ui.select(
                                    label="Роль",
                                    options={v: v if v else "— не задана —" for v in TURBO_ROLE_OPTIONS}
                                ).classes("w-full")

                        # Коронная фраза
                        core_phrase_widget["w"] = ui.input(
                            label="Коронная фраза (неизменяемая)",
                            placeholder="Три удара — и зритель твой..."
                        ).classes("w-full mb-3")
'''

    new_pair = '''                        # Цех и порода — DNK_PORODA_VMESTO_ROLI_V1
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

    if old_pair in src:
        src = src.replace(old_pair, new_pair, 1)
        changed = True
    else:
        print("✗ не нашёл блок 'Цех и роль' — стоп (структура файла отличается от ожидаемой)")
        sys.exit(1)

    # ── 2) Заводим current_poroda / poroda_btns там же, где role_widget был объявлен ──
    anchor_widgets = '                  workshop_widget = {"w": None}\n                  role_widget = {"w": None}\n                  core_phrase_widget = {"w": None}'
    new_widgets = '                  workshop_widget = {"w": None}\n                  current_poroda = {"value": ""}  # DNK_PORODA_VMESTO_ROLI_V1\n                  poroda_btns = {}'
    if anchor_widgets in src:
        src = src.replace(anchor_widgets, new_widgets, 1)
    else:
        print("✗ не нашёл объявление role_widget/core_phrase_widget — стоп")
        sys.exit(1)

    # ── 3) update_poroda_buttons рядом с update_rarity_buttons ──
    anchor_update_rarity = "                def update_rarity_buttons():"
    if anchor_update_rarity not in src:
        print("✗ не нашёл def update_rarity_buttons — стоп"); sys.exit(1)
    update_poroda_func = '''                def update_poroda_buttons():
                    for p, b in poroda_btns.items():
                        b.classes(remove="active-mythic")
                        if p == current_poroda["value"]:
                            b.classes(add="active-mythic")

                def update_rarity_buttons():'''
    src = src.replace(anchor_update_rarity, update_poroda_func, 1)

    # ── 4) collect_form: убираем Turbo_Role/Core_Phrase, добавляем "порода" ──
    old_collect = '''                        if role_widget["w"]: obj["Turbo_Role"] = role_widget["w"].value or ""
                        if core_phrase_widget["w"]: obj["Core_Phrase"] = core_phrase_widget["w"].value or ""
                        if anchor_points_widget["w"]: obj["Anchor_Points"] = anchor_points_widget["w"].value or ""'''
    new_collect = '''                        obj["порода"] = current_poroda["value"]  # DNK_PORODA_VMESTO_ROLI_V1
                        if anchor_points_widget["w"]: obj["Anchor_Points"] = anchor_points_widget["w"].value or ""'''
    if old_collect in src:
        src = src.replace(old_collect, new_collect, 1)
    else:
        print("✗ не нашёл сборку Turbo_Role/Core_Phrase в collect_form — стоп"); sys.exit(1)

    # ── 5) populate_form: убираем восстановление Turbo_Role/Core_Phrase, восстанавливаем породу ──
    old_populate = '''                        if role_widget["w"]: role_widget["w"].value = obj.get("Turbo_Role", "")
                        if core_phrase_widget["w"]: core_phrase_widget["w"].value = obj.get("Core_Phrase", "")
                        if anchor_points_widget["w"]: anchor_points_widget["w"].value = obj.get("Anchor_Points", "")'''
    new_populate = '''                        current_poroda["value"] = obj.get("порода", "")  # DNK_PORODA_VMESTO_ROLI_V1
                        update_poroda_buttons()
                        if anchor_points_widget["w"]: anchor_points_widget["w"].value = obj.get("Anchor_Points", "")'''
    if old_populate in src:
        src = src.replace(old_populate, new_populate, 1)
    else:
        print("✗ не нашёл восстановление Turbo_Role/Core_Phrase в populate_form — стоп"); sys.exit(1)

    # ── 6) clear_form: убираем сброс role_widget/core_phrase_widget, сбрасываем породу ──
    old_clear = '''                    for w in [workshop_widget, role_widget, core_phrase_widget,
                              anchor_points_widget, home_story_widget,
                              pull_vector_widget, hidden_taste_widget, trigger_keywords_widget]:
                        if w["w"]: w["w"].value = ""'''
    new_clear = '''                    current_poroda["value"] = ""  # DNK_PORODA_VMESTO_ROLI_V1
                    update_poroda_buttons()
                    for w in [workshop_widget,
                              anchor_points_widget, home_story_widget,
                              pull_vector_widget, hidden_taste_widget, trigger_keywords_widget]:
                        if w["w"]: w["w"].value = ""'''
    if old_clear in src:
        src = src.replace(old_clear, new_clear, 1)
    else:
        print("✗ не нашёл сброс role_widget/core_phrase_widget в clear_form — стоп"); sys.exit(1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}"); sys.exit(1)

    if not TARGET.with_suffix(".py.bak_dnk_poroda").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_dnk_poroda"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: Роль и Коронная фраза убраны из ДНК, рядом с Workshop_ID — порода")


if __name__ == "__main__":
    main()
