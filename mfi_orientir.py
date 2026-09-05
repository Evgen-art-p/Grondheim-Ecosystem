#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MFI_ORIENTIR_NE_SIGNAL_V1 — 05.09
Запускать из КОРНЯ репо (Grondheim-Ecosystem), как предыдущие патчи.

Убирает MFI из условия «подпитки той же стороной» в hooks.py
(proverit_tochku). Было: новый некрон той же стороны продлевает точку
ТОЛЬКО если MFI на этом баре GREEN или SQUAT — иначе код проваливался
в структурный слом и убивал точку целиком, даже когда новый более
глубокий некрон был честным и правильным (живой пример — «квадрат»
17-19.08, оба некрона прошли формулу, MFI ни при чём).

Слово Шефа (05.09): «MFI — ориентир, не сигнал». Условие снято: точка
углубляется всякий раз, когда приходит новый некрон той же стороны.
MFI остаётся в тексте `reason` как факт на столе, не как ворота.

Идемпотентен: повторный запуск — 0 правок. Бэкап .bak_mfi рядом.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

STARIY = '''    # ── 1. подпитка той же стороной — ПРОВЕРЯЕТСЯ ПЕРВОЙ ──
    # Порядок важен (найдено тестом при отладке патча): пробой
    # zero_point_price свежим баром той же стороны с GREEN/SQUAT —
    # это НЕ слом, это новая, более глубокая версия ТОЙ ЖЕ точки.
    # Слом — только когда пробой ничем не подтверждён.
    if wf.get("bdb_dir") == napr and mfi_type in ("GREEN", "SQUAT"):
        novaya_zp = None
        if napr == "BULL" and low is not None:
            novaya_zp = min(zp, low)      # новое, более глубокое дно
        elif napr == "BEAR" and high is not None:
            novaya_zp = max(zp, high)     # новый, более высокий потолок
        if novaya_zp is not None and novaya_zp != zp:
            isk["zero_point_price"] = novaya_zp
            isk["rodilas_na_bare"]  = md.get("bar_time")
            save_trading_state(tstate)
            return {"alive": True,
                    "reason": f"подпитка {mfi_type}: точка обновлена → {novaya_zp}",
                    "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1
'''

NOVYY = '''    # ── 1. подпитка той же стороной — ПРОВЕРЯЕТСЯ ПЕРВОЙ ──
    # MFI_ORIENTIR_NE_SIGNAL_V1 (05.09): было условием — новый некрон
    # той же стороны без GREEN/SQUAT проваливался в структурный слом,
    # хотя сам факт нового более глубокого некрона уже делает его
    # новой версией точки (живой пример «квадрата» 17-19.08 — оба
    # некрона честно прошли формулу, MFI при этом ни при чём). Слово
    # Шефа: «MFI — ориентир, не сигнал». Убрано как ворота; MFI
    # остаётся в reason фактом на столе, не условием жизни точки.
    if wf.get("bdb_dir") == napr:
        novaya_zp = None
        if napr == "BULL" and low is not None:
            novaya_zp = min(zp, low)      # новое, более глубокое дно
        elif napr == "BEAR" and high is not None:
            novaya_zp = max(zp, high)     # новый, более высокий потолок
        if novaya_zp is not None and novaya_zp != zp:
            isk["zero_point_price"] = novaya_zp
            isk["rodilas_na_bare"]  = md.get("bar_time")
            save_trading_state(tstate)
            return {"alive": True,
                    "reason": f"подпитка (MFI {mfi_type}): точка обновлена → {novaya_zp}",
                    "changed": True, "direction": napr}   # TOCHKA_NAPRAVLENIE_V1
'''


def _naiti(rel_suffix: str) -> list[Path]:
    found = []
    for p in REPO_ROOT.rglob("*"):
        if p.is_file() and str(p).replace("\\", "/").endswith(rel_suffix):
            found.append(p)
    return found


def main():
    print("=== MFI_ORIENTIR_NE_SIGNAL_V1 ===\n")
    files = _naiti("Биржа/hooks.py")
    if not files:
        print("❌ hooks.py не найден — запускать из корня репо!")
        return

    for path in files:
        text = path.read_text(encoding="utf-8")
        if NOVYY.strip() in text:
            print(f"⏭  {path}: уже правлено, пропускаю")
            continue
        n = text.count(STARIY)
        if n == 0:
            print(f"⚠️  {path}: старый фрагмент не найден "
                  f"(структура изменилась — патч не применён, ничего не сломано)")
            continue
        if n > 1:
            print(f"⚠️  {path}: старый фрагмент встретился {n} раз — "
                  f"не трогаю, разбираться руками")
            continue

        bak = path.with_suffix(path.suffix + ".bak_mfi")
        if not bak.exists():
            bak.write_text(text, encoding="utf-8")

        text = text.replace(STARIY, NOVYY, 1)
        path.write_text(text, encoding="utf-8")
        print(f"✅ {path}: MFI убран из условия подпитки точки")

    print("\nГотово. Резервная копия — hooks.py.bak_mfi.")
    print("Проверь синтаксис (python -c \"import ast; ast.parse(open('Биржа/hooks.py',encoding='utf-8').read())\")")
    print("перед тем как гонять живой прогон.")


if __name__ == "__main__":
    main()
