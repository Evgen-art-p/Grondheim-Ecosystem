# -*- coding: utf-8 -*-
"""
patch_brat_header_birzha_style.py

Запускать из КОРНЯ репозитория:
    python patch_brat_header_birzha_style.py

Что делает:
  1) Добавляет в BRAT_CSS класс .birzha-header-btn — точная копия
     стиля кнопки "📡 РЫНОК" из Биржа/ui_torg.py (второй ряд, stage-toolbar).
  2) Переоформляет 5 кнопок хедера Брата (ГРОНДХЕЙМ, Тик, Прописка, Роль,
     Страница Жизни) — убирает разномастные inline-градиенты (золото/
     зелёный/синий у каждой свой цвет + margin-right:14px россыпью),
     сажает все пять на единый класс .birzha-header-btn и оборачивает
     в один flex-ряд с gap:10px (как оформлен ряд аватаров в Бирже).
  3) Переносит селектор модели на обёртку и ширину как в Бирже:
     было — класс .brat-model-sel, min-width:210px;
     стало — inline-div (margin-right:10px; background rgba(255,255,255,0.06);
     border 1px solid rgba(255,255,255,0.12); border-radius:10px),
     min-width:190px — 1-в-1 с шапкой Биржи.

Перед записью делает бэкап рядом: Брат/ui_brat.py.bak_before_birzha_style
Если паттерн не найден (файл уже другой) — скрипт НИЧЕГО не трогает
и прямо говорит об этом, без попытки угадать.
"""

import sys
from pathlib import Path

TARGET = Path("Брат") / "ui_brat.py"

OLD_CSS_ANCHOR = '''.brat-gate .q-btn__content{ width:100% !important; justify-content:center !important; }
.brat-gate:hover{ background: linear-gradient(135deg, rgba(201,168,76,0.24), rgba(201,168,76,0.14)) !important; }
"""'''

NEW_CSS_ANCHOR = '''.brat-gate .q-btn__content{ width:100% !important; justify-content:center !important; }
.brat-gate:hover{ background: linear-gradient(135deg, rgba(201,168,76,0.24), rgba(201,168,76,0.14)) !important; }

/* PATCH_BIRZHA_HEADER_STYLE — кнопки хедера Брата в стиле кнопки
   "РЫНОК" из Биржи (Биржа/ui_torg.py, stage-toolbar, второй ряд). */
.birzha-header-btn{
    padding: 8px 18px !important; border-radius: 8px !important;
    background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10)) !important;
    border: 1px solid rgba(0,255,136,0.35) !important;
    color: rgba(255,255,255,0.9) !important; font-weight: 700 !important;
}
.birzha-header-btn:hover{
    background: linear-gradient(135deg, rgba(0,255,136,0.24), rgba(0,204,255,0.16)) !important;
}
"""'''

OLD_HEADER_BLOCK = '''                ui.button("ГРОНДХЕЙМ",
                          on_click=lambda: ui.navigate.to("/karta")  # PATCH_KARTA_BTN
                          ).props("flat no-caps").style(
                    'padding:10px 40px; border-radius:10px; font-size:1.1rem; '
                    'font-weight:900; letter-spacing:0.16em; '
                    'background: linear-gradient(135deg, rgba(201,168,76,0.22), rgba(201,168,76,0.08)) !important; '
                    'border: 1px solid rgba(201,168,76,0.55); color:#c9a84c;')
                ui.element("div").style("flex:1")
                ui.button("⏱ Тик",
                          on_click=do_tik  # PATCH_BRAT_TIK_V1
                          ).props("flat no-caps").style(
                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "
                    "background:linear-gradient(135deg,rgba(80,200,140,0.15),rgba(80,200,140,0.08)); "
                    "border:1px solid rgba(80,200,140,0.35); color:#fff;")
                ui.button("Прописка",
                          on_click=do_propiska  # PATCH_PROPISKA_BRAT
                          ).props("flat no-caps").style(
                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "
                    "background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08)); "
                    "border:1px solid rgba(201,168,76,0.35); color:#fff;")
                ui.button("Роль",
                          on_click=do_naznachit_rol  # PATCH_NAZNACHIT_ROL
                          ).props("flat no-caps").style(
                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "
                    "background:linear-gradient(135deg,rgba(120,168,201,0.15),rgba(120,168,201,0.08)); "
                    "border:1px solid rgba(120,168,201,0.35); color:#fff;")
                ui.button("Страница Жизни",
                          on_click=lambda: ui.navigate.to("/registry")  # PATCH_ROZH_BTN
                          ).props("flat no-caps").style(
                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "
                    "background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08)); "
                    "border:1px solid rgba(201,168,76,0.35); color:#fff;")
                with ui.element("div").classes("brat-model-sel"):
                    opts = {m["id"]: f'{m["name"]} ({m["price"]})' for m in MODELS_CATALOG}
                    ui.select(opts, value=state["model"], on_change=on_model_change) \\
                        .props('dense borderless dark options-dense').style("min-width:210px;")'''

