#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# NAZNACHENIYA_PROCH_V1
"""
НАЗНАЧЕНИЯ ПРОЧЬ — клик по полке снова значит одно.

    python patch_naznacheniya_proch.py            посмотреть
    python patch_naznacheniya_proch.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ЗАЧЕМ ИМЕННО ТАК, А НЕ ОТКАТОМ

    Откатить «панель» и «инструмент» по их копиям нельзя без потерь:
    после них те же самые файлы правили «движок не решает» и «выбор
    свой, не книжный». Копия четырнадцати часов вернула бы файл в
    состояние ДО обеих починок и стёрла их заодно.

    Поэтому убираю руками ровно то, что мешает, — и ничего больше.

ЧТО УБИРАЕТСЯ

    · клик по полке больше не назначает инструмент активному трейдеру.
      Он снова значит одно: чем мы работаем. Все смотрят на выбранное;
    · пропадающие уведомления «Нина: задание такое-то» — вместо них
      строка состава под пузырьками, которая никуда не девается.

ЧТО ОСТАЁТСЯ ЛЕЖАТЬ БЕЗ ДЕЛА

    Сам механизм заданий (`Биржа/vybor.py`) остаётся в городе, но его
    никто не зовёт: заданий нет — трейдеры берут инструмент с полки,
    как и раньше. Понадобится — вернём, уже от простого: сперва чтобы
    было видно, потом чтобы было чем управлять.
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
MARKER = "# NAZNACHENIYA_PROCH_V1 - marker"
BAK = ".bak_bez_naznacheniy"

STEZHKI = (
    ('клик по полке — только выбор', '    def set_active(i):\n        """PANEL_TREYDERA_V1: полка принадлежит АКТИВНОМУ трейдеру.\n\n        Кликнул человека наверху — панель стала его. Кликнул инструмент\n        — он взял его в работу. Переключился на другого — у того свой.\n        """\n        assets = state.get("loaded_assets", [])\n        if not (0 <= i < len(assets)):\n            return\n        state["active_asset"] = i\n        a = assets[i]\n        slot = _slot_agenta(state.get("active_agent", ""))\n        if slot:\n            try:\n                from vybor import naznachit as _nazn\n                ok, msg = _nazn(tseh_id, slot, a["symbol"])\n                imya = _agent_label(roster, state["active_agent"])\n                ui.notify(f"🎯 {imya}: {msg}" if ok else f"⚠ {msg}",\n                          type="positive" if ok else "negative")\n                print(f"[ПАНЕЛЬ] 🎯 {imya} ({slot}) ← {a[\'symbol\']}")\n            except Exception as e:\n                ui.notify(f"⚠ задание не записалось: {e}", type="negative")\n        else:\n            ui.notify(f"Активен: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n        update_files_display()\n', '    def set_active(i):\n        """Клик по полке: выбрать, чем работаем. И только.\n\n        NAZNACHENIYA_PROCH_V1: тут стояло назначение инструмента\n        активному трейдеру. Шеф сказал прямо: непонятно, никто нигде\n        ничего не пишет, говорят одно — написано другое. Убрано.\n\n        Все смотрят на то, что выбрано на полке. Кто чем работает —\n        видно строкой состава под пузырьками, а не по кликам.\n        """\n        assets = state.get("loaded_assets", [])\n        if not (0 <= i < len(assets)):\n            return\n        state["active_asset"] = i\n        a = assets[i]\n        ui.notify(f"Работаем: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n        update_files_display()\n'),
    ('без мелькающих уведомлений', '        # PANEL_TREYDERA_V1: панель котировок теперь его — перерисуем,\n        # чтобы было видно, чем он работает.\n        try:\n            update_files_display()\n            _slot = _slot_agenta(agent_id)\n            if _slot:\n                from vybor import instrument_dlya as _idl\n                _ins, _otk = _idl(tseh_id, _slot, "")\n                if _ins:\n                    ui.notify(f"🎯 {_agent_label(roster, agent_id)}: "\n                              f"{_ins} ({_otk})", type="info")\n        except Exception:\n            pass\n', '        # NAZNACHENIYA_PROCH_V1: было уведомление про инструмент —\n        # мелькало и пропадало. Теперь всё в строке состава.\n        try:\n            update_files_display()\n            update_sostav()\n        except Exception:\n            pass\n'),
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
    print("НАЗНАЧЕНИЯ ПРОЧЬ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 60)

    if not UI.exists():
        print("x не вижу Биржа/ui_torg.py — запускай из КОРНЯ")
        return 1
    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0
    if "PANEL_TREYDERA_V1" not in tekst:
        print("  панели с назначением и нет — убирать нечего")
        return 0

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x якорь «{nazv}» найден {n} раз — файл не трогаю")
            if n == 0:
                print("    (может, строка состава ещё не накатана —")
                print("     поставь сперва patch_prosto_i_rovno.py)")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_torg.py"):
        return 1

    if suho:
        print("\nЭто был показ. Накатывать: "
              "python patch_naznacheniya_proch.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nПерезапусти город. Клик по полке снова значит одно:")
    print("чем работаем. Кто на местах — в строке под пузырьками.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
