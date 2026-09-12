# -*- coding: utf-8 -*-
# ubrat_alligator_s_kadra_A06.py — линии Аллигатора убираются со СВОЕГО
# кадра A06 (тот, что подкладывается сам, без просьбы рукой) и с
# панели, которую видит Шеф.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папками Биржа/ и GRONDHEIM_CITY/).
# Запуск из PowerShell, из корня:   python ubrat_alligator_s_kadra_A06.py
#
# Зачем: рукой добытые кадры (pokazat_etazh, возврат домой, стол на
# этаже) уже рисуются без линий — patch KADR_BEZ_ALLIGATORA_V1. Но
# кадр, который сам ложится к КАЖДОМУ взгляду трейдера (в мозге —
# без запроса руки), линии рисовал по-прежнему: `grafik.kadr()` без
# аргумента linii=False рисует их по умолчанию. Значит самая частая
# картинка — как раз с линиями, отсюда и утечка Аллигатора в ответы
# первого уровня, даже когда в тексте про него ничего нет.
#
# Что правит:
#   1-2. GRONDHEIM_CITY/.../слоты/A06/мозг.py — оба места, где
#        подкладывается свой кадр (`_glaz` и `_glaz_s_rukами`).
#   3.   Биржа/ui_torg.py — панель «Взгляд», которую видит Шеф;
#        меняется вместе с трейдером, чтобы оба смотрели на одну
#        картинку, как и было задумано изначально.
#
# ВАЖНО: правка панели в ui_torg.py — на ОБЩИЙ код кабинета, не на
# файл одного слота. Она уберёт линии с панели для ЛЮБОГО выбранного
# места (в т.ч. A07/A08), не только для A06, — панель одна на троих.
# Если это нежелательно, отвечай "нет" на этот пункт и запускай без
# него (см. флаг --bez-paneli ниже).
#
# Ничего не удаляет. Перед правкой кладёт рядом копию файла с
# хвостом .bak_alligator_s_kadra. Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent

MOZG_A06 = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" /
            "торговый_хаос" / "слоты" / "A06" / "мозг.py")
UI = KOREN / "Биржа" / "ui_torg.py"

BEZ_PANELI = "--bez-paneli" in sys.argv


def _s_novoy_strokoy(put) -> str:
    with open(put, "r", encoding="utf-8", newline="") as f:
        return f.read()


def _zapisat(put, tekst: str) -> None:
    with open(put, "w", encoding="utf-8", newline="") as f:
        f.write(tekst)


def main() -> int:
    sdelano, uzhe, ne_nashlos, net_fayla = 0, 0, 0, 0

    # ── 1-2. мозг.py A06 — свой кадр без линий ──────────────────────
    if not MOZG_A06.exists():
        print(f"✗ нет файла: {MOZG_A06}")
        net_fayla += 1
    else:
        tekst = _s_novoy_strokoy(MOZG_A06)
        crlf = "\r\n" in tekst
        ishodnyy = tekst

        bylo = "put = grafik.kadr(symbol, timeframe)"
        stalo = ("put = grafik.kadr(symbol, timeframe, linii=False)  "
                 "# KADR_BEZ_ALLIGATORA_V1")

        b = bylo.replace("\n", "\r\n") if crlf else bylo
        s = stalo.replace("\n", "\r\n") if crlf else stalo

        chislo_bylo = tekst.count(b)
        chislo_stalo = tekst.count(s)

        if chislo_stalo >= 2:
            print("· уже починено — свой кадр A06 без линий (оба места)")
            uzhe += 1
        elif chislo_bylo == 2:
            tekst = tekst.replace(b, s)
            print("✓ свой кадр A06 без линий (2 места: свой взгляд "
                  "и взгляд с руками)")
            sdelano += 1
        elif chislo_bylo == 1 and chislo_stalo == 1:
            tekst = tekst.replace(b, s)
            print("✓ свой кадр A06 без линий (второе из двух мест "
                  "было уже починено раньше)")
            sdelano += 1
        else:
            print(f"✗ не нашёл ожидаемые два места в {MOZG_A06.name} "
                  f"(нашёл {chislo_bylo} старых, {chislo_stalo} новых)")
            ne_nashlos += 1

        if tekst != ishodnyy:
            kopiya = MOZG_A06.with_suffix(MOZG_A06.suffix
                                           + ".bak_alligator_s_kadra")
            if not kopiya.exists():
                shutil.copy2(MOZG_A06, kopiya)
                print(f"  (копия старого: {kopiya.name})")
            _zapisat(MOZG_A06, tekst)

    # ── 3. панель ui_torg.py ─────────────────────────────────────────
    if BEZ_PANELI:
        print("· панель ui_torg.py пропущена (--bez-paneli)")
    elif not UI.exists():
        print(f"✗ нет файла: {UI}")
        net_fayla += 1
    else:
        tekst = _s_novoy_strokoy(UI)
        crlf = "\r\n" in tekst
        ishodnyy = tekst

        bylo = (
            "                import asyncio\n"
            "                _loop = asyncio.get_event_loop()\n"
            "                p = await _loop.run_in_executor(\n"
            "                    None, grafik.kadr, symbol, tf)\n"
        )
        stalo = (
            "                import asyncio\n"
            "                import functools\n"
            "                _loop = asyncio.get_event_loop()\n"
            "                # KADR_BEZ_ALLIGATORA_V1: панель показывает\n"
            "                # то же, что видит трейдер — без линий.\n"
            "                p = await _loop.run_in_executor(\n"
            "                    None, functools.partial(\n"
            "                        grafik.kadr, symbol, tf, linii=False))\n"
        )

        b = bylo.replace("\n", "\r\n") if crlf else bylo
        s = stalo.replace("\n", "\r\n") if crlf else stalo

        if b in tekst:
            tekst = tekst.replace(b, s, 1)
            print("✓ панель ui_torg.py: без линий Аллигатора")
            sdelano += 1
        elif s in tekst:
            print("· уже починено — панель ui_torg.py")
            uzhe += 1
        else:
            print("✗ не нашёл место в панели ui_torg.py")
            ne_nashlos += 1

        if tekst != ishodnyy:
            kopiya = UI.with_suffix(UI.suffix + ".bak_alligator_s_kadra")
            if not kopiya.exists():
                shutil.copy2(UI, kopiya)
                print(f"  (копия старого: {kopiya.name})")
            _zapisat(UI, tekst)

    print()
    print(f"ИТОГ: починено {sdelano}, было уже в порядке {uzhe}, "
          f"не нашлось мест {ne_nashlos}, файлов не найдено {net_fayla}")
    if ne_nashlos or net_fayla:
        print("Если что-то не нашлось — скажи Брату, поправим по месту.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
