# -*- coding: utf-8 -*-
# VAHTA_NOVAYA_SVECHA_V1
"""
ВАХТА — трейдер смотрит КАЖДУЮ новую свечу рабочего этажа.

    python patch_vahta.py --suho    посмотреть
    python patch_vahta.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_vahta.

ЧТО ПОЯВЛЯЕТСЯ

    Кнопка ВАХТА рядом с РЫНКОМ. Включил — кабинет каждые двадцать
    секунд тихо спрашивает у крана время последнего бара выбранного
    инструмента и этажа. Время сменилось — значит свеча закрылась и
    открылась новая: Совет собирается сам, без твоей руки. Ровно то же
    самое, что нажать РЫНОК, только вовремя.

    Выключил — всё как было, руками.

КАК ЭТО СЕБЯ ВЕДЁТ

    · Первый тик после включения ничего не запускает — только
      запоминает, на какой свече мы стоим. Иначе Вахта дёргала бы
      Совет сразу, посреди уже начатой свечи.
    · Пока прогон идёт, следующий не начнётся: сверяемся с тем же
      флажком, что и кнопка.
    · Инструмент и этаж берутся оттуда же, откуда кадр, — с полки.
      Переключил актив на полке — Вахта пошла за ним.
    · В ТЕСТЕРЕ вахта молчит: там время бежит из файла, а не из жизни.
    · Каждую новую свечу сверху мелькает, какая именно пришла.

ЧЕСТНО ПРО ДЕНЬГИ

    Один прогон — это пять голов, и он платный. Считай сам:
      H4  — шесть прогонов в сутки, дёшево;
      H1  — двадцать четыре;
      M15 — почти сотня;
      M5  — под три сотни в сутки.
    На младших этажах Вахту лучше не оставлять на ночь. Поэтому она и
    выключена по умолчанию: включаешь осознанно.

    И ещё: пока за столом сидит один человек из трёх, двое молчат
    вакансией, но их мозги всё равно не зовутся — платить будешь за
    тех, кто говорит.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
UI = KOREN / "Биржа" / "ui_torg.py"
MARKER = "# VAHTA_NOVAYA_SVECHA_V1 - marker"
BAK = ".bak_vahta"

# ── 1. память вахты в состоянии кабинета ──────────────────────
STAROE_STATE = '''        "model": DEFAULT_MODEL,   # BIRZHA_MODEL_SEL_V1
'''
NOVOE_STATE = '''        "model": DEFAULT_MODEL,   # BIRZHA_MODEL_SEL_V1
        # VAHTA_NOVAYA_SVECHA_V1: смотрим каждую новую свечу рабочего
        # этажа. Выключена по умолчанию — прогон платный, включать надо
        # осознанно.
        "vahta": False,
        "vahta_bar": "",
'''

# ── 2. сама вахта: тик и кнопка ───────────────────────────────
STAROE_KNOPKA = '''                        ui.button("📡 РЫНОК", on_click=market_dispatch).props("flat").style(\'\'\'
                            padding: 8px 18px; border-radius: 8px;
                            background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10)) !important;
                            border: 1px solid rgba(0,255,136,0.35);
                            color: rgba(255,255,255,0.9); font-weight: 700;
                        \'\'\')
'''
NOVOE_KNOPKA = '''                        ui.button("📡 РЫНОК", on_click=market_dispatch).props("flat").style(\'\'\'
                            padding: 8px 18px; border-radius: 8px;
                            background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10)) !important;
                            border: 1px solid rgba(0,255,136,0.35);
                            color: rgba(255,255,255,0.9); font-weight: 700;
                        \'\'\')

                        # VAHTA_NOVAYA_SVECHA_V1 — стоять на вахте и
                        # смотреть каждую новую свечу рабочего этажа.
                        toolbar_refs["vahta_btn"] = ui.element("div").style(
                            "padding:6px 14px;border-radius:7px;font-size:12px;"
                            "font-weight:700;cursor:pointer;"
                            "background:rgba(255,255,255,0.03);"
                            "color:rgba(255,255,255,0.45);"
                            "border:1px solid rgba(255,255,255,0.08);")
                        with toolbar_refs["vahta_btn"]:
                            toolbar_refs["vahta_html"] = ui.html("⏱ ВАХТА")
                        toolbar_refs["vahta_btn"].on(
                            "click", lambda: _vahta_pereklyuchit())
                        ui.timer(20.0, _vahta_tik)   # async-колбэк NiceGUI ждёт сам
'''

# ── 3. руки вахты ─────────────────────────────────────────────
STAROE_DISPATCH = '''    async def market_dispatch():
'''
NOVOE_DISPATCH = '''    def _vahta_vid():
        """Вид кнопки: горит — стоим на вахте."""
        el = toolbar_refs.get("vahta_btn")
        ht = toolbar_refs.get("vahta_html")
        if el is None or ht is None:
            return
        if state.get("vahta"):
            el.style("background:rgba(0,204,255,0.15);color:#00ccff;"
                     "border:1px solid rgba(0,204,255,0.45);")
            ht.content = "⏱ ВАХТА ●"
        else:
            el.style("background:rgba(255,255,255,0.03);"
                     "color:rgba(255,255,255,0.45);"
                     "border:1px solid rgba(255,255,255,0.08);")
            ht.content = "⏱ ВАХТА"

    def _vahta_pereklyuchit():
        state["vahta"] = not state.get("vahta")
        # забываем, где стояли: включаем — начинаем считать заново
        state["vahta_bar"] = ""
        _vahta_vid()
        if state["vahta"]:
            _s, _t = _aktivnyy_rynok()
            ui.notify(f"⏱ вахта: жду новую свечу {_s} {_t}", type="info")
        else:
            ui.notify("⏱ вахта снята", type="info")

    def _posledniy_bar(symbol: str, tf: str) -> str:
        """Время последнего бара по тому же крану, что и кадр."""
        try:
            from feed_source import bars as _src_bars
            _bs, _ = _src_bars(symbol, tf, 3)
            if _bs:
                return str(_bs[-1].get("date", ""))
        except Exception:
            pass
        return ""

    async def _vahta_tik():
        """Раз в двадцать секунд: не сменилась ли свеча.

        VAHTA_NOVAYA_SVECHA_V1. Первый тик только запоминает бар —
        иначе Совет дёргался бы посреди уже начатой свечи. В тестере
        молчим: там время идёт из файла, а не из жизни.
        """
        if not state.get("vahta") or state.get("running"):
            return
        if state.get("mode") == "tester":
            return
        _s, _t = _aktivnyy_rynok()
        _bar = _posledniy_bar(_s, _t)
        if not _bar:
            return
        if not state.get("vahta_bar"):
            state["vahta_bar"] = _bar
            return
        if _bar == state["vahta_bar"]:
            return
        state["vahta_bar"] = _bar
        ui.notify(f"🔔 новая свеча {_s} {_t} · {_bar[:16]} — смотрю",
                  type="positive")
        await market_dispatch()

    async def market_dispatch():
'''

STEZHKI = (
    ("память вахты", STAROE_STATE, NOVOE_STATE),
    ("руки вахты", STAROE_DISPATCH, NOVOE_DISPATCH),
    ("кнопка вахты", STAROE_KNOPKA, NOVOE_KNOPKA),
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
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("=" * 58)
    print("ВАХТА · новая свеча" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("=" * 58)

    if not UI.exists():
        print("x не вижу Биржа/ui_torg.py — запускай из КОРНЯ репо")
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

    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: python patch_vahta.py")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nВыбери актив и этаж на полке, жми ВАХТА — кнопка загорится.")
    print("Дальше он смотрит сам, на каждой новой свече.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
