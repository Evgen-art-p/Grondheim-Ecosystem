# -*- coding: utf-8 -*-
"""
pochinit_progon_bez_okna.py · MARKER: PROGON_BEZ_OKNA_V1

ЧТО СЛУЧИЛОСЬ (20.08)
─────────────────────
Прогон отработал верно — наблюдение взялось, город шагал молча, дошёл
до следующего места. А потом упал:

    Client has been deleted but is still being used
    KeyError: 244   в update_chat_display → chat_log_ref["element"].clear()

Это не про Биржу и не про трейдера. Это NiceGUI: вкладка браузера
переподключилась (связь моргнула, страница обновилась, компьютер ушёл
в сон), старый клиент умер — а прогон в фоне продолжает писать в его
элементы. Первая же запись в чат роняет всю задачу.

Прогон долгий: пятнадцать мест, между ними десятки молчаливых шагов.
Вероятность, что вкладка за это время моргнёт, высокая — потому и
«коннект прерывается».

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. `update_chat_display` перестаёт быть смертельной. Любой сбой при
   отрисовке — записываем в консоль и живём дальше. Лента в мёртвой
   вкладке всё равно никому не видна, а прогон не должен из-за неё
   падать.

2. Кадр рисуется так же осторожно.

3. Прогон замечает, что окна больше нет, и **доводит работу до конца
   молча**: считает, ведёт точку, пишет отчёт на диск. Отчёт лежит в
   `цеха/торговый_хаос/прогоны/` — его можно открыть и после.

Ни одной правки в том, ЧТО считается и КОГО зовут. Только в том, что
падение окна больше не роняет работу.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_progon_bez_okna.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PROGON_BEZ_OKNA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists()


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


YAKOR = '''    def update_chat_display():
        if not chat_log_ref["element"]:
            return
        chat_log_ref["element"].clear()
        with chat_log_ref["element"]:'''

NOV = '''    def update_chat_display():
        # PROGON_BEZ_OKNA_V1: вкладка могла умереть, пока прогон
        # работает в фоне (связь моргнула, страница обновилась,
        # компьютер уснул). NiceGUI на запись в мёртвого клиента
        # бросает «Client has been deleted» и KeyError, и это роняло
        # ВЕСЬ прогон. Лента в закрытой вкладке никому не видна —
        # значит и падать из-за неё нельзя. Считаем дальше молча,
        # отчёт всё равно пишется на диск.
        try:
            _risovat_chat()
        except Exception as e:
            print(f"[ПРОГОН] окно не принимает ленту ({e}) — "
                  f"работаю молча, отчёт пишется на диск")

    def _risovat_chat():
        if not chat_log_ref["element"]:
            return
        chat_log_ref["element"].clear()
        with chat_log_ref["element"]:'''

YAKOR2 = '''                    _kadr = None
                    try:
                        _kadr = await loop.run_in_executor(
                            None, lambda s=_sym, t=_tf: __import__(
                                "grafik").kadr(s, t))
                        pokazat_kadr(_kadr)
                    except Exception as _ek:
                        print(f"[ПРОГОН] кадр не нарисовался: {_ek}")'''

NOV2 = '''                    _kadr = None
                    try:
                        _kadr = await loop.run_in_executor(
                            None, lambda s=_sym, t=_tf: __import__(
                                "grafik").kadr(s, t))
                    except Exception as _ek:
                        print(f"[ПРОГОН] кадр не нарисовался: {_ek}")
                    try:
                        # PROGON_BEZ_OKNA_V1: показать — дело окна,
                        # а его может уже не быть. Кадр всё равно
                        # сохранён и попадёт в отчёт.
                        pokazat_kadr(_kadr)
                    except Exception as _ep:
                        print(f"[ПРОГОН] кадр не показан ({_ep}) — "
                              f"он в отчёте")'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "ui_torg.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if t.count(YAKOR) != 1:
        print(f"✗ якорь ленты найден {t.count(YAKOR)} раз — жду один")
        return 1
    pary = [(YAKOR, NOV)]
    if t.count(YAKOR2) == 1:
        pary.append((YAKOR2, NOV2))
    else:
        print("· кадр в шаге прогона не найден — правлю только ленту")

    novyy = t
    for yakor, zamena in pary:
        novyy = novyy.replace(yakor, zamena, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_bezokna_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ прогон переживает разрыв связи (копия: {bak.name})")
    print("\nЕсли вкладка отвалится посреди прогона, в консоли будет:")
    print("  [ПРОГОН] окно не принимает ленту (...) — работаю молча,")
    print("           отчёт пишется на диск")
    print("\nОтчёт лежит в GRONDHEIM_CITY\\Биржа\\цеха\\торговый_хаос\\прогоны")
    print("— его можно открыть и после, лента для этого не нужна.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
