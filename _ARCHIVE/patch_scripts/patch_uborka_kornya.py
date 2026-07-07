# -*- coding: utf-8 -*-
"""
PATCH: УБОРКА КОРНЯ — мусор и отработавшие разовые скрипты в _ARCHIVE/.
Маркер: UBORKA_KORNYA_V1

НИЧЕГО НЕ УДАЛЯЕТ. Только переносит (shutil.move) в _ARCHIVE/, с той же
структурой имён — если что-то понадобится, оно там, не потеряно.

ЧТО УБИРАЕМ и почему (сверено по факту, не на глаз):

  ЯВНЫЙ МУСОР (дубликаты, уже применены инсталлятором):
    _payload_main.py           — копия main.py, тот же маркер в шапке
                                  (PATCH_REAL_ZHIZN_APPLIED и т.д.),
                                  уже перенесена в main.py
    _payload_ui_grondheim.py   — копия ГОРОД/ui_grondheim.py, применена
    kalibrovka_birzha.py       — источник для установки в
                                  Биржа/kalibrovka.py (мой огрех в
                                  патче), больше не читается никем

  РАЗОВЫЕ СКРИПТЫ (своё дело сделали):
    fix_passport_json.py   — чинил паспорт Локи, применён
    diag.py                 — диагностика скана жителей, разовая
    diag_zhiteli.py          — диагностика list_zhiteli(), разовая

  12 ПАТЧ-СКРИПТОВ (все идемпотентны, все накатаны) — по прецеденту
  старого города ("батники — костыли, выбрасывай", мёртвые файлы
  в _OLD/): patch_birzha_baza.py, patch_kalibrovka.py,
  patch_karta_zhiteli.py, patch_karta_cvet.py, patch_karta_klik_zhitel.py,
  patch_karta_klik_ne_drag.py, patch_zhitel_tekushaya_lokacia.py,
  patch_zhitel_panel.py, patch_zhitel_loc_vlevo.py,
  patch_zhitel_karta_big.py, patch_zhitel_zaryad_bipolar.py,
  patch_zhitel_optika_slova.py

НЕ ТРОГАЕМ (живые, постоянные):
  kalibrovka_core.py, sostoyanie.py — мозг, живут в корне навсегда
  main.py, .env.example, .gitignore, .gitattributes — стоят как есть
  ЛЕТОПИСЬ_ГРОНДХЕЙМА.md, ЧЕРТЁЖ_ЕДИНИЦЫ.md — документы
  Биржа/, Брат/, ГОРОД/, жители/, GRONDHEIM_CITY/, 00_REGISTRY_NFT/ — код и данные

Идемпотентен: файла уже нет в корне (перенесён раньше) → тихо пропускаем.
Сам патч-скрипт себя тоже унесёт в архив последним, после отчёта.

Запуск из корня репо:  python patch_uborka_kornya.py
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
ARCHIVE = REPO / "_ARCHIVE"

YAVNYI_MUSOR = [
    "_payload_main.py",
    "_payload_ui_grondheim.py",
    "kalibrovka_birzha.py",
]

RAZOVYE_SKRIPTY = [
    "fix_passport_json.py",
    "diag.py",
    "diag_zhiteli.py",
]

PATCH_SKRIPTY = [
    "patch_birzha_baza.py",
    "patch_kalibrovka.py",
    "patch_karta_zhiteli.py",
    "patch_karta_cvet.py",
    "patch_karta_klik_zhitel.py",
    "patch_karta_klik_ne_drag.py",
    "patch_zhitel_tekushaya_lokacia.py",
    "patch_zhitel_panel.py",
    "patch_zhitel_loc_vlevo.py",
    "patch_zhitel_karta_big.py",
    "patch_zhitel_zaryad_bipolar.py",
    "patch_zhitel_optika_slova.py",
]


def _perenesti(imya: str, podpapka: str, itog: dict):
    src = REPO / imya
    if not src.exists():
        itog["уже_нет"].append(imya)
        return
    dst_dir = ARCHIVE / podpapka
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / imya
    if dst.exists():
        # не перезаписываем архив молча — добавляем метку времени
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dst = dst_dir / f"{stamp}__{imya}"
    shutil.move(str(src), str(dst))
    itog["перенесено"].append(f"{imya} → _ARCHIVE/{podpapka}/{dst.name}")


def install():
    print("═══ PATCH UBORKA_KORNYA_V1 — уборка корня в _ARCHIVE/ ═══")
    print(f"репо: {REPO}")
    print("(ничего не удаляется — только переносится)\n")

    itog = {"перенесено": [], "уже_нет": []}

    print("── явный мусор (дубликаты) ──")
    for f in YAVNYI_MUSOR:
        _perenesti(f, "мусор", itog)

    print("── разовые скрипты (дело сделано) ──")
    for f in RAZOVYE_SKRIPTY:
        _perenesti(f, "разовые_скрипты", itog)

    print("── патч-скрипты (все накатаны, идемпотентны) ──")
    for f in PATCH_SKRIPTY:
        _perenesti(f, "patch_scripts", itog)

    for line in itog["перенесено"]:
        print(f"  ✔ {line}")
    for name in itog["уже_нет"]:
        print(f"  ○ уже отсутствует (перенесён раньше): {name}")

    print(f"\n═══ ИТОГ: перенесено {len(itog['перенесено'])}, "
          f"пропущено {len(itog['уже_нет'])} ═══")
    print(f"Всё лежит в: {ARCHIVE.relative_to(REPO)}/")
    print("Корень репо чист. Ничего не потеряно — если что-то нужно")
    print("вернуть, оно там же, просто в _ARCHIVE/.")

    # себя — последним, после отчёта
    self_path = Path(__file__).resolve()
    try:
        self_dst_dir = ARCHIVE / "patch_scripts"
        self_dst_dir.mkdir(parents=True, exist_ok=True)
        self_dst = self_dst_dir / self_path.name
        if not self_dst.exists():
            shutil.move(str(self_path), str(self_dst))
            print(f"  ✔ {self_path.name} → _ARCHIVE/patch_scripts/ (сам себя убрал)")
    except Exception as e:
        print(f"  ⚠ себя не унёс ({e}) — не страшно, можешь убрать руками")

    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
