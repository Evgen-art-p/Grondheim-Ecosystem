# AKADEMIA_MODEL_SEL_V1
"""
AKADEMIA_MODEL_SEL_V1 — переключатель модели LLM в кабинете Академии\n(тем же способом, что у Брата). bibliotekar.sprosit() уже принимал\nmodel=... параметром — не хватало UI и передачи выбора в вызов.

Идемпотентно: если маркер AKADEMIA_MODEL_SEL_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_akademia_model_sel.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_akademia.py')
MARKER = 'AKADEMIA_MODEL_SEL_V1'

REPLACEMENTS = [
    ('import sys\nimport json\nfrom pathlib import Path\nfrom datetime import datetime, timezone\n\nfrom nicegui import ui, app', 'import os\nimport sys\nimport json\nfrom pathlib import Path\nfrom datetime import datetime, timezone\n\nfrom nicegui import ui, app\n\n# AKADEMIA_MODEL_SEL_V1: тот же каталог, что в кабинете Брата (ui_brat.py) —\n# один список моделей на весь город, не плодим второй источник правды.\n# bibliotekar.py уже принимает model=... в sprosit() — только UI не давал выбрать.\n_OPENROUTER_MODEL_ENV = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")\nMODELS_CATALOG = [\n    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},\n    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},\n    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},\n    {"id": "openai/gpt-4o-mini-2024-07-18",              "name": "GPT-4o mini",      "price": "$0,15 / $0,60"},\n    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},\n    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},\n]\nDEFAULT_MODEL = _OPENROUTER_MODEL_ENV or MODELS_CATALOG[0]["id"]'),
    ('.akad-btn{\n  padding:6px 14px; border-radius:7px; font-size:12px; font-weight:700;\n  cursor:pointer; display:flex; align-items:center;\n  background:rgba(255,255,255,0.03); color:rgba(255,255,255,0.55);\n  border:1px solid rgba(255,255,255,0.10);\n}', '.akad-btn{\n  padding:6px 14px; border-radius:7px; font-size:12px; font-weight:700;\n  cursor:pointer; display:flex; align-items:center;\n  background:rgba(255,255,255,0.03); color:rgba(255,255,255,0.55);\n  border:1px solid rgba(255,255,255,0.10);\n}\n\n/* AKADEMIA_MODEL_SEL_V1 — калька .brat-model-sel из ui_brat.py */\n.amodel-sel .q-field__control{ background:rgba(255,255,255,0.06)!important;\n  border:1px solid rgba(255,255,255,0.12)!important; border-radius:10px!important; }'),
    ('    state = {\n        "активное_место": _first,\n        "чат": [],\n        "руда": [],          # что принял загрузчик за эту сессию\n        "отчёт": "",\n    }', '    state = {\n        "активное_место": _first,\n        "чат": [],\n        "руда": [],          # что принял загрузчик за эту сессию\n        "отчёт": "",\n        "model": DEFAULT_MODEL,\n    }\n\n    def on_model_change(e):\n        state["model"] = e.value'),
    ('        try:\n            _otvet = await _bib.sprosit(msg, state["чат"][:-2], "Шеф")\n        except Exception as _e:', '        try:\n            _otvet = await _bib.sprosit(msg, state["чат"][:-2], "Шеф",\n                                        model=state.get("model"))\n        except Exception as _e:'),
    ('                with ui.row().style("gap:6px; align-items:center;"):\n                    _b1 = ui.element("div").classes("akad-btn")', '                with ui.row().style("gap:6px; align-items:center;"):\n                    with ui.element("div").classes("amodel-sel").style("margin-right:6px;"):\n                        _opts = {m["id"]: f\'{m["name"]} ({m["price"]})\' for m in MODELS_CATALOG}\n                        ui.select(_opts, value=state["model"], on_change=on_model_change) \\\n                            .props(\'dense borderless dark options-dense\').style("min-width:180px;")\n                    _b1 = ui.element("div").classes("akad-btn")'),
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

# AKADEMIA_MODEL_SEL_V1 — маркер идемпотентности