# -*- coding: utf-8 -*-
"""
postavit_tolko_zakrytye.py · MARKER: TOLKO_ZAKRYTYE_V1

ЧТО НАЙДЕНО (Шеф поймал глазом 20.08)
─────────────────────────────────────
На столе стоял «РАЗВОРОТНЫЙ БАР: BEAR @ 1.16828» на баре 20.08 04:00.
По определению всё верно: бар обновил максимум и закрылся в нижней
половине — это разворотник по КАНОН_ВХОДА §2.4.

Только бар был НЕ ЗАКРЫТ. Три запуска подряд, один и тот же бар:

    C=1.16739  →  C=1.16754  →  C=1.1675

H4-свеча, открывшаяся в 04:00, живёт до 08:00. Её закрытие ходит
туда-сюда четыре часа, и вместе с ним разворотник то появляется, то
пропадает. К восьми утра бара, по которому принято решение, может не
остаться вовсе.

MetaTrader отдаёт с нулевой позиции ИДУЩУЮ свечу — так он устроен.
Значит в живом режиме последний бар всегда формирующийся.

В прогоне по истории мы это давно запретили: курсор (`istoriya.py`)
отдаёт только закрытые бары, иначе город видел бы будущее и врал в
свою пользу. В реале запрета не было — перекос, из-за которого точка
могла родиться на бумажном баре и разбудить трейдера зря.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Одна рука `_tolko_zakrytye(bars)` в `Биржа/hooks.py`: в режиме РЕАЛ
отбрасывает последний бар, в ТЕСТЕРЕ не трогает ничего (там курсор уже
отвечает за честность). Ставится в трёх местах, где город берёт бары
для РЕШЕНИЯ:

    hooks.rynok_novyy_bar  — рождение точки, заявки, закрытие позиций
    stol.nakryt            — приборы, по которым судит трейдер
    grafik.narisovat       — кадр, который трейдер видит глазом

Кадр правим тоже нарочно: иначе Шеф и трейдер смотрят разные картинки,
а на столе стоит третья правда. Живую свечу смотри в терминале — он
для этого и открыт.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_tolko_zakrytye.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TOLKO_ZAKRYTYE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "stol.py").exists()
            and (p / "Биржа" / "grafik.py").exists())


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


# ── hooks.py: сама рука + её место в руке рынка ──────────────

H_YAKOR_FN = "def rynok_novyy_bar(symbol: str, timeframe: str,"

H_RUKA = '''# ═══════════════════════════════════════════════════════════
# TOLKO_ZAKRYTYE_V1 — решаем по ЗАКРЫТЫМ барам, не по идущей свече
# ═══════════════════════════════════════════════════════════
# MetaTrader отдаёт с нулевой позиции формирующуюся свечу. Пока она
# живёт (у H4 — четыре часа), её закрытие ходит туда-сюда, а вместе с
# ним появляется и пропадает разворотный бар. Шеф поймал это глазом
# 20.08: три запуска подряд по одному бару дали C=1.16739, 1.16754,
# 1.1675 — и «РАЗВОРОТНЫЙ БАР: BEAR», которого к закрытию могло не
# остаться.
#
# В прогоне по истории это запрещено с самого начала: курсор отдаёт
# только закрытые бары, иначе город видел бы будущее. Здесь тот же
# закон для реала.

def _tolko_zakrytye(bars: list) -> list:
    """В РЕАЛЕ отбросить последний, ещё идущий бар. В ТЕСТЕРЕ не
    трогать: там за честность отвечает курсор истории."""
    try:
        from feed_source import get_feed_mode
        if (get_feed_mode() or {}).get("mode") != "real":
            return bars
    except Exception:
        return bars
    if bars and len(bars) > 1:
        return bars[:-1]
    return bars


'''

H_YAKOR_BARY = '''            bars, _p = _src_bars(symbol, timeframe, 300)'''

H_NOV_BARY = '''            bars, _p = _src_bars(symbol, timeframe, 300)
            bars = _tolko_zakrytye(bars)   # TOLKO_ZAKRYTYE_V1'''

H_YAKOR_OKNO = '''    if point is not None:
        _p = point
    if not bars:
        itog["причина"] = "нет баров"
        return itog'''

H_NOV_OKNO = '''    if point is not None:
        _p = point
    if window:
        # TOLKO_ZAKRYTYE_V1: окно пришло снаружи (кабинет/прогон) — в
        # реале в нём тоже сидит идущая свеча, режем и её.
        bars = _tolko_zakrytye(bars)
    if not bars:
        itog["причина"] = "нет баров"
        return itog'''

# ── stol.py ──────────────────────────────────────────────────

S_YAKOR = '''                bars, point = source_bars(symbol, timeframe, count=400)'''

S_NOV = '''                bars, point = source_bars(symbol, timeframe, count=400)
                # TOLKO_ZAKRYTYE_V1: приборы считаем по закрытым барам —
                # идущая свеча пляшет и вместе с ней пляшет разворотник.
                try:
                    from hooks import _tolko_zakrytye
                    bars = _tolko_zakrytye(bars)
                except Exception:
                    pass'''

# ── grafik.py ────────────────────────────────────────────────

G_YAKOR = '''    bs, point = source_bars(symbol, timeframe, count=max(400, barov + 60))'''

G_NOV = '''    bs, point = source_bars(symbol, timeframe, count=max(400, barov + 60))
    # TOLKO_ZAKRYTYE_V1: кадр рисуем по тем же барам, по которым считан
    # стол. Иначе Шеф и трейдер смотрят разные картинки, а на столе
    # стоит третья правда. Живая свеча — в терминале.
    try:
        from hooks import _tolko_zakrytye
        bs = _tolko_zakrytye(bs)
    except Exception:
        pass'''


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
    bak = f.with_suffix(f".py.bak_zakrytye_{datetime.now():%Y%m%d_%H%M%S}")
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

    if not _pravit(koren / "Биржа" / "hooks.py",
                   [(H_YAKOR_FN, H_RUKA + H_YAKOR_FN),
                    (H_YAKOR_BARY, H_NOV_BARY),
                    (H_YAKOR_OKNO, H_NOV_OKNO)], "hooks.py"):
        return 1
    if not _pravit(koren / "Биржа" / "stol.py", [(S_YAKOR, S_NOV)], "stol.py"):
        print("\n⚠️  hooks.py поправлен, stol.py нет — верни hooks.py из")
        print("   свежей .bak_zakrytye_* и позови меня.")
        return 1
    if not _pravit(koren / "Биржа" / "grafik.py", [(G_YAKOR, G_NOV)],
                   "grafik.py"):
        print("\n⚠️  hooks.py и stol.py поправлены, grafik.py нет — верни их")
        print("   из свежих .bak_zakrytye_* и позови меня.")
        return 1

    if SUHO:
        return 0
    print("\nПроверить сразу, без модели и без денег:")
    print("  py stol_pokazat.py EURUSD H4")
    print("\nПоследний бар должен стать ПРЕДЫДУЩИМ (для H4 — на четыре")
    print("часа раньше), и два запуска подряд обязаны дать ОДНО И ТО ЖЕ.")
    print("Если цифры пляшут — значит идущая свеча всё ещё пролезает,")
    print("покажи мне вывод.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
