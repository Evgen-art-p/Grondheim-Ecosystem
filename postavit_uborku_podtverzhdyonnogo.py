# -*- coding: utf-8 -*-
# UBORKA_PODTVERZHDYONNOGO_V1
"""
Дополнение к uborshchik.py: тот распознаёт отработавшие патчи ПО
МАРКЕРУ, и трёх скриптов не узнал (маркер в них называется иначе, чем
он ищет), хотя они реально накатаны — сверено с живой репой в этом же
разговоре: vyrezat_klichki.py, ubrat_ac.py, vspomnit_metki_polya.py.
Остальные 14 в списке — «под вопросом» из отчёта uborshchik.py,
Шеф решил убрать (05.09), оставив на потом только Студию и ещё два.

Механика та же, что у uborshchik.py: НЕ удаляет, переносит в
_УБОРКА/{дата}/ с сохранением дорожек, манифест.json и КАК_ВЕРНУТЬ.txt
рядом. Идемпотентен по построению: второй раз файлов уже не будет на
месте — сообщит об этом честно и не упадёт.

Запускать из корня репозитория:
    python postavit_uborku_podtverzhdyonnogo.py           — сухой прогон
    python postavit_uborku_podtverzhdyonnogo.py --ubrat   — перенос
"""
from __future__ import annotations
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

SPISOK = [
    "bumaga_a01.py",
    "bumaga_a03.py",
    "bumaga_a05.py",
    "bumagi_a02_a04.py",
    "chistaya_pamyat.py",
    "gde_vhodyat.py",
    "kontora_ne_kartridzh.py",
    "mesta_zavodyatsya_sami.py",
    "odin_v_odin.py",
    "pochinit_dubli_mest.py",
    "pochinit_etazh_v_barah.py",
    "pokazat_puzyri.py",
    "ubrat_ac.py",
    "ubrat_ac_iz_znaniy.py",
    "ubrat_mertvyy_kod_03_09.py",
    "vspomnit_metki_polya.py",
    "vyrezat_klichki.py",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ubrat", action="store_true",
                     help="реально перенести (по умолчанию — сухой показ)")
    a = ap.parse_args()

    koren = Path(__file__).resolve().parent
    chulan = koren / "_УБОРКА"

    naydeny = []
    for imya in SPISOK:
        p = koren / imya
        if p.exists():
            naydeny.append(p)
        else:
            print(f"уже нет на месте (убрано раньше?): {imya}")

    print(f"К переносу: {len(naydeny)} из {len(SPISOK)}")
    if not naydeny:
        return 0

    if not a.ubrat:
        for p in naydeny:
            print(f"   {p.name}  ({p.stat().st_size} байт)")
        print("\nЭто был показ. Перенести по-настоящему:")
        print("    python postavit_uborku_podtverzhdyonnogo.py --ubrat")
        return 0

    kuda = chulan / datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest = []
    for p in naydeny:
        otn = p.relative_to(koren)
        cel = kuda / otn
        cel.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(cel))
        manifest.append({"откуда": str(otn), "куда": str(cel.relative_to(koren)),
                          "почему": "решение Шефа 05.09 — мёртвый корневой "
                                    "скрипт, три подтверждены отработавшими "
                                    "патчами вручную, не по маркеру"})
        print(f"перенесено: {otn}")

    kuda.mkdir(parents=True, exist_ok=True)
    (kuda / "манифест.json").write_text(
        json.dumps({"когда": datetime.now().isoformat(timespec="seconds"),
                    "всего": len(manifest), "файлы": manifest},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (kuda / "КАК_ВЕРНУТЬ.txt").write_text(
        "Ничего не удалено — всё лежит здесь, дорожки сохранены.\n"
        "Вернуть один файл: скопировать его отсюда обратно по пути\n"
        "из поля «откуда» в манифест.json.\n"
        "Вернуть всё: скопировать содержимое этой папки в корень репо\n"
        "с сохранением дорожек (манифест и эту записку не копировать).\n",
        encoding="utf-8")
    print(f"\nГотово. Манифест: {kuda / 'манифест.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# UBORKA_PODTVERZHDYONNOGO_V1 - marker
