# -*- coding: utf-8 -*-
"""
PATCH: ЧЕСТНЫЙ RECONFIGURE — правка reportAttributeAccessIssue у Pylance.
Маркер: RECONFIGURE_HONEST_V1

НАЙДЕНО (Pylance): sys.stdout типизирован как TextIO (абстрактный
интерфейс) — у него метода reconfigure НЕТ по объявлению типа. Метод
реально есть только у TextIOWrapper — конкретного класса, которым
sys.stdout ЯВЛЯЕТСЯ во время выполнения, но не то, что заявлено типом.

ПРОВЕРЕНО через pyright (тот же движок, что у Pylance), не на глаз:
  try/except Exception: pass           → ошибка ОСТАЁТСЯ (try не лечит
                                          статический анализ, только
                                          рантайм)
  if hasattr(...): ...                 → ошибка ОСТАЁТСЯ (не помогает
                                          здесь, проверено)
  if isinstance(sys.stdout, TextIOWrapper): ...
                                        → 0 ошибок — ЧЕСТНАЯ починка,
                                          не подавление. Спрашивает
                                          "ты правда тот класс?" — и
                                          если да, обращается к методу,
                                          который у него правда есть.

Правит 4 живых файла (patch-скрипты уже в архиве, их не трогаем):
  kalibrovka_core.py, sostoyanie.py,
  Биржа/cartridge_registry.py, Биржа/kalibrovka.py

Идемпотентен: если isinstance-проверка уже стоит — не трогает.

Запуск из корня репо:  python patch_reconfigure_honest.py
"""
import sys
import io
import ast
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
MARKER = "RECONFIGURE_HONEST_V1"

# (файл, старый_блок, новый_блок) — по одному на каждый вариант импорта sys
FIXES = [
    (
        REPO / "kalibrovka_core.py",
        '''    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass''',
        '''    import sys
    import io
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")''',
    ),
    (
        REPO / "sostoyanie.py",
        '''    import sys, tempfile, shutil
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass''',
        '''    import sys, tempfile, shutil, io
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")''',
    ),
    (
        REPO / "Биржа" / "cartridge_registry.py",
        '''    import sys as _s
    try:
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass''',
        '''    import sys as _s
    import io as _io
    if isinstance(_s.stdout, _io.TextIOWrapper):
        _s.stdout.reconfigure(encoding="utf-8")''',
    ),
    (
        REPO / "Биржа" / "kalibrovka.py",
        '''    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass''',
        '''    import io as _io
    if isinstance(_sys.stdout, _io.TextIOWrapper):
        _sys.stdout.reconfigure(encoding="utf-8")''',
    ),
    (
        # ВТОРАЯ, ОТДЕЛЬНАЯ ошибка (не reconfigure): now_utc: datetime = None
        # объявлен ОБЯЗАТЕЛЬНЫМ datetime, а по умолчанию None — неточно.
        # Честная типизация: datetime | None = None. Настоящая ошибка,
        # не квирк стаба — сама сигнатура была неверной.
        REPO / "Биржа" / "kalibrovka.py",
        '''def aktivnaya_sessiya(now_utc: datetime = None) -> dict | None:''',
        '''def aktivnaya_sessiya(now_utc: datetime | None = None) -> dict | None:''',
    ),
    (
        REPO / "Биржа" / "kalibrovka.py",
        '''def kalibrovat_ceh(ceh_id: str, now_utc: datetime = None, llm=None,
                   stamp: bool = True) -> dict:''',
        '''def kalibrovat_ceh(ceh_id: str, now_utc: datetime | None = None, llm=None,
                   stamp: bool = True) -> dict:''',
    ),
]


def install():
    print(f"═══ PATCH {MARKER} — честный reconfigure + datetime|None ═══")
    print(f"репо: {REPO}")

    # группируем правки по файлу — читаем/пишем каждый файл один раз
    po_faylam = {}
    for path, old, new in FIXES:
        po_faylam.setdefault(path, []).append((old, new))

    vsego_pochineno = 0
    vsego_uje = 0

    for path, pravki in po_faylam.items():
        rel = path.relative_to(REPO) if path.is_relative_to(REPO) else path
        if not path.exists():
            print(f"  ○ нет файла (пропускаю): {rel}")
            continue
        src = path.read_text(encoding="utf-8")
        changed_this_file = False
        for old, new in pravki:
            if new in src:
                vsego_uje += 1
                continue
            if old not in src:
                print(f"  ✖ якорь не найден в {rel} (для одной из правок) — "
                      f"пропускаю её, остальные пробую")
                continue
            src = src.replace(old, new)
            changed_this_file = True
            vsego_pochineno += 1
        if changed_this_file:
            try:
                ast.parse(src)
            except SyntaxError as e:
                print(f"  ✖ СИНТАКСИС БИТЫЙ после правки {rel}: {e} — не сохраняю")
                continue
            path.write_text(src, encoding="utf-8")
            print(f"  ✔ починен: {rel}")
        else:
            print(f"  ○ уже всё честно: {rel}")

    print("\n═══ ИТОГ ═══")
    print(f"  починено правок: {vsego_pochineno}, уже было: {vsego_uje}")
    print("  Проверь: pyright <файл> — должно быть 0 errors на каждом.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
