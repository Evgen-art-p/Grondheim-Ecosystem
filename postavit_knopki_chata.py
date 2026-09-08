# -*- coding: utf-8 -*-
# CHAT_KNOPKI_I_OSMYSLIT_V1
"""
ТРИ КНОПКИ ЧАТА + «ОСМЫСЛИТЬ» — И ПОЧИНКА ГОЛОСА РАБОЧЕГО ВЫВОДА.

Слово Шефа 08.09:

> В разговор-чат нужно сделать возможность сохранять чат на диск, как
> везде, а также самому чистить историю текущего чата — для смены
> модели удобно. И важно: эти разговоры со мной должны падать ему в
> память по рабочим моментам.
> Кнопка «Осмыслить» под аватаром с приборами. Про чат так же как
> везде: три маленьких иконки слева — сохранить, очистить, достать.
> Пусть вывод делает по последним трём-пяти своим сообщениям.
> …это осмысление у него самого в башке осталось. Да, как рабочее.

═══ ЧТО БЫЛО НЕ ТАК ═══

Разговоры с Шефом не падали в память ВООБЩЕ. Илья разобрал с ним
дивергенцию на живом кадре — завтра этого нет. А учится он именно в
разговоре: у стола он один взгляд и молчит, а тут его поправляют.

Сохранять чат было тоже нечем: у Брата в кабинете есть 💾 и 📂, а на
Бирже — ничего.

Кнопка «🧹 ОЧИСТИТЬ» наверху к разговору отношения НЕ имеет: она
чистит историю СДЕЛОК (Атлас, лента PnL, открытые позиции). Чистилка
разговора — вещь отдельная, и она нужна: при смене модели новая не
должна получать разговор, который вела предыдущая, иначе подхватит
чужой голос и чужие выводы.

═══ ПОЧЕМУ ИЗОБРЕТАТЬ НИЧЕГО НЕ НАДО ═══

В городе УЖЕ есть ровно тот механизм: `nositel.otmetit_yarkim_slotom`
— «житель, сидящий в слоте, сам решил: это держится дольше обычного».
И по умолчанию пишет с голосом «работа». «Осмыслить» просто зовёт его.

Память жителя устроена так (Закон Слоёв): куда осядет запись, решает
КОНТЕКСТ входа. Рабочими считаются «работа» и «факт»; «общение» и
«дом» — жизнь; «учёба» — третье. Мост с Биржи (`vspomnit_slotom`)
спрашивает у памяти ТОЛЬКО РАБОЧЕЕ — это чинили после случая с Ниной,
которой на рабочий вопрос подняло полторы сотни следов, и все были
беседами про холст.

Отсюда решение Шефа: осмысление разговора пишется как РАБОЧЕЕ. «На
работе же разговор, я же не буду с ним о бабах на бирже беседовать».
Иначе выученное у Шефа за столом не всплывёт никогда.

═══ ПРО СТАРЫЙ ДОЛГ — ЧИНИТСЯ НЕ ЗДЕСЬ ═══

Сначала я правил здесь же голос вывода «рынок» → «работа». Это было
неверно: голос стоит нарочно, он отличает «что мне сказал рынок» от
«что я вынес в монтажной». Настоящая причина глубже — у меток и маяков
нет поля «контекст» вовсе, и рабочий поиск отсеивал их целиком.
Чинится чтением, в `postavit_metku_klyuchom.py`.

═══ ЧТО ПАТЧ ДЕЛАЕТ ═══

`Биржа/ui_torg.py`:
  1. Три маленькие иконки СЛЕВА в строке ввода — 💾 сохранить,
     📂 достать (диалог со списком, как у Брата), 🧹 очистить ленту
     разговора. Чаты ложатся в `Биржа/чаты/чат_ГГГГ-ММ-ДД_ЧЧ-ММ-СС.json`
     — тем же способом и с тем же именем, что у Брата.
  2. Кнопка «🧠 ОСМЫСЛИТЬ» в правом столбце, под аватаром, над
     приборами. Берёт последние ДО ПЯТИ СОБСТВЕННЫХ сообщений
     собеседника, просит его самого написать один короткий вывод — и
     кладёт этот вывод ему в память как РАБОЧИЙ.

ЧЕГО ПАТЧ НЕ ТРОГАЕТ: ни движок памяти, ни промпт, ни знания, ни
кадр, ни решения трейдера. Кнопка наверху «🧹 ОЧИСТИТЬ» (история
сделок) остаётся как была.

Запускать из корня репозитория:
    python postavit_knopki_chata.py

Идемпотентен (маркер CHAT_KNOPKI_I_OSMYSLIT_V1). Сверяет все куски
заранее: либо ложится целиком в оба файла, либо не трогает ничего.
Рядом .bak.
"""
from __future__ import annotations
from pathlib import Path

