# patch_ubrat_block2_i_porodu.py
# UBRAT_BLOCK2_I_PORODU_V1 · убрать блок ② "Социальный профиль" и породу из ДНК
# ─────────────────────────────────────────────────────────────
# Закон (Шеф, 28.06): "блок 1 оставь, блок 2 убрать, блок 3,4,5,6 и днк
# оставь" + "породу тоже убери" + "режем, порода уже в маски уходит".
#
# Порода теперь переезжает в маски (слой 2/прописка) — НЕ отменяется,
# просто больше не задаётся в форме рождения личности (слой 1). Закон
# §2.1 (резидент/хранитель/воркер) остаётся в летописи, просто его
# источник меняется: раньше — форма рождения, теперь — маска.
#
# Делает в ui_registry.py:
#   1. Убирает блок ② "Социальный профиль" из BLOCKS целиком
#      (Social_Rank, Profession, Area_of_Responsibility, Access_Level).
#      ВНИМАНИЕ: BLOCKS[:3] в левой колонке и BLOCKS[3:] в правой колонке
#      берут блоки по срезу индексов — при удалении блока ② сдвигаются
#      все индексы. Патч правит сами срезы, чтобы левая колонка осталась
#      с ①③ (было ①②③), правая — без сдвига (④⑤⑥, было то же самое,
#      но индекс блока ⑦ после удаления ② меняется с 6 на 5 — НЕ влияет,
#      т.к. ⑦ и так не рендерится текущим кодом, см. ниже).
#   2. Убирает блок "Порода" из ДНК-секции (UI: 3 кнопки + obj["порода"]
#      в collect_form/populate_form/clear_form).
#   3. Save_object: убирает проверку уникальности резидента — она
#      работала по obj.get("порода"), которого больше нет в форме.
#
# Поля Social_Rank/Profession/Area_of_Responsibility/Access_Level
# остаются как имена ключей в коде (используются в детальном просмотре
# каталога — see_detail) — НЕ трогаем, это просмотр старых записей,
# не форма ввода.
#
# Идемпотентно. Бэкап в .bak_ubrat_block2_poroda.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "UBRAT_BLOCK2_I_PORODU_V1"
TARGET = Path(__file__).resolve().parent / "ui_registry.py"


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_registry.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    # ── 1) Убираем блок ② из списка BLOCKS целиком ──
    old_block2 = '''    {
        "icon": "②",
        "title": "Социальный профиль",
        "tag": "Государство",
        "fields": [
            ("Social_Rank", "select", ["", "Хозяин", "Хозяйка", "Хранитель", "Мастер", "Мастерица", "Специалист", "Гражданин", "Гражданка"], False),
            ("Profession", "input", "Сценарист смыслов...", False),
            ("Area_of_Responsibility", "input", "За что отвечает в мире", True),
            ("Access_Level", "slider", (1, 10, 5), False),
        ]
    },
'''
    if old_block2 not in src:
        print("✗ шаг 1: не нашёл блок ② в списке BLOCKS — стоп")
        sys.exit(1)
    src = src.replace(old_block2, '', 1)

    # ── 2) Левая колонка рендерит BLOCKS[:3] (①②③) → теперь после удаления
    #       блока ② из списка останется ①③④⑤⑥⑦ — левая колонка должна
    #       рендерить ①③ = BLOCKS[:2], правая — ④⑤⑥ = BLOCKS[2:5] ──
    old_left = '                    # Блоки 1,2,3 (Идентификация, Социальный, Физическое)\n                    for block in BLOCKS[:3]:'
    new_left = '                    # Блоки 1,3 (Идентификация, Физическое) — UBRAT_BLOCK2_I_PORODU_V1\n                    for block in BLOCKS[:2]:'
    if old_left not in src:
        print("✗ шаг 2: не нашёл цикл левой колонки BLOCKS[:3] — стоп")
        sys.exit(1)
    src = src.replace(old_left, new_left, 1)

    old_right = '                    # Блоки 4,5,6 (Глубинная суть, Динамика, Печать)\n                    for block in BLOCKS[3:]:'
    new_right = '                    # Блоки 4,5,6 (Глубинная суть, Динамика, Печать) — UBRAT_BLOCK2_I_PORODU_V1\n                    for block in BLOCKS[2:5]:'
    if old_right not in src:
        print("✗ шаг 2b: не нашёл цикл правой колонки BLOCKS[3:] — стоп")
        sys.exit(1)
    src = src.replace(old_right, new_right, 1)

    # ── 3) Убираем UI-блок "Порода" целиком из ДНК-секции ──
    old_poroda_ui = '''                        # Порода — PORODA_UBORKA_V1 (закон §2.1, личность слой 1, без прописки)
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

                        # Якорные точки'''
    new_poroda_ui = '''                        # Порода убрана из формы рождения — UBRAT_BLOCK2_I_PORODU_V1
                        # (порода теперь задаётся через маску/прописку, не при рождении)

                        # Якорные точки'''
    if old_poroda_ui not in src:
        print("✗ шаг 3: не нашёл UI-блок 'Порода' в ДНК — стоп")
        sys.exit(1)
    src = src.replace(old_poroda_ui, new_poroda_ui, 1)

    # ── 4) Объявления current_poroda/poroda_btns — убираем (мёртвые без UI) ──
    old_decl = '                  current_poroda = {"value": ""}  # PORODA_UBORKA_V1\n                  poroda_btns = {}\n'
    if old_decl not in src:
        print("✗ шаг 4: не нашёл объявление current_poroda/poroda_btns — стоп")
        sys.exit(1)
    src = src.replace(old_decl, '', 1)

    # ── 5) update_poroda_buttons — убираем функцию целиком ──
    old_func = '''                def update_poroda_buttons():
                    for p, b in poroda_btns.items():
                        b.classes(remove="active-mythic")
                        if p == current_poroda["value"]:
                            b.classes(add="active-mythic")

                def update_rarity_buttons():'''
    new_func = '''                def update_rarity_buttons():'''
    if old_func not in src:
        print("✗ шаг 5: не нашёл update_poroda_buttons — стоп")
        sys.exit(1)
    src = src.replace(old_func, new_func, 1)

    # ── 6) collect_form: убираем obj["порода"] = ... ──
    old_collect = '''                    if t == "agent":
                        obj["порода"] = current_poroda["value"]  # PORODA_UBORKA_V1
                        if anchor_points_widget["w"]: obj["Anchor_Points"] = anchor_points_widget["w"].value or ""'''
    new_collect = '''                    if t == "agent":
                        if anchor_points_widget["w"]: obj["Anchor_Points"] = anchor_points_widget["w"].value or ""'''
    if old_collect not in src:
        print("✗ шаг 6: не нашёл сборку obj['порода'] в collect_form — стоп")
        sys.exit(1)
    src = src.replace(old_collect, new_collect, 1)

    # ── 7) populate_form: убираем восстановление породы ──
    old_populate = '''                    if t == "agent":
                        current_poroda["value"] = obj.get("порода", "")  # PORODA_UBORKA_V1
                        update_poroda_buttons()
                        if anchor_points_widget["w"]: anchor_points_widget["w"].value = obj.get("Anchor_Points", "")'''
    new_populate = '''                    if t == "agent":
                        if anchor_points_widget["w"]: anchor_points_widget["w"].value = obj.get("Anchor_Points", "")'''
    if old_populate not in src:
        print("✗ шаг 7: не нашёл восстановление породы в populate_form — стоп")
        sys.exit(1)
    src = src.replace(old_populate, new_populate, 1)

    # ── 8) clear_form: убираем сброс породы ──
    old_clear = '''                    current_poroda["value"] = ""  # PORODA_UBORKA_V1
                    update_poroda_buttons()
                    for w in [anchor_points_widget, home_story_widget,'''
    new_clear = '''                    for w in [anchor_points_widget, home_story_widget,'''
    if old_clear not in src:
        print("✗ шаг 8: не нашёл сброс породы в clear_form — стоп")
        sys.exit(1)
    src = src.replace(old_clear, new_clear, 1)

    # ── 9) save_object: убираем проверку уникальности резидента (была по породе) ──
    old_check = '''                    # ── PORODA_PRI_ROZHDENII_V1: резидент один на город — предупреждение ──
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
                            )

                    # ── Печать Создателя: хешируем секретную фразу ──'''
    new_check = '''                    # Проверка уникальности резидента убрана вместе с породой — UBRAT_BLOCK2_I_PORODU_V1
                    # (порода теперь задаётся через маску, проверка переедет туда же)

                    # ── Печать Создателя: хешируем секретную фразу ──'''
    if old_check not in src:
        print("✗ шаг 9: не нашёл проверку уникальности резидента в save_object — стоп")
        sys.exit(1)
    src = src.replace(old_check, new_check, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}")
        sys.exit(1)

    if not TARGET.with_suffix(".py.bak_ubrat_block2_poroda").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_ubrat_block2_poroda"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: блок ② и порода убраны из формы; ①③④⑤⑥ + ДНК (без породы) остались")


if __name__ == "__main__":
    main()
