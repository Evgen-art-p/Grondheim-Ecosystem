# -*- coding: utf-8 -*-
# patch_letopis_birzha_hygiene_note.py — LETOPIS_BIRZHA_HYGIENE_NOTE_V1
# ─────────────────────────────────────────────────────────────
# Короткая правка ЛЕТОПИСЬ_ГРОНДХЕЙМА.md (в корне репо) — по её же
# собственной конвенции (см. шапку v4.2): Летопись держит факт
# города ЦЕЛИКОМ, БИРЖА.md — подробности одного квартала. Здесь
# НЕ дублируем список патчей гигиены типов (он целиком в БИРЖА.md
# §7а) — только одна ссылающаяся строка внутри уже существующего
# абзаца про торговый цех, чтобы Летопись не соврала свежему Брату,
# что tester_express.py всё ещё на флат-импортах.
#
# ЗАПУСК из корня:  python patch_letopis_birzha_hygiene_note.py
# Требует, чтобы БИРЖА.md уже был обновлён
# (patch_birzha_md_typing_pass.py) — иначе ссылка будет в никуда.
# Идемпотентен, бэкап .md.bak_*.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import shutil
import sys
from pathlib import Path
from datetime import datetime

MARKER = "LETOPIS_BIRZHA_HYGIENE_NOTE_V1"
TARGET = Path("ЛЕТОПИСЬ_ГРОНДХЕЙМА.md")

OLD = '''   проверкой), затем — нога «Опыт» Стола Трейдера (Чертёж, Гл.5.3):
   pnl.jsonl копится, но в решение агента ещё не подаётся.
3. ЦЕХ СКАЛЬПЕРОВ-СНАЙПЕРОВ'''

NEW = '''   проверкой), затем — нога «Опыт» Стола Трейдера (Чертёж, Гл.5.3):
   pnl.jsonl копится, но в решение агента ещё не подаётся.
   ГИГИЕНА (09.07, вторая половина дня): Pylance прошёлся по всей
   Бирже — закрыто патчами (детали и гарантия нулевого изменения
   поведения: БИРЖА.md §7а). Заодно tester_express.py дозрел с
   флат-импортов на _slot_brain — был долг с самого переноса.
3. ЦЕХ СКАЛЬПЕРОВ-СНАЙПЕРОВ'''

EOF_MARKER = f"\n<!-- {MARKER} -->\n"


def main():
    if not TARGET.exists():
        print(f"НЕ НАЙДЕН: {TARGET} (запусти из корня Grondheim-Ecosystem)")
        sys.exit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("Уже применено — идемпотентность держит, ничего не меняю.")
        return

    if OLD not in src:
        print("⚠️  Якорь не найден — файл менялся с момента диагностики.")
        print("Ничего не режу — правь руками или пришли свежий файл.")
        sys.exit(1)

    backup = TARGET.with_suffix(f".md.bak_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(TARGET, backup)
    print(f"Бэкап: {backup}")

    src = src.replace(OLD, NEW, 1) + EOF_MARKER
    TARGET.write_text(src, encoding="utf-8")
    print("Готово: короткая ссылка на гигиену типов добавлена в Летопись.")


if __name__ == "__main__":
    main()
