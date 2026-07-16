# -*- coding: utf-8 -*-
"""
patch_close_treydera.py
════════════════════════════════════════════════════════════════════
ВОЛЯ ТРЕЙДЕРА CLOSE → РЕАЛЬНОЕ ЗАКРЫТИЕ ПАКЕТА

БОЛЕЗНЬ: приёмник ЕСТЬ, сигнал НЕ ДОХОДИТ.
  • hooks._settle_positions (КАМЕНЬ 3, EXECUTOR_MANAGE_HAND_V1) умеет:
      if pos.get("manual_close"): exit=close, reason=MANUAL_CLOSE
    — воля трейдера раньше стопа и колокола. Готов.
  • НО мост ведения (_primenit_vedenie) на action==CLOSE только ПЕЧАТАЛ
      «settle закроет сам, не форсирую» — и НЕ ставил manual_close.
    Значит settle НИКОГДА не видел воли. CLOSE был пустым словом.

ЛЕЧЕНИЕ: на CLOSE мост помечает позицию этого magic manual_close=True.
На следующем _settle_bar позиция закроется по close, причина
MANUAL_CLOSE — весь ПАКЕТ разом (один пакет = одна позиция, settle
закрывает целиком; кусочничество не нужно). Осознанный выход
трейдера теперь исполняется.

ИДЕМПОТЕНТЕН (маркер CLOSE_TREYDERA_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_close_treydera.py
"""
import io
import sys
from pathlib import Path

MARKER = "CLOSE_TREYDERA_V1"


def find_tester() -> Path:
    for p in (Path("Биржа") / "tester_express.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "tester_express.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден tester_express.py — запусти из корня")
    sys.exit(1)


def main():
    path = find_tester()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src

    old = (
        '    if action not in ("ADD", "MOVE_STOP"):\n'
        '        if action in ("CLOSE",):\n'
        '            out(f"     └─ воля: {action} (settle закроет сам, не форсирую)")\n'
        '        return False\n'
    )
    new = (
        '    if action not in ("ADD", "MOVE_STOP"):\n'
        '        # ' + MARKER + ': CLOSE — воля трейдера. Ставим manual_close,\n'
        '        # settle закроет ВЕСЬ ПАКЕТ по close (причина MANUAL_CLOSE)\n'
        '        # на следующем баре — раньше стопа и колокола.\n'
        '        if action == "CLOSE":\n'
        '            from hooks import load_trading_state, save_trading_state\n'
        '            _ts = load_trading_state()\n'
        '            _hit = False\n'
        '            for _p in _ts.get("positions", []) or []:\n'
        '                if _p.get("magic") == pos_magic and _p.get("status") == "OPEN":\n'
        '                    _p["manual_close"] = True\n'
        '                    _hit = True\n'
        '            if _hit:\n'
        '                save_trading_state(_ts)\n'
        '                out(f"     └─ 🚪 CLOSE: {sid} закрывает пакет своей волей "\n'
        '                    f"(settle исполнит на след. баре)")\n'
        '                return True\n'
        '            out("     └─ 🚪 CLOSE: открытой позиции нет — нечего закрывать")\n'
        '        return False\n'
    )
    if old not in src:
        print("[ПАТЧ] ✗ якорь CLOSE в мосту не найден — примени "
              "patch_most_vedeniya.py сначала")
        sys.exit(2)
    src = src.replace(old, new, 1)

    bak = path.with_suffix(".py.bak_close")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ CLOSE трейдера теперь закрывает пакет по-настоящему.")
    print("[ПАТЧ]    Воля → manual_close → settle закроет весь пакет")
    print("[ПАТЧ]    (MANUAL_CLOSE), раньше стопа и колокола.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
