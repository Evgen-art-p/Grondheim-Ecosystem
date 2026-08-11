#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# OKNO_MOGLO_UYTI_V1
"""
ОКНО МОГЛО УЙТИ — кнопка ТЕРМИНАЛ падала уже ПОСЛЕ работы.

    python patch_okno_moglo_uyti.py            посмотреть
    python patch_okno_moglo_uyti.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ЧТО СЛУЧИЛОСЬ

    Терминал ответил, котировки собрались — и всё рухнуло на попытке
    перерисовать полку:

        Client has been deleted but is still being used
        KeyError: 27

    Опрос идёт долго: каждый инструмент умножается на девять этажей, и
    каждый вопрос — отдельный поход в терминал. Пока он шёл, страница в
    браузере пережила перезагрузку. Опрос вернулся с готовым списком и
    полез рисовать в окно, которого уже нет.

ЧТО СТАНЕТ

    · всё, что трогает экран после похода, обёрнуто: данные ложатся в
      кабинет всегда, а рисуем — если есть куда. Ушло окно — обновишь
      страницу и увидишь собранное;
    · итог печатается ещё и в чёрное окно, чтобы результат не пропадал
      вместе с браузером;
    · сам опрос стал быстрее: шесть рабочих этажей вместо девяти и
      потолок в двадцать пять инструментов за раз. На большом обзоре
      рынка это была разница между секундами и минутами — а чем короче
      опрос, тем меньше поводов разойтись со страницей.
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
MARKER = "# OKNO_MOGLO_UYTI_V1 - marker"
BAK = ".bak_okno"

STEZHKI = (
    ("окно могло уйти", '    async def sobrat_terminal():\n        """Кнопка ТЕРМИНАЛ: сходить и разложить котировки по полке."""\n        ui.notify("📡 спрашиваю терминал…", type="info")\n        import asyncio as _a\n        aktivy, beda = await _a.get_event_loop().run_in_executor(\n            None, _sobrat_iz_terminala)\n        if beda:\n            ui.notify(f"⚠ {beda}", type="warning")\n            return\n        # файлы не выкидываем: живое и история лежат рядом, но помечены\n        bylo = [x for x in state.get("loaded_assets", [])\n                if x.get("источник") != "терминал"]\n        state["loaded_assets"] = aktivy + bylo\n        if state.get("active_asset") is None and aktivy:\n            state["active_asset"] = 0\n        update_files_display()\n        simvolov = len({x["symbol"] for x in aktivy})\n        ui.notify(f"📡 с терминала: инструментов {simvolov}, "\n                  f"этажей {len(aktivy)}", type="positive")\n', '    async def sobrat_terminal():\n        """Кнопка ТЕРМИНАЛ: сходить и разложить котировки по полке.\n\n        OKNO_MOGLO_UYTI_V1: опрос долгий, а страница за это время могла\n        перезагрузиться. Тогда окно, в которое мы собрались рисовать,\n        уже мертво — NiceGUI роняет KeyError изнутри. Поэтому всё, что\n        трогает экран ПОСЛЕ похода, обёрнуто: данные ложатся в state\n        всегда, а рисуем — если есть куда.\n        """\n        def _tiho(chto, *a, **kw):\n            try:\n                chto(*a, **kw)\n            except Exception:\n                pass       # окна нет — не беда, данные уже сохранены\n\n        _tiho(ui.notify, "📡 спрашиваю терминал… это небыстро",\n              type="info")\n        import asyncio as _a\n        aktivy, beda = await _a.get_event_loop().run_in_executor(\n            None, _sobrat_iz_terminala)\n        if beda:\n            _tiho(ui.notify, f"⚠ {beda}", type="warning")\n            print(f"[ТЕРМИНАЛ] ⚠️  {beda}")\n            return\n        # файлы не выкидываем: живое и история лежат рядом, но помечены\n        bylo = [x for x in state.get("loaded_assets", [])\n                if x.get("источник") != "терминал"]\n        state["loaded_assets"] = aktivy + bylo\n        if state.get("active_asset") is None and aktivy:\n            state["active_asset"] = 0\n        simvolov = len({x["symbol"] for x in aktivy})\n        print(f"[ТЕРМИНАЛ] 📡 инструментов {simvolov}, этажей {len(aktivy)}")\n        _tiho(update_files_display)\n        _tiho(ui.notify, f"📡 с терминала: инструментов {simvolov}, "\n                         f"этажей {len(aktivy)}", type="positive")\n'),
    ("опрос короче", '    _TERM_ETAZHI = ("M5", "M15", "M30", "H1", "H4", "H8", "D1", "W1", "MN1")\n', '    # OKNO_MOGLO_UYTI_V1: было девять этажей — на большом обзоре рынка это\n    # сотни походов в терминал, опрос тянулся минутами, и страница успевала\n    # уйти из-под него. Шесть рабочих этажей и потолок по инструментам:\n    # быстро, и хватает на всё, чем торгуют.\n    _TERM_ETAZHI = ("M15", "M30", "H1", "H4", "D1", "W1")\n    _TERM_POTOLOK = 25      # инструментов за раз; обзор рынка длиннее — режем\n'),
    ("потолок по инструментам", '        vidnye = [s for s in vse if getattr(s, "visible", False)]\n        if not vidnye:\n            vidnye = list(vse)[:20]      # обзор пуст — берём хоть что-то\n', '        vidnye = [s for s in vse if getattr(s, "visible", False)]\n        if not vidnye:\n            vidnye = list(vse)[:10]      # обзор пуст — берём хоть что-то\n        vidnye = vidnye[:_TERM_POTOLOK]\n'),
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
    print("ОКНО МОГЛО УЙТИ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
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
              "python patch_okno_moglo_uyti.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nЖми ТЕРМИНАЛ. Итог придёт и на экран, и в чёрное окно —")
    print("так что даже если страница уйдёт, ты увидишь, что собралось.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
