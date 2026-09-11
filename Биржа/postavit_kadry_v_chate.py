# -*- coding: utf-8 -*-
# KADRY_V_CHATE_V1
"""
КАДРЫ — ПОД ЕГО ОТВЕТОМ, В ЧАТЕ

Слово Шефа 11.09: «он дёргает разные картинки, и я не пойму, что
конкретно он анализировал: начал читать одну, пока смотрел — ещё три
сменилось». Панель одна, а кадров за один вопрос несколько: с чем
разбудили, куда сходил рукой, куда вернулся. Она показывает
последний — и к моменту, когда Шеф дочитал ответ, она уже про
следующее место.

ЧТО ДЕЛАЕТ ПАТЧ. Каждый кадр, который трейдер видел за этот вопрос,
ложится ПОД его ответом в чате. Читаешь слова — рядом ровно те
картинки, про которые он говорит. Они уже никогда не разъедутся:
лежат вместе.

КАК СОБИРАЮТСЯ. Тем же крючком, что ловит живой кадр для панели, —
он видит каждую отрисовку. Теперь он не только кладёт последний на
площадь, но и копит все в список ответа. Кабинет забирает список,
чистит его и вешает на сообщение.

Панель при этом живёт как жила: она про «сейчас», чат — про «что
было». Больше они не спорят.

ПРАВИТ: мозги A06/A07/A08 (копилка) и Биржа/ui_torg.py (показ).

КУДА КЛАСТЬ ЭТОТ ФАЙЛ: в корень репы, рядом с main.py. Оттуда и
запускать.

БЕЗОПАСНОСТЬ: .bak_kadrychat, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_kadry_v_chate.py --suho
    python postavit_kadry_v_chate.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KADRY_V_CHATE_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
TORG = _REPO / "Биржа" / "ui_torg.py"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# ── мозг: копим кадры ответа ─────────────────────────────────
STAROE_MOZG = '''            _t["zhivoy_kadr"] = {'''
NOVOE_MOZG = '''            # KADRY_V_CHATE_V1: копим ВСЕ кадры этого ответа — не
            # только последний. Панель покажет последний, а чат —
            # все, под словами, про которые они и были.
            try:
                _spisok = list(_t.get("кадры_ответа") or [])
                if _p not in _spisok:
                    _spisok.append(_p)
                _t["кадры_ответа"] = _spisok[-12:]
            except Exception:
                pass
            _t["zhivoy_kadr"] = {'''

# ── кабинет: вешаем кадры на сообщение ───────────────────────
STAROE_TORG = '''                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()'''

NOVOE_TORG = '''                # KADRY_V_CHATE_V1: забираем всё, что он видел за этот
                # вопрос, и вешаем на сообщение. Список чистим, чтобы
                # следующему ответу достались только его кадры.
                _kadry_otveta = []
                try:
                    from hooks import (load_trading_state as _lts_k,
                                       save_trading_state as _sts_k)
                    _tk = _lts_k()
                    _kadry_otveta = list(_tk.get("кадры_ответа") or [])
                    if _kadry_otveta:
                        _tk["кадры_ответа"] = []
                        _sts_k(_tk)
                except Exception as _e_k:
                    print(f"[ЧАТ] кадры ответа не забрались ({_e_k})")
                if _kadr and str(_kadr) not in _kadry_otveta:
                    _kadry_otveta.insert(0, str(_kadr))

                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)",
                    "кадры": _kadry_otveta})
                update_chat_display()'''

# ── кабинет: рисуем их в ленте ───────────────────────────────
STAROE_RIS = '''                    else:
                        ui.html(f'<div class="chat-msg-assistant"><b>{who}:</b> {content}</div>')'''

NOVOE_RIS = '''                    else:
                        ui.html(f'<div class="chat-msg-assistant"><b>{who}:</b> {content}</div>')
                        # KADRY_V_CHATE_V1: под ответом — то, что он
                        # видел. Панель одна и всегда про «сейчас»;
                        # здесь картинки лежат рядом со словами и
                        # больше не разъезжаются.
                        _kadry = msg.get("кадры") or []
                        if _kadry:
                            with ui.row().style(
                                "gap:6px; flex-wrap:wrap; "
                                "margin:2px 0 10px 10px;"
                            ):
                                for _i_k, _pk in enumerate(_kadry, 1):
                                    try:
                                        if not Path(_pk).exists():
                                            continue
                                        with ui.element("div").style(
                                            "display:flex; "
                                            "flex-direction:column; "
                                            "align-items:center;"
                                        ):
                                            ui.image(str(_pk)).style(
                                                "width:210px; "
                                                "border-radius:6px; "
                                                "border:1px solid "
                                                "rgba(255,255,255,0.10); "
                                                "cursor:pointer;").on(
                                                "click",
                                                lambda _=None, p=_pk:
                                                    _kadr_krupno(p))
                                            ui.label(f"кадр {_i_k}").style(
                                                "color:rgba(255,255,255,0.35);"
                                                "font-size:10px;")
                                    except Exception:
                                        continue

    def _kadr_krupno(put: str):
        """Клик по кадру в ленте — показать во весь экран."""
        try:
            with ui.dialog() as _d, ui.card().style(
                "background:#0d1117; padding:10px; max-width:96vw;"
            ):
                ui.image(str(put)).style("max-width:92vw; max-height:86vh;")
                ui.button("закрыть", on_click=_d.close).props(
                    "flat no-caps dense").style(
                    "color:rgba(255,255,255,0.5); font-size:0.75rem;")
            _d.open()
        except Exception as _e:
            print(f"[ЧАТ] кадр не открылся крупно ({_e})")'''


def _pravka_mozga(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0
    if txt.count(STAROE_MOZG) != 1:
        print(f"  {slot}: ОТКАЗ — крючок живого кадра не нашёлся "
              f"({txt.count(STAROE_MOZG)} совпадений)")
        return 0
    novy = txt.replace(STAROE_MOZG, NOVOE_MOZG, 1)
    novy = novy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_kadrychat"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("КАДРЫ В ЧАТЕ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    print("1. МОЗГИ — копят кадры ответа:")
    vsego = 0
    if not SLOTY.exists():
        print("  слотов нет — запускать из корня репы")
    else:
        for s in ("A06", "A07", "A08"):
            vsego += _pravka_mozga(s)

    print()
    print("2. КАБИНЕТ — показывает их под ответом:")
    if not TORG.exists():
        print("  ui_torg.py: файла нет")
    else:
        txt = TORG.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  ui_torg.py: уже стоит")
        else:
            novy, ok = txt, True
            for imya, st, nv in (("сбор кадров", STAROE_TORG, NOVOE_TORG),
                                 ("показ в ленте", STAROE_RIS, NOVOE_RIS)):
                if novy.count(st) != 1:
                    print(f"  ui_torg.py: ОТКАЗ на «{imya}» — "
                          f"{novy.count(st)} совпадений")
                    ok = False
                    break
                novy = novy.replace(st, nv, 1)
            if ok:
                try:
                    ast.parse(novy)
                    if not SUHO:
                        shutil.copy2(TORG,
                                     TORG.with_suffix(".py.bak_kadrychat"))
                        TORG.write_text(novy, encoding="utf-8")
                    print(f"  ui_torg.py: {'готов' if SUHO else 'поправлен'}")
                    vsego += 1
                except SyntaxError as e:
                    print(f"  ui_torg.py: ОТКАЗ — синтаксис сломан ({e})")

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_kadrychat")
    print("Слова и картинки теперь лежат вместе. Клик — во весь экран.")
    print()


if __name__ == "__main__":
    main()
