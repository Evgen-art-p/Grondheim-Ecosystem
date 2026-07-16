# -*- coding: utf-8 -*-
"""
patch_zagruzchik_scroll2_torg.py
════════════════════════════════════════════════════════════════════
ЗАГРУЗЧИК: раскрытый список ТФ не скроллится — до нижних не добраться

ДИАГНОЗ (нашёл настоящую причину):
  Прошлый CSS-патч (.file-list max-height:300px; overflow-y:auto) НЕ
  действовал, потому что в коде на самом элементе стоит ИНЛАЙН-стиль,
  а инлайн сильнее класса:

    строка ~1851:  files_ref["element"] = ui.element("div").classes("file-list")
                     .style("height:auto; max-height:none; overflow:visible; ...")
                                          └── max-height:none + overflow:visible
                                              = расти бесконечно, не скроллить

    строка ~1837:  .classes("glass asset-bay").style("height:auto; flex:1;")
                                                        └── контейнер без предела

  Итог: список ТФ раскрывается вниз за край панели и обрезается, а
  скролла нет — оба инлайна глушат ограничение высоты.

ЛЕЧЕНИЕ (правим ИНЛАЙН прямо в коде, где он сильнее CSS):
  • .file-list  → max-height:300px; overflow-y:auto (реально крутит);
  • .asset-bay  → max-height:360px, чтобы контейнер имел потолок.

ИДЕМПОТЕНТЕН (маркер ZAGRUZCHIK_SCROLL2_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_zagruzchik_scroll2_torg.py
"""
import io
import sys
from pathlib import Path

MARKER = "ZAGRUZCHIK_SCROLL2_V1"


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

    # 1. file-list инлайн: max-height:none; overflow:visible → скролл
    f_old = ('                    files_ref["element"] = ui.element("div").classes("file-list").style(\n'
             '                        "height:auto; max-height:none; overflow:visible; padding:4px 8px;")')
    f_new = ('                    # ' + MARKER + ': инлайн глушил CSS-скролл. Даём предел\n'
             '                    # высоты и вертикальный скролл — до нижних ТФ добраться.\n'
             '                    files_ref["element"] = ui.element("div").classes("file-list").style(\n'
             '                        "max-height:300px; overflow-y:auto; overflow-x:hidden; padding:4px 8px;")')
    if f_old in src:
        src = src.replace(f_old, f_new, 1)
        changes += 1
        print("[ПАТЧ] ✓ .file-list инлайн — max-height:300px, крутит")
    else:
        print("[ПАТЧ] ⚠️  .file-list инлайн якорь не найден")

    # 2. asset-bay инлайн: height:auto; flex:1 → потолок контейнеру
    a_old = '            with ui.element("div").classes("glass asset-bay").style("height:auto; flex:1;"):'
    a_new = ('            with ui.element("div").classes("glass asset-bay").style('
             '"height:auto; max-height:360px; flex:0 0 auto;"):  # ' + MARKER)
    if a_old in src:
        src = src.replace(a_old, a_new, 1)
        changes += 1
        print("[ПАТЧ] ✓ .asset-bay инлайн — потолок 360px")
    else:
        print("[ПАТЧ] ⚠️  .asset-bay инлайн якорь не найден")

    if changes == 0:
        print("[ПАТЧ] ✗ ни один якорь не совпал — покажи строки 1837 и 1850")
        sys.exit(2)

    bak = path.with_suffix(".py.bak_scroll2")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✅ Готово (правок: {changes}). Обнови /torg — раскрытая")
    print("[ПАТЧ]    папка теперь скроллится, до нижних ТФ можно дотянуться.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
