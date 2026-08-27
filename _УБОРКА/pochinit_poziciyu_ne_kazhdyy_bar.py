# -*- coding: utf-8 -*-
"""
pochinit_poziciyu_ne_kazhdyy_bar.py · MARKER: POZICIYA_NE_KAZHDYY_BAR_V1

ЧТО НАШЛОСЬ НА ГОДОВОМ ПРОГОНЕ
──────────────────────────────
Пока позиция открыта, ключ будил трейдера КАЖДЫЙ бар:

    2025.08.14 08:00 · своя OPEN — позицию ведём
    2025.08.14 12:00 · своя OPEN — позицию ведём
    2025.08.14 16:00 · своя OPEN — позицию ведём
    ... и так до самого закрытия

Одна сделка на десять дней — это шестьдесят оплаченных взглядов вместо
одного. На годовом прогоне — сотни.

А правило Шефа стоит с самого начала и здесь тоже верно: побарный
мониторинг — ошибка большинства трейдеров. Стоп ведёт код, по фракталам
(VEDENIE_FRAKTALY_V1). Смотреть каждую свечу человеку не за чем.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Заявка и позиция будят по СОБЫТИЮ, а не по факту существования:

    заявка висит, ещё не сработала → зовём (её надо держать в голове)
    позиция ТОЛЬКО ЧТО открылась    → зовём: вошёл, вот твоя цена
    позиция ТОЛЬКО ЧТО закрылась    → зовём: чем кончилось
    позиция просто стоит открытой   → молчим, стоп ведёт код
    случилось событие структуры     → зовём, как и раньше

То есть трейдера дёргают на входе, на выходе и на событиях рынка —
ровно там, где от него что-то зависит.

Различаем «только что» по бару города: если позиция открылась или
закрылась на ЭТОМ баре — событие; на прошлом — уже нет.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_poziciyu_ne_kazhdyy_bar.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "POZICIYA_NE_KAZHDYY_BAR_V1"
NUZHEN = "KLYUCH_PROBUZHDENIYA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "council.py").exists()
            and (p / "Биржа" / "hooks.py").exists())


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


H_YAKOR = '''    if closed:
        chain["open_positions"] = still_open
        tstate = load_trading_state()
        tstate["positions"] = still_open
        save_trading_state(tstate)'''

H_NOV = '''    if closed:
        chain["open_positions"] = still_open
        tstate = load_trading_state()
        tstate["positions"] = still_open
        # POZICIYA_NE_KAZHDYY_BAR_V1: последнее закрытие — в стол, чтобы
        # ключ мог позвать трейдера ровно на том баре, где сделка
        # кончилась. Раньше закрытия жили только в журнале, и город
        # молчал о самом важном.
        _p = closed[-1]
        tstate["последнее_закрытие"] = {
            "бар": _p.get("closed_at"),
            "symbol": _p.get("symbol"),
            "причина": _p.get("close_reason"),
            "выход": _p.get("exit"),
            "pnl": _p.get("pnl_price"),
        }
        save_trading_state(tstate)'''

YAKOR = '''        # позицию ведём всегда, чем бы ни кончилась точка
        sym = (symbol or "").strip().upper()
        for p in (t.get("positions") or []):
            if p.get("status") not in _ZHIVYE_STATUSY:
                continue
            psym = (p.get("symbol") or "").strip().upper()
            # инструмента в записи нет (старая позиция) — считаем своей
            if not psym or psym == sym:
                return {"будим": True,
                        "почему": f"своя {p.get('status')} — позицию ведём"}'''

NOV = '''        # POZICIYA_NE_KAZHDYY_BAR_V1: заявка и позиция будят по
        # СОБЫТИЮ, а не по факту существования. Раньше открытая позиция
        # звала каждый бар — одна сделка на десять дней стоила шестьдесят
        # оплаченных взглядов. Стоп ведёт код по фракталам, смотреть
        # каждую свечу человеку не за чем: побарный мониторинг — ошибка
        # большинства трейдеров (слово Шефа).
        sym = (symbol or "").strip().upper()
        for p in (t.get("positions") or []):
            if p.get("status") not in _ZHIVYE_STATUSY:
                continue
            psym = (p.get("symbol") or "").strip().upper()
            # инструмента в записи нет (старая позиция) — считаем своей
            if psym and sym and psym != sym:
                continue
            _st = p.get("status")
            if _st in ("WATCHING", "PENDING"):
                return {"будим": True,
                        "почему": f"своя {_st} — заявка ещё висит"}
            # открылась на ЭТОМ баре — вошёл, надо сказать
            if bar_goroda and str(p.get("opened_at") or "") == bar_goroda:
                return {"будим": True,
                        "почему": f"вошёл @ {p.get('entry')} — позиция открыта"}
            # просто стоит открытой — молчим, стоп ведёт код

        # закрылась на этом баре — чем кончилось
        _z = t.get("последнее_закрытие") or {}
        if (_z and bar_goroda
                and str(_z.get("бар") or "") == bar_goroda):
            _zsym = (_z.get("symbol") or "").strip().upper()
            if not (_zsym and sym and _zsym != sym):
                return {"будим": True,
                        "почему": f"сделка закрылась: {_z.get('причина')} "
                                  f"@ {_z.get('выход')}"}'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "council.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_klyuch_probuzhdeniya.py")
        return 1
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
        return 1

    # сперва hooks: закрытие должно попадать в стол
    h = koren / "Биржа" / "hooks.py"
    ht = h.read_text(encoding="utf-8")
    if MARKER not in ht:
        if ht.count(H_YAKOR) != 1:
            print(f"✗ hooks.py: якорь найден {ht.count(H_YAKOR)} раз")
            return 1
        hnov = ht.replace(H_YAKOR, H_NOV, 1) + f"\n# {MARKER} - marker\n"
        try:
            ast.parse(hnov)
        except SyntaxError as e:
            print(f"✗ hooks.py не разбирается: {e}")
            return 1
        if not SUHO:
            hbak = h.with_suffix(
                f".py.bak_nekazhdyy_{datetime.now():%Y%m%d_%H%M%S}")
            shutil.copy2(h, hbak)
            h.write_text(hnov, encoding="utf-8")
            py_compile.compile(str(h), doraise=True)
            print(f"✓ hooks.py: закрытие пишется в стол ({hbak.name})")

    novyy = t.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_nekazhdyy_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ позиция больше не будит каждый бар (копия: {bak.name})")
    print("\nТеперь трейдера зовут: на входе, на выходе, на событиях")
    print("структуры и пока висит несработавшая заявка.")
    print("\nПока позиция просто стоит — молчим, стоп ведёт код по")
    print("фракталам. Одна сделка на десять дней стоит два взгляда,")
    print("а не шестьдесят.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
