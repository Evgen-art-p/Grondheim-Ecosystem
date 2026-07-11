# -*- coding: utf-8 -*-
"""
patch_arkhiv_atlas_path_abs_v1.py
────────────────────────────────────────────────────────────────────
ЧИНИТ: «A05: Похожих случаев в Атласе: 0. Уверенность: LOW» — ВСЕГДА.
Архивариус слеп к памяти Биржи: сколько бы сделок ни закрылось, он
видит пустой Атлас.

КОРЕНЬ — тот же дрейф путей, что был у ленты закрытий (pnl):
  • hooks._write_atlas ПИШЕТ в АБСОЛЮТНЫЙ путь
        _REPO / GRONDHEIM_CITY / Биржа / данные / atlas_trading.jsonl
  • мозг Архивариуса ЧИТАЕТ из ОТНОСИТЕЛЬНОГО
        economy/data/atlas_trading.jsonl   (старый путь студии, CWD=studio)

  Файл портирован «дословно» из studio/, где относительный путь честно
  резолвился (CWD=studio). В новом городе CWD=корень — путь мёртв, файла
  там нет, писатель туда не пишет. Reader и writer разошлись.

  Хуже того: hooks._prepare_atlas_digest ДЕЛЕГИРУET выжимку самому мозгу
  Архивариуса (_b_arkhiv.build_digest). Свой правильный АБСОЛЮТНЫЙ чит
  hooks держит лишь как фоллбэк «на исключение». Но мозг не падает — он
  тихо возвращает 0. Поэтому верный фоллбэк НИКОГДА не срабатывает, и в
  ленте всегда sample=0. Одна строка чинит и прямой запуск A05 в Совете,
  и выжимку hooks.

ЛЕЧЕНИЕ: якорим ATLAS_PATH мозга к тому же абсолютному файлу, что пишет
hooks — через __file__ самого слота (без импорта hooks, чтобы не зависеть
от загрузки через _slot_brain):
    ATLAS_PATH = Path(__file__).resolve().parents[4] / "данные" / "atlas_trading.jsonl"
  parents[4] от .../цеха/контора/слоты/архивариус/мозг.py == GRONDHEIM_CITY/Биржа.
  Проверено: путь байт-в-байт совпадает с hooks.ATLAS_PATH.

Идемпотентно. Маркер ARKHIV_ATLAS_PATH_ABS_V1. Бэкап рядом (.bak).
Запуск из КОРНЯ репы (Windows/PowerShell):
    python patch_arkhiv_atlas_path_abs_v1.py
"""
from __future__ import annotations
import sys
from pathlib import Path

MARKER = "ARKHIV_ATLAS_PATH_ABS_V1"
TARGET = (Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "контора" /
          "слоты" / "архивариус" / "мозг.py")

OLD = 'ATLAS_PATH   = Path("economy/data/atlas_trading.jsonl")'
NEW = ('ATLAS_PATH   = Path(__file__).resolve().parents[4] / "данные" / '
       '"atlas_trading.jsonl"   # ' + MARKER +
       ': тот же файл, что пишет hooks._write_atlas')


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET}")
        print("  запусти из КОРНЯ репы (там, где папка GRONDHEIM_CITY).")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if OLD not in src:
        print("✗ не нашёл ожидаемую строку с относительным путём Атласа:")
        print(f"    {OLD}")
        print("  Возможно, путь уже правился вручную. Проверь ATLAS_PATH в "
              "мозге Архивариуса — он должен смотреть в "
              "GRONDHEIM_CITY/Биржа/данные/atlas_trading.jsonl.")
        return 2

    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")
    else:
        print(f"• бэкап уже был: {bak} (не перезаписываю)")

    TARGET.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"✓ {TARGET}: ATLAS_PATH теперь смотрит в тот же файл, что пишет hooks.")
    print("  Архивариус снова видит закрытые сделки → sample/уверенность оживут.")
    print(f"  Маркер идемпотентности: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
