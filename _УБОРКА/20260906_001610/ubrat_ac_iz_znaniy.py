# -*- coding: utf-8 -*-
# MARKER: AC_VON_ZNANIYA_V1
"""
AC УХОДИТ ИЗ ЗНАНИЙ ТРЕЙДЕРОВ — ХВОСТ ВЧЕРАШНЕЙ ВЫЧИСТКИ.

ЧТО НАШЛОСЬ
    Вчера (AC_VON_V1) AC убрали из ядра и со стола. Но остался один
    файл: KOTIN_PHILOSOPHY.md, раздел «Данные, которые вы видите»,
    строка — «ao, ac — текущие значения осцилляторов и дивергенции».

    Это не код — это КАНОН, который трейдер читает как знания. Файл
    прямо говорит: «в market_data будет ac». А его там больше нет.
    Отсюда и разговоры Ильи про AC на прогоне — не глюк, а устаревшая
    инструкция, которая противоречит тому, что реально лежит на столе.

    Файл ОБЩИЙ у всех слотов Биржи (проверено: у A06 и A07 — один и
    тот же файл, побайтово).

ЧТО ДЕЛАЕТ ПАТЧ
    Убирает одно слово из одной строки. AO остаётся — он работает.
    Больше ничего в файле не трогает.

Идемпотентен. .bak рядом. Путь ищет сам — правит файл в КАЖДОМ слоте,
где найдёт (общий канон может быть скопирован по слотам).
"""
import shutil
import sys
from pathlib import Path

MARKER_STROKA = "— `ao` — текущее значение осциллятора и дивергенция."

YAKOR = "— `ao`, `ac` — текущие значения осцилляторов и дивергенции."


def _nayti_faily() -> list:
    """Все KOTIN_PHILOSOPHY.md в городе — по слотам может быть не один."""
    zdes = Path(__file__).resolve().parent
    korni = [zdes, Path.cwd().resolve()]
    nashli = []
    for k in korni:
        try:
            for f in k.rglob("KOTIN_PHILOSOPHY.md"):
                if f not in nashli:
                    nashli.append(f)
        except OSError:
            pass
        if nashli:
            break
    return nashli


def main():
    fayly = _nayti_faily()
    if not fayly:
        print("Не нашёл ни одного KOTIN_PHILOSOPHY.md.")
        print("Запусти из корня репозитория — файл лежит в знаниях слотов.")
        return

    print(f"Нашёл файлов: {len(fayly)}\n")
    pravlено = 0
    for f in fayly:
        text = f.read_text(encoding="utf-8")
        if MARKER_STROKA in text:
            print(f"  . {f}: уже поправлен, пропускаю")
            continue
        if text.count(YAKOR) != 1:
            print(f"  X {f}: строка не найдена или не одна "
                  f"({text.count(YAKOR)}) — не трогаю")
            continue
        novyy = text.replace(YAKOR, MARKER_STROKA)
        shutil.copy2(f, f.with_suffix(".md.bak_ac_znaniya"))
        f.write_text(novyy, encoding="utf-8")
        print(f"  + {f}: строка про AC убрана (.bak рядом)")
        pravlено += 1

    print(f"\nГотово. Поправлено файлов: {pravlено}.")
    print("AO в тексте остался, AC убран из фразы целиком.")
    print("Действует со следующего вопроса трейдеру — прогон, который")
    print("уже идёт, эту правку читать не будет (знания берутся при")
    print("каждом обращении заново, но текущий процесс уже запущен).")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
