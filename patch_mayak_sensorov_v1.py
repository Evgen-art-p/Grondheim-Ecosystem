# -*- coding: utf-8 -*-
"""
patch_mayak_sensorov_v1.py
────────────────────────────────────────────────────────────────────
МАЯЧОК В СУДЬЕ СЕНСОРОВ — временная диагностика.

Три раза подряд я ошибался, потому что домысливал вместо того, чтобы
посмотреть в источник. Хватит. Ставим маячок и слушаем, что говорит
сам код на живом прогоне.

ФАКТЫ, которые уже есть:
  · все 14 патчей стоят;
  · трейдеры дышат (Илья −0.147, Брут +0.007);
  · сенсоры молчат (паспорта от 07-08.07);
  · зомби-позиций со старым слепком нет;
  · _zval исправен — принимает и UP/LONG, и DOWN/SHORT.

ЗНАЧИТ обрыв ГДЕ-ТО МЕЖДУ закрытием позиции и записью в носителя.
Маячок печатает КАЖДЫЙ шаг:
  · вызвался ли _judge_iskra_by_result вообще;
  · что пришло в pos (есть ли «стол_входа», что внутри);
  · для каждого сенсора: звал / не звал, какой вывод родился;
  · что вернула запись (или дыхание).

ЭТО ВРЕМЕННЫЙ ПАТЧ. Снять: python patch_mayak_sensorov_v1.py --snyat

Идемпотентно. .bak рядом.  Из КОРНЯ репы:
    python patch_mayak_sensorov_v1.py
    (гоняешь тестер с УЧИТЬ, кидаешь мне лог)
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "MAYAK_SENSOROV_V1"
HOOKS = Path("Биржа") / "hooks.py"

OLD = '''    stol = pos.get("стол_входа") or {}
    if not stol or pnl_r is None:
        return
    try:
        import sys as _s
        from pathlib import Path as _P
        _b = str(_P(__file__).resolve().parent)
        if _b not in _s.path:
            _s.path.insert(0, _b)
        from nositel import SENSOR_SLOTS, sudit_sensora, zapisat_vyvod_pare'''

NEW = '''    # ''' + MARKER + ''' — ВРЕМЕННЫЙ МАЯЧОК (снять после разбора)
    print(f"[МАЯК] судья сенсоров вызван: pnl_r={pnl_r}, "
          f"trader={pos.get('trader')}, dir={pos.get('direction')}")
    print(f"[МАЯК] ключи позиции: {list(pos.keys())}")
    stol = pos.get("стол_входа") or {}
    print(f"[МАЯК] стол_входа: {stol}")
    if not stol or pnl_r is None:
        print("[МАЯК] ⛔ ВЫХОД: слепка нет или pnl_r=None")
        return
    try:
        import sys as _s
        from pathlib import Path as _P
        _b = str(_P(__file__).resolve().parent)
        if _b not in _s.path:
            _s.path.insert(0, _b)
        from nositel import SENSOR_SLOTS, sudit_sensora, zapisat_vyvod_pare
        import nositel as _nmod
        print(f"[МАЯК] nositel загружен. UCHIT={getattr(_nmod, 'UCHIT', 'НЕТ ПОЛЯ')}")'''

OLD_LOOP = '''        for key, slot in SENSOR_SLOTS.items():
            pokazanie = stol.get(key) or {}
            vyvod = sudit_sensora(key, pokazanie, direction, pnl_r, trader, bar)
            if vyvod:
                # значимое: вдох уже внутри zapisat_vyvod_pare
                zapisat_vyvod_pare("торговый_хаос", slot, vyvod, pnl_r=pnl_r)
                continue
            # DYHANIE_SDELKI_V1: вывода нет (рутина) — но если сенсор ЗВАЛ в
            # эту сделку, исход его задевает: заряд двигается. Молчавший НЕ
            # дышит — не его сделка, не его боль (то же правило, что в суде).
            try:
                from nositel import _zval, dyhnut_slovom
                if _zval(key, pokazanie, direction):
                    dyhnut_slovom("торговый_хаос", slot, pnl_r)
            except Exception:
                pass'''

NEW_LOOP = '''        from nositel import _zval, dyhnut_slovom   # ''' + MARKER + '''
        for key, slot in SENSOR_SLOTS.items():
            pokazanie = stol.get(key) or {}
            zval = _zval(key, pokazanie, direction)
            vyvod = sudit_sensora(key, pokazanie, direction, pnl_r, trader, bar)
            print(f"[МАЯК] {slot} {key}: показание={pokazanie} "
                  f"звал={zval} вывод={'ЕСТЬ' if vyvod else 'пусто'}")
            if vyvod:
                r = zapisat_vyvod_pare("торговый_хаос", slot, vyvod, pnl_r=pnl_r)
                print(f"[МАЯК] {slot} ЗАПИСЬ → {r}")
                continue
            if zval:
                r = dyhnut_slovom("торговый_хаос", slot, pnl_r)
                print(f"[МАЯК] {slot} ДЫХАНИЕ → {r}")
            else:
                print(f"[МАЯК] {slot} молчал — не судим, не дышит")'''

SNYAT = "--snyat" in sys.argv


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not HOOKS.exists():
        print(f"✗ не нашёл {HOOKS} — ты в КОРНЕ репы?")
        return 1

    src = HOOKS.read_text(encoding="utf-8")

    if SNYAT:
        if MARKER not in src:
            print("маячка нет — снимать нечего")
            return 0
        src = src.replace(NEW, OLD, 1).replace(NEW_LOOP, OLD_LOOP, 1)
        HOOKS.write_text(src, encoding="utf-8")
        print("✓ маячок снят, hooks вернулся к рабочему виду")
        return 0

    if MARKER in src:
        print("✓ маячок уже стоит — гони тестер и кидай лог")
        return 0

    if OLD not in src:
        print("✗ не нашёл начало _judge_iskra_by_result в ожидаемом виде.")
        return 2
    if OLD_LOOP not in src:
        print("✗ не нашёл цикл по сенсорам (с дыханием). Стоит ли "
              "patch_dyhanie_sdelki_v1?")
        return 3

    bak = HOOKS.with_suffix(".py.bak_mayak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")

    src = src.replace(OLD, NEW, 1).replace(OLD_LOOP, NEW_LOOP, 1)
    HOOKS.write_text(src, encoding="utf-8")

    print("✓ МАЯЧОК ПОСТАВЛЕН в судью сенсоров.")
    print("\nТеперь:")
    print("  1. гони тестер (УЧИТЬ включён), ловить 5-10")
    print("  2. кидай мне ВЕСЬ вывод консоли со строками [МАЯК]")
    print("\nОн скажет: вызвался ли судья, что в слепке, звал ли каждый")
    print("сенсор, родился ли вывод, и что ответила запись/дыхание.")
    print("\nПотом снять:  python patch_mayak_sensorov_v1.py --snyat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
