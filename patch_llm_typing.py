# -*- coding: utf-8 -*-
# patch_llm_typing.py — LLM_TYPING_V1
# ─────────────────────────────────────────────────────────────
# Закрывает неявный Optional в 6 сигнатурах llm.py + один голый
# `callable` вместо typing.Callable (Pylance не понимает `callable`
# как аннотацию типа — это встроенная функция-предикат, не тип).
#
# ЧИСТО ТИПИЗАЦИЯ. Ни одна формула ретраев, ни одна ветка chat()/
# chat_with_tools()/chat_with_images() не меняется — файл сам себя
# описывает как "перенесено МЕХАНИЗМОМ, без изменений в поведении",
# и патч этот закон уважает: только сигнатуры, тело не трогаем.
#
# ЗАПУСК из корня:  python patch_llm_typing.py
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "LLM_TYPING_V1"
ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "llm.py"

# ── 1. импорт typing (Optional + Callable) ──
OLD_IMPORT = '''import os
import json
import time
import requests
from pathlib import Path'''
NEW_IMPORT = '''import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Callable  # LLM_TYPING_V1'''

# ── 2. _post_with_retry: proxies/timeout ──
OLD_1 = '''def _post_with_retry(url: str, headers: dict, json_payload: dict,
                     proxies: dict = None, timeout: int = None) -> requests.Response:'''
NEW_1 = '''def _post_with_retry(url: str, headers: dict, json_payload: dict,
                     proxies: Optional[dict] = None, timeout: Optional[int] = None) -> requests.Response:'''

# ── 3. chat_with_tools: tools_schema/temperature/on_tool_call ──
OLD_2 = '''    knowledge: str = "",
    tools_schema: list = None,
    max_tool_rounds: int = 3,
    temperature: float = None,
    on_tool_call: callable = None,'''
NEW_2 = '''    knowledge: str = "",
    tools_schema: Optional[list] = None,
    max_tool_rounds: int = 3,
    temperature: Optional[float] = None,
    on_tool_call: Optional[Callable] = None,'''

# ── 4. chat: history/temperature ──
OLD_3 = '''def chat(system: str, user: str, knowledge: str = "", history: list = None, temperature: float = None,
         agent_id: str = "unknown", slot_id: str = "unknown",
         knowledge_source: str = "internal") -> str:'''
NEW_3 = '''def chat(system: str, user: str, knowledge: str = "", history: Optional[list] = None,
         temperature: Optional[float] = None,
         agent_id: str = "unknown", slot_id: str = "unknown",
         knowledge_source: str = "internal") -> str:'''

# ── 5. chat_with_images: images/history/temperature ──
OLD_4 = '''def chat_with_images(system: str, user_text: str, images: list = None,
                     knowledge: str = "", history: list = None, temperature: float = None,
                     agent_id: str = "unknown", slot_id: str = "unknown",
                     knowledge_source: str = "internal") -> str:'''
NEW_4 = '''def chat_with_images(system: str, user_text: str, images: Optional[list] = None,
                     knowledge: str = "", history: Optional[list] = None,
                     temperature: Optional[float] = None,
                     agent_id: str = "unknown", slot_id: str = "unknown",
                     knowledge_source: str = "internal") -> str:'''

EOF_MARKER = "\n# LLM_TYPING_V1 — маркер идемпотентности\n"

BLOCKS = [
    ("импорт typing",                    OLD_IMPORT, NEW_IMPORT),
    ("_post_with_retry: proxies/timeout", OLD_1, NEW_1),
    ("chat_with_tools: 3 параметра",      OLD_2, NEW_2),
    ("chat: history/temperature",         OLD_3, NEW_3),
    ("chat_with_images: 3 параметра",     OLD_4, NEW_4),
]


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: 7 неявных Optional в llm.py")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print("• маркер уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    ok = True
    for label, old, _new in BLOCKS:
        n = text.count(old)
        status = "✓" if n == 1 else "✗"
        print(f"  {status} якорь [{label}]: найден {n} раз (нужно ровно 1)")
        if n != 1:
            ok = False
    if not ok:
        print("✗ якоря не сошлись — файл отличается от ожидаемого. Ничего не режу.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_name(TARGET.name + f".bak_{ts}")
    shutil.copy2(TARGET, bak)
    print(f"• бэкап: {bak.name}")

    for _label, old, new in BLOCKS:
        text = text.replace(old, new, 1)
    text += EOF_MARKER

    TARGET.write_text(text, encoding="utf-8")
    print("• правки внесены (5 блоков)")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}\n  Файл откатан из бэкапа.")
        sys.exit(1)

    print()
    print("  ГОТОВО:")
    print("  • proxies/timeout/tools_schema/temperature×3/history×2/images")
    print("    → Optional[...] (было TYPE = None)")
    print("  • on_tool_call: callable → Optional[Callable] (callable — это")
    print("    встроенная функция-предикат, не аннотация типа)")
    print("  Ретраи/chat()/chat_with_tools()/chat_with_images() не тронуты.")
    print("═" * 62)


if __name__ == "__main__":
    main()
