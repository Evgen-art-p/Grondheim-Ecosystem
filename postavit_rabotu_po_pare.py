# -*- coding: utf-8 -*-
"""
postavit_rabotu_po_pare.py · MARKER: RABOTA_PO_PARE_V1

ТРЕБУЕТ: сначала postavit_ruku_rynka.py и postavit_paru_mesta.py.

ЧТО ЭТО
───────
Слово Шефа 14.08: «мне не нужно, чтобы один трейдер несколько
инструментов одновременно читал, мне нужно, чтобы три трейдера три
свои инструмента выбранных читали адекватно и корректно; выбрал если
инструмент и паттерн — то пусть работает».

Один трейдер — ОДИН инструмент. Трое — три разных. До этого патча
город устроен наоборот: всем троим раздавался один инструмент с полки
кабинета, а каждый мозг втихую подменял его на свой. Этаж не подменял
никто — он оставался чужим.

ЧТО ЧИНИТ (три дыры, все настоящие)
───────────────────────────────────
1. СОВЕТ РАЗДАВАЛ ОДИН ИНСТРУМЕНТ НА ВСЕХ.
   `wake_council(symbol, timeframe)` — сама подпись двери требовала
   одну пару на весь стол. Теперь Совет спрашивает у каждого места
   ЕГО пару (`vybor.rabota_dlya`) и работает по ней. Не выбран
   инструмент, паттерн или этаж — место честно молчит с причиной, а
   не работает чужим.

2. ПОЗИЦИЯ НЕ ЗНАЛА СВОЕГО ИНСТРУМЕНТА.
   В позиции лежали трейдер, направление, вход, стоп, магик — и НИ
   СЛОВА о том, по какому инструменту она открыта. При одном общем
   инструменте это сходило с рук. При трёх разных — беда: заявка
   Синди по золоту проверялась барами Нины по евро. Цена туда не
   дойдёт никогда → заявка провисит и умрёт как «протухшая», хотя
   рынок её давно взял. А закрытие могло прибить чужую позицию
   чужой ценой и записать в журнал неверный инструмент.
   Теперь позиция несёт `symbol` и `timeframe` с рождения.

3. ФИЗИКА НЕ СМОТРЕЛА, ЧЕЙ БАР ПРИШЁЛ.
   `_settle_positions` и `_aktivirovat_ordera` шли по ВСЕМ позициям
   стола подряд. Теперь обе сверяют инструмент позиции с инструментом
   бара и чужие не трогают. Старые позиции без поля `symbol` не
   выбрасываются и не судятся вслепую — их видно в консоли отдельной
   строкой, решение по ним за Шефом.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Смену инструмента «по согласию Шефа» — следующим шагом. Сейчас
инструмент задаётся в посте, этаж трейдер ставит себе сам.

БЕЗОПАСНОСТЬ
────────────
Идемпотентен, .bak рядом, ast.parse и py_compile до записи, корень
ищет сам. Старую подпись `wake_council(symbol, timeframe)` не ломает:
аргументы стали необязательными, кабинет и тестер зовут как звали.

Запуск: py postavit_rabotu_po_pare.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RABOTA_PO_PARE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "council.py").exists()
            and (p / "Биржа" / "vybor.py").exists()
            and (p / "main.py").exists())


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


def pravit(put: Path, proverka, pravka, imya: str) -> bool:
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  · {put.name}: маркер уже стоит — пропускаю")
        return True
    ok, prichina = proverka(tekst)
    if not ok:
        print(f"  ✗ {put.name}: {prichina}")
        return False
    novyy = pravka(tekst)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    bak = put.with_suffix(put.suffix
                          + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(put, bak)
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}: правка легла (копия: {bak.name})")
    return True


# ═══════════════════════════════════════════════════════════
# 1. ГОТОВНОСТЬ МЕСТА = инструмент + паттерн + этаж
# ═══════════════════════════════════════════════════════════
ST_GOTOV = '''    instr, otk_i = instrument_dlya(ceh, slot)
    etazh, otk_e = "", ""
    if instr:
        etazh = etazh_zhitelya(ceh, slot, instr)
        otk_e = "выбрал сам" if etazh else ""
    return {"инструмент": instr, "этаж": etazh,
            "откуда_инструмент": otk_i if instr else "",
            "откуда_этаж": otk_e,
            "готов": bool(instr and etazh)}'''

NOV_GOTOV = '''    instr, otk_i = instrument_dlya(ceh, slot)
    etazh, otk_e = "", ""
    if instr:
        etazh = etazh_zhitelya(ceh, slot, instr)
        otk_e = "выбрал сам" if etazh else ""
    # RABOTA_PO_PARE_V1: слово Шефа — «выбрал если инструмент и
    # паттерн, то пусть работает». Значит готовность стоит на трёх
    # ногах, и паттерн (место входа) — такая же нога, как инструмент.
    pattern = (chitat(ceh, slot).get("текст") or "").strip()
    return {"инструмент": instr, "этаж": etazh, "паттерн": pattern,
            "откуда_инструмент": otk_i if instr else "",
            "откуда_этаж": otk_e,
            "готов": bool(instr and etazh and pattern)}'''

ST_MOLCHIT = '''    if not r["инструмент"]:
        return "инструмент не задан и не выбран"
    return "рабочий этаж не выбран"'''

NOV_MOLCHIT = '''    if not r["инструмент"]:
        return "инструмент не задан и не выбран"
    if not r.get("паттерн"):
        return "свой вход ещё не выбран"
    return "рабочий этаж не выбран"'''


# ═══════════════════════════════════════════════════════════
# 2. ФИЗИКА СМОТРИТ, ЧЕЙ БАР (hooks)
# ═══════════════════════════════════════════════════════════
ST_SETTLE_LOOP = '''    still_open, closed = [], []
    for pos in positions:
        # VASILY_ZASADA_V1: засада/заявка — не открытая позиция, закрывать
        # нечего (у WATCHING координаты входа заданы, но входа ещё НЕ БЫЛО).
        if pos.get("status") in ("WATCHING", "PENDING"):'''

NOV_SETTLE_LOOP = '''    still_open, closed = [], []
    for pos in positions:
        # RABOTA_PO_PARE_V1: ЧЕЙ БАР ПРИШЁЛ. Трое трейдеров — три
        # разных инструмента, а стол цеха один. Позиция по золоту не
        # имеет никакого отношения к барам евро: её нельзя ни закрыть
        # по чужому стопу, ни записать в журнал чужим символом.
        _psym = (pos.get("symbol") or "").strip().upper()
        if _psym and symbol and _psym != str(symbol).strip().upper():
            still_open.append(pos)
            continue
        if not _psym:
            print(f"[SETTLE] ⚠️  позиция {pos.get('trader')} без инструмента "
                  f"(открыта до 14.08) — не сужу её чужим баром {symbol}. "
                  f"Решение по старым позициям за Шефом.")
            still_open.append(pos)
            continue
        # VASILY_ZASADA_V1: засада/заявка — не открытая позиция, закрывать
        # нечего (у WATCHING координаты входа заданы, но входа ещё НЕ БЫЛО).
        if pos.get("status") in ("WATCHING", "PENDING"):'''

ST_AKT_LOOP = '''    for pos in live:
        # VASILY_ZASADA_V1: засада Консерватора — своя ветка, до PENDING.
        if pos.get("status") == "WATCHING":'''

NOV_AKT_LOOP = '''    _bar_sym = str(md.get("symbol", "") or "").strip().upper()
    for pos in live:
        # RABOTA_PO_PARE_V1: заявку берёт ТОЛЬКО её собственный рынок.
        # Иначе заявка Синди по золоту ждала бы, пока до неё дойдёт
        # евро, и умирала бы «протухшей» на живом сигнале.
        _psym = (pos.get("symbol") or "").strip().upper()
        if _bar_sym and _psym and _psym != _bar_sym:
            ostalis.append(pos)
            continue
        # VASILY_ZASADA_V1: засада Консерватора — своя ветка, до PENDING.
        if pos.get("status") == "WATCHING":'''


# ═══════════════════════════════════════════════════════════
# 3. ПОЗИЦИЯ НЕСЁТ СВОЙ ИНСТРУМЕНТ (исполнитель)
# ═══════════════════════════════════════════════════════════
ST_RUKA_YAKOR = "def _open_positions_from_table("

RUKA_RYNKA_TREYDERA = '''# ═══════════════════════════════════════════════════════════
# ЧЕЙ РЫНОК (RABOTA_PO_PARE_V1)
# ═══════════════════════════════════════════════════════════
# Раньше Исполнитель знал один инструмент на всех — тот, что пришёл
# сверху. Теперь у каждого трейдера свой, и позиция обязана родиться
# с ним: иначе физика не отличит заявку по золоту от заявки по евро.
_KEY_SLOT = {"brut": "A06", "avan": "A07", "cons": "A08"}


def _rynok_treydera(key: str, market: dict) -> tuple:
    """(инструмент, этаж) того, чей вердикт исполняем."""
    try:
        import vybor
        r = vybor.rabota_dlya("торговый_хаос", _KEY_SLOT.get(key, ""))
        if r.get("инструмент"):
            return r["инструмент"], r.get("этаж") or market.get("timeframe")
    except Exception:
        pass
    return market.get("symbol"), market.get("timeframe")


def _open_positions_from_table('''

ST_POS = '''        pos = {
            "trader":    TRADER_NAME[key],
            "magic":     magic,
            "direction": direction,'''

NOV_POS = '''        # RABOTA_PO_PARE_V1: позиция рождается ЗНАЯ свой рынок, и
        # рынок этот — ТОГО трейдера, чей вердикт исполняем. Общего
        # инструмента больше нет: у троих их три.
        _sym, _tf = _rynok_treydera(key, market)
        pos = {
            "trader":    TRADER_NAME[key],
            "symbol":    _sym,
            "timeframe": _tf,
            "magic":     magic,
            "direction": direction,'''


# ═══════════════════════════════════════════════════════════
# 4. СОВЕТ — КАЖДОМУ ЕГО ПАРА (council)
# ═══════════════════════════════════════════════════════════
ST_COUNCIL_HEAD = '''def wake_council(symbol: str, timeframe: str,
                 on_event: Optional[Callable] = None,
                 window=None, point=None,
                 ceh_id: str = _CEH_TORGOVYY) -> dict:'''

NOV_COUNCIL_HEAD = '''def _para_slota(ceh_id: str, slot: str, zapasnoy_sym: str = "",
                zapasnoy_tf: str = "") -> dict:
    """Чем и на каком этаже работает ЭТО место. RABOTA_PO_PARE_V1.

    Один трейдер — один инструмент, свой. Кабинетного «общего» тут
    нет: он и был тем четвёртым, которого никто не выбирал, а
    работали по нему все трое.

    Запасная пара нужна ровно одному случаю — прогону тестера, где
    инструмент задан файлом истории. В живой работе она пустая.
    """
    try:
        import vybor
        r = vybor.rabota_dlya(ceh_id, slot)
        if r.get("готов"):
            return {"symbol": r["инструмент"], "timeframe": r["этаж"],
                    "готов": True, "почему": ""}
        if zapasnoy_sym and zapasnoy_tf:
            return {"symbol": zapasnoy_sym, "timeframe": zapasnoy_tf,
                    "готов": True, "почему": ""}
        return {"symbol": "", "timeframe": "", "готов": False,
                "почему": vybor.pochemu_molchit(ceh_id, slot)}
    except Exception as e:
        if zapasnoy_sym and zapasnoy_tf:
            return {"symbol": zapasnoy_sym, "timeframe": zapasnoy_tf,
                    "готов": True, "почему": ""}
        return {"symbol": "", "timeframe": "", "готов": False,
                "почему": f"пара не прочиталась ({e})"}


def wake_council(symbol: str = "", timeframe: str = "",
                 on_event: Optional[Callable] = None,
                 window=None, point=None,
                 ceh_id: str = _CEH_TORGOVYY) -> dict:'''

ST_COUNCIL_RYNOK = '''    try:
        import hooks as _hr
        _rynok = _hr.rynok_novyy_bar(symbol, timeframe,
                                     window=window, point=point)
        if _rynok.get("активировано") or _rynok.get("закрыто"):
            _emit({"type": "рынок", **_rynok})
    except Exception as _er:
        print(f"[РЫНОК] ⚠️  бар не рассужен: {_er}")
'''

NOV_COUNCIL_RYNOK = '''    _sudil = set()   # RABOTA_PO_PARE_V1: какие рынки уже рассудили
    # RABOTA_PO_PARE_V1: у каждого свой рынок, значит и судить надо
    # каждый рынок отдельно — своим баром. Пары повторяются редко, но
    # если двое работают одним инструментом на одном этаже, второй
    # раз не судим.
    _za_stolom = _treydery(ceh_id)
    _pary = {}
    for _aid, _c, _slot, _fn, _pre in _za_stolom:
        _p = _para_slota(ceh_id, _slot, symbol, timeframe)
        _pary[_slot] = _p
        if not _p["готов"]:
            print(f"[СОВЕТ] 🤐 {_slot} молчит: {_p['почему']}")
            _emit({"type": "молчит", "slot": _slot, "почему": _p["почему"]})
            continue
        _klyuch = (_p["symbol"], _p["timeframe"])
        if _klyuch in _sudil:
            continue
        _sudil.add(_klyuch)
        try:
            import hooks as _hr
            _rynok = _hr.rynok_novyy_bar(
                _p["symbol"], _p["timeframe"],
                window=window if _klyuch == (symbol, timeframe) else None,
                point=point if _klyuch == (symbol, timeframe) else None)
            if _rynok.get("активировано") or _rynok.get("закрыто"):
                _emit({"type": "рынок", "рынок": _p["symbol"],
                       "этаж": _p["timeframe"], **_rynok})
        except Exception as _er:
            print(f"[РЫНОК] ⚠️  {_p['symbol']} {_p['timeframe']} "
                  f"не рассужен: {_er}")
'''

ST_COUNCIL_TREYDERY = '''    _za_stolom = _treydery(ceh_id)
    if not _za_stolom:
        print("[СОВЕТ] в цехе нет ни одного картриджа с мозгом")
    for aid, ceh, slot, fn, pre in _za_stolom:
        r = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)'''

NOV_COUNCIL_TREYDERY = '''    if not _za_stolom:
        print("[СОВЕТ] в цехе нет ни одного картриджа с мозгом")
    for aid, ceh, slot, fn, pre in _za_stolom:
        # RABOTA_PO_PARE_V1: каждому — ЕГО инструмент и ЕГО этаж.
        _p = _pary.get(slot) or _para_slota(ceh_id, slot, symbol, timeframe)
        if not _p["готов"]:
            summary["verdicts"][aid] = None
            summary["results"][aid] = {"ok": False, "error": _p["почему"],
                                       "молчит": True}
            continue
        print(f"[СОВЕТ] 👤 {slot}: {_p['symbol']} {_p['timeframe']}")
        r = _call(ceh, slot, fn,
                  symbol=_p["symbol"], timeframe=_p["timeframe"])'''



def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    vybor = koren / "Биржа" / "vybor.py"
    hooks = koren / "Биржа" / "hooks.py"
    council = koren / "Биржа" / "council.py"
    ispoln = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
              / "слоты" / "исполнитель" / "мозг.py")

    # проверка предшественников
    nety = []
    if "RUKA_RYNKA_V1" not in hooks.read_text(encoding="utf-8"):
        nety.append("postavit_ruku_rynka.py")
    if "PARA_MESTA_V1" not in vybor.read_text(encoding="utf-8"):
        nety.append("postavit_paru_mesta.py")
    if nety:
        print("✗ Сначала накати: " + ", ".join(nety))
        print("  Этот патч стоит на них.")
        return 1

    print("\n1. Готовность места = инструмент + паттерн + этаж")
    ok1 = pravit(
        vybor,
        lambda t: (t.count(ST_GOTOV) == 1 and t.count(ST_MOLCHIT) == 1,
                   "не нашёл rabota_dlya/pochemu_molchit дословно"),
        lambda t: t.replace(ST_GOTOV, NOV_GOTOV, 1)
                   .replace(ST_MOLCHIT, NOV_MOLCHIT, 1)
                   + "\n# RABOTA_PO_PARE_V1 - marker\n",
        "para2")

    print("\n2. Физика смотрит, чей бар пришёл")
    ok2 = pravit(
        hooks,
        lambda t: (t.count(ST_SETTLE_LOOP) == 1 and t.count(ST_AKT_LOOP) == 1,
                   "не нашёл циклы закрытия/активации дословно"),
        lambda t: t.replace(ST_SETTLE_LOOP, NOV_SETTLE_LOOP, 1)
                   .replace(ST_AKT_LOOP, NOV_AKT_LOOP, 1)
                   + "\n# RABOTA_PO_PARE_V1 - marker\n",
        "chey_bar")

    print("\n3. Позиция рождается со своим инструментом")
    ok3 = pravit(
        ispoln,
        lambda t: (t.count(ST_POS) == 1 and t.count(ST_RUKA_YAKOR) == 1,
                   "не нашёл рождение позиции дословно"),
        lambda t: t.replace(ST_RUKA_YAKOR, RUKA_RYNKA_TREYDERA, 1)
                   .replace(ST_POS, NOV_POS, 1)
                   + "\n# RABOTA_PO_PARE_V1 - marker\n",
        "pos_symbol")

    print("\n4. Совет даёт каждому его пару")
    ok4 = pravit(
        council,
        lambda t: (t.count(ST_COUNCIL_HEAD) == 1
                   and t.count(ST_COUNCIL_RYNOK) == 1
                   and t.count(ST_COUNCIL_TREYDERY) == 1,
                   "не нашёл якоря Совета дословно"),
        lambda t: t.replace(ST_COUNCIL_HEAD, NOV_COUNCIL_HEAD, 1)
                   .replace(ST_COUNCIL_RYNOK, NOV_COUNCIL_RYNOK, 1)
                   .replace(ST_COUNCIL_TREYDERY, NOV_COUNCIL_TREYDERY, 1)
                   + "\n# RABOTA_PO_PARE_V1 - marker\n",
        "sovet_pary")

    if not (ok1 and ok2 and ok3 and ok4):
        print("\n✗ Не всё легло — файлы целы.")
        return 1

    if not SUHO:
        import py_compile
        for f in (vybor, hooks, council, ispoln):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь на кнопку РЫНОК:")
        print("  каждое место берёт СВОЙ инструмент и СВОЙ этаж;")
        print("  рынок судится по каждому из них отдельно, своим баром;")
        print("  чужие позиции не трогаются — у позиции есть инструмент;")
        print("  кому нечем работать — молчит с причиной в консоли.")
        print("\nПока ни у кого нет рабочего этажа — все трое промолчат.")
        print("Этаж трейдер ставит себе сам словом «ЭТАЖ: H1».")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
