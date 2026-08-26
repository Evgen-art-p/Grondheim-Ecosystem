# -*- coding: utf-8 -*-
"""
postavit_krayniye_tochki.py · MARKER: KRAYNIYE_TOCHKI_V1

СЛОВА ШЕФА
──────────
    «Последние фракталы не пойдёт, это очень шумный индикатор, они
    всюду.»
    «А на взгляде ей просто — это экстремумы самые, там точно волна.»
    «Смотрит ещё пускай глазами.»

ЧТО ИЗ ЭТОГО СЛЕДУЕТ
────────────────────
Опора не разметка волн и не фракталы, а ВЕРШИНА и ДНО — то, что глаз
ловит мгновенно и без порогов. Между ними волна, спорить не о чем.

Но одними глазами она границы не назовёт: на кадре подписи мелкие, и
дату она переврёт. Поэтому код даёт ТОЧНЫЕ координаты крайних точек —
дату и цену, — а какая из них начало её волны, решает она, глядя на
картинку. Числа под глазом, а не вместо него.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Рука `krayniye_tochki(этаж, баров)` — голые факты:
   · вершина и дно всего окна: когда и почём;
   · то же по первой и второй половине окна — чтобы было видно, с
     какой стороны что лежит;
   · сколько баров между вершиной и дном.
   Ни слова о том, волна это или нет, и какая.

2. ПОТОЛОК ОБРАЩЕНИЙ поднят с 3-4 до 12. Матрёшка Шефа — посмотреть
   зигзаг целиком, потом волну C внутри него, потом её третью — это
   три-четыре растяжки подряд, и каждая с картинкой. На старом
   потолке она упиралась на середине и отвечала недосмотрев.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не размечает волны, не ищет зигзаг, не называет A, B, C. Экстремум —
это факт; имя волне даёт трейдер, посмотрев.

ПРО ЦЕНУ, ЧЕСТНО
────────────────
Такой проход дороже прежнего: было одно обращение и один кадр на
место, станет три-четыре картинки. Это плата за то, чтобы трейдер
смотрел, а не сверялся с инструкцией.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_krayniye_tochki.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KRAYNIYE_TOCHKI_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ruki_treydera.py").exists()
            and (p / "Биржа" / "llm.py").exists())


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


ST_SHEMA = '''        {"type": "function", "function": {
            "name": "pokazat_etazh",'''

NOV_SHEMA = '''        # KRAYNIYE_TOCHKI_V1: опора для растяжки. Не разметка волн и
        # не фракталы (те всюду и шумят) — вершина и дно, то, что глаз
        # ловит сразу. Числа нужны, чтобы назвать границы точно: на
        # кадре подписи мелкие, дату по картинке не прочесть.
        {"type": "function", "function": {
            "name": "krayniye_tochki",
            "description": (
                "Вершина и дно на куске: когда и почём. Отдельно по первой "
                "и второй половине куска. Голые числа — какая из этих точек "
                "начало твоей волны, решаешь ты, глядя на картинку. Нужны, "
                "чтобы назвать границы для rastyanut_volnu без промаха."),
            "parameters": {"type": "object", "properties": {
                "этаж": {"type": "string",
                         "description": "пусто — твой рабочий"},
                "баров": {"type": "integer",
                          "description": "сколько баров назад смотреть, "
                                         "по умолчанию 140"}},
                "required": []}}},
        {"type": "function", "function": {
            "name": "pokazat_etazh",'''

ST_RUKI = '''    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,'''

NOV_RUKI = '''    def _krayniye(args: dict) -> str:
        """KRAYNIYE_TOCHKI_V1: вершина и дно. Факты, не разметка."""
        tf = str(args.get("этаж", "")).strip().upper()
        try:
            import masshtab
            if not masshtab.est(tf):
                tf = rabochiy_etazh if masshtab.est(rabochiy_etazh) else "H4"
            n = int(args.get("баров") or 140)
            from feed_source import bars as _bars
            b, _p = _bars(symbol, tf, max(n, 60))
        except Exception as e:
            return f"крайние точки не посчитались: {e}"
        if not b:
            return f"котировок {symbol} {tf} не дали"
        b = b[-n:]

        def _kray(kusok, imya):
            if not kusok:
                return f"{imya}: пусто"
            v = max(kusok, key=lambda x: x["high"])
            d = min(kusok, key=lambda x: x["low"])
            return (f"{imya}: вершина {v['high']} ({v.get('date')}) · "
                    f"дно {d['low']} ({d.get('date')})")

        pol = len(b) // 2
        v = max(b, key=lambda x: x["high"])
        d = min(b, key=lambda x: x["low"])
        mezhdu = abs(b.index(v) - b.index(d))
        return ("=== КРАЙНИЕ ТОЧКИ · факты, не разметка ===\\n"
                f"{symbol} {tf}, {len(b)} баров "
                f"({b[0].get('date')} → {b[-1].get('date')})\\n"
                + _kray(b, "всё окно") + "\\n"
                + f"между вершиной и дном: {mezhdu} баров\\n"
                + _kray(b[:pol], "первая половина") + "\\n"
                + _kray(b[pol:], "вторая половина"))

    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,
            "krayniye_tochki": _krayniye,      # KRAYNIYE_TOCHKI_V1'''

ST_PODPIS = '''def ruki(symbol: str, ceh: str, slot: str, self_key: str,
         dnevnik_fn=None) -> dict:'''
NOV_PODPIS = '''def ruki(symbol: str, ceh: str, slot: str, self_key: str,
         dnevnik_fn=None, rabochiy_etazh: str = "H4") -> dict:'''

# ── потолок обращений ──
ST_POTOLOK = '''    max_tool_rounds: int = 3,'''
NOV_POTOLOK = '''    # KRAYNIYE_TOCHKI_V1: было 3 — на матрёшку Шефа (зигзаг целиком →
    # волна C внутри него → её третья волна) этого не хватает: три-
    # четыре растяжки подряд, каждая с картинкой. На старом потолке
    # трейдер упирался на середине и отвечал недосмотрев.
    max_tool_rounds: int = 12,'''

ST_POTOLOK2 = '''    max_tool_rounds: int = 4,'''
NOV_POTOLOK2 = '''    max_tool_rounds: int = 12,      # KRAYNIYE_TOCHKI_V1'''


def pravit(put: Path, pary: list, imya: str) -> bool:
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"  · {put.name}: маркер уже стоит")
        return True
    beda = [st[:40].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден → «{b}…»")
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
    ruki = koren / "Биржа" / "ruki_treydera.py"
    llm = koren / "Биржа" / "llm.py"

    print("\n1. Рука крайних точек")
    if not pravit(ruki, [(ST_PODPIS, NOV_PODPIS), (ST_SHEMA, NOV_SHEMA),
                         (ST_RUKI, NOV_RUKI)], "kray"):
        return 1

    print("\n2. Мозги передают рукам рабочий этаж")
    # Без этого рука крайних точек угадывает этаж, а он у каждого свой.
    st = """                    executors=_rt.ruki(symbol, ceh, slot, self_key,
                                       dnevnik_fn=_read_recent_diary),"""
    nov = """                    executors=_rt.ruki(symbol, ceh, slot, self_key,
                                       dnevnik_fn=_read_recent_diary,
                                       rabochiy_etazh=timeframe),"""
    for _slot in ("A06", "A07", "A08"):
        _m = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
              / "слоты" / _slot / "мозг.py")
        if not _m.exists():
            continue
        _t = _m.read_text(encoding="utf-8")
        if MARKER in _t:
            print(f"  · {_slot}: уже")
            continue
        if _t.count(st) != 1:
            print(f"  ⚠ {_slot}: вызов рук выглядит иначе — пропускаю")
            continue
        if SUHO:
            print(f"  · {_slot}: правка готова (сухой прогон)")
            continue
        shutil.copy2(_m, _m.with_suffix(
            f".py.bak_kray_{datetime.now():%Y%m%d_%H%M%S}"))
        _m.write_text(_t.replace(st, nov, 1) + f"\n# {MARKER} - marker\n",
                      encoding="utf-8")
        print(f"  ✓ {_slot}")

    print("\n3. Потолок обращений — 12 вместо 3-4")
    t = llm.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        pary = []
        if t.count(ST_POTOLOK) == 1:
            pary.append((ST_POTOLOK, NOV_POTOLOK))
        if t.count(ST_POTOLOK2) == 1:
            pary.append((ST_POTOLOK2, NOV_POTOLOK2))
        if not pary:
            print("  ✗ не нашёл, где стоит потолок")
            return 1
        if not pravit(llm, pary, "kray"):
            return 1

    if not SUHO:
        import py_compile
        for f in (ruki, llm):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь она может так:")
        print("  крайние точки → «растяни от дна 12.04 до вершины 05.05»")
        print("  → смотрит → «а теперь от вершины до сейчас» → смотрит")
        print("  → и только потом судит.")
        print("\nЭкстремум — факт. Какая это волна, называет она сама.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
