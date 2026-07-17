# -*- coding: utf-8 -*-
"""
patch_arhiv_kak_informaciya.py
════════════════════════════════════════════════════════════════════
АРХИВ — ИНФОРМАЦИЯ, НЕ ПРИКАЗ. Подключаем канал, который выглядел
построенным, но был мёртв (Брут читал t["arkhiv"], но никто туда не
писал — та же болезнь, что sync_to_dna и стол ведения без применения)

Слово Шефа: «не влиял вообще, ничего непосредственно указывать-
приказывать не должно, только как информация, а решения трейдеры
принимают сами. Если читать они архив будут, то полезно.»

Это тот же принцип, что уже работает для сенсоров («их удар — вводная,
не команда»). Архив встаёт в тот же ряд: доступен, весит его сам
трейдер, ничего не принуждает.

ЛЕЧЕНИЕ: сразу после _prepare_atlas_digest(state) (A05 ещё не
говорил, но выжимка уже посчитана) — кладём КОРОТКУЮ, читаемую версию
в trading_state["arkhiv"], откуда Брут/Илья/Василий её и так уже умеют
читать (`table.get("arkhiv", {})` — код был готов, просто пуст).

Форма нарочно компактна (sample_size, closed_trades, success_rate,
top_failure_reason, confidence) — трейдер получает ЧИСЛА и повод
задуматься, не сырой массив recent_cases (это уже пересказал бы
Архивариус словами в своём narrative, дублировать не нужно).

ИДЕМПОТЕНТЕН (маркер ARKHIV_KAK_INFORMACIYA_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_arhiv_kak_informaciya.py
"""
import io
import sys
from pathlib import Path

MARKER = "ARKHIV_KAK_INFORMACIYA_V1"


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

    old = (
        '    if agent_id == "A05":\n'
        '        _prepare_atlas_digest(state)\n'
        '        _prepare_trade_setup(state)\n'
    )
    if old not in src:
        print("[ПАТЧ] ✗ якорь A05/_prepare_atlas_digest не найден")
        sys.exit(2)

    new = (
        '    if agent_id == "A05":\n'
        '        _prepare_atlas_digest(state)\n'
        '        _prepare_trade_setup(state)\n'
        '        # ' + MARKER + ': выжимка Архива — В СТОЛ, как ИНФОРМАЦИЯ.\n'
        '        # Не приказ, не фильтр входа — трейдер сам решает, весить ли\n'
        '        # её (тот же принцип, что и у сенсоров: вводная, не команда).\n'
        '        try:\n'
        '            _dig = (state.get("chain_data", {}) or {}).get("atlas_digest", {}) or {}\n'
        '            if _dig:\n'
        '                _ts = load_trading_state()\n'
        '                _ts["arkhiv"] = {\n'
        '                    "sample_size":        _dig.get("sample_size"),\n'
        '                    "closed_trades":      _dig.get("closed_trades"),\n'
        '                    "success_rate":       _dig.get("success_rate"),\n'
        '                    "top_failure_reason": _dig.get("top_failure_reason"),\n'
        '                    "confidence":         _dig.get("arkhiv_confidence"),\n'
        '                }\n'
        '                save_trading_state(_ts)\n'
        '        except Exception as _ae:\n'
        '            print(f"[ARKHIV] ⚠️  выжимка не легла в стол: {_ae}")\n'
    )
    src = src.replace(old, new, 1)

    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ правка ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(3)

    bak = path.with_suffix(".py.bak_arhiv_info")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Архив теперь реально доходит до трейдеров — как")
    print("[ПАТЧ]    информация в столе, не команда. Решение — их.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
