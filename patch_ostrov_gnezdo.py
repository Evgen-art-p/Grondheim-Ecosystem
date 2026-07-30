# -*- coding: utf-8 -*-
# patch_ostrov_gnezdo.py — пульс острова зажигает гнездо на Маяке
"""
До этого патча: причал (prichal.py) принимал пульс и просто писал
карточку на диск (Маяк/острова/{id}/город.json) — Маяк об этом никак
не знал, гнёзда не шевелились.

После патча: main.py, приняв пульс, ещё и втыкает гнездо рода
«остров» (gnezda.votknut). Каждый новый пульс продлевает срок
(gnezda.podderzhat через тот же votknut). Не прислал пульс 30 минут —
гнездо гаснет само (SEANS_MINUT в gnezda.py), как любой «живой».

prichal.py НЕ трогаем — он самодостаточен нарочно (комментарий в
самом файле: не импортирует ни город, ни маяк). Крючок к gnezda
ставим только в main.py — это уже сторона материка, не общий контракт
с островом.

Идемпотентно: если маркер PRICHAL_GNEZDO_V1 уже стоит — патч молча
выходит, второй раз не портит файл.

Запуск (из корня репо Grondheim-Ecosystem):
    python patch_ostrov_gnezdo.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

TARGET = Path("main.py")
MARKER = "PRICHAL_GNEZDO_V1"

STAROE = (
    '    try:\n'
    '        telo = await request.json()\n'
    '    except Exception:\n'
    '        return {"ok": False, "причина": "тело не разобралось как JSON", "id": ""}\n'
    '    return _prichal.prinyat(telo, request.headers.get(_prichal.KEY_HEADER, ""))\n'
)

NOVOE = (
    '    try:\n'
    '        telo = await request.json()\n'
    '    except Exception:\n'
    '        return {"ok": False, "причина": "тело не разобралось как JSON", "id": ""}\n'
    '    rez = _prichal.prinyat(telo, request.headers.get(_prichal.KEY_HEADER, ""))\n'
    '\n'
    '    # ГНЕЗДО ОСТРОВА — PRICHAL_GNEZDO_V1\n'
    '    # Пульс дошёл — зажигаем гнездо рода «остров». Род не в числе\n'
    '    # постоянных (см. POSTOYANNYE в gnezda.py), поэтому если остров\n'
    '    # замолчит дольше SEANS_MINUT — гнездо погаснет само, честно.\n'
    '    if rez.get("ok"):\n'
    '        try:\n'
    '            import gnezda as _gnezda\n'
    '            _gnezda.votknut(\n'
    '                rod="остров",\n'
    '                imya=telo.get("имя") or rez.get("id", ""),\n'
    '                klyuch=f"prichal:{rez.get(\'id\', \'\')}",\n'
    '                chto="пульс с границы",\n'
    '            )\n'
    '        except Exception:\n'
    '            pass\n'
    '\n'
    '    return rez\n'
)


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускай из корня Grondheim-Ecosystem")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"✓ уже применено ({MARKER} найден в {TARGET}) — выхожу, ничего не трогаю")
        return

    if STAROE not in text:
        print("✗ не нашёл ожидаемый кусок в main.py — файл, видимо, менялся "
              "с тех пор, как я его смотрел в последний раз. Патч не применён, "
              "ничего не сломано.")
        sys.exit(1)

    if text.count(STAROE) != 1:
        print(f"✗ ожидаемый кусок встретился {text.count(STAROE)} раз, а "
              "должен ровно 1 — на всякий случай не трогаю файл.")
        sys.exit(1)

    backup = TARGET.with_suffix(TARGET.suffix + ".bak_ostrov_gnezdo")
    shutil.copy2(TARGET, backup)
    print(f"· бэкап сохранён: {backup}")

    novyy_text = text.replace(STAROE, NOVOE)

    # проверка синтаксиса ДО записи на диск
    try:
        ast.parse(novyy_text)
    except SyntaxError as e:
        print(f"✗ после патча получился синтаксически неверный файл: {e}")
        print("  на диск ничего не писал, бэкап можешь удалить.")
        sys.exit(1)

    TARGET.write_text(novyy_text, encoding="utf-8")
    print(f"✓ {TARGET} пропатчен")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("✓ py_compile: чисто")
    except py_compile.PyCompileError as e:
        print(f"✗ py_compile ругается: {e}")
        print(f"  откатываю из бэкапа...")
        shutil.copy2(backup, TARGET)
        print("  откат сделан, main.py как было")
        sys.exit(1)

    print("\nГотово. Теперь любой настоящий пульс с острова будет ещё и "
          "зажигать гнездо на /mayak — не только писать карточку на диск.")


if __name__ == "__main__":
    main()
