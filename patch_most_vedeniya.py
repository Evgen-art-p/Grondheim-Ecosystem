# -*- coding: utf-8 -*-
"""
patch_most_vedeniya.py
════════════════════════════════════════════════════════════════════
МОСТ ВЕДЕНИЯ: решение трейдера (ADD / MOVE_STOP) → РЕАЛЬНАЯ позиция

БОЛЕЗНЬ (нашли по коду + отчёт GBPUSD): _vesti_poziciyu будит хозяина
позиции, тот РЕАЛЬНО думает (LLM жжёт токены) и решает ADD/MOVE_STOP
своим характером — но решение кладётся ТОЛЬКО на табло
(t["brut"]["action"]/new_stop/add_lot) и в дневник. К настоящей
позиции (pos["stop"], pos["lot"]) НИЧЕГО не применяется.
Тот же класс, что был у sync_to_dna — только тоньше: тут «успех»
тихий, код думает, что сделал дело, а сделал только запись мысли.

Отсюда «0 сделок ≥+2R» в отчёте: даже когда фрактал по тренду был и
трейдер решал ADD — долив не долетал. Стоп двигал лишь безличный
трейлинг (своя логика Зубов), осознанное решение хозяина гасло.

ЛЕЧЕНИЕ: после того как разбуженный хозяин вернул r с signal,
читаем его action и ПРИМЕНЯЕМ к позиции этого magic:

  • MOVE_STOP → pos["stop"] = new_stop, НО ТОЛЬКО В ЗАЩИТУ
      (LONG стоп только вверх, SHORT только вниз — нельзя отодвинуть
      стоп дальше от входа и раздуть риск). stop_initial НЕ трогаем:
      R меряется от входного стопа (Закон stop_initial).
  • ADD → доливка. ЧЕСТНО: полная пирамида Котина — это отдельные
      позиции (свой вход/стоп у каждого долива). Это большая стройка.
      ПЕРВЫЙ ШАГ (здесь): наращиваем лот существующей позиции на
      add_lot и, если стоп ещё не в сейфе, тянем его за Зубы (весь
      пакет за Зубами — §7). Пирамиду отдельными ногами — потом.
  • HOLD / WAIT → ничего (осознанный покой).
  • CLOSE → НЕ трогаем принудительно: settle закроет по стопу/колоколу.
      Только лог — чтобы видеть волю трейдера.

Префикс полей по слоту: A06→brut_, A07→avan_, A08→cons_.

ИДЕМПОТЕНТЕН (маркер MOST_VEDENIYA_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_most_vedeniya.py
"""
import io
import sys
from pathlib import Path

MARKER = "MOST_VEDENIYA_V1"


