# -*- coding: utf-8 -*-
"""
patch_slepok_iz_chain_v1.py
────────────────────────────────────────────────────────────────────
СЛЕПОК СТОЛА — ИЗ ПРАВИЛЬНОГО ИСТОЧНИКА.

НАЙДЕНО НА ЖИВОМ ПРОГОНЕ (12.07): заряд Ильи двинулся (−0.147, суд
ТРЕЙДЕРА работает), а у Веры/Моржа/Паникёра/Ганса — ноль черновиков,
паспорта от 08.07. Суд СЕНСОРОВ молчал на всех 28 закрытых сделках.

ПРИЧИНА — МОЯ ОШИБКА в patch_sud_sensorov_v2. Слепок собирался так:

    "стол_входа": {
        k: dict(tstate.get(k, {}) or {})
        for k in ("iskra", "morj", "panic", "hans")
    },

tstate = load_trading_state() — это СТАРЫЙ ФАЙЛ С ДИСКА, прочитанный
в начале _persist_trading_state. В _DEFAULT_STATE вообще есть только
"iskra"; ключей morj/panic/hans там нет по определению. Итог: слепок
приезжал пустой ({} или устаревший), а судья сенсоров начинается с

    stol = pos.get("стол_входа") or {}
    if not stol or pnl_r is None:
        return          # ← тихо выходил

и молчал. Тихо, без единой строки в логе.

ГДЕ ПРАВДА: свежие показания ЭТОГО бара лежат в chain_data — ими
Совет и думал. Это видно по соседям в том же файле:
    _log_rejections:      chain.get("t1_status"), chain.get("morj_status"),
                          chain.get("panic_phase"), chain.get("fractal_valid")
    _prepare_atlas_digest: та же четвёрка — сигнатура похожести
Я взял не из того источника. Беру из того же, что все.

ЧТО ДЕЛАЕТ: переписывает сборку "стол_входа" на chain_data. Плюс
кладёт КОМПАС и СТОРОНУ ФРАКТАЛА — без них _zval не может понять,
звал ли сенсор В СТОРОНУ сделки (Вера с компасом BULL «звала» в LONG,
но НЕ звала в SHORT; Ганс с фракталом UP — то же самое).

Идемпотентно. .bak рядом.  Из КОРНЯ репы:
    python patch_slepok_iz_chain_v1.py

ПОСЛЕ: гони тестер (УЧИТЬ включён) и жди в логе строки вида
    [МОСТ] 📝 черновик → Вера (A01): «МОЯ ОШИБКА (...)» (раз: 1/3)
    [МОСТ] 🫁 Морж: -1.0R → заряд -0.08
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "SLEPOK_IZ_CHAIN_V1"
HOOKS = Path("Биржа") / "hooks.py"

OLD = '''            # SUD_SENSOROV_V2: СЛЕПОК СТОЛА — показания всех четырёх сенсоров на баре
            # ВХОДА, целиком. Стол перетирается каждый бар: судить сенсора
            # по чужому бару было бы клеветой. Это их опыт — слово, которое
            # рынок потом либо подтвердил, либо нет.
            "стол_входа": {
                k: dict(tstate.get(k, {}) or {})
                for k in ("iskra", "morj", "panic", "hans")
            },'''

NEW = '''            # SUD_SENSOROV_V2 · ''' + MARKER + ''': СЛЕПОК СТОЛА — показания
            # всех четырёх сенсоров на баре ВХОДА. Стол перетирается каждый
            # бар: судить сенсора по чужому бару было бы клеветой.
            #
            # ИСТОЧНИК — chain_data, НЕ tstate. tstate = load_trading_state()
            # это СТАРЫЙ ФАЙЛ С ДИСКА (в _DEFAULT_STATE есть только "iskra",
            # ключей morj/panic/hans там нет вовсе) — слепок приезжал пустым,
            # и судья сенсоров молча выходил на 28 сделках подряд.
            # chain_data — то, чем Совет ДУМАЛ на этом баре. Ровно оттуда
            # берут соседи: _log_rejections и _prepare_atlas_digest.
            "стол_входа": {
                "iskra": {
                    "t1_status":        chain.get("t1_status"),
                    "zero_point_price": chain.get("zero_point_price"),
                    # компас: без него не понять, звала ли Вера В СТОРОНУ
                    # сделки (BULL зовёт в LONG, но НЕ зовёт в SHORT)
                    "trend_direction":  (chain.get("market_data", {}) or {})
                                        .get("global_bias"),
                },
                "morj": {
                    "morj_status":      chain.get("morj_status"),
                    "wave_1_validated": chain.get("wave_1_validated"),
                },
                "panic": {
                    "panic_phase":      chain.get("panic_phase"),
                },
                "hans": {
                    "fractal_valid":    chain.get("fractal_valid"),
                    # сторона фрактала — та же логика, что у компаса Веры
                    "fractal_side":     chain.get("hans_direction")
                                        or chain.get("fractal_side"),
                    "fractal_price":    chain.get("fractal_price"),
                },
            },'''


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ СЛЕПОК СТОЛА — из chain_data, а не из старого файла ═══")

    if not HOOKS.exists():
        print(f"✗ не нашёл {HOOKS} — ты в КОРНЕ репы?")
        return 1

    src = HOOKS.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if OLD not in src:
        print("✗ не нашёл сборку «стол_входа» из tstate в ожидаемом виде.")
        print("  Сначала patch_sud_sensorov_v2.py? Или файл правился вручную.")
        return 2

    bak = HOOKS.with_suffix(".py.bak_slepok")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")

    HOOKS.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")

    print(f"✓ {HOOKS}: слепок берётся из chain_data (свежие показания бара)")
    print("   + компас Веры и сторона фрактала Ганса — без них _zval не мог")
    print("     понять, звал ли сенсор В СТОРОНУ сделки.")
    print(f"   Маркер: {MARKER}")
    print("\nГони тестер (УЧИТЬ включён). Жди в логе:")
    print("   [МОСТ] 📝 черновик → Вера (A01): «МОЯ ОШИБКА...» (раз: 1/3)")
    print("   [МОСТ] 🫁 Морж: -1.0R → заряд -0.08")
    print("\nПотом: python proverka_ucheby.py — у сенсоров должны появиться")
    print("заряды и черновики, паспорта — с сегодняшней датой.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
