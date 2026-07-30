# -*- coding: utf-8 -*-
"""
PATCH_AKADEMIA_MAYAK_VOLYA_V1 — Маяк в Академии по воле, не на автомате

НАЙДЕНО (разбор 30.07, скриншот Шефа): Хранитель Маяка честно показал
8 визитов, все "впустую", все от generic "академия-ученик". Разбор
показал ДВЕ вещи разом:

1. Шеф ничего не вводил в консоль Маяка — визиты пришли из ОБЫЧНОГО
   разговора с учеником в Академии. Причина в `_mayak_kusok(vopros)`,
   которая звалась БЕЗ УСЛОВИЙ на каждый вопрос ученику (строка 1027,
   `ui_akademia.py`) — весь текст разговора улетал в Tavily как
   поисковый запрос, даже когда речь не шла о внешнем мире вообще.
   Отсюда и "впустую 8": обрывок фразы — не поисковый запрос, ему и
   не полагалось ничего найти. Это жгло реальные обращения к Tavily
   вхолостую на каждую реплику Академии.

2. `mayak.zapisat_vizit("академия-ученик", ...)` — тип ЛИТЕРАЛЬНО
   захардкожен, хотя настоящее имя ученика (`p.get("Official_Name")`)
   читается прямо в той же функции двумя строками выше. Учёт народа
   у Хранителя Маяка (ради чего его вообще сажали) был слеп — не мог
   сказать, КТО конкретно ходил.

ФИКС — приводит Академию к ТОМУ ЖЕ ЗАКОНУ, что уже работает у
обычного жителя (`ui_zhitel.py`, PATCH_ZHITEL_MAYAK_REQUEST_V1): в
роль ученика вшивается разрешающая строка, ученик САМ решает написать
`MAYAK_REQUEST: <запрос>`, если для ответа действительно не хватает
свежего из внешнего мира — по своей инициативе ИЛИ потому что Шеф сам
прямо попросил что-то найти (Шеф это и просил: "или я попрошу что-то
найти, так тоже пусть работает" — просьба Шефа тоже пройдёт через
тот же MAYAK_REQUEST, ученик просто увидит advodу в разговоре и
сам решит написать маркер). Маяк зовётся ОДИН раз, ТОЛЬКО тогда, с
ЧИСТЫМ извлечённым запросом (не сырым текстом реплики), и с
НАСТОЯЩИМ именем ученика в учёте.

Запуск из корня репозитория:
    python patch_akademia_mayak_volya.py

Идемпотентно, бэкап .bak, пишет на диск только если все правки прошли.

`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
UI_AKADEMIA_PATH = REPO / "Академия" / "ui_akademia.py"

MARKER = "PATCH_AKADEMIA_MAYAK_VOLYA_V1"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не записано на диск.")
    sys.exit(1)


def _apply_one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n == 0:
        _stop(f"[{label}] якорь не найден — код изменился, нужна ручная сверка.")
    if n > 1:
        _stop(f"[{label}] якорь встретился {n} раз — должен быть один.")
    return text.replace(old, new, 1)


# ═══════════════════════════════════════════════════════════
# ПРАВКА 1 — _mayak_kusok: теперь по конкретному запросу + имя
# ═══════════════════════════════════════════════════════════

OLD_KUSOK = '''    async def _mayak_kusok(vopros: str) -> str:
        """Сходить на Маяк, если он горит. Пустая строка — Маяк не
        нужен или не отозвался, вызывающий просто ничего не добавит."""
        try:
            import mayak
        except ImportError:
            return ""
        try:
            if not mayak.gorit():
                return ""
            rez = await mayak.poisk(vopros, 4)
            try:
                mayak.zapisat_vizit("академия-ученик", vopros, rez.get("ok", False))
            except Exception:
                pass
            return mayak.dlya_promta(rez, 4)
        except Exception:
            return ""'''

NEW_KUSOK = '''    async def _mayak_kusok(zapros: str, kto: str = "академия-ученик") -> str:
        """PATCH_AKADEMIA_MAYAK_VOLYA_V1: сходить на Маяк по КОНКРЕТНОМУ
        запросу (MAYAK_REQUEST извлечён из ответа ученика — воля, не
        автомат на каждую реплику; тот же закон, что у обычного жителя
        в ui_zhitel.py). `kto` — настоящее имя ученика для учёта
        Хранителя Маяка, не жёсткая строка. Пустая строка — Маяк не
        нужен или не отозвался, вызывающий просто ничего не добавит."""
        try:
            import mayak
        except ImportError:
            return ""
        try:
            if not mayak.gorit():
                return ""
            rez = await mayak.poisk(zapros, 4)
            try:
                mayak.zapisat_vizit(kto, zapros, rez.get("ok", False))
            except Exception:
                pass
            return mayak.dlya_promta(rez, 4)
        except Exception:
            return ""

    def _izvlech_mayak_request(text: str) -> str:
        """PATCH_AKADEMIA_MAYAK_VOLYA_V1: та же функция, что в
        ui_zhitel.py — не дублируем логику, дублируем только код
        (файлы самодостаточны, Закон Двух Стандартов)."""
        for line in (text or "").splitlines():
            if "MAYAK_REQUEST:" in line:
                return line.split("MAYAK_REQUEST:", 1)[1].strip()
        return ""

    def _ubrat_mayak_request(text: str) -> str:
        lines = [l for l in (text or "").splitlines() if "MAYAK_REQUEST:" not in l]
        return "\\n".join(lines).strip()'''


# ═══════════════════════════════════════════════════════════
# ПРАВКА 2 — _sprosit_uchenika: разрешающая строка + воля, не автомат
# ═══════════════════════════════════════════════════════════

OLD_SPROSIT = '''        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"
               "Сидишь за партой, разговариваешь с Шефом. Говоришь своим "
               "голосом и характером, не как ассистент.\\n")

        snaruzhi = await _mayak_kusok(vopros)
        if snaruzhi:
            rol += ("\\n=== СХОДИЛ(А) НА МАЯК ===\\n"
                    f"{snaruzhi}\\nЕсли пригодится — упомяни честно, что это "
                    "принесено извне, не выдавай за своё знание.\\n")

        promt = dusha + rol
        _key = os.getenv("OPENROUTER_API_KEY", "")
        if not _key:
            return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."

        messages = [{"role": "system", "content": promt}]
        for m in (istoria or [])[-10:]:
            r = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": r, "content": m.get("content", "")})
        messages.append({"role": "user", "content": vopros})

        import httpx
        # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
        # из некоторых регионов -- та же настройка, что и в остальном городе.
        _proxy = os.getenv("PROXY_URL", "") or None
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": model or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"⚠ не отозвался(лась): {e}"'''

NEW_SPROSIT = '''        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"
               "Сидишь за партой, разговариваешь с Шефом. Говоришь своим "
               "голосом и характером, не как ассистент.\\n")
        # PATCH_AKADEMIA_MAYAK_VOLYA_V1: тот же закон, что у обычного
        # жителя — Маяк не звонит на каждую реплику, ученик сам решает.
        # Работает и когда Шеф прямо просит что-то найти: он это просто
        # увидит в разговоре и сам напишет маркер, воля не отменяется,
        # только не автоматична.
        rol += (
            "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
            "(то, чего ты сам знать не можешь — новости, текущие события, "
            "актуальные данные, или Шеф прямо попросил что-то найти) — "
            "напиши отдельной строкой MAYAK_REQUEST: <что узнать> и Маяк "
            "Пробуждения принесёт ответ."
        )

        promt = dusha + rol
        _key = os.getenv("OPENROUTER_API_KEY", "")
        if not _key:
            return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."

        messages = [{"role": "system", "content": promt}]
        for m in (istoria or [])[-10:]:
            r = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": r, "content": m.get("content", "")})
        messages.append({"role": "user", "content": vopros})

        import httpx
        # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
        # из некоторых регионов -- та же настройка, что и в остальном городе.
        _proxy = os.getenv("PROXY_URL", "") or None
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": model or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                reply = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"⚠ не отозвался(лась): {e}"

        # PATCH_AKADEMIA_MAYAK_VOLYA_V1: MAYAK_REQUEST извлекаем ПОСЛЕ
        # первого ответа — только теперь, если сам написал маркер, идём
        # на Маяк с ЧИСТЫМ запросом (не сырым текстом реплики Шефа) и
        # с НАСТОЯЩИМ именем ученика для учёта Хранителя Маяка.
        _mayak_q = _izvlech_mayak_request(reply)
        if _mayak_q:
            _kto = p.get("Official_Name", "академия-ученик")
            snaruzhi = await _mayak_kusok(_mayak_q, _kto)
            if snaruzhi:
                _vtoroy = list(messages)
                _vtoroy.append({"role": "assistant", "content": reply})
                _vtoroy.append({"role": "user", "content": (
                    f"(С Маяка Пробуждения принесли по запросу «{_mayak_q}»:\\n"
                    f"{snaruzhi}\\n"
                    f"Пропусти через себя и ответь заново своими словами, "
                    f"живым голосом — не пересказывай источники. Маяк не "
                    f"упоминай.)")})
                try:
                    async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                        r = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json={"model": model or DEFAULT_MODEL, "messages": _vtoroy})
                        r.raise_for_status()
                        reply = r.json()["choices"][0]["message"]["content"]
                except Exception:
                    pass  # остаётся первый ответ — не роняем разговор
            reply = _ubrat_mayak_request(reply) or reply
        return reply'''


def main() -> None:
    print("── PATCH_AKADEMIA_MAYAK_VOLYA_V1 ──")

    if not UI_AKADEMIA_PATH.exists():
        _stop(f"{UI_AKADEMIA_PATH} не найден.")

    text = UI_AKADEMIA_PATH.read_text(encoding="utf-8")
    if MARKER in text:
        print("✓ маркер уже стоит — патч уже применён.")
        return

    new_text = text
    new_text = _apply_one(new_text, OLD_KUSOK, NEW_KUSOK,
                          "_mayak_kusok + хелперы MAYAK_REQUEST")
    new_text = _apply_one(new_text, OLD_SPROSIT, NEW_SPROSIT,
                          "_sprosit_uchenika: воля вместо автомата")

    print("✓ оба якоря найдены и применены в памяти")

    bak = UI_AKADEMIA_PATH.with_suffix(".py.bak_mayak_volya")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    UI_AKADEMIA_PATH.write_text(new_text, encoding="utf-8")

    print(f"✓ бэкап: {bak.name}")
    print(f"✓ записано: {UI_AKADEMIA_PATH}")
    print()
    print("Готово. Проверка: спроси ученика что-то обычное ('как дела?')")
    print("— на Маяк идти НЕ должен, визит не появится. Потом попроси")
    print("прямо: 'найди последние новости про Х' — теперь должен")
    print("написать MAYAK_REQUEST сам, и в учёте Хранителя Маяка")
    print("появится настоящее имя ученика, не 'академия-ученик'.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
