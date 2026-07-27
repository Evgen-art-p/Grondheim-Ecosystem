# PATCH_BRAT_GOLD_BUTTONS_V1
"""
PATCH_BRAT_GOLD_BUTTONS_V1 -- единый цвет всех кнопок кабинета Брата.

Было: три разных палитры —
  зелёно-голубая  .brat-gate (ГОРОД/Тик/Прописка/Роль), .birzha-header-btn (ГРОНДХЕЙМ/Страница Жизни)
  фиолетовая      📂 (загрузить чат), ⚗ Просеять, ⬇ (скачать просев)
  золотая         💾 (сохранить чат), ОТПРАВИТЬ (.send-button)

Стало: все кнопки — золотая палитра .send-button (rgba(201,168,76,...)).
Форма/раскладка каждой кнопки (высота, скругление, вкладка сверху у
.brat-gate и т.п.) не тронута — меняется только цвет.

Не трогает: .neon-btn (g/b/p) и .util-btn — эти CSS-классы объявлены,
но НЕ используются нигде в текущей разметке кабинета (легаси из
копии стиля Биржи), перекрашивать их — менять то, что не рисуется.

Идемпотентно: если маркер PATCH_BRAT_GOLD_BUTTONS_V1 уже стоит в
файле — патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_brat_gold_buttons.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Брат/ui_brat.py')
MARKER = 'PATCH_BRAT_GOLD_BUTTONS_V1'

REPLACEMENTS = [
    # ── .brat-gate: зелёно-голубой → золотой ──
    (
        '.brat-gate{ min-height:45px !important; padding:10px 22px !important;\n'
        '            border-radius:8px 8px 0 0 !important;\n'
        '            min-width:150px !important; width:auto !important; max-width:none !important;\n'
        '            background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10)) !important;\n'
        '            border-top: 1px solid rgba(0,255,136,0.35) !important;\n'
        '            border-left: 1px solid rgba(0,255,136,0.35) !important;\n'
        '            border-right: 1px solid rgba(0,255,136,0.35) !important;\n'
        '            border-bottom: none !important;\n'
        '            color: rgba(255,255,255,0.9) !important; font-weight:700 !important; font-size:0.85rem !important;\n'
        '            text-transform:none !important; }\n'
        '.brat-gate .q-btn__content{ width:100% !important; justify-content:center !important; }\n'
        '.brat-gate:hover{ background: linear-gradient(135deg, rgba(0,255,136,0.24), rgba(0,204,255,0.16)) !important; }',

        '/* PATCH_BRAT_GOLD_BUTTONS_V1: было зелёно-голубое, теперь золото — как .send-button */\n'
        '.brat-gate{ min-height:45px !important; padding:10px 22px !important;\n'
        '            border-radius:8px 8px 0 0 !important;\n'
        '            min-width:150px !important; width:auto !important; max-width:none !important;\n'
        '            background: linear-gradient(135deg, rgba(201,168,76,0.15), rgba(201,168,76,0.10)) !important;\n'
        '            border-top: 1px solid rgba(201,168,76,0.35) !important;\n'
        '            border-left: 1px solid rgba(201,168,76,0.35) !important;\n'
        '            border-right: 1px solid rgba(201,168,76,0.35) !important;\n'
        '            border-bottom: none !important;\n'
        '            color: rgba(255,255,255,0.9) !important; font-weight:700 !important; font-size:0.85rem !important;\n'
        '            text-transform:none !important; }\n'
        '.brat-gate .q-btn__content{ width:100% !important; justify-content:center !important; }\n'
        '.brat-gate:hover{ background: linear-gradient(135deg, rgba(201,168,76,0.24), rgba(201,168,76,0.16)) !important; }',
    ),
    # ── .birzha-header-btn: зелёно-голубой → золотой ──
    (
        '.birzha-header-btn{\n'
        '    padding: 8px 18px !important; border-radius: 8px !important;\n'
        '    background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10)) !important;\n'
        '    border: 1px solid rgba(0,255,136,0.35) !important;\n'
        '    color: rgba(255,255,255,0.9) !important; font-weight: 700 !important;\n'
        '}\n'
        '.birzha-header-btn:hover{\n'
        '    background: linear-gradient(135deg, rgba(0,255,136,0.24), rgba(0,204,255,0.16)) !important;\n'
        '}',

        '/* PATCH_BRAT_GOLD_BUTTONS_V1: было зелёно-голубое, теперь золото */\n'
        '.birzha-header-btn{\n'
        '    padding: 8px 18px !important; border-radius: 8px !important;\n'
        '    background: linear-gradient(135deg, rgba(201,168,76,0.15), rgba(201,168,76,0.10)) !important;\n'
        '    border: 1px solid rgba(201,168,76,0.35) !important;\n'
        '    color: rgba(255,255,255,0.9) !important; font-weight: 700 !important;\n'
        '}\n'
        '.birzha-header-btn:hover{\n'
        '    background: linear-gradient(135deg, rgba(201,168,76,0.24), rgba(201,168,76,0.16)) !important;\n'
        '}',
    ),
    # ── ⚗ Просеять: фиолетовый → золотой ──
    (
        '                    ui.button("⚗ Просеять", on_click=do_sift).props("flat no-caps").style(\n'
        '                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "\n'
        '                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "\n'
        '                        "background:linear-gradient(135deg,rgba(189,0,255,0.18),rgba(0,204,255,0.10)) !important; "\n'
        '                        "border:1px solid rgba(189,0,255,0.45) !important; color:#e0aaff !important;")',

        '                    # PATCH_BRAT_GOLD_BUTTONS_V1: было фиолетовое, теперь золото\n'
        '                    ui.button("⚗ Просеять", on_click=do_sift).props("flat no-caps").style(\n'
        '                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "\n'
        '                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "\n'
        '                        "background:linear-gradient(135deg,rgba(201,168,76,0.18),rgba(201,168,76,0.10)) !important; "\n'
        '                        "border:1px solid rgba(201,168,76,0.45) !important; color:#e8c96a !important;")',
    ),
    # ── ⬇ скачать просев: фиолетовый → золотой ──
    (
        '                        ui.button("⬇", on_click=lambda f=fp: ui.download(f)) \\\n'
        '                            .props("flat dense").style(\n'
        '                                "font-size:0.9rem; padding:2px 8px; border-radius:6px; "\n'
        '                                "color:rgba(189,0,255,0.9); background:rgba(189,0,255,0.12); "\n'
        '                                "border:1px solid rgba(189,0,255,0.35); min-width:0;")',

        '                        ui.button("⬇", on_click=lambda f=fp: ui.download(f)) \\\n'
        '                            .props("flat dense").style(\n'
        '                                "font-size:0.9rem; padding:2px 8px; border-radius:6px; "\n'
        '                                "color:rgba(201,168,76,0.9); background:rgba(201,168,76,0.12); "\n'
        '                                "border:1px solid rgba(201,168,76,0.35); min-width:0;")',
    ),
    # ── 📂 загрузить чат: голубой → золотой (💾 рядом уже золотое) ──
    (
        '                    ui.button("📂", on_click=do_load).props("flat").style(\n'
        '                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "\n'
        '                        "color:rgba(0,204,255,0.9); background:rgba(0,204,255,0.10); "\n'
        '                        "border:1px solid rgba(0,204,255,0.35);")',

        '                    # PATCH_BRAT_GOLD_BUTTONS_V1: было голубое, теперь золото — как 💾 рядом\n'
        '                    ui.button("📂", on_click=do_load).props("flat").style(\n'
        '                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "\n'
        '                        "color:rgba(201,168,76,0.9); background:rgba(201,168,76,0.10); "\n'
        '                        "border:1px solid rgba(201,168,76,0.35);")',
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_gold_buttons")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
