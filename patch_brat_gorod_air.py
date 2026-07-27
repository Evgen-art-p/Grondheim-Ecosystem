# PATCH_BRAT_GOROD_AIR_V1
"""
PATCH_BRAT_GOROD_AIR_V1 -- визуальная правка кабинета Брата (ui_brat.py):
  1. Больше воздуха НАД кнопкой «ГОРОД» (stage-toolbar) — было почти
     прижато к верху стола, стало с отступом.
  2. Плотнее общий грид контейнеров (.app-container: column-gap/row-gap) —
     меньше зазор между глянцевыми блоками (header/left/stage/right).

Идемпотентно: если маркер PATCH_BRAT_GOROD_AIR_V1 уже стоит в файле —
патч молча выходит, повторно не наложится. Бэкап .bak делается один
раз, при первом применении.

Запуск из корня репо:  python patch_brat_gorod_air.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Брат/ui_brat.py')
MARKER = 'PATCH_BRAT_GOROD_AIR_V1'

REPLACEMENTS = [
    (
        '  column-gap: 20px;\n'
        '  row-gap: 8px;\n'
        '  padding: 20px;',
        '  column-gap: 12px;  /* PATCH_BRAT_GOROD_AIR_V1: было 20px — плотнее контейнеры */\n'
        '  row-gap: 6px;      /* PATCH_BRAT_GOROD_AIR_V1: было 8px */\n'
        '  padding: 20px;',
    ),
    (
        '                with ui.element("div").classes("stage-toolbar").style(\n'
        '                    "flex-shrink:0; grid-template-columns:1fr; justify-items:center; "\n'
        '                    "align-items:end !important; height:55px !important; "\n'
        '                    "padding:9px 12px 6px !important; "\n'
        '                    "background:transparent !important; border-bottom:none !important; "\n'
        '                    "backdrop-filter:none !important;"\n'
        '                ):',
        '                with ui.element("div").classes("stage-toolbar").style(\n'
        '                    "flex-shrink:0; grid-template-columns:1fr; justify-items:center; "\n'
        '                    "align-items:end !important; height:78px !important; "  # PATCH_BRAT_GOROD_AIR_V1: было 55px\n'
        '                    "padding:28px 12px 6px !important; "  # PATCH_BRAT_GOROD_AIR_V1: было 9px 12px 6px — больше воздуха сверху\n'
        '                    "background:transparent !important; border-bottom:none !important; "\n'
        '                    "backdrop-filter:none !important;"\n'
        '                ):',
    ),
]

# REPLACE_ALL — можно встречаться много раз, меняем ВСЕ вхождения
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_gorod_air")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
