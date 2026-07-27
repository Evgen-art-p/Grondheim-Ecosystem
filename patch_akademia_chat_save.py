# AKADEMIA_CHAT_SAVE_V1
"""
AKADEMIA_CHAT_SAVE_V1 -- сохранить/достать чат в кабинете Академии,
тем же способом, что у Брата (Брат/чаты). Своя полка на каждого
студента: дом/академия_чаты/ -- отдельно от личных чатов кабинета
жителя (дом/чаты/, ZHITEL_CHAT_SAVE_V1), Закон Двух Стандартов
(своя кухня внутри, общий язык на границе).

Требует: Академия/ui_akademia.py в исходном виде (send_message,
_mesto_row, state["чат"], mesta уже определены).

Идемпотентно: если маркер AKADEMIA_CHAT_SAVE_V1 уже стоит в файле —
патч молча выходит, повторно не наложится. Бэкап .bak делается один
раз, при первом применении.

Запуск из корня репо:  python patch_akademia_chat_save.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_akademia.py')
MARKER = 'AKADEMIA_CHAT_SAVE_V1'

CHAT_SAVE_FUNCS = '''    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar zpok-bar--zaryad"><div class="zpok-mid"></div>'
        f'<div class="zpok-fill" style="left:{left}%; width:{half}%; background:{zcolor};"></div></div></div>'
        f'<div class="zpok-row"><div class="zpok-lab">оптика<b style="color:{ocolor};">{optika}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" style="width:{int((1-mut)*100)}%; '
        f'background:{ocolor};"></div></div></div>'
        '</div>'
    )


# ═══════════════════════════════════════════════════════════
# AKADEMIA_CHAT_SAVE_V1 -- сохранить/достать чат, как у Брата
# (Брат/чаты) -- своя полка на каждого СТУДЕНТА (не общий котёл
# кабинета Академии): дом/академия_чаты/, отдельно от личных чатов
# кабинета жителя (дом/чаты/).
# ═══════════════════════════════════════════════════════════

def _save_chat_akademii(dom: Path, chat: list) -> str:
    chats_dir = dom / "академия_чаты"
    chats_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fp = chats_dir / f"чат_{ts}.json"
    fp.write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp.name


def _list_chaty_akademii(dom: Path) -> list:
    chats_dir = dom / "академия_чаты"
    if not chats_dir.exists():
        return []
    return sorted(chats_dir.glob("чат_*.json"), reverse=True)


def _load_chat_akademii(fp: Path) -> list:
    return json.loads(fp.read_text(encoding="utf-8"))'''

DO_SAVE_LOAD_FUNCS = '''        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
        update_chat()

    # AKADEMIA_CHAT_SAVE_V1
    def do_save_chat_akad():
        """Сохраняет чат в дом ТЕКУЩЕГО студента (активное место) --
        своя полка, не общий котёл кабинета Академии."""
        if not state["чат"]:
            ui.notify("Чат пустой — нечего сохранять", type="warning")
            return
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — сохранять некуда", type="warning")
            return
        name = _save_chat_akademii(m["дом"], state["чат"])
        ui.notify(f"💾 сохранено: {name}", type="positive")

    async def do_load_chat_akad():
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — читать некому", type="warning")
            return
        chats = _list_chaty_akademii(m["дом"])
        if not chats:
            ui.notify("Сохранённых чатов нет", type="warning")
            return
        with ui.dialog() as dlg, ui.card().style(
            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "
            "border-radius:16px; min-width:340px; padding:20px;"
        ):
            ui.html('<div style="color:rgba(255,255,255,0.9); font-weight:700; '
                    'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">'
                    '📂 ВЫБЕРИ ЧАТ</div>')
            for fp in chats[:20]:
                label = fp.stem.replace("чат_", "")
                def _load(f=fp):
                    state["чат"] = _load_chat_akademii(f)
                    update_chat()
                    dlg.close()
                    ui.notify(f"📂 загружен: {f.name}", type="positive")
                ui.button(label, on_click=_load).props("flat no-caps").style(
                    "width:100%; text-align:left; font-family:monospace; "
                    "font-size:0.78rem; color:rgba(255,255,255,0.75); "
                    "padding:8px 12px; border-radius:8px; "
                    "background:rgba(255,255,255,0.04); margin-bottom:4px;")
            ui.button("отмена", on_click=dlg.close).props("flat").style(
                "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")
        dlg.open()

    # ═══ LAYOUT — калька Биржи ═══════════════════════════════
    with ui.element("div").classes("app-container"):'''

CHAT_BUTTONS = '''                with ui.element("div").classes("floating-console"):
                    input_ref["element"] = ui.input(placeholder="Сообщение ученику...").props(
                        "borderless").style("flex:1")
                    input_ref["element"].on("keydown.enter", send_message)
                    # AKADEMIA_CHAT_SAVE_V1
                    ui.button("💾", on_click=do_save_chat_akad).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(0,204,255,0.9); background:rgba(0,204,255,0.10); "
                        "border:1px solid rgba(0,204,255,0.35);")
                    ui.button("📂", on_click=do_load_chat_akad).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(189,0,255,0.9); background:rgba(189,0,255,0.10); "
                        "border:1px solid rgba(189,0,255,0.35);")
                    ui.button("SEND", on_click=send_message).classes("send-button")'''

REPLACEMENTS = [
    (
        '    return (\n'
        '        \'<div class="zpok">\'\n'
        '        f\'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>\'\n'
        '        f\'<div class="zpok-bar zpok-bar--zaryad"><div class="zpok-mid"></div>\'\n'
        '        f\'<div class="zpok-fill" style="left:{left}%; width:{half}%; background:{zcolor};"></div></div></div>\'\n'
        '        f\'<div class="zpok-row"><div class="zpok-lab">оптика<b style="color:{ocolor};">{optika}</b></div>\'\n'
        '        f\'<div class="zpok-bar"><div class="zpok-fill" style="width:{int((1-mut)*100)}%; \'\n'
        '        f\'background:{ocolor};"></div></div></div>\'\n'
        '        \'</div>\'\n'
        '    )',
        CHAT_SAVE_FUNCS,
    ),
    (
        '        state["чат"].pop()\n'
        '        state["чат"].append({"role": "assistant", "кто": m["имя"],\n'
        '                             "content": _otvet})\n'
        '        update_chat()\n'
        '\n'
        '    # ═══ LAYOUT — калька Биржи ═══════════════════════════════\n'
        '    with ui.element("div").classes("app-container"):',
        DO_SAVE_LOAD_FUNCS,
    ),
    (
        '                with ui.element("div").classes("floating-console"):\n'
        '                    input_ref["element"] = ui.input(placeholder="Сообщение ученику...").props(\n'
        '                        "borderless").style("flex:1")\n'
        '                    input_ref["element"].on("keydown.enter", send_message)\n'
        '                    ui.button("SEND", on_click=send_message).classes("send-button")',
        CHAT_BUTTONS,
    ),
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_chat_save")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()

# AKADEMIA_CHAT_SAVE_V1 — маркер идемпотентности