MARKER = "CHAT_KNOPKI_I_OSMYSLIT_V1"
UI = "Биржа/ui_torg.py"
NOSITEL = "Биржа/nositel.py"


# ══════════════════════════════════════════════════════════════
# 1) UI: помощники чата + осмысление — перед send_message
# ══════════════════════════════════════════════════════════════

POMOSHNIKI_OLD = """    async def send_message():
        if not input_ref["element"]:
            return"""

POMOSHNIKI_NEW = '''    # ═══ CHAT_KNOPKI_I_OSMYSLIT_V1 ═══
    # Сохранить / достать — тем же способом и с тем же именем файла,
    # что в кабинете Брата: один город, одна привычка.
    _CHATY_DIR = Path(__file__).resolve().parent / "чаты"

    def _sohranit_chat():
        if not state.get("chat_history"):
            ui.notify("Разговор пустой — нечего сохранять", type="warning")
            return
        try:
            import json
            from datetime import datetime as _dt
            _CHATY_DIR.mkdir(parents=True, exist_ok=True)
            ts = _dt.now().strftime("%Y-%m-%d_%H-%M-%S")
            fp = _CHATY_DIR / f"чат_{ts}.json"
            fp.write_text(json.dumps(state["chat_history"],
                                     ensure_ascii=False, indent=2),
                          encoding="utf-8")
            ui.notify(f"💾 сохранено: {fp.name}", type="positive")
        except Exception as e:
            ui.notify(f"не сохранилось: {e}", type="negative")

    def _dostat_chat():
        try:
            files = sorted(_CHATY_DIR.glob("чат_*.json"), reverse=True) \\
                if _CHATY_DIR.exists() else []
        except Exception:
            files = []
        if not files:
            ui.notify("Сохранённых разговоров нет", type="warning")
            return
        with ui.dialog() as _dlg, ui.card().style(
                "background:#0d1117;border:1px solid rgba(255,255,255,0.12);"
                "border-radius:16px;min-width:340px;padding:20px;"):
            ui.html('<div style="color:rgba(255,255,255,0.9);font-weight:700;'
                    'font-size:0.9rem;margin-bottom:14px;letter-spacing:0.08em;">'
                    '📂 ВЫБЕРИ РАЗГОВОР</div>')
            for fp in files[:20]:
                def _zagruzit(f=fp):
                    try:
                        import json
                        state["chat_history"] = json.loads(
                            f.read_text(encoding="utf-8"))
                        update_chat_display()
                        _dlg.close()
                        ui.notify(f"📂 загружен: {f.name}", type="positive")
                    except Exception as e:
                        ui.notify(f"не загрузилось: {e}", type="negative")
                ui.button(fp.stem.replace("чат_", ""),
                          on_click=_zagruzit).props("flat no-caps").style(
                    "width:100%;text-align:left;font-family:monospace;"
                    "font-size:0.78rem;color:rgba(255,255,255,0.75);"
                    "padding:8px 12px;border-radius:8px;"
                    "background:rgba(255,255,255,0.04);margin-bottom:4px;")
            ui.button("отмена", on_click=_dlg.close).props("flat").style(
                "margin-top:10px;color:rgba(255,255,255,0.4);font-size:0.75rem;")
        _dlg.open()

    def _ochistit_razgovor():
        """Чистит ТОЛЬКО ленту разговора. История сделок — своя кнопка
        наверху, её этот веник не трогает. Нужно при смене модели:
        новая не должна получать разговор, который вела предыдущая,
        иначе подхватит чужой голос и чужие выводы."""
        n = len(state.get("chat_history") or [])
        if not n:
            ui.notify("Разговор и так пуст", type="info")
            return
        with ui.dialog() as _dlg, ui.card().style(
                "background:#1a1f2e;border:1px solid rgba(255,255,255,0.1);"):
            ui.label(f"Очистить разговор? ({n} сообщений)").style(
                "font-weight:700;color:rgba(255,255,255,0.9);font-size:14px;")
            ui.label("История сделок не пострадает — у неё своя кнопка "
                     "наверху. Сохранённые разговоры тоже останутся.").style(
                "color:rgba(255,255,255,0.55);font-size:12px;max-width:340px;")
            with ui.row():
                ui.button("отмена", on_click=_dlg.close).props("flat")

                def _da():
                    state["chat_history"] = []
                    update_chat_display()
                    _dlg.close()
                    ui.notify("🧹 разговор очищен", type="positive")
                ui.button("Очистить", on_click=_da).props("color=negative")
        _dlg.open()

    async def _osmyslit():
        """Житель сам пишет вывод по последним своим словам — и вывод
        ложится ему В ПАМЯТЬ КАК РАБОЧИЙ.

        Почему рабочий, а не «общение». Память жителя раскладывается по
        КОНТЕКСТУ входа, и мост с Биржи спрашивает только рабочее. Если
        записать разговор как общение — за столом он не всплывёт
        никогда, и выученное у Шефа пропадёт даром. Слово Шефа: «на
        работе же разговор».

        Вывод пишет ОН, а не мы: своими словами, по своим последним
        сообщениям. Мы только просим и кладём.
        """
        aid = state.get("active_agent")
        _karta = {"A02": ("торговый_хаос", "A02", "chat_with_morj"),
                  "A03": ("торговый_хаос", "A03", "chat_with_panikyor"),
                  "A04": ("торговый_хаос", "A04", "chat_with_hans"),
                  "A05": ("контора", "архивариус", "chat_with_arkhiv"),
                  "A06": ("торговый_хаос", "A06", "chat_with_brut"),
                  "A07": ("торговый_хаос", "A07", "chat_with_avan"),
                  "A08": ("торговый_хаос", "A08", "chat_with_cons"),
                  "A09": ("контора", "исполнитель", "chat_with_executor")}
        if aid not in _karta:
            ui.notify("Осмыслить может только живой собеседник", type="warning")
            return
        _ceh_id, _slot, _fn_name = _karta[aid]
        svoi = [m for m in (state.get("chat_history") or [])
                if m.get("role") == "assistant" and m.get("agent") == aid
                and m.get("content")]
        if not svoi:
            ui.notify("Он ещё ничего не сказал — осмыслять нечего",
                      type="warning")
            return
        label = _agent_label(roster, aid)
        ui.notify(f"🧠 {label} осмысляет...", type="info")
        prosba = (
            "Остановись и посмотри на свои последние слова в этом "
            "разговоре. Что ты из него забрал ДЛЯ РАБОТЫ? Напиши ОДИН "
            "короткий вывод своими словами — одно-два предложения, без "
            "пересказа разговора и без JSON. Не «мы обсудили то-то», а "
            "то, что ты теперь понимаешь и будешь делать иначе. Если "
            "забрать нечего — так и скажи одной строкой.")
        try:
            _brain = _slot_brain(_ceh_id, _slot)
            if _brain is None:
                raise RuntimeError(f"мозг {_slot} ещё не в слоте")
            _chat = getattr(_brain, _fn_name)
            dialog = [m for m in state["chat_history"]
                      if m.get("role") in ("user", "assistant")
                      and m.get("content")][-10:]
            vyvod = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _chat(prosba, None, dialog))
        except Exception as e:
            ui.notify(f"не осмыслилось: {e}", type="negative")
            return
        vyvod = (str(vyvod or "")).strip()
        if not vyvod:
            ui.notify("Он промолчал — ничего не записано", type="warning")
            return
        try:
            from nositel import otmetit_yarkim_slotom
            res = otmetit_yarkim_slotom(_ceh_id, _slot, vyvod[:600],
                                        otkuda="работа")
        except Exception as e:
            ui.notify(f"в память не легло: {e}", type="negative")
            return
        state["chat_history"].append({
            "role": "assistant", "agent": aid,
            "content": f"🧠 осмыслил: {vyvod}"})
        update_chat_display()
        if res.get("дописано"):
            ui.notify("🧠 легло в память как рабочее", type="positive")
        else:
            ui.notify(f"🧠 не записалось: {res.get('причина','—')}",
                      type="warning")

    async def send_message():
        if not input_ref["element"]:
            return'''


