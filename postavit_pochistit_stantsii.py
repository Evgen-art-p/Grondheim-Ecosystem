# -*- coding: utf-8 -*-
# POCHISTIT_STANTSII_V_PAMYATI_V1
"""
Слово Шефа (05.09): «чистим всё, что реально влияет». Станции
(Брут/Авантюрист/Консерватор) убраны из кода и знаний патчем
vyrezat_klichki.py (04.09), но в ЛИЧНОЙ ПАМЯТИ жителей — resonance и
archive — остались стенограммы разговоров, где житель во время учёбы
в Академии (когда станции ещё существовали) говорил от лица станции
или приписывал СВОЙ вывод другому жителю.

Это не дневник места (diary_A0*.jsonl) — тот уже безопасен: `_moi_sobytiya`
в мозгах отсеивает всё неподписанное или подписанное чужим именем.
Это личный архив ЖИТЕЛЯ (жители/ковчег/{имя}/{archive,resonance}) — его
поднимает `vspomnit_slotom`, когда житель сам просит вспомнить
(MEMORY_REQUEST). Тут фильтра по подписи нет, и порча реально всплывает.

НЕ трогает строчные «авантюрист по натуре» — это слово о характере,
не о станции, и переписывать чужую личность не наше дело.

Запускать из корня репозитория:
    python postavit_pochistit_stantsii.py

Идемпотентен: заменённый текст в файле не совпадёт с ANCHOR повторно.
Создаёт .bak_stancii перед первой правкой каждого файла.
"""
from __future__ import annotations
from pathlib import Path

# (относительный путь от корня репо, старый текст, новый текст)
ZAMENY = [
    (
        "GRONDHEIM_CITY/жители/ковчег/Илья/archive/archive.jsonl",
        "сначала я (Авантюрист) на конце C, потом Вася на конце волны 2, "
        "потом Ганс/Брут на пробое фрактала",
        "сначала вход на конце C, потом на конце волны 2, "
        "потом на пробое фрактала",
    ),
    (
        "GRONDHEIM_CITY/жители/ковчег/Илья/archive/archive.jsonl",
        "мы, авантюристы, входим первыми на этом самом конце C, следом "
        "Вася на конце волны 2, и уж потом Ганс с Брутом на пробое фрактала",
        "входим первыми на этом самом конце C, следом на конце волны 2, "
        "и уж потом на пробое фрактала",
    ),
    (
        "GRONDHEIM_CITY/жители/ковчег/Илья/resonance/event_log.jsonl",
        "Это мой способ быть Авантюристом, но с головой на плечах.",
        "Это мой способ быть собой, но с головой на плечах.",
    ),
    (
        "GRONDHEIM_CITY/жители/ковчег/Илья/resonance/event_log.jsonl",
        "В болото я не лезу — меня Брут научил.",
        "В болото я не лезу — сам для себя это понял.",
    ),
]


def main() -> None:
    root = Path(__file__).resolve().parent
    tronutye = set()
    for rel, old, new in ZAMENY:
        path = root / rel
        if not path.exists():
            print(f"НЕТ ФАЙЛА: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if old not in text:
            print(f"уже чисто (или не найдено): {rel} :: {old[:40]}...")
            continue
        if path not in tronutye:
            bak = path.with_suffix(path.suffix + ".bak_stancii")
            if not bak.exists():
                bak.write_text(text, encoding="utf-8")
            tronutye.add(path)
            text = path.read_text(encoding="utf-8") if bak.exists() else text
        # перечитываем на случай нескольких замен в одном файле подряд
        current = path.read_text(encoding="utf-8")
        if old in current:
            path.write_text(current.replace(old, new, 1), encoding="utf-8")
            print(f"ПОЧИЩЕНО: {rel} :: {old[:40]}...")


if __name__ == "__main__":
    main()

# POCHISTIT_STANTSII_V_PAMYATI_V1 - marker
