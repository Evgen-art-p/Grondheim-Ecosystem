# ZHITEL_MODEL_SEL_V1
"""
ZHITEL_MODEL_SEL_V1 — переключатель модели LLM в кабинете жителя\n(тем же способом, что у Брата: каталог моделей, state["model"], select в шапке).\nДвижок (call_zhitel_llm) уже принимал model параметром — не хватало UI.

Идемпотентно: если маркер ZHITEL_MODEL_SEL_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_zhitel_model_sel.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('жители/ui_zhitel.py')
MARKER = 'ZHITEL_MODEL_SEL_V1'

REPLACEMENTS = [
    ('OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")\nOPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")\nPROXY_URL        = os.getenv("PROXY_URL", "") or None', 'OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")\nOPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")\nPROXY_URL        = os.getenv("PROXY_URL", "") or None\n\n# ZHITEL_MODEL_SEL_V1: тот же каталог, что в кабинете Брата (ui_brat.py) —\n# один список моделей на весь город, не плодим второй источник правды.\nMODELS_CATALOG = [\n    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},\n    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},\n    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},\n    {"id": "openai/gpt-4o-mini-2024-07-18",              "name": "GPT-4o mini",      "price": "$0,15 / $0,60"},\n    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},\n    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},\n]\nDEFAULT_MODEL = OPENROUTER_MODEL or MODELS_CATALOG[0]["id"]'),
    ('    state = {"chat": [], "model": ""}\n    refs: dict = {"chat": None, "viewer": None, "input": None, "files": None}', '    state = {"chat": [], "model": DEFAULT_MODEL}\n    refs: dict = {"chat": None, "viewer": None, "input": None, "files": None}\n\n    def on_model_change(e):\n        state["model"] = e.value'),
    ('.zback{ padding:8px 20px; border-radius:10px;\n  background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08));\n  border:1px solid rgba(201,168,76,0.35); color:#fff; font-size:0.82rem; }', '.zback{ padding:8px 20px; border-radius:10px;\n  background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08));\n  border:1px solid rgba(201,168,76,0.35); color:#fff; font-size:0.82rem; }\n/* ZHITEL_MODEL_SEL_V1 — калька .brat-model-sel из ui_brat.py */\n.zmodel-sel .q-field__control{ background:rgba(255,255,255,0.06)!important;\n  border:1px solid rgba(255,255,255,0.12)!important; border-radius:10px!important; }'),
    ('                ui.element("div").style("flex:1")\n                ui.button("карта", on_click=lambda: ui.navigate.to("/grondheim")) \\\n                    .props("flat no-caps").classes("zback").style("margin-right:8px;")\n                ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")) \\\n                    .props("flat no-caps").classes("zback")', '                ui.element("div").style("flex:1")\n                with ui.element("div").classes("zmodel-sel").style("margin-right:12px;"):\n                    _opts = {m["id"]: f\'{m["name"]} ({m["price"]})\' for m in MODELS_CATALOG}\n                    ui.select(_opts, value=state["model"], on_change=on_model_change) \\\n                        .props(\'dense borderless dark options-dense\').style("min-width:190px;")\n                ui.button("карта", on_click=lambda: ui.navigate.to("/grondheim")) \\\n                    .props("flat no-caps").classes("zback").style("margin-right:8px;")\n                ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")) \\\n                    .props("flat no-caps").classes("zback")'),
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")

if __name__ == "__main__":
    main()

# ZHITEL_MODEL_SEL_V1 — маркер идемпотентности