NEW_HEADER_BLOCK = '''                with ui.element("div").style(
                    "display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:center;"
                ):
                    ui.button("ГРОНДХЕЙМ",
                              on_click=lambda: ui.navigate.to("/karta")  # PATCH_KARTA_BTN
                              ).props("flat no-caps").classes("birzha-header-btn")
                    ui.button("⏱ Тик",
                              on_click=do_tik  # PATCH_BRAT_TIK_V1
                              ).props("flat no-caps").classes("birzha-header-btn")
                    ui.button("Прописка",
                              on_click=do_propiska  # PATCH_PROPISKA_BRAT
                              ).props("flat no-caps").classes("birzha-header-btn")
                    ui.button("Роль",
                              on_click=do_naznachit_rol  # PATCH_NAZNACHIT_ROL
                              ).props("flat no-caps").classes("birzha-header-btn")
                    ui.button("Страница Жизни",
                              on_click=lambda: ui.navigate.to("/registry")  # PATCH_ROZH_BTN
                              ).props("flat no-caps").classes("birzha-header-btn")
                ui.element("div").style("flex:1")
                with ui.element("div").style(
                    "margin-right:10px; background:rgba(255,255,255,0.06); "
                    "border:1px solid rgba(255,255,255,0.12); border-radius:10px;"
                ):
                    opts = {m["id"]: f'{m["name"]} ({m["price"]})' for m in MODELS_CATALOG}
                    ui.select(opts, value=state["model"], on_change=on_model_change) \\
                        .props('dense borderless dark options-dense').style("min-width:190px;")'''


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН файл: {TARGET.resolve()}")
        print("Запусти скрипт из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")
    original = text

    missing = []
    if OLD_CSS_ANCHOR not in text:
        missing.append("CSS-якорь (.brat-gate:hover / конец BRAT_CSS)")
    if OLD_HEADER_BLOCK not in text:
        missing.append("блок кнопок хедера (ГРОНДХЕЙМ...Страница Жизни + brat-model-sel)")

    if missing:
        print("Патч НЕ применён — не нашёл в файле ожидаемый текст:")
        for m in missing:
            print(f"  - {m}")
        print("Файл не тронут. Похоже, ui_brat.py уже отличается от версии,")
        print("под которую писан этот патч — нужно свериться заново.")
        sys.exit(2)

    text = text.replace(OLD_CSS_ANCHOR, NEW_CSS_ANCHOR, 1)
    text = text.replace(OLD_HEADER_BLOCK, NEW_HEADER_BLOCK, 1)

    backup = TARGET.with_name(TARGET.name + ".bak_before_birzha_style")
    backup.write_text(original, encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")

    print(f"Бэкап сохранён: {backup}")
    print(f"Патч применён: {TARGET}")
    print("Готово. Кнопки хедера Брата теперь на .birzha-header-btn")
    print("(стиль кнопки РЫНОК из Биржи), поле модели — min-width:190px,")
    print("обёртка как в шапке Биржи.")


if __name__ == "__main__":
    main()
