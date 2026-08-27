# -*- coding: utf-8 -*-
"""
pochinit_progon_posle_sloma.py · MARKER: PROGON_POSLE_SLOMA_V1

ИЗ ЖИВОГО ЛОГА (20.08)
──────────────────────
    [НАБЛЮДЕНИЕ] 👁 A06 взял на карандаш EURUSD H4
    ... город шагает молча ...
    [ТОЧКА] ✕ погасла — структурный слом: цена закрылась за 1.05068
    ... и продолжает молча топтать бары до следующего места

Цепочка отработала верно. Но после смерти точки прогон продолжал
шагать: наблюдение-то с трейдера никто не снял, а снимает его только
он сам — и правильно, так решил Шеф.

Денег это не стоит (модель между событиями не зовётся), но и смысла
нет: наблюдать больше не за чем, точка ушла. По слову Шефа — «если
точка ушла, Нина в любом случае только на новом сигнале проснётся».

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
В прогоне по истории: точка по этой паре погасла — наблюдение
снимается, идём к следующему месту сразу.

Это правило ТОЛЬКО для прогона: там места известны заранее и следующее
уже ждёт. В живом городе ничего не меняется — там наблюдение по-прежнему
снимает сам трейдер, и никто, кроме него.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ прогона вперёд — патч это проверит.
Запуск: py pochinit_progon_posle_sloma.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PROGON_POSLE_SLOMA_V1"
NUZHEN = "PROGON_VPERYOD_V1"
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


YAKOR = '''                    try:
                        import hooks as _h
                        if not _h.nablyudenie(_sym, _tf, _sl):
                            break
                    except Exception as _en:
                        print(f"[ПРОГОН] наблюдение не прочлось: {_en}")
                        break'''

NOV = '''                    try:
                        import hooks as _h
                        if not _h.nablyudenie(_sym, _tf, _sl):
                            break
                        # PROGON_POSLE_SLOMA_V1: точка ушла — наблюдать
                        # больше не за чем, идём к следующему месту.
                        # Правило ТОЛЬКО для прогона: там следующее
                        # место известно заранее. В живом городе
                        # наблюдение снимает сам трейдер, и никто иной.
                        _tt = _h._blok_tochki(_h.load_trading_state(),
                                              _h._para_tochki(_sym, _tf))
                        if not _tt.get("alive"):
                            _h.snyat_nablyudenie(_sym, _tf, _sl,
                                                 "точка ушла")
                            state["chat_history"].append({
                                "role": "system",
                                "content": "✕ точка ушла — иду к "
                                           "следующему месту"})
                            update_chat_display()
                            break
                    except Exception as _en:
                        print(f"[ПРОГОН] наблюдение не прочлось: {_en}")
                        break'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "ui_torg.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_progon_vperyod.py")
        return 1
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
        return 1

    novyy = t.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_posleslom_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ прогон не топчется после слома (копия: {bak.name})")
    print("\nВ ленте вместо тишины появится:")
    print("  ✕ точка ушла — иду к следующему месту")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
