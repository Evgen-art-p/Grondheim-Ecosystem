#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VAHTA_GORODSKAYA_V1
"""
ВАХТА ГОРОДСКАЯ — стоит, пока поднят город, а не пока открыто окно.

    python patch_vahta_gorodskaya.py            посмотреть
    python patch_vahta_gorodskaya.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ЧТО БЫЛО НЕ ТАК

    Вахта была комнатная: таймер жил в открытой вкладке кабинета.
    Перешёл на другую страницу — вахта встала. Закрыл браузер — встала.
    И, что хуже, молча: снаружи это выглядело как «стоит».

ЧТО СТАНЕТ

    Вахта живёт при ГОРОДЕ. Заводится один раз, тикает на сервере,
    работает, пока город поднят. Можно уйти на Маяк, открыть Брата,
    закрыть браузер совсем — она стоит на посту.

    Совет она зовёт НАПРЯМУЮ, а не через кнопку кабинета: кнопка рисует
    в окно, а окна может не быть вовсе. Что происходит — пишется в
    чёрное окно города.

    Что сторожим, запоминается в миг нажатия: инструмент и этаж с полки.
    Вахта живёт отдельно от кабинета и полку потом не увидит — поэтому
    сменил инструмент, сними и поставь вахту заново. На кнопке теперь
    написано, что именно она сторожит.

    Кнопка показывает правду из любого окна: зашёл с другой страницы —
    видно, что вахта идёт.

ПРО ДЕНЬГИ, ЕЩЁ РАЗ

    Теперь она не остановится сама, когда ты закроешь браузер. Один
    прогон — это головы, и он платный. На H4 это шесть прогонов в сутки,
    на M15 — почти сотня. Снимается тем же нажатием.
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
MARKER = "# VAHTA_GORODSKAYA_V1 - marker"
BAK = ".bak_vahta_gor"

STEZHKI = (
    ("городская служба вахты", '\n\ndef page_torg(', '\n\n# ══════════════════════════════════════════════════════════════\n# ВАХТА ГОРОДСКАЯ (VAHTA_GORODSKAYA_V1)\n# ══════════════════════════════════════════════════════════════\n# Была вахта комнатная: таймер жил в открытой вкладке. Ушёл на другую\n# страницу — вахта встала, и никто об этом не сказал.\n#\n# Теперь она живёт при ГОРОДЕ, а не при окне: заводится один раз на\n# запуск, тикает на сервере и работает, пока город поднят. Закрыл\n# браузер — она всё равно стоит на посту. Вернулся — кнопка горит.\n_VAHTA = {\n    "идёт": False,      # стоим ли на вахте\n    "инструмент": "",   # что сторожим — запомнили в миг нажатия\n    "этаж": "",\n    "бар": "",          # на какой свече стоим\n    "работает": False,  # прогон уже идёт — второй не начинаем\n    "последнее": "",    # что случилось в прошлый раз (для кнопки)\n}\n_VAHTA_ZAVEDENA = False\n\n\ndef _vahta_posledniy_bar(symbol: str, tf: str) -> str:\n    try:\n        from feed_source import bars as _src_bars\n        _bs, _ = _src_bars(symbol, tf, 3)\n        if _bs:\n            return str(_bs[-1].get("date", ""))\n    except Exception:\n        pass\n    return ""\n\n\nasync def _vahta_sluzhba():\n    """Тик вахты. Живёт на сервере, окна не касается.\n\n    VAHTA_GORODSKAYA_V1: Совет зовём НАПРЯМУЮ, а не через кнопку\n    кабинета — кнопка рисует в окно, а окна может не быть вовсе.\n    """\n    if not _VAHTA["идёт"] or _VAHTA["работает"]:\n        return\n    sym, tf = _VAHTA["инструмент"], _VAHTA["этаж"]\n    if not sym or not tf:\n        return\n    bar = _vahta_posledniy_bar(sym, tf)\n    if not bar:\n        return\n    if not _VAHTA["бар"]:\n        _VAHTA["бар"] = bar          # первый тик — только запомнить\n        return\n    if bar == _VAHTA["бар"]:\n        return\n\n    _VAHTA["бар"] = bar\n    _VAHTA["работает"] = True\n    print(f"[ВАХТА] 🔔 новая свеча {sym} {tf} · {bar[:16]} — зову Совет")\n    try:\n        import asyncio as _a\n        import council\n        await _a.get_event_loop().run_in_executor(\n            None, lambda: council.wake_council(sym, tf))\n        _VAHTA["последнее"] = f"{bar[:16]} · Совет отработал"\n        print(f"[ВАХТА] ✓ {sym} {tf} · {bar[:16]} — Совет отработал")\n    except Exception as e:\n        _VAHTA["последнее"] = f"{bar[:16]} · сбой: {e}"\n        print(f"[ВАХТА] ⚠️  сбой на {sym} {tf}: {e}")\n    finally:\n        _VAHTA["работает"] = False\n\n\ndef _vahta_zavesti():\n    """Один таймер на весь город, не на каждое окно."""\n    global _VAHTA_ZAVEDENA\n    if _VAHTA_ZAVEDENA:\n        return\n    try:\n        from nicegui import app as _app\n        _app.timer(20.0, _vahta_sluzhba)\n        _VAHTA_ZAVEDENA = True\n        print("[ВАХТА] ⏱ городская вахта заведена (тик 20 сек)")\n    except Exception as e:\n        print(f"[ВАХТА] ⚠️  не завелась: {e}")\n\n\ndef page_torg('),
    ("кнопка спрашивает город", '    def _vahta_vid():\n        """Вид кнопки: горит — стоим на вахте."""\n        el = toolbar_refs.get("vahta_btn")\n        ht = toolbar_refs.get("vahta_html")\n        if el is None or ht is None:\n            return\n        if state.get("vahta"):\n            el.style("background:rgba(0,204,255,0.15);color:#00ccff;"\n                     "border:1px solid rgba(0,204,255,0.45);")\n            ht.content = "⏱ ВАХТА ●"\n        else:\n            el.style("background:rgba(255,255,255,0.03);"\n                     "color:rgba(255,255,255,0.45);"\n                     "border:1px solid rgba(255,255,255,0.08);")\n            ht.content = "⏱ ВАХТА"\n\n    def _vahta_pereklyuchit():\n        state["vahta"] = not state.get("vahta")\n        # забываем, где стояли: включаем — начинаем считать заново\n        state["vahta_bar"] = ""\n        _vahta_vid()\n        if state["vahta"]:\n            _s, _t = _aktivnyy_rynok()\n            ui.notify(f"⏱ вахта: жду новую свечу {_s} {_t}", type="info")\n        else:\n            ui.notify("⏱ вахта снята", type="info")\n', '    def _vahta_vid():\n        """Вид кнопки: горит — стоим на вахте.\n\n        VAHTA_GORODSKAYA_V1: спрашиваем ГОРОДСКУЮ вахту, не окно. Зашёл\n        с другой страницы или из другого окна — кнопка всё равно\n        показывает правду.\n        """\n        el = toolbar_refs.get("vahta_btn")\n        ht = toolbar_refs.get("vahta_html")\n        if el is None or ht is None:\n            return\n        if _VAHTA["идёт"]:\n            el.style("background:rgba(0,204,255,0.15);color:#00ccff;"\n                     "border:1px solid rgba(0,204,255,0.45);")\n            ht.content = (f\'⏱ ВАХТА ● {_VAHTA["инструмент"]} \'\n                          f\'{_VAHTA["этаж"]}\')\n        else:\n            el.style("background:rgba(255,255,255,0.03);"\n                     "color:rgba(255,255,255,0.45);"\n                     "border:1px solid rgba(255,255,255,0.08);")\n            ht.content = "⏱ ВАХТА"\n\n    def _vahta_pereklyuchit():\n        if _VAHTA["идёт"]:\n            _VAHTA.update({"идёт": False, "бар": ""})\n            _vahta_vid()\n            ui.notify("⏱ вахта снята", type="info")\n            print("[ВАХТА] ⏹ снята")\n            return\n        if state.get("mode") == "tester":\n            ui.notify("⏱ в тестере вахта не нужна — там время из файла",\n                      type="warning")\n            return\n        _s, _t = _aktivnyy_rynok()\n        # что сторожим — запоминаем СЕЙЧАС: вахта живёт при городе и\n        # полки кабинета потом не увидит.\n        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,\n                       "бар": ""})\n        _vahta_zavesti()\n        _vahta_vid()\n        ui.notify(f"⏱ вахта: сторожу {_s} {_t}. Идёт, пока поднят город "\n                  f"— окно можно закрыть", type="info")\n        print(f"[ВАХТА] ▶ стою на {_s} {_t}")\n'),
    ("комнатный тик убран", '    def _posledniy_bar(symbol: str, tf: str) -> str:\n        """Время последнего бара по тому же крану, что и кадр."""\n        try:\n            from feed_source import bars as _src_bars\n            _bs, _ = _src_bars(symbol, tf, 3)\n            if _bs:\n                return str(_bs[-1].get("date", ""))\n        except Exception:\n            pass\n        return ""\n\n    async def _vahta_tik():\n        """Раз в двадцать секунд: не сменилась ли свеча.\n\n        VAHTA_NOVAYA_SVECHA_V1. Первый тик только запоминает бар —\n        иначе Совет дёргался бы посреди уже начатой свечи. В тестере\n        молчим: там время идёт из файла, а не из жизни.\n        """\n        if not state.get("vahta") or state.get("running"):\n            return\n        if state.get("mode") == "tester":\n            return\n        _s, _t = _aktivnyy_rynok()\n        _bar = _posledniy_bar(_s, _t)\n        if not _bar:\n            return\n        if not state.get("vahta_bar"):\n            state["vahta_bar"] = _bar\n            return\n        if _bar == state["vahta_bar"]:\n            return\n        state["vahta_bar"] = _bar\n        ui.notify(f"🔔 новая свеча {_s} {_t} · {_bar[:16]} — смотрю",\n                  type="positive")\n        await market_dispatch()\n', '    # VAHTA_GORODSKAYA_V1: комнатный тик убран — вахту несёт город\n    # (см. _vahta_sluzhba наверху файла). Здесь осталась только\n    # синхронизация кнопки при заходе на страницу.\n'),
    ("таймер только для вида", '                        ui.timer(20.0, _vahta_tik)   # async-колбэк NiceGUI ждёт сам\n', '                        # VAHTA_GORODSKAYA_V1: таймер вахты живёт при\n                        # городе. Здесь только подтягиваем вид кнопки —\n                        # чтобы, зайдя из другого окна, видеть правду.\n                        ui.timer(3.0, _vahta_vid)\n'),
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

    print("=" * 62)
    print("ВАХТА ГОРОДСКАЯ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    if not UI.exists():
        print("x не вижу Биржа/ui_torg.py — запускай из КОРНЯ")
        return 1
    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0
    if "_vahta_pereklyuchit" not in tekst:
        print("x кнопки ВАХТА ещё нет — сперва patch_vahta.py")
        return 1

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
              "python patch_vahta_gorodskaya.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nВыбери инструмент, жми ВАХТА — на кнопке напишется, что она")
    print("сторожит. Дальше уходи куда хочешь, хоть закрывай браузер:")
    print("что происходит, видно в чёрном окне города.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
