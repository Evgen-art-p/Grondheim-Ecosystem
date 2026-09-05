# -*- coding: utf-8 -*-
# MARKER: PUZYR_PRYAMO_V_BRAUZER_V5
"""
КОЛЬЦО — ПРЯМОЙ КОМАНДОЙ БРАУЗЕРУ.

ЧТО УЖЕ ИСКЛЮЧЕНО (проверено, не догадки)
    · Обрыв клика — нет: V3 показал чистый лог, ни одной «сорвалась».
    · Не тот пузырёк — нет: лог говорит A06=active, это правильный.
    · Классы не ставятся — ставятся: читал исходник nicegui 3.16,
      `.classes()` шлёт обновление сам, когда список изменился.
    · div против кнопки — не при чём: прогнал оба на живом nicegui,
      ведут себя одинаково.
    · Стили Quasar сильнее — нет: V4 ставит inline с !important.
    · Код Академии другой — нет: там БУКВАЛЬНО тот же
      `el.classes(replace=base)` + `add("active")` и тот же порядок
      вызовов при клике.
    · Связь с браузером мертва — нет: часы в шапке идут верно.
    · Пузырьки рисуются дважды — нет: отрисовка одна.

ЧТО ОСТАЛОСЬ
    Сервер делает всё правильно, а на экране кольцо не переезжает.
    Значит теряется последнее звено — доставка обновления ИМЕННО
    ЭТИМ элементам. Кабинет с такой болезнью уже сталкивался, вот
    запись рядом в этом же файле (KABINET_ZHIVYOT_PRI_GORODE_V1):
        «Прогон, начатый в другой вкладке (или до обновления
         страницы), держит ссылку на СТАРОЕ окно и в это уже не
         пишет.»
    Для ленты чата это лечили догонялкой. Для пузырьков — нечем.

ЧТО ДЕЛАЕТСЯ
────────────
    Перестаём просить элемент обновиться и приказываем БРАУЗЕРУ
    напрямую: `ui.run_javascript` в момент клика. Команда уходит в
    то окно, где кликнули, — обработчик клика знает своего клиента
    наверняка, в отличие от элемента, созданного когда-то раньше.
    Каждый пузырёк адресуется по своему номеру через getHtmlElement,
    так что промахнуться мимо элемента нельзя.

    Всё прежнее (классы, inline-стиль) остаётся на месте и не
    мешает: если доставка вдруг починится сама, они сработают.

    В лог добавляется строка:
        [ПУЗЫРЬ] команда в браузер: 5 пузырьков
    Если она есть, а кольцо не двигается — значит дело уже не в
    сервере вовсе, и дальше только F12.

Ставится ПОВЕРХ V3 и V4. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PUZYR_PRYAMO_V_BRAUZER_V5"

STAR = '''        if _vidno:
            print("[ПУЗЫРЬ] подсветка: " + " ".join(_vidno))
            print(f"[ПУЗЫРЬ] стиль применён: {_stil_leg} из {len(_vidno)}")'''

NOV = '''        # PUZYR_PRYAMO_V_BRAUZER_V5: приказываем браузеру напрямую.
        # Обновление элементов где-то теряется (см. докстроку патча),
        # а команда из обработчика клика уходит в ТО окно, где кликнули.
        try:
            _kuski = []
            for _aid, _el in avatars_ref["elements"].items():
                if _aid == state["active_agent"]:
                    _bc, _bs = ("rgba(0,204,255,0.95)",
                                "0 0 0 2px rgba(0,204,255,0.30) inset, "
                                "0 0 30px rgba(0,204,255,0.45)")
                elif _aid in state["reports"]:
                    _bc, _bs = ("rgba(0,255,136,0.95)",
                                "0 0 0 2px rgba(0,255,136,0.30) inset, "
                                "0 0 30px rgba(0,255,136,0.45)")
                else:
                    _bc, _bs = ("rgba(255,255,255,0.14)", "none")
                _kuski.append(
                    "(()=>{const e=getHtmlElement(%d);"
                    "if(e){e.style.setProperty('border-color','%s','important');"
                    "e.style.setProperty('box-shadow','%s','important');}})();"
                    % (_el.id, _bc, _bs))
            if _kuski:
                ui.run_javascript("".join(_kuski))
                print(f"[ПУЗЫРЬ] команда в браузер: {len(_kuski)} пузырьков")
        except Exception as _e_js:
            # фоновый вызов без окна — это нормально, не шумим лишнего
            print(f"[ПУЗЫРЬ] команда в браузер не ушла: {_e_js}")

        if _vidno:
            print("[ПУЗЫРЬ] подсветка: " + " ".join(_vidno))
            print(f"[ПУЗЫРЬ] стиль применён: {_stil_leg} из {len(_vidno)}")'''


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
    if "PUZYR_STILEM_I_UPDATE_V4" not in src:
        print(f"\n{f}: ! сперва нужны V3 и V4 — этот патч ставится поверх них")
        return
    if STAR not in src or src.count(STAR) != 1:
        print(f"\n{f}: ! не нашёл блок печати дословно — не трогаю")
        return

    novyy = src.replace(STAR, NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_brauzer"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}: кольцо ставится прямой командой браузеру (.bak_brauzer рядом)")
    print("\nВ логе появится строка:")
    print("   [ПУЗЫРЬ] команда в браузер: 5 пузырьков")
    print("\nЕсли она есть, а кольцо стоит на месте — сервер тут ни при чём,")
    print("и дальше я по коду не найду: нужен взгляд в саму страницу (F12).")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
