# -*- coding: utf-8 -*-
# KADR_K_KLYUCHU_V1
"""
ОДНА ПОБУДКА — ОДИН КАДР, СПРАВА

Слово Шефа 12.09: «кадры в чате не показывать, пусть там же справа,
и если он один, пусть выходит с ключом вместе».

КАК БЫЛО. Панель меняла картинку на КАЖДУЮ отрисовку — а их за один
вопрос две-три, и часть служебные. Пока Шеф читал ответ, панель
успевала уехать. Я на это ответил кадрами в ленте чата, но так вышло
шумно: под каждым ответом гроздь картинок.

КАК СТАНЕТ. Панель меняется РОВНО ОДИН раз за побудку — на том
кадре, который нарисован под вопрос. Служебные отрисовки её больше
не трогают. Из чата картинки убираются.

ЧТО ПРАВИТСЯ:

 · мозги A06/A07/A08 — крючок живого кадра кладёт на площадь только
   ПЕРВЫЙ кадр ответа (тот, что под вопрос), остальные копит молча;
 · Биржа/ui_torg.py — лента чата больше не рисует картинки.

Кадры никуда не пропадают: каждый по-прежнему сохраняется в папку
отчёта, и на странице отчёта видно всё — там им и место, там они не
мешают читать.

ТРЕБУЕТ: KADRY_V_CHATE_V1 (этот патч его и сворачивает).

КУДА КЛАСТЬ ЭТОТ ФАЙЛ: в корень репы, рядом с main.py.

БЕЗОПАСНОСТЬ: .bak_kadrklyuch, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python pochinit_kadr_k_klyuchu.py --suho
    python pochinit_kadr_k_klyuchu.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KADR_K_KLYUCHU_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
TORG = _REPO / "Биржа" / "ui_torg.py"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# ── мозг: на площадь — только первый кадр ответа ─────────────
STAROE_MOZG = '''            _t["zhivoy_kadr"] = {'''
NOVOE_MOZG = '''            # KADR_K_KLYUCHU_V1: панель меняем ОДИН раз за побудку —
            # на первом кадре ответа, том, что нарисован под вопрос.
            # Служебные отрисовки её больше не дёргают: Шеф читал
            # ответ, а картинка успевала уехать на следующее место.
            if len(_t.get("кадры_ответа") or []) > 1:
                _t["zhivoy_kadr"] = _t.get("zhivoy_kadr") or {}
                save_trading_state(_t)
                return
            _t["zhivoy_kadr"] = {'''

# ── кабинет: чат без картинок ────────────────────────────────
STAROE_TORG = '''                        _kadry = msg.get("кадры") or []
                        if _kadry:'''
NOVOE_TORG = '''                        # KADR_K_KLYUCHU_V1: в ленте картинок больше нет —
                        # кадр показывается справа, один на побудку.
                        # Все кадры места целы в папке отчёта и видны
                        # на странице отчёта, там им и место.
                        _kadry = []
                        if _kadry:'''


def _pravka_mozga(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0
    if "KADRY_V_CHATE_V1" not in txt:
        print(f"  {slot}: пропускаю — копилки кадров нет")
        return 0
    if txt.count(STAROE_MOZG) != 1:
        print(f"  {slot}: ОТКАЗ — якорь встречается "
              f"{txt.count(STAROE_MOZG)} раз(а)")
        return 0
    novy = txt.replace(STAROE_MOZG, NOVOE_MOZG, 1)
    novy = novy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_kadrklyuch"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("КАДР К КЛЮЧУ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    vsego = 0
    print("1. МОЗГИ — панель меняется раз за побудку:")
    if not SLOTY.exists():
        print("  слотов нет — запускать из корня репы")
    else:
        for s in ("A06", "A07", "A08"):
            vsego += _pravka_mozga(s)

    print()
    print("2. КАБИНЕТ — чат без картинок:")
    if not TORG.exists():
        print("  ui_torg.py: файла нет")
    else:
        txt = TORG.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  ui_torg.py: уже стоит")
        elif txt.count(STAROE_TORG) != 1:
            print(f"  ui_torg.py: ОТКАЗ — якорь встречается "
                  f"{txt.count(STAROE_TORG)} раз(а)")
        else:
            novy = txt.replace(STAROE_TORG, NOVOE_TORG, 1)
            try:
                ast.parse(novy)
                if not SUHO:
                    shutil.copy2(TORG, TORG.with_suffix(".py.bak_kadrklyuch"))
                    TORG.write_text(novy, encoding="utf-8")
                print(f"  ui_torg.py: {'готов' if SUHO else 'поправлен'}")
                vsego += 1
            except SyntaxError as e:
                print(f"  ui_torg.py: ОТКАЗ — синтаксис сломан ({e})")

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_kadrklyuch")
    print("Кадр справа, один на побудку. Остальные — в отчёте.")
    print()


if __name__ == "__main__":
    main()
