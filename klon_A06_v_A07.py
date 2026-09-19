# -*- coding: utf-8 -*-
# klon_A06_v_A07.py — переносит начинку слота A06 в A07, один в один.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python klon_A06_v_A07.py
#
# ═══ ЗАЧЕМ ═══
#
# Замер натуры. У Синди упрямство 0.25, автономия 0.5, заряд −1.0 —
# её мотает состоянием, а мы гоняем прогоны по три года, где она
# получает по −1R десятками. У Ильвы упрямство 0.85, автономия 1.0,
# заряд +0.07.
#
# Чтобы сравнение было честным, знания должны быть ОДИНАКОВЫЕ. Иначе
# мы сравним не характеры, а бумаги.
#
# Слот A07 существует и обустроен, но СТАРЫЙ: мозг 94 КБ против 108 у
# A06, промпт 11.7 КБ против 26.5. Ни одна правка последних дней туда
# не попала — ни три условия, ни направление перед дивером, ни метка,
# ни ведение глазом.
#
# ═══ ЧТО ДЕЛАЕТ ═══
#
# Копирует из A06 в A07: мозг.py, промпт.md, всю папку «знания».
# Старое А07 не удаляет, а откладывает рядом с пометкой .bylo_A07.
#
# И правит в новом мозге три гвоздя — места, где A06 прибит намертво:
#     _SLOT = "A06"              → "A07"
#     _SELF_KEY = "a06"          → "a07"
#     stats_A06.json             → stats_A07.json
# Всё остальное мозг определяет по своей же папке и подстроится сам.
#
# Папку «данные» НЕ трогает: там живёт опыт жителя, и он у каждого
# свой. Ильва начнёт с чистого листа — это честно.
#
# ═══ ЧЕГО НЕ ДЕЛАЕТ ═══
#
# НЕ нанимает Ильву. Найм — дело Страницы Работы в Кабинете, там
# заводится маска работы (цех торговый_хаос, слот A07, магик). Руками
# в файлах этого лучше не делать: реестр читает маски, и кривая маска
# ломает найм молча.
#
# Город про A07 уже знает: роль AVANTURIST, магик 100002, дневник
# diary_avan.jsonl. Место ждёт жителя.
#
# БЕЗОПАСНО. Сперва проверяет, что всё на месте и мозг после правки
# рабочий (ast.parse). Не сошлось — не трогает ничего.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "KLON_A06_V_A07_V1"

SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")

# Гвозди — места, где A06 прибит намертво. Всё прочее мозг
# определяет по своей же папке и подстроится сам.
# Число = сколько раз встречается; сторож ниже проверит.
GVOZDI = [
    ('_SLOT = "A06"', '_SLOT = "A07"', 1),
    ('_SELF_KEY = "a06"', '_SELF_KEY = "a07"', 1),
    ('"stats_A06.json"', '"stats_A07.json"', 1),
    # личная тетрадь: без этого Ильва писала бы в тетрадь Синди
    ('"diary_A06.jsonl"', '"diary_A07.jsonl"', 1),
    # подпись обращений к модели — город ждёт для A07 роль AVANTURIST
    ('agent_id="A06_BRUT"', 'agent_id="A07_AVANTURIST"', 2),
    # ещё две подписи, уже без роли
    ('agent_id="A06"', 'agent_id="A07"', 2),
]


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti_sloty():
    if SLOTY.exists():
        return SLOTY
    nash = [p.parent for p in KOREN.rglob("слоты/A06") if p.is_dir()]
    if len(nash) == 1:
        return nash[0]
    return None


def otlozhit(put: Path, hvost: str):
    """Отложить старое рядом, не удаляя."""
    if not put.exists():
        return
    zapas = put.with_name(put.name + hvost)
    n = 1
    while zapas.exists():
        n += 1
        zapas = put.with_name(f"{put.name}{hvost}{n}")
    put.rename(zapas)
    print(f"  (старое отложено: {zapas.name})")


def main():
    sloty = nayti_sloty()
    if sloty is None:
        print("✗ не нашёл папку слотов — запускай из корня репозитория")
        return 1
    a06, a07 = sloty / "A06", sloty / "A07"

    if not a06.exists():
        print("✗ слота A06 нет")
        return 1
    for imya in ("мозг.py", "промпт.md"):
        if not (a06 / imya).exists():
            print(f"✗ в A06 нет файла {imya}")
            return 1

    if (a07 / "мозг.py").exists():
        t = (a07 / "мозг.py").read_text(encoding="utf-8")
        if MARKER in t:
            print("· уже сделано")
            return 0

    # ── готовим мозг в памяти ──
    mozg = (a06 / "мозг.py").read_text(encoding="utf-8")
    for staroe, _, skolko in GVOZDI:
        if mozg.count(staroe) != skolko:
            print(f"✗ в мозге A06 нашёл {mozg.count(staroe)} раз «{staroe}», "
                  f"а ждал {skolko}.")
            print("  Ничего не тронул. Скажи Брату, поправим по месту.")
            return 1
    novyy = mozg
    for staroe, novoe, _ in GVOZDI:
        novyy = novyy.replace(staroe, novoe)
    novyy = (f"# {MARKER}: начинка скопирована из A06 один в один,\n"
             f"# переставлены только имя слота, ключ и файл статистики.\n"
             f"# Знания и промпт те же — чтобы сравнивать НАТУРЫ, а не\n"
             f"# бумаги.\n" + novyy)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ мозг после правки поломался (строка {beda.lineno})")
        print("  Ничего не записал.")
        return 1

    if "A06" in novyy.replace("из A06", "").replace("слоты/A06", ""):
        ost = [l.strip() for l in novyy.split("\n")
               if "A06" in l and not l.strip().startswith("#")]
        if ost:
            print("⚠ в новом мозге остались упоминания A06 вне комментариев:")
            for l in ost[:5]:
                print("   ", l[:90])
            print("  Это может быть безобидно, но посмотри глазами.")

    a07.mkdir(parents=True, exist_ok=True)

    # ── откладываем старое ──
    otlozhit(a07 / "мозг.py", ".bylo_A07")
    otlozhit(a07 / "промпт.md", ".bylo_A07")
    if (a07 / "знания").exists():
        otlozhit(a07 / "знания", ".bylo_A07")

    # ── кладём новое ──
    (a07 / "мозг.py").write_text(novyy, encoding="utf-8")
    shutil.copy2(a06 / "промпт.md", a07 / "промпт.md")
    if (a06 / "знания").exists():
        shutil.copytree(a06 / "знания", a07 / "знания")
    (a07 / "данные").mkdir(exist_ok=True)

    skolko = len(list((a07 / "знания").glob("*"))) if (a07 / "знания").exists() else 0
    print("✓ слот A07 стал копией A06:")
    print("    · мозг.py — те же правки; переставлены имя слота, ключ,")
    print("      файл статистики, личная тетрадь и подпись обращений")
    print("    · промпт.md — один в один")
    print(f"    · знания — {skolko} файл(ов)")
    print("    · папка «данные» пустая: опыт у каждого свой")
    print()
    print("ОСТАЛОСЬ, И ЭТО РУКАМИ: нанять Ильву на A07 через Страницу")
    print("Работы в Кабинете. Город про место уже знает — роль")
    print("AVANTURIST, магик 100002.")
    print()
    print("Потом перезапусти main.py и прогони ОДИН отрезок на обеих.")
    print("Знания одинаковые, разная только натура — вот и сравним.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
