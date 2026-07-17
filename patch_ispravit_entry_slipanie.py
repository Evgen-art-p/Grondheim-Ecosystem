# -*- coding: utf-8 -*-
"""
patch_ispravit_entry_slipanie.py
════════════════════════════════════════════════════════════════════
ДВЕ МОИ ОШИБКИ ИЗ СЕГОДНЯШНИХ УТРЕННИХ ПАТЧЕЙ — НАЙДЕНЫ ШЕФОМ ПО ОТЧЁТУ

БАГ 1 — entry ВСЕХ трейдеров слипался в одну цену (OTLOZHKA_SPREAD_V2)

Болезнь (отчёт EURUSD H12): три РАЗНЫХ трейдера (Брут/Илья/Василий) на
одном баре дали LONG — и все трое получили АБСОЛЮТНО идентичный
entry/exit/R до шестого знака. У них разный канон входа (фрактал/
разворотный бар/откат) — совпадение статистически невозможно.

Причина:
    if d == "LONG":
        if high is not None:
            entry = round(high + 2 * sp, 6)
`high` — ХАЙ ТЕКУЩЕГО БАРА СОВЕТА (chain.market_data.price.high), ОДИН
И ТОТ ЖЕ для всех трейдеров на этом баре. Код ВЫБРАСЫВАЛ персональный
entry трейдера (order.get("entry") — посчитанный по ЕГО канону) и
подставлял вместо него общий бар.

Лечение: спред добавляется К СОБСТВЕННОМУ entry трейдера, не заменяет
его чужим числом:
    LONG:  entry = order.entry + 2×спред   (был: chain.high + 2×спред)
    SHORT: entry = order.entry - 3 пункта  (был: chain.low  - 3 пункта)

БАГ 2 — NameError 'point' не определена (PUNKT_OT_POINT_V1, тот же день)

При проверке фикса бага 1 нашёлся ВТОРОЙ, более тяжёлый баг в той же
функции: `punkt = 10 * float(point or 0.01)` — переменная `point`
НИГДЕ в этой функции не определялась (в отличие от соседней
_pereezd_zayavki, где я её определил верно). Строка выполняется
БЕЗУСЛОВНО перед разбором LONG/SHORT — падала на КАЖДОМ вызове.
Подтверждено прямым запуском живого модуля (не только ast-синтаксисом).

Лечение: добавлена `point = md.get("point") or 0.01` перед использованием.

ПРОВЕРЕНО: три трейдера с разным СВОИМ entry теперь дают три РАЗНЫХ
итоговых числа (было — одно на всех). Функция больше не падает.

ИДЕМПОТЕНТЕН (маркер ENTRY_NE_SLIPAETSYA_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_ispravit_entry_slipanie.py
"""
import io
import sys
from pathlib import Path

MARKER = "ENTRY_NE_SLIPAETSYA_V1"


def find_hooks() -> Path:
    for p in (Path("Биржа") / "hooks.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "hooks.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден hooks.py — запусти из корня")
    sys.exit(1)


def main():
    path = find_hooks()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src
    n = 0

    # ── Баг 2 сначала (добавить point) ──────────────────────
    old_point = (
        '    sp = _spread_price(chain)\n'
        '    punkt = 10 * float(point or 0.01)  # PUNKT_OT_POINT_V1: пункт = 10×point (любой инструмент)\n'
    )
    new_point = (
        '    sp = _spread_price(chain)\n'
        '    point = md.get("point") or 0.01  # POINT_NE_OPREDELEN_V1: было не\n'
        '    # определено — NameError на КАЖДОМ вызове, падало безусловно\n'
        '    punkt = 10 * float(point or 0.01)  # PUNKT_OT_POINT_V1: пункт = 10×point (любой инструмент)\n'
    )
    if old_point in src:
        src = src.replace(old_point, new_point, 1)
        n += 1
        print("[ПАТЧ] ✓ Баг 2: 'point' определена, NameError починен")
    else:
        print("[ПАТЧ] ⚠️  Баг 2: якорь не найден (может, уже починен отдельно)")

    # ── Баг 1: слипание entry ────────────────────────────────
    old_slip = (
        '    if d == "LONG":\n'
        '        if high is not None:\n'
        '            entry = round(high + 2 * sp, 6)      # Buy Stop над баром, по Ask\n'
        '        # стоп снизу по Bid — спред не мешает\n'
        '    elif d == "SHORT":\n'
        '        if low is not None:\n'
        '            entry = round(low - 3 * punkt, 6)    # Sell Stop, запас 3 пункта\n'
        '        if stop is not None:\n'
        '            stop = round(stop + 2 * sp, 6)       # стоп сверху по Ask\n'
    )
    new_slip = (
        '    # ' + MARKER + ': спред добавляется К СОБСТВЕННОМУ входу\n'
        '    # трейдера (entry уже посчитан ИМ по ЕГО канону — фрактал/\n'
        '    # разворотный бар/откат), а не заменяется общим high/low бара\n'
        '    # Совета. Иначе разные трейдеры на одном баре сливались бы в\n'
        '    # одну цену — так и было найдено (три верда LONG = один entry).\n'
        '    if d == "LONG":\n'
        '        if entry is not None:\n'
        '            entry = round(entry + 2 * sp, 6)     # Buy Stop, по Ask\n'
        '        # стоп снизу по Bid — спред не мешает\n'
        '    elif d == "SHORT":\n'
        '        if entry is not None:\n'
        '            entry = round(entry - 3 * punkt, 6)  # Sell Stop, запас 3 пункта\n'
        '        if stop is not None:\n'
        '            stop = round(stop + 2 * sp, 6)       # стоп сверху по Ask\n'
    )
    if old_slip in src:
        src = src.replace(old_slip, new_slip, 1)
        n += 1
        print("[ПАТЧ] ✓ Баг 1: entry больше не слипается между трейдерами")
    else:
        print("[ПАТЧ] ⚠️  Баг 1: якорь не найден (может, уже починен)")

    if n == 0:
        print("[ПАТЧ] ✗ ни один якорь не совпал — останов")
        sys.exit(2)

    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ правка ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_entry_slipanie")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✅ Готово ({n} правок). Каждый трейдер входит по СВОЕЙ")
    print("[ПАТЧ]    цене, функция больше не падает на NameError.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()

