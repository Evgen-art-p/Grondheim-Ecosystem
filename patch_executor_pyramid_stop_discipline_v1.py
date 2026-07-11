# -*- coding: utf-8 -*-
"""
patch_executor_pyramid_stop_discipline_v1.py
────────────────────────────────────────────────────────────────────
ЧИНИТ (разбор канона Котина/Уильямса — «ведение позиции», «реверсивная
пирамида», 2026-07-11): «рука ведущая» (_manage_positions_from_table,
Исполнитель A09) исполняла MOVE_STOP и ADD буквально, любым числом от
LLM, без единой инженерной страховки. Философия и промты трейдеров
знают правильную форму ведения — код доверял им вслепую.

ПЕРВОИСТОЧНИК (Trading Chaos / реверсивная пирамида Уильямса):
  · Трейлинг-стоп — «ключевая техника выхода», двигается ВДОЛЬ тренда:
    только в защитную сторону, никогда не отступает назад. Отступивший
    стоп — не трейлинг, а ошибка.
  · Реверсивная пирамида: первый вход — минимальный объём; ПЕРВЫЙ долив
    может быть агрессивным скачком (подтверждение Wiseman 2); КАЖДЫЙ
    СЛЕДУЮЩИЙ долив — не крупнее предыдущего («gradually reducing the
    funds you add on»). Форма пирамиды: узкое основание входа, широкий
    первый долив, дальше на убыль — не хаотичные числа.
  · Золотое правило пирамидинга: «with every new position you add, you
    MUST adjust your stop-loss on the entire position» — долив без
    подтяжки стопа запрещён.

ТРИ ПРАВКИ В _manage_positions_from_table:

  1) MOVE_STOP: новый стоп проверяется на монотонность по стороне
     позиции (LONG — только вверх/не ниже старого; SHORT — только
     вниз/не выше старого). Ослабляющий стоп молча отклоняется
     (позиция остаётся на старом, изменение не пишется в летопись).

  2) ADD: со ВТОРОГО долива (pyramids >= 1 до этого вызова) требуем
     add_lot <= размера предыдущего долива (pos["last_add_lot"]).
     Первый долив (pyramids == 0) не ограничен — это разрешённый
     каноном агрессивный скачок. Нарушающий форму долив отклоняется.

  3) СВЯЗКА: при исполнении ADD, если трейдер тем же ходом назвал ещё
     и new_stop — подтягиваем стоп В ТОЙ ЖЕ операции (той же проверкой
     монотонности из п.1), а не ждём отдельного хода MOVE_STOP.

Идемпотентно. Маркер EXECUTOR_PYRAMID_STOP_DISCIPLINE_V1. Бэкап рядом
(.bak). Запуск из КОРНЯ репы (Windows/PowerShell):
    python patch_executor_pyramid_stop_discipline_v1.py
"""
from __future__ import annotations
import sys
from pathlib import Path

MARKER = "EXECUTOR_PYRAMID_STOP_DISCIPLINE_V1"
TARGET = (Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "контора" /
          "слоты" / "исполнитель" / "мозг.py")

OLD = '''def _manage_positions_from_table(traders: dict) -> list:
    """
    Для каждого трейдера с открытой позицией исполняет его действие
    ведения над trading_state["positions"]. Возвращает список изменений
    (для летописи). Открытие (ENTER) — не здесь, это рука открывающая.
    """
    from hooks import load_trading_state, save_trading_state
    tstate = load_trading_state()
    positions = tstate.get("positions", []) or []
    if not positions:
        return []

    changed = []
    dirty = False
    for key in ("brut", "avan", "cons"):
        v = traders.get(key, {})
        action = (v.get("action") or "").upper().strip()
        if action in ("", "ENTER", "WAIT", "HOLD"):
            continue
        magic = MAGIC[key]
        pos = next((p for p in positions
                    if p.get("magic") == magic and p.get("status") == "OPEN"), None)
        if not pos:
            continue

        if action == "MOVE_STOP":
            ns = v.get("new_stop")
            if ns is None:
                continue
            old = pos.get("stop")
            pos["stop"] = ns
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "MOVE_STOP",
                            "from": old, "to": ns})

        elif action == "ADD":
            al = v.get("add_lot")
            if al is None or al <= 0:
                continue
            old_lot = pos.get("lot") or 0
            pos["lot"] = round(old_lot + al, 4)
            pos.setdefault("pyramids", 0)
            pos["pyramids"] += 1
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "ADD",
                            "add_lot": al, "lot_now": pos["lot"]})

        elif action == "CLOSE":
            pos["manual_close"] = True
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "CLOSE"})
'''

