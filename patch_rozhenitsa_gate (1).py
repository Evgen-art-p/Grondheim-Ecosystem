# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: СТРАНИЦА ЖИЗНИ — подключить бланк паспорта (ступень 2)║
║                                                              ║
║    1. main.py — route /rozhenitsa                           ║
║    2. ui_brat.py — кнопка «Страница Жизни» в хедере         ║
║                                                              ║
║  Требует: ui_rozhenitsa.py в корне репо.                    ║
║  Идемпотентно. Новый город · ни нитки из -2.                ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MARK = "# PATCH_ROZHENITSA_GATE_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def patch_main():
    p = Path("main.py")
    if not p.exists():
        fail("main.py не найден — запускай из корня Grondheim-Ecosystem")
    src = p.read_text(encoding="utf-8")
    if MARK in src:
        print("[ПАТЧ main.py] ⊙ Страница Жизни уже подключена — пропускаю")
        return

    anchor = (
        '@ui.page("/brat")\n'
        'def _brat():\n'
        '    page_brat()\n'
    )
    if anchor not in src:
        fail("блок @ui.page('/brat') не найден в main.py — покажи свежий")

    addition = (
        anchor +
        '\n'
        '# ── СТРАНИЦА ЖИЗНИ — бланк паспорта (ступень 2) ──\n'
        'from ui_rozhenitsa import page_rozhenitsa\n'
        '@ui.page("/rozhenitsa")\n'
        'def _rozhenitsa():\n'
        '    page_rozhenitsa()\n'
    )
    src = src.replace(anchor, addition, 1)
    src = src.replace('# main.py', f'# main.py  {MARK}', 1)
    p.write_text(src, encoding="utf-8")
    print("[ПАТЧ main.py] ✓ route /rozhenitsa зарегистрирован")


def patch_brat():
    p = Path("ui_brat.py")
    if not p.exists():
        fail("ui_brat.py не найден")
    src = p.read_text(encoding="utf-8")
    if "PATCH_ROZH_BTN" in src:
        print("[ПАТЧ ui_brat.py] ⊙ кнопка Страницы Жизни уже есть — пропускаю")
        return

    # Якорь: модельный селект в хедере (точно есть, читал).
    # Вставим кнопку «Страница Жизни» прямо перед блоком модель-селекта.
    anchor = 'with ui.element("div").classes("brat-model-sel"):'
    if anchor not in src:
        fail("якорь brat-model-sel не найден в ui_brat.py — покажи свежий файл")
    if src.count(anchor) != 1:
        fail(f"якорь brat-model-sel встречается {src.count(anchor)}× — нужен 1")

    # Берём реальный отступ строки с якорем — чтобы вставка легла на любой уровень
    line = next(l for l in src.splitlines() if anchor in l)
    indent = line[:len(line) - len(line.lstrip())]

    btn_lines = [
        'ui.button("Страница Жизни",',
        '          on_click=lambda: ui.navigate.to("/rozhenitsa")  # PATCH_ROZH_BTN',
        '          ).props("flat no-caps").style(',
        '    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "',
        '    "background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08)); "',
        '    "border:1px solid rgba(201,168,76,0.35); color:#fff;")',
    ]
    btn = "\n".join(indent + bl for bl in btn_lines) + "\n" + indent + anchor
    src = src.replace(indent + anchor, btn, 1)
    p.write_text(src, encoding="utf-8")
    print("[ПАТЧ ui_brat.py] ✓ кнопка «Страница Жизни» добавлена в хедер")


def main():
    if not Path("ui_rozhenitsa.py").exists():
        fail("ui_rozhenitsa.py не найден — сначала положи Страницу Жизни, потом патч")
    patch_main()
    patch_brat()
    print()
    print("[ПАТЧ] ✓ Страница Жизни подключена.")
    print("       Проверка: python main.py → /brat → «Страница Жизни» в шапке")
    print("       Заполни бланк → РОДИТЬ ПАСПОРТ → появится в GRONDHEIM_CITY/паспорта/")


if __name__ == "__main__":
    main()
