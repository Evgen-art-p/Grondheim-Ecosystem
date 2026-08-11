#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VYBOR_POKAZAT_V1
"""
ЧЕЙ ВЫБОР — показать, что записано на самом деле.

Двойной щелчок по `ВЫБОР.bat`, из корня города.

ЗАЧЕМ

    Трейдер может СКАЗАТЬ «мой вход — первый откат». Это ещё ничего не
    значит: он мог прочитать это в книге минуту назад и назвать своим.
    Настоящий выбор — тот, что ЗАПИСАН меткой в доме человека, с датой.

    Скрипт лезет на диск и показывает по каждому месту: кто сидит, что
    у него записано, когда и сколько раз он передумывал. Ничего не
    меняет — только смотрит.

КАК ЧИТАТЬ

    «выбор записан» + дата   — настоящий, человек его носит;
    «метки нет»              — он берёт книжное и выдаёт за своё;
    один текст у двоих       — либо оба правда так решили, либо метка
                               легла не тому, и это уже поломка.
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
for p in (KOREN / "Биржа", KOREN / "ГОРОД", KOREN / "жители"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def skazat(s=""):
    print(s, flush=True)


def main() -> int:
    skazat("=" * 64)
    skazat("ЧЕЙ ВЫБОР")
    skazat("=" * 64)

    try:
        import vybor as V
    except Exception as e:
        skazat(f"x механизм выбора не поднялся: {e}")
        skazat("  (нужен Биржа/vybor.py — его кладёт postavit_vybor_metkoy)")
        return 1

    try:
        from cartridge_registry import resolve_para
    except Exception as e:
        skazat(f"x Закон Пары не поднялся: {e}")
        return 1

    ceh = "торговый_хаос"
    teksty = {}

    for slot in ("A06", "A07", "A08"):
        skazat(f"\n── {ceh} / {slot} " + "─" * 34)
        n = None
        try:
            n = resolve_para(ceh, slot)
        except Exception as e:
            skazat(f"   носитель не читается: {e}")
        if not n:
            skazat("   за столом никого — вакансия")
            continue

        imya = n.get("имя", "?")
        skazat(f"   сидит: {imya}   (дом: {n.get('папка','?')})")

        try:
            ist = V.istoriya(ceh, slot)
        except Exception as e:
            skazat(f"   метки не читаются: {e}")
            continue

        if not ist:
            skazat("   ВЫБОРА НЕТ — метки не записано.")
            skazat("   Значит всё, что он говорит про свой вход, взято из")
            skazat("   книги сейчас, а не решено им однажды.")
            continue

        posl = ist[-1]
        skazat(f"   ВЫБОР ЗАПИСАН: {posl.get('текст','')}")
        skazat(f"   когда: {posl.get('когда','?')}")
        if len(ist) > 1:
            skazat(f"   передумывал(а) раз: {len(ist) - 1}")
            for z in ist[:-1]:
                skazat(f"      было: {z.get('текст','')} "
                       f"({str(z.get('когда',''))[:16]})")
        teksty.setdefault(posl.get("текст", "").strip().lower(),
                          []).append(f"{imya} ({slot})")

    skazat("\n" + "─" * 64)
    sovpali = {t: kto for t, kto in teksty.items() if len(kto) > 1}
    if sovpali:
        skazat("! у разных людей ОДИН И ТОТ ЖЕ записанный выбор:")
        for t, kto in sovpali.items():
            skazat(f"   «{t}» — {', '.join(kto)}")
        skazat("  Либо оба правда так решили, либо метка легла не тому.")
        skazat("  Покажи это Брату — разберёт.")
    elif teksty:
        skazat("Записанные выборы у всех разные — как и должно быть.")
    else:
        skazat("Записанных выборов нет ни у кого.")
        skazat("Спроси каждого в кабинете Биржи: «какой у тебя вход и")
        skazat("почему именно он твой» — и пусть объявит строкой ВЫБОР.")
    return 0


if __name__ == "__main__":
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
