# -*- coding: utf-8 -*-
"""
pochinit_tochku_v_progone.py · MARKER: TOCHKA_NE_TASHCHITSYA_V1

ЧТО ВИДНО В ЛОГЕ ПРОГОНА (20.08, EURUSD H4, 15 мест)
────────────────────────────────────────────────────
Места и ответы чередуются через одно:

    ✦ родилась BEAR @ 1.04424 · 2025.02.05   → 🔑 Нину позвали
    (следующее место 2025.05.01)             → 🔒 спит: точки нет
    ✦ родилась BULL @ 1.12873 · 2025.05.01   → 🔑 позвали
    (следующее место 2025.05.05)             → 🔒 спит
    ✦ родилась BEAR @ 1.17781 · 2025.07.24   → 🔑 позвали
    (следующее место 2025.08.06)             → 🔒 спит

Ровно половина мест теряется. Причина не в ключе и не в трейдере.

Прогон ПРЫГАЕТ: от места к месту проходят недели и месяцы. А точка
живёт между вызовами — так и задумано, в реале город идёт баром за
баром. В прогоне же на новое место приезжает точка, рождённая полгода
назад: заново она не рождается (сторона та же, формально жива), а
`proverit_tochku` её тут же и хоронит структурным сломом — цена-то за
эти месяцы ушла куда угодно. Итог: на месте, где стоит честный
разворотник с читаемой структурой, трейдера не зовут.

Об этом я предупреждал перед первым прогоном — теперь видно на числах.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. `Биржа/hooks.py` — рука `zabyt_tochku(symbol, timeframe)`: стирает
   точку по этой паре. Ничего не судит, просто чистая доска.

2. `Биржа/ui_torg.py` — прогон зовёт её сразу после того, как встал
   курсором на новое место, до того как собирается Совет. Прыгнули в
   другой год — прошлое к этому месту отношения не имеет.

Никаких порогов и никаких «сколько баров считать разрывом»: прогон
сам знает, что прыгнул, и говорит об этом прямо.

ЖИВОЙ ГОРОД НЕ ТРОНУТ. Вахта идёт баром за баром, там точка обязана
жить между барами — и живёт.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ точки ноль — патч это проверит.
Запуск: py pochinit_tochku_v_progone.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TOCHKA_NE_TASHCHITSYA_V1"
NUZHEN = "TOCHKA_ROZHDAETSYA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "ui_torg.py").exists())


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


H_YAKOR = "def _vesti_tochku(md: dict, symbol: str = \"\", timeframe: str = \"\") -> dict:"

H_RUKA = '''def zabyt_tochku(symbol: str = "", timeframe: str = "") -> bool:
    """TOCHKA_NE_TASHCHITSYA_V1: стереть точку по паре.

    Нужна прогону по истории: он ПРЫГАЕТ от места к месту через недели
    и месяцы, а точка живёт между вызовами (в реале так и надо — город
    идёт баром за баром). Без чистки на новое место приезжает точка,
    рождённая полгода назад: заново не родится, а проверка тут же
    похоронит её структурным сломом — и трейдера не позовут там, где
    стоит честный разворотник.

    Ничего не судит и никого не будит. Просто чистая доска.
    """
    try:
        t = load_trading_state()
        para = _para_tochki(symbol, timeframe)
        polka = t.get("точки") or {}
        bylo = bool((polka.get(para) or {}).get("alive"))
        if para in polka:
            polka.pop(para, None)
            t["точки"] = polka
            save_trading_state(t)
        return bylo
    except Exception as e:
        print(f"[ТОЧКА] забыть не вышло ({e}) — работаем дальше")
        return False


'''

U_YAKOR = '''                istoriya.postavit(data)
                imya = _agent_label(roster, _sl) or _sl'''

U_NOV = '''                istoriya.postavit(data)
                # TOCHKA_NE_TASHCHITSYA_V1: прогон прыгнул в другой
                # момент истории — точка с прошлого места сюда не
                # едет. Иначе она формально жива, заново не рождается,
                # и ключ молчит на честном разворотнике.
                try:
                    import hooks as _h
                    _h.zabyt_tochku(_sym, _tf)
                except Exception as _ez:
                    print(f"[ПРОГОН] точку забыть не вышло: {_ez}")
                imya = _agent_label(roster, _sl) or _sl'''


def _pravit(f: Path, pary: list, imya: str) -> bool:
    t = f.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"· {imya}: маркер уже стоит — пропускаю")
        return True
    for yakor, _ in pary:
        n = t.count(yakor)
        if n != 1:
            print(f"✗ {imya}: якорь найден {n} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return False
    novyy = t
    for yakor, zamena in pary:
        novyy = novyy.replace(yakor, zamena, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ {imya}: после правки не разбирается — {e}")
        return False
    if SUHO:
        print(f"· {imya}: правка готова (сухой прогон)")
        return True
    bak = f.with_suffix(f".py.bak_netashchim_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ {imya}: НЕ компилируется ({e}) — откатил из {bak.name}")
        return False
    print(f"✓ {imya}: правка легла (копия: {bak.name})")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")

    h = koren / "Биржа" / "hooks.py"
    if NUZHEN not in h.read_text(encoding="utf-8"):
        print("✗ Сперва накати точку ноль (postavit_tochku_nol.py) —")
        print("  этому патчу нечего чистить.")
        return 1

    if not _pravit(h, [(H_YAKOR, H_RUKA + H_YAKOR)], "hooks.py"):
        return 1
    if not _pravit(koren / "Биржа" / "ui_torg.py", [(U_YAKOR, U_NOV)],
                   "ui_torg.py"):
        print("\n⚠️  hooks.py поправлен, ui_torg.py нет — верни hooks.py из")
        print("   свежей .bak_netashchim_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nПрогони историю снова, теми же местами.")
    print("Строк «🔒 спит: точки нет» между местами быть не должно:")
    print("на каждом месте стоит разворотник с читаемой структурой,")
    print("значит на каждом должна родиться точка и зазвучать 🔑.")
    print("\nЕсли где-то всё равно замок — покажи, там будет уже другое.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
