# -*- coding: utf-8 -*-
# chisla_v_mesto.py — в отчёт попадают показатели, а не один текст.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python chisla_v_mesto.py
#
# ═══ ЧТО БЫЛО ═══
#
# В места.jsonl за весь прогон 17.09 (285 мест):
#     разворотный: None — 285 из 285
#     компас:      None — 285 из 285
#     длина_волны: None — 285 из 285
#
# Поля есть, данных в них нет. Отчёт получался слепым: один текст
# трейдера и ни одного показателя. Проверить её слова числом нельзя —
# только поверить или не поверить.
#
# Почему пусто: эти поля брались из КАНДИДАТА (k). В прогоне кандидат
# приходит от ключа пробуждения и таких полей не несёт.
#
# ═══ ГДЕ ЧИСЛА НА САМОМ ДЕЛЕ ═══
#
# Мозг трейдера уже отдаёт городу ВЕСЬ СТОЛ — ключом "table" в своём
# ответе. Тот самый стол, который трейдер видел своими глазами.
# Отчёт этот ключ получал и не разбирал.
#
# Берём числа оттуда, а не пересчитываем заново: пересчёт на момент
# записи мог бы попасть на другой бар, и в отчёте оказалась бы
# неправда — хуже, чем пусто.
#
# ═══ ЧТО ПОЯВИТСЯ В КАЖДОМ МЕСТЕ ═══
#
#   разворотный, цена_разворотного — сторона будильника (BULL/BEAR)
#   компас, вода_этажи, вода_почему — куда смотрит большая вода
#   направление_рабочего            — куда смотрит свой этаж
#   ao_значение, ao_прошлое, ao_растёт — прибор голыми числами
#   фрактал_вверх, фрактал_вниз     — последние подтверждённые
#   цена_бара, бар_времени, спред_шаг
#
# Всё это — ГОЛЫЕ ПОКАЗАНИЯ, без единого суждения. Закон отчёта
# соблюдён: он записывает, а не судит.
#
# Старые поля из кандидата не выбрасываются: если кандидат что-то
# принёс, оно и останется, стол только дополняет пустое.
#
# ЧЕГО НЕ ДЕЛАЕТ. Торговли не касается. Трейдер ничего не почувствует:
# это запись для Шефа.
#
# БЕЗОПАСНО. Проверяет ast.parse. Рядом кладёт otchyot.py.bak_chisla.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "CHISLA_V_MESTO_V1"

STAROE = (
    '        self.mesta.append({\n'
    '            "когда_на_рынке": _nastoyashchiy_bar or k.get("дата", ""),\n'
    '            "место_найдено_на": k.get("дата", ""),\n'
    '            "кто": imya, "слот": slot,\n'
    '            "инструмент": symbol, "этаж": etazh,\n'
    '            "разворотный": k.get("разворотный"),\n'
    '            "цена_разворотного": k.get("цена_разворотного"),\n'
    '            "длина_волны": k.get("длина_волны"),\n'
    '            "в_окне_100_140": bool(\n'
    '                k.get("длина_волны")\n'
    '                and OKNO[0] <= k["длина_волны"] <= OKNO[1]),\n'
    '            "компас": k.get("компас"),\n'
)

NOVOE = (
    '        # CHISLA_V_MESTO_V1: показатели берём СО СТОЛА трейдера.\n'
    '        # Мозг отдаёт его целиком ключом "table" — это ровно то,\n'
    '        # что трейдер видел. Кандидат в прогоне таких полей не\n'
    '        # несёт, оттого в 285 местах подряд стояло None.\n'
    '        # Пересчитывать заново нельзя: попадём на другой бар и\n'
    '        # запишем неправду — хуже, чем пусто.\n'
    '        _st = {}\n'
    '        _pr = {}\n'
    '        try:\n'
    '            _st = (rezultat or {}).get("table") or {}\n'
    '            _pr = _st.get("приборы") or {}\n'
    '        except Exception:\n'
    '            pass\n'
    '        _rb = _pr.get("разворотный_бар") or {}\n'
    '        _ao = _pr.get("ao") or {}\n'
    '        _fr = _pr.get("фракталы") or {}\n'
    '\n'
    '        def _ili(iz_kandidata, iz_stola):\n'
    '            """Кандидат главнее — он ближе к моменту находки."""\n'
    '            return iz_kandidata if iz_kandidata is not None else iz_stola\n'
    '\n'
    '        _volna = k.get("длина_волны")\n'
    '        self.mesta.append({\n'
    '            "когда_на_рынке": _nastoyashchiy_bar or k.get("дата", ""),\n'
    '            "место_найдено_на": k.get("дата", ""),\n'
    '            "кто": imya, "слот": slot,\n'
    '            "инструмент": symbol, "этаж": etazh,\n'
    '            "разворотный": _ili(k.get("разворотный"),\n'
    '                                _rb.get("сторона")),\n'
    '            "цена_разворотного": _ili(k.get("цена_разворотного"),\n'
    '                                      _rb.get("цена")),\n'
    '            "длина_волны": _volna,\n'
    '            "в_окне_100_140": bool(\n'
    '                _volna and OKNO[0] <= _volna <= OKNO[1]),\n'
    '            "компас": _ili(k.get("компас"), _pr.get("вода")),\n'
    '            # ── голые показания стола, без суждений ──\n'
    '            "вода_этажи": _pr.get("вода_этажи"),\n'
    '            "вода_почему": _pr.get("вода_почему"),\n'
    '            "направление_рабочего": _pr.get("направление_рабочего"),\n'
    '            "ao_значение": _ao.get("значение"),\n'
    '            "ao_прошлое": _ao.get("прошлое"),\n'
    '            "ao_растёт": _ao.get("растёт"),\n'
    '            "фрактал_вверх": _fr.get("вверх"),\n'
    '            "фрактал_вниз": _fr.get("вниз"),\n'
    '            "цена_бара": _pr.get("цена"),\n'
    '            "бар_времени": _pr.get("бар"),\n'
    '            "шаг_цены": _pr.get("point"),\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    prosto = KOREN / "Биржа" / "otchyot.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak", ".bylo")
    nashlos = [p for p in KOREN.rglob("otchyot.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько otchyot.py:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/otchyot.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if tekst.count(STAROE) != 1:
        print(f"✗ нашёл {tekst.count(STAROE)} мест вместо одного —")
        print("  отчёт мог измениться. Ничего не тронул.")
        print("  Скажи Брату, поправим по месту.")
        return 1

    # как в этом файле зовётся ответ трейдера
    imya_otveta = "rezultat"
    for kandidat in ("rezultat", "result", "r", "otvet"):
        if f"def zapisat(self, k: dict, slot: str, imya: str," in tekst:
            break
    import re
    m = re.search(r"def zapisat\(self,[^)]*\)", tekst)
    if m and "rezultat" not in m.group(0):
        for kandidat in ("result", "r", "otvet", "res"):
            if re.search(rf"[,(]\s*{kandidat}\s*[:,)=]", m.group(0)):
                imya_otveta = kandidat
                break

    novyy = tekst.replace(STAROE, NOVOE.replace("rezultat", imya_otveta), 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): "
              f"{beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_chisla")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ числа пошли в место:")
    print(f"    · ответ трейдера в этом файле зовётся «{imya_otveta}»")
    print("    · сторона будильника и его цена")
    print("    · компас, этажи воды и почему её нет")
    print("    · AO голыми числами, последние фракталы")
    print("    · цена бара, время бара, шаг цены")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("В места.jsonl поля перестанут быть пустыми — и тогда её")
    print("«дивергенция AO» станет проверяемой числом, а не на слово.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
