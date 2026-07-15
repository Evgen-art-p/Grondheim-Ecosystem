# -*- coding: utf-8 -*-
"""
patch_snyat_mayatnik_sensorov.py
════════════════════════════════════════════════════════════════════
СНЯТИЕ МЁРТВОГО МАЯТНИКА sync_to_dna ИЗ МОЗГОВ СЕНСОРОВ (A01–A04)

БОЛЕЗНЬ (из живого лога 15 срабатываний):
    [ISKRA] ⚠️  sync_to_dna не сработал (No module named 'studio')
    …и то же у Моржа, Паникёра, Ганса — каждый бар, каждый сенсор.

ДИАГНОЗ:
    Внутри мозг.py четырёх сенсоров остался ПОРТИРОВАННЫЙ из мёртвой
    студии вызов:
        from studio.grondheim_memory import sync_to_dna
    Модуль снесён вместе со студией. Вызов падает → except → печать
    предупреждения → молча ничего. Это не рабочий код, это надгробие,
    которое ещё и шумит в лог.

ПОЧЕМУ РЕЖЕМ, А НЕ ЧИНИМ ЧЕРЕЗ МОСТ (канон, не экономия):

  1. sync_to_dna — это КАЧАНИЕ ДНК за «хорошую/плохую работу».
     Чертёж (гл.4.2) зовёт маятник ДНК НЕ-опытом. Нога Опыта строится
     трубой  исход → судья → вывод словами → якоря носителя,
     а НЕ восстановлением маятника. Воскресить канал = воскресить
     механизм, который Чертёж уже осознанно похоронил.

  2. Закон Одного Глагола: СУДЬЯ возвращает последствия ИЗ МИРА.
     Рынок — чистейший судья, и он УЖЕ судит сенсоров:
     hooks._judge_iskra_by_result → nositel.zapisat_vyvod_pare
     (в логе: «звал=True → ЕСТЬ», метки растут на живом убытке Ильи).
     А DETECTED→CONFIRMED — это сенсор, подтверждающий СВОЮ ЖЕ находку.
     Самооценка вместо суда. Дубль работающего механизма.

  3. «Строим, когда заболит.» Дыра (сенсор учится только когда была
     сделка И он звал) пока не болит — метки растут, выводы оплачены
     настоящими деньгами. Если однажды заболит — строить надо ЧЕРЕЗ
     МОСТ (словами в якоря, судья = мир), а не маятником ДНК.

ЧТО ДЕЛАЕТ ПАТЧ:
    В каждом из A01–A04 вырезает блок
        # ── 6b. ПЕТЛЯ ОБУЧЕНИЯ … (если есть заголовок)
        try:
            from studio.grondheim_memory import sync_to_dna
            … sync_to_dna(...) …
        except Exception as e:
            print(f"[…] ⚠️  sync_to_dna не сработал ({e})")
    и кладёт на его место короткое надгробие-канон (комментарий),
    чтобы НИКТО потом не «починил» восстановлением.

    Логика решения сенсора (phase/coherent/fact_valid/field_alive и т.п.)
    НЕ трогается — только мёртвый маятник.

ИДЕМПОТЕНТЕН: повторный запуск ничего не делает (маркер + отсутствие
    цели проверяются). Бэкап каждого файла — рядом, один раз.

Запуск из корня проекта:
    python patch_snyat_mayatnik_sensorov.py
"""
import io
import re
import sys
from pathlib import Path

MARKER = "MAYATNIK_SNYAT_V1"

BASE = Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# tag сенсора в print — чтобы найти правильный except и подставить надгробие
SLOTS = {
    "A01": "ISKRA",
    "A02": "MORJ",
    "A03": "PANIC",
    "A04": "HANS",
}


