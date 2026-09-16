# -*- coding: utf-8 -*-
# POSTAVIT_PODPIS_OKOSHKOM_V1
"""
ПАТЧ: подпись — отдельным окошком, панель загрузчика как была.

Запускать из КОРНЯ РЕПО:
    python postavit_podpis_okoshkom.py

ЧТО СЛОМАЛ Я
    Поставил в панель загрузчика три поля насовсем — источник, подпись,
    тема. Панель фиксированной высоты, ниже неё блок уроков. Поля
    заняли место, и кнопку «📖 Прочитать» утащило ВНИЗ, под соседний
    блок. Резать список было бесполезно: место съели поля.

ЧТО ДЕЛАЕТ
    Поля из панели убирает. Вместо них — «✎ ПОДПИСЬ» рядом с CLEAR:
    жмёшь, открывается окошко с теми же тремя полями, вписал, закрыл.
    Окошко всплывает поверх и места в панели не занимает.

    Подпись запоминается между загрузками — вписал «вильямс» один раз
    и кладёшь хоть всю главу. Что сейчас стоит, видно прямо в панели
    одной серой строкой; ничего не вписано — так и написано.

    Ничего не отнято: подписывает по-прежнему только Шеф, машина за
    него не сочиняет.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_podpis_okoshkom, ast.parse перед записью.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# PODPIS_OKOSHKOM_V1"


def _nayti():
    kand = [p for p in _KOREN.rglob("ui_akademia.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл ui_akademia.py. Запускай из корня репозитория.")
        return None
    if len(kand) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kand, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            return kand[int(input("Который? номер: ").strip()) - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kand[0]


# ── поля вон из панели, вместо них кнопка и строка состояния ──
STARO_1 = '''                        ui.button("CLEAR", on_click=clear_ruda).props("flat dense size=xs").style(
                            "color:rgba(255,80,80,0.5); font-size:9px;")
                    # SKLAD_V_ZAGRUZCHIKE_V1: подпись ставит ТОЛЬКО Шеф.
                    # Источник -- короткое имя, из него собирается ключ
                    # («вильямс» + «gl07_str11» = вильямс/gl07_str11).
                    ui.html('<div style="padding:4px 16px 2px 16px;color:rgba(255,255,255,0.35);'
                            'font-size:9px;line-height:1.5;">подпишу сам — '
                            'машина за меня не сочиняет</div>')

                    def _pole(imya_polya, podskazka):
                        def _menyat(e, k=imya_polya):
                            state[k] = e.value or ""
                        return ui.input(placeholder=podskazka,
                                        on_change=_menyat).props(
                            "dense borderless dark").style(
                            "margin:2px 12px; width:calc(100% - 24px); "
                            "font-size:11px; color:rgba(255,255,255,0.85); "
                            "background:rgba(255,255,255,0.05); "
                            "border:1px solid rgba(255,255,255,0.10); "
                            "border-radius:8px; padding:1px 8px;")

                    _pole("источник", "источник: вильямс, котин, скрин…")
                    _pole("подпись", "подпись: что тут нарисовано")
                    _pole("тема", "тема: трейдинг, психология…")'''

NOVO_1 = '''                        # PODPIS_OKOSHKOM_V1: поля ушли в окошко.
                        # Панель фиксированной высоты, ниже неё блок
                        # уроков — три поля утаскивали «Прочитать» вниз,
                        # под соседний блок.
                        ui.button("✎ ПОДПИСЬ", on_click=lambda: _okno_podpisi()) \\
                            .props("flat dense size=xs").style(
                            "color:rgba(0,204,255,0.75); font-size:9px;")
                        ui.button("CLEAR", on_click=clear_ruda).props("flat dense size=xs").style(
                            "color:rgba(255,80,80,0.5); font-size:9px;")

                    # SKLAD_V_ZAGRUZCHIKE_V1: подпись ставит ТОЛЬКО Шеф,
                    # машина за него не сочиняет.
                    # PODPIS_OKOSHKOM_V1: что сейчас стоит — одной строкой.
                    podpis_ref["строка"] = ui.html("")

                    def _pokazat_podpis():
                        _i = (state.get("источник") or "").strip()
                        _p = (state.get("подпись") or "").strip()
                        _t = (state.get("тема") or "").strip()
                        if _i or _p or _t:
                            _kuski = [x for x in (_i, _p, _t) if x]
                            _txt = ("✎ " + " · ".join(_kuski))
                            _cv = "rgba(0,255,136,0.60)"
                        else:
                            _txt = "без подписи — ищется только по источнику"
                            _cv = "rgba(255,255,255,0.30)"
                        podpis_ref["строка"].set_content(
                            f'<div style="padding:3px 16px 4px 16px;color:{_cv};'
                            f'font-size:9px;line-height:1.4;word-break:break-word;">'
                            f'{_txt}</div>')

                    def _okno_podpisi():
                        dlg = ui.dialog()
                        with dlg, ui.card().style(
                                "background:#0e1420; min-width:360px; "
                                "border:1px solid rgba(255,255,255,0.12);"):
                            ui.html('<div style="color:#8adfff;font-size:12px;'
                                    'letter-spacing:.12em;padding-bottom:2px;">'
                                    '✎ ПОДПИСЬ</div>')
                            ui.html('<div style="color:rgba(255,255,255,0.40);'
                                    'font-size:10px;line-height:1.5;'
                                    'padding-bottom:8px;">Подписываю сам — '
                                    'машина за меня не сочиняет.<br>Источник '
                                    'коротко: из него собирается ключ '
                                    '(«вильямс» → вильямс/gl07_str11).<br>'
                                    'Держится до смены — клади хоть всю '
                                    'главу.</div>')

                            def _pole(imya_polya, podskazka):
                                def _menyat(e, k=imya_polya):
                                    state[k] = e.value or ""
                                    _pokazat_podpis()
                                return ui.input(
                                    placeholder=podskazka,
                                    value=state.get(imya_polya) or "",
                                    on_change=_menyat).props(
                                    "dense borderless dark").style(
                                    "width:100%; font-size:12px; "
                                    "color:rgba(255,255,255,0.88); "
                                    "background:rgba(255,255,255,0.05); "
                                    "border:1px solid rgba(255,255,255,0.10); "
                                    "border-radius:8px; padding:2px 10px; "
                                    "margin-bottom:6px;")

                            _pole("источник", "источник: вильямс, котин, скрин…")
                            _pole("подпись", "подпись: что тут нарисовано")
                            _pole("тема", "тема: трейдинг, психология…")

                            def _steret():
                                state["источник"] = ""
                                state["подпись"] = ""
                                state["тема"] = ""
                                _pokazat_podpis()
                                dlg.close()
                                ui.notify("Подпись снята", color="info")

                            with ui.row().style("gap:8px; margin-top:4px;"):
                                ui.button("Готово", on_click=dlg.close).props(
                                    "flat").style("color:#8adfff;")
                                ui.button("Стереть", on_click=_steret).props(
                                    "flat").style("color:rgba(255,80,80,0.6);")
                        dlg.open()

                    _pokazat_podpis()'''


# ── подставка под ссылку на строку состояния ────────────────
STARO_2 = '''        "руда": [],
        "источник": "", "подпись": "", "тема": "",'''

NOVO_2 = '''        "руда": [],
        "источник": "", "подпись": "", "тема": "",
        # PODPIS_OKOSHKOM_V1: сюда кладём строку состояния подписи
        "_подпись_строка": None,'''


STARO_3 = '''    ruda_ref   = {"element": None, "uploader": None}'''
NOVO_3 = '''    ruda_ref   = {"element": None, "uploader": None}
    podpis_ref = {"строка": None}   # PODPIS_OKOSHKOM_V1'''


ZAMENY = [
    ("поля в окошко", STARO_1, NOVO_1),
    ("состояние", STARO_2, NOVO_2),
    ("подставка", STARO_3, NOVO_3),
]


def main():
    print("=" * 58)
    print("ПОДПИСЬ — ОКОШКОМ")
    print("=" * 58)

    fajl = _nayti()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return

    print("\n--- ЗАМЕНЫ ---")
    ne = []
    for imya, staro, _n in ZAMENY:
        c = tekst.count(staro)
        print(f"  {'✓' if c == 1 else '⚠ ' + str(c)}  {imya}")
        if c != 1:
            ne.append(imya)
    if ne:
        print(f"\n⚠ не сошлось: {', '.join(ne)} — ничего не тронул.")
        return

    novyy = tekst
    for _i, staro, novo in ZAMENY:
        novyy = novyy.replace(staro, novo, 1)
    novyy = novyy.rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_podpis_okoshkom")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город:")
    print("  В шапке загрузчика рядом с CLEAR — ✎ ПОДПИСЬ.")
    print("  Под шапкой одной серой строкой видно, что сейчас стоит.")
    print("  Кнопка «📖 Прочитать» должна вернуться на место.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_PODPIS_OKOSHKOM_V1 - marker