NEW = '''# ''' + MARKER + '''
def _stop_tightens(direction: str, old_stop, new_stop) -> bool:
    """
    Трейлинг-стоп (первоисточник Уильямса) — только в защитную сторону.
    LONG: новый стоп не ниже старого. SHORT: новый стоп не выше старого.
    Старого стопа нет (первое выставление) — пропускаем как валидное.
    """
    if old_stop is None or new_stop is None:
        return True
    if (direction or "").upper() == "LONG":
        return new_stop >= old_stop
    return new_stop <= old_stop  # SHORT


def _manage_positions_from_table(traders: dict) -> list:
    """
    Для каждого трейдера с открытой позицией исполняет его действие
    ведения над trading_state["positions"]. Возвращает список изменений
    (для летописи). Открытие (ENTER) — не здесь, это рука открывающая.

    ''' + MARKER + ''': стоп двигается только по канону трейлинга
    (никогда не ослабляется), долив идёт формой реверсивной пирамиды
    (со второго — не крупнее предыдущего), долив со стопом в одном
    ходу подтягивает и то, и другое разом.
    """
    from hooks import load_trading_state, save_trading_state
    tstate = load_trading_state()
    positions = tstate.get("positions", []) or []
    if not positions:
        return []

    changed = []
    dirty = False
    for key in ("brut", "avan", "cons"):
        v = traders.get(key, {})
        action = (v.get("action") or "").upper().strip()
        if action in ("", "ENTER", "WAIT", "HOLD"):
            continue
        magic = MAGIC[key]
        pos = next((p for p in positions
                    if p.get("magic") == magic and p.get("status") == "OPEN"), None)
        if not pos:
            continue

        if action == "MOVE_STOP":
            ns = v.get("new_stop")
            if ns is None:
                continue
            old = pos.get("stop")
            if not _stop_tightens(pos.get("direction"), old, ns):
                changed.append({"trader": TRADER_NAME[key], "action": "MOVE_STOP_REJECTED",
                                "from": old, "attempted": ns,
                                "why": "ослабляет стоп — против канона трейлинга"})
                continue
            pos["stop"] = ns
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "MOVE_STOP",
                            "from": old, "to": ns})

        elif action == "ADD":
            al = v.get("add_lot")
            if al is None or al <= 0:
                continue
            prior_pyramids = pos.get("pyramids", 0)
            last_add = pos.get("last_add_lot")
            if prior_pyramids >= 1 and last_add is not None and al > last_add:
                changed.append({"trader": TRADER_NAME[key], "action": "ADD_REJECTED",
                                "attempted": al, "last_add_lot": last_add,
                                "why": "долив крупнее предыдущего — против формы "
                                       "реверсивной пирамиды (Уильямс)"})
                continue
            old_lot = pos.get("lot") or 0
            pos["lot"] = round(old_lot + al, 4)
            pos["pyramids"] = prior_pyramids + 1
            pos["last_add_lot"] = al
            dirty = True
            add_change = {"trader": TRADER_NAME[key], "action": "ADD",
                          "add_lot": al, "lot_now": pos["lot"]}
            # золотое правило пирамидинга: долив без подтяжки стопа не
            # бывает — если трейдер тем же ходом назвал new_stop, тянем
            # его сюда же, той же проверкой монотонности.
            ns = v.get("new_stop")
            if ns is not None:
                old_stop = pos.get("stop")
                if _stop_tightens(pos.get("direction"), old_stop, ns):
                    pos["stop"] = ns
                    add_change["stop_from"] = old_stop
                    add_change["stop_to"] = ns
                else:
                    add_change["stop_move_rejected"] = ns
            changed.append(add_change)

        elif action == "CLOSE":
            pos["manual_close"] = True
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "CLOSE"})
'''


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
        print("✗ не нашёл ожидаемое тело _manage_positions_from_table.")
        print("  Возможно, функция уже правилась вручную. Проверь "
              "исполнитель/мозг.py — MOVE_STOP/ADD блоки.")
        return 2

    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")
    else:
        print(f"• бэкап уже был: {bak} (не перезаписываю)")

    TARGET.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"✓ {TARGET}: рука ведущая теперь блюдёт трейлинг и форму "
          f"реверсивной пирамиды.")
    print(f"  Маркер идемпотентности: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
