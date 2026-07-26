# BIRZHA_MODEL_SEL_V1
"""
BIRZHA_MODEL_SEL_V1 -- селектор модели в шапке кабинета Совета Биржи.
Один общий переключатель на весь Совет (решение Шефа: 'GPT-4o mini
одну оставить, проще'). Требует patch_birzha_llm_model_sel.py --
накатывай llm.py первым, потом этот.

Идемпотентно: если маркер BIRZHA_MODEL_SEL_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_birzha_torg_model_sel.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Биржа/ui_torg.py')
MARKER = 'BIRZHA_MODEL_SEL_V1'

REPLACEMENTS = [
    ('import cartridge_registry as reg', 'import cartridge_registry as reg\nimport llm  # BIRZHA_MODEL_SEL_V1: переключатель модели -- set_model()/get_model()\n\n# BIRZHA_MODEL_SEL_V1: тот же каталог, что в кабинете Брата (ui_brat.py).\n# Дефолт -- GPT-4o mini (решение Шефа, 26.07: "одну оставить, проще" --\n# она и график по числам Вильямса читает, и считает, vision не нужен\n# никому в Совете сейчас -- ни один агент картинку не видит, llm.chat_with_images\n# существует, но не подключён ни к одному слоту).\nMODELS_CATALOG = [\n    {"id": "openai/gpt-4o-mini-2024-07-18",    "name": "GPT-4o mini",      "price": "$0.15/$0.60"},\n    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},\n    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},\n    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},\n    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},\n    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},\n]\nDEFAULT_MODEL = MODELS_CATALOG[0]["id"]'),
    ('        "arkhiv_digest": {},\n    }', '        "arkhiv_digest": {},\n        "model": DEFAULT_MODEL,   # BIRZHA_MODEL_SEL_V1\n    }\n\n    llm.set_model(state["model"])  # BIRZHA_MODEL_SEL_V1: применяем сразу при открытии кабинета\n\n    def on_model_change(e):        # BIRZHA_MODEL_SEL_V1\n        state["model"] = e.value\n        llm.set_model(e.value)'),
    ('                        avatars_ref["elements"][old_id] = avatar\n                ui.button("← Город", on_click=lambda: ui.navigate.to("/grondheim")).props("flat").style(\n                    "color:rgba(255,255,255,0.5);")', '                        avatars_ref["elements"][old_id] = avatar\n                with ui.element("div").style(\n                    "margin-right:10px; background:rgba(255,255,255,0.06); "\n                    "border:1px solid rgba(255,255,255,0.12); border-radius:10px;"\n                ):\n                    _opts = {m["id"]: f\'{m["name"]} ({m["price"]})\' for m in MODELS_CATALOG}\n                    ui.select(_opts, value=state["model"], on_change=on_model_change) \\\n                        .props(\'dense borderless dark options-dense\').style("min-width:190px;")\n                ui.button("← Город", on_click=lambda: ui.navigate.to("/grondheim")).props("flat").style(\n                    "color:rgba(255,255,255,0.5);")'),
]

# REPLACE_ALL — можно встречаться много раз, меняем ВСЕ вхождения
REPLACE_ALL = [
]

def main():
    if not TARGET.exists():
        print(f"⚠ не найден {TARGET} — запускай из корня репо")
        sys.exit(1)
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже стоит в {TARGET} — патч не нужен")
        return
    for old, new in REPLACEMENTS:
        if old not in text:
            print("⚠ не нашёл кусок для замены — файл изменился с момента патча:")
            print(old[:200])
            sys.exit(1)
        if text.count(old) > 1:
            print("⚠ кусок встречается больше одного раза — небезопасно патчить:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new, 1)
    for old, new in REPLACE_ALL:
        if old not in text:
            print("⚠ не нашёл кусок для повсеместной замены — файл изменился:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new)
    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")

if __name__ == "__main__":
    main()

# BIRZHA_MODEL_SEL_V1 — маркер идемпотентности