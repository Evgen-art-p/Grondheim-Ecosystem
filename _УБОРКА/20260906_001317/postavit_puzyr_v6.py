# -*- coding: utf-8 -*-
# MARKER: PUZYR_BEZ_GETHTMLELEMENT_V6
"""
КОМАНДА БРАУЗЕРУ — БЕЗ getHtmlElement.

ЧТО ПОКАЗАЛА КОНСОЛЬ БРАУЗЕРА (Шеф открыл F12, 04.09 00:19)
    [ПУЗЫРЬ] команда в браузер: 5 пузырьков      ← в логе сервера
    ReferenceError: getHtmlElement is not defined ← в консоли браузера

    То есть подход V5 верный: команда доходит до нужного окна, связь
    живая. Ошибся я в одном — в способе адресации. `getHtmlElement`
    появился только в NiceGUI 2.9, а в установленной версии его нет,
    поэтому команда падала целиком, не успев ничего покрасить.

    Заодно это окончательно объясняет и первопричину: обновления
    элементов до пузырьков не доезжают, а прямая команда доезжает —
    значит дело именно в доставке к этим элементам, как и было
    записано в кабинете про ленту чата.

ЧТО ДЕЛАЕТСЯ
────────────
    Адресация меняется на самую обычную и не зависящую ни от версии
    NiceGUI, ни от Quasar: браузер сам находит пузырьки по их
    оформлению (класс `avatar`) в том же порядке, в каком они
    нарисованы, и красит по списку. Ничего специфического не
    вызывается — только то, что есть в любом браузере.

    Порядок надёжен: пузырьки рисуются одним циклом по roster, и в
    том же порядке лежат в avatars_ref — значит N-й на экране это
    N-й в списке.

    В лог добавлена длина списка, чтобы при расхождении это было
    видно сразу.

Ставится ПОВЕРХ V5 (postavit_puzyr_v_brauzer.py). Идемпотентен.
.bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PUZYR_BEZ_GETHTMLELEMENT_V6"

STAR = '''                _kuski.append(
                    "(()=>{const e=getHtmlElement(%d);"
                    "if(e){e.style.setProperty('border-color','%s','important');"
                    "e.style.setProperty('box-shadow','%s','important');}})();"
                    % (_el.id, _bc, _bs))
            if _kuski:
                ui.run_javascript("".join(_kuski))
                print(f"[ПУЗЫРЬ] команда в браузер: {len(_kuski)} пузырьков")'''

NOV = '''                # PUZYR_BEZ_GETHTMLELEMENT_V6: getHtmlElement есть
                # только с NiceGUI 2.9 — на здешней версии команда
                # падала целиком (ReferenceError в консоли). Берём
                # самый обычный способ: браузер сам находит пузырьки
                # по их оформлению, в порядке отрисовки.
                _kuski.append("['%s','%s']" % (_bc, _bs))
            if _kuski:
                _js = ("(()=>{const st=[" + ",".join(_kuski) + "];"
                       "const els=document.querySelectorAll('.avatar');"
                       "els.forEach((e,i)=>{if(st[i]){"
                       "e.style.setProperty('border-color',st[i][0],'important');"
                       "e.style.setProperty('box-shadow',st[i][1],'important');"
                       "}});})();")
                ui.run_javascript(_js)
                print(f"[ПУЗЫРЬ] команда в браузер: {len(_kuski)} пузырьков")'''


def _nayti_birzhu() -> Path:
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (koren / "Биржа", koren):
            if (p / "ui_torg.py").exists():
                return p
    print("Не нашёл Биржа/ui_torg.py.")
    s = input("Перетащи сюда папку «Биржа» и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if (p / "ui_torg.py").exists():
        return p
    raise SystemExit("не та папка — там нет ui_torg.py")


def main():
    f = _nayti_birzhu() / "ui_torg.py"
    src = f.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"\n{f}: уже накачено")
        return
    if "PUZYR_PRYAMO_V_BRAUZER_V5" not in src:
        print(f"\n{f}: ! сперва нужен postavit_puzyr_v_brauzer.py (V5)")
        return
    if STAR not in src or src.count(STAR) != 1:
        print(f"\n{f}: ! не нашёл кусок с getHtmlElement дословно — не трогаю")
        return

    novyy = src.replace(STAR, NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_v6"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}: getHtmlElement убран, ищем по классу (.bak_v6 рядом)")
    print("\nВ консоли браузера (F12) красной строки про getHtmlElement")
    print("быть больше не должно, а кольцо — переезжать.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
