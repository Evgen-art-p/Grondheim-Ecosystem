# -*- coding: utf-8 -*-
"""
ochistit_atlas.py — разовая чистка Атласа и ленты PnL.

Причина: сегодняшние файлы накопили противоречивые записи (одна и та
же историческая сделка посчитана по-разному в разных прогонах — код
расчёта риска менялся несколько раз за день) + Атлас 94/94 записей
без сигнатуры сенсоров (патч ARKHIV_SIGNATURA_ISHODA_V1 это лечит
для НОВЫХ записей, старые уже не почистить задним числом).

Архивирует оба файла целиком (не удаляет — переименовывает с меткой
времени), затем создаёт пустые файлы на их месте. Дальше система
копит историю заново, уже на полностью пропатченном коде.

НЕ трогает trading_state.json (открытые позиции) — для него свой
скрипт, ochistit_pozicii.py.

Запуск из корня проекта:
    python ochistit_atlas.py
"""
import io
import sys
from datetime import datetime
from pathlib import Path


def find(name):
    for base in (Path("Биржа") / "данные", Path("GRONDHEIM_CITY") / "Биржа" / "данные"):
        p = base / name
        if p.exists():
            return p
    return None


def find_dir():
    for base in (Path("Биржа") / "данные", Path("GRONDHEIM_CITY") / "Биржа" / "данные"):
        if base.exists():
            return base
    return None


def ochistit(path, label):
    if not path:
        print(f"[ЧИСТКА] {label}: файл не найден — нечего чистить")
        return

    n_lines = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if n_lines == 0:
        print(f"[ЧИСТКА] {label}: и так пуст — чистить нечего")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = path.with_name(f"{path.stem}_archive_{stamp}{path.suffix}")
    archive.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    path.write_text("", encoding="utf-8")

    print(f"[ЧИСТКА] {label}: OK — архивировано {n_lines} строк → {archive.name}")
    print(f"[ЧИСТКА]   файл обнулён, копим заново")


def main():
    d = find_dir()
    if not d:
        print("[ЧИСТКА] ✗ не найдена папка Биржа/данные — запусти из корня проекта")
        sys.exit(1)

    print(f"[ЧИСТКА] папка данных: {d}\n")

    ochistit(find("atlas_trading.jsonl"), "atlas_trading.jsonl (память Архивариуса)")
    print()
    ochistit(find("trading_pnl.jsonl"), "trading_pnl.jsonl (лента закрытий)")

    print("\n[ЧИСТКА] ✅ Готово. Оба файла архивированы и обнулены.")
    print("[ЧИСТКА]    Новые сделки лягут уже на полностью пропатченном коде:")
    print("[ЧИСТКА]    честный stop_initial, честный трейлинг, сигнатура")
    print("[ЧИСТКА]    сенсоров в Атласе. Гоняй заново — история чистая.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
