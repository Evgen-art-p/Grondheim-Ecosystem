# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ВРАТА КАРТЫ — подключить каркас карты-иерархии        ║
║  Ступень 1 рождения мира · «сначала карта готовая»          ║
║                                                              ║
║  Что делает:                                                 ║
║    1. main.py — регистрирует route /karta (страница карты)   ║
║    2. ui_brat.py — кнопка «Карта» в хедере кабинета         ║
║                                                              ║
║  Требует: ui_karta.py уже лежит в корне репо (каркас карты). ║
║  Идемпотентно. Новый город · ни нитки из -2.                ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MARK = "# PATCH_KARTA_GATE_APPLIED"


def fail(msg):
    print(f"[ПАТЧ] ✗ {msg}")
    sys.exit(1)


def patch_main():
    p = Path("main.py")
    if not p.exists():
        fail("main.py не найден — запускай из корня Grondheim-Ecosystem")
    src = p.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ main.py] ⊙ карта уже подключена — пропускаю")
        return

    # Якорь: блок регистрации страницы Брата
    anchor = (
        '@ui.page("/brat")\n'
        'def _brat():\n'
        '    page_brat()\n'
    )
    if anchor not in src:
        fail("блок @ui.page('/brat') не найден дословно в main.py — покажи свежий")

    addition = (
        anchor +
        '\n'
        '# ── КАРТА-ИЕРАРХИЯ — зрение Брата (ступень 1) ──\n'
        'from ui_karta import page_karta\n'
        '@ui.page("/karta")\n'
        'def _karta():\n'
        '    page_karta()\n'
    )
    src = src.replace(anchor, addition, 1)

    # метка
    src = src.replace('# main.py', f'# main.py  {MARK}', 1)
    p.write_text(src, encoding="utf-8")
    print("[ПАТЧ main.py] ✓ route /karta зарегистрирован")


def patch_brat():
    p = Path("ui_brat.py")
    if not p.exists():
        fail("ui_brat.py не найден")
    src = p.read_text(encoding="utf-8")

    if "PATCH_KARTA_BTN" in src:
        print("[ПАТЧ ui_brat.py] ⊙ кнопка Карты уже есть — пропускаю")
        return

    # Якорь: кнопка ГРОНДХЕЙМ в хедере (она точно есть, я её читал)
    anchor = 'ui.button("ГРОНДХЕЙМ").props("flat no-caps")'
    if anchor not in src:
        fail("кнопка ГРОНДХЕЙМ не найдена в ui_brat.py — покажи свежий файл")

    # Вешаем на ГРОНДХЕЙМ переход на карту — она и есть «вход в город»
    old = 'ui.button("ГРОНДХЕЙМ").props("flat no-caps").style('
    new = ('ui.button("ГРОНДХЕЙМ",\n'
           '                          on_click=lambda: ui.navigate.to("/karta")  # PATCH_KARTA_BTN\n'
           '                          ).props("flat no-caps").style(')
    if src.count(old) != 1:
        fail(f"якорь кнопки ГРОНДХЕЙМ встречается {src.count(old)}× — нужен 1")
    src = src.replace(old, new, 1)

    p.write_text(src, encoding="utf-8")
    print("[ПАТЧ ui_brat.py] ✓ кнопка ГРОНДХЕЙМ → карта города")


def main():
    if not Path("ui_karta.py").exists():
        fail("ui_karta.py не найден в корне — сначала положи каркас карты, потом патч")
    patch_main()
    patch_brat()
    print()
    print("[ПАТЧ] ✓ Карта подключена.")
    print("       Проверка: python main.py → /brat → жми «ГРОНДХЕЙМ» в шапке")
    print("       Откроется карта-иерархия: Брат → 4 этажа (Храм с вратами).")
    print("       Назад — кнопкой «← в кабинет».")


if __name__ == "__main__":
    main()
