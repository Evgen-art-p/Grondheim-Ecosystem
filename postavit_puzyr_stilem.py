# -*- coding: utf-8 -*-
# MARKER: PUZYR_STILEM_I_UPDATE_V4
"""
ПУЗЫРЁК: ПОДСВЕТКА СТИЛЕМ + ЯВНАЯ КОМАНДА ОБНОВИТЬСЯ.

ЧТО ПОКАЗАЛ ЛОГ ШЕФА (03.09, после V3)
    [ПУЗЫРЬ] нажали: A06
    [ПУЗЫРЬ] подсветка: A06=active A07=vacant A08=vacant A05=— A09=—
    ...и ни одной строки «⚠ сорвалась».

    То есть V3 сделал своё дело: обрыва нет, подсветка доходит,
    активным считается ПРАВИЛЬНЫЙ пузырёк (A06). Причина «клик
    обрывался на первой ошибке» — снята и больше не при чём.
    А на экране кольцо всё равно висит на A09 (прежнем), и на A06
    не появляется. Значит сервер класс поставил, а браузер этого не
    показал.

ЧТО ПРОВЕРЕНО В САМОМ NiceGUI (3.16, читал исходник classes.py)
    `.classes()` шлёт обновление в браузер САМ, но только если список
    классов изменился (`if self != new_classes`). По логу он меняется,
    значит письмо уходит. Дальше по коду не различить, что именно
    ломается — не долетает обновление или класс перебивается уже на
    странице. Поэтому чиню так, чтобы работало в обоих случаях.

ЧТО ДЕЛАЕТСЯ
────────────
    1. Подсветка ставится ПРЯМО В STYLE элемента, с !important —
       inline-стиль сильнее любых классов и любых стилей Quasar, спорить
       с ним нечему. Классы .active/.done по-прежнему навешиваются, они
       не мешают.
    2. Базовый style (аватарка фоном) запоминается при первом проходе и
       не затирается — подсветка дописывается к нему.
    3. Элементу даётся ЯВНАЯ команда обновиться (`el.update()`) — на
       случай, если автоматическое письмо в браузер не уходит.
    4. В лог добавляется, скольким пузырькам стиль реально применён:
           [ПУЗЫРЬ] стиль применён: 5 из 5

СТАВИТСЯ ПОВЕРХ V3 (postavit_puzyr_ne_obryvaetsya.py) — он должен быть
накачен, патч ищет его блок. V3 остаётся на месте, ничего не откатывает.

Правит Биржа/ui_torg.py. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PUZYR_STILEM_I_UPDATE_V4"

STAR = '''            _vidno.append(f"{aid}=" + ("active" if aid == state["active_agent"]
                                       else "done" if aid in state["reports"]
                                       else "vacant" if "vacant" in base
                                       else "—"))'''

NOV = '''            _vidno.append(f"{aid}=" + ("active" if aid == state["active_agent"]
                                       else "done" if aid in state["reports"]
                                       else "vacant" if "vacant" in base
                                       else "—"))

            # PUZYR_STILEM_I_UPDATE_V4: кольцо — inline-стилем, с
            # !important. Классов оказалось мало: сервер их менял
            # (видно строкой выше), а на экране кольцо не переезжало.
            # Inline сильнее классов и стилей Quasar; плюс явная
            # команда обновиться — на случай, если автописьмо в
            # браузер не уходит.
            try:
                if not hasattr(el, "_baz_style_puzyrya"):
                    el._baz_style_puzyrya = "; ".join(
                        f"{_k}: {_v}" for _k, _v in
                        getattr(el, "_style", {}).items()) or ""
                if aid == state["active_agent"]:
                    _hvost = ("border-color: rgba(0,204,255,0.95) !important; "
                              "box-shadow: 0 0 0 2px rgba(0,204,255,0.30) inset, "
                              "0 0 30px rgba(0,204,255,0.45) !important;")
                elif aid in state["reports"]:
                    _hvost = ("border-color: rgba(0,255,136,0.95) !important; "
                              "box-shadow: 0 0 0 2px rgba(0,255,136,0.30) inset, "
                              "0 0 30px rgba(0,255,136,0.45) !important;")
                else:
                    _hvost = ("border-color: rgba(255,255,255,0.14) !important; "
                              "box-shadow: none !important;")
                _baz = el._baz_style_puzyrya
                el.style(replace=(_baz + "; " if _baz else "") + _hvost)
                el.update()
                _stil_leg += 1
            except Exception as _e_st:
                print(f"[ПУЗЫРЬ] ⚠ стиль {aid} не лёг: {_e_st}")'''

HEAD_STAR = '''        _vidno = []   # PUZYR_NE_OBRYVAETSYA_V3'''
HEAD_NOV = '''        _vidno = []   # PUZYR_NE_OBRYVAETSYA_V3
        _stil_leg = 0   # PUZYR_STILEM_I_UPDATE_V4'''

TAIL_STAR = '''        if _vidno:
            print("[ПУЗЫРЬ] подсветка: " + " ".join(_vidno))'''
TAIL_NOV = '''        if _vidno:
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
    if "PUZYR_NE_OBRYVAETSYA_V3" not in src:
        print(f"\n{f}: ! сперва нужен postavit_puzyr_ne_obryvaetsya.py "
              f"(V3) — этот патч ставится поверх него")
        return
    for kusok, imya in ((STAR, "блок подсветки"), (HEAD_STAR, "начало функции"),
                        (TAIL_STAR, "печать в лог")):
        if kusok not in src or src.count(kusok) != 1:
            print(f"\n{f}: ! не нашёл {imya} дословно — не трогаю")
            return

    novyy = src.replace(HEAD_STAR, HEAD_NOV).replace(STAR, NOV) \
               .replace(TAIL_STAR, TAIL_NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n{f}: ! после правки не разбирается ({e}) — файл НЕ тронут")
        return

    shutil.copy2(f, f.with_suffix(".py.bak_stil"))
    f.write_text(novyy, encoding="utf-8")
    print(f"\n{f}: кольцо ставится стилем + явное обновление (.bak_stil рядом)")
    print("\nВ логе теперь будет ВТОРАЯ строка:")
    print("   [ПУЗЫРЬ] стиль применён: 5 из 5")
    print("Если кольцо всё равно не переедет при 5 из 5 — дело не в")
    print("сервере вовсе, и надо смотреть страницу через F12.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