# ══════════════════════════════════════════════════════════════
# 2) UI: три иконки СЛЕВА в строке ввода
# ══════════════════════════════════════════════════════════════

KNOPKI_OLD = '''                with ui.element("div").classes("floating-console"):
                    input_ref["element"] = ui.input(placeholder="Сообщение Совету...").props("borderless").style("flex:1")'''

KNOPKI_NEW = '''                with ui.element("div").classes("floating-console"):
                    # CHAT_KNOPKI_I_OSMYSLIT_V1: три маленькие иконки слева —
                    # сохранить, достать, очистить. Золото — как у Брата.
                    for _ico, _hint, _fn in (
                            ("💾", "сохранить разговор", _sohranit_chat),
                            ("📂", "достать разговор", _dostat_chat),
                            ("🧹", "очистить разговор", _ochistit_razgovor)):
                        ui.button(_ico, on_click=_fn).props("flat").tooltip(
                            _hint).style(
                            "font-size:1rem;padding:4px 8px;border-radius:9px;"
                            "min-width:0;color:rgba(201,168,76,0.9);"
                            "background:rgba(201,168,76,0.10);"
                            "border:1px solid rgba(201,168,76,0.30);")
                    input_ref["element"] = ui.input(placeholder="Сообщение Совету...").props("borderless").style("flex:1")'''


