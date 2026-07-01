# patch_propiska_brat.py
"""
Камень второй: инструмент «Прописка» в Кабинете Брата.

Брат СВЯЗЫВАЕТ, не ДЕРЖИТ — прописка это связь между двумя единицами
(житель ↔ локация), значит это работа узла (Брата), не личный диалог
жителя с собой. Поэтому инструмент живёт в ui_brat.py, а не в ui_zhitel.py.

Что делает патч в Брат/ui_brat.py:
  1. Импорт list_zhiteli/find_dom (из ui_zhitel) и list_lokacii (из
     ui_lokacia) — с защитой на случай автономного запуска.
  2. propisat_zhitelya(zid, lid, домашний_промпт) — единственная точка
     записи: читает паспорт жителя по-настоящему свежим (find_dom, без
     кэша), пишет "прописка" и "домашний_промпт", сохраняет. Локация
     ничего не хранит (Закон Пары) — паспорт локации патч не трогает.
  3. Кнопка «Прописка» в хедере кабинета Брата, рядом со «Страница
     Жизни» — открывает диалог: житель → локация → домашний промпт
     (подсказка берётся из Unique_Mark/Hidden_History локации, Шеф
     может переписать) → «прописать».

Запуск из КОРНЯ репо:
    python patch_propiska_brat.py

Идемпотентен — если маркер PATCH_PROPISKA_BRAT уже стоит в файле,
скрипт не тронет его повторно.

Бэкап: Брат/ui_brat.py.bak_propiska_brat
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
TARGET = _ROOT / "Брат" / "ui_brat.py"
MARKER = "PATCH_PROPISKA_BRAT"


def main():
    if not TARGET.exists():
        print(f"✗ не найден: {TARGET}")
        print("  запускай из корня репо (там же, где main.py)")
        return

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"— уже применён ({MARKER} найден в {TARGET.name}) — пропускаю")
        return

    # ── 1. импорт list_zhiteli/find_dom/list_lokacii ──
    anchor_import = (
        'try:\n'
        '    from dotenv import load_dotenv\n'
        '    load_dotenv()\n'
        'except Exception:\n'
        '    pass\n'
        '\n'
        'OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")\n'
    )
    if anchor_import not in src:
        print("✗ не нашёл опорный блок (dotenv → OPENROUTER_KEY) — файл изменился, откатываю")
        return

    addition_import = (
        f'# {MARKER} — Брат связывает жителя и локацию (Брат СВЯЗЫВАЕТ, не\n'
        '# ДЕРЖИТ). Ничего не хранит сам — читает по требованию, пишет один раз,\n'
        '# в паспорт жителя. Локацию патч не трогает (Закон Пары).\n'
        '_REPO_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent\n'
        'try:\n'
        '    from ui_zhitel import list_zhiteli, find_dom\n'
        'except ImportError:\n'
        '    import sys as _sys\n'
        '    _zh_dir = str(_REPO_ROOT_FOR_IMPORT / "жители")\n'
        '    if _zh_dir not in _sys.path:\n'
        '        _sys.path.insert(0, _zh_dir)\n'
        '    from ui_zhitel import list_zhiteli, find_dom\n'
        'try:\n'
        '    from ui_lokacia import list_lokacii\n'
        'except ImportError:\n'
        '    import sys as _sys\n'
        '    _gor_dir = str(_REPO_ROOT_FOR_IMPORT / "ГОРОД")\n'
        '    if _gor_dir not in _sys.path:\n'
        '        _sys.path.insert(0, _gor_dir)\n'
        '    from ui_lokacia import list_lokacii\n'
        '\n'
        '\n'
        'def propisat_zhitelya(zid: str, lid: str, domashny_prompt: str):\n'
        '    """Пишет прописку в паспорт жителя. Единственная точка записи —\n'
        '    сама локация ничего не хранит (Закон Пары), только житель несёт\n'
        '    факт о доме в себе. Возвращает (успех: bool, сообщение: str)."""\n'
        '    p, dom = find_dom(zid)\n'
        '    if p is None or dom is None:\n'
        '        return False, "житель не найден"\n'
        '    passport_path = dom / "passport.json"\n'
        '    try:\n'
        '        import json\n'
        '        p["прописка"] = lid\n'
        '        p["домашний_промпт"] = domashny_prompt\n'
        '        passport_path.write_text(\n'
        '            json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")\n'
        '        return True, "прописан"\n'
        '    except Exception as e:\n'
        '        return False, str(e)\n'
        '\n'
        '\n'
    )
    src = src.replace(anchor_import, anchor_import + addition_import, 1)

    # ── 2. кнопка «Прописка» в хедере, рядом со «Страница Жизни» ──
    anchor_button = (
        '                ui.button("Страница Жизни",\n'
        '                          on_click=lambda: ui.navigate.to("/registry")  # PATCH_ROZH_BTN\n'
        '                          ).props("flat no-caps").style(\n'
        '                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "\n'
        '                    "background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08)); "\n'
        '                    "border:1px solid rgba(201,168,76,0.35); color:#fff;")\n'
        '                with ui.element("div").classes("brat-model-sel"):\n'
    )
    if anchor_button not in src:
        print("✗ не нашёл кнопку «Страница Жизни» в хедере — файл изменился, откатываю")
        return

    addition_button = (
        '                ui.button("Прописка",\n'
        f'                          on_click=do_propiska  # {MARKER}\n'
        '                          ).props("flat no-caps").style(\n'
        '                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "\n'
        '                    "background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08)); "\n'
        '                    "border:1px solid rgba(201,168,76,0.35); color:#fff;")\n'
    )
    new_button_block = addition_button + anchor_button
    src = src.replace(anchor_button, new_button_block, 1)

    # ── 3. do_propiska() — нужен определённым ДО хедера (замыкание в page_brat) ──
    anchor_send_end = (
        '        reply = await call_brat_llm(messages, state["model"])\n'
        '        state["chat"].append({"role": "assistant", "content": reply})\n'
        '        state["waiting"] = False\n'
        '        update_chat()\n'
        '\n'
        '    # ═══ LAYOUT — калька Биржи ═══\n'
    )
    if anchor_send_end not in src:
        print("✗ не нашёл конец send() перед LAYOUT — файл изменился, откатываю")
        return

    do_propiska_code = (
        '    async def do_propiska():\n'
        '        """Брат связывает жителя и локацию: диалог житель → локация →\n'
        '        домашний промпт → запись в паспорт жителя."""\n'
        '        zhiteli = list_zhiteli()\n'
        '        if not zhiteli:\n'
        '            ui.notify("Жителей ещё нет — роди их в Странице Жизни", color="warning")\n'
        '            return\n'
        '        lokacii = [l for l in list_lokacii() if l.get("ID_Object") != "0000_CITY_GRONDHEIM"]\n'
        '\n'
        '        pick = {"zhitel": None, "lokacia": None}\n'
        '\n'
        '        with ui.dialog() as dlg, ui.card().style(\n'
        '            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "\n'
        '            "border-radius:16px; min-width:380px; max-width:460px; padding:20px;"\n'
        '        ):\n'
        '            body = ui.element("div")\n'
        '\n'
        '            def render():\n'
        '                body.clear()\n'
        '                with body:\n'
        '                    if pick["zhitel"] is None:\n'
        '                        ui.html(\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n'
        '                                \'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">\'\n'
        '                                \'⌂ ПРОПИСКА · кого прописываем?</div>\')\n'
        '                        for z in zhiteli:\n'
        '                            nm = z.get("Official_Name", "?")\n'
        '                            cur = z.get("прописка")\n'
        '                            sub = f" · сейчас: {cur}" if cur else " · без прописки"\n'
        '                            def _pick_z(z=z):\n'
        '                                pick["zhitel"] = z\n'
        '                                render()\n'
        '                            ui.button(nm + sub, on_click=_pick_z).props("flat no-caps").style(\n'
        '                                "width:100%; text-align:left; font-family:monospace; "\n'
        '                                "font-size:0.78rem; color:rgba(255,255,255,0.75); "\n'
        '                                "padding:8px 12px; border-radius:8px; "\n'
        '                                "background:rgba(255,255,255,0.04); margin-bottom:4px;")\n'
        '                        ui.button("отмена", on_click=dlg.close).props("flat").style(\n'
        '                            "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")\n'
        '\n'
        '                    elif pick["lokacia"] is None:\n'
        '                        zn = pick["zhitel"].get("Official_Name", "?")\n'
        '                        ui.html(f\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n'
        '                                f\'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">\'\n'
        '                                f\'⌂ {zn} → куда?</div>\')\n'
        '                        if not lokacii:\n'
        '                            ui.html(\'<div style="color:rgba(255,255,255,0.4); font-size:0.8rem;">\'\n'
        '                                    \'— локаций ещё нет — роди их в Странице Жизни —</div>\')\n'
        '                        for loc in lokacii:\n'
        '                            nm = loc.get("Official_Name", "?")\n'
        '                            def _pick_l(loc=loc):\n'
        '                                pick["lokacia"] = loc\n'
        '                                render()\n'
        '                            ui.button(nm, on_click=_pick_l).props("flat no-caps").style(\n'
        '                                "width:100%; text-align:left; font-family:monospace; "\n'
        '                                "font-size:0.78rem; color:rgba(255,255,255,0.75); "\n'
        '                                "padding:8px 12px; border-radius:8px; "\n'
        '                                "background:rgba(255,255,255,0.04); margin-bottom:4px;")\n'
        '\n'
        '                        def _back_z():\n'
        '                            pick["zhitel"] = None\n'
        '                            render()\n'
        '                        ui.button("← назад", on_click=_back_z).props("flat").style(\n'
        '                            "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")\n'
        '\n'
        '                    else:\n'
        '                        zn = pick["zhitel"].get("Official_Name", "?")\n'
        '                        ln = pick["lokacia"].get("Official_Name", "?")\n'
        '                        suggestion = (pick["lokacia"].get("Unique_Mark")\n'
        '                                      or pick["lokacia"].get("Hidden_History") or "")\n'
        '                        ui.html(f\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n'
        '                                f\'font-size:0.9rem; margin-bottom:10px; letter-spacing:0.08em;">\'\n'
        '                                f\'⌂ {zn} → {ln}</div>\')\n'
        '                        ui.html(\'<div style="color:rgba(255,255,255,0.45); font-size:0.68rem; \'\n'
        '                                \'margin-bottom:6px; text-transform:uppercase; letter-spacing:0.06em;">\'\n'
        '                                \'домашний промпт — своё, личное</div>\')\n'
        '                        ta = ui.textarea(value=suggestion).props("dark outlined").style(\n'
        '                            "width:100%; font-size:0.8rem;")\n'
        '\n'
        '                        async def _confirm():\n'
        '                            ok, msg = propisat_zhitelya(\n'
        '                                pick["zhitel"].get("ID_Object", ""),\n'
        '                                pick["lokacia"].get("ID_Object", ""),\n'
        '                                (ta.value or "").strip(),\n'
        '                            )\n'
        '                            if ok:\n'
        '                                ui.notify(f"⌂ {zn} прописан(а): {ln}", color="positive")\n'
        '                                dlg.close()\n'
        '                            else:\n'
        '                                ui.notify(f"⚠ {msg}", color="negative")\n'
        '\n'
        '                        def _back_l():\n'
        '                            pick["lokacia"] = None\n'
        '                            render()\n'
        '\n'
        '                        with ui.row().style("gap:8px; margin-top:14px; width:100%;"):\n'
        '                            ui.button("← назад", on_click=_back_l).props("flat").style(\n'
        '                                "color:rgba(255,255,255,0.4); font-size:0.75rem;")\n'
        '                            ui.element("div").style("flex:1")\n'
        '                            ui.button("прописать", on_click=_confirm).props("flat no-caps").style(\n'
        '                                "padding:8px 20px; border-radius:8px; font-weight:700; font-size:0.8rem; "\n'
        '                                "background:linear-gradient(135deg,rgba(201,168,76,0.30),rgba(201,168,76,0.18)); "\n'
        '                                "border:1px solid rgba(201,168,76,0.55); color:#fff;")\n'
        '\n'
        '            render()\n'
        '        dlg.open()\n'
        '\n'
    )

    new_send_end = anchor_send_end.replace(
        '    # ═══ LAYOUT — калька Биржи ═══\n',
        do_propiska_code + '    # ═══ LAYOUT — калька Биржи ═══\n',
    )
    src = src.replace(anchor_send_end, new_send_end, 1)

    # ── бэкап + запись ──
    backup = TARGET.with_name(TARGET.name + ".bak_propiska_brat")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ патч применён: {TARGET}")
    print(f"✓ бэкап:         {backup}")
    print("— кнопка «Прописка» в хедере кабинета Брата, рядом со «Страница Жизни».")
    print("— проверь: python main.py → /brat → «Прописка»")


if __name__ == "__main__":
    main()
