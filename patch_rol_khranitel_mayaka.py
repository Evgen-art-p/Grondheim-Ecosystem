# -*- coding: utf-8 -*-
"""
PATCH_ROL_KHRANITEL_MAYAKA_V1 — Хранитель Маяка в форму «Роль»

Пост khranitel_mayaka уже заведён на диске (patch_khranitel_mayaka.py),
но форма «Роль» в Брат/ui_brat.py берёт список типов из захардкоженного
TIPY + TIP_TO_POST, а не сканирует rezidenty.list_posty() живьём —
поэтому новый пост сам не появился. Это точечная правка ровно двух
строк, не переделка списка (Шеф решил категории не трогать).

Запуск из корня репозитория:
    python patch_rol_khranitel_mayaka.py

Идемпотентно, бэкап .bak.
`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
UI_BRAT_PATH = REPO / "Брат" / "ui_brat.py"

MARKER = "хранитель_маяка"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    sys.exit(1)


OLD_TIPY = '''        TIPY = ["резидент", "хранитель", "воркер", "студент",
                "библиотекарь", "хранитель_архива", "ректор"]  # PATCH_AKADEMIA_STUDENT_V1 + PATCH_POST_CHEREZ_ROL_V1
        # PATCH_POST_CHEREZ_ROL_V1: тип -> id поста в rezidenty.py.
        # Библиотекарь/Архив/Ректор — это ПОСТЫ (GRONDHEIM_CITY/посты/),
        # не Закон Пары. Выбрал такой тип — полей Цех/Слот/Фраза не
        # будет, посадка идёт сразу, одним кликом «назначить».
        TIP_TO_POST = {
            "библиотекарь": "bibliotekar",
            "хранитель_архива": "khranitel_arkhiva",
            "ректор": "rektor",
        }'''

NEW_TIPY = '''        TIPY = ["резидент", "хранитель", "воркер", "студент",
                "библиотекарь", "хранитель_архива", "ректор",
                "хранитель_маяка"]  # PATCH_AKADEMIA_STUDENT_V1 + PATCH_POST_CHEREZ_ROL_V1 + PATCH_ROL_KHRANITEL_MAYAKA_V1
        # PATCH_POST_CHEREZ_ROL_V1: тип -> id поста в rezidenty.py.
        # Библиотекарь/Архив/Ректор/Маяк — это ПОСТЫ (GRONDHEIM_CITY/посты/),
        # не Закон Пары. Выбрал такой тип — полей Цех/Слот/Фраза не
        # будет, посадка идёт сразу, одним кликом «назначить».
        TIP_TO_POST = {
            "библиотекарь": "bibliotekar",
            "хранитель_архива": "khranitel_arkhiva",
            "ректор": "rektor",
            "хранитель_маяка": "khranitel_mayaka",
        }'''


def main() -> None:
    print("── PATCH_ROL_KHRANITEL_MAYAKA_V1 ──")
    if not UI_BRAT_PATH.exists():
        _stop(f"{UI_BRAT_PATH} не найден.")

    text = UI_BRAT_PATH.read_text(encoding="utf-8")
    if '"хранитель_маяка"' in text and MARKER in text:
        print("✓ уже добавлено — патч уже применён.")
        return

    n = text.count(OLD_TIPY)
    if n == 0:
        _stop("якорь не найден — форма «Роль» изменилась с 29.07, "
              "нужна ручная сверка.")
    if n > 1:
        _stop(f"якорь встретился {n} раз — должен быть один.")

    new_text = text.replace(OLD_TIPY, NEW_TIPY, 1)

    bak = UI_BRAT_PATH.with_suffix(".py.bak_rol_mayaka")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    UI_BRAT_PATH.write_text(new_text, encoding="utf-8")

    print(f"✓ бэкап: {bak.name}")
    print(f"✓ записано: {UI_BRAT_PATH}")
    print()
    print("Готово. В форме «Роль» появился пункт «хранитель_маяка» —")
    print("выбери Софию → тип «хранитель_маяка» → назначить. Полей")
    print("Цех/Слот/Фраза не будет, только подтверждение (это пост).")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