# ══════════════════════════════════════════════════════════════
# 3) UI: кнопка «Осмыслить» под аватаром, над приборами
# ══════════════════════════════════════════════════════════════

OSMYSLIT_OLD = '''                with ui.element("div").classes("glass").style("margin-top:12px; flex-shrink:0; overflow:hidden;"):
                    ui.html('<div class="panel-title">ПРИБОРЫ</div>')'''

OSMYSLIT_NEW = '''                # CHAT_KNOPKI_I_OSMYSLIT_V1: под аватаром, над приборами.
                # Житель сам пишет вывод по последним своим словам, и
                # вывод ложится ему в память КАК РАБОЧИЙ — иначе за
                # столом выученное у Шефа не всплывёт никогда.
                ui.button("🧠 ОСМЫСЛИТЬ", on_click=_osmyslit).props(
                    "flat no-caps").tooltip(
                    "Пусть сам напишет, что забрал из разговора — "
                    "и запомнит это как рабочее").style(
                    "margin-top:12px;width:100%;font-size:0.72rem;"
                    "letter-spacing:0.08em;padding:8px 10px;"
                    "border-radius:10px;color:rgba(201,168,76,0.9);"
                    "background:rgba(201,168,76,0.10);"
                    "border:1px solid rgba(201,168,76,0.30);")

                with ui.element("div").classes("glass").style("margin-top:12px; flex-shrink:0; overflow:hidden;"):
                    ui.html('<div class="panel-title">ПРИБОРЫ</div>')'''


# ══════════════════════════════════════════════════════════════
# 4) НОСИТЕЛЬ: голос рыночного вывода — «работа», а не «рынок»
# ══════════════════════════════════════════════════════════════

