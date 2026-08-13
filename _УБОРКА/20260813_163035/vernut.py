#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VERNUT_KAK_BYLO_V1
"""
ВЕРНУТЬ КАК БЫЛО — откатить патч по его же копии.

Двойной щелчок по `ВЕРНУТЬ.bat`, из корня города.

ЗАЧЕМ

    Каждый патч перед правкой кладёт копию файла рядом с собой:
    `ui_torg.py.bak_panel`, `мозг.py.bak_lesenka` и так далее. Значит
    любой шаг можно отменить — надо только знать, какой файл откуда.

    Скрипт собирает все такие копии, показывает списком по патчам и
    возвращает те, что скажешь. Ничего не удаляет: то, что стоит
    сейчас, перед откатом само ложится копией `*.bak_otkat`.

КАК ПОЛЬЗОВАТЬСЯ

    Запустил — увидел пронумерованный список: какой патч, сколько
    файлов, когда накатан. Набрал номер (или несколько через запятую) —
    вернулось как было до него.

    Откатывать лучше с конца: последний накатанный — первый на откат.
    Скрипт так их и сортирует, свежие сверху.
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
NE_LEZEM = {".git", "__pycache__", "_УБОРКА", "_ARCHIVE", "_OLD",
            "_ПЕРЕЕЗД", "_ОТПРАВКА", "_ПРИБЫТИЕ"}

# по-человечески, чтобы не гадать по хвосту файла
IMENA = {
    "bak_panel": "панель принадлежит трейдеру",
    "bak_instrument": "инструмент: задать или на выбор",
    "bak_lesenka": "лесенка этажей",
    "bak_vybor_svoy": "выбор свой, не книжный",
    "bak_ne_reshaet": "движок не решает",
    "bak_vahta_gor": "вахта городская",
    "bak_vahta": "вахта",
    "bak_svyaz": "связь с терминалом",
    "bak_okno": "окно могло уйти",
    "bak_polka": "полка из терминала",
    "bak_svoyo_okno": "своё окно каждой двери",
    "bak_kto_ya": "кто ты и кто я",
    "bak_glaz": "глаз не тараторит",
    "bak_znaniya": "знания в разговор",
    "bak_razgovor": "разговор со столом",
    "bak_kvadrat": "кадр на всю клетку",
    "bak_vzglyad": "взгляд",
    "bak_gemini": "модель со зрением",
    "bak_odna_bumaga": "одна бумага на троих",
    "bak_vybor": "выбор входа меткой",
    "bak_lichnoe": "личное уезжает с жителем",
    "bak_korotkiy": "короткий бланк",
    "bak_lokaciya": "места даёт локация",
    "bak_otkat": "СНИМОК ПЕРЕД ОТКАТОМ",
}


def skazat(s=""):
    print(s, flush=True)


def sobrat() -> dict:
    """Все копии, разложенные по патчам."""
    po_patcham = {}
    for p in KOREN.rglob("*.bak_*"):
        if any(x in NE_LEZEM for x in p.parts):
            continue
        hvost = p.name.split(".bak_", 1)[-1]
        klyuch = "bak_" + hvost
        zhivoy = p.with_name(p.name.split(".bak_", 1)[0])
        if not zhivoy.exists():
            continue
        po_patcham.setdefault(klyuch, []).append((p, zhivoy))
    return po_patcham


def main() -> int:
    skazat("=" * 64)
    skazat("ВЕРНУТЬ КАК БЫЛО")
    skazat("=" * 64)

    po_patcham = sobrat()
    if not po_patcham:
        skazat("\nКопий рядом нет — откатывать нечего.")
        return 0

    # свежие сверху: по времени самой новой копии
    spisok = sorted(po_patcham.items(),
                    key=lambda kv: max(p.stat().st_mtime for p, _ in kv[1]),
                    reverse=True)

    skazat("\nЧто можно вернуть (свежее сверху):\n")
    for i, (klyuch, pary) in enumerate(spisok, 1):
        imya = IMENA.get(klyuch, klyuch)
        kogda = datetime.fromtimestamp(
            max(p.stat().st_mtime for p, _ in pary)).strftime("%d.%m %H:%M")
        skazat(f"  {i:>2}. {imya:<38} файлов {len(pary)}   {kogda}")
        for _, zhivoy in pary:
            skazat(f"      {zhivoy.relative_to(KOREN)}")

    skazat("\n  номер (или несколько через запятую) · Enter — ничего")
    try:
        otvet = input("\n> ").strip()
    except Exception:
        otvet = ""
    if not otvet:
        skazat("ничего не трогаю")
        return 0

    nomera = [int(x) for x in otvet.replace(" ", "").split(",")
              if x.isdigit() and 1 <= int(x) <= len(spisok)]
    if not nomera:
        skazat("не понял номер — ничего не трогаю")
        return 0

    skazat("")
    vsego = 0
    for n in nomera:
        klyuch, pary = spisok[n - 1]
        skazat(f"— {IMENA.get(klyuch, klyuch)}")
        for kopiya, zhivoy in pary:
            try:
                # то, что стоит сейчас, тоже сохраним — вдруг передумаешь
                snimok = zhivoy.with_suffix(zhivoy.suffix + ".bak_otkat")
                if not snimok.exists():
                    shutil.copy2(zhivoy, snimok)
                shutil.copy2(kopiya, zhivoy)
                skazat(f"   ✓ {zhivoy.relative_to(KOREN)}")
                vsego += 1
            except Exception as e:
                skazat(f"   x {zhivoy.relative_to(KOREN)}: {e}")

    skazat("\n" + "─" * 64)
    skazat(f"Вернул файлов: {vsego}")
    skazat("То, что стояло до отката, лежит рядом как *.bak_otkat.")
    skazat("Перезапусти город, чтобы увидеть.")
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
