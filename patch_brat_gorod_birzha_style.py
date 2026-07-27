# -*- coding: utf-8 -*-
"""
patch_brat_gorod_birzha_style.py

Запускать из КОРНЯ репозитория:
    python patch_brat_gorod_birzha_style.py

Что делает (и только это — первый ряд с кнопками хедера НЕ трогает):
  Кнопка "ГОРОД" во втором ряду (stage-toolbar, класс .brat-gate)
  меняет вид на стиль кнопки "📡 РЫНОК" из Биржа/ui_torg.py:
    - фон: зелёно-голубой градиент rgba(0,255,136,0.15)→rgba(0,204,255,0.10)
    - рамка: 1px solid rgba(0,255,136,0.35) — но ТОЛЬКО сверху/слева/справа,
      снизу рамки нет (border-bottom: none) — кнопка растёт прямо из
      нижней границы поля, без собственной "подошвы", как РЫНОК на скрине
    - скругление только сверху (8px 8px 0 0), низ плоский — сливается
      с полем под кнопкой
    - текст: rgba(255,255,255,0.9), font-weight:700 (было #c9a84c, 400)
  И высота поля увеличена на треть: было min-height:34px → стало 45px
  (34 * 4/3 ≈ 45), ширина расфиксирована (было жёстко 130px — теперь
  auto с min-width:150px, чтобы кнопка не была тесной при новой высоте).

ВЕРСИЯ 2 — вместо точного посимвольного совпадения ищет CSS-правила
.brat-gate{...}, .brat-gate .q-btn__content{...}, .brat-gate:hover{...}
через regex (по имени селектора, не по пробелам/отступам/переносам
строк) — переживает любые различия в форматировании файла.

Перед записью — бэкап рядом: Брат/ui_brat.py.bak_before_gorod_style
Если селектор .brat-gate вообще не найден в файле — ничего не меняет
и прямо об этом говорит, с диагностикой.
"""

import re
import sys
from pathlib import Path

TARGET = Path("Брат") / "ui_brat.py"

NEW_GATE_RULE = '''.brat-gate{ min-height:45px !important; padding:10px 22px !important;
            border-radius:8px 8px 0 0 !important;
            min-width:150px !important; width:auto !important; max-width:none !important;
            background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10)) !important;
            border-top: 1px solid rgba(0,255,136,0.35) !important;
            border-left: 1px solid rgba(0,255,136,0.35) !important;
            border-right: 1px solid rgba(0,255,136,0.35) !important;
            border-bottom: none !important;
            color: rgba(255,255,255,0.9) !important; font-weight:700 !important; font-size:0.85rem !important;
            text-transform:none !important; }'''

NEW_CONTENT_RULE = '''.brat-gate .q-btn__content{ width:100% !important; justify-content:center !important; }'''

NEW_HOVER_RULE = '''.brat-gate:hover{ background: linear-gradient(135deg, rgba(0,255,136,0.24), rgba(0,204,255,0.16)) !important; }'''

# Каждый паттерн ловит ОДНО CSS-правило целиком: от селектора до первой
# закрывающей "}". В простых объявлениях (без вложенных блоков) это
# безопасно — а .brat-gate правила именно такие.
PATTERNS = [
    (re.compile(r'\.brat-gate\s*\{.*?\}', re.DOTALL), NEW_GATE_RULE, ".brat-gate{...}"),
    (re.compile(r'\.brat-gate\s+\.q-btn__content\s*\{.*?\}', re.DOTALL), NEW_CONTENT_RULE, ".brat-gate .q-btn__content{...}"),
    (re.compile(r'\.brat-gate:hover\s*\{.*?\}', re.DOTALL), NEW_HOVER_RULE, ".brat-gate:hover{...}"),
]


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН файл: {TARGET.resolve()}")
        print("Запусти скрипт из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")
    original = text

    if ".brat-gate" not in text:
        print("Патч НЕ применён — в файле вообще нет селектора .brat-gate.")
        print("Файл не тронут. Проверь, тот ли это ui_brat.py.")
        sys.exit(2)

    problems = []
    new_text = text
    for pattern, replacement, label in PATTERNS:
        matches = pattern.findall(new_text)
        if len(matches) == 0:
            problems.append(f"не найдено правило {label}")
            continue
        if len(matches) > 1:
            problems.append(f"правило {label} встречается {len(matches)} раз (ожидалось 1) — пропущено, чтобы не сломать лишнее")
            continue
        new_text = pattern.sub(lambda m: replacement, new_text, count=1)

    if problems:
        print("Патч НЕ применён полностью — есть нестыковки:")
        for p in problems:
            print(f"  - {p}")
        idx = text.find(".brat-gate")
        snippet = text[max(0, idx - 60):idx + 300]
        print("\nВот что реально стоит в файле вокруг .brat-gate (для сверки):\n")
        print(snippet)
        print("\nФайл НЕ изменён.")
        sys.exit(3)

    backup = TARGET.with_name(TARGET.name + ".bak_before_gorod_style")
    backup.write_text(original, encoding="utf-8")
    TARGET.write_text(new_text, encoding="utf-8")

    print(f"Бэкап сохранён: {backup}")
    print(f"Патч применён: {TARGET}")
    print("Кнопка ГОРОД теперь в стиле РЫНОК из Биржи, высота +1/3,")
    print("низ без рамки и без скругления — растёт из границы поля.")
    print("Ряд кнопок хедера не тронут.")


if __name__ == "__main__":
    main()
