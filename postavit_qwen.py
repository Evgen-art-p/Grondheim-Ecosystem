# -*- coding: utf-8 -*-
# QWEN_V_SPISKE_V1 — Qwen 3.5 в кабинете Биржи
"""
QWEN В СПИСКЕ МОДЕЛЕЙ

Слово Шефа 10.09: `qwen/qwen3.5-397b-a17b` запечатать в модалку
кабинета Биржи.

ЧТО ДЕЛАЕТ. Добавляет модель в `MODELS_CATALOG` в `Биржа/ui_torg.py`
— в тот самый список, из которого кабинет строит выпадающий выбор.
Поле «своя модель с OpenRouter» никуда не девается: список для
постоянных, поле для разовых проб.

ЦЕНУ НЕ ВЫДУМЫВАЮ. У остальных в списке цена стоит рядом с именем —
её видно при выборе. Здесь ставится прочерк: сколько стоит эта
модель на OpenRouter, я не знаю, а придуманное число хуже
отсутствующего — по нему станут считать. Посмотришь на openrouter.ai
— скажи, впишу одной строкой.

ЧЕГО НЕ ТРОГАЕТ: модель по умолчанию (кабинет по-прежнему
открывается на той, что видит кадр), Академию, поле своей модели.

БЕЗОПАСНОСТЬ: .bak_qwen, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_qwen.py --suho
    python postavit_qwen.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "QWEN_V_SPISKE_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

MODEL_ID = "qwen/qwen3.5-397b-a17b"

STAROE = ('    {"id": "anthropic/claude-sonnet-4-5",      '
          '"name": "Claude Sonnet 4.5", "price": "$3/$15"},\n]')

NOVOE = ('    {"id": "anthropic/claude-sonnet-4-5",      '
         '"name": "Claude Sonnet 4.5", "price": "$3/$15"},\n'
         '    # QWEN_V_SPISKE_V1 (слово Шефа 10.09). Цена прочерком:\n'
         '    # выдуманное число хуже отсутствующего — по нему станут\n'
         '    # считать. Посмотрит на openrouter.ai — впишем.\n'
         '    {"id": "qwen/qwen3.5-397b-a17b",           '
         '"name": "Qwen 3.5 397B",   "price": "—"},\n]')


def main():
    print()
    print("QWEN В СПИСКЕ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt or MODEL_ID in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if txt.count(STAROE) != 1:
        print(f"!! якорь списка встречается {txt.count(STAROE)} раз(а) — "
              f"не трогаю")
        return

    novy = txt.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return

    print("  модель добавлена в MODELS_CATALOG")
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_qwen"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_qwen")
    print("Модель по умолчанию не менялась.")
    print()


if __name__ == "__main__":
    main()
