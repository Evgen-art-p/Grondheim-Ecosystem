#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PODPISI_POD_PUZYRKAMI_V1
"""
КТО ЧЕМ ЗАНЯТ — написано именами, и назначается кликом.

    python patch_podpisi.py            посмотреть
    python patch_podpisi.py --sdelat   накатить

Запускать из КОРНЯ. Ставится последним, после всех сегодняшних.

ЧТО ПОЯВЛЯЕТСЯ

    Строка под пузырьками перестаёт быть общей кашей и пишется по
    людям:

        Нина — GBPUSD H4  ·  Синди — EURUSD H4  ·  вахта идёт

    Зелёным — у кого СВОЁ (ты назначил или он взял сам). Серым — кто
    работает по общему, с полки. Видно сразу, без кликов и без
    пропадающих уведомлений.

    Назначается так, как ты и просил: кликнул человека наверху,
    кликнул инструмент слева — он взял его в работу, и подпись тут же
    поменялась. Никого не выбрал — меняешь общий, как раньше.

ПОЧЕМУ СТРОКОЙ, А НЕ ПОДПИСЬЮ ПОД САМИМ ПУЗЫРЬКОМ

    Честно: подпись прямо под кружком ломает ряд — он уже разъезжался
    сегодня из-за кнопки ВАХТА, и второй раз я туда не полезу без
    нужды. Строка стоит там же, вплотную под пузырьками, и говорит то
    же самое, а верстку не трогает. Захочешь именно под кружком —
    сделаю отдельно и покажу до наката.

ПРО ВАХТУ

    Вахта одна на город: она жмёт РЫНОК, а РЫНОК собирает всех разом.
    Но каждый трейдер в работе смотрит СВОЙ инструмент, если он у него
    есть. То есть свеча приходит по общему, а работают все по своему —
    и по-настоящему разное.
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
MARKER = "# PODPISI_POD_PUZYRKAMI_V1 - marker"
BAK = ".bak_podpisi"

STEZHKI = (
    ("назначение кликом", '    def set_active(i):\n        """Клик по полке: выбрать, чем работаем. И только.\n\n        NAZNACHENIYA_PROCH_V1: тут стояло назначение инструмента\n        активному трейдеру. Шеф сказал прямо: непонятно, никто нигде\n        ничего не пишет, говорят одно — написано другое. Убрано.\n\n        Все смотрят на то, что выбрано на полке. Кто чем работает —\n        видно строкой состава под пузырьками, а не по кликам.\n        """\n        assets = state.get("loaded_assets", [])\n        if not (0 <= i < len(assets)):\n            return\n        state["active_asset"] = i\n        a = assets[i]\n        # VAHTA_ZA_POLKOY_V1: вахта идёт ЗА ПОЛКОЙ, а не помнит, что было\n        # при нажатии. Раньше выходило так: работаем EURUSD, а вахта\n        # сторожит GBPUSD, потому что её включали на нём.\n        if _VAHTA["идёт"]:\n            _VAHTA.update({"инструмент": a["symbol"],\n                           "этаж": a["timeframe"], "бар": ""})\n            print(f"[ВАХТА] ↪ теперь сторожу {a[\'symbol\']} {a[\'timeframe\']}")\n        ui.notify(f"Работаем: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n        update_files_display()\n', '    def set_active(i):\n        """Клик по полке: чем работает ВЫБРАННЫЙ сейчас трейдер.\n\n        PODPISI_POD_PUZYRKAMI_V1: кликнул человека наверху, кликнул\n        инструмент слева — он взял его. Кто чем занят, тут же написано\n        строкой ниже, по именам. Никого не выбрал — меняем общий.\n        """\n        assets = state.get("loaded_assets", [])\n        if not (0 <= i < len(assets)):\n            return\n        state["active_asset"] = i\n        a = assets[i]\n        slot = _slot_agenta(state.get("active_agent", ""))\n        if slot:\n            try:\n                from vybor import naznachit as _nazn\n                _nazn(tseh_id, slot, a["symbol"])\n                imya = _agent_label(roster, state["active_agent"])\n                ui.notify(f"{imya} → {a[\'symbol\']} {a[\'timeframe\']}",\n                          type="positive")\n                print(f"[РАБОТА] {imya} ({slot}) → {a[\'symbol\']}")\n            except Exception as e:\n                ui.notify(f"⚠ не записалось: {e}", type="negative")\n        else:\n            ui.notify(f"Работаем: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n        if _VAHTA["идёт"]:\n            _VAHTA.update({"инструмент": a["symbol"],\n                           "этаж": a["timeframe"], "бар": ""})\n        update_files_display()\n'),
    ("строка по людям", '        try:\n            _s, _t = _aktivnyy_rynok()\n            # VAHTA_ZA_POLKOY_V1: по-человечески. Было «EURUSD H4 · Нина ·\n            # Синди · A08 свободно · вахта: GBPUSD H4» — набор слов, из\n            # которого не понять, кто чем занят и почему разное.\n            _kto = [_row["resident"].get("имя", _sl)\n                    for _sl in ("A06", "A07", "A08")\n                    for _row in [_agent_row(roster, _sl)]\n                    if _row and _row.get("resident")]\n            _text = (f\'работаем: <b style="color:rgba(0,255,136,0.9)">\'\n                     f\'{_s} {_t}</b>\')\n            if _kto:\n                _text += (f\'&nbsp;&nbsp;·&nbsp;&nbsp;за столом: \'\n                          f\'{", ".join(_kto)}\')\n            else:\n                _text += (\'&nbsp;&nbsp;·&nbsp;&nbsp;<span style="opacity:.5">\'\n                          \'за столом никого</span>\')\n            if _VAHTA["идёт"]:\n                _text += (\'&nbsp;&nbsp;·&nbsp;&nbsp;\'\n                          \'<span style="color:#00ccff">вахта идёт</span>\')\n            el.content = _text\n        except Exception:\n            pass\n', '        try:\n            _s, _t = _aktivnyy_rynok()\n            # PODPISI_POD_PUZYRKAMI_V1: по людям, а не общей кашей.\n            # Видно сразу, кто чем занят и у кого своё.\n            from vybor import instrument_dlya as _idl\n            kuski = []\n            for _sl in ("A06", "A07", "A08"):\n                _row = _agent_row(roster, _sl)\n                if not (_row and _row.get("resident")):\n                    continue\n                _imya = _row["resident"].get("имя", _sl)\n                try:\n                    _ins, _otk = _idl(tseh_id, _sl, _s)\n                except Exception:\n                    _ins, _otk = _s, ""\n                _svoy = _otk in ("назначен", "выбрал сам")\n                _cvet = "rgba(0,255,136,0.9)" if _svoy else \\\n                        "rgba(255,255,255,0.6)"\n                kuski.append(f\'{_imya} — <b style="color:{_cvet}">\'\n                             f\'{_ins or _s} {_t}</b>\')\n            if not kuski:\n                kuski = [\'<span style="opacity:.5">за столом никого</span>\']\n            _text = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(kuski)\n            if _VAHTA["идёт"]:\n                _text += (\'&nbsp;&nbsp;·&nbsp;&nbsp;\'\n                          \'<span style="color:#00ccff">вахта идёт</span>\')\n            el.content = _text\n        except Exception:\n            pass\n'),
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
    print("КТО ЧЕМ ЗАНЯТ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
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
            print("    (нужны все сегодняшние патчи по порядку)")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_torg.py"):
        return 1
    if suho:
        print("\nЭто был показ. Накатывать: python patch_podpisi.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nПерезапусти. Кликни Нину, потом инструмент слева — строка")
    print("под пузырьками сразу покажет, что у неё своё.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
