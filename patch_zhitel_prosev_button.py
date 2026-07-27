# PROSEV_ZHIZNENNYI_V1
"""
PROSEV_ZHIZNENNYI_V1 -- просев личного (Чертёж §10 «НЕТ СОВСЕМ»):
кнопка «🪞 Осмыслить» в кабинете жителя. Труба: топ личных моментов
по искре (sobrat_dlya_proseva, уже в новом dvizhok.py) -> LLM
осмысляет, что это говорит о жителе -> dopisat_vyvod() (уже
существовавший код, звать -- не строить).

Требует: жители/dvizhok.py уже заменён на версию с PAMYAT_ISKRA_V1 /
PROSEV_ZHIZNENNYI_V1 (sobrat_dlya_proseva, тонус/сила в _zapisat_sobytie).
Этот патч трогает ТОЛЬКО жители/ui_zhitel.py.

Идемпотентно: если маркер PROSEV_ZHIZNENNYI_V1 уже стоит в файле --
патч молча выходит, повторно не наложится. Бэкап .bak делается один
раз, при первом применении.

Запуск из корня репо:  python patch_zhitel_prosev_button.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('жители/ui_zhitel.py')
MARKER = 'PROSEV_ZHIZNENNYI_V1'

DO_PROSEV_FUNC = '''
    async def do_prosev():
        """PROSEV_ZHIZNENNYI_V1: житель осмысляет накопленные личные
        моменты (НЕ рабочую память -- Стол Трейдера этого не касается,
        разделение Шефа 27.07) и дописывает вывод о себе. Труба: топ
        моментов по искре (sobrat_dlya_proseva) -> LLM осмысляет ->
        dopisat_vyvod() (уже работает -- не строили заново, только позвали)."""
        if state.get("waiting"):
            return
        if dom is None or not (dom / "passport.json").exists():
            ui.notify("дом не найден — осмыслять нечего", color="warning")
            return
        try:
            _dv = Dvizhok(dom)
        except Exception as ex:
            ui.notify(f"⚠ движок не дышит: {ex}", color="negative")
            return
        momenty = _dv.sobrat_dlya_proseva(limit=8)
        if len(momenty) < 3:
            ui.notify("пока накопилось мало — рано осмыслять", color="warning")
            return
        state["waiting"] = True
        ui.notify(f"🪞 {name} осмысляет {len(momenty)} момент(ов)", color="info")
        spisok = "\\n".join(f"— [{m['тонус']}] {m['факт']}" for m in momenty)
        dusha = _dusha_chtenia(p)
        prompt = (
            f"Вот моменты из твоей жизни за последнее время, которые тебя "
            f"тронули (тепло или царапнуло):\\n{spisok}\\n\\n"
            f"Что это говорит о тебе? Чем ты стала (стал) немного другой? "
            f"Ответь от первого лица, 1–3 коротких фразы — вывод о себе, "
            f"не пересказ моментов. Не выдумывай лишнего сверх того, что видно. "
            f"Без строк MEMORY_REQUEST."
        )
        messages = [
            {"role": "system", "content": dusha},
            {"role": "user", "content": prompt},
        ]
        vyvod = await call_zhitel_llm(messages, state.get("model"))
        state["waiting"] = False
        if not vyvod or vyvod.startswith("⚠"):
            ui.notify(f"⚠ просев не удался: {(vyvod or '')[:90]}", color="negative")
            return
        vyvod = _ubrat_memory_request(vyvod) or vyvod.strip()
        res = _dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
        try:
            _dv.sохранить()
        except Exception:
            pass
        if res.get("дописано"):
            state["chat"].append({"role": "zhitel", "content": f"🪞 {vyvod.strip()}"})
            ui.notify("✦ вывод дописан в метки", color="positive")
        else:
            ui.notify(f"— {res.get('причина', 'уже было')}", color="info")
        update_chat()

    async def send():'''

PROSEV_BUTTON = '''                    ui.button("📖 Прочитать", on_click=do_chtenie).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:rgba(201,168,76,0.15) !important; "
                        "border:1px solid rgba(201,168,76,0.45) !important; color:#e8c96a !important;")
                    # PROSEV_ZHIZNENNYI_V1
                    ui.button("🪞 Осмыслить", on_click=do_prosev).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:rgba(160,160,220,0.12) !important; "
                        "border:1px solid rgba(160,160,220,0.35) !important; color:#c8c8ec !important;")'''

REPLACEMENTS = [
    (
        '        state["waiting"] = False\n'
        '        update_files()\n'
        '        update_chat()\n'
        '\n'
        '    async def send():',
        DO_PROSEV_FUNC,
    ),
    (
        '                    ui.button("📖 Прочитать", on_click=do_chtenie).props("flat no-caps").style(\n'
        '                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "\n'
        '                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "\n'
        '                        "background:rgba(201,168,76,0.15) !important; "\n'
        '                        "border:1px solid rgba(201,168,76,0.45) !important; color:#e8c96a !important;")',
        PROSEV_BUTTON,
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak2")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()

# PROSEV_ZHIZNENNYI_V1 — маркер идемпотентности
