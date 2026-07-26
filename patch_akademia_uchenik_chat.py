# PATCH_AKADEMIA_UCHENIK_CHAT_V1
"""
PATCH_AKADEMIA_UCHENIK_CHAT_V1 -- чат Академии активируется по клику
на пузырёк и говорит с ЖИВЫМ учеником на этом месте (его личность
через rezidenty.sobrat_dushu), а не всегда библиотекарем. Маяк
подключён тем же способом: если горит, собеседник получает кусок
из внешнего мира. Библиотекарь остаётся отдельно -- за кнопкой
'Библиотека' (пока стаб, отдельная дверь ещё не построена).

Идемпотентно: если маркер PATCH_AKADEMIA_UCHENIK_CHAT_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_akademia_uchenik_chat.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_akademia.py')
MARKER = 'PATCH_AKADEMIA_UCHENIK_CHAT_V1'

REPLACEMENTS = [
    ('    # ── чат с учеником (честная заглушка первого слоя) ─────\n    async def send_message():\n        if not input_ref["element"]:\n            return\n        msg = (input_ref["element"].value or "").strip()\n        if not msg:\n            return\n        input_ref["element"].value = ""\n        state["чат"].append({"role": "user", "content": msg})\n        update_chat()\n\n        # PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: говорит БИБЛИОТЕКАРЬ.\n        # Личность его — из паспорта того, кто на посту; роль — из\n        # bibliotekar.py. Две разные вещи, склеенные в момент работы.\n        try:\n            import bibliotekar as _bib\n        except Exception as _e:\n            state["чат"].append({\n                "role": "assistant", "кто": "СИСТЕМА",\n                "content": f"движок библиотекаря не поднялся: {_e}"})\n            update_chat()\n            return\n\n        _imya_bib = ""\n        try:\n            _promt, _imya_bib = _bib.sobrat_promt(msg, "Шеф")\n        except Exception:\n            _promt = ""\n\n        if not _promt:\n            state["чат"].append({\n                "role": "assistant", "кто": "СИСТЕМА",\n                "content": ("Библиотекаря в городе пока нет — пост свободен. "\n                            "Посади кого-нибудь: Брат → Роль → библиотекарь.")})\n            update_chat()\n            return\n\n        state["чат"].append({"role": "assistant", "кто": _imya_bib,\n                             "content": "…ищу на полках"})\n        update_chat()\n        try:\n            _otvet = await _bib.sprosit(msg, state["чат"][:-2], "Шеф",\n                                        model=state.get("model"))\n        except Exception as _e:\n            _otvet = f"⚠ библиотекарь не отозвался: {_e}"\n        state["чат"].pop()          # снимаем «ищу»\n        state["чат"].append({"role": "assistant", "кто": _imya_bib,\n                             "content": _otvet})\n        update_chat()', '    # ── чат с учеником: активируется по клику на пузырёк ───\n    # PATCH_AKADEMIA_UCHENIK_CHAT_V1: раньше чат ВСЕГДА говорил\n    # библиотекарем, кто бы ни был выбран пузырьком — место просто\n    # красилось активным, но с ним никто не разговаривал. Теперь\n    # активное место и есть собеседник: клик по пузырьку меняет\n    # switch_mesto() -> state["активное_место"], и чат обращается\n    # именно к этому жителю (его личность — rezidenty.sobrat_dushu,\n    # та же развязка личность/роль, что у библиотекаря). Маяк\n    # подключён тем же способом: если горит — собеседник получает\n    # свежий кусок из внешнего мира.\n\n    async def _mayak_kusok(vopros: str) -> str:\n        """Сходить на Маяк, если он горит. Пустая строка — Маяк не\n        нужен или не отозвался, вызывающий просто ничего не добавит."""\n        try:\n            import mayak\n        except ImportError:\n            return ""\n        try:\n            if not mayak.gorit():\n                return ""\n            rez = await mayak.poisk(vopros, 4)\n            try:\n                mayak.zapisat_vizit("академия-ученик", vopros, rez.get("ok", False))\n            except Exception:\n                pass\n            return mayak.dlya_promta(rez, 4)\n        except Exception:\n            return ""\n\n    async def _sprosit_uchenika(dom, vopros: str, istoria: list, model: str) -> str:\n        p = _read_json(dom / "passport.json", {}) or {}\n        if not p:\n            return "⚠ паспорт не читается — не могу собрать личность."\n        try:\n            import rezidenty\n            dusha = rezidenty.sobrat_dushu(p)\n        except Exception:\n            dusha = f"Ты — {p.get(\'Official_Name\',\'житель\')}, житель Грондхейма.\\n"\n\n        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"\n               "Сидишь за партой, разговариваешь с Шефом. Говоришь своим "\n               "голосом и характером, не как ассистент.\\n")\n\n        snaruzhi = await _mayak_kusok(vopros)\n        if snaruzhi:\n            rol += ("\\n=== СХОДИЛ(А) НА МАЯК ===\\n"\n                    f"{snaruzhi}\\nЕсли пригодится — упомяни честно, что это "\n                    "принесено извне, не выдавай за своё знание.\\n")\n\n        promt = dusha + rol\n        _key = os.getenv("OPENROUTER_API_KEY", "")\n        if not _key:\n            return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."\n\n        messages = [{"role": "system", "content": promt}]\n        for m in (istoria or [])[-10:]:\n            r = "user" if m.get("role") == "user" else "assistant"\n            messages.append({"role": r, "content": m.get("content", "")})\n        messages.append({"role": "user", "content": vopros})\n\n        import httpx\n        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}\n        payload = {"model": model or DEFAULT_MODEL, "messages": messages}\n        try:\n            async with httpx.AsyncClient(timeout=120) as client:\n                r = await client.post(\n                    "https://openrouter.ai/api/v1/chat/completions",\n                    headers=headers, json=payload)\n                r.raise_for_status()\n                return r.json()["choices"][0]["message"]["content"]\n        except Exception as e:\n            return f"⚠ не отозвался(лась): {e}"\n\n    async def send_message():\n        if not input_ref["element"]:\n            return\n        msg = (input_ref["element"].value or "").strip()\n        if not msg:\n            return\n        input_ref["element"].value = ""\n\n        m = _mesto_row(mesta, state["активное_место"])\n        if not (m and m["занято"]):\n            state["чат"].append({"role": "user", "content": msg})\n            state["чат"].append({\n                "role": "assistant", "кто": "СИСТЕМА",\n                "content": "Это место свободно — здесь некому ответить. "\n                          "Кликни на занятый пузырёк."})\n            update_chat()\n            return\n\n        state["чат"].append({"role": "user", "content": msg})\n        update_chat()\n\n        state["чат"].append({"role": "assistant", "кто": m["имя"],\n                             "content": "…думает"})\n        update_chat()\n        try:\n            _otvet = await _sprosit_uchenika(m["дом"], msg, state["чат"][:-2],\n                                             state.get("model"))\n        except Exception as _e:\n            _otvet = f"⚠ не отозвался(лась): {_e}"\n        state["чат"].pop()\n        state["чат"].append({"role": "assistant", "кто": m["имя"],\n                             "content": _otvet})\n        update_chat()'),
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

# PATCH_AKADEMIA_UCHENIK_CHAT_V1 — маркер идемпотентности