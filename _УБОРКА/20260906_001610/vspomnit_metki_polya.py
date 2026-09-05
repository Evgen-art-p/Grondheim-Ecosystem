#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VSPOMNIT_METKI_POLYA_V1 — 05.09
Запускать из КОРНЯ репо (Grondheim-Ecosystem), как предыдущие патчи.

Четыре расхождения имён полей в `dvizhok.py` ломают поиск по нажитому
опыту (2_метки/metki.json, 3_маяки/mayaki.json) через vspomnit():

  1) Записи метки/маяка хранят содержание под ключом "текст". Поиск
     `vspomnit()` при подсчёте совпадений смотрит на ключ "факт" —
     этого ключа там нет. Результат: у ЛЮБОЙ метки или маяка score
     всегда 0, независимо от темы запроса. Подтверждено тестом на
     точной копии кода: поправка учителя ложится честно, но
     `vspomnit("зигзаг")` её не находит вообще — пока поле не
     исправлено (после исправления — находит, score=1).

  2) Та же запись хранит время под ключом "когда", а vspomnit сортирует
     находки по ключу "ts", которого там нет.

  3) Тот же самый пропуск — в финальной строке вывода: она тоже читает
     "факт" вместо "текст". Без этой правки находка есть, но выводится
     с пустым текстом (проверено: после правок 1-2 без этой — строка
     вида «— [дата · практика] » пустая).

  4) `popravka_uchitelya()` (05.09) не проставляет "контекст" записи.
     Фильтр `vspomnit(..., o_chyom="работа")` смотрит на это поле
     (через kontekst_zapisi) — без него запись невидима именно для
     рабочего запроса, даже после починки (1)-(3). Поправка учителя
     трейдеру по определению рабочее знание — проставляем "работа".

Идемпотентен: повторный запуск — 0 правок. Бэкап .bak_vspomnit рядом.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

STARIY_POLE = '''            fakt = str(z.get("факт", "")).lower()
            score = sum(1 for w in slova if w in fakt)
            if iskomyj_tonus and z.get("тонус") == iskomyj_tonus:
                score += 2   # PAMYAT_ISKRA_V1: тон совпал — весит как два слова
            if score > 0:
                naydeno.append((score, str(z.get("ts", "")), z))'''

NOVOE_POLE = '''            # VSPOMNIT_METKI_POLYA_V1 (05.09): метки/маяки хранят
            # содержание под ключом "текст", а sensory/resonance/
            # archive — под "факт". Без фоллбэка любая метка и маяк
            # давали score=0 независимо от темы запроса — весь опыт
            # (рыночный, учебный, поправки учителя) был невидим для
            # vspomnit(), хотя реально лежал на диске.
            fakt = str(z.get("текст") or z.get("факт") or "").lower()
            score = sum(1 for w in slova if w in fakt)
            if iskomyj_tonus and z.get("тонус") == iskomyj_tonus:
                score += 2   # PAMYAT_ISKRA_V1: тон совпал — весит как два слова
            if score > 0:
                # VSPOMNIT_METKI_POLYA_V1: та же история со временем —
                # метки/маяки пишут "когда", не "ts".
                naydeno.append((score, str(z.get("ts") or z.get("когда") or ""), z))'''

STARIY_VYVOD = '''        stroki = []
        for _, _, z in naydeno[:limit]:
            ts = str(z.get("ts", ""))[:10]'''

NOVYY_VYVOD = '''        stroki = []
        for _, _, z in naydeno[:limit]:
            # VSPOMNIT_METKI_POLYA_V1: тот же фоллбэк для вывода даты.
            ts = str(z.get("ts") or z.get("когда") or "")[:10]'''

STARAYA_STROKA_VYVODA = '''            stroki.append(f"— [{ts}{otkuda}] {z.get('факт', '')}")'''

NOVAYA_STROKA_VYVODA = '''            # VSPOMNIT_METKI_POLYA_V1: и здесь тот же фоллбэк —
            # метки/маяки хранят текст под «текст», не «факт».
            stroki.append(f"— [{ts}{otkuda}] {z.get('текст') or z.get('факт') or ''}")'''

STARAYA_POPRAVKA = '''        metki.append({
            "текст": tekst,
            "паттерн": pattern,
            "откуда": "учитель",
            "когда": now_iso,
            "раз": 1,
        })'''

NOVAYA_POPRAVKA = '''        metki.append({
            "текст": tekst,
            "паттерн": pattern,
            "откуда": "учитель",
            "когда": now_iso,
            "раз": 1,
            # VSPOMNIT_METKI_POLYA_V1 (05.09): без контекста запись
            # невидима для vspomnit(..., o_chyom="работа") — а поправка
            # учителя трейдеру по определению рабочее знание.
            "контекст": "работа",
        })'''


def _naiti(rel_suffix: str) -> list[Path]:
    found = []
    for p in REPO_ROOT.rglob("*"):
        if p.is_file() and str(p).replace("\\", "/").endswith(rel_suffix):
            found.append(p)
    return found


def _backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_vspomnit")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def patch_dvizhok(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "VSPOMNIT_METKI_POLYA_V1" in text:
        print(f"  ⏭  {path}: уже правлено")
        return False

    changed = False
    if STARIY_POLE in text:
        text = text.replace(STARIY_POLE, NOVOE_POLE, 1)
        changed = True
        print(f"  ✅ {path}: поле «факт»/«текст» в подсчёте score исправлено")
    else:
        print(f"  ⚠️  {path}: место подсчёта score не нашёл — структура изменилась")

    if STARIY_VYVOD in text:
        text = text.replace(STARIY_VYVOD, NOVYY_VYVOD, 1)
        changed = True
        print(f"  ✅ {path}: поле даты в выводе исправлено")
    else:
        print(f"  ⚠️  {path}: место вывода даты не нашёл")

    if STARAYA_STROKA_VYVODA in text:
        text = text.replace(STARAYA_STROKA_VYVODA, NOVAYA_STROKA_VYVODA, 1)
        changed = True
        print(f"  ✅ {path}: поле текста в строке вывода исправлено")
    else:
        print(f"  ⚠️  {path}: строку вывода текста не нашёл")

    if STARAYA_POPRAVKA in text:
        text = text.replace(STARAYA_POPRAVKA, NOVAYA_POPRAVKA, 1)
        changed = True
        print(f"  ✅ {path}: поправке учителя проставлен контекст «работа»")
    else:
        print(f"  ⚠️  {path}: popravka_uchitelya не нашёл")

    if changed:
        _backup(path)
        path.write_text(text, encoding="utf-8")
    return changed


def main():
    print("=== VSPOMNIT_METKI_POLYA_V1 ===\n")
    files = _naiti("жители/dvizhok.py")
    if not files:
        print("❌ dvizhok.py не найден — запускать из корня репо!")
        return
    for p in files:
        patch_dvizhok(p)
    print("\nГотово. Резервная копия — dvizhok.py.bak_vspomnit.")
    print("Это общий движок всех жителей города, не только трейдеров —")
    print("проверь синтаксис перед боевым запуском:")
    print("  python -c \"import ast; ast.parse(open('жители/dvizhok.py',encoding='utf-8').read())\"")


if __name__ == "__main__":
    main()