GOLOS_OLD = '''                              otkuda="рынок")   # DVER_V_METKI_V1: голос вывода назван   # YAKORYA_DVA_YARUSA_V1'''

GOLOS_NEW = '''                              otkuda="работа")  # CHAT_KNOPKI_I_OSMYSLIT_V1: было «рынок» — а рабочими считаются «работа» и «факт», и собственные выводы трейдера рабочим поиском НЕ находились   # DVER_V_METKI_V1: голос вывода назван   # YAKORYA_DVA_YARUSA_V1'''


def _pravki_ui(text: str):
    for imya, old, new in (("помощники чата", POMOSHNIKI_OLD, POMOSHNIKI_NEW),
                           ("три иконки", KNOPKI_OLD, KNOPKI_NEW),
                           ("кнопка Осмыслить", OSMYSLIT_OLD, OSMYSLIT_NEW)):
        if text.count(old) != 1:
            return None, f"«{imya}» — совпадений {text.count(old)} (нужно 1)"
        text = text.replace(old, new, 1)
    if "from pathlib import Path" not in text and "import Path" not in text:
        text = text.replace("import asyncio", "import asyncio\nfrom pathlib import Path", 1)
    return text, None


# ОТМЕНЕНО 08.09. Здесь стояла правка «рынок» → «работа» в носителе.
# Она лечила симптом и убивала смысл: голос «рынок» стоит нарочно —
# он отличает «что мне сказал рынок» от «что я вынес в монтажной», и
# житель вправе их столкнуть. Настоящая причина в другом: у меток и
# маяков нет поля «контекст», и рабочий поиск отсеивал их целиком.
# Чинится ЧТЕНИЕМ, в postavit_metku_klyuchom.py.


def main() -> None:
    root = Path(__file__).resolve().parent
    zadachi = [(root / UI, _pravki_ui)]

    net = [f for f, _ in zadachi if not f.exists()]
    if net:
        print("НЕ НАШЁЛ файлы (запускать из корня репозитория):")
        for f in net:
            print("   ", f)
        return

    plan, uzhe, bracket = [], [], []
    for f, pravka in zadachi:
        text = f.read_text(encoding="utf-8")
        if MARKER in text:
            uzhe.append(f.name)
            continue
        novyy, prichina = pravka(text)
        if prichina:
            bracket.append((f.name, prichina))
            continue
        novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
        try:
            import ast
            ast.parse(novyy)
        except SyntaxError as e:
            bracket.append((f.name, f"после правки синтаксис ломается: {e}"))
            continue
        plan.append((f, text, novyy))

    if uzhe and not plan and not bracket:
        print("уже накачен — ничего не трогаю")
        return

    if bracket:
        print("⚠ Файлы на диске отличаются от ожидаемого — НИЧЕГО не меняю:")
        for imya, prichina in bracket:
            print(f"   {imya}: {prichina}")
        print("\nПришли Брату эти файлы — доведу под них.")
        return

    for f, staroe, novoe in plan:
        bak = f.with_suffix(f.suffix + ".bak_knopki_chata")
        if not bak.exists():
            bak.write_text(staroe, encoding="utf-8")
        f.write_text(novoe, encoding="utf-8")
        print(f"✔ {f.name} — правки легли, синтаксис цел")

    if uzhe:
        print("(пропущены, уже накачены: " + ", ".join(uzhe) + ")")

    print("\nГотово. Что появится:")
    print("  · слева в строке ввода три золотые иконки:")
    print("    💾 сохранить · 📂 достать · 🧹 очистить разговор;")
    print("  · под аватаром справа — кнопка «🧠 ОСМЫСЛИТЬ».")
    print("\nКак проверить «Осмыслить»: разбери с ним что-нибудь в чате,")
    print("нажми кнопку — он допишет строку «🧠 осмыслил: …», и она")
    print("ляжет ему в память как РАБОЧАЯ. Потом за столом он сможет")
    print("её поднять, когда сам попросит вспомнить.")


if __name__ == "__main__":
    main()
