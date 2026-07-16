# -*- coding: utf-8 -*-
"""
patch_yazyk_doliva.py
════════════════════════════════════════════════════════════════════
ЯЗЫК ДОЛИВКИ — ПОСЛЕДНЯЯ СТРОКА ПРОМТА МОЛЧАЛА ПРО ADD/MOVE_STOP

Диагноз Локи (подтверждён): полная JSON-схема с action/new_stop/
add_lot ЕСТЬ в системном промте (промпт.md), но ПОСЛЕДНЯЯ строка
user_msg (Python-код в мозг.py) — самая свежая, самая весомая
инструкция по правилу recency — у всех троих (A06/A07/A08) обрезана
до СТАРЫХ полей входа (verdict/reason/direction/entry/stop/lot).
Ни action, ни new_stop, ни add_lot там не упоминались вовсе. Это
реально могло глушить долив — модель видит противоречие между полной
схемой (система) и куцым напоминанием в конце (юзер).

ЛЕЧЕНИЕ: дописать в эту финальную строку все шесть полей ведения,
консистентно с полной JSON-схемой. Один текст, три префикса
(brut_/avan_/cons_).

ИДЕМПОТЕНТЕН (проверяет наличие "_action" в этой строке). Бэкапы —
по файлу.
Запуск из корня Grondheim-Ecosystem:
    python patch_yazyk_doliva.py
"""
import io
import sys
from pathlib import Path

SLOTS = {
    "A06": "brut",
    "A07": "avan",
    "A08": "cons",
}


def find_brain(aid):
    for base in (Path("GRONDHEIM_CITY") / "Биржа", Path("Биржа")):
        p = base / "цеха" / "торговый_хаос" / "слоты" / aid / "мозг.py"
        if p.exists():
            return p
    return None


OLD_TEXTS = {
    "A06": (
        '        "Выдай строго JSON {narrative, signal, diary_entry}. signal: "\n'
        '        "brut_verdict, brut_reason, brut_direction, brut_entry, brut_stop, "\n'
        '        "brut_lot. diary_entry: input, action, result(=null). Ничего вне JSON."\n'
    ),
    "A07": (
        '        "Выдай строго JSON {narrative, signal, "\n'
        '        "diary_entry}. signal: avan_verdict, avan_reason, avan_direction, "\n'
        '        "avan_entry, avan_stop, avan_lot. diary_entry: input, action, "\n'
        '        "result(=null). Ничего вне JSON."\n'
    ),
    "A08": (
        '        "как поступить. Выдай строго JSON {narrative, signal, "\n'
        '        "diary_entry}. signal: cons_verdict, cons_reason, cons_direction, "\n'
        '        "cons_entry, cons_stop, cons_lot. diary_entry: input, action, "\n'
        '        "result(=null). Ничего вне JSON."\n'
    ),
}


def new_text(aid, pref):
    return (
        '        # YAZYK_DOLIVA_V1: дописаны action/new_stop/add_lot — раньше\n'
        '        # эта, самая СВЕЖАЯ строка промта молчала про ведение позиции.\n'
        f'        "Выдай строго JSON {{narrative, signal, diary_entry}}.\\n"\n'
        f'        "Нет открытой позиции: signal ключи — {pref}_verdict "\n'
        f'        "(APPROVED/REJECTED), {pref}_reason, {pref}_direction, "\n'
        f'        "{pref}_entry, {pref}_stop, {pref}_lot.\\n"\n'
        f'        "Есть открытая позиция (см. блок \'position\' на столе): signal "\n'
        f'        "ключи — {pref}_action (ENTER/WAIT/HOLD/MOVE_STOP/ADD/CLOSE), "\n'
        f'        "{pref}_reason, {pref}_new_stop (если MOVE_STOP), {pref}_add_lot "\n'
        f'        "(если ADD).\\n"\n'
        '        "diary_entry: input, action, result(=null). Ничего вне JSON."\n'
    )


def main():
    changed = 0
    for aid, pref in SLOTS.items():
        path = find_brain(aid)
        if not path:
            print(f"[ПАТЧ] ⚠️  {aid}: мозг.py не найден — пропуск")
            continue
        src = path.read_text(encoding="utf-8")

        if "YAZYK_DOLIVA_V1" in src:
            print(f"[ПАТЧ] ✓ {aid}: уже починен — идемпотентно")
            continue

        old = OLD_TEXTS[aid]
        if old not in src:
            print(f"[ПАТЧ] ⚠️  {aid}: якорь не найден — файл изменён? проверь вручную")
            continue

        new = new_text(aid, pref)
        new_src = src.replace(old, new, 1)

        import ast
        try:
            ast.parse(new_src)
        except SyntaxError as e:
            print(f"[ПАТЧ] ✗ {aid}: правка ломает синтаксис ({e}) — НЕ пишу")
            continue

        bak = path.with_suffix(".py.bak_yazyk_doliva")
        if not bak.exists():
            bak.write_text(src, encoding="utf-8")
        path.write_text(new_src, encoding="utf-8")
        print(f"[ПАТЧ] ✓ {aid}: язык ведения дописан в финальную строку промта")
        changed += 1

    if changed:
        print(f"[ПАТЧ] ✅ Готово ({changed} мозгов). Последняя строка промта")
        print("[ПАТЧ]    теперь честно называет ADD/MOVE_STOP при живой позиции.")
    else:
        print("[ПАТЧ] ✓ Менять нечего (или уже применено).")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
