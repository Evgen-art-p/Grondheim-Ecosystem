# AKADEMIA_REKTOR_ROUTE_V1
"""
AKADEMIA_REKTOR_ROUTE_V1 -- регистрирует /rektor/{zid} и /rektor.
Перед запуском положи Академия/rektor.py и Академия/ui_rektor.py --
"Академия" уже в sys.path, новую подпапку заводить не нужно.

Идемпотентно: если маркер AKADEMIA_REKTOR_ROUTE_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_rektor_main_route.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('main.py')
MARKER = 'AKADEMIA_REKTOR_ROUTE_V1'

REPLACEMENTS = [
    ('from ui_akademia import page_akademia\n\n@ui.page("/akademia")\ndef _akademia():\n    page_akademia()', 'from ui_akademia import page_akademia\n\n@ui.page("/akademia")\ndef _akademia():\n    page_akademia()\n\n\n# ── РЕКТОР АКАДЕМИИ — приёмная комиссия, зачисление, оценки, диплом ──\n# AKADEMIA_REKTOR_ROUTE_V1\nfrom ui_rektor import page_rektor\n\n@ui.page("/rektor/{zid}")\ndef _rektor(zid: str = ""):\n    page_rektor(zid)\n\n@ui.page("/rektor")\ndef _rektor0():\n    page_rektor()'),
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

# AKADEMIA_REKTOR_ROUTE_V1 — маркер идемпотентности