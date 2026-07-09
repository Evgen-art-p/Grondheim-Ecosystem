# -*- coding: utf-8 -*-
# patch_llm_typing2.py — LLM_TYPING_V2
# ─────────────────────────────────────────────────────────────
# Дельта поверх LLM_TYPING_V1. Закрывает reportArgumentType в
# chat_with_images (строка ~494).
#
# КОРЕНЬ: messages = [{"role": "system", "content": system}] — Pylance
# по первому элементу решает, что content всегда str, и весь список
# типизируется list[dict[str, str]]. Но в chat_with_images формат
# сообщений честно СМЕШАННЫЙ по контракту OpenRouter/OpenAI vision:
# у обычных реплик content — строка, у сообщения с картинками —
# список блоков [{"type":"image_url",...}, {"type":"text",...}].
# Это не опечатка и не костыль — так требует протокол vision-API,
# один текстовый content не умеет нести картинку. Задача типизации —
# просто честно назвать то, что уже происходит в рантайме.
#
# ПРАВКА: явная аннотация messages при объявлении —
# list[dict[str, Any]]. chat() и chat_with_tools() не трогаем: там
# content везде строка, аннотация им не нужна (и не задета отчётом).
#
# ЗАПУСК из корня:  python patch_llm_typing2.py
# Требует уже применённый LLM_TYPING_V1 (нужен импорт typing).
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER   = "LLM_TYPING_V2"
REQUIRED = "LLM_TYPING_V1"

ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "llm.py"

# ── импорт Any (LLM_TYPING_V1 добавил Optional, Callable — доносим Any) ──
OLD_IMPORT = "from typing import Optional, Callable  # LLM_TYPING_V1"
NEW_IMPORT = "from typing import Optional, Callable, Any  # LLM_TYPING_V1 / LLM_TYPING_V2"

# ── messages в chat_with_images: явный смешанный тип content.
#    Якорь начинается с def chat_with_images(...) — общий шаблон
#    proxies/messages/history дословно совпадает с chat(), поэтому
#    без сигнатуры функции якорь ловит оба места сразу (найдено 2). ──
OLD = '''def chat_with_images(system: str, user_text: str, images: Optional[list] = None,
                     knowledge: str = "", history: Optional[list] = None,
                     temperature: Optional[float] = None,
                     agent_id: str = "unknown", slot_id: str = "unknown",
                     knowledge_source: str = "internal") -> str:
    """
    Отправляет запрос с изображениями (vision).

    Args:
        system: системный промпт
        user_text: текстовое сообщение
        images: список dict [{"base64": "...", "mime_type": "image/png", "name": "file.png"}, ...]
        knowledge: база знаний
        history: история диалога
    """
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    messages = [{"role": "system", "content": system}]
    if knowledge:
        messages.append({"role": "user", "content": f"БАЗА ЗНАНИЙ:\\n{knowledge}"})
        messages.append({"role": "assistant", "content": "Принял базу знаний. Готов к работе."})

    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})'''

NEW = '''def chat_with_images(system: str, user_text: str, images: Optional[list] = None,
                     knowledge: str = "", history: Optional[list] = None,
                     temperature: Optional[float] = None,
                     agent_id: str = "unknown", slot_id: str = "unknown",
                     knowledge_source: str = "internal") -> str:
    """
    Отправляет запрос с изображениями (vision).

    Args:
        system: системный промпт
        user_text: текстовое сообщение
        images: список dict [{"base64": "...", "mime_type": "image/png", "name": "file.png"}, ...]
        knowledge: база знаний
        history: история диалога
    """
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    # LLM_TYPING_V2: content здесь честно смешанный — обычная реплика
    # несёт строку, сообщение с картинкой ниже несёт список блоков
    # (протокол vision OpenRouter/OpenAI). dict[str, Any] называет то,
    # что уже происходит в рантайме, а не выдумывает новое поведение.
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    if knowledge:
        messages.append({"role": "user", "content": f"БАЗА ЗНАНИЙ:\\n{knowledge}"})
        messages.append({"role": "assistant", "content": "Принял базу знаний. Готов к работе."})

    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})'''

EOF_MARKER = "\n# LLM_TYPING_V2 — маркер идемпотентности\n"

BLOCKS = [
    ("импорт Any",                       OLD_IMPORT, NEW_IMPORT),
    ("chat_with_images: messages типизация", OLD, NEW),
]


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: messages в chat_with_images")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if REQUIRED not in text:
        print(f"✗ не наложен базовый патч {REQUIRED}.")
        print("  Сначала прогони patch_llm_typing.py — этот идёт поверх него.")
        sys.exit(1)

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
    print("• правки внесены (2 блока)")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}\n  Файл откатан из бэкапа.")
        sys.exit(1)

    print()
    print("  ГОТОВО: messages в chat_with_images аннотирован list[dict[str, Any]].")
    print("  Vision-протокол (список блоков в content) больше не конфликтует")
    print("  с обычными строковыми репликами того же списка.")
    print("═" * 62)


if __name__ == "__main__":
    main()
