# ZHITEL_UCHEBA_BTN_V1
"""
ZHITEL_UCHEBA_BTN_V1 -- кнопка «Учёба» в шапке кабинета жителя,
ведёт на /rektor/{ID_Object} -- к Ректору Академии на собеседование.

Идемпотентно: если маркер ZHITEL_UCHEBA_BTN_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_zhitel_ucheba_button.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('жители/ui_zhitel.py')
MARKER = 'ZHITEL_UCHEBA_BTN_V1'

REPLACEMENTS = [
    ('                ui.button("карта", on_click=lambda: ui.navigate.to("/grondheim")) \\\n                    .props("flat no-caps").classes("zback").style("margin-right:8px;")\n                ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")) \\\n                    .props("flat no-caps").classes("zback")', '                # ZHITEL_UCHEBA_BTN_V1\n                ui.button("🎓 учёба", on_click=lambda: ui.navigate.to(f"/rektor/{p.get(\'ID_Object\',\'\')}")) \\\n                    .props("flat no-caps").classes("zback").style("margin-right:8px;")\n                ui.button("карта", on_click=lambda: ui.navigate.to("/grondheim")) \\\n                    .props("flat no-caps").classes("zback").style("margin-right:8px;")\n                ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")) \\\n                    .props("flat no-caps").classes("zback")'),
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")

if __name__ == "__main__":
    main()

# ZHITEL_UCHEBA_BTN_V1 — маркер идемпотентности