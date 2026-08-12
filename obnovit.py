#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# OBNOVIT_GOROD_V1
"""
ОБНОВИТЬ ГОРОД — накатить всё, что лежит рядом, в правильном порядке.

Двойной щелчок по `ОБНОВИТЬ.bat`, из корня города.

    python obnovit.py            посмотреть, что будет
    python obnovit.py --sdelat   накатить

ЗАЧЕМ

    Патчи копятся, и порядок между ними важен: лесенка кладётся раньше
    инструмента, инструмент — раньше панели. Держать это в голове
    незачем.

    Скрипт берёт только те файлы, что реально лежат рядом, и зовёт их
    по очереди. Каждый сам решает, надо ли что-то делать: уже накатан —
    скажет «уже накатано» и пропустит. Гонять можно сколько угодно.

    Ничего не скачивает и не удаляет. Каждый патч, как обычно, кладёт
    копию правленого файла рядом с собой.
"""
import argparse
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent

# порядок важен: снизу вверх по зависимостям
PORYADOK = [
    # ── основа ──
    ("patch_treyder_ozhivit.py", "оживить трейдеров"),
    ("postavit_standart_raboty.py", "стандарт работы"),
    ("postavit_stranicu_raboty.py", "страница работы"),
    ("patch_lokaciya_daet_mesta.py", "места даёт локация"),
    ("patch_korotkiy_blank.py", "короткий бланк"),
    ("patch_lichnoe_uezzhaet.py", "личное уезжает с жителем"),
    # ── кабинет ──
    ("patch_kabinet_vzglyad.py", "взгляд"),
    ("patch_kadr_i_vakansiya.py", "свой кадр, пустое место молчит"),
    ("patch_kadr_na_ves_kvadrat.py", "кадр на всю клетку"),
    ("patch_razgovor_so_stolom.py", "разговор со столом"),
    ("patch_znaniya_v_razgovore.py", "знания в разговор"),
    ("patch_glaz_ne_taratorit.py", "глаз не тараторит"),
    ("patch_zovu_po_imeni.py", "зовёшь по имени"),
    ("patch_kto_ty_i_kto_ya.py", "кто ты и кто я"),
    ("patch_gemini_po_umolchaniyu.py", "модель со зрением"),
    # ── трейдер решает сам ──
    ("patch_odna_bumaga.py", "одна бумага на троих"),
    ("postavit_vybor_metkoy.py", "выбор входа меткой"),
    ("patch_dvizhok_ne_reshaet.py", "движок не решает"),
    ("patch_vybor_svoy.py", "выбор свой, не книжный"),
    ("patch_lesenka_treydera.py", "лесенка этажей"),
    ("patch_instrument_treydera.py", "инструмент: задать или на выбор"),
    ("patch_panel_treydera.py", "панель принадлежит трейдеру"),
    # ── котировки и вахта ──
    ("patch_polka_iz_terminala.py", "полка из терминала"),
    ("patch_svyaz_s_terminalom.py", "связь с терминалом"),
    ("patch_okno_moglo_uyti.py", "окно могло уйти"),
    ("patch_vahta.py", "вахта"),
    ("patch_vahta_gorodskaya.py", "вахта городская"),
    ("patch_svoyo_okno.py", "своё окно каждой двери"),
    # ── архив ──
    ("postavit_pamyat.py", "памяти города"),
    ("postavit_ruki_arkhivariusa.py", "руки архивариуса"),
    # ── остров ──
    ("postavit_glavnuyu.py", "главная острова"),
    ("postavit_zastroyshchika.py", "застройщик"),
    ("postavit_perevozku.py", "перевозка кнопкой"),
]


def skazat(s=""):
    print(s, flush=True)


def kak_zvat(put: Path, sdelat: bool) -> list:
    """Патчи писались в разное время: у ранних накат по умолчанию и
    --suho для показа, у поздних наоборот. Смотрим в сам файл."""
    try:
        tekst = put.read_text(encoding="utf-8", errors="replace")
    except Exception:
        tekst = ""
    novyy = "--sdelat" in tekst
    if sdelat:
        return ["--sdelat"] if novyy else []
    return [] if novyy else ["--suho"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()

    skazat("=" * 64)
    skazat("ОБНОВИТЬ ГОРОД" + ("" if a.sdelat else "   [ПОКАЗ — ничего не меняю]"))
    skazat("=" * 64)

    est = [(f, opis) for f, opis in PORYADOK if (KOREN / f).exists()]
    net = [f for f, _ in PORYADOK if not (KOREN / f).exists()]

    if not est:
        skazat("\nx рядом нет ни одного патча.")
        skazat("  Положи их в эту папку и запусти снова.")
        return 1

    skazat(f"\nнашёл рядом: {len(est)}")
    if net:
        skazat(f"нет рядом (и не надо, если не нужны): {len(net)}")

    horosho, ploho = [], []
    for imya, opis in est:
        skazat("\n" + "─" * 64)
        skazat(f"▶ {opis}   [{imya}]")
        skazat("─" * 64)
        r = subprocess.run(
            [sys.executable, str(KOREN / imya), *kak_zvat(KOREN / imya, a.sdelat)],
            cwd=str(KOREN))
        (horosho if r.returncode == 0 else ploho).append((imya, opis))

    skazat("\n" + "=" * 64)
    skazat(f"прошло: {len(horosho)}   не легло: {len(ploho)}")
    if ploho:
        skazat("\nне легли:")
        for imya, opis in ploho:
            skazat(f"   · {opis}  [{imya}]")
        skazat("\nЭто не поломка: чаще всего патч уже накатан или не нужен")
        skazat("этому берегу. Если сомневаешься — покажи это окно Брату.")
    if not a.sdelat:
        skazat("\nЭто был показ. Накатить по-настоящему:")
        skazat("    python obnovit.py --sdelat")
        skazat("(или запусти ОБНОВИТЬ.bat и ответь «да»)")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32" and "--sdelat" not in sys.argv:
        try:
            otvet = input("Накатить по-настоящему? [Enter — только показ, "
                          "да — накатить]: ").strip().lower()
            if otvet in ("да", "y", "yes", "д"):
                sys.argv.append("--sdelat")
        except Exception:
            pass
    try:
        kod = main()
    except Exception as e:
        skazat(f"\nx что-то пошло не так: {type(e).__name__}: {e}")
        kod = 1
    if sys.platform == "win32":
        try:
            input("\nEnter — закрыть окно.")
        except Exception:
            pass
    sys.exit(kod)
