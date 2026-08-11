#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# POLKA_IZ_TERMINALA_V1
"""
ПОЛКА ИЗ ТЕРМИНАЛА — котировки сами приходят на левую колонку.

    python patch_polka_iz_terminala.py            посмотреть
    python patch_polka_iz_terminala.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ЧТО БЫЛО

    Левая колонка — загрузчик файлов. Что положил CSV-кой, то и на
    полке. Живого рынка она не знает вовсе: имя брали из имени файла,
    и я сам говорил, что это ступенька, а не финал.

ЧТО СТАНЕТ

    Рядом с CLEAR встаёт кнопка ТЕРМИНАЛ. Жмёшь — кабинет спрашивает
    у самого терминала: какие инструменты открыты в обзоре рынка и
    какие этажи по ним реально отдаются. Что нашлось, то и ложится на
    ту же полку, рядом с файлами.

    Дальше всё как было: кликнул этаж — он и есть рабочий. «Взгляд»,
    РЫНОК и ВАХТА берут его оттуда же, править их не пришлось.

    У каждой строки видно, откуда она: `терминал` или `файл`. Спутать
    живое с историей больше нельзя.

ЧЕСТНО ПРО ДВЕ ВЕЩИ

    Опрос идёт по инструментам ИЗ ОБЗОРА РЫНКА — тем, что у тебя
    открыты в терминале. Нужен другой инструмент — добавь его в обзор,
    и он появится. Так честнее, чем тащить все шесть тысяч символов
    брокера.

    Проверяются девять этажей — от пятиминутки до месяца. Пустые не
    показываются: в субботу дневки и восьмичасовки часто молчат, и
    полка тогда честно короче.
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
MARKER = "# POLKA_IZ_TERMINALA_V1 - marker"
BAK = ".bak_polka"

# ── 1. сбор с терминала ───────────────────────────────────────
STAROE_SBOR = '''    def _scan_test_data():
'''
NOVOE_SBOR = '''    # POLKA_IZ_TERMINALA_V1 — какие этажи спрашиваем у терминала.
    # Не все подряд: минутка и двухчасовка редко нужны, а опрос платный
    # временем. Пустые этажи на полку не кладём.
    _TERM_ETAZHI = ("M5", "M15", "M30", "H1", "H4", "H8", "D1", "W1", "MN1")

    def _sobrat_iz_terminala() -> tuple:
        """Спросить сам терминал: что открыто в обзоре рынка и что живо.

        Возвращает (активы, беда). Беда — текстом, чтобы кабинет мог
        сказать её вслух, а не молчать.
        """
        try:
            import sys as _s
            _b = str(_HERE)
            if _b not in _s.path:
                _s.path.insert(0, _b)
            import mt5_feed as _mf
        except Exception as e:
            return [], f"насос не поднялся: {e}"

        mt5 = _mf._terminal()
        if mt5 is None:
            return [], ("терминал молчит: не установлен MetaTrader5 для "
                        "питона или сам терминал не запущен")

        try:
            vse = mt5.symbols_get() or []
        except Exception as e:
            return [], f"терминал не отдал список инструментов: {e}"

        vidnye = [s for s in vse if getattr(s, "visible", False)]
        if not vidnye:
            vidnye = list(vse)[:20]      # обзор пуст — берём хоть что-то

        aktivy = []
        for s in vidnye:
            imya = getattr(s, "name", "")
            if not imya:
                continue
            for tf in _TERM_ETAZHI:
                kod = _mf._TF_MAP.get(tf)
                if kod is None:
                    continue
                try:
                    bary = mt5.copy_rates_from_pos(imya, kod, 0, 2)
                except Exception:
                    bary = None
                if bary is None or len(bary) == 0:
                    continue          # этаж молчит — на полку не кладём
                try:
                    from datetime import datetime as _dt
                    posledniy = _dt.fromtimestamp(
                        int(bary[-1]["time"])).strftime("%Y.%m.%d %H:%M")
                except Exception:
                    posledniy = "?"
                aktivy.append({
                    "name": f"{imya} {tf}", "path": "", "symbol": imya,
                    "timeframe": tf, "bars": 0,
                    "date_from": "терминал", "date_to": posledniy,
                    "источник": "терминал",
                })
        try:
            mt5.shutdown()
        except Exception:
            pass
        if not aktivy:
            return [], ("терминал на связи, но ни один этаж не отдал баров "
                        "— выходной или инструменты не открыты в обзоре")
        return aktivy, ""

    async def sobrat_terminal():
        """Кнопка ТЕРМИНАЛ: сходить и разложить котировки по полке."""
        ui.notify("📡 спрашиваю терминал…", type="info")
        import asyncio as _a
        aktivy, beda = await _a.get_event_loop().run_in_executor(
            None, _sobrat_iz_terminala)
        if beda:
            ui.notify(f"⚠ {beda}", type="warning")
            return
        # файлы не выкидываем: живое и история лежат рядом, но помечены
        bylo = [x for x in state.get("loaded_assets", [])
                if x.get("источник") != "терминал"]
        state["loaded_assets"] = aktivy + bylo
        if state.get("active_asset") is None and aktivy:
            state["active_asset"] = 0
        update_files_display()
        simvolov = len({x["symbol"] for x in aktivy})
        ui.notify(f"📡 с терминала: инструментов {simvolov}, "
                  f"этажей {len(aktivy)}", type="positive")

    def _scan_test_data():
'''

# ── 2. кнопка в шапке загрузчика ──────────────────────────────
STAROE_KNOPKA = '''                        ui.button("CLEAR", on_click=clear_files).props("flat dense size=xs").style(
                            "color:rgba(255,80,80,0.5); font-size:9px;")
'''
NOVOE_KNOPKA = '''                        # POLKA_IZ_TERMINALA_V1: живые котировки на полку
                        ui.button("ТЕРМИНАЛ", on_click=sobrat_terminal).props(
                            "flat dense size=xs").style(
                            "color:rgba(0,255,136,0.75); font-size:9px;")
                        ui.button("CLEAR", on_click=clear_files).props("flat dense size=xs").style(
                            "color:rgba(255,80,80,0.5); font-size:9px;")
'''

# ── 3. на полке видно, откуда строка ──────────────────────────
STAROE_VID = '''            active = state.get("active_asset")
'''
NOVOE_VID = '''            active = state.get("active_asset")
            # POLKA_IZ_TERMINALA_V1: живое и история лежат рядом — пусть
            # будет видно, что есть что. Спутать их дороже всего.
            _zhivyh = sum(1 for _a in assets
                          if _a.get("источник") == "терминал")
            if _zhivyh:
                ui.label(f"из терминала: {_zhivyh}").style(
                    "color:rgba(0,255,136,0.55); font-size:9px; "
                    "letter-spacing:.08em; padding:0 4px 4px;")
'''

STEZHKI = (
    ("сбор с терминала", STAROE_SBOR, NOVOE_SBOR),
    ("кнопка ТЕРМИНАЛ", STAROE_KNOPKA, NOVOE_KNOPKA),
    ("пометка на полке", STAROE_VID, NOVOE_VID),
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
    print("ПОЛКА ИЗ ТЕРМИНАЛА" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
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
              "python patch_polka_iz_terminala.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nОткрой кабинет, слева вверху жми ТЕРМИНАЛ.")
    print("Что терминал отдаёт — ляжет на полку с пометкой «терминал».")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
