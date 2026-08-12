#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SVOYO_OKNO_V1
"""
СВОЁ ОКНО КАЖДОЙ ДВЕРИ — переходы открываются отдельной вкладкой.

    python patch_svoyo_okno.py            посмотреть
    python patch_svoyo_okno.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров). Правит только те файлы,
что найдёт: на материке кабинеты, на острове ещё и плашку.

ЗАЧЕМ

    Раньше любая дверь уводила из текущего окна: нажал «← БРАТ» — и
    кабинет Биржи закрылся, вернулся — он собирается заново. Теперь
    каждая дверь открывает СВОЮ вкладку, а прежняя остаётся на месте.

    Кабинет Биржи можно держать открытым и параллельно смотреть Маяк,
    Работу или Брата — каждый в своём окне.

ЧТО ПРАВИТСЯ

    Все переходы между страницами города: в кабинете Биржи, у Брата,
    на Странице Работы, у застройщика, на доске Маяка и в плашке
    острова. Внутренние действия (кнопки внутри страницы) не трогаются
    — только переходы по адресам.
"""
import argparse
import ast
import py_compile
import re
import shutil
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
MARKER = "# SVOYO_OKNO_V1 - marker"
BAK = ".bak_svoyo_okno"

FAYLY = [
    Path("ui_ostrov.py"),          # плашка острова
    Path("Биржа") / "ui_torg.py",
    Path("Брат") / "ui_brat.py",
    Path("ГОРОД") / "ui_rabota.py",
    Path("Архив") / "ui_arkhiv.py",
    Path("Маяк") / "ui_mayak.py",
    Path("ui_zastroyshchik.py"),
    Path("ui_perevozka.py"),
]

# ui.navigate.to("/что-то")  →  ui.navigate.to("/что-то", new_tab=True)
PEREHOD = re.compile(r'ui\.navigate\.to\((\s*)(["\'])(/[^"\']*)\2\s*\)')

# двери плашки острова — обычные ссылки
SSYLKA = re.compile(r'<a href="(/[^"]*)">')

# плашка острова строит двери через переменную: navigate.to(k)
PEREMENNAYA = re.compile(
    r'ui\.navigate\.to\((\s*)([a-zA-Z_][a-zA-Z_0-9]*)\s*\)')


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"    x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"    x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def odin(otn: Path, suho: bool) -> int:
    """Возвращает число правок; -1 — беда."""
    put = KOREN / otn
    if not put.exists():
        return 0
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {otn}: уже накатано")
        return 0

    novy, n1 = PEREHOD.subn(
        lambda m: f'ui.navigate.to({m.group(1)}{m.group(2)}{m.group(3)}'
                  f'{m.group(2)}, new_tab=True)', tekst)
    novy, n2 = SSYLKA.subn(r'<a href="\1" target="_blank">', novy)
    novy, n3 = PEREMENNAYA.subn(
        lambda m: f'ui.navigate.to({m.group(1)}{m.group(2)}, new_tab=True)',
        novy)
    n2 += n3

    if n1 + n2 == 0:
        print(f"  {otn}: переходов не нашёл — пропускаю")
        return 0

    novy = novy.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(novy, otn.name):
        return -1

    print(f"  {otn}: {n1 + n2} "
          f"({'ляжет' if suho else 'правлено'})")
    if not suho:
        shutil.copy2(put, put.with_suffix(put.suffix + BAK))
        put.write_text(novy, encoding="utf-8")
    return n1 + n2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 60)
    print("СВОЁ ОКНО КАЖДОЙ ДВЕРИ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 60)
    print()

    vsego = 0
    for otn in FAYLY:
        n = odin(otn, suho)
        if n < 0:
            print("\n! файл не тронут — дальше не иду")
            return 1
        vsego += n

    print("-" * 60)
    if not vsego:
        print("Править нечего.")
        return 0
    if suho:
        print(f"Всего переходов: {vsego}. "
              f"Накатывать: python patch_svoyo_okno.py --sdelat")
        return 0
    print(f"Готово: {vsego} переходов открываются своим окном.")
    print("Кабинет Биржи теперь можно не закрывать — вахта в нём и так")
    print("живёт при городе, а вкладки больше не топчут друг друга.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
