# -*- coding: utf-8 -*-
# KADR_NA_VES_KVADRAT_V1
"""
КАДР НА ВСЮ КЛЕТКУ · И ДАТА ПОСЛЕДНЕГО БАРА В ПОДПИСИ

    python patch_kadr_na_ves_kvadrat.py --suho    посмотреть
    python patch_kadr_na_ves_kvadrat.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_kvadrat.
Ложится поверх patch_kabinet_vzglyad.py — без него якорей не найдёт.

── 1. КАРТИНКА НЕ НА ВСЮ КЛЕТКУ (мой недосмотр) ────────────────

    Клетка кадра — флекс, разложенный В СТРОКУ. Пока в ней лежала
    одна картинка, это было незаметно. Я добавил подпись — и она
    встала не под картинкой, а СПРАВА от неё, отжав картинку влево
    и не дав ей растянуться. Ровно это видно на снимке кабинета.

    Стало: клетка разложена в колонку. Картинка занимает всё место,
    какое есть, и тянется до краёв, сохраняя пропорции — не плющится.
    Подпись садится под ней, как ей и положено.

── 2. ДАТА ПОСЛЕДНЕГО БАРА ─────────────────────────────────────

    Мы говорили: с полки берётся только ИМЯ, а данные приносит кран.
    Но глазом реал от истории не отличить — обе картинки выглядят
    одинаково честно.

    Теперь в подписи стоит дата последнего бара. Живой рынок — там
    сегодняшнее число. Тестер — прошлогоднее. Спорить больше не о чем:
    видно сразу, чем сейчас кормят и тебя, и трейдера.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
    Не трогает мозги, стол и найм. Только клетка кадра в кабинете.
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
MARKER = "# KADR_NA_VES_KVADRAT_V1 - marker"
BAK = ".bak_kvadrat"

# ── клетка кадра: колонка, а не строка ────────────────────────
STAROE_KLETKA = '''                            kadr_ref["element"] = ui.element("div").classes("viewer").style(
                                "flex:1; min-height:0; overflow:auto; "
                                "display:flex; align-items:center; "
                                "justify-content:center;")
'''
NOVOE_KLETKA = '''                            # KADR_NA_VES_KVADRAT_V1: колонка, не строка.
                            # В строке подпись вставала СПРАВА от кадра и
                            # отжимала его — картинка не тянулась на клетку.
                            kadr_ref["element"] = ui.element("div").classes("viewer").style(
                                "flex:1; min-height:0; overflow:hidden; "
                                "display:flex; flex-direction:column; "
                                "align-items:center; "
                                "justify-content:center;")
'''

# ── сам кадр: во всю клетку, подпись с датой под ним ──────────
STAROE_KADR = '''            ui.image(str(p)).style("width:100%; height:auto;")
            # KABINET_VZGLYAD_V1: подпись под кадром. Что смотрим и
            # каким краном — иначе глазом реал от истории не отличить.
            _kran = "ТЕСТЕР" if state.get("mode") == "tester" else "РЕАЛ"
            ui.label(f"👁 {symbol} · {tf} · {_kran}").style(
                "color:rgba(139,233,253,0.75); font-size:11px; "
                "letter-spacing:0.06em; padding-top:6px;")
'''
NOVOE_KADR = '''            # KADR_NA_VES_KVADRAT_V1: тянемся на всю клетку, но БЕЗ
            # плющенья — contain держит пропорции свечей. Плющеная
            # свеча врёт глазу, а глаз у нас важнее цифры.
            ui.image(str(p)).style(
                "width:100%; height:100%; object-fit:contain; "
                "flex:1; min-height:0;")
            # KABINET_VZGLYAD_V1: подпись под кадром. Что смотрим и
            # каким краном — иначе глазом реал от истории не отличить.
            # KADR_NA_VES_KVADRAT_V1: плюс дата последнего бара —
            # живой рынок сегодняшним числом, тестер прошлогодним.
            _kran = "ТЕСТЕР" if state.get("mode") == "tester" else "РЕАЛ"
            _kogda = ""
            try:
                from feed_source import bars as _src_bars
                _bs, _ = _src_bars(symbol, tf, 3)
                if _bs:
                    _kogda = f" · {str(_bs[-1].get('date', ''))[:16]}"
            except Exception:
                pass
            ui.label(f"👁 {symbol} · {tf} · {_kran}{_kogda}").style(
                "color:rgba(139,233,253,0.75); font-size:11px; "
                "letter-spacing:0.06em; padding-top:6px; "
                "flex-shrink:0; width:100%; text-align:center;")
'''

STEZHKI = (
    ("клетка кадра — колонка", STAROE_KLETKA, NOVOE_KLETKA),
    ("кадр во всю клетку и дата в подписи", STAROE_KADR, NOVOE_KADR),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("═" * 58)
    print("КАДР НА ВСЮ КЛЕТКУ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 58)

    if not UI.exists():
        print("✗ не вижу Биржа/ui_torg.py — запускай из КОРНЯ репо")
        return 1

    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано — ничего не трогаю")
        return 0

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  ✗ якорь «{nazv}» найден {n} раз — файл не трогаю.")
            if n == 0:
                print("    Скорее всего не накатан patch_kabinet_vzglyad.py —")
                print("    поставь сперва его.")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  · {nazv} — заменено")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_torg.py"):
        return 1

    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_kadr_na_ves_kvadrat.py")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n✓ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nПроверить: жми «Взгляд» — картинка должна занять клетку")
    print("целиком, подпись сесть ПОД ней, и в подписи стоять дата")
    print("последнего бара. Переключи кран и нажми снова: в реале")
    print("дата сегодняшняя, в тестере — из файла.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
