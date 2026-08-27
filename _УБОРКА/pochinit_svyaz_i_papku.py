# -*- coding: utf-8 -*-
"""
pochinit_svyaz_i_papku.py · MARKER: SVYAZ_I_PAPKA_V1

ПОЧЕМУ ВКЛАДКА ОТВАЛИВАЕТСЯ РАЗ ЗА РАЗОМ
────────────────────────────────────────
В логе прогона список всех тридцати CSV повторяется десятки раз:

    [CORE] 📂 EURUSDH4.csv: 50110 баров ...
    [CORE] 📂 GBPUSDM5.csv: 100000 баров ...
    ... и так весь каталог, снова и снова
    Timer cancelled because client is not connected after 60.0 seconds

Это не прогон. Это ПОЛКА. Когда браузер переподключается, страница
кабинета строится заново, а при постройке она сканирует папку
test_data и читает КАЖДЫЙ csv целиком — почти миллион баров, в главном
потоке. Пока читает, сервер не отвечает; браузер ждёт минуту и рвёт
связь; связь порвалась — страница строится ещё раз, и так по кругу.

Отсюда и «коннект прерывается», и таймеры, гаснущие по 60 секунд.

И вторая моя вина, помельче: молчаливый шаг прогона я звал прямо в
корутине — рука рынка считала приборы, держа тот же поток. Каждый шаг
подмораживал окно.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Полка запоминает разобранные файлы: путь, размер и время правки.
   Файл не менялся — берём из памяти, диск не трогаем. Поменялся или
   появился новый — читаем его один раз. Пересборка страницы после
   переподключения перестаёт стоить миллион баров.

2. Молчаливый шаг прогона уходит в рабочий поток, как и все остальные
   тяжёлые вызовы вокруг. Окно остаётся живым, пока город считает.

Ни одной правки в том, что считается. Только в том, сколько раз мы
читаем одно и то же с диска и в каком потоке.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_svyaz_i_papku.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "SVYAZ_I_PAPKA_V1"
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


# ── 1. полка помнит разобранные файлы ────────────────────────

YAKOR = '''    def _passport_from_csv(path):
        from williams_core import read_mt5_csv
        p = Path(path)
        bars = read_mt5_csv(str(p))
        if not bars:
            return None'''

NOV = '''    def _passport_from_csv(path):
        # SVYAZ_I_PAPKA_V1: помним разобранные файлы по пути, размеру и
        # времени правки. Пересборка страницы (а она случается на КАЖДОМ
        # переподключении браузера) читала весь каталог заново — почти
        # миллион баров в главном потоке. Сервер молчал, браузер рвал
        # связь по минуте, страница строилась опять — и так по кругу.
        from williams_core import read_mt5_csv
        p = Path(path)
        try:
            st = p.stat()
            klyuch = (str(p.resolve()), st.st_size, int(st.st_mtime))
        except Exception:
            klyuch = None
        if klyuch is not None and klyuch in _PASPORTA_KESH:
            return dict(_PASPORTA_KESH[klyuch])
        bars = read_mt5_csv(str(p))
        if not bars:
            return None'''

YAKOR2 = '''        symbol, tf = _parse_symbol_tf(p.name)
        return {
            "name": p.name, "path": str(p), "symbol": symbol, "timeframe": tf,
            "bars": len(bars), "date_from": bars[0].get("date", "?"), "date_to": bars[-1].get("date", "?"),
        }'''

NOV2 = '''        symbol, tf = _parse_symbol_tf(p.name)
        _pasport = {
            "name": p.name, "path": str(p), "symbol": symbol, "timeframe": tf,
            "bars": len(bars), "date_from": bars[0].get("date", "?"), "date_to": bars[-1].get("date", "?"),
        }
        if klyuch is not None:      # SVYAZ_I_PAPKA_V1
            _PASPORTA_KESH[klyuch] = dict(_pasport)
        return _pasport'''

YAKOR3 = '''    _TEST_DATA_DIR = _HERE / "test_data"'''

NOV3 = '''    _TEST_DATA_DIR = _HERE / "test_data"

    # SVYAZ_I_PAPKA_V1: память полки живёт в модуле, а не в странице —
    # переподключился браузер, страница новая, а разобранные файлы те же.
    global _PASPORTA_KESH
    try:
        _PASPORTA_KESH
    except NameError:
        _PASPORTA_KESH = {}'''

# ── 2. молчаливый шаг — в рабочий поток ──────────────────────

YAKOR4 = '''                    try:
                        import hooks as _hh
                        _hh.rynok_novyy_bar(_sym, _tf)
                        _kk = __import__("council")._klyuch_probuzhdeniya(
                            _sym, _tf, _sl)'''

NOV4 = '''                    try:
                        # SVYAZ_I_PAPKA_V1: молчаливый шаг — в рабочий
                        # поток. Раньше он считал приборы прямо в
                        # корутине и подмораживал окно на каждом баре.
                        def _schitat(s=_sym, t=_tf, sl=_sl):
                            import hooks as _hh2
                            _hh2.rynok_novyy_bar(s, t)
                            return __import__("council")._klyuch_probuzhdeniya(
                                s, t, sl)
                        _kk = await loop.run_in_executor(None, _schitat)'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "ui_torg.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [(YAKOR3, NOV3), (YAKOR, NOV), (YAKOR2, NOV2)]
    if t.count(YAKOR4) == 1:
        pary.append((YAKOR4, NOV4))
    else:
        print("· молчаливого шага не нашёл — правлю только полку")

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

    bak = f.with_suffix(f".py.bak_svyaz_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ полка помнит файлы, шаг ушёл в поток (копия: {bak.name})")
    print("\nПосле накатки список всех CSV в консоли должен появиться")
    print("ОДИН раз за запуск города, а не десятки. И «Timer cancelled»")
    print("с обрывами связи должны прекратиться.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
