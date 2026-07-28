# PATCH_REKTOR_KANDIDAT_GOLOS_V1
"""
PATCH_REKTOR_KANDIDAT_GOLOS_V1 -- у кандидата на собеседовании
появляется СВОЙ голос.

БАГ (слово Шефа): "ректор знает о студенте, видит, вопрос задал, а
Нина ответить ему не может". Диагноз: кабинет Ректора (ui_rektor.py)
— чат в ОДНУ сторону. Шеф пишет, Ректор отвечает (через
rektor.sprosit(), знает о кандидате из kandidat_p) -- но сама Нина
никогда не говорит СВОИМИ словами. Личность кандидата используется
Ректором как информация о ней, а не как отдельный голос.

ЧТО ДЕЛАЕТ: добавляет кнопку "🙋 {имя} отвечает" рядом с SEND.
Клик -- берёт ПОСЛЕДНЮЮ реплику Ректора из чата, кандидат отвечает
на неё своей натурой (rezidenty.sobrat_dushu(kandidat_p), тот же
способ, что у студента в кабинете Академии), ответ ложится в чат
отдельной репликой с её именем -- НЕ через уста Ректора.

Не пишет в её личную память (dvizhok) -- это разговор-собеседование,
не прожитый урок; если Шеф захочет, чтобы это тоже запоминалось --
отдельный шаг (см. do_chtenie_uroka в Академии как образец).

Идемпотентно: если маркер PATCH_REKTOR_KANDIDAT_GOLOS_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_rektor_kandidat_golos.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_rektor.py')
MARKER = 'PATCH_REKTOR_KANDIDAT_GOLOS_V1'

OLD_NESTED_ANCHOR = '''    async def send_message():
        if not input_ref["element"] or not state["активен"]:
            if not state["активен"]:
                ui.notify("Сначала кликни по пузырьку", type="warning")
            return
        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        input_ref["element"].value = ""
        state["чат"].append({"role": "user", "content": msg})
        update_chat()
        state["чат"].append({"role": "assistant", "кто": imya, "content": "…думает"})
        update_chat()
        try:
            otvet = await _rek.sprosit(msg, state["чат"][:-2], kandidat_p, "Шеф",
                                       model=state.get("model"))
        except Exception as e:
            otvet = f"⚠ не отозвался(лась): {e}"
        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": imya, "content": otvet})
        update_chat()

    # ── действия (явные, не из текста чата) ─────────────────'''

NOVYI_NESTED_ANCHOR = '''    async def send_message():
        if not input_ref["element"] or not state["активен"]:
            if not state["активен"]:
                ui.notify("Сначала кликни по пузырьку", type="warning")
            return
        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        input_ref["element"].value = ""
        state["чат"].append({"role": "user", "content": msg})
        update_chat()
        state["чат"].append({"role": "assistant", "кто": imya, "content": "…думает"})
        update_chat()
        try:
            otvet = await _rek.sprosit(msg, state["чат"][:-2], kandidat_p, "Шеф",
                                       model=state.get("model"))
        except Exception as e:
            otvet = f"⚠ не отозвался(лась): {e}"
        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": imya, "content": otvet})
        update_chat()

    # PATCH_REKTOR_KANDIDAT_GOLOS_V1: у кандидата -- СВОЙ голос, не
    # через уста Ректора. Ректор про неё ЗНАЕТ, но говорит она сама.
    async def do_otvet_kandidata():
        if not kandidat_imya:
            ui.notify("Нет кандидата — отвечать некому", type="warning")
            return
        posledniy_rektor = None
        for m in reversed(state["чат"]):
            if m.get("role") == "assistant" and m.get("кто") == imya:
                posledniy_rektor = m.get("content", "")
                break
        if not posledniy_rektor:
            ui.notify(f"{imya or 'Ректор'} ещё ничего не сказал(а)", type="warning")
            return
        _key = os.getenv("OPENROUTER_API_KEY", "")
        if not _key:
            ui.notify("OPENROUTER_API_KEY не задан", type="negative")
            return
        try:
            import rezidenty
            dusha = rezidenty.sobrat_dushu(kandidat_p)
        except Exception:
            dusha = (f"Ты — {kandidat_imya}, житель Грондхейма. "
                    f"Говоришь от первого лица.\\n")
        rol = ("\\n=== ТЫ СЕЙЧАС НА СОБЕСЕДОВАНИИ В АКАДЕМИИ (Замок Сов) ===\\n"
              f"С тобой говорит Ректор{f' ({imya})' if imya else ''}. Отвечай "
              "своим голосом, своим характером — честно, не как ассистент.\\n")

        state["чат"].append({"role": "assistant", "кто": kandidat_imya,
                             "content": "…думает"})
        update_chat()

        messages = [{"role": "system", "content": dusha + rol},
                   {"role": "user", "content": posledniy_rektor}]
        import httpx
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": state.get("model") or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                otvet = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            otvet = f"⚠ {kandidat_imya} не отозвалась: {e}"

        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": kandidat_imya,
                             "content": otvet})
        update_chat()

    # ── действия (явные, не из текста чата) ─────────────────'''

OLD_LAYOUT_ANCHOR = '''                with ui.element("div").classes("floating-console"):
                    input_ref["element"] = ui.input(placeholder="Сообщение Ректору...").props(
                        "borderless").style("flex:1")
                    input_ref["element"].on("keydown.enter", send_message)
                    ui.button("SEND", on_click=send_message).classes("send-button")'''

NOVYI_LAYOUT_ANCHOR = '''                with ui.element("div").classes("floating-console"):
                    input_ref["element"] = ui.input(placeholder="Сообщение Ректору...").props(
                        "borderless").style("flex:1")
                    input_ref["element"].on("keydown.enter", send_message)
                    # PATCH_REKTOR_KANDIDAT_GOLOS_V1
                    ui.button(f"🙋 {kandidat_imya or 'кандидат'} отвечает",
                              on_click=do_otvet_kandidata).props("flat no-caps").style(
                        "font-size:0.75rem; padding:8px 14px; border-radius:20px; "
                        "color:rgba(80,250,123,0.9); background:rgba(80,250,123,0.10); "
                        "border:1px solid rgba(80,250,123,0.35); white-space:nowrap;")
                    ui.button("SEND", on_click=send_message).classes("send-button")'''

REPLACEMENTS = [
    (OLD_NESTED_ANCHOR, NOVYI_NESTED_ANCHOR),
    (OLD_LAYOUT_ANCHOR, NOVYI_LAYOUT_ANCHOR),
]

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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_kandidat_golos")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
