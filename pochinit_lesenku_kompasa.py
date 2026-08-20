# -*- coding: utf-8 -*-
"""
pochinit_lesenku_kompasa.py · MARKER: GLUBINA_KOMPASA_V2

МОЯ ЖЕ ОШИБКА, ПОЙМАНА ШЕФОМ НА СКОРОСТИ
────────────────────────────────────────
Утренний патч GLUBINA_KOMPASA_V1 научил компас просить посильную
глубину лесенкой: 2000 → 500 → 200, первый непустой ответ. На живом
терминале это вылечило пропавшие дневки.

Но когда старшего этажа НЕТ вообще (в тестере нет файла дневок; в
терминале не прокачана история) — пусто приходит на всех трёх
ступенях. Значит вместо одного обращения к источнику стало ТРИ. А
компас считается на КАЖДОМ баре, внутри build_market_data.

Замерено: при пустом старшем этаже 20 баров вместо 1.0 с идут 3.0 с,
обращений к источнику 60 вместо 20. В реале ещё хуже: насос на пустой
ответ сам делает две повторные попытки со сном по 0.35 с — то есть
каждая лишняя ступень стоит около секунды.

Отсюда и «искатель ооочень медленно перебирает бары»: раньше история
пролетала, теперь ползёт. Виноват не искатель — виновата моя лесенка.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Компас запоминает ответ по паре «инструмент + старший этаж»:

    ступень сработала → в следующий раз идём сразу с неё, без перебора
    пусто на всех     → помним это минуту и не долбимся в пустое

Память живёт в процессе, не на диске: поднял город заново — спросит
заново. Минута выбрана так, чтобы прогон по истории не тратил на
несуществующий этаж ничего, а живой город успел заметить, что история
в терминале прокачалась.

Ни одной новой ступени, ни одного нового порога расчёта. Только память
о том, что уже спрашивали.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ pochinit_glubinu_kompasa.py — патч это проверит.
Запуск: py pochinit_lesenku_kompasa.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "GLUBINA_KOMPASA_V2"
NUZHEN = "GLUBINA_KOMPASA_V1"
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


YAKOR = '''    sbars, point = [], None
    for _glubina in (2000, 500, 200):
        sbars, point = source_bars(symbol, senior, count=_glubina)
        if sbars:
            break'''

NOV = '''    # GLUBINA_KOMPASA_V2: лесенку помним, в пустое не долбимся.
    # V1 перебирала три ступени КАЖДЫЙ раз, а компас считается на
    # каждом баре. Пустой старший этаж стоил трёх обращений вместо
    # одного (в реале — с двумя повторами и снами внутри насоса), и
    # прогон по истории из быстрого стал ползучим.
    sbars, point = _sprosit_starshiy(symbol, senior)'''

RUKA = '''# GLUBINA_KOMPASA_V2 ─────────────────────────────────────────
# Память о том, что уже спрашивали. В процессе, не на диске: поднял
# город заново — спросит заново.
_LESENKA = (2000, 500, 200)
_GLUBINA_POMNIM: dict = {}     # (символ, этаж) -> ступень, которая дала бары
_PUSTO_POMNIM: dict = {}       # (символ, этаж) -> когда получили пусто
_PUSTO_ZHIVYOT = 60.0          # секунд молчать, не переспрашивая


def _sprosit_starshiy(symbol: str, senior: str):
    """Бары старшего этажа. Ступень, которая сработала, запоминаем;
    пустой ответ помним минуту и не переспрашиваем."""
    import time
    from feed_source import bars as source_bars

    klyuch = (symbol, senior)
    kogda = _PUSTO_POMNIM.get(klyuch)
    if kogda and (time.time() - kogda) < _PUSTO_ZHIVYOT:
        return [], None

    poryadok = list(_LESENKA)
    znaem = _GLUBINA_POMNIM.get(klyuch)
    if znaem in poryadok:
        poryadok.remove(znaem)
        poryadok.insert(0, znaem)

    for glubina in poryadok:
        sbars, point = source_bars(symbol, senior, count=glubina)
        if sbars:
            _GLUBINA_POMNIM[klyuch] = glubina
            _PUSTO_POMNIM.pop(klyuch, None)
            return sbars, point

    _PUSTO_POMNIM[klyuch] = time.time()
    return [], None


'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "global_anchor.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати pochinit_glubinu_kompasa.py — этот патч")
        print("  чинит его лесенку, а не пишет её с нуля.")
        return 1
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
        return 1

    # рука встаёт перед той функцией, где её зовут
    tochka = t.find("def global_trend(")
    if tochka < 0:
        print("✗ не нашёл global_trend — останавливаюсь")
        return 1
    novyy = t[:tochka] + RUKA + t[tochka:]
    novyy = novyy.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_lesenka_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ компас помнит лесенку (копия: {bak.name})")
    print("\nПрогон по истории должен снова полететь, как до утра.")
    print("Если старший этаж есть — компас спросит его одним обращением;")
    print("если его нет — спросит один раз и минуту не будет трогать.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
