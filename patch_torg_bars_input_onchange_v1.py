# -*- coding: utf-8 -*-
"""
patch_torg_bars_input_onchange_v1.py
─────────────────────────────────────────────────────────────
ПОЧИНКА ПОЛЯ «ЛОВИТЬ» · Биржа/ui_torg.py

ДИАГНОЗ: поле числа сигналов тестера было привязано так:
    _bi = ui.number(value=1, min=1, max=999, format="%d")...
    _bi.on("update:model-value", lambda e: state.update(...))

  "update:model-value" — сырое имя внутреннего quasar-события, не
  часть публичного API NiceGUI. В зависимости от версии NiceGUI/Quasar
  оно может не всплывать так, как ожидается — тогда ввод в поле НЕ
  долетает до state["bars_to_live"], тестер всегда ловит 1 сигнал
  независимо от того, что введено (что и наблюдалось).

ЛЕЧЕНИЕ: используем штатный параметр on_change из публичного API
ui.number — гарантированно работает в любой поддерживаемой версии
NiceGUI, не зависит от внутренних имён событий Quasar.

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_torg_bars_input_onchange_v1.py

Идемпотентно: маркер TORG_BARS_ONCHANGE_V1.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "ui_torg.py"
MARKER = "# TORG_BARS_ONCHANGE_V1 — маркер идемпотентности"

OLD_BLOCK = '''                        with toolbar_refs["bars_input"]:
                            _bi = ui.number(value=1, min=1, max=999, format="%d").props("dense borderless").style(
                                "width:60px;font-family:JetBrains Mono;font-size:12px;color:rgba(0,204,255,0.9);")
                            _bi.on("update:model-value", lambda e: state.update({"bars_to_live": int(e.args or 1)}))'''

NEW_BLOCK = '''                        with toolbar_refs["bars_input"]:
                            def _on_bars_change(e):   # TORG_BARS_ONCHANGE_V1
                                try:
                                    state["bars_to_live"] = int(e.value or 1)
                                except (TypeError, ValueError):
                                    state["bars_to_live"] = 1
                            _bi = ui.number(
                                value=1, min=1, max=999, format="%d",
                                on_change=_on_bars_change,   # штатный API NiceGUI, не сырое quasar-событие
                            ).props("dense borderless").style(
                                "width:60px;font-family:JetBrains Mono;font-size:12px;color:rgba(0,204,255,0.9);")'''


def _patch():
    if not TARGET.exists():
        print(f"[ПАТЧ] ❌ Не найден {TARGET} — запусти из корня репо.")
        raise SystemExit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ уже пропатчен (TORG_BARS_ONCHANGE_V1) — пропускаю.")
        return False

    if OLD_BLOCK in src:
        src = src.replace(OLD_BLOCK, NEW_BLOCK)
        print("[ПАТЧ] 🔧 поле «ловить»: on_change вместо сырого quasar-события")
    elif NEW_BLOCK in src:
        print("[ПАТЧ] ↺ уже на месте")
        return False
    else:
        print("[ПАТЧ] ⚠️  блок не совпал — проверь вручную")
        return False

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    TARGET.write_text(src, encoding="utf-8")
    print("[ПАТЧ] 💾 ui_torg.py сохранён.")
    return True


def main():
    print("═" * 62)
    print("  ПОЧИНКА ПОЛЯ «ЛОВИТЬ» · TORG_BARS_ONCHANGE_V1")
    print("═" * 62)
    _patch()
    print("═" * 62)
    print("  ✅ ГОТОВО. Перезапусти студию. Проверка: вкладка ТЕСТЕР,")
    print("     поставь в поле «ловить» число 3, жми РЫНОК — тестер должен")
    print("     сказать 'ловлю 3 срабатываний', не 1.")
    print("═" * 62)


if __name__ == "__main__":
    main()
