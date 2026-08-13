#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# KABINET_ZNAET_CEH_V1
"""
КАБИНЕТ ГОВОРИТ СОВЕТУ, КАКОЙ ЦЕХ.

    python patch_kabinet_znaet_ceh.py            посмотреть
    python patch_kabinet_znaet_ceh.py --sdelat   накатить

Запускать из КОРНЯ. После patch_svoy_stol_ceha.py.

ЗАЧЕМ

    Кабинет уже открывается по адресу любого цеха: `/torg/{цех}`. А
    кнопка РЫНОК звала Совет БЕЗ цеха — и Совет всегда собирал
    торговый хаос, чей бы кабинет ты ни открыл.

    Пока цех один, это незаметно. Появится второй — окажется, что
    открываешь мужской, а работает женский.

ЧТО СТАНЕТ

    · РЫНОК собирает Совет по тому цеху, чей кабинет открыт;
    · вахта запоминает не только инструмент и этаж, но и ЦЕХ — и
      сторожит свой. Две вахты в двух кабинетах не мешают друг другу;
    · если Совет постарше и про цех не знает — зовём как раньше, без
      него. Ничего не ломается.

    Вместе с цеховым столом и сканером картриджей это и есть «вставил
    цех — работает».
"""
import argparse
import ast
import py_compile
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
UI = KOREN / "Биржа" / "ui_torg.py"
MARKER = "# KABINET_ZNAET_CEH_V1 - marker"
BAK = ".bak_znaet_ceh"

STEZHKI = (
    ('вахта помнит цех', '    "бар": "",          # на какой свече стоим\n', '    "бар": "",          # на какой свече стоим\n    "цех": "",          # KABINET_ZNAET_CEH_V1: чей цех сторожим\n'),
    ('запомнить при включении', '        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,\n                       "бар": ""})\n', '        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,\n                       "бар": "", "цех": tseh_id})\n'),
    ('вахта зовёт свой цех', '        import asyncio as _a\n        import council\n        await _a.get_event_loop().run_in_executor(\n            None, lambda: council.wake_council(sym, tf))\n', '        import asyncio as _a\n        import council\n        # KABINET_ZNAET_CEH_V1: вахта сторожит СВОЙ цех, а не «какой-то».\n        _ceh = _VAHTA.get("цех") or ""\n        await _a.get_event_loop().run_in_executor(\n            None, lambda: (council.wake_council(sym, tf, ceh_id=_ceh)\n                           if _ceh else council.wake_council(sym, tf)))\n'),
    ('РЫНОК зовёт свой цех', '            _market_future = loop.run_in_executor(\n                None, lambda: council.wake_council(_sym_now, _tf_now,\n                                                   on_event=_on_event))\n', '            # KABINET_ZNAET_CEH_V1: кабинет открыт по адресу цеха —\n            # значит и Совет собираем по ЭТОМУ цеху, а не по зашитому.\n            # Совет постарше про цех не знает — тогда зовём как раньше.\n            def _zvat_sovet():\n                try:\n                    return council.wake_council(_sym_now, _tf_now,\n                                                on_event=_on_event,\n                                                ceh_id=tseh_id)\n                except TypeError:\n                    return council.wake_council(_sym_now, _tf_now,\n                                                on_event=_on_event)\n\n            _market_future = loop.run_in_executor(None, _zvat_sovet)\n'),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 60)
    print("КАБИНЕТ ЗНАЕТ ЦЕХ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 60)

    if not UI.exists():
        print("x не вижу Биржа/ui_torg.py — запускай из КОРНЯ")
        return 1
    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x якорь «{nazv}» найден {n} раз — файл не трогаю")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_torg.py"):
        return 1
    if suho:
        print("\nЭто был показ. Накатывать: "
              "python patch_kabinet_znaet_ceh.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nЖми РЫНОК — в чёрном окне стол сохранится с именем цеха,")
    print("чей кабинет открыт.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
