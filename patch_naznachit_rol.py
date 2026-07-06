# patch_naznachit_rol.py
"""
Хвост №2 (Чертёж Единицы, §9, найден 06.07): прописка сейчас
одевает только АДРЕС (propisat_zhitelya → "прописка" + "домашний_промпт"),
но не одевает РОЛЬ. Маска «работа» (маски/работа/mask.json) остаётся
"_активна": false навсегда, поле "тип" (резидент/хранитель/воркер,
обязательный общий ключ паспорта — Гл.7.3) не пишется нигде.

Житель рождается «голышом» — это ЗАКОННО (Гл.1.5.2: тип живёт в Роли,
Роль — не при рождении). Но должен быть ВТОРОЙ акт, что его одевает.
Этот патч — тот акт.

Что делает патч в Брат/ui_brat.py:
  1. naznachit_rol(zid, tip, workshop_id, turbo_role, core_phrase) —
     пишет "тип" в passport.json (top-level, рядом с "порода" —
     тот же обязательный ключ границы, Гл.7.3), АКТИВИРУЕТ маску
     «работа» (mask.json: Workshop_ID/Turbo_Role/Core_Phrase,
     "_активна": True). Роль и адрес — разные акты, эта функция
     прописку (локацию) не трогает.
  2. Кнопка «Роль» в хедере кабинета Брата, рядом с «Прописка» —
     диалог: житель → тип (резидент/хранитель/воркер) → цех + слот +
     коронная фраза → «назначить».

Требует: patch_propiska_brat.py уже применён (использует его кнопку
«Прописка» как якорь и его импорт list_zhiteli/find_dom).

Запуск из КОРНЯ репо:
    python patch_naznachit_rol.py

Идемпотентен — если маркер PATCH_NAZNACHIT_ROL уже стоит в файле,
скрипт не тронет его повторно.

Бэкап: Брат/ui_brat.py.bak_naznachit_rol
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
TARGET = _ROOT / "Брат" / "ui_brat.py"
MARKER = "PATCH_NAZNACHIT_ROL"
REQUIRED_MARKER = "PATCH_PROPISKA_BRAT"


def main():
    if not TARGET.exists():
        print(f"✗ не найден: {TARGET}")
        print("  запускай из корня репо (там же, где main.py)")
        return

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"— уже применён ({MARKER} найден в {TARGET.name}) — пропускаю")
        return

    if REQUIRED_MARKER not in src:
        print(f"✗ {REQUIRED_MARKER} не найден — сначала накати patch_propiska_brat.py")
        return

    # ── 1. naznachit_rol() — сразу после propisat_zhitelya() ──
    anchor_func = (
        '        passport_path.write_text(\n'
        '            json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")\n'
        '        return True, "прописан"\n'
        '    except Exception as e:\n'
        '        return False, str(e)\n'
        '\n'
        '\n'
    )
    if anchor_func not in src:
        print("✗ не нашёл конец propisat_zhitelya() — файл изменился, откатываю")
        return

    addition_func = (
        f'# {MARKER} — Брат надевает РОЛЬ жителю (тип + маска «работа»).\n'
        '# Роль и адрес (Прописка) — разные акты (Чертёж §1.5.2). Тип живёт\n'
        '# рядом с породой в паспорте — тот же обязательный ключ границы\n'
        '# (Гл.7.3: «тройка ID+имя+тип»).\n'
        'def naznachit_rol(zid: str, tip: str, workshop_id: str,\n'
        '                  turbo_role: str, core_phrase: str):\n'
        '    """Пишет тип в passport.json, активирует маску «работа»\n'
        '    (mask.json: Workshop_ID/Turbo_Role/Core_Phrase, "_активна": True).\n'
        '    Прописку (локацию) не трогает. Возвращает (успех: bool, сообщение: str)."""\n'
        '    p, dom = find_dom(zid)\n'
        '    if p is None or dom is None:\n'
        '        return False, "житель не найден"\n'
        '    try:\n'
        '        import json\n'
        '        passport_path = dom / "passport.json"\n'
        '        p["тип"] = tip\n'
        '        passport_path.write_text(\n'
        '            json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")\n'
        '\n'
        '        mask_path = dom / "маски" / "работа" / "mask.json"\n'
        '        mask_path.parent.mkdir(parents=True, exist_ok=True)\n'
        '        mask = {}\n'
        '        if mask_path.exists():\n'
        '            try:\n'
        '                mask = json.loads(mask_path.read_text(encoding="utf-8"))\n'
        '            except Exception:\n'
        '                mask = {}\n'
        '        mask["_note"] = ("маска \'работа\' (слой 2 паспорта). "\n'
        '                         "Активирована Братом при назначении роли.")\n'
        '        mask["_активна"] = True\n'
        '        mask["Workshop_ID"] = workshop_id\n'
        '        mask["Turbo_Role"] = turbo_role\n'
        '        mask["Core_Phrase"] = core_phrase\n'
        '        mask_path.write_text(\n'
        '            json.dumps(mask, ensure_ascii=False, indent=2), encoding="utf-8")\n'
        '        return True, "роль назначена"\n'
        '    except Exception as e:\n'
        '        return False, str(e)\n'
        '\n'
        '\n'
    )
    src = src.replace(anchor_func, anchor_func + addition_func, 1)

    # ── 2. кнопка «Роль» — сразу после кнопки «Прописка» ──
    anchor_button = (
        '                ui.button("Прописка",\n'
        '                          on_click=do_propiska  # PATCH_PROPISKA_BRAT\n'
        '                          ).props("flat no-caps").style(\n'
        '                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "\n'
        '                    "background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08)); "\n'
        '                    "border:1px solid rgba(201,168,76,0.35); color:#fff;")\n'
    )
    if anchor_button not in src:
        print("✗ не нашёл кнопку «Прописка» — файл изменился, откатываю")
        return

    addition_button = (
        '                ui.button("Роль",\n'
        f'                          on_click=do_naznachit_rol  # {MARKER}\n'
        '                          ).props("flat no-caps").style(\n'
        '                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "\n'
        '                    "background:linear-gradient(135deg,rgba(120,168,201,0.15),rgba(120,168,201,0.08)); "\n'
        '                    "border:1px solid rgba(120,168,201,0.35); color:#fff;")\n'
    )
    src = src.replace(anchor_button, anchor_button + addition_button, 1)

    # ── 3. do_naznachit_rol() — сразу перед do_propiska() ──
    anchor_do = '    async def do_propiska():\n'
    if anchor_do not in src:
        print("✗ не нашёл do_propiska() — файл изменился, откатываю")
        return

    do_rol_code = (
        '    async def do_naznachit_rol():\n'
        '        """Брат надевает роль жителю: житель → тип → цех+слот+фраза →\n'
        '        назначить. Активирует маску «работа», не трогает прописку."""\n'
        '        zhiteli = list_zhiteli()\n'
        '        if not zhiteli:\n'
        '            ui.notify("Жителей ещё нет — роди их в Странице Жизни", color="warning")\n'
        '            return\n'
        '\n'
        '        TIPY = ["резидент", "хранитель", "воркер"]\n'
        '        pick = {"zhitel": None, "tip": None}\n'
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
        '                                \'⚙ РОЛЬ · кому назначаем?</div>\')\n'
        '                        for z in zhiteli:\n'
        '                            nm = z.get("Official_Name", "?")\n'
        '                            cur_tip = z.get("тип")\n'
        '                            sub = f" · сейчас: {cur_tip}" if cur_tip else " · без роли"\n'
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
        '                    elif pick["tip"] is None:\n'
        '                        zn = pick["zhitel"].get("Official_Name", "?")\n'
        '                        ui.html(f\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n'
        '                                f\'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">\'\n'
        '                                f\'⚙ {zn} → какой тип?</div>\')\n'
        '                        for t in TIPY:\n'
        '                            def _pick_t(t=t):\n'
        '                                pick["tip"] = t\n'
        '                                render()\n'
        '                            ui.button(t, on_click=_pick_t).props("flat no-caps").style(\n'
        '                                "width:100%; text-align:left; font-family:monospace; "\n'
        '                                "font-size:0.78rem; color:rgba(255,255,255,0.75); "\n'
        '                                "padding:8px 12px; border-radius:8px; "\n'
        '                                "background:rgba(255,255,255,0.04); margin-bottom:4px;")\n'
        '                        def _back_z():\n'
        '                            pick["zhitel"] = None\n'
        '                            render()\n'
        '                        ui.button("← назад", on_click=_back_z).props("flat").style(\n'
        '                            "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")\n'
        '\n'
        '                    else:\n'
        '                        zn = pick["zhitel"].get("Official_Name", "?")\n'
        '                        ui.html(f\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n'
        '                                f\'font-size:0.9rem; margin-bottom:10px; letter-spacing:0.08em;">\'\n'
        '                                f\'⚙ {zn} · {pick["tip"]}</div>\')\n'
        '                        ws = ui.input("Цех (Workshop_ID)").props("dark outlined").style(\n'
        '                            "width:100%; font-size:0.8rem; margin-bottom:8px;")\n'
        '                        role = ui.input("Слот роли (Turbo_Role)").props("dark outlined").style(\n'
        '                            "width:100%; font-size:0.8rem; margin-bottom:8px;")\n'
        '                        phrase = ui.input("Коронная фраза (Core_Phrase)").props(\n'
        '                            "dark outlined").style("width:100%; font-size:0.8rem;")\n'
        '\n'
        '                        async def _confirm():\n'
        '                            ok, msg = naznachit_rol(\n'
        '                                pick["zhitel"].get("ID_Object", ""),\n'
        '                                pick["tip"],\n'
        '                                (ws.value or "").strip(),\n'
        '                                (role.value or "").strip(),\n'
        '                                (phrase.value or "").strip(),\n'
        '                            )\n'
        '                            if ok:\n'
        '                                ui.notify(f"⚙ {zn}: роль назначена ({pick[\'tip\']})", color="positive")\n'
        '                                dlg.close()\n'
        '                            else:\n'
        '                                ui.notify(f"⚠ {msg}", color="negative")\n'
        '\n'
        '                        def _back_t():\n'
        '                            pick["tip"] = None\n'
        '                            render()\n'
        '\n'
        '                        with ui.row().style("gap:8px; margin-top:14px; width:100%;"):\n'
        '                            ui.button("← назад", on_click=_back_t).props("flat").style(\n'
        '                                "color:rgba(255,255,255,0.4); font-size:0.75rem;")\n'
        '                            ui.element("div").style("flex:1")\n'
        '                            ui.button("назначить", on_click=_confirm).props("flat no-caps").style(\n'
        '                                "padding:8px 20px; border-radius:8px; font-weight:700; font-size:0.8rem; "\n'
        '                                "background:linear-gradient(135deg,rgba(120,168,201,0.30),rgba(120,168,201,0.18)); "\n'
        '                                "border:1px solid rgba(120,168,201,0.55); color:#fff;")\n'
        '\n'
        '            render()\n'
        '        dlg.open()\n'
        '\n'
    )
    src = src.replace(anchor_do, do_rol_code + anchor_do, 1)

    # ── бэкап + запись ──
    backup = TARGET.with_name(TARGET.name + ".bak_naznachit_rol")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ патч применён: {TARGET}")
    print(f"✓ бэкап:         {backup}")
    print("— кнопка «Роль» в хедере кабинета Брата, рядом с «Прописка».")
    print("— проверь: python main.py → /brat → «Роль»")


if __name__ == "__main__":
    main()
