# -*- coding: utf-8 -*-
"""
pochinit_pamyat_kompasa.py · MARKER: GLUBINA_KOMPASA_V3

ЗАМЕР ШЕФА (20.08, XAUUSD H1, 1500 баров)
─────────────────────────────────────────
    всего: 83.0 с · на бар 55 мс
    919 раз · 68.0 с всего · XAUUSD H8      ← сюда ушло всё

Из восьмидесяти трёх секунд шестьдесят восемь — походы за барами
СТАРШЕГО этажа. Компас считается на каждом баре, и на каждом баре он
идёт в терминал заново:

    919 × MetaTrader5.initialize      16.9 с
    919 × _fetch                      29.6 с
    1 838 067 × strftime              14.6 с   (2000 баров × 919 раз)

Лесенка тут ни при чём: обращение ровно одно на бар, память ступеней
(V2) работает. Дело в том, что старший этаж вообще не должен спрашиваться
чаще, чем он меняется. H8 меняется раз в восемь часов, а мы дёргали его
девятьсот девятнадцать раз подряд, пока перебирали историю ОДНОГО дня
за другим.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Компас запоминает сами БАРЫ старшего этажа, а не только глубину.

Ключ памяти — инструмент, этаж и МОМЕНТ, на котором стоит курсор
истории. Поэтому в прогоне по истории подмены не будет: сдвинулся
курсор — ключ другой, бары спросятся заново. В живом режиме курсора
нет, там память живёт двадцать секунд — старший этаж за это время
измениться не может при всём желании.

Память маленькая: последние восемь ответов, дальше самые старые
выбрасываются. Живёт в процессе, не на диске.

Ожидаемо: 919 обращений превращаются в единицы, из 83 секунд уходит
около 68.

Ни одного нового числа в расчёте. Меняется только то, как часто мы
задаём тот же самый вопрос.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ pochinit_lesenku_kompasa.py — патч это проверит.
Запуск: py pochinit_pamyat_kompasa.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "GLUBINA_KOMPASA_V3"
NUZHEN = "GLUBINA_KOMPASA_V2"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "global_anchor.py").exists()


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


YAKOR = '''def _sprosit_starshiy(symbol: str, senior: str):
    """Бары старшего этажа. Ступень, которая сработала, запоминаем;
    пустой ответ помним минуту и не переспрашиваем."""
    import time
    from feed_source import bars as source_bars

    klyuch = (symbol, senior)'''

NOV = '''# GLUBINA_KOMPASA_V3 ─────────────────────────────────────────
# Замер Шефа (XAUUSD H1, 1500 баров): 83 с всего, из них 68 — походы
# за барами старшего этажа. 919 обращений к терминалу на 919 баров,
# каждое с MetaTrader5.initialize и переводом двух тысяч дат в строки.
# Старший этаж не должен спрашиваться чаще, чем он меняется: H8 живёт
# восемь часов, а мы дёргали его девятьсот раз подряд.
_BARY_KESH: dict = {}          # (символ, этаж, момент) -> (бары, point, когда)
_KESH_ZHIVYOT = 20.0           # секунд в живом режиме (курсора нет)
_KESH_PREDEL = 8               # больше ответов не храним


def _moment_kursora() -> str:
    """Где стоит курсор истории. В прогоне это пришпиливает память к
    конкретному моменту прошлого — подмены быть не может. В живом
    режиме курсора нет, вернётся пусто."""
    try:
        import istoriya
        return str(istoriya.gde_stoim() or "")
    except Exception:
        return ""


def _sprosit_starshiy(symbol: str, senior: str):
    """Бары старшего этажа. Ступень, которая сработала, запоминаем;
    пустой ответ помним минуту и не переспрашиваем; сами бары держим
    в памяти, пока они не могли измениться."""
    import time
    from feed_source import bars as source_bars

    klyuch = (symbol, senior)

    # ── память о самих барах ──
    kesh_klyuch = (symbol, senior, _moment_kursora())
    est = _BARY_KESH.get(kesh_klyuch)
    if est is not None:
        bary, point, kogda = est
        # момент истории задан — ответ вечен: прошлое не меняется
        if kesh_klyuch[2] or (time.time() - kogda) < _KESH_ZHIVYOT:
            return bary, point

    def _zapomnit(bary, point):
        _BARY_KESH[kesh_klyuch] = (bary, point, time.time())
        while len(_BARY_KESH) > _KESH_PREDEL:
            _BARY_KESH.pop(next(iter(_BARY_KESH)))
        return bary, point'''

YAKOR2 = '''        if sbars:
            _GLUBINA_POMNIM[klyuch] = glubina
            _PUSTO_POMNIM.pop(klyuch, None)
            return sbars, point

    _PUSTO_POMNIM[klyuch] = time.time()
    return [], None'''

NOV2 = '''        if sbars:
            _GLUBINA_POMNIM[klyuch] = glubina
            _PUSTO_POMNIM.pop(klyuch, None)
            return _zapomnit(sbars, point)   # GLUBINA_KOMPASA_V3

    _PUSTO_POMNIM[klyuch] = time.time()
    return _zapomnit([], None)               # GLUBINA_KOMPASA_V3'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "global_anchor.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати pochinit_lesenku_kompasa.py — этот патч")
        print("  надстраивает его память, а не пишет её заново.")
        return 1
    for yakor in (YAKOR, YAKOR2):
        if t.count(yakor) != 1:
            print(f"✗ якорь найден {t.count(yakor)} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return 1

    novyy = t.replace(YAKOR, NOV, 1).replace(YAKOR2, NOV2, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_pamyat_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ компас помнит бары старшего этажа (копия: {bak.name})")
    print("\nПроверь тем же замером, один в один:")
    print("  py zamerit_iskatelya.py --symbol XAUUSD --tf H1 --barov 1500")
    print("\nСтрока «919 раз · 68.0 с · XAUUSD H8» должна превратиться")
    print("в единицы обращений, а общее время упасть примерно до 15 с.")
    print("Если не упало — покажи новый замер, дальше пойдём по нему.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
