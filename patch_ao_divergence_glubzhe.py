# -*- coding: utf-8 -*-
"""
ПАТЧ: AO_DIVERGENCE_GLUBZHE_V1

Общая дыра для Искры и Василия (не только его — тот же корень).
_ao_divergence_at_bar ищет дивергенцию против ПЕРВОГО попавшегося
локального экстремума цены назад по истории. Если у этого конкретного
экстремума знак AO не подходит — return False СРАЗУ, поиск обрывается,
хотя дальше в истории мог стоять честный экстремум с правильным знаком.

Замер (voronka_bdb.py, EURUSD D1, 2941 бар): 1048 кандидатов bdb,
из них ao_divergence=True только у 89 (8.5%) — уже AND с is_peak даёт
bdb_strong 18 (1.7% от кандидатов). Узкое место — ao_divergence режет
сильнее второго условия, и режет структурно (обрыв на первом экстремуме),
не потому что дивергенций в природе рынка действительно так мало.

ЧТО МЕНЯЕТ:
  williams_core.py: _ao_divergence_at_bar — оба цикла (BULL/BEAR),
  return False внутри for → continue. Поиск идёт дальше по истории,
  пока не найдёт экстремум с правильным знаком AO или не кончится
  диапазон (range(i-2, 1, -1) — тот же, что и был, границы не трогаем).

Бьёт по ОБОИМ: у Искры это её точка (bdb_dir/bdb_price, НЕ компас —
компас идёт через отдельную detect_ao_divergence с окном, он не
трогается). У Василия — тот же путь, этажом глубже (VASYA_SVOY_RAZVOROT_V1).

ЗАПУСК: из корня репо
    python patch_ao_divergence_glubzhe.py

Идемпотентно. Бэкап рядом (.bak).
"""
import ast
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "williams_core.py"
MARKER = "AO_DIVERGENCE_GLUBZHE_V1"

OLD = '''    if direction == "BULL":
        if ao_i >= 0:
            return False
        for k in range(i - 2, 1, -1):
            if (bars[k]["low"] < bars[k-1]["low"] and
                bars[k]["low"] < bars[k+1]["low"]):
                ao_k = ao_series[k]
                if ao_k is None or ao_k >= 0:
                    return False
                return bool(bars[i]["low"] < bars[k]["low"] and ao_i > ao_k)
    else:
        if ao_i <= 0:
            return False
        for k in range(i - 2, 1, -1):
            if (bars[k]["high"] > bars[k-1]["high"] and
                bars[k]["high"] > bars[k+1]["high"]):
                ao_k = ao_series[k]
                if ao_k is None or ao_k <= 0:
                    return False
                return bool(bars[i]["high"] > bars[k]["high"] and ao_i < ao_k)
    return False'''

NEW = '''    # AO_DIVERGENCE_GLUBZHE_V1: раньше первый попавшийся экстремум с
    # неправильным знаком AO обрывал весь поиск (return False внутри
    # цикла). Теперь — continue: если этот экстремум не подошёл, ищем
    # ДАЛЬШЕ по истории, пока диапазон не кончится. Дивергенция реже
    # экстремумов, но не настолько реже, насколько её резал обрыв на
    # первом кандидате (замер voronka_bdb.py: 8.5% от кандидатов до
    # патча — структурный обрыв, не редкость рынка).
    if direction == "BULL":
        if ao_i >= 0:
            return False
        for k in range(i - 2, 1, -1):
            if (bars[k]["low"] < bars[k-1]["low"] and
                bars[k]["low"] < bars[k+1]["low"]):
                ao_k = ao_series[k]
                if ao_k is None or ao_k >= 0:
                    continue
                if bars[i]["low"] < bars[k]["low"] and ao_i > ao_k:
                    return True
    else:
        if ao_i <= 0:
            return False
        for k in range(i - 2, 1, -1):
            if (bars[k]["high"] > bars[k-1]["high"] and
                bars[k]["high"] > bars[k+1]["high"]):
                ao_k = ao_series[k]
                if ao_k is None or ao_k <= 0:
                    continue
                if bars[i]["high"] > bars[k]["high"] and ao_i < ao_k:
                    return True
    return False'''


def main() -> int:
    if not TARGET.exists():
        print(f"[ПАТЧ] ✗ не найден {TARGET}")
        return 1
    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — пропускаю")
        return 0
    if OLD not in src:
        print("[ПАТЧ] ✗ якорь не найден — файл уже другой")
        return 1
    src = src.replace(OLD, NEW, 1)
    src += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ результат не парсится: {e}")
        return 1
    shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {MARKER} применён → {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
