# -*- coding: utf-8 -*-
# SVOY_VYBOR_U_KAZHDOGO_V1
"""
ЕДИНЫЙ ВЫБОР СНЯТ · у трейдера свой, и он запоминается

Слово Шефа 10.09: «единый выбор убери. Выбор трейдера запоминается,
они не зависят».

ЧТО БЫЛО. `vybor.rabota_dlya` сперва спрашивала ЭКРАН, и то, что
выбрал Шеф, становилось работой трейдера. Отсюда сегодняшнее:
кабинет показывает D1, а прогон идёт по M5 — экран держал прошлое
значение. Лечить это записью в экран было бы неверно: тогда любой
взгляд Шефа перекладывал бы работу всем троим разом.

ЧТО СТАНОВИТСЯ. Экран — это экран Шефа: где он сам сейчас смотрит.
Работа трейдера — его собственная и запомненная:

    инструмент — назначенный ему (пост, метка)
    этаж       — тот, что он себе записал; не записал — комфортный

Они больше не зависят друг от друга. Шеф смотрит D1 — трейдер
работает там, где работал.

ЧТО ПРАВИТСЯ:

 1. `Биржа/vybor.py` — блок «сперва ЭКРАН» снимается целиком.
 2. `Биржа/ui_torg.py` — клик по этажу в полке ЗАПОМИНАЕТ этаж тому
    трейдеру, которого Шеф сейчас выбрал (и только ему). Никого не
    выбрал — просто смотрит, ничья работа не меняется.

ПОБОЧНО: это возвращает смысл кнопке выбора. Раньше клик назначал
один инструмент, а этаж молча брался «от комфорта» — то есть выбрать
этаж трейдеру было нечем.

БЕЗОПАСНОСТЬ: .bak_svoy, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_svoy_vybor.py --suho
    python postavit_svoy_vybor.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "SVOY_VYBOR_U_KAZHDOGO_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
VYBOR = _REPO / "Биржа" / "vybor.py"
TORG = _REPO / "Биржа" / "ui_torg.py"

NACHALO_EKRANA = "    # EDINYY_VYBOR_V1: сперва ЭКРАН."
KONEC_EKRANA = "    instr, otk_i = instrument_dlya(ceh, slot)"

ZAMENA_EKRANA = '''    # SVOY_VYBOR_U_KAZHDOGO_V1: блок «сперва ЭКРАН» снят по слову
    # Шефа: «единый выбор убери, выбор трейдера запоминается, они не
    # зависят». Экран — это где смотрит Шеф. Работа трейдера — своя:
    # назначенный инструмент и ЗАПОМНЕННЫЙ им этаж.

'''

STAROE_TORG = '''        state["active_asset"] = i
        a = assets[i]
        slot = _slot_agenta(state.get("active_agent", ""))
        if slot:
            try:
                from vybor import naznachit as _nazn
                _nazn(tseh_id, slot, a["symbol"])'''

NOVOE_TORG = '''        state["active_asset"] = i
        a = assets[i]
        slot = _slot_agenta(state.get("active_agent", ""))
        if slot:
            try:
                from vybor import naznachit as _nazn
                _nazn(tseh_id, slot, a["symbol"])
                # SVOY_VYBOR_U_KAZHDOGO_V1: запоминаем и ЭТАЖ — тому,
                # кого Шеф сейчас выбрал, и только ему. Раньше клик
                # назначал один инструмент, а этаж молча брался «от
                # комфорта»: выбрать этаж трейдеру было нечем.
                try:
                    from vybor import zapisat_etazh as _zap
                    _zap(tseh_id, slot, a["symbol"], a["timeframe"])
                except Exception as _e_et:
                    print(f"[ВЫБОР] этаж не запомнился ({_e_et})")'''


def _pravka(p: Path, staroe: str, novoe: str, imya: str) -> int:
    if not p.exists():
        print(f"  {imya}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {imya}: уже стоит")
        return 0
    if txt.count(staroe) != 1:
        print(f"  {imya}: ОТКАЗ — якорь встречается {txt.count(staroe)} раз(а)")
        return 0
    novy = txt.replace(staroe, novoe, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {imya}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_svoy"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {imya}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("СВОЙ ВЫБОР У КАЖДОГО" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    vsego = 0

    print("1. ВЫБОР — экран больше не решает за трейдера:")
    if not VYBOR.exists():
        print("  vybor.py: файла нет")
    else:
        txt = VYBOR.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  vybor.py: уже стоит")
        elif NACHALO_EKRANA not in txt or KONEC_EKRANA not in txt:
            print("  vybor.py: ОТКАЗ — блок экрана не нашёлся")
        else:
            n1 = txt.index(NACHALO_EKRANA)
            n2 = txt.index(KONEC_EKRANA, n1)
            novy = txt[:n1] + ZAMENA_EKRANA + txt[n2:]
            try:
                ast.parse(novy)
                if not SUHO:
                    shutil.copy2(VYBOR, VYBOR.with_suffix(".py.bak_svoy"))
                    VYBOR.write_text(novy, encoding="utf-8")
                print(f"  vybor.py: {'готов' if SUHO else 'поправлен'}")
                vsego += 1
            except SyntaxError as e:
                print(f"  vybor.py: ОТКАЗ — синтаксис сломан ({e})")

    print()
    print("2. КАБИНЕТ — клик запоминает этаж выбранному трейдеру:")
    vsego += _pravka(TORG, STAROE_TORG, NOVOE_TORG, "ui_torg.py")

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_svoy")
    print("Экран — Шефа. Работа — трейдера, своя и запомненная.")
    print()


if __name__ == "__main__":
    main()
