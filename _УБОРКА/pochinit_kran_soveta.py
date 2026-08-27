# -*- coding: utf-8 -*-
# MARKER: SOVET_CHEREZ_KRAN_V1
"""
СОВЕТ ПЕРЕСТАЁТ ДЁРГАТЬ ЖИВОЙ ТЕРМИНАЛ.

ЧТО БЫЛО СЛОМАНО
────────────────
Закон города (feed_source.py): «есть кнопки режимов, одна включает
один источник, другая — другой, но читает один движок». В тестерном
режиме MT5 не должен подниматься вообще — кран закрыт.

Но в council.py дешёвая проверка точки шла в терминал НАПРЯМУЮ, мимо
крана:

    if bars is None:
        from mt5_feed import pull_bars
        bars, _point = pull_bars(symbol, timeframe, 300)

Про кран этот кусок не знает. А pull_bars внутри себя (mt5_feed._fetch)
на КАЖДОМ обращении делает mt5.initialize() и следом mt5.shutdown() —
поднимает терминал и тут же гасит.

На сплошном прогоне это сотни циклов «включить-выключить» живого MT5
подряд. Отсюда потеря связи и ругань терминала во время прогона по
истории, где живой рынок вообще не нужен.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Тот же вопрос идёт через КРАН — feed_source.bars(). Кран сам смотрит,
какой режим включён кнопкой:
    тестер → читает CSV из папки, MT5 не трогает ВООБЩЕ
    реал   → идёт в терминал, как и раньше

Поведение в реале не меняется: тот же источник, те же бары.
Если крана почему-то нет (старая сборка) — падаем на прежний путь
через mt5_feed, чтобы ничего не сломать.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не трогает кабинет и его ленту — пустая страница после обновления
браузера лечится отдельно, это другая поломка (состояние кабинета
живёт при вкладке, а не при городе).

Идемпотентен. .bak рядом. Путь ищет сам.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "SOVET_CHEREZ_KRAN_V1"


def _nayti_birzhu() -> Path:
    primety = ("council.py", "feed_source.py")
    nashli = []
    korni = []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        mesta = [koren]
        try:
            mesta += [x for x in koren.iterdir() if x.is_dir()]
        except OSError:
            pass
        for p in mesta:
            if all((p / f).exists() for f in primety) and p not in nashli:
                nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл папку Биржа рядом со скриптом.")
        s = input("Перетащи сюда папку Биржа и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "council.py").exists():
            return p
        raise SystemExit("не та папка — там нет council.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


YAKOR = '''    bars = window
    _point = point
    if bars is None:
        from mt5_feed import pull_bars
        bars, _point = pull_bars(symbol, timeframe, 300)
'''

NOVOE = '''    bars = window
    _point = point
    if bars is None:
        # SOVET_CHEREZ_KRAN_V1: спрашиваем бары у КРАНА, а не у
        # терминала напрямую. Кран сам знает, какой режим включён
        # кнопкой: тестер — читает CSV и MT5 не трогает вообще,
        # реал — идёт в терминал, как и раньше.
        #
        # Прежде здесь стоял прямой вызов mt5_feed.pull_bars, который
        # про кран не знает. А он внутри на КАЖДОМ обращении делает
        # mt5.initialize() и следом mt5.shutdown() — поднимает живой
        # терминал и тут же гасит. На сплошном прогоне это сотни
        # циклов «включить-выключить» подряд: терминал терял связь и
        # ругался, хотя история читается из файлов и живой рынок там
        # не нужен вовсе.
        try:
            from feed_source import bars as _kran
            bars, _point = _kran(symbol, timeframe, 300)
        except Exception as _e_kran:
            print(f"[СОВЕТ] кран недоступен ({_e_kran}) — иду прежним путём")
            from mt5_feed import pull_bars
            bars, _point = pull_bars(symbol, timeframe, 300)
'''


def main():
    b = _nayti_birzhu()
    print(f"\nБиржа: {b}\n")
    p = b / "council.py"
    text = p.read_text(encoding="utf-8")

    if MARKER in text:
        print("  . council.py: уже накачен, пропускаю")
    else:
        if text.count(YAKOR) != 1:
            raise SystemExit(
                f"  X council.py: якорь не найден или не один "
                f"({text.count(YAKOR)}). Файл НЕ ТРОНУТ.")
        novyy = text.replace(YAKOR, NOVOE)
        novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
        ast.parse(novyy)
        shutil.copy2(p, p.with_suffix(".py.bak"))
        p.write_text(novyy, encoding="utf-8")
        print("  + council.py: Совет ходит через кран (.bak рядом)")

    print("\nГотово. Теперь в режиме ТЕСТЕР живой MT5 не поднимается.")
    print("Если он всё равно ругается во время прогона — скажи, ищу дальше.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
