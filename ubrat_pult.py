# -*- coding: utf-8 -*-
"""
ubrat_pult.py · MARKER: ODNA_KNOPKA_V1

ЗАЧЕМ
─────
Слово Шефа: «жмёшь… прыгаешь… этаж в пузырёк… ключ пробуждения…
сноси такой тестер, я не маг-колдун и такие заклинания не буду
делать».

Справедливо. Я навесил пульт: ⏮ ◀◀ ◀ ▶ ▶▶ ⏭, потом 🔍 ⟨ ⟩ 3/12 — и
чтобы прогнать историю, надо было помнить порядок нажатий. Это моя
ошибка: я сделал плеер вместо работы.

КАК СТАЛО
─────────
Кнопок больше нет. Одна кнопка РЫНОК, и она уже умеет разводить сама:

    режим РЕАЛ   → живой Совет, как сейчас
    режим ТЕСТЕР → прогон по истории

Прогон делает всё сам:

    1. берёт трейдеров, у кого есть пара (инструмент и этаж);
    2. по каждому пробегает историю кодом и находит места,
       где стоит взглянуть — бесплатно, это математика;
    3. встаёт в каждое место по очереди, от старых к свежим;
    4. зовёт ТОГО трейдера, чьё это место, и пишет в ленту, что он
       сказал;
    5. дошёл до конца или ты нажал СТОП — снимает курсор и всё.

Сколько мест обойти — поле «ловить», оно уже есть рядом. СТОП уже
есть. Ничего нового нажимать не надо.

ЧТО УБРАНО
──────────
Из кабинета убраны обе мои панели — шаги по барам и прыжки по
кандидатам. Сам механизм (курсор истории, искатель) остался: им
теперь пользуется прогон, а не ты руками.

Листалка `listat.py` в корне остаётся — если захочешь пройти кусок
истории глазами сам, без трейдеров. Но для работы она не нужна.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py ubrat_pult.py   (или --suho)
"""
import ast
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "ODNA_KNOPKA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ui_torg.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


# ── новый прогон, кладём рядом с market_dispatch ──
PROGON = '''    async def progon_po_istorii():
        """ODNA_KNOPKA_V1: весь тестер в одной кнопке.

        Раньше здесь был пульт из стрелок, а до него — tester_express
        на упразднённой Искре. Теперь: код ищет места, город встаёт в
        каждое, трейдер говорит. Шеф только читает ленту.
        """
        if state.get("tester_running"):
            ui.notify("Прогон уже идёт", type="warning")
            return
        try:
            import istoriya
            import kandidaty as _kd
            import vybor
        except Exception as e:
            ui.notify(f"Прогон недоступен: {e}", type="negative")
            return

        # кто может работать: у кого есть и инструмент, и этаж
        rabotniki = []
        for _sl in ("A06", "A07", "A08"):
            r = vybor.rabota_dlya(tseh_id, _sl)
            if r.get("готов"):
                rabotniki.append((_sl, r["инструмент"], r["этаж"]))
            else:
                print(f"[ПРОГОН] {_sl} не участвует: "
                      f"{vybor.pochemu_molchit(tseh_id, _sl)}")
        if not rabotniki:
            ui.notify("Некому работать: ни у кого нет инструмента и этажа",
                      type="warning")
            return

        skolko = int(state.get("bars_to_live") or 1)
        state["tester_running"] = True
        state["stop_requested"] = False
        _bylo_moment = ""
        try:
            _bylo_moment = istoriya.gde_stoim()
        except Exception:
            pass

        state["chat_history"].append({
            "role": "system",
            "content": (f"▶ ПРОГОН ПО ИСТОРИИ · {len(rabotniki)} "
                        f"трейдер(ов) · ищу до {skolko} мест каждому")})
        update_chat_display()
        ui.notify("🔍 ищу места в истории…", type="info")

        import asyncio
        loop = asyncio.get_event_loop()

        # 1. код ищет места — бесплатно, поэтому ищем сразу всем
        mesta = []
        for _sl, _sym, _tf in rabotniki:
            try:
                spisok = await loop.run_in_executor(
                    None, lambda s=_sym, t=_tf: _kd.iskat(
                        s, t, skolko=skolko, govorit=print))
            except Exception as e:
                print(f"[ПРОГОН] {_sl}: искать не вышло — {e}")
                continue
            for k in spisok:
                mesta.append((k.get("момент") or k.get("дата", ""),
                              _sl, _sym, _tf, k))

        if not mesta:
            state["tester_running"] = False
            state["chat_history"].append({
                "role": "system",
                "content": "Ничего не нашлось в истории — пусто."})
            update_chat_display()
            ui.notify("Мест не нашлось", type="warning")
            return

        # от старых к свежим — как шло время
        mesta.sort(key=lambda x: x[0])
        state["chat_history"].append({
            "role": "system",
            "content": f"Нашёл {len(mesta)} мест. Иду по ним."})
        update_chat_display()

        # 2. по каждому месту: встать туда и спросить того, чьё оно
        proydeno = 0
        try:
            for data, _sl, _sym, _tf, k in mesta:
                if state.get("stop_requested"):
                    state["chat_history"].append({
                        "role": "system", "content": "⏸ остановлено"})
                    update_chat_display()
                    break
                istoriya.postavit(data)
                try:
                    pokazat_kadr()
                except Exception:
                    pass
                imya = _agent_label(roster, _sl) or _sl
                state["chat_history"].append({
                    "role": "system",
                    "content": f"📍 {_kd.slovami(k)} → спрашиваю {imya}"})
                update_chat_display()

                def _zvat():
                    import council
                    return council.wake_council("", "", ceh_id=tseh_id)

                try:
                    itog = await loop.run_in_executor(None, _zvat)
                except Exception as e:
                    print(f"[ПРОГОН] Совет сорвался на {data}: {e}")
                    continue
                proydeno += 1

                r = (itog.get("results") or {}).get(_sl) or {}
                skazal = (r.get("narrative") or "").strip()
                if not skazal and r.get("error"):
                    skazal = f"(промолчал: {r['error']})"
                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()
        finally:
            state["tester_running"] = False
            state["stop_requested"] = False
            try:
                istoriya.postavit(_bylo_moment)
            except Exception:
                pass

        state["chat_history"].append({
            "role": "system",
            "content": f"✓ прогон окончен · пройдено мест: {proydeno}"})
        update_chat_display()
        ui.notify(f"✓ прогон окончен · {proydeno} мест", type="positive")

'''

