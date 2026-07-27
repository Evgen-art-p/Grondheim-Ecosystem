# ZHITEL_CHAT_SAVE_V1
"""
ZHITEL_CHAT_SAVE_V1 -- сохранить/достать чат в кабинете жителя, тем же
способом, что у Брата (Брат/чаты, ui_brat.py: save_chat/list_chats/
load_chat). Своя полка на каждого жителя: дом/чаты/, не общий котёл.

Идемпотентно: если маркер ZHITEL_CHAT_SAVE_V1 уже стоит в файле —
патч молча выходит, повторно не наложится. Бэкап .bak делается один
раз, при первом применении.

Запуск из корня репо:  python patch_zhitel_chat_save.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('жители/ui_zhitel.py')
MARKER = 'ZHITEL_CHAT_SAVE_V1'

CHAT_SAVE_FUNCS = '''
# ═══════════════════════════════════════════════════════════
# ZHITEL_CHAT_SAVE_V1 -- сохранить/достать чат, как у Брата
# (Брат/чаты) -- своя полка на каждого жителя: дом/чаты/, не общий
# котёл. Формат файла тот же: чат_YYYY-MM-DD_HH-MM-SS.json.
# ═══════════════════════════════════════════════════════════

def _save_chat_zhitelya(dom: Path, chat: list) -> str:
    chats_dir = dom / "чаты"
    chats_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fp = chats_dir / f"чат_{ts}.json"
    fp.write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp.name


def _list_chaty_zhitelya(dom: Path) -> list:
    chats_dir = dom / "чаты"
    if not chats_dir.exists():
        return []
    return sorted(chats_dir.glob("чат_*.json"), reverse=True)


def _load_chat_zhitelya(fp: Path) -> list:
    return json.loads(fp.read_text(encoding="utf-8"))


_ROOT = Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: файл в жители/, корень репо — на уровень выше'''

DO_SAVE_LOAD_FUNCS = '''        state["chat"].append({"role": "zhitel", "content": reply})
        state["waiting"] = False
        update_chat()

    # ZHITEL_CHAT_SAVE_V1
    def do_save_chat():
        if not state["chat"]:
            ui.notify("Чат пустой — нечего сохранять", color="warning")
            return
        if dom is None:
            ui.notify("дом не найден — сохранять некуда", color="warning")
            return
        name = _save_chat_zhitelya(dom, state["chat"])
        ui.notify(f"💾 сохранено: {name}", color="positive")

    async def do_load_chat():
        if dom is None:
            ui.notify("дом не найден — читать некому", color="warning")
            return
        chats = _list_chaty_zhitelya(dom)
        if not chats:
            ui.notify("Сохранённых чатов нет", color="warning")
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
                    state["chat"] = _load_chat_zhitelya(f)
                    update_chat()
                    dlg.close()
                    ui.notify(f"📂 загружен: {f.name}", color="positive")
                ui.button(label, on_click=_load).props("flat no-caps").style(
                    "width:100%; text-align:left; font-family:monospace; "
                    "font-size:0.78rem; color:rgba(255,255,255,0.75); "
                    "padding:8px 12px; border-radius:8px; "
                    "background:rgba(255,255,255,0.04); margin-bottom:4px;")
            ui.button("отмена", on_click=dlg.close).props("flat").style(
                "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")
        dlg.open()

    with ui.element("div").classes("app-container"):'''

CHAT_BUTTONS = '''                with ui.element("div").classes("floating-console"):
                    refs["input"] = ui.input(placeholder=f"скажи {name}...").props("borderless").style("flex:1")
                    refs["input"].on("keydown.enter", lambda e: asyncio.create_task(send()))  # DVIZHOK_V_KABINET_V1
                    # ZHITEL_CHAT_SAVE_V1
                    ui.button("💾", on_click=do_save_chat).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(201,168,76,0.9); background:rgba(201,168,76,0.10); "
                        "border:1px solid rgba(201,168,76,0.35);")
                    ui.button("📂", on_click=do_load_chat).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(0,204,255,0.9); background:rgba(0,204,255,0.10); "
                        "border:1px solid rgba(0,204,255,0.35);")
                    ui.button("ОТПРАВИТЬ", on_click=send).classes("send-button")'''

REPLACEMENTS = [
    (
        '_ROOT = Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: файл в жители/, корень репо — на уровень выше',
        CHAT_SAVE_FUNCS,
    ),
    (
        '        state["chat"].append({"role": "zhitel", "content": reply})\n'
        '        state["waiting"] = False\n'
        '        update_chat()\n'
        '\n'
        '    with ui.element("div").classes("app-container"):',
        DO_SAVE_LOAD_FUNCS,
    ),
    (
        '                with ui.element("div").classes("floating-console"):\n'
        '                    refs["input"] = ui.input(placeholder=f"скажи {name}...").props("borderless").style("flex:1")\n'
        '                    refs["input"].on("keydown.enter", lambda e: asyncio.create_task(send()))  # DVIZHOK_V_KABINET_V1\n'
        '                    ui.button("ОТПРАВИТЬ", on_click=send).classes("send-button")',
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak3")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()

# ZHITEL_CHAT_SAVE_V1 — маркер идемпотентности