def _nadgrobie(indent: str) -> str:
    """Комментарий-канон на месте вырезанного маятника."""
    i = indent
    return (
        f"{i}# {MARKER}: мёртвый маятник sync_to_dna снят (см. патч-док).\n"
        f"{i}# Сенсор НЕ качает свою ДНК за «точность» — это НЕ-опыт (Чертёж 4.2).\n"
        f"{i}# Судья сенсора = РЫНОК: hooks._judge_iskra_by_result →\n"
        f"{i}# nositel.zapisat_vyvod_pare. Вывод оплачивается деньгами, не сам собой.\n"
        f"{i}# Не воскрешать: сюда придёт Мост, если петля точности заболит.\n"
    )


def patch_one(slot: str, tag: str) -> str:
    """Возвращает строку статуса для лога."""
    path = BASE / slot / "мозг.py"
    if not path.exists():
        return f"[{slot}] ✗ не найден {path}"

    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        return f"[{slot}] ✓ уже снят ({MARKER}) — пропуск"

    if "sync_to_dna" not in src:
        return f"[{slot}] ✓ маятника нет — пропуск"

    orig = src

    # Ловим весь блок:  try:  … from studio.grondheim_memory import sync_to_dna …
    #                   except Exception as e:
    #                       print(f"[TAG] ⚠️  sync_to_dna не сработал ({e})")
    # Захватываем отступ try, чтобы точно подставить надгробие тем же отступом.
    pattern = re.compile(
        r'(?P<ind>[ \t]*)try:\s*\n'
        r'(?:[ \t]*#[^\n]*\n)*'                       # возможные комментарии
        r'[ \t]*from studio\.grondheim_memory import sync_to_dna[^\n]*\n'
        r'(?:(?![ \t]*except\b)[^\n]*\n)*?'           # тело try (до except)
        r'[ \t]*except Exception as e:\s*\n'
        r'[ \t]*print\(f?"\[' + re.escape(tag) + r'\][^\n]*sync_to_dna[^\n]*\)\s*\n',
        re.UNICODE,
    )

    m = pattern.search(src)
    if not m:
        return f"[{slot}] ⚠️  блок sync_to_dna не распознан — НЕ тронут (проверь вручную)"

    indent = m.group("ind")
    src = src[:m.start()] + _nadgrobie(indent) + src[m.end():]

    # Постпроверка: не осталось ли ЖИВОГО кода (импорт/вызов), а не
    # упоминаний sync_to_dna в комментариях-прозе (они законны — история).
    live = re.search(
        r'^[ \t]*(?:from studio\.grondheim_memory import sync_to_dna'
        r'|sync_to_dna\s*\()',
        src, re.MULTILINE,
    )
    if live:
        return f"[{slot}] ⚠️  остался ЖИВОЙ sync_to_dna — НЕ сохраняю, проверь вручную"

    # бэкап + запись
    bak = path.with_suffix(".py.bak_mayatnik")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")

    path.write_text(src, encoding="utf-8")
    return f"[{slot}] ✅ маятник снят, надгробие поставлено · бэкап: {bak.name}"


def main():
    if not BASE.exists():
        print(f"[ПАТЧ] ✗ не найдена папка слотов: {BASE}")
        print("[ПАТЧ]   запусти из КОРНЯ проекта Grondheim-Ecosystem")
        sys.exit(1)

    print("[ПАТЧ] Снятие мёртвого маятника sync_to_dna из мозгов сенсоров")
    print("[ПАТЧ] " + "─" * 56)
    any_changed = False
    for slot, tag in SLOTS.items():
        line = patch_one(slot, tag)
        print("[ПАТЧ] " + line)
        if "✅" in line:
            any_changed = True

    print("[ПАТЧ] " + "─" * 56)
    if any_changed:
        print("[ПАТЧ] ✅ Готово. Лог станет чистым — предупреждения уйдут.")
        print("[ПАТЧ]    Суд сенсоров остаётся на Мосту (рынок судит словом).")
    else:
        print("[ПАТЧ] ✓ Нечего менять (идемпотентно).")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
