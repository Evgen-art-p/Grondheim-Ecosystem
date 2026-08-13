#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VAHTA_ZA_POLKOY_V1
"""
ВАХТА ИДЁТ ЗА ПОЛКОЙ · и строка по-человечески.

    python patch_vahta_za_polkoy.py            посмотреть
    python patch_vahta_za_polkoy.py --sdelat   накатить

Запускать из КОРНЯ.

ЧТО БЫЛО НЕ ТАК

    1. ВАХТА ЖИЛА СВОЕЙ ЖИЗНЬЮ.
       Она запоминала инструмент в миг нажатия и с тех пор сторожила
       только его. Сменил на полке — работаешь по одному, а вахта
       сторожит другое. На экране это и было видно: «работаем EURUSD
       H4… вахта: GBPUSD H4». Я сам так задумал и сам же был неправ:
       помнить старое оказалось хуже, чем не помнить.

    2. СТРОКА БЫЛА НАБОРОМ СЛОВ.
       «EURUSD H4 · Нина · Синди · A08 свободно · вахта: GBPUSD H4» —
       из этого не понять ни кто чем занят, ни почему там разное.

ЧТО СТАНЕТ

    · вахта идёт за полкой: что выбрано, то и сторожит. Сменил
      инструмент — она сменила без разговоров, и в чёрном окне пишет
      об этом строкой;

    · строка читается словами:

          работаем: EURUSD H4  ·  за столом: Нина, Синди  ·  вахта идёт

      Чем работаем — зелёным. Кто за столом — по именам. Идёт вахта
      или нет — да или нет, без подробностей: подробности теперь те же,
      что и у всех.
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
MARKER = "# VAHTA_ZA_POLKOY_V1 - marker"
BAK = ".bak_vahta_polka"

STEZHKI = (
    ("строка по-человечески", '        try:\n            _s, _t = _aktivnyy_rynok()\n            kuski = [f\'<b style="color:rgba(0,255,136,0.85)">{_s} {_t}</b>\']\n            for _sl in ("A06", "A07", "A08"):\n                _row = _agent_row(roster, _sl)\n                if _row and _row.get("resident"):\n                    kuski.append(_row["resident"].get("имя", _sl))\n                else:\n                    kuski.append(f\'<span style="opacity:.4">{_sl} свободно\'\n                                 f\'</span>\')\n            if _VAHTA["идёт"]:\n                kuski.append(f\'<span style="color:#00ccff">вахта: \'\n                             f\'{_VAHTA["инструмент"]} {_VAHTA["этаж"]}</span>\')\n            el.content = "  ·  ".join(kuski)\n        except Exception:\n            pass\n', '        try:\n            _s, _t = _aktivnyy_rynok()\n            # VAHTA_ZA_POLKOY_V1: по-человечески. Было «EURUSD H4 · Нина ·\n            # Синди · A08 свободно · вахта: GBPUSD H4» — набор слов, из\n            # которого не понять, кто чем занят и почему разное.\n            _kto = [_row["resident"].get("имя", _sl)\n                    for _sl in ("A06", "A07", "A08")\n                    for _row in [_agent_row(roster, _sl)]\n                    if _row and _row.get("resident")]\n            _text = (f\'работаем: <b style="color:rgba(0,255,136,0.9)">\'\n                     f\'{_s} {_t}</b>\')\n            if _kto:\n                _text += (f\'&nbsp;&nbsp;·&nbsp;&nbsp;за столом: \'\n                          f\'{", ".join(_kto)}\')\n            else:\n                _text += (\'&nbsp;&nbsp;·&nbsp;&nbsp;<span style="opacity:.5">\'\n                          \'за столом никого</span>\')\n            if _VAHTA["идёт"]:\n                _text += (\'&nbsp;&nbsp;·&nbsp;&nbsp;\'\n                          \'<span style="color:#00ccff">вахта идёт</span>\')\n            el.content = _text\n        except Exception:\n            pass\n'),
    ("вахта идёт за полкой", '        state["active_asset"] = i\n        a = assets[i]\n        ui.notify(f"Работаем: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n        update_files_display()\n', '        state["active_asset"] = i\n        a = assets[i]\n        # VAHTA_ZA_POLKOY_V1: вахта идёт ЗА ПОЛКОЙ, а не помнит, что было\n        # при нажатии. Раньше выходило так: работаем EURUSD, а вахта\n        # сторожит GBPUSD, потому что её включали на нём.\n        if _VAHTA["идёт"]:\n            _VAHTA.update({"инструмент": a["symbol"],\n                           "этаж": a["timeframe"], "бар": ""})\n            print(f"[ВАХТА] ↪ теперь сторожу {a[\'symbol\']} {a[\'timeframe\']}")\n        ui.notify(f"Работаем: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n        update_files_display()\n'),
    ("и при включении тоже", '        _s, _t = _aktivnyy_rynok()\n        # что сторожим — запоминаем СЕЙЧАС: вахта живёт при городе и\n        # полки кабинета потом не увидит.\n        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,\n                       "бар": ""})\n', '        _s, _t = _aktivnyy_rynok()\n        # VAHTA_ZA_POLKOY_V1: берём выбранное сейчас, и дальше вахта\n        # идёт за полкой — сменил инструмент, сменилось и то, что она\n        # сторожит. Помнить старое оказалось хуже, чем не помнить.\n        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,\n                       "бар": ""})\n'),
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
    print("ВАХТА ИДЁТ ЗА ПОЛКОЙ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
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
            print("    (нужны patch_prosto_i_rovno и patch_naznacheniya_proch)")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_torg.py"):
        return 1

    if suho:
        print("\nЭто был показ. Накатывать: "
              "python patch_vahta_za_polkoy.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nПерезапусти город. Включи вахту, потом смени инструмент на")
    print("полке — в чёрном окне будет видно, что она пошла за тобой.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
