# MAYAK_MODEL_SEL_V1
"""
MAYAK_MODEL_SEL_V1 — переключатель модели LLM в кабинете Маяка\n(тем же способом, что у Брата). _llm() раньше был жёстко прибит\nк OPENROUTER_MODEL — теперь читает выбор из шапки.

Идемпотентно: если маркер MAYAK_MODEL_SEL_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_mayak_model_sel.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('ГОРОД/ui_mayak.py')
MARKER = 'MAYAK_MODEL_SEL_V1'

REPLACEMENTS = [
    ('OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")\nOPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")\nPROXY_URL = os.getenv("PROXY_URL", "") or None', 'OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")\nOPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")\nPROXY_URL = os.getenv("PROXY_URL", "") or None\n\n# MAYAK_MODEL_SEL_V1: тот же каталог, что в кабинете Брата (ui_brat.py) —\n# один список моделей на весь город, не плодим второй источник правды.\nMODELS_CATALOG = [\n    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},\n    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},\n    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},\n    {"id": "openai/gpt-4o-mini-2024-07-18",              "name": "GPT-4o mini",      "price": "$0,15 / $0,60"},\n    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},\n    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},\n]\nDEFAULT_MODEL = OPENROUTER_MODEL or MODELS_CATALOG[0]["id"]'),
    ('.mbtn{ padding:6px 13px; border-radius:8px; font-size:11px; font-weight:700;\n  cursor:pointer; display:flex; align-items:center;\n  background:rgba(255,255,255,0.03); color:rgba(255,255,255,0.6);\n  border:1px solid rgba(255,255,255,0.10); }\n.mbtn:hover{ color:rgba(255,255,255,0.9); border-color:rgba(0,229,222,0.35); }', '.mbtn{ padding:6px 13px; border-radius:8px; font-size:11px; font-weight:700;\n  cursor:pointer; display:flex; align-items:center;\n  background:rgba(255,255,255,0.03); color:rgba(255,255,255,0.6);\n  border:1px solid rgba(255,255,255,0.10); }\n.mbtn:hover{ color:rgba(255,255,255,0.9); border-color:rgba(0,229,222,0.35); }\n\n/* MAYAK_MODEL_SEL_V1 — калька .brat-model-sel из ui_brat.py, бирюзовый акцент */\n.mmodel-sel .q-field__control{ background:rgba(255,255,255,0.06)!important;\n  border:1px solid rgba(0,229,222,0.20)!important; border-radius:10px!important; }'),
    ('    state = {"гнездо": _pervoe, "чат": [], "смыслы": []}\n    refs = {"чат": None, "отчёт": None, "ввод": None,\n            "лево": None, "право": None, "шапка": None}', '    state = {"гнездо": _pervoe, "чат": [], "смыслы": [], "модель": DEFAULT_MODEL}\n    refs = {"чат": None, "отчёт": None, "ввод": None,\n            "лево": None, "право": None, "шапка": None}\n\n    def on_model_change(e):\n        state["модель"] = e.value'),
    ('                                 json={"model": OPENROUTER_MODEL, "messages": msgs})', '                                 json={"model": state.get("модель", DEFAULT_MODEL), "messages": msgs})'),
    ('                update_shapka()\n                with ui.row().style("gap:6px;align-items:center;"):\n                    for podpis, deystvie in (', '                update_shapka()\n                with ui.row().style("gap:6px;align-items:center;"):\n                    with ui.element("div").classes("mmodel-sel").style("margin-right:6px;"):\n                        _opts = {m["id"]: f\'{m["name"]} ({m["price"]})\' for m in MODELS_CATALOG}\n                        ui.select(_opts, value=state["модель"], on_change=on_model_change) \\\n                            .props(\'dense borderless dark options-dense\').style("min-width:180px;")\n                    for podpis, deystvie in ('),
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

# MAYAK_MODEL_SEL_V1 — маркер идемпотентности