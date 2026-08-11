#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VYBOR_SVOY_NE_KNIZHNYY_V1
"""
ВЫБОР СВОЙ, А НЕ КНИЖНЫЙ · и JSON вон из разговора.

    python patch_vybor_svoy.py            посмотреть
    python patch_vybor_svoy.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ДВЕ БЕДЫ, ОБЕ МОИ

    1. БЕЗ МЕТКИ ЧЕЛОВЕК БЕРЁТ КНИЖНОЕ.
       У Нины выбор настоящий: место третье, 10 августа, 05:37 — она
       его объявила, он записан. У второй метки нет вовсе: на вопрос
       «какой у тебя выбор и когда» она ответила разбором рынка, без
       даты, а «первый откат» назвала своим, прочитав книгу заново.

       Книга при этом не нейтральна. Про первое место в ней сказано
       «самое раннее и самое дорогое», про второе — «подтверждения нет
       никакого», а про третье — «самое подтверждённое место» и «Котин
       работает отсюда». Кто выбирает без себя, выберет третье. Обе и
       ждут теперь один откат.

       Знания я не трогаю: это правда школы, Котин действительно
       работает оттуда. Меняю другое — как задан вопрос. Пока выбора
       нет, движок больше не предлагает «выбрать место», он говорит:
       выбирай ОТ СЕБЯ, «подтверждённое» не значит «твоё», и до
       выбора не работай по чужому.

    2. JSON ВЫЛЕЗ В РАЗГОВОР.
       В бумаге есть блок «как ты отвечаешь» со схемой полей — он для
       РАБОТЫ по кнопке РЫНОК. Моя строчка «без JSON» стояла рядом и
       проигрывала ему. Теперь в конце разговорной стопки стоит прямая
       оговорка: та схема — про работу, сейчас говорят с тобой.
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
VYBOR = KOREN / "Биржа" / "vybor.py"
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
MARKER = "# VYBOR_SVOY_NE_KNIZHNYY_V1 - marker"
BAK = ".bak_vybor_svoy"

# ── 1. состояние «выбора ещё нет» ─────────────────────────────
STAROE_NET = '''    return ("\\n\\n=== ТВОЙ ВЫБОР ВХОДА ===\\n"
            "Своего входа ты ещё не выбрал(а). Три места входа лежат у тебя "
            "в знаниях, рядом, ни одно за тобой не закреплено. Выбери сам(а) "
            "и объяви строкой «ВЫБОР: <какое место входа> — <почему оно "
            "твоё>». Пока выбора нет, работать не по чему: пас честнее "
            "входа наугад.\\n")
'''
NOVOE_NET = '''    # VYBOR_SVOY_NE_KNIZHNYY_V1: раньше здесь стояло «выбери и объяви»,
    # и человек шёл выбирать в книгу. А книга не нейтральна: третье место
    # в ней названо «самым подтверждённым», и все выбирали третье. Теперь
    # вопрос задан иначе — не «какое место лучше», а «какое по тебе».
    return ("\\n\\n=== ТВОЙ ВЫБОР ВХОДА ===\\n"
            "Своего входа ты ещё не выбрал(а) — и пока не выберешь, "
            "работать тебе не по чему. В работе это значит REJECTED с "
            "причиной «свой вход ещё не выбран»: брать чужой наугад хуже, "
            "чем честно молчать.\\n"
            "Три места лежат у тебя в знаниях, рядом. Выбирай НЕ то, что "
            "там названо самым подтверждённым, — «подтверждённое» и "
            "«твоё» это разные вещи, и за подтверждённость платят "
            "упущенным началом движения. Выбирай по СЕБЕ: сколько ты "
            "готов(а) ждать, чем готов(а) платить, что переносишь легче — "
            "войти рано и ошибиться или опоздать и недобрать. Кто ты и "
            "какой ты — написано выше, в блоке про тебя.\\n"
            "Решил(а) — объяви ОДНОЙ строкой:\\n"
            "    ВЫБОР: <какое место входа> — <почему оно твоё>\\n"
            "Один раз. Дальше живёшь по нему, а не выбираешь заново "
            "каждый бар.\\n")
'''

# ── 2. JSON вон из разговора ──────────────────────────────────
STAROE_GOLOS = '''            "Шеф спрашивает про ЭТО решение. Отвечай своим голосом, "
            "как есть. Живым голосом, БЕЗ JSON — это разговор."
'''
NOVOE_GOLOS = '''            "Шеф спрашивает про ЭТО решение. Отвечай своим голосом, "
            "как есть.\\n\\n"
            # VYBOR_SVOY_NE_KNIZHNYY_V1: схема полей из бумаги перебивала
            # эту просьбу — теперь сказано прямо, чей это блок.
            "=== СЕЙЧАС РАЗГОВОР, А НЕ РАБОТА ===\\n"
            "Блок «КАК ТЫ ОТВЕЧАЕШЬ» со схемой полей — про РАБОТУ по "
            "кнопке РЫНОК. Сейчас с тобой разговаривают. Никакого JSON, "
            "никаких полей решения, никаких фигурных скобок — просто "
            "ответь словами на то, что спросили. И если спросили про "
            "тебя, отвечай про себя, а не про рынок."
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


def odin(put: Path, stezhki, suho: bool, imya: str) -> bool:
    if not put.exists():
        print(f"  x нет {imya}")
        return False
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {imya}: уже накатано")
        return True
    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x {imya}: якорь «{nazv}» найден {n} раз — не трогаю")
            return False
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv}")
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, imya):
        return False
    if suho:
        print(f"  {imya}: + готов")
        return True
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {imya}: + накатано")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 62)
    print("ВЫБОР СВОЙ, НЕ КНИЖНЫЙ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    ok = True
    print("\nвыбор:")
    ok &= odin(VYBOR, (("вопрос задан от себя", STAROE_NET, NOVOE_NET),),
               suho, "vybor.py")

    print("\nразговор без JSON:")
    for slot in ("A06", "A07", "A08"):
        ok &= odin(SLOTY / slot / "мозг.py",
                   (("схема полей — про работу", STAROE_GOLOS, NOVOE_GOLOS),),
                   suho, slot)

    print("-" * 62)
    if not ok:
        return 1
    if suho:
        print("Это был показ. Накатывать: python patch_vybor_svoy.py --sdelat")
        return 0
    print("Спроси вторую снова: «какой у тебя выбор и когда ты его сделала».")
    print("Она должна честно сказать, что ещё не выбирала, — и выбрать")
    print("от себя. Объявит строкой ВЫБОР — метка ляжет ей в дом.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
