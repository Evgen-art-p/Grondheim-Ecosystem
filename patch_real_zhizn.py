# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ВЕРНУТЬ НАСТОЯЩУЮ СТРАНИЦУ ЖИЗНИ                      ║
║                                                              ║
║  Проблема: подключён черновик ui_rozhenitsa (бедный бланк), ║
║  а настоящая полная Страница ui_registry — закомментирована.║
║                                                              ║
║  Чиним:                                                      ║
║    • выключаем черновик ui_rozhenitsa                        ║
║    • включаем настоящую ui_registry (route /registry)        ║
║    • кнопка «Страница Жизни» у Брата → /registry             ║
║                                                              ║
║  Черновик в топку — как договорились (путь А).              ║
║  Идемпотентно.                                               ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MARK = "# PATCH_REAL_ZHIZN_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def patch_main():
    p = Path("main.py")
    if not p.exists():
        fail("main.py не найден — запускай из корня Grondheim-Ecosystem")
    src = p.read_text(encoding="utf-8")
    if MARK in src:
        print("[ПАТЧ main.py] ⊙ настоящая Страница уже подключена — пропускаю")
        return

    # 1. Выключаем черновик ui_rozhenitsa (закомментируем блок)
    rozh_block = (
        '# ── СТРАНИЦА ЖИЗНИ — бланк паспорта (ступень 2) ──\n'
        'from ui_rozhenitsa import page_rozhenitsa\n'
        '@ui.page("/rozhenitsa")\n'
        'def _rozhenitsa():\n'
        '    page_rozhenitsa()\n'
    )
    if rozh_block in src:
        rozh_off = (
            '# ── ЧЕРНОВИК ui_rozhenitsa ВЫКЛЮЧЕН (в топку, путь А) ──\n'
            '# Настоящая Страница Жизни — ui_registry ниже.\n'
            '# from ui_rozhenitsa import page_rozhenitsa\n'
            '# @ui.page("/rozhenitsa")\n'
            '# def _rozhenitsa():\n'
            '#     page_rozhenitsa()\n'
        )
        src = src.replace(rozh_block, rozh_off, 1)
        print("[ПАТЧ main.py] ✓ черновик ui_rozhenitsa выключен")
    else:
        print("[ПАТЧ main.py] ⚠ блок черновика не найден дословно — возможно уже убран")

    # 2. Включаем настоящую ui_registry (раскомментируем)
    reg_off = (
        '# ── РЕЕСТР (если нужен) ──\n'
        '# from ui_registry import page_registry\n'
        '# @ui.page("/registry")\n'
        '# def _registry():\n'
        '#     page_registry()\n'
    )
    reg_on = (
        '# ── НАСТОЯЩАЯ СТРАНИЦА ЖИЗНИ · Реестр (полная форма) ──\n'
        'from ui_registry import page_registry\n'
        '@ui.page("/registry")\n'
        'def _registry():\n'
        '    page_registry()\n'
    )
    if reg_off in src:
        src = src.replace(reg_off, reg_on, 1)
        print("[ПАТЧ main.py] ✓ настоящая ui_registry включена (/registry)")
    elif 'from ui_registry import page_registry' in src and '@ui.page("/registry")' in src:
        print("[ПАТЧ main.py] ⊙ ui_registry уже подключена")
    else:
        fail("закомментированный блок реестра не найден — покажи свежий main.py")

    src = src.replace('# main.py', f'# main.py  {MARK}', 1)
    p.write_text(src, encoding="utf-8")


def patch_brat():
    p = Path("ui_brat.py")
    if not p.exists():
        print("[ПАТЧ ui_brat.py] ⚠ ui_brat.py не найден — пропускаю кнопку")
        return
    src = p.read_text(encoding="utf-8")
    # Перенаправляем кнопку «Страница Жизни» с /rozhenitsa на /registry
    if 'ui.navigate.to("/rozhenitsa")' in src:
        src = src.replace('ui.navigate.to("/rozhenitsa")', 'ui.navigate.to("/registry")')
        p.write_text(src, encoding="utf-8")
        print("[ПАТЧ ui_brat.py] ✓ кнопка «Страница Жизни» → /registry")
    else:
        print("[ПАТЧ ui_brat.py] ⊙ кнопка уже ведёт куда надо (или её нет)")


def main():
    patch_main()
    patch_brat()
    print()
    print("[ПАТЧ] ✓ Готово. Настоящая Страница Жизни вернулась.")
    print("       python main.py → /brat → «Страница Жизни» → откроется ТВОЯ полная форма")
    print("       (или прямо http://localhost:8080/registry )")


if __name__ == "__main__":
    main()
