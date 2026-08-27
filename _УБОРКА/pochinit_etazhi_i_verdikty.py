# -*- coding: utf-8 -*-
"""
pochinit_etazhi_i_verdikty.py · MARKER: SVEZHEST_V1

ДВЕ БЕДЫ ИЗ ЖИВОГО ЛОГА 18.08
─────────────────────────────

БЕДА 1: СТАРШИЕ ЭТАЖИ НЕ ПРИХОДЯТ
    [FEED] ⚠️  Нет котировок: EURUSD D1     (десяток раз подряд)

    Полез в таблицу кодов MT5 — два из них НЕВЕРНЫЕ:

        W1  = 16409   а должно 32769
        MN1 = 16410   а должно 49153

    То есть недельного и месячного этажей город не получал НИКОГДА:
    просил их по несуществующим кодам. По ним считается компас —
    направление сверху, — значит компас был слеп по определению.

    D1 = 16408 верен. Там другое: MT5 отдаёт пусто, пока история
    этажа не «прокачана» в терминале. Лечится тем же приёмом, что
    и везде с MT5: выбрать символ в обзор рынка и повторить запрос.
    Первый заход часто пустой, второй приносит данные.

БЕДА 2: ИСПОЛНИТЕЛЬ СУДИТ ПО ПРОТУХШИМ ВЕРДИКТАМ
    [СОВЕТ] 🤐 A07 молчит   ← Совет их НЕ ЗВАЛ
    [СОВЕТ] 🤐 A08 молчит
    A09: Авантюрист: REJECTED (...)   ← а Исполнитель их доложил
         Консерватор: REJECTED (...)

    Он читает t["brut"|"avan"|"cons"] из стола — последние
    записанные вердикты, БЕЗ ОТМЕТКИ, к какому бару они относятся.
    Молчавший трейдер оставляет там прошлую запись, и она идёт в
    дело как сегодняшняя.

    Сейчас это безобидно — там REJECTED. Но если в старой записи
    лежит APPROVED с ценой входа, Исполнитель поставит ордер по
    вердикту, которого сегодня никто не давал. Это уже деньги.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Правит коды W1 и MN1; при пустом ответе выбирает символ в обзор
   рынка и повторяет запрос — трижды, с короткой паузой.

2. Вердикт получает отметку БАРА. Исполнитель берёт только те, что
   от текущего бара; протухшие отбрасывает и говорит об этом вслух:

       [ИСПОЛНИТЕЛЬ] ⏳ avan: вердикт от прошлого бара — не считаю

   Отметки нет (запись старая, до патча) — тоже не считаем: лучше
   пропустить вход, чем поставить ордер по вчерашнему слову.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_etazhi_i_verdikty.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "SVEZHEST_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "mt5_feed.py").exists()
            and (p / "Биржа" / "hooks.py").exists()
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


# ── 1. коды этажей ──
ST_MAP = '''    "D1": 16408, "W1": 16409, "MN1": 16410,
}'''
NOV_MAP = '''    # SVEZHEST_V1: W1 и MN1 были 16409 и 16410 — таких кодов у MT5
    # нет. Недельный и месячный этажи город не получал НИКОГДА,
    # а по ним считается компас: он был слеп по определению.
    "D1": 16408, "W1": 32769, "MN1": 49153,
}'''

# ── 2. пустой ответ: выбрать символ и повторить ──
ST_FETCH = '''        rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, count)
    finally:
        mt5.shutdown()'''
NOV_FETCH = '''        # SVEZHEST_V1: MT5 отдаёт пусто, пока история этажа не
        # «прокачана» в терминале — особенно на старших. Лечится тем
        # же приёмом, что и везде: выбрать символ в обзор рынка и
        # повторить. Первый заход часто пустой, второй приносит.
        rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, count)
        if rates is None or len(rates) == 0:
            import time as _t
            try:
                mt5.symbol_select(symbol, True)
            except Exception:
                pass
            for _popytka in (1, 2):
                _t.sleep(0.35)
                rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, count)
                if rates is not None and len(rates):
                    print(f"[FEED] {symbol} {tf_name}: пришли со "
                          f"{_popytka + 1}-й попытки "
                          f"(история подкачалась)")
                    break
    finally:
        mt5.shutdown()'''

# ── 3. вердикт с отметкой бара ──
ST_VERDIKT = '''        "brut": t.get("brut", {}),
        "avan": t.get("avan", {}),
        "cons": t.get("cons", {}),'''
NOV_VERDIKT = '''        # SVEZHEST_V1: только СЕГОДНЯШНИЕ вердикты. Молчавший трейдер
        # оставляет в столе прошлую запись, и она шла в дело как
        # свежая: в логе 18.08 Совет A07/A08 не звал, а Исполнитель
        # доложил их вердикты. Там был REJECTED — безобидно; но если
        # бы лежал APPROVED с ценой, он поставил бы ордер по вчерашнему
        # слову. Лучше пропустить вход, чем открыть по протухшему.
        "brut": _svezhiy(t, "brut"),
        "avan": _svezhiy(t, "avan"),
        "cons": _svezhiy(t, "cons"),'''

SVEZHIY = '''

def _tekushchiy_bar(t: dict) -> str:
    """Бар, на котором город стоит сейчас (его пишет рука рынка)."""
    return str((t.get("рынок") or {}).get("бар") or t.get("бар") or "")


def _svezhiy(t: dict, key: str) -> dict:
    """SVEZHEST_V1: вердикт этого бара — или пусто.

    Нет отметки бара (запись старая, до патча) — тоже пусто: чужого
    вчерашнего слова нам не надо.
    """
    v = dict(t.get(key, {}) or {})
    if not v:
        return {}
    bar_seychas = _tekushchiy_bar(t)
    bar_verdikta = str(v.get("бар") or v.get("bar_time") or "")
    if not bar_seychas:
        return v            # город не сказал, какой бар — не судим строго
    if bar_verdikta and bar_verdikta == bar_seychas:
        return v
    print(f"[ИСПОЛНИТЕЛЬ] ⏳ {key}: вердикт "
          f"{'от ' + bar_verdikta if bar_verdikta else 'без отметки бара'} "
          f"— не считаю (сейчас {bar_seychas})")
    return {}

'''

# ── 4. рука рынка отмечает текущий бар ──
ST_RUKA = '''    state = {"chain_data": {"market_data": md}}
    cd = state["chain_data"]'''
NOV_RUKA = '''    # SVEZHEST_V1: отмечаем, на каком баре город стоит сейчас, —
    # по этой отметке Исполнитель отличает свежий вердикт от вчерашнего.
    try:
        _t_bar = load_trading_state()
        _t_bar.setdefault("рынок", {})["бар"] = str(md.get("bar_time") or "")
        save_trading_state(_t_bar)
    except Exception as _eb:
        print(f"[РЫНОК] отметку бара не поставил: {_eb}")

    state = {"chain_data": {"market_data": md}}
    cd = state["chain_data"]'''


def pravit(put: Path, pary: list, imya: str, dopisat: str = "") -> bool:
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"  · {put.name}: маркер уже стоит")
        return True
    beda = [st[:38].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден → «{b}…»")
        return False
    novyy = t
    for st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    if dopisat:
        novyy = novyy.rstrip("\n") + "\n" + dopisat
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
    feed = koren / "Биржа" / "mt5_feed.py"
    hooks = koren / "Биржа" / "hooks.py"
    ispoln = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
              / "слоты" / "исполнитель" / "мозг.py")

    print("\n1. Коды этажей и повтор запроса к терминалу")
    if not pravit(feed, [(ST_MAP, NOV_MAP), (ST_FETCH, NOV_FETCH)], "etazhi"):
        return 1

    print("\n2. Рука рынка отмечает текущий бар")
    if not pravit(hooks, [(ST_RUKA, NOV_RUKA)], "svezhest"):
        return 1

    print("\n3. Исполнитель не берёт протухшие вердикты")
    if not pravit(ispoln, [(ST_VERDIKT, NOV_VERDIKT)], "svezhest", SVEZHIY):
        return 1

    if not SUHO:
        import py_compile
        for f in (feed, hooks, ispoln):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nЧто должно измениться в логе:")
        print("  · «Нет котировок: EURUSD D1» — реже или совсем уйдёт;")
        print("  · W1 и MN1 наконец начнут приходить (компас прозреет);")
        print("  · Исполнитель перестанет докладывать вердикты тех,")
        print("    кого Совет сегодня не звал.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
