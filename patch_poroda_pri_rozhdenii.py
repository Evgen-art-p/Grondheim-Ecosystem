# patch_poroda_pri_rozhdenii.py
# PORODA_PRI_ROZHDENII_V1 · порода (резидент/хранитель/воркер) — закон §2.1
# ─────────────────────────────────────────────────────────────
# Закон (Шеф, летопись §2.1): порода — это РОД (слой 1, навсегда),
# не маска. Не выводится из цеха/Workshop_ID — Архивариус-резидент
# сидит в торговом цехе рядом с воркерами, цех породу не определяет.
#
# Накатывается ПОСЛЕ patch_rozhdenie_tonkoe.py (ROZHDENIE_TONKOE_V1).
# Без него — стоп, нет смысла (нет ковчега, нет слоя "прописка").
#
# Делает четыре вещи в ui_registry.py:
#   1. Три кнопки породы (резидент/хранитель/воркер) рядом с типом
#      объекта — видны только когда Тип Объекта == "agent".
#   2. collect_form/populate_form/clear_form — порода едет в obj["порода"].
#   3. zavesti_sloi кладёт "порода" в passport.json рядом с "прописка": null.
#   4. save_object: проверка уникальности резидента —
#      ПРЕДУПРЕЖДЕНИЕ (не блокирует), если резидент с таким Official_Name
#      уже стоит в жители/ (любой этаж, любой ковчег).
#
# Идемпотентно. Бэкап в .bak_poroda. `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "PORODA_PRI_ROZHDENII_V1"
REQUIRED_MARKER = "ROZHDENIE_TONKOE_V1"
TARGET = Path(__file__).resolve().parent / "ui_registry.py"

PORODA_OPTIONS = ("резидент", "хранитель", "воркер")


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_registry.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    if REQUIRED_MARKER not in src:
        print(f"✗ не нашёл {REQUIRED_MARKER} — сначала накати patch_rozhdenie_tonkoe.py")
        sys.exit(1)

    # ── 1) Кнопки породы: вставляем после блока "Тип Объекта", перед "Изображение" ──
    anchor_poroda = '                  # ── Image upload ──'
    if anchor_poroda not in src:
        print("✗ не нашёл якорь '# ── Image upload ──' — стоп"); sys.exit(1)

    poroda_block = '''                  # ── PORODA_PRI_ROZHDENII_V1: порода (резидент/хранитель/воркер) ──
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

''' + anchor_poroda

    src = src.replace(anchor_poroda, poroda_block, 1)

    # ── 2) update_poroda_buttons + расширяем update_type_blocks, чтоб показывал блок породы только для agent ──
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

    anchor_update_type = "                def update_type_blocks():\n                    t = current_obj_type[\"value\"]"
    if anchor_update_type not in src:
        print("✗ не нашёл def update_type_blocks — стоп"); sys.exit(1)
    new_update_type = '''                def update_type_blocks():
                    t = current_obj_type["value"]
                    if poroda_block_ref["el"]:
                        poroda_block_ref["el"].set_visibility(t == "agent")'''
    src = src.replace(anchor_update_type, new_update_type, 1)

    # ── 3) collect_form: порода едет в obj ──
    anchor_collect = '                    obj = {\n                        "Rarity": current_rarity["value"],\n                        "Object_Type_Class": current_obj_type["value"],  # agent/location/asset\n                    }'
    if anchor_collect not in src:
        print("✗ не нашёл сборку obj в collect_form — стоп"); sys.exit(1)
    new_collect = '''                    obj = {
                        "Rarity": current_rarity["value"],
                        "Object_Type_Class": current_obj_type["value"],  # agent/location/asset
                        "порода": current_poroda["value"] if current_obj_type["value"] == "agent" else "",  # PORODA_PRI_ROZHDENII_V1
                    }'''
    src = src.replace(anchor_collect, new_collect, 1)

    # ── 4) populate_form: восстанавливаем породу при редактировании ──
    anchor_populate = '                    current_rarity["value"] = obj.get("Rarity", "")\n                    update_rarity_buttons()'
    if anchor_populate not in src:
        print("✗ не нашёл начало populate_form — стоп"); sys.exit(1)
    new_populate = '''                    current_rarity["value"] = obj.get("Rarity", "")
                    update_rarity_buttons()
                    current_poroda["value"] = obj.get("порода", "")  # PORODA_PRI_ROZHDENII_V1
                    update_poroda_buttons()'''
    src = src.replace(anchor_populate, new_populate, 1)

    # ── 5) clear_form: сбрасываем породу ──
    anchor_clear = '                    current_rarity["value"] = ""\n                    current_obj_type["value"] = ""\n                    update_rarity_buttons()\n                    update_type_blocks()'
    if anchor_clear not in src:
        print("✗ не нашёл начало clear_form — стоп"); sys.exit(1)
    new_clear = '''                    current_rarity["value"] = ""
                    current_obj_type["value"] = ""
                    current_poroda["value"] = ""  # PORODA_PRI_ROZHDENII_V1
                    update_rarity_buttons()
                    update_poroda_buttons()
                    update_type_blocks()'''
    src = src.replace(anchor_clear, new_clear, 1)

    # ── 6) zavesti_sloi: кладём породу в личность, рядом с пропиской ──
    anchor_lichnost = '    lichnost = dict(obj)\n    for _k in _MASKA_POLYA:\n        lichnost.pop(_k, None)          # маска ушла в файл\n    lichnost["прописка"] = None         # ПРЕБЫВАЕТ в ковчеге (слой 2 пуст)'
    if anchor_lichnost not in src:
        print("✗ не нашёл сборку lichnost в zavesti_sloi — стоп"); sys.exit(1)
    new_lichnost = '''    lichnost = dict(obj)
    for _k in _MASKA_POLYA:
        lichnost.pop(_k, None)          # маска ушла в файл
    lichnost["прописка"] = None         # ПРЕБЫВАЕТ в ковчеге (слой 2 пуст)
    lichnost["порода"] = obj.get("порода", "") or ""  # PORODA_PRI_ROZHDENII_V1: род, слой 1, навсегда'''
    src = src.replace(anchor_lichnost, new_lichnost, 1)

    # ── 7) save_object: проверка уникальности резидента (предупреждение, не запрет) ──
    anchor_save = '                    obj["_timestamp"] = datetime.now().isoformat()'
    if anchor_save not in src:
        print("✗ не нашёл строку _timestamp в save_object — стоп"); sys.exit(1)
    check_block = '''                    obj["_timestamp"] = datetime.now().isoformat()

                    # ── PORODA_PRI_ROZHDENII_V1: резидент один на город — предупреждение ──
                    if obj.get("порода") == "резидент":
                        _dup_name = (obj.get("Official_Name") or "").strip().lower()
                        _existing_resident = next(
                            (o for o in catalog
                             if o.get("порода") == "резидент"
                             and (o.get("Official_Name") or "").strip().lower() == _dup_name
                             and o.get("ID_Object") != obj.get("ID_Object")),
                            None
                        )
                        if _existing_resident:
                            ui.notify(
                                f"⚠ Резидент «{obj.get('Official_Name')}» уже есть в городе "
                                f"({_existing_resident.get('ID_Object')}). Один на город — закон §2.1. "
                                f"Сохраняю, но проверь, не плодим ли второго.",
                                type="warning", timeout=8000
                            )'''
    src = src.replace(anchor_save, check_block, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}"); sys.exit(1)

    if not TARGET.with_suffix(".py.bak_poroda").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_poroda"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: порода в форме рождения, в личности (passport.json), проверка резидента-уникума")


if __name__ == "__main__":
    main()
