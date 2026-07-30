# -*- coding: utf-8 -*-
"""
PATCH_KARTA_ARKHIV_GATE_V1 — Архив на карте города

НАЙДЕНО: LOCATION_GATES в ГОРОД/ui_grondheim.py заводит клик-переходы
для Маяка, Биржи, Академии — Архива в списке нет. Без записи клик по
зданию Архива вёл в общий безликий паспорт локации (/lokacia/{id}),
не в настоящий рабочий кабинет (/arkhiv, ui_arkhiv.py). Вот почему
"не попасть в архив" — врата просто не были заявлены.

ID локации — "0015_GRONDHEIM_ARCHIVE", подтверждён кодом самого
кабинета (Архив/ui_arkhiv.py: ZDANIE = "0015_GRONDHEIM_ARCHIVE") и
разбором дубля 29.07 — это живая копия, не черновик 0006.

Запуск из корня репозитория:
    python patch_karta_arkhiv_gate.py

Идемпотентно, бэкап .bak.
`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
UI_GRONDHEIM_PATH = REPO / "ГОРОД" / "ui_grondheim.py"

MARKER = "0015_GRONDHEIM_ARCHIVE"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    sys.exit(1)


OLD = '''LOCATION_GATES = {
    "0005_LIGHTHOUSE_AWAKENING": "/mayak",  # Маяк -> кабинет (ui_mayak.py)
    "0014_EXCHANGE": "/torg",       # Биржа -> стол Совета (ui_torg.py)
    "0008_OWL_CASTLE": "/akademia", # Замок Сов -> кабинет Академии (ui_akademia.py)
}'''

NEW = '''LOCATION_GATES = {
    "0005_LIGHTHOUSE_AWAKENING": "/mayak",  # Маяк -> кабинет (ui_mayak.py)
    "0014_EXCHANGE": "/torg",       # Биржа -> стол Совета (ui_torg.py)
    "0008_OWL_CASTLE": "/akademia", # Замок Сов -> кабинет Академии (ui_akademia.py)
    "0015_GRONDHEIM_ARCHIVE": "/arkhiv",  # Архив -> кабинет Хранителя (ui_arkhiv.py)
}'''


def main() -> None:
    print("── PATCH_KARTA_ARKHIV_GATE_V1 ──")
    if not UI_GRONDHEIM_PATH.exists():
        _stop(f"{UI_GRONDHEIM_PATH} не найден.")

    text = UI_GRONDHEIM_PATH.read_text(encoding="utf-8")
    if f'"{MARKER}": "/arkhiv"' in text:
        print("✓ уже добавлено — патч уже применён.")
        return

    n = text.count(OLD)
    if n == 0:
        _stop("якорь LOCATION_GATES не найден — код изменился, нужна ручная сверка.")
    if n > 1:
        _stop(f"якорь встретился {n} раз — должен быть один.")

    new_text = text.replace(OLD, NEW, 1)

    bak = UI_GRONDHEIM_PATH.with_suffix(".py.bak_arkhiv_gate")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    UI_GRONDHEIM_PATH.write_text(new_text, encoding="utf-8")

    print(f"✓ бэкап: {bak.name}")
    print(f"✓ записано: {UI_GRONDHEIM_PATH}")
    print()
    print("Готово. На карте (/grondheim) клик по зданию Архива теперь")
    print("ведёт прямо в кабинет Хранителя (/arkhiv), как Маяк и Академия.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
