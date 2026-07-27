# PATCH_BRAT_GOROD_REMOVED_V1
"""
PATCH_BRAT_GOROD_REMOVED_V1 -- кабинет Брата: убрана кнопка «ГОРОД»
из тулбара стола. Клик по «ГРОНДХЕЙМ» в хедере теперь ведёт на
/grondheim (карту) вместо /karta — одна дверь на карту, не две.

Требует: Брат/ui_brat.py уже прошёл через
  patch_brat_tik_propiska_rol_to_stage.py
(Тик/Прописка/Роль стоят в тулбаре стола рядом с ГОРОД).

Идемпотентно: если маркер PATCH_BRAT_GOROD_REMOVED_V1 уже стоит в
файле — патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_brat_gorod_removed.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Брат/ui_brat.py')
MARKER = 'PATCH_BRAT_GOROD_REMOVED_V1'

REPLACEMENTS = [
    (
        '                    ui.button("ГРОНДХЕЙМ",\n'
        '                              on_click=lambda: ui.navigate.to("/karta")  # PATCH_KARTA_BTN\n'
        '                              ).props("flat no-caps").classes("birzha-header-btn")',

        '                    # PATCH_BRAT_GOROD_REMOVED_V1: раньше вела на /karta,\n'
        '                    # теперь открывает карту напрямую — кнопка ГОРОД убрана\n'
        '                    ui.button("ГРОНДХЕЙМ",\n'
        '                              on_click=lambda: ui.navigate.to("/grondheim")\n'
        '                              ).props("flat no-caps").classes("birzha-header-btn")',
    ),
    (
        '                    with ui.element("div").style(\n'
        '                        "display:flex; gap:8px; align-items:center; justify-content:center;"\n'
        '                    ):\n'
        '                        ui.button("ГОРОД",\n'
        '                                  on_click=lambda: ui.navigate.to("/grondheim")\n'
        '                                  ).props("flat").classes("brat-gate")  # PATCH_GRONDHEIM_VISUAL_MAP\n'
        '                        # PATCH_BRAT_TIK_PROPISKA_ROL_TO_STAGE_V1: спущены из хедера,\n'
        '                        # тот же стиль, что у ГОРОД (.brat-gate) — обработчики те же\n'
        '                        ui.button("⏱ Тик",',

        '                    with ui.element("div").style(\n'
        '                        "display:flex; gap:8px; align-items:center; justify-content:center;"\n'
        '                    ):\n'
        '                        # PATCH_BRAT_GOROD_REMOVED_V1: кнопка ГОРОД убрана — карта\n'
        '                        # открывается кликом на ГРОНДХЕЙМ в хедере (см. выше). Стиль\n'
        '                        # .brat-gate у оставшихся кнопок не тронут.\n'
        '                        ui.button("⏱ Тик",',
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_gorod_removed")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
