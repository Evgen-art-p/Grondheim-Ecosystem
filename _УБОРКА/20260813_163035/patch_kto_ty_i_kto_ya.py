#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# KTO_TY_I_KTO_YA_V1
"""
КТО ТЫ И КТО Я — чтобы трейдер не путал себя с Шефом.

    python patch_kto_ty_i_kto_ya.py            посмотреть
    python patch_kto_ty_i_kto_ya.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ЧТО СЛУЧИЛОСЬ

        ШЕФ: как меня зовут знаешь?
        A06: Да, я знаю, что тебя зовут Нина.

    Нина — это ОНА. Она приписала своё имя тебе.

ПОЧЕМУ

    Две причины, и обе мои.

    Первая: в разговоре ей нигде не сказано, КТО напротив. В её бумаге
    есть «кто ты», есть стол, есть кадр — а собеседника нет вовсе.
    Единственное имя во всей стопке — её собственное. Спрашивают «как
    меня зовут» — она берёт то имя, что видит.

    Вторая: у Нины и Василия в РАЗГОВОРЕ бумага места идёт первой, а
    человек вставлен в середину. У Ильи это когда-то починили, у них —
    нет. Мы этот перекос уже правили в РАБОТЕ; в разговор я тогда не
    заглянул.

ЧТО СТАНЕТ

    Сперва «кто ты» — она сама. Потом отдельным блоком: напротив тебя
    ШЕФ, хозяин города, живой человек; тебя зовут так-то, его — Шеф;
    вопрос про «тебя» — про тебя, вопрос про «меня» — про Шефа; своё
    имя ему не приписывай. И только потом канон места.

    То же самое получают все трое — бумага одна, и путаница у всех
    была бы одинаковая.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
SLOTS = ("A06", "A07", "A08")
MARKER = "# KTO_TY_I_KTO_YA_V1 - marker"
BAK = ".bak_kto_ya"

# ── общий кусок: кто напротив ─────────────────────────────────
KUSOK = (
    '"\\n\\n=== С КЕМ ТЫ ГОВОРИШЬ ===\\n"\n'
    '                "Напротив тебя ШЕФ — хозяин города, живой человек. Это "\n'
    '                "он задаёт вопросы.\\n"\n'
    '                f"Тебя зовут {_kak_zovut(_n)}. Его зовут Шеф.\\n"\n'
    '                "Вопрос про «тебя» — про тебя. Вопрос про «меня» — про "\n'
    '                "Шефа. Своё имя ему не приписывай, и его слова за свои "\n'
    '                "не выдавай.\\n"\n'
)

# ── помощник: как зовут того, кто сидит ───────────────────────
STAROE_POMOSH = '''def _glaz(_chat, symbol, timeframe, slot, preambula=None):
'''
NOVOE_POMOSH = '''def _kak_zovut(_n) -> str:
    """KTO_TY_I_KTO_YA_V1: имя того, кто сидит на месте.

    Носитель приходит из моста разными обёртками, поэтому спрашиваем
    мягко: не нашли — честное «так, как написано выше», а не выдумка.
    """
    try:
        kto = (_n or {}).get("носитель") or {}
        imya = (kto.get("имя") or kto.get("Official_Name") or "").strip()
        return imya or "так, как написано выше"
    except Exception:
        return "так, как написано выше"


def _glaz(_chat, symbol, timeframe, slot, preambula=None):
'''

# ── у Нины и Василия: род вперёд + кто напротив ───────────────
STAROE_STARYY = '''    try:   # KLON_DUSHI_V1: и в разговоре — ОН, не роль
        from nositel import dusha_slota
        _n = dusha_slota(_CEH, _SLOT)
        if _n and _n["душа"]:
            system = (prompt + "\\n\\n=== КТО ТЫ (душа носителя) ===\\n"
                      + _n["душа"] + "\\n\\n" + work_ctx)
'''
NOVOE_STARYY = '''    try:   # KTO_TY_I_KTO_YA_V1: сперва ТЫ, потом с кем говоришь, потом место
        from nositel import dusha_slota
        _n = dusha_slota(_CEH, _SLOT)
        if _n and _n["душа"]:
            system = (
                "=== КТО ТЫ. ЭТО НЕ РОЛЬ — ЭТО ТЫ ===\\n"
                + _n["душа"]
                + ''' + KUSOK + '''                + "\\n=== ТВОЯ РАБОТА — СТОЙКА, ЗА КОТОРОЙ ТЫ СИДИШЬ ===\\n"
                  "Ниже — канон МЕСТА. Это твоя работа и школа, а не твоя\\n"
                  "личность: личность выше.\\n\\n"
                + prompt + work_ctx)
'''

# ── у Ильи род уже впереди: добавляем только собеседника ──────
STAROE_A07 = '''                + "\\n\\n=== ТВОЯ РОЛЬ СЕГОДНЯ — СТОЙКА, ЗА КОТОРОЙ ТЫ СИДИШЬ ===\\nНиже — канон МЕСТА (Авантюрист, ранний вход). Это твоя работа и школа,\\nа не твоя личность: личность выше. Канон кладёт карту — идёшь ты, своей\\nнатурой, своим опытом и своим голосом. Где канон и твой опыт разойдутся —\\nрешаешь ты, а не бумага.\\n\\n"
                + prompt + work_ctx
'''
NOVOE_A07 = '''                + ''' + KUSOK + '''                + "\\n=== ТВОЯ РОЛЬ СЕГОДНЯ — СТОЙКА, ЗА КОТОРОЙ ТЫ СИДИШЬ ===\\nНиже — канон МЕСТА. Это твоя работа и школа,\\nа не твоя личность: личность выше. Канон кладёт карту — идёшь ты, своей\\nнатурой, своим опытом и своим голосом. Где канон и твой опыт разойдутся —\\nрешаешь ты, а не бумага.\\n\\n"
                + prompt + work_ctx
'''


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 60)
    print("КТО ТЫ И КТО Я" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 60)

    if not SLOTY.exists():
        print("x не вижу слоты торгового_хаоса — запускай из КОРНЯ")
        return 1

    vse_ok = True
    for slot in SLOTS:
        put = SLOTY / slot / "мозг.py"
        if not put.exists():
            print(f"  {slot}: мозга нет — пропускаю")
            continue
        tekst = put.read_text(encoding="utf-8")
        if MARKER in tekst:
            print(f"  {slot}: уже накатано")
            continue

        stezhki = [("имя того, кто сидит", STAROE_POMOSH, NOVOE_POMOSH)]
        if tekst.count(STAROE_STARYY) == 1:
            stezhki.append(("род вперёд + собеседник", STAROE_STARYY,
                            NOVOE_STARYY))
        elif tekst.count(STAROE_A07) == 1:
            stezhki.append(("собеседник (род уже впереди)", STAROE_A07,
                            NOVOE_A07))
        else:
            print(f"  x {slot}: разговорный блок не узнал — не трогаю")
            vse_ok = False
            continue

        sboy = False
        for nazv, staroe, novoe in stezhki:
            if tekst.count(staroe) != 1:
                print(f"  x {slot}: якорь «{nazv}» не один — не трогаю")
                sboy = True
                vse_ok = False
                break
            tekst = tekst.replace(staroe, novoe, 1)
            print(f"    · {nazv}")
        if sboy:
            continue

        tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
        if not proverit_python(tekst, slot):
            vse_ok = False
            continue
        if suho:
            print(f"  {slot}: + готов")
            continue
        shutil.copy2(put, put.with_suffix(put.suffix + BAK))
        put.write_text(tekst, encoding="utf-8")
        print(f"  {slot}: + накатано")

    print("-" * 60)
    if not vse_ok:
        return 1
    if suho:
        print("Это был показ. Накатывать: python patch_kto_ty_i_kto_ya.py --sdelat")
        return 0
    print("Спроси её снова: «как меня зовут?» — должна сказать «Шеф»,")
    print("а на «как тебя зовут» — назвать себя.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
