# -*- coding: utf-8 -*-
# NE_UGLUBLYATSYA_V1
"""
Слово Шефа (05.09, живой разговор): бесконечный спуск по этажам в
поисках уверенности — та же болезнь, что мониторинг каждого бара по
времени, только по вертикали. Рынок нелинейный, ясности не будет ни
на каком этаже; увидел этаж — сравнил с тем, как выглядит рабочая
ситуация, — решил.

Запускать из корня репозитория:
    python postavit_ne_uglublyatsya.py

Идемпотентен: если абзац уже стоит (проверка по уникальной фразе, не
по заголовку — урок 05.09), скрипт молчит и ничего не трогает.
"""
from __future__ import annotations
from pathlib import Path

MARKER_PHRASE = "Не углубляться бесконечно"

ANCHOR = (
    "Не предсказывай исход — это грубая ошибка. Думай, что рынок делает\n"
    "СЕЙЧАС и куда идёт сейчас, иди с ценой взглядом. Не мониторь каждый\n"
    "бар последовательно — только если некрон звякнул."
)

INSERT = (
    ANCHOR
    + "\n\n"
    + "**Не углубляться бесконечно.** Увидел этаж — сравнил с тем, как\n"
      "выглядит рабочая ситуация, — решил. Спуск ниже — это не поиск\n"
      "уверенности, а взгляд на свой масштаб, если решил работать глубже.\n"
      "Бесконечное хождение по этажам в поисках однозначности — та же\n"
      "болезнь, что мониторинг каждого бара, только по вертикали: рынок\n"
      "нелинейный, ясности не будет ни на каком этаже."
)

SLOTS = ["A06", "A07", "A08"]
REL_PATH = "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/{slot}/промпт.md"


def patch_one(path: Path) -> str:
    if not path.exists():
        return f"НЕТ ФАЙЛА: {path}"
    text = path.read_text(encoding="utf-8")
    if MARKER_PHRASE in text:
        return f"уже стоит: {path}"
    if text.count(ANCHOR) != 1:
        return f"ЯКОРЬ НЕ НАЙДЕН (не тронуто): {path}"
    bak = path.with_suffix(path.suffix + ".bak_uglublyatsya")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    new_text = text.replace(ANCHOR, INSERT, 1)
    path.write_text(new_text, encoding="utf-8")
    return f"ПРИМЕНЁН: {path}"


def main() -> None:
    root = Path(__file__).resolve().parent
    for slot in SLOTS:
        p = root / REL_PATH.format(slot=slot)
        print(patch_one(p))


if __name__ == "__main__":
    main()

# NE_UGLUBLYATSYA_V1 - marker