def find_target() -> Path:
    for p in (Path("Биржа") / "tester_express.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "tester_express.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден Биржа/tester_express.py — запусти из корня")
    sys.exit(1)


HELPER = '''
# ''' + MARKER + ''': применяем решение хозяина к РЕАЛЬНОЙ позиции ──────
_VEDENIE_PREFIX = {"A06": "brut", "A07": "avan", "A08": "cons"}


def _primenit_vedenie(sid, r, pos_magic, md, out=print):
    """Читает signal разбуженного хозяина и применяет action к позиции
    с magic=pos_magic. MOVE_STOP только в защиту; ADD растит лот +
    тянет стоп в сейф. Возвращает True, если что-то реально изменил."""
    from hooks import load_trading_state, save_trading_state

    sig = (r or {}).get("signal", {}) or {}
    pref = _VEDENIE_PREFIX.get(sid)
    if not pref:
        return False

    action = (sig.get(f"{pref}_action") or "").upper().strip()
    new_stop = sig.get(f"{pref}_new_stop")
    add_lot = sig.get(f"{pref}_add_lot")

    if action not in ("ADD", "MOVE_STOP"):
        if action in ("CLOSE",):
            out(f"     └─ воля: {action} (settle закроет сам, не форсирую)")
        return False

    teeth = ((md.get("alligator", {}) or {}).get("teeth"))
    close = ((md.get("price", {}) or {}).get("close"))

    ts = load_trading_state()
    changed = False
    for p in ts.get("positions", []) or []:
        if p.get("magic") != pos_magic or p.get("status") != "OPEN":
            continue
        d = (p.get("direction") or "").upper()
        old_stop = p.get("stop")

        if action == "MOVE_STOP" and new_stop is not None:
            ns = float(new_stop)
            # только в защиту: LONG стоп вверх, SHORT вниз
            ok = ((d == "LONG" and old_stop is not None and ns > old_stop)
                  or (d == "SHORT" and old_stop is not None and ns < old_stop))
            # и не за цену
            if ok and close is not None:
                if d == "LONG" and ns >= close:
                    ok = False
                if d == "SHORT" and ns <= close:
                    ok = False
            if ok:
                p["stop"] = round(ns, 6)
                changed = True
                out(f"     └─ ✋ MOVE_STOP применён: стоп {old_stop} → {p['stop']}")
            else:
                out(f"     └─ ✋ MOVE_STOP отклонён (не в защиту / за цену): {ns}")

        elif action == "ADD" and add_lot is not None:
            try:
                al = float(add_lot)
            except (TypeError, ValueError):
                al = 0.0
            if al > 0:
                p["lot"] = round(float(p.get("lot") or 0.0) + al, 4)
                # весь пакет за Зубами (§7): тянем стоп в сейф, если Зубы
                # уже прошли вход и стоп ещё не там
                if teeth is not None and old_stop is not None:
                    if d == "LONG" and teeth > old_stop and (close is None or teeth < close):
                        p["stop"] = round(teeth, 6)
                    elif d == "SHORT" and teeth < old_stop and (close is None or teeth > close):
                        p["stop"] = round(teeth, 6)
                p["dolivok"] = int(p.get("dolivok", 0)) + 1
                changed = True
                out(f"     └─ 🔺 ADD применён: лот +{al} → {p['lot']}"
                    f" (доливок: {p['dolivok']}), стоп {p.get('stop')}")
            else:
                out("     └─ 🔺 ADD без объёма — гашу (лот не трогаю)")

    if changed:
        save_trading_state(ts)
    return changed


'''


def main():
    path = find_target()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src

    # 1. вставить helper перед def _vesti_poziciyu
    def_anchor = "def _vesti_poziciyu("
    if def_anchor not in src:
        print("[ПАТЧ] ✗ не найдена _vesti_poziciyu — файл изменён?")
        sys.exit(2)
    src = src.replace(def_anchor, HELPER + def_anchor, 1)

    # 2. вызвать применение внутри _vesti_poziciyu, сразу после того как
    #    получили r и убедились в ok. Якорь — строка budili = True.
    call_anchor = "            budili = True\n"
    if call_anchor not in src:
        print("[ПАТЧ] ✗ якорь 'budili = True' не найден — покажи _vesti_poziciyu")
        sys.exit(3)
    call_inject = (
        "            budili = True\n"
        "            # " + MARKER + ": решение хозяина → РЕАЛЬНАЯ позиция\n"
        "            try:\n"
        "                _primenit_vedenie(sid, r, pos.get('magic'), md, out)\n"
        "            except Exception as _pe:\n"
        "                out(f'     ⚠️  применение ведения не вышло: {_pe}')\n"
    )
    src = src.replace(call_anchor, call_inject, 1)

    bak = path.with_suffix(".py.bak_most_vedeniya")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Мост ведения построен.")
    print("[ПАТЧ]    Теперь ADD растит лот, MOVE_STOP двигает стоп (в защиту).")
    print("[ПАТЧ]    Решение хозяина долетает до позиции, не гаснет на табло.")
    print("[ПАТЧ]    Пирамида отдельными ногами — отдельная стройка потом.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
