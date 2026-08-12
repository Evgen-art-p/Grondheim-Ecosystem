#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PROSTO_I_ROVNO_V1
"""
ПРОСТО И РОВНО — ряд кнопок на место, состав на виду.

    python patch_prosto_i_rovno.py            посмотреть
    python patch_prosto_i_rovno.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ЧТО БЫЛО НЕ ТАК

    1. РЯД КНОПОК РАЗЪЕХАЛСЯ.
       Я сделал подпись у ВАХТЫ длинной — она стала показывать, что
       сторожит. На узком ряду это свернулось в две строки, кнопка
       выросла и подняла соседей. РЫНОК уехал вверх, РЕАЛ и ОЧИСТИТЬ
       вниз, половину стало не нажать.

    2. НИКТО НИЧЕГО НЕ ПИШЕТ.
       Кто чем работает, было видно только по мелькающим уведомлениям.
       Мелькнуло и пропало — а на экране всё то же самое. Оттого и
       «говорят одно, написано другое».

ЧТО СТАНЕТ

    · ВАХТА снова в одну строку и той же высоты, что соседи. Что она
      сторожит — в подсказке, если навести;

    · под пузырьками появляется СТРОКА СОСТАВА, всегда на виду:

          EURUSD H4  ·  Нина  ·  Синди  ·  A08 свободно  ·  вахта: EURUSD H4

      Слева зелёным — чем работаем сейчас. Дальше кто на местах, и
      пустые честно помечены. Стоит вахта — видно и её.

    Строка обновляется сама: сменил актив, переключил трейдера, снял
    вахту — она сразу другая. Гадать и кликать не надо.
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
MARKER = "# PROSTO_I_ROVNO_V1 - marker"
BAK = ".bak_prosto"

STEZHKI = (
    ("место под строку состава", '    def _vahta_vid():\n', '    sostav_ref: dict = {"element": None}\n\n    def _vahta_vid():\n'),
    ("кнопка ВАХТА в одну строку", '                        toolbar_refs["vahta_btn"] = ui.element("div").style(\n                            "padding:6px 14px;border-radius:7px;font-size:12px;"\n                            "font-weight:700;cursor:pointer;"\n                            "background:rgba(255,255,255,0.03);"\n                            "color:rgba(255,255,255,0.45);"\n                            "border:1px solid rgba(255,255,255,0.08);")\n', '                        # PROSTO_I_ROVNO_V1: кнопка сворачивалась в две\n                        # строки и поднимала соседей — ряд разъезжался.\n                        # Теперь одна строка и та же высота, что у прочих.\n                        toolbar_refs["vahta_btn"] = ui.element("div").style(\n                            "padding:8px 16px;border-radius:8px;font-size:12px;"\n                            "font-weight:700;cursor:pointer;white-space:nowrap;"\n                            "display:flex;align-items:center;flex-shrink:0;"\n                            "background:rgba(255,255,255,0.03);"\n                            "color:rgba(255,255,255,0.45);"\n                            "border:1px solid rgba(255,255,255,0.08);")\n'),
    ("подпись короткая, подсказка длинная", '        if _VAHTA["идёт"]:\n            el.style("background:rgba(0,204,255,0.15);color:#00ccff;"\n                     "border:1px solid rgba(0,204,255,0.45);")\n            ht.content = (f\'⏱ ВАХТА ● {_VAHTA["инструмент"]} \'\n                          f\'{_VAHTA["этаж"]}\')\n', '        if _VAHTA["идёт"]:\n            el.style("background:rgba(0,204,255,0.15);color:#00ccff;"\n                     "border:1px solid rgba(0,204,255,0.45);"\n                     "white-space:nowrap;")\n            # PROSTO_I_ROVNO_V1: в подписи коротко, что сторожит — в\n            # подсказке и в строке состава под пузырьками.\n            ht.content = "⏱ ВАХТА ●"\n            try:\n                el.tooltip(f\'сторожу {_VAHTA["инструмент"]} \'\n                           f\'{_VAHTA["этаж"]}\')\n            except Exception:\n                pass\n'),
    ("строка состава под пузырьками", '                with ui.element("div").style(\n                    "margin-right:10px; background:rgba(255,255,255,0.06); "\n                    "border:1px solid rgba(255,255,255,0.12); border-radius:10px;"\n                ):\n', '                # PROSTO_I_ROVNO_V1: строка состава. Всегда на виду, кто\n                # на местах и чем работаем — чтобы не гадать по кликам и\n                # не ловить пропадающие уведомления.\n                sostav_ref["element"] = ui.html("").style(\n                    "color:rgba(255,255,255,0.55); font-size:11px; "\n                    "letter-spacing:0.04em; margin-right:14px; "\n                    "white-space:nowrap; overflow:hidden; "\n                    "text-overflow:ellipsis; max-width:46vw;")\n                with ui.element("div").style(\n                    "margin-right:10px; background:rgba(255,255,255,0.06); "\n                    "border:1px solid rgba(255,255,255,0.12); border-radius:10px;"\n                ):\n'),
    ("как её рисовать", '    def update_avatar_states():\n', '    def update_sostav():\n        """PROSTO_I_ROVNO_V1: кто на местах и чем работаем — одной строкой.\n\n        Раньше это было видно только по мелькающим уведомлениям, и\n        выходило «говорят одно, написано другое». Теперь висит на месте.\n        """\n        el = sostav_ref.get("element")\n        if el is None:\n            return\n        try:\n            _s, _t = _aktivnyy_rynok()\n            kuski = [f\'<b style="color:rgba(0,255,136,0.85)">{_s} {_t}</b>\']\n            for _sl in ("A06", "A07", "A08"):\n                _row = _agent_row(roster, _sl)\n                if _row and _row.get("resident"):\n                    kuski.append(_row["resident"].get("имя", _sl))\n                else:\n                    kuski.append(f\'<span style="opacity:.4">{_sl} свободно\'\n                                 f\'</span>\')\n            if _VAHTA["идёт"]:\n                kuski.append(f\'<span style="color:#00ccff">вахта: \'\n                             f\'{_VAHTA["инструмент"]} {_VAHTA["этаж"]}</span>\')\n            el.content = "  ·  ".join(kuski)\n        except Exception:\n            pass\n\n    def update_avatar_states():\n'),
    ("держим свежей", '    def update_files_display():\n', '    def update_files_display():\n        update_sostav()          # PROSTO_I_ROVNO_V1: состав всегда свеж\n'),
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
    print("ПРОСТО И РОВНО" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
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
              "python patch_prosto_i_rovno.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nПерезапусти город. Ряд кнопок должен встать ровно, а под")
    print("пузырьками появиться строка: чем работаем и кто на местах.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
