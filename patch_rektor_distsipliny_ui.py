# PATCH_REKTOR_DISTSIPLINY_UI_V1
"""
PATCH_REKTOR_DISTSIPLINY_UI_V1 -- тулбар Ректора переведён на модель
Дисциплин вместо свободного текста «предмет».

БЫЛО: поле «предмет» текстом (можно было вписать что угодно, даже
несуществующее), одна общая «оценка» без разделения теория/практика.
Функции для дисциплин (zapisat_na_distsiplinu, postavit_otsenku_
distsipliny) уже были в rektor.py, но кнопок под них не было — отсюда
и то, что Нина не помнила, что учится: записи на дисциплину просто
никогда не происходило, метку писать было не о чем.

СТАЛО:
  1. «📚 Записать» -- выпадающий список направлений (живой, с диска) +
     выпадающий список дисциплин внутри направления (обновляется при
     смене направления) + кнопка. Зовёт zapisat_na_distsiplinu() --
     эта функция УЖЕ пишет отпечаток в личную память кандидата(ки)
     ("Начал(а) изучать «X»") -- теперь наконец есть от кого его ждать.
  2. «📋 Оценить» -- выпадающий список ЕЁ СОБСТВЕННЫХ дисциплин (только
     те, на которые уже записана) + переключатель теория/практика +
     поле оценки + кнопка. Зовёт postavit_otsenku_distsipliny() --
     тоже уже писала отпечаток, тоже была без кнопки.
  3. Отчёты (viewer) показывают дисциплины и оценки по каждой части
     отдельно, не только старые оценки/экзамены (те тоже оставлены --
     ничего не удаляем без причины).

Старый postavit_otsenku()/deystvie_otsenka() в rektor.py/ui_rektor.py
НЕ удаляются -- просто больше не вызываются из тулбара. Работающее
не трогаем без причины.

Требует: PATCH_REKTOR_DISTSIPLINY_V1 в rektor.py уже применён (даёт
list_napravlenia/list_distsipliny/zapisat_na_distsiplinu/
postavit_otsenku_distsipliny).

Идемпотентно: если маркер PATCH_REKTOR_DISTSIPLINY_UI_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_rektor_distsipliny_ui.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_rektor.py')
MARKER = 'PATCH_REKTOR_DISTSIPLINY_UI_V1'

OLD_UPDATE_VIEWER_BODY = '''            zap = _rek.najti_zapis(kandidat_imya)
            md = ""
            if zap:
                md += f"**Место:** {zap.get('место','—')} · **Курс:** {zap.get('курс') or '—'}\\n\\n"
                otsenki = zap.get("оценки", [])
                md += "**Оценки:** " + (", ".join(
                    f"{o['предмет']}: {o['оценка']}" for o in otsenki) or "нет") + "\\n\\n"
                ekz = zap.get("экзамены", [])
                md += "**Экзамены:** " + (", ".join(
                    f"{e['предмет']}: {e['результат']}" for e in ekz) or "нет") + "\\n\\n"
                dip = zap.get("диплом")
                md += f"**Диплом:** {dip['профессия'] if dip else 'не выдан'}\\n"
            else:
                md += "*Пока не студент(ка) — кандидат(ка) на собеседовании.*\\n"'''

NEW_UPDATE_VIEWER_BODY = '''            zap = _rek.najti_zapis(kandidat_imya)
            md = ""
            if zap:
                md += f"**Место:** {zap.get('место','—')} · **Курс:** {zap.get('курс') or '—'}\\n\\n"
                # PATCH_REKTOR_DISTSIPLINY_UI_V1: дисциплины и оценки по
                # частям -- рядом со старыми полями, не вместо них.
                distsipliny = zap.get("дисциплины", []) or []
                if distsipliny:
                    md += "**Дисциплины:**\\n"
                    for d in distsipliny:
                        t_oc = (d.get("теория", {}) or {}).get("оценки", []) or []
                        p_oc = (d.get("практика", {}) or {}).get("оценки", []) or []
                        t_posl = t_oc[-1]["оценка"] if t_oc else "—"
                        p_posl = p_oc[-1]["оценка"] if p_oc else "—"
                        md += (f"- **{d.get('дисциплина')}** ({d.get('направление','')}) "
                              f"— теория: {t_posl} · практика: {p_posl}\\n")
                    md += "\\n"
                else:
                    md += "**Дисциплины:** пока не записан(а) ни на одну\\n\\n"
                otsenki = zap.get("оценки", [])
                md += "**Оценки (старые):** " + (", ".join(
                    f"{o['предмет']}: {o['оценка']}" for o in otsenki) or "нет") + "\\n\\n"
                ekz = zap.get("экзамены", [])
                md += "**Экзамены:** " + (", ".join(
                    f"{e['предмет']}: {e['результат']}" for e in ekz) or "нет") + "\\n\\n"
                dip = zap.get("диплом")
                md += f"**Диплом:** {dip['профессия'] if dip else 'не выдан'}\\n"
            else:
                md += "*Пока не студент(ка) — кандидат(ка) на собеседовании.*\\n"'''

OLD_REFS_AND_DEYSTVIE = '''    oc_predmet_ref = {"el": None}
    oc_otsenka_ref = {"el": None}

    def deystvie_otsenka():
        if not kandidat_imya:
            ui.notify("Нет кандидата", type="warning")
            return
        predmet = (oc_predmet_ref["el"].value or "").strip() if oc_predmet_ref["el"] else ""
        otsenka = (oc_otsenka_ref["el"].value or "").strip() if oc_otsenka_ref["el"] else ""
        if not predmet or not otsenka:
            ui.notify("Укажи предмет и оценку", type="warning")
            return
        ok, msg = _rek.postavit_otsenku(kandidat_imya, predmet, otsenka)
        ui.notify(msg, type="positive" if ok else "warning")
        update_viewer()
        update_kand_caption()'''

NEW_REFS_AND_DEYSTVIE = '''    # PATCH_REKTOR_DISTSIPLINY_UI_V1: тулбар работает с настоящими
    # дисциплинами (диск), не со свободным текстом.
    oc_otsenka_ref = {"el": None}          # текст оценки — общий для обеих кнопок
    zapis_napr_ref = {"value": (_rek.list_napravlenia() or [""])[0]}
    zapis_dist_container = {"element": None}
    zapis_dist_ref = {"el": None}
    otsenka_dist_container = {"element": None}
    otsenka_dist_ref = {"el": None}
    otsenka_chast_ref = {"el": None}

    def render_zapis_dist_select():
        if not zapis_dist_container["element"]:
            return
        zapis_dist_container["element"].clear()
        with zapis_dist_container["element"]:
            opts = {d.get("id", d.get("название", "?")): d.get("название", d.get("id", "?"))
                    for d in _rek.list_distsipliny(zapis_napr_ref["value"])}
            if not opts:
                ui.label("(дисциплин нет)").style(
                    "font-size:10px; color:rgba(255,255,255,0.4); padding:6px;")
                zapis_dist_ref["el"] = None
            else:
                zapis_dist_ref["el"] = ui.select(opts, value=next(iter(opts))).props(
                    "dense outlined dark").style("width:150px; font-size:11px;")

    def on_zapis_napr_change(e):
        zapis_napr_ref["value"] = e.value
        render_zapis_dist_select()

    def render_otsenka_dist_select():
        if not otsenka_dist_container["element"]:
            return
        otsenka_dist_container["element"].clear()
        with otsenka_dist_container["element"]:
            zap = _rek.najti_zapis(kandidat_imya) if kandidat_imya else None
            moi = (zap or {}).get("дисциплины", []) or []
            if not moi:
                ui.label("(не записан(а) ни на одну)").style(
                    "font-size:10px; color:rgba(255,255,255,0.4); padding:6px;")
                otsenka_dist_ref["el"] = None
            else:
                opts = {d["дисциплина"]: d["дисциплина"] for d in moi}
                otsenka_dist_ref["el"] = ui.select(opts, value=next(iter(opts))).props(
                    "dense outlined dark").style("width:150px; font-size:11px;")

    def deystvie_zapisat_distsiplinu():
        if not kandidat_imya:
            ui.notify("Нет кандидата", type="warning")
            return
        if not zapis_dist_ref["el"]:
            ui.notify("В этом направлении нет дисциплин", type="warning")
            return
        did = zapis_dist_ref["el"].value
        ok, msg = _rek.zapisat_na_distsiplinu(kandidat_imya, did, zapis_napr_ref["value"])
        ui.notify(msg, type="positive" if ok else "warning")
        update_viewer()
        update_kand_caption()
        render_otsenka_dist_select()

    def deystvie_otsenka_distsipliny():
        if not kandidat_imya:
            ui.notify("Нет кандидата", type="warning")
            return
        if not otsenka_dist_ref["el"]:
            ui.notify("Сначала запиши на дисциплину", type="warning")
            return
        did = otsenka_dist_ref["el"].value
        chast = otsenka_chast_ref["el"].value if otsenka_chast_ref["el"] else "теория"
        otsenka = (oc_otsenka_ref["el"].value or "").strip() if oc_otsenka_ref["el"] else ""
        if not otsenka:
            ui.notify("Укажи оценку", type="warning")
            return
        ok, msg = _rek.postavit_otsenku_distsipliny(kandidat_imya, did, chast, otsenka)
        ui.notify(msg, type="positive" if ok else "warning")
        update_viewer()
        update_kand_caption()'''

OLD_TOOLBAR_ROW = '''                    with ui.row().style("gap:6px; flex-wrap:wrap;"):
                        _bz = ui.element("div").classes("rekt-btn")
                        _bz.on("click", lambda: deystvie_zachislit())
                        with _bz:
                            ui.html("🎓 Зачислить")
                        oc_predmet_ref["el"] = ui.input(placeholder="предмет").props(
                            "dense outlined dark").style("width:100px; font-size:11px;")
                        oc_otsenka_ref["el"] = ui.input(placeholder="оценка").props(
                            "dense outlined dark").style("width:80px; font-size:11px;")
                        _bo = ui.element("div").classes("rekt-btn")
                        _bo.on("click", lambda: deystvie_otsenka())
                        with _bo:
                            ui.html("📋 Оценка")
                        dip_prof_ref["el"] = ui.input(placeholder="профессия").props(
                            "dense outlined dark").style("width:110px; font-size:11px;")
                        _bd = ui.element("div").classes("rekt-btn")
                        _bd.on("click", lambda: deystvie_diplom())
                        with _bd:
                            ui.html("🏅 Диплом")'''

NEW_TOOLBAR_ROW = '''                    with ui.row().style("gap:6px; flex-wrap:wrap; align-items:center;"):
                        _bz = ui.element("div").classes("rekt-btn")
                        _bz.on("click", lambda: deystvie_zachislit())
                        with _bz:
                            ui.html("🎓 Зачислить")

                    # PATCH_REKTOR_DISTSIPLINY_UI_V1: запись на дисциплину
                    with ui.row().style("gap:6px; flex-wrap:wrap; align-items:center; "
                                        "padding:4px 0; border-top:1px solid rgba(255,255,255,0.06);"):
                        ui.label("📚 Записать:").style(
                            "font-size:10px; color:rgba(255,255,255,0.5);")
                        _napr_opts = {n: n for n in (_rek.list_napravlenia() or [])}
                        ui.select(_napr_opts, value=zapis_napr_ref["value"],
                                 on_change=on_zapis_napr_change).props(
                            "dense outlined dark").style("width:140px; font-size:11px;")
                        zapis_dist_container["element"] = ui.element("div")
                        render_zapis_dist_select()
                        _bzap = ui.element("div").classes("rekt-btn")
                        _bzap.on("click", lambda: deystvie_zapisat_distsiplinu())
                        with _bzap:
                            ui.html("➕ Записать")

                    # PATCH_REKTOR_DISTSIPLINY_UI_V1: оценка теории/практики
                    with ui.row().style("gap:6px; flex-wrap:wrap; align-items:center; "
                                        "padding:4px 0; border-top:1px solid rgba(255,255,255,0.06);"):
                        ui.label("📋 Оценить:").style(
                            "font-size:10px; color:rgba(255,255,255,0.5);")
                        otsenka_dist_container["element"] = ui.element("div")
                        render_otsenka_dist_select()
                        otsenka_chast_ref["el"] = ui.select(
                            {"теория": "теория", "практика": "практика"}, value="теория"
                        ).props("dense outlined dark").style("width:100px; font-size:11px;")
                        oc_otsenka_ref["el"] = ui.input(placeholder="оценка").props(
                            "dense outlined dark").style("width:80px; font-size:11px;")
                        _bo = ui.element("div").classes("rekt-btn")
                        _bo.on("click", lambda: deystvie_otsenka_distsipliny())
                        with _bo:
                            ui.html("✓ Оценить")

                    with ui.row().style("gap:6px; flex-wrap:wrap; align-items:center;"):
                        dip_prof_ref["el"] = ui.input(placeholder="профессия").props(
                            "dense outlined dark").style("width:110px; font-size:11px;")
                        _bd = ui.element("div").classes("rekt-btn")
                        _bd.on("click", lambda: deystvie_diplom())
                        with _bd:
                            ui.html("🏅 Диплом")'''

REPLACEMENTS = [
    (OLD_UPDATE_VIEWER_BODY, NEW_UPDATE_VIEWER_BODY),
    (OLD_REFS_AND_DEYSTVIE, NEW_REFS_AND_DEYSTVIE),
    (OLD_TOOLBAR_ROW, NEW_TOOLBAR_ROW),
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_distsipliny_ui")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
