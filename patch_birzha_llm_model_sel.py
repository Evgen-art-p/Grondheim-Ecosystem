# BIRZHA_MODEL_SEL_V1
"""
BIRZHA_MODEL_SEL_V1 -- управляемая текущая модель в llm.py (Биржа).
Один общий переключатель на весь Совет (решение Шефа: 'GPT-4o mini
одну оставить, проще' -- vision сейчас никому из агентов не нужен,
все данные идут числом из williams_core.py, не картинкой).

Идемпотентно: если маркер BIRZHA_MODEL_SEL_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_birzha_llm_model_sel.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Биржа/llm.py')
MARKER = 'BIRZHA_MODEL_SEL_V1'

REPLACEMENTS = [
    ('OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")', 'OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")\n\n# BIRZHA_MODEL_SEL_V1: одна модель на весь Совет разом (решение Шефа —\n# "проще"), не per-slot. Кабинет (ui_torg.py) меняет её через set_model()\n# из выбора в шапке; агенты её не выбирают сами, только исполняют.\n_CURRENT_MODEL = OPENROUTER_MODEL\n\n\ndef set_model(model_id: str) -> None:\n    """Кабинет вызывает это при смене селектора в шапке. Пустое значение —\n    не трогаем текущую (защита от случайного сброса на дефолт)."""\n    global _CURRENT_MODEL\n    if model_id:\n        _CURRENT_MODEL = model_id\n\n\ndef get_model() -> str:\n    """Что сейчас реально летит в OpenRouter — для UI/логов."""\n    return _CURRENT_MODEL'),
]

# REPLACE_ALL — можно встречаться много раз, меняем ВСЕ вхождения
REPLACE_ALL = [
    ('"model": OPENROUTER_MODEL,', '"model": _CURRENT_MODEL,'),
    ('f"модель: {OPENROUTER_MODEL[:30]}{_t} | потолок: {LLM_MAX_TOKENS}")', 'f"модель: {_CURRENT_MODEL[:30]}{_t} | потолок: {LLM_MAX_TOKENS}")'),
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