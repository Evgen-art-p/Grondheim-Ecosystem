# -*- coding: utf-8 -*-
"""
PATCH_UBRAT_DUBL_ARKHIV_V1 — убрать дубль-черновик локации «Архив Города»

НАЙДЕНО (сверка диска 29.07): на диске одновременно две локации
«Архив Города» — 0006_GRONDHEIM_ARCHIVE (родилась 26.07, раньше) и
0015_GRONDHEIM_ARCHIVE (родилась той же ночью, на час позже). Паспорта
идентичны (тот же Creator_Seal_Hash), разница только в _image_path.
Код кабинета (Архив/ui_arkhiv.py, ZDANIE=...) смотрит на 0015 — она
живая. 0006 — черновик, никуда не подключён, мёртвый груз.

ЧТО ДЕЛАЕТ ЭТОТ ПАТЧ:
  1. Проверяет, что 0015_GRONDHEIM_ARCHIVE существует и читается —
     если нет, НИЧЕГО не трогает и честно останавливается (не удалять
     единственную живую копию по ошибке).
  2. Проверяет, что Архив/ui_arkhiv.py действительно ссылается на
     0015 (ищет строку ZDANIE = "0015_GRONDHEIM_ARCHIVE") — если код
     вдруг сверстан на другой ID, патч НЕ действует, требует ручной
     проверки.
  3. Если 0006_GRONDHEIM_ARCHIVE нет на диске — патч уже применён
     раньше или дубль убран руками. Идемпотентно, тихо выходит.
  4. Иначе — сверяет Creator_Seal_Hash 0006 и 0015 (должны совпасть,
     это и есть признак дубля, не двух разных архивов). Не совпало —
     ОСТАНОВКА, ничего не трогаем, это не тот случай.
  5. Бэкапит всю папку 0006_GRONDHEIM_ARCHIVE в zip
     (_АРХИВ_ЧИСТКИ/дубли_локаций/0006_GRONDHEIM_ARCHIVE_<штамп>.zip)
     — стереть можно всегда, а восстановить архив другого хода нет.
  6. Только после бэкапа — удаляет папку 0006_GRONDHEIM_ARCHIVE
     с диска.

Запуск из корня репозитория:
    python patch_ubrat_dubl_arkhiv.py

Ничего не переписывает молча — на каждом шаге печатает, что делает.
`шесть·проверено·до·корня`
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
LOKACII = REPO / "GRONDHEIM_CITY" / "локации"
STARAYA = LOKACII / "0006_GRONDHEIM_ARCHIVE"
ZHIVAYA = LOKACII / "0015_GRONDHEIM_ARCHIVE"
KABINET = REPO / "Архив" / "ui_arkhiv.py"
BEKAP_DIR = REPO / "_АРХИВ_ЧИСТКИ" / "дубли_локаций"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не тронуто. Патч НЕ применён.")
    sys.exit(1)


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        _stop(f"не прочитать {p}: {e}")
        return {}


def main() -> None:
    print("── PATCH_UBRAT_DUBL_ARKHIV_V1 ──")

    # 1. Живая копия должна существовать
    if not ZHIVAYA.exists():
        _stop(f"живой локации {ZHIVAYA.name} нет на диске — "
              f"без неё удалять 0006 нельзя, вдруг это единственная копия.")

    zhivoy_pasp = ZHIVAYA / "passport.json"
    if not zhivoy_pasp.exists():
        _stop(f"{zhivoy_pasp} отсутствует — живая локация неполная.")
    zhivoy_data = _read_json(zhivoy_pasp)
    print(f"✓ живая локация на месте: {ZHIVAYA.name}")

    # 2. Код кабинета должен смотреть на 0015
    if not KABINET.exists():
        _stop(f"{KABINET} не найден — не могу сверить, на что смотрит кабинет.")
    kod = KABINET.read_text(encoding="utf-8")
    if 'ZDANIE = "0015_GRONDHEIM_ARCHIVE"' not in kod:
        _stop("Архив/ui_arkhiv.py не ссылается на 0015_GRONDHEIM_ARCHIVE — "
              "код изменился с момента разбора, нужна ручная проверка Шефа.")
    print("✓ код кабинета (ZDANIE) подтверждён: ссылается на 0015")

    # 3. Идемпотентность — дубля уже может не быть
    if not STARAYA.exists():
        print(f"✓ {STARAYA.name} уже отсутствует на диске — патч уже применён "
              f"(или дубль убран руками). Делать нечего.")
        return

    # 4. Сверка, что это реально дубль, а не два разных архива
    staryy_pasp = STARAYA / "passport.json"
    if not staryy_pasp.exists():
        _stop(f"{staryy_pasp} отсутствует — не могу подтвердить, что "
              f"{STARAYA.name} это дубль, а не что-то другое.")
    staryy_data = _read_json(staryy_pasp)

    hash_zhivoy = zhivoy_data.get("_Creator_Seal_Hash")
    hash_staryy = staryy_data.get("_Creator_Seal_Hash")
    if not hash_zhivoy or not hash_staryy or hash_zhivoy != hash_staryy:
        _stop(f"_Creator_Seal_Hash не совпадает ({hash_staryy!r} vs "
              f"{hash_zhivoy!r}) — это не подтверждённый дубль, "
              f"нужна ручная проверка Шефа, прежде чем удалять.")
    print("✓ Creator_Seal_Hash совпадает — подтверждённый дубль-черновик")

    # 5. Бэкап в zip перед удалением
    BEKAP_DIR.mkdir(parents=True, exist_ok=True)
    shtamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    bekap_base = BEKAP_DIR / f"{STARAYA.name}_{shtamp}"
    zip_path = shutil.make_archive(str(bekap_base), "zip", root_dir=STARAYA)
    print(f"✓ бэкап сделан: {zip_path}")

    # 6. Удаление
    shutil.rmtree(STARAYA)
    print(f"✓ {STARAYA.name} удалена с диска.")
    print()
    print("Дубль убран. Живая локация Архива — 0015_GRONDHEIM_ARCHIVE.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
