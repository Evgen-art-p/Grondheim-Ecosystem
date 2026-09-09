# -*- coding: utf-8 -*-
# POLYA_PRIKAZA_PROSHCHAYUT_V1 — приказ не теряет «почему»
"""
ПРИКАЗ БОЛЬШЕ НЕ ТЕРЯЕТ ПРИЧИНУ

ЧТО СЛУЧИЛОСЬ. Первый живой приказ прошёл — и пришёл без «зачем».
В логе видно причину: модель прислала поле с пробелом на конце —
`'почему '`. Рука спрашивала `почему`, получала пустоту, и причина
не легла ни на табло, ни в след.

Приказ исполнился верно. Потерялось ровно то, ради чего след и
заводится: почему он это сделал.

ПОЧЕМУ ЭТО НАШЕ, А НЕ ЕГО. Имя руки поиск уже прощает — там
разобраны и кириллический двойник латинской буквы, и мелкая
опечатка (RUKI_TREYDERA_V1). А имена ПОЛЕЙ внутри руки сверялись
знак в знак. Та же болезнь, просто этажом ниже.

ЧТО ДЕЛАЕТ ПАТЧ. Одна правка в `Биржа/ruki_treydera.py`: перед
разбором приказа имена полей чистятся — пробелы по краям и регистр.
Значения не трогаются вовсе. Приказ, разобранный не по форме,
по-прежнему честно отбивается — мы прощаем описку в имени поля, а
не выдумываем недостающее.

Требует, чтобы уже стоял RUKA_PRIKAZA_V1.

БЕЗОПАСНОСТЬ: .bak_polya, идемпотентен (маркер), синтаксис
проверяется до записи, `--suho` ничего не трогает.

    python pochinit_polya_prikaza.py --suho
    python pochinit_polya_prikaza.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "POLYA_PRIKAZA_PROSHCHAYUT_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ruki_treydera.py"

STAROE = '''    def _otdat(args: dict) -> str:
        from datetime import datetime, timezone
        chto = str(args.get("что", "")).upper().strip()'''

NOVOE = '''    def _otdat(args: dict) -> str:
        from datetime import datetime, timezone
        # POLYA_PRIKAZA_PROSHCHAYUT_V1: имя поля чистим от пробелов и
        # регистра. Первый живой приказ пришёл с полем «почему » — с
        # пробелом на конце — и причина потерялась целиком. Имя РУКИ
        # поиск уже прощает; имена полей сверялись знак в знак, а это
        # та же болезнь этажом ниже. Значения не трогаем: прощаем
        # описку в имени, ничего не выдумывая за трейдера.
        args = {str(_k).strip().lower(): _v
                for _k, _v in (args or {}).items()}
        chto = str(args.get("что", "")).upper().strip()'''


def main():
    print()
    print("ПРИКАЗ НЕ ТЕРЯЕТ ПРИЧИНУ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if "RUKA_PRIKAZA_V1" not in txt:
        print("!! руки приказа ещё нет — сперва postavit_ruku_prikaza.py")
        return
    if txt.count(STAROE) != 1:
        print(f"!! якорь встречается {txt.count(STAROE)} раз(а) — не трогаю")
        return

    novy = txt.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return

    print("  чистка имён полей — вставлена")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_polya"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ruki_treydera.py.bak_polya")
    print()


if __name__ == "__main__":
    main()
