# -*- coding: utf-8 -*-
"""
pochinit_odin_bar_odno_reshenie.py · MARKER: ODIN_BAR_ODNO_RESHENIE_V1

ЧТО ПОКАЗАЛ ПРОГОН (20.08, GBPUSD H4)
─────────────────────────────────────
Второе событие сработало ПЕРВЫЙ раз за всё время:

    [ВОЛНА 1] ⛰ кончилась @ 1.34226 · бар 2025.10.06 00:00 · 13 бар. от точки

А через две строки, на том же самом баре и по той же цене:

    [ТОЧКА] ✦ родилась BULL @ 1.34226 · бар 2025.10.06 00:00
    [КЛЮЧ]  🔑 A06: точка родилась: BULL @ 1.34226

Трейдера позвали — но с другим поводом. Событие, ради которого всё
строилось, до него не доехало.

ПОЧЕМУ
──────
Рука рынка на одном баре зовётся ДВАЖДЫ: сперва молчаливым шагом
прогона (посчитать и посмотреть ключ), потом внутри самого Совета,
когда трейдера уже позвали.

Первый заход честно отметил конец волны 1. Второй зашёл на тот же бар
заново, увидел, что отметка уже стоит, — и провалился дальше, в блок
рождения. А там разворотник обратной стороны с читаемой структурой —
законное новое начало: точка родилась заново, отметка о конце волны
стёрлась (её стирает рождение), и ключ доложил про рождение.

Оба решения по отдельности верны. Беда в том, что их приняли ДВА РАЗА
на одном баре, и второе затёрло первое.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Один бар — одно решение. Рука рынка запоминает, на каком баре она уже
решала по этой паре, и на повторный заход отдаёт ТОТ ЖЕ ответ, ничего
не пересчитывая и ничего не затирая.

Ни одного нового правила про рынок. Только запрет решать дважды об
одном и том же.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_odin_bar_odno_reshenie.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "ODIN_BAR_ODNO_RESHENIE_V1"
NUZHEN = "TOCHKA_ROZHDAETSYA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "hooks.py").exists()


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


YAKOR = '''    para = _para_tochki(symbol, timeframe)
    try:
        wf = md.get("wave_form") or {}
        napr = wf.get("bdb_dir")
        cena = wf.get("bdb_price")
        price = md.get("price") or {}
        bar = md.get("bar_time")

        t = load_trading_state()
        isk = _blok_tochki(t, para)'''

NOV = '''    para = _para_tochki(symbol, timeframe)
    try:
        wf = md.get("wave_form") or {}
        napr = wf.get("bdb_dir")
        cena = wf.get("bdb_price")
        price = md.get("price") or {}
        bar = md.get("bar_time")

        t = load_trading_state()
        isk = _blok_tochki(t, para)

        # ODIN_BAR_ODNO_RESHENIE_V1: один бар — одно решение.
        # Рука рынка на одном баре зовётся дважды: молчаливым шагом
        # прогона и потом внутри Совета. В прогоне 20.08 из-за этого
        # пропал первый в истории конец волны 1: первый заход его
        # отметил, второй зашёл заново, увидел отметку, провалился в
        # блок рождения — и точка родилась поверх события, стерев его.
        # Оба решения по отдельности верны, но принимать их дважды об
        # одном баре нельзя.
        if bar and str(isk.get("reshali_na_bare") or "") == str(bar):
            return dict(isk.get("otvet_bara") or {"alive": bool(isk.get("alive"))})

        def _zapomnit_otvet(otvet: dict) -> dict:
            """Запомнить решение этого бара и отдать его как есть."""
            try:
                t2 = load_trading_state()
                isk2 = _blok_tochki(t2, para)
                isk2["reshali_na_bare"] = str(bar or "")
                isk2["otvet_bara"] = dict(otvet)
                save_trading_state(t2)
            except Exception:
                pass
            return otvet'''

# каждый выход руки — через память бара
ZAMENY = [
    ('''                print(f"[ВОЛНА 1] ⛰ {para}: кончилась @ {cena} · бар {bar} "
                      f"· {_prozhito} бар(ов) от точки "
                      f"(структура {_dlina})")
                return {"alive": True, "konec_volny_1": True,
                        "direction": storona}''',
     '''                print(f"[ВОЛНА 1] ⛰ {para}: кончилась @ {cena} · бар {bar} "
                      f"· {_prozhito} бар(ов) от точки "
                      f"(структура {_dlina})")
                return _zapomnit_otvet({"alive": True, "konec_volny_1": True,
                                        "direction": storona})'''),
    ('''                return {"alive": True, "rodilas": True, "direction": napr}''',
     '''                return _zapomnit_otvet({"alive": True, "rodilas": True,
                                        "direction": napr})'''),
    ('''        elif res.get("changed"):
            print(f"[ТОЧКА] ✕ {para}: погасла — {res.get('reason')}")
        return res''',
     '''        elif res.get("changed"):
            print(f"[ТОЧКА] ✕ {para}: погасла — {res.get('reason')}")
        return _zapomnit_otvet(res)'''),
]


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "hooks.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_tochku_nol.py")
        return 1

    pary = [(YAKOR, NOV)] + ZAMENY
    for yakor, _ in pary:
        if t.count(yakor) != 1:
            print(f"✗ якорь найден {t.count(yakor)} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return 1

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

    bak = f.with_suffix(f".py.bak_odinbar_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ один бар — одно решение (копия: {bak.name})")
    print("\nТеперь конец волны 1 доедет до трейдера: ключ скажет")
    print("  [КЛЮЧ] 🔑 A06: волна 1 кончилась @ 1.34226 (13 бар. от точки)")
    print("а не «точка родилась», как вышло в прошлом прогоне.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
