# -*- coding: utf-8 -*-
"""
patch_zagruzchik_scroll_torg.py
════════════════════════════════════════════════════════════════════
ЗАГРУЗЧИК: раскрытая папка ТФ не влезала и не скроллилась + нет стрелки

БОЛЕЗНЬ (скрин шефа):
  Папка "XAUUSD · 12 ТФ" раскрывается, но:
    1. содержимое обрезается, вниз не крутит;
    2. нет стрелки-символа раскрытия.

ДИАГНОЗ (CSS в ui_torg.py):
  .asset-bay{ height:120px; overflow:hidden }  — жёсткие 120px, режет.
  .file-list{ max-height:50px }                — список зажат в 50px.
  Раскрыл 12 ТФ — им некуда влезть, overflow:hidden не даёт крутить.
  Стрелка ui.expansion (Quasar-иконка) тонет в тёмной теме.

ЛЕЧЕНИЕ:
  • .asset-bay — выше (180px) и overflow:visible, чтобы не резал;
  • .file-list — max-height до 300px + плавный overflow-y:auto (крутит);
  • стрелке expansion (.q-expansion-item .q-icon) — явный светлый цвет.

Только CSS-строки. Логику папок (ZAGRUZCHIK_PAPKI_TORG_V1) не трогаем.

ИДЕМПОТЕНТЕН (маркер ZAGRUZCHIK_SCROLL_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_zagruzchik_scroll_torg.py
"""
import io
import sys
from pathlib import Path

MARKER = "ZAGRUZCHIK_SCROLL_V1"


def find_target() -> Path:
    for p in (Path("Биржа") / "ui_torg.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "ui_torg.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден Биржа/ui_torg.py — запусти из корня")
    sys.exit(1)


def main():
    path = find_target()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src
    changes = 0

    # 1. .asset-bay — выше и не режет
    a_old = ".asset-bay{ height: 120px; flex-shrink: 0; overflow: hidden; }"
    a_new = (".asset-bay{ height: auto; max-height: 340px; flex-shrink: 0; "
             "overflow: visible; }  /* " + MARKER + ": было 120px/hidden */")
    if a_old in src:
        src = src.replace(a_old, a_new, 1)
        changes += 1
        print("[ПАТЧ] ✓ .asset-bay — растёт, не режет")
    else:
        print("[ПАТЧ] ⚠️  .asset-bay якорь не найден")

    # 2. .file-list — крутит
    f_old = (".file-list{ padding: 8px 12px; max-height: 50px; overflow-y: auto; "
             "font-family: monospace; font-size: 11px; }")
    f_new = (".file-list{ padding: 8px 12px; max-height: 300px; overflow-y: auto; "
             "font-family: monospace; font-size: 11px; }  /* " + MARKER
             + ": было 50px */")
    if f_old in src:
        src = src.replace(f_old, f_new, 1)
        changes += 1
        print("[ПАТЧ] ✓ .file-list — max-height 300px, крутит")
    else:
        print("[ПАТЧ] ⚠️  .file-list якорь не найден")

    # 3. стрелка expansion — явный цвет. Вставляем правило после .file-list.
    if ".q-expansion-item" not in src and f_new in src:
        arrow_css = (
            f_new + "\n"
            "/* " + MARKER + ": стрелка раскрытия папок — видимый цвет */\n"
            ".file-list .q-expansion-item .q-icon,\n"
            ".file-list .q-item__section--side .q-icon{\n"
            "  color: rgba(0,204,255,0.9) !important;\n"
            "}\n"
            ".file-list .q-expansion-item{ color: rgba(255,255,255,0.85); }\n"
        )
        src = src.replace(f_new, arrow_css, 1)
        changes += 1
        print("[ПАТЧ] ✓ стрелка expansion — голубая, видимая")

    if changes == 0:
        print("[ПАТЧ] ✗ ни один якорь не совпал — CSS изменён? останов")
        sys.exit(2)

    bak = path.with_suffix(".py.bak_zagruzchik_scroll")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✅ Готово (правок: {changes}). Обнови /torg — папка")
    print("[ПАТЧ]    крутится, все ТФ видны, стрелка на месте.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
