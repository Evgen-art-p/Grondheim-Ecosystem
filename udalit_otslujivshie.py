#!/usr/bin/env python3
# udalit_otslujivshie.py
# ─────────────────────────────────────────────────────────────
# Удаляет два отслуживших файла из корня (решение Шефа 21.07):
#
#   linii_kasaniya.py           — тестовый инструмент под идею «линий
#                                  через экстремумы», отменённую Шефом
#                                  («забудь, не спеши»). Удаляется
#                                  безусловно.
#
#   arkhivirovat_zigzag_core.py — одноразовый скрипт переноса
#                                  Биржа/zigzag_core.py в архив.
#                                  Удаляется ТОЛЬКО если свою работу
#                                  уже сделал — то есть Биржа/
#                                  zigzag_core.py на месте больше нет.
#                                  Если файл ещё лежит на старом месте
#                                  (скрипт не запускали) — НЕ удаляет
#                                  его, чтобы не потерять инструмент
#                                  до того, как он сработал.
#
# Ничего не архивирует — это удаление НАСОВСЕМ (решение Шефа: «удалить»,
# не «архивировать»). git у Шефа уже хранит историю, если понадобится
# вернуть.
#
# ЗАПУСК (из корня репо):
#   py udalit_otslujivshie.py            — реально удаляет
#   py udalit_otslujivshie.py --dry-run  — только показывает, что сделает
# ─────────────────────────────────────────────────────────────

import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_ROOT = Path(__file__).resolve().parent


def main():
    dry_run = "--dry-run" in sys.argv[1:]

    # ── 1. linii_kasaniya.py — безусловно ──
    linii = _ROOT / "linii_kasaniya.py"
    if linii.exists():
        print(f"[УДАЛЕНИЕ] linii_kasaniya.py — найден "
              f"({linii.stat().st_size:,} байт)".replace(",", " "))
        if not dry_run:
            linii.unlink()
            print("[УДАЛЕНИЕ] linii_kasaniya.py — удалён")
    else:
        print("[УДАЛЕНИЕ] linii_kasaniya.py — уже нет, пропускаю")

    # ── 2. arkhivirovat_zigzag_core.py — только если своё дело сделал ──
    arkhivator = _ROOT / "arkhivirovat_zigzag_core.py"
    zigzag_core_still_here = (_ROOT / "Биржа" / "zigzag_core.py").exists()

    if not arkhivator.exists():
        print("[УДАЛЕНИЕ] arkhivirovat_zigzag_core.py — уже нет, пропускаю")
    elif zigzag_core_still_here:
        print("[УДАЛЕНИЕ] arkhivirovat_zigzag_core.py — НЕ удаляю: "
              "Биржа/zigzag_core.py ещё на старом месте, скрипт свою "
              "работу не сделал. Сначала запусти его без --dry-run, "
              "потом снова этот скрипт.")
    else:
        print("[УДАЛЕНИЕ] arkhivirovat_zigzag_core.py — Биржа/zigzag_core.py "
              "уже в архиве, скрипт своё дело сделал")
        if not dry_run:
            arkhivator.unlink()
            print("[УДАЛЕНИЕ] arkhivirovat_zigzag_core.py — удалён")

    if dry_run:
        print("\n[DRY-RUN] Ничего не удалено. Запусти без --dry-run.")


if __name__ == "__main__":
    main()
