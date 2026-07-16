# -*- coding: utf-8 -*-
"""
proverit_atlas.py — ИНСПЕКТОР, не патч. Ничего не меняет и не пишет.

Показывает честную картину atlas_trading.jsonl и trading_pnl.jsonl:
  • всего строк / сколько битых (не JSON);
  • сколько УНИКАЛЬНЫХ сделок по ключу (symbol, timeframe, trader,
    opened_at) — если одна и та же историческая сделка встречается
    несколько раз, это и есть след повторных прогонов;
  • для дублей — показывает, отличается ли pnl_r между копиями
    (разные R на одном и том же баре = между прогонами менялся код
     расчёта риска, а не просто повтор);
  • разброс дат opened_at — одним взглядом видно, гонялся ли один и
    тот же исторический период много раз подряд.

Запуск из корня Grondheim-Ecosystem:
    python proverit_atlas.py
"""
import io
import json
import sys
from collections import defaultdict
from pathlib import Path


def find(name):
    for base in (Path("Биржа") / "данные", Path("GRONDHEIM_CITY") / "Биржа" / "данные"):
        p = base / name
        if p.exists():
            return p
    return None


def proверить(path, label):
    print(f"\n{'='*60}")
    print(f"  {label}: {path}")
    print('='*60)

    total = 0
    bad = 0
    by_key = defaultdict(list)  # (symbol, timeframe, trader, opened_at) -> [record,...]
    dates = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue

            sym = rec.get("symbol")
            tf = rec.get("timeframe")
            trader = rec.get("trader")
            opened = rec.get("opened_at")
            if opened:
                dates.append(str(opened))

            # берём только записи с исходом (закрытые сделки) — их и
            # дублирует повторный прогон
            if rec.get("pnl_r") is not None or rec.get("pnl") is not None:
                key = (sym, tf, trader, opened)
                by_key[key].append(rec)

    print(f"всего строк: {total}   битых (не JSON): {bad}")

    dup_keys = {k: v for k, v in by_key.items() if len(v) > 1}
    unique_trades = len(by_key)
    total_closed = sum(len(v) for v in by_key.values())

    print(f"закрытых записей всего: {total_closed}")
    print(f"уникальных сделок (symbol+tf+trader+opened_at): {unique_trades}")
    print(f"из них ДУБЛИРОВАННЫХ (одна и та же сделка встречается ≥2 раз): "
          f"{len(dup_keys)}")

    if dup_keys:
        print("\n  --- примеры дублей (первые 5) ---")
        for i, (key, recs) in enumerate(dup_keys.items()):
            if i >= 5:
                print(f"  ... и ещё {len(dup_keys)-5} таких")
                break
            r_values = [r.get("pnl_r") for r in recs]
            distinct_r = len(set(r_values))
            flag = "⚠️  РАЗНЫЕ R!" if distinct_r > 1 else "(R совпадает — чистый повтор)"
            print(f"  {key}: встречена {len(recs)}× · pnl_r={r_values} {flag}")

    if dates:
        dates_sorted = sorted(set(dates))
        print(f"\nразброс дат opened_at: {dates_sorted[0]} … {dates_sorted[-1]}")
        print(f"уникальных дат открытия: {len(set(dates))}")

    return unique_trades, len(dup_keys)


def main():
    atlas = find("atlas_trading.jsonl")
    pnl = find("trading_pnl.jsonl")

    if not atlas and not pnl:
        print("[ИНСПЕКТОР] ✗ не найдены ни atlas_trading.jsonl, ни "
              "trading_pnl.jsonl — запусти из корня проекта")
        sys.exit(1)

    if pnl:
        proверить(pnl, "trading_pnl.jsonl (полная лента закрытий)")
    if atlas:
        proверить(atlas, "atlas_trading.jsonl (память Архивариуса)")

    print(f"\n{'='*60}")
    print("  ВЫВОД")
    print('='*60)
    print("Если 'ДУБЛИРОВАННЫХ' много относительно 'уникальных сделок' —")
    print("файлы засорены повторными прогонами одного и того же периода.")
    print("Если среди дублей есть '⚠️  РАЗНЫЕ R' — это хуже: один и тот же")
    print("исторический бар посчитан по-разному в разных прогонах (код")
    print("расчёта риска менялся между ними). Такие записи противоречат")
    print("друг другу в памяти Архивариуса.")
    print("Решение, если грязно: почистить оба файла и начать копить")
    print("историю заново на сегодняшнем, финальном коде — скажи, дам")
    print("скрипт очистки (по аналогии с ochistit_pozicii.py).")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
