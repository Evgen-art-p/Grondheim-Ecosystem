# patch_kto_zdes_byvaet.py
"""
Камень: реверс-транспорт локация → жители («кто здесь бывает»).

До патча: правая панель ui_lokacia.py — текст-заглушка, ничего не
сканирует. У жителя есть поле "прописка", локация его не спрашивает.

После патча: панель зовёт list_zhiteli() из ui_zhitel.py, отбирает тех,
у кого прописка == ID_Object этой локации, показывает кликабельный
список → /zhitel/{id}. Ничего не хранится на стороне локации —
Закон Пары: одна правда у жителя, локация её только спрашивает по
требованию, как list_cartridges() у цехов.

Запуск из КОРНЯ репо (там же, где main.py):
    python patch_kto_zdes_byvaet.py

Идемпотентен — если маркер PATCH_KTO_ZDES_BYVAET уже стоит в файле,
скрипт не тронет его повторно.

Бэкап: ГОРОД/ui_lokacia.py.bak_kto_zdes_byvaet
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
TARGET = _ROOT / "ГОРОД" / "ui_lokacia.py"
MARKER = "PATCH_KTO_ZDES_BYVAET"


def main():
    if not TARGET.exists():
        print(f"✗ не найден: {TARGET}")
        print("  запускай из корня репо (там же, где main.py)")
        return

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"— уже применён ({MARKER} найден в {TARGET.name}) — пропускаю")
        return

    changed = False

    # ── 1. импорт list_zhiteli (с защитой на случай автономного запуска) ──
    anchor_import = (
        'import json\n'
        'from pathlib import Path\n'
        'from nicegui import ui\n'
        '\n'
        '_ROOT = Path(__file__).resolve().parent.parent  # файл в ГОРОД/, корень репо — выше\n'
        'LOKACII_DIR = _ROOT / "GRONDHEIM_CITY" / "локации"\n'
    )
    if anchor_import not in src:
        print("✗ не нашёл опорный блок импортов — файл изменился, патч не подходит вслепую")
        return

    addition_import = (
        '\n'
        f'# {MARKER} — реверс-транспорт: локация спрашивает жителей, кто здесь\n'
        '# прописан. Ничего не хранит сама (Закон Пары) — только сканирует по\n'
        '# требованию, как list_cartridges() у цехов.\n'
        'try:\n'
        '    from ui_zhitel import list_zhiteli\n'
        'except ImportError:\n'
        '    import sys as _sys\n'
        '    _zh_dir = str(_ROOT / "жители")\n'
        '    if _zh_dir not in _sys.path:\n'
        '        _sys.path.insert(0, _zh_dir)\n'
        '    from ui_zhitel import list_zhiteli\n'
    )
    src = src.replace(anchor_import, anchor_import + addition_import, 1)
    changed = True

    # ── 2. CSS: список жителей локации ──
    anchor_css = (
        '.script-item{ font-size:0.8rem; color:rgba(255,255,255,0.82); padding:7px 10px; margin:5px 0;\n'
        '  border-radius:10px; background:rgba(255,255,255,0.04); border-left:3px solid rgba(201,168,76,0.5); }\n'
    )
    if anchor_css not in src:
        print("✗ не нашёл CSS-опору .script-item — файл изменился, откатываю")
        TARGET.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")  # noop safety
        return

    addition_css = (
        '.residents{ max-height:220px; overflow-y:auto; padding:6px 10px; }\n'
        '.resident-item{ width:100% !important; text-align:left !important; margin:4px 0 !important;\n'
        '  padding:8px 12px !important; border-radius:10px !important;\n'
        '  background:rgba(201,168,76,0.08) !important; border:1px solid rgba(201,168,76,0.25) !important;\n'
        '  color:#fff !important; font-size:0.8rem !important; text-transform:none !important;\n'
        '  font-weight:400 !important; }\n'
        '.resident-item:hover{ background:rgba(201,168,76,0.16) !important; }\n'
    )
    src = src.replace(anchor_css, anchor_css + addition_css, 1)

    # ── 3. живой блок вместо заглушки ──
    anchor_block = (
        '                # кто здесь бывает (задел: пока жители не привязаны к локации)\n'
        '                with ui.element("div").classes("glass").style("flex-shrink:0;"):\n'
        '                    ui.html(\'<div class="panel-title">кто здесь бывает</div>\')\n'
        '                    ui.html(\'<div class="lcore" style="opacity:0.6;">— пока никто не прописан сюда —<br>\'\n'
        '                            \'появятся, когда жители получат прописку в этом месте</div>\')\n'
    )
    if anchor_block not in src:
        print("✗ не нашёл блок «кто здесь бывает» — файл изменился, откатываю")
        return

    new_block = (
        f'                # {MARKER}: живой скан по прописке — не список, а вопрос жителям\n'
        '                with ui.element("div").classes("glass").style("flex-shrink:0;"):\n'
        '                    ui.html(\'<div class="panel-title">кто здесь бывает</div>\')\n'
        '                    _lid_here = p.get("ID_Object", "")\n'
        '                    _zdes = [z for z in list_zhiteli()\n'
        '                             if str(z.get("прописка") or "") == str(_lid_here)]\n'
        '                    if _zdes:\n'
        '                        with ui.element("div").classes("residents"):\n'
        '                            for _z in _zdes:\n'
        '                                _nm = _z.get("Official_Name", "?")\n'
        '                                _zi = _z.get("ID_Object", "")\n'
        '                                ui.button(_nm, on_click=lambda _zi=_zi: ui.navigate.to(f"/zhitel/{_zi}")) \\\n'
        '                                    .props("flat no-caps").classes("resident-item")\n'
        '                    else:\n'
        '                        ui.html(\'<div class="lcore" style="opacity:0.6;">— пока никто не прописан сюда —<br>\'\n'
        '                                \'появятся, когда жители получат прописку в этом месте</div>\')\n'
    )
    src = src.replace(anchor_block, new_block, 1)

    # ── бэкап + запись ──
    backup = TARGET.with_name(TARGET.name + ".bak_kto_zdes_byvaet")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ патч применён: {TARGET}")
    print(f"✓ бэкап:         {backup}")
    print("— «кто здесь бывает» теперь живой скан по полю «прописка».")
    print("— проверь: python main.py → /lokacia/0006_CREATOR_TOWER")


if __name__ == "__main__":
    main()
