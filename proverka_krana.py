# -*- coding: utf-8 -*-
# PROVERKA_KRANA_V1
"""
Смотрелец. Ничего не меняет, не пишет — только показывает правду.

Отвечает на три вопроса разом:
  1. Какой кран РЕАЛЬНО включён в площади (trading_state["feed"]) —
     то, что видит feed_source.bars(), а не то, что светится в кабинете.
  2. Что отдаёт терминал MT5 напрямую (последний бар, дата) — живой ли он.
  3. Что лежит в файле test_data для того же инструмента — на какую
     дату он остановлен.

Запускать из корня репозитория:
    python proverka_krana.py [SYMBOL] [TF]
По умолчанию GBPUSD H4.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"
if str(_BIRZHA) not in sys.path:
    sys.path.insert(0, str(_BIRZHA))


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "GBPUSD"
    tf = sys.argv[2] if len(sys.argv) > 2 else "H4"

    print(f"Проверяю {symbol} {tf}\n")

    print("═══ 1. КАКОЙ КРАН ВКЛЮЧЁН НА ПЛОЩАДИ ═══")
    try:
        import feed_source
        mode_info = feed_source.get_feed_mode()
        print(f"  trading_state['feed'] = {mode_info}")
    except Exception as e:
        print(f"  не прочитал: {e}")

    print("\n═══ 2. ЧТО ОТДАЁТ ТЕРМИНАЛ MT5 НАПРЯМУЮ (в обход крана) ═══")
    try:
        bars_t, point_t = feed_source._bars_from_terminal(symbol, tf, 3)
        if bars_t:
            posl = bars_t[-1]
            print(f"  живой: ДА, последний бар {posl.get('date')}, "
                  f"close={posl.get('close')}, point={point_t}")
        else:
            print("  живой: НЕТ — терминал не дал баров "
                  "(закрыт, не тот символ в обзоре рынка, или недоступен)")
    except Exception as e:
        print(f"  ошибка при обращении к терминалу: {e}")

    print("\n═══ 3. ЧТО ЛЕЖИТ В ФАЙЛЕ test_data ДЛЯ ТОГО ЖЕ ИНСТРУМЕНТА ═══")
    try:
        p = feed_source._find_csv(symbol, tf)
        if p is None:
            print("  файла нет — тестовый кран для этого этажа пуст")
        else:
            bars_f, point_f = feed_source._bars_from_folder(symbol, tf, 3)
            if bars_f:
                posl = bars_f[-1]
                print(f"  файл: {p.name}")
                print(f"  последний бар В ФАЙЛЕ (без курсора истории, "
                      f"хвост): {posl.get('date')}, close={posl.get('close')}")
            else:
                print(f"  файл {p.name} есть, но пуст или курсор истории "
                      f"обрезал всё (см. ниже)")
    except Exception as e:
        print(f"  ошибка при чтении файла: {e}")

    print("\n═══ 4. КУРСОР ИСТОРИИ — НЕ СНЯТ ЛИ ═══")
    try:
        import istoriya
        moment = istoriya.gde_stoim()
        if moment:
            print(f"  ⚠ КУРСОР СТОИТ В ПРОШЛОМ: {moment}")
            print("  Пока он стоит — тестовый кран отдаёт бары ТОЛЬКО")
            print("  до этой даты, даже если в файле есть более свежие.")
        else:
            print("  курсора нет — тестовый кран отдаёт весь хвост файла")
    except Exception as e:
        print(f"  не прочитал курсор: {e}")

    print("\n═══ 5. ЧТО РЕАЛЬНО ПОЛУЧИТ ГОРОД ПРЯМО СЕЙЧАС ═══")
    try:
        bars_now, point_now = feed_source.bars(symbol, tf, 3)
        if bars_now:
            posl = bars_now[-1]
            print(f"  bars({symbol}, {tf}) → последний бар {posl.get('date')}, "
                  f"close={posl.get('close')}")
        else:
            print("  bars() вернул пусто")
    except Exception as e:
        print(f"  ошибка: {e}")


if __name__ == "__main__":
    main()
