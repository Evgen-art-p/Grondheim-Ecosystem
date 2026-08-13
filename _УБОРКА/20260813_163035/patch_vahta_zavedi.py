#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VAHTA_ZAVEDI_LYUBOY_V1
"""
ВАХТА ЗАВОДИТСЯ ЛЮБЫМ СПОСОБОМ — и честно говорит, если не вышло.

    python patch_vahta_zavedi.py            посмотреть
    python patch_vahta_zavedi.py --sdelat   накатить

Запускать из КОРНЯ.

ЧТО СЛУЧИЛОСЬ

    В чёрном окне: «ВАХТА ⚠️ не завелась: 'App' object has no attribute
    'timer'». А следом — «▶ стою на EURUSD H1».

    То есть кнопка горела, вахта числилась на посту, а тика не было
    вовсе: в твоей версии NiceGUI того таймера, которым я её заводил,
    просто нет. Худший вид поломки — когда выглядит живым.

ЧТО СТАНЕТ

    Три захода по очереди: городской таймер, если он есть; своя петля
    в общем круге; отдельная нитка. Хоть один да сработает — в любой
    версии.

    А если не вышло ни одного, кнопка НЕ загорится и ты увидишь прямо:
    «вахта не завелась, жми РЫНОК руками». Молчать об этом она больше
    не будет.
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
MARKER = "# VAHTA_ZAVEDI_LYUBOY_V1 - marker"
BAK = ".bak_zavedi"

STEZHKI = (
    ("три способа завести", 'def _vahta_zavesti():\n    """Один таймер на весь город, не на каждое окно."""\n    global _VAHTA_ZAVEDENA\n    if _VAHTA_ZAVEDENA:\n        return\n    try:\n        from nicegui import app as _app\n        _app.timer(20.0, _vahta_sluzhba)\n        _VAHTA_ZAVEDENA = True\n        print("[ВАХТА] ⏱ городская вахта заведена (тик 20 сек)")\n    except Exception as e:\n        print(f"[ВАХТА] ⚠️  не завелась: {e}")\n', 'def _vahta_zavesti():\n    """Один тик на весь город, не на каждое окно.\n\n    VAHTA_ZAVEDI_LYUBOY_V1: раньше звался только app.timer — в NiceGUI\n    постарше его нет, и вахта молча не заводилась. Кнопка горела, а\n    тика не было: худший вид поломки. Теперь три захода по очереди,\n    и если не вышло ни одного — говорим об этом вслух, а не молчим.\n    """\n    global _VAHTA_ZAVEDENA\n    if _VAHTA_ZAVEDENA:\n        return\n    # 1. городской таймер NiceGUI — если он в этой версии есть\n    try:\n        from nicegui import app as _app\n        if hasattr(_app, "timer"):\n            _app.timer(20.0, _vahta_sluzhba)\n            _VAHTA_ZAVEDENA = True\n            print("[ВАХТА] ⏱ заведена городским таймером (тик 20 сек)")\n            return\n    except Exception as e:\n        print(f"[ВАХТА] городской таймер не вышел: {e}")\n    # 2. своя петля в общем круге — работает в любой версии\n    try:\n        import asyncio as _a\n\n        async def _petlya():\n            print("[ВАХТА] ⏱ заведена своей петлёй (тик 20 сек)")\n            while True:\n                await _a.sleep(20)\n                try:\n                    await _vahta_sluzhba()\n                except Exception as e:\n                    print(f"[ВАХТА] ⚠️  сбой тика: {e}")\n\n        _a.get_event_loop().create_task(_petlya())\n        _VAHTA_ZAVEDENA = True\n        return\n    except Exception as e:\n        print(f"[ВАХТА] своя петля не вышла: {e}")\n    # 3. отдельная нитка — последний заход\n    try:\n        import asyncio as _a\n        import threading as _t\n\n        def _nitka():\n            print("[ВАХТА] ⏱ заведена отдельной ниткой (тик 20 сек)")\n            while True:\n                _time.sleep(20)\n                try:\n                    _a.run(_vahta_sluzhba())\n                except Exception as e:\n                    print(f"[ВАХТА] ⚠️  сбой тика: {e}")\n\n        import time as _time\n        _t.Thread(target=_nitka, daemon=True).start()\n        _VAHTA_ZAVEDENA = True\n        return\n    except Exception as e:\n        print(f"[ВАХТА] ⚠️  НЕ ЗАВЕЛАСЬ ВОВСЕ: {e}")\n        print("[ВАХТА] ⚠️  кнопка гореть будет, а сторожить некому — "\n              "нажимай РЫНОК руками")\n\n\n'),
    ("не завелась — сказать", '        _vahta_zavesti()\n        _vahta_vid()\n        ui.notify(f"⏱ вахта: сторожу {_s} {_t}. Идёт, пока поднят город "\n                  f"— окно можно закрыть", type="info")\n', '        _vahta_zavesti()\n        _vahta_vid()\n        if _VAHTA_ZAVEDENA:\n            ui.notify(f"⏱ вахта: сторожу {_s} {_t}. Идёт, пока поднят "\n                      f"город — окно можно закрыть", type="info")\n        else:\n            # VAHTA_ZAVEDI_LYUBOY_V1: не завелась — так и скажем, а не\n            # оставим гореть кнопку впустую.\n            _VAHTA["идёт"] = False\n            _vahta_vid()\n            ui.notify("⚠ вахта не завелась — смотри чёрное окно. "\n                      "Пока жми РЫНОК руками.", type="negative")\n'),
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
    print("ВАХТА ЗАВОДИТСЯ ЛЮБЫМ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
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
              "python patch_vahta_zavedi.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nПерезапусти, нажми ВАХТУ и посмотри в чёрное окно:")
    print("там должно быть «заведена» и каким способом.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
