# -*- coding: utf-8 -*-
"""
otperet_treyderov.py · MARKER: OTPERET_V1

ЧТО СЛУЧИЛОСЬ (моя вина)
────────────────────────
В логе три строки подряд:

    [СОВЕТ] 🤐 A06 молчит: рабочий этаж не выбран
    [СОВЕТ] 🤐 A07 молчит: рабочий этаж не выбран
    [СОВЕТ] 🤐 A08 молчит: рабочий этаж не выбран

Я поставил условие «нет рабочего этажа — не работаешь», а способа
этот этаж выбрать в кабинете НЕ ДАЛ: обход написан, но к кнопкам не
подключён, и позвать его можно только из консоли. Трейдеры оказались
заперты требованием, которое им нечем исполнить. Кнопка ТЕСТЕР при
этом не оживает: прогон видит, что работать некому, и выходит сразу.

ЧТО ПРАВИТ
──────────
1. РАБОЧИЙ ЭТАЖ ПО УМОЛЧАНИЮ — H4. Это не выдумка: слова Шефа —
   «мне комфортно работать H4-H1, я с него начинаю, смотрю, и если
   сразу не видно ничего — прохожу». Рабочий этаж и есть тот, от
   которого пляшешь. Трейдер по-прежнему волен сменить его сам,
   сказав «ЭТАЖ: H1», и его выбор всегда старше умолчания.

   В консоли видно, откуда этаж взят: «выбрал сам» или «от комфорта».

2. ПУСТОЙ ЭТАЖ У КОНТОРЫ. В логе:

       [FEED] ⚠️  Неизвестный таймфрейм '' — пропуск

   Исполнителя зовут с пустой парой — кабинет своего инструмента
   больше не имеет, а конторе он всё ещё передавался. Контора
   торгует не по инструменту: ей нужен стол цеха, а не чей-то этаж.
   Пустое больше не передаём и в кран не лезем.

3. СТОЛ ЛОЖИТСЯ В ОБЩУЮ ТЕТРАДЬ. В логе:

       [STATE] 💾 стол сохранён (общий): ...

   «общий» вместо «торговый_хаос» значит, что цех столу не назвали.
   Совет называет его сам, но ДО Совета стол успевает открыть тот,
   кто зовёт краном раньше. Патч называет цех при входе в кабинет —
   один раз, при открытии страницы.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не подключает обход этажей к кнопкам — это отдельная работа и своё
решение. Сейчас важно, чтобы трейдеры просто ожили.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py otperet_treyderov.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "OTPERET_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "vybor.py").exists()
            and (p / "Биржа" / "council.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


# ── 1. этаж по умолчанию ──
ST_V = '''    instr, otk_i = instrument_dlya(ceh, slot)
    etazh, otk_e = "", ""
    if instr:
        etazh = etazh_zhitelya(ceh, slot, instr)
        otk_e = "выбрал сам" if etazh else ""'''

NOV_V = '''    instr, otk_i = instrument_dlya(ceh, slot)
    etazh, otk_e = "", ""
    if instr:
        etazh = etazh_zhitelya(ceh, slot, instr)
        otk_e = "выбрал сам" if etazh else ""
        # OTPERET_V1: не выбрал — берём КОМФОРТНЫЙ. Слова Шефа: «мне
        # комфортно работать H4-H1, я с него начинаю, смотрю, и если
        # сразу не видно ничего — прохожу». Рабочий этаж и есть тот,
        # от которого пляшут. Раньше без выбора место молчало намертво,
        # а выбрать его в кабинете было нечем — я запер троих
        # требованием, которое им нечем исполнить.
        # Собственный выбор всегда старше умолчания.
        if not etazh:
            etazh, otk_e = ETAZH_OT_KOMFORTA, "от комфорта"'''

ST_V2 = '''PATTERN_ETAZH = "рабочий_этаж"      # ключ метки'''
NOV_V2 = '''# OTPERET_V1: с какого этажа человек пляшет, пока не сказал иначе.
ETAZH_OT_KOMFORTA = "H4"

PATTERN_ETAZH = "рабочий_этаж"      # ключ метки'''

ST_V3 = '''    if not r.get("паттерн"):
        return "свой вход ещё не выбран"
    return "рабочий этаж не выбран"'''
NOV_V3 = '''    if not r.get("паттерн"):
        return "свой вход ещё не выбран"
    return "рабочий этаж не выбран"   # OTPERET_V1: теперь почти не бывает'''


# ── 2. контора без пустой пары ──
ST_C = '''    aid, ceh, slot, fn = _EXECUTOR
    rex = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)'''
NOV_C = '''    aid, ceh, slot, fn = _EXECUTOR
    # OTPERET_V1: контора торгует не по инструменту — ей нужен стол
    # цеха, а не чей-то этаж. Кабинет своей пары больше не имеет, и
    # пустое доезжало до крана: «[FEED] Неизвестный таймфрейм ''».
    # Пары нет — берём ту, по которой реально работали в этот проход.
    _sym_i, _tf_i = symbol, timeframe
    if not (_sym_i and _tf_i):
        for _p_i in _pary.values():
            if _p_i.get("готов"):
                _sym_i, _tf_i = _p_i["symbol"], _p_i["timeframe"]
                break
    rex = _call(ceh, slot, fn, symbol=_sym_i, timeframe=_tf_i)'''


def pravit(put: Path, pary: list, imya: str) -> bool:
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"  · {put.name}: маркер уже стоит")
        return True
    beda = [st[:44].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден дословно → «{b}…»")
        return False
    novyy = t
    for st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    shutil.copy2(put, put.with_suffix(
        put.suffix + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}"))
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    vybor = koren / "Биржа" / "vybor.py"
    council = koren / "Биржа" / "council.py"
    ui_torg = koren / "Биржа" / "ui_torg.py"

    print("\n1. Рабочий этаж по умолчанию — H4 (от комфорта)")
    if not pravit(vybor, [(ST_V2, NOV_V2), (ST_V, NOV_V), (ST_V3, NOV_V3)],
                  "otperet"):
        return 1

    print("\n2. Контора без пустой пары")
    t = council.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    elif t.count(ST_C) != 1:
        print(f"  ⚠ вызов исполнителя выглядит иначе "
              f"({t.count(ST_C)} совпадений) — пропускаю этот шаг")
    else:
        if not pravit(council, [(ST_C, NOV_C)], "otperet"):
            return 1

    print("\n3. Стол ложится в тетрадь цеха, а не в общую")
    t = ui_torg.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        yakor = "def page_torg(tseh_id: str = \"торговый_хаос\") -> None:"
        if t.count(yakor) != 1:
            print("  ⚠ не нашёл вход в кабинет — пропускаю")
        else:
            vstavka = (yakor + '''
    # OTPERET_V1: назвать цех столу СРАЗУ при входе в кабинет. Совет
    # называет его сам, но до Совета стол успевает открыть тот, кто
    # зовёт краном раньше — и запись уходила в общую тетрадь
    # («[STATE] стол сохранён (общий)»).
    try:
        import hooks as _h_ceh
        if hasattr(_h_ceh, "postavit_ceh"):
            _h_ceh.postavit_ceh(tseh_id)
    except Exception:
        pass''')
            novyy = t.replace(yakor, vstavka, 1) + f"\n# {MARKER} - marker\n"
            try:
                ast.parse(novyy)
            except SyntaxError as e:
                print(f"  ✗ после правки не разбирается: {e}")
                return 1
            if SUHO:
                print("  · правка готова (сухой прогон)")
            else:
                shutil.copy2(ui_torg, ui_torg.with_suffix(
                    f".py.bak_otperet_{datetime.now():%Y%m%d_%H%M%S}"))
                ui_torg.write_text(novyy, encoding="utf-8")
                print("  ✓ цех называется при входе")

    if not SUHO:
        import py_compile
        for f in (vybor, council, ui_torg):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь на РЫНОК должно быть так:")
        print("  [СОВЕТ] 👤 A06: EURUSD H4   (от комфорта)")
        print("  [СОВЕТ] 👤 A07: XAUUSD H4")
        print("  [СОВЕТ] 👤 A08: GBPUSD H4")
        print("Скажет трейдер «ЭТАЖ: H1» — станет H1, его слово старше.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
