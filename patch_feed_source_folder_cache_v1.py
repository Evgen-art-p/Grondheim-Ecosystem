# -*- coding: utf-8 -*-
"""
patch_feed_source_folder_cache_v1.py
────────────────────────────────────────────────────────────────────
ЧИНИТ: тестер на H1 (и любом младшем ТФ) висит десятки минут и не
находит НИ ОДНОГО срабатывания, хотя визуально волны на графике есть.
В консоли VS Code при этом бесконечно скроллится одна и та же пара
строк:
    [CORE] 📁 XAUUSDH8.csv: 12470 баров (...)
    [CORE]    _Point=0.01 (XAUUSD)
без единой строки "Сито 1 готово" — сито-1 физически не успевает
закончить сканирование истории.

КОРЕНЬ — НЕ архитектура, НЕ пороги, НЕ дрейф путей. Чистая производи-
тельность:

  williams_core.build_market_data() на КАЖДЫЙ вызов лезет за честным
  глобальным трендом (§12 Котина, ENGINE_ONE_DOOR_V1):
      from global_anchor import global_trend as _gt
      _r = _gt(symbol, timeframe, as_of_date=_bar_time)

  global_trend() считает старший этаж (рабочий ×5 по лесенке Шефа —
  для H1 это H8) и берёт его бары через:
      from feed_source import bars as source_bars
      sbars, point = source_bars(symbol, senior, count=100000)

  А feed_source._bars_from_folder() (тестовый кран) читает CSV
  СТАРШЕГО этажа С ДИСКА ЗАНОВО, без кэша, НА КАЖДЫЙ ВЫЗОВ:
      bars = read_mt5_csv(str(p))   # полный разбор файла, каждый раз

  Сито-1 (математика ядра, без LLM) гоняет build_market_data на
  КАЖДОМ баре истории — для XAUUSD H1 это 94 566 вызовов. Итог:
  94 566 полных чтений+разборов файла XAUUSDH8.csv (12 470 строк)
  с диска. На H4 (24 806 баров) это тоже происходит, но в ~4 раза
  реже — потому симптом ярче всего именно на младших ТФ и незаметен
  на H4, где сессии выше уже проходили нормально.

  Логика якоря (§12 Котина, старший этаж ×5) верна и её трогать не
  нужно — чинится только производительность источника.

ЛЕЧЕНИЕ: кэш полного разобранного файла в feed_source._bars_from_folder
по абсолютному пути. Исторические CSV статичны в рамках одного запуска
процесса — файл читается с диска один раз, дальше только хвост
(bars[-count:]) режется из уже разобранного списка в памяти. Кран
РЕАЛ (терминал MT5, _bars_from_terminal) патч не трогает вообще —
живой рынок как был, так и остался без кэша (ему это не нужно и не
должно быть нужно — там всегда свежие бары).

Идемпотентно. Маркер FEED_SOURCE_FOLDER_CACHE_V1. Бэкап рядом (.bak).
Запуск из КОРНЯ репы (Windows/PowerShell):
    python patch_feed_source_folder_cache_v1.py
"""
from __future__ import annotations
import sys
from pathlib import Path

MARKER = "FEED_SOURCE_FOLDER_CACHE_V1"
TARGET = Path("Биржа") / "feed_source.py"

OLD = (
    'def _bars_from_folder(symbol: str, tf: str, count: int) -> Tuple[list, Optional[float]]:\n'
    '    """\n'
    '    КРАН ТЕСТ: папка test_data. Читает CSV нужного этажа, отдаёт\n'
    '    последние count баров + point из таблички (терминала-то нет).\n'
    '    MT5 НЕ трогаем — вот вся суть герметичности.\n'
    '    """\n'
    '    from williams_core import read_mt5_csv\n'
    '    p = _find_csv(symbol, tf)\n'
    '    if p is None:\n'
    '        return [], None\n'
    '    bars = read_mt5_csv(str(p))\n'
    '    if not bars:\n'
    '        return [], None\n'
    '    point = _test_point(symbol)\n'
    '    tail = bars[-count:] if count and len(bars) > count else bars\n'
    '    return tail, point\n'
)

NEW = (
    '# ' + MARKER + ': кэш полного разбора CSV по абсолютному пути.\n'
    '# Исторические файлы статичны в рамках одного прогона процесса —\n'
    '# читаем с диска ОДИН РАЗ, дальше режем хвост из памяти. Без этого\n'
    '# build_market_data (через global_anchor.global_trend, §12 Котина)\n'
    '# на КАЖДЫЙ бар сита-1 заново читал и парсил старший этаж целиком —\n'
    '# на H1 (94 566 баров) это превращало прогон в час+ без единого\n'
    '# срабатывания (сито-1 не успевало закончить сканирование истории).\n'
    '_FOLDER_BARS_CACHE: dict = {}\n'
    '\n'
    '\n'
    'def _bars_from_folder(symbol: str, tf: str, count: int) -> Tuple[list, Optional[float]]:\n'
    '    """\n'
    '    КРАН ТЕСТ: папка test_data. Читает CSV нужного этажа, отдаёт\n'
    '    последние count баров + point из таблички (терминала-то нет).\n'
    '    MT5 НЕ трогаем — вот вся суть герметичности.\n'
    '\n'
    '    ' + MARKER + ': полный разбор файла кэшируется по абсолютному\n'
    '    пути — читаем с диска один раз за весь прогон, а не на каждый\n'
    '    вызов (см. докстроку патча). Хвост (count) режется из кэша.\n'
    '    """\n'
    '    from williams_core import read_mt5_csv\n'
    '    p = _find_csv(symbol, tf)\n'
    '    if p is None:\n'
    '        return [], None\n'
    '    key = str(p.resolve())\n'
    '    bars = _FOLDER_BARS_CACHE.get(key)\n'
    '    if bars is None:\n'
    '        bars = read_mt5_csv(str(p))\n'
    '        _FOLDER_BARS_CACHE[key] = bars or []\n'
    '    if not bars:\n'
    '        return [], None\n'
    '    point = _test_point(symbol)\n'
    '    tail = bars[-count:] if count and len(bars) > count else bars\n'
    '    return tail, point\n'
)


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти из КОРНЯ репы "
              f"(там, где папка «Биржа»).")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if OLD not in src:
        print("✗ не нашёл ожидаемое тело _bars_from_folder в "
              "Биржа/feed_source.py.")
        print("  Возможно, файл уже правился вручную. Проверь, что "
              "_bars_from_folder кэширует read_mt5_csv по пути файла, "
              "а не читает диск на каждый вызов.")
        return 2

    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")
    else:
        print(f"• бэкап уже был: {bak} (не перезаписываю)")

    TARGET.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"✓ {TARGET}: _bars_from_folder теперь кэширует разбор CSV "
          f"по пути файла.")
    print("  Тестер на любом ТФ (особенно H1/M30/M15) больше не будет "
          "перечитывать старший этаж с диска на каждый бар сита-1.")
    print(f"  Маркер идемпотентности: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