ST_DISPATCH = '''    async def market_dispatch():
        if state.get("mode") == "tester":
            await run_tester_session()
        else:
            await run_market()'''

NOV_DISPATCH = PROGON + '''    async def market_dispatch():
        # ODNA_KNOPKA_V1: одна кнопка РЫНОК. В реале — живой Совет,
        # в тестере — прогон по истории. Старый run_tester_session
        # оставлен в файле нетронутым: он держится на упразднённой
        # Искре и не заводится, но выкидывать чужой труд не мне.
        if state.get("mode") == "tester":
            await progon_po_istorii()
        else:
            await run_market()'''


def _vyrezat_blok(t: str, nachalo: str, konec: str, imya: str):
    """Вырезать кусок от строки-начала до строки-конца (не включая)."""
    i = t.find(nachalo)
    if i < 0:
        return t, f"{imya}: не нашёл начало"
    j = t.find(konec, i)
    if j < 0:
        return t, f"{imya}: не нашёл конец"
    return t[:i] + t[j:], ""


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ui_torg = koren / "Биржа" / "ui_torg.py"
    t = ui_torg.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if "VREMYA_V_KABINETE_V1" not in t or "ISKATEL_V1" not in t:
        print("✗ В кабинете нет панелей, которые надо снести —")
        print("  видимо, патчи времени/искателя не накачены.")
        return 1

    besporyadok = []

    # 1. вырезаем кнопки искателя (от 🔍 до метки momenta)
    t, beda = _vyrezat_blok(
        t,
        '                            # ISKATEL_V1: прыжки по местам, а не по барам',
        '                            toolbar_refs["moment_label"] = ui.label(',
        "кнопки искателя")
    if beda:
        besporyadok.append(beda)

    # 2. вырезаем всю панель времени целиком
    t, beda = _vyrezat_blok(
        t,
        '                        # VREMYA_V_KABINETE_V1: шаг по истории. Видно',
        '                        toolbar_refs["bars_label"] = ui.element("div")',
        "панель времени")
    if beda:
        besporyadok.append(beda)

    if besporyadok:
        print("✗ " + "; ".join(besporyadok))
        print("  Кабинет правили — ничего не трогаю.")
        return 1

    # 3. прогон вместо мёртвого тестера
    if t.count(ST_DISPATCH) != 1:
        print(f"✗ развилка РЫНОК/ТЕСТЕР найдена {t.count(ST_DISPATCH)} раз")
        return 1
    t = t.replace(ST_DISPATCH, NOV_DISPATCH, 1)

    # 4. ссылки на снесённые кнопки — чтобы не искали пустоту
    t = t.replace('"learn_btn", "vremya_panel"):   # TORG_LEARN_SWITCH_V1',
                  '"learn_btn"):   # TORG_LEARN_SWITCH_V1')

    t += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = ui_torg.with_suffix(
        f".py.bak_pult_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(ui_torg, bak)
    ui_torg.write_text(t, encoding="utf-8")
    print(f"✓ пульт снесён (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(ui_torg), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    ostalos = len(re.findall(r"⏮|◀◀|▶▶|⏭|kand_label", t))
    print(f"  кнопок пульта осталось в файле: {ostalos} (должно быть 0)")

    print("\nТеперь так:")
    print("  ТЕСТЕР → в поле «ловить» число мест → РЫНОК.")
    print("  Дальше он сам: найдёт места, встанет в каждое,")
    print("  спросит того трейдера, чьё это место, и напишет в ленту.")
    print("  Надоело — СТОП.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
