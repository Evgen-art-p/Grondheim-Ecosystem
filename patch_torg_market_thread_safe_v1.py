# -*- coding: utf-8 -*-
"""
patch_torg_market_thread_safe_v1.py
─────────────────────────────────────────────────────────────
ПОЧИНКА SLOT STACK · Биржа/ui_torg.py · run_market()

ДИАГНОЗ (моя недоделка из прошлого патча — исправляю):
  BIRZHA_UI_THREAD_SAFE_V1 чинил ТОЛЬКО run_tester_session(). Кнопка
  РЫНОК (run_market()) устроена ТОЧНО ТАК ЖЕ — council.wake_council
  крутится в фоновом потоке (run_in_executor), колбэк _on_event
  вызывается ИЗ ЭТОГО ЖЕ потока и напрямую дёргает _apply_agent_result
  (ui.*-вызовы) — тот же "slot stack ... empty".

  ХУЖЕ: в council.py у _emit() есть try/except Exception: pass —
  ошибка не просто не рисует UI, она ПРОГЛАТЫВАЕТСЯ МОЛЧА. Поэтому
  через кнопку РЫНОК не падает вообще ничего — ни отчёт, ни аватары,
  ни даже строка в консоли.

ЛЕЧЕНИЕ (тот же паттерн, что уже работает в run_tester_session):
  1. _on_event теперь ТОЛЬКО кладёт событие в потокобезопасную очередь.
  2. Разбор событий (тот же код, что раньше был внутри _on_event)
     переехал в _apply_market_event() — вызывается на ГЛАВНОМ потоке.
  3. Пока council.wake_council крутится в executor'е, главный поток
     дренирует очередь короткими проверками (get_nowait + sleep 0.05,
     если пусто) и применяет события через _apply_market_event().
  4. После завершения — добор хвоста очереди.

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_torg_market_thread_safe_v1.py

Идемпотентно: маркер BIRZHA_MARKET_THREAD_SAFE_V1 — повторный запуск
скажет "уже пропатчено" и ничего не тронет второй раз.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "ui_torg.py"
MARKER = "# BIRZHA_MARKET_THREAD_SAFE_V1 — маркер идемпотентности"

OLD_BLOCK = '''    async def run_market():
        # ── ЕДИНАЯ ДВЕРЬ СОВЕТА (ENGINE_ONE_DOOR_V1) ──
        # Раньше здесь была ручная лестница вызовов агентов — вторая
        # копия той, что жила в tester_express.py. Это был маскарад:
        # две лестницы расходятся. Теперь кабинет зовёт ТУ ЖЕ дверь
        # council.wake_council, что и тестер. Порядок, ворота по
        # спуску, обработка сбоев — одно место правды (council.py).
        #
        # ВОРОТА: раньше кабинет сам проверял t1 in (DETECTED,
        # CONFIRMED), чтобы решить, будить ли остальных. Это была
        # СТАРАЯ логика — тестер уже давно живёт по ЗАКОНУ СПУСКА
        # (COUNCIL_BY_DESCENT_V1): спуск нашёл точку = ФАКТ, Совет
        # собирается сам, t1_status — голос Искры, не замок. Теперь
        # кабинет тоже по этому закону (summary["idle"] из wake_council).
        #
        # ПОТОК: весь прогон — один run_in_executor (тот же приём,
        # что уже работает в run_tester_session/_on_progress). Колбэк
        # on_event мутирует state и дёргает update_* синхронно —
        # проверенный паттерн этого кабинета, не новый риск.
        if state["running"]:
            ui.notify("Прогон уже идёт...", type="warning")
            return
        state["running"] = True
        ui.notify("📡 Поднимаю контур, бужу Искру...", type="info")

        import council

        def _on_event(ev):
            etype = ev.get("type")

            if etype == "council_idle":
                # Спуск не нашёл точку — Искра уже отработала (ниже),
                # дальше никого не будим. Финальный notify — после
                # wake_council вернёт summary.
                return

            if etype != "agent":
                return

            aid = ev.get("id")
            r = ev.get("result", {}) or {}
            narrative = ev.get("narrative", "") or r.get("raw", "")

            _apply_agent_result(aid, r, narrative)


        try:
            summary = await asyncio.get_event_loop().run_in_executor(
                None, lambda: council.wake_council("XAUUSD", "H4", on_event=_on_event))
        except Exception as e:
            state["running"] = False
            ui.notify(f"Сбой прогона: {e}", type="negative")
            return
        state["running"] = False

        if summary.get("idle"):
            ui.notify("📣 Спуск не нашёл точку — Совет не собирается", type="info")'''

NEW_BLOCK = '''    async def run_market():
        # ── ЕДИНАЯ ДВЕРЬ СОВЕТА (ENGINE_ONE_DOOR_V1) ──
        # Раньше здесь была ручная лестница вызовов агентов — вторая
        # копия той, что жила в tester_express.py. Это был маскарад:
        # две лестницы расходятся. Теперь кабинет зовёт ТУ ЖЕ дверь
        # council.wake_council, что и тестер. Порядок, ворота по
        # спуску, обработка сбоев — одно место правды (council.py).
        #
        # ВОРОТА: раньше кабинет сам проверял t1 in (DETECTED,
        # CONFIRMED), чтобы решить, будить ли остальных. Это была
        # СТАРАЯ логика — тестер уже давно живёт по ЗАКОНУ СПУСКА
        # (COUNCIL_BY_DESCENT_V1): спуск нашёл точку = ФАКТ, Совет
        # собирается сам, t1_status — голос Искры, не замок. Теперь
        # кабинет тоже по этому закону (summary["idle"] из wake_council).
        #
        # BIRZHA_MARKET_THREAD_SAFE_V1: council.wake_council крутится
        # в фоновом потоке (run_in_executor) — тот же слот-стек NiceGUI
        # туда не копируется, что уже чинили в run_tester_session.
        # Колбэк _on_event раньше дёргал _apply_agent_result НАПРЯМУЮ
        # из фонового потока — "slot stack ... empty", да ещё и
        # ПРОГЛОЧЕННЫЙ МОЛЧА через try/except в council._emit(). Теперь
        # _on_event только кладёт событие в очередь; разбор — на
        # главном потоке (_apply_market_event, дренаж ниже), как в
        # тестере.
        if state["running"]:
            ui.notify("Прогон уже идёт...", type="warning")
            return
        state["running"] = True
        ui.notify("📡 Поднимаю контур, бужу Искру...", type="info")

        import council
        import queue as _queue_mod

        _mkt_queue: "_queue_mod.Queue" = _queue_mod.Queue()

        def _on_event(ev):
            _mkt_queue.put(ev)

        def _apply_market_event(ev):
            """Та же логика, что раньше жила прямо в _on_event — теперь
            вызывается на главном потоке, где слот-контекст клиента жив."""
            etype = ev.get("type")

            if etype == "council_idle":
                return

            if etype != "agent":
                return

            aid = ev.get("id")
            r = ev.get("result", {}) or {}
            narrative = ev.get("narrative", "") or r.get("raw", "")

            try:
                _apply_agent_result(aid, r, narrative)
            except Exception as e:
                print(f"[TORG·MARKET] _apply_agent_result сбой ({aid}): {e}")

        try:
            loop = asyncio.get_event_loop()
            _market_future = loop.run_in_executor(
                None, lambda: council.wake_council("XAUUSD", "H4", on_event=_on_event))
            # Дренаж очереди на ГЛАВНОМ потоке, пока wake_council крутится.
            while not _market_future.done():
                drained_any = False
                while True:
                    try:
                        _ev = _mkt_queue.get_nowait()
                    except _queue_mod.Empty:
                        break
                    drained_any = True
                    _apply_market_event(_ev)
                if not drained_any:
                    await asyncio.sleep(0.05)
            summary = await _market_future
            # Добор хвоста очереди — событие могло прийти между
            # последней проверкой .done() и фактическим концом потока.
            while True:
                try:
                    _ev = _mkt_queue.get_nowait()
                except _queue_mod.Empty:
                    break
                _apply_market_event(_ev)
        except Exception as e:
            state["running"] = False
            ui.notify(f"Сбой прогона: {e}", type="negative")
            return
        state["running"] = False

        if summary.get("idle"):
            ui.notify("📣 Спуск не нашёл точку — Совет не собирается", type="info")'''


def _patch():
    if not TARGET.exists():
        print(f"[ПАТЧ] ❌ Не найден {TARGET} — запусти из корня репо.")
        raise SystemExit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ ui_torg.py уже пропатчен (BIRZHA_MARKET_THREAD_SAFE_V1) — пропускаю.")
        return False

    if OLD_BLOCK in src:
        src = src.replace(OLD_BLOCK, NEW_BLOCK)
        print("[ПАТЧ] 🔧 run_market(): очередь вместо прямых ui.*-вызовов из потока")
    elif NEW_BLOCK in src:
        print("[ПАТЧ] ↺ run_market() уже пропатчен")
        return False
    else:
        print("[ПАТЧ] ⚠️  тело run_market() не совпало один-в-один — "
              "файл менялся вручную, проверь функцию сам.")
        return False

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] 💾 ui_torg.py сохранён.")
    return True


def main():
    print("═" * 62)
    print("  ПОЧИНКА RUN_MARKET · BIRZHA_MARKET_THREAD_SAFE_V1")
    print("═" * 62)
    _patch()
    print("═" * 62)
    print("  ✅ ГОТОВО. Перезапусти приложение (python main.py или как у тебя")
    print("     запускается студия) — файл поменялся на диске, старый процесс")
    print("     этого не увидит, пока не перезапустишь.")
    print("     Проверка: жми РЫНОК в режиме РЕАЛ — правая панель, аватары")
    print("     и приборы должны обновляться на каждом агенте.")
    print("═" * 62)


if __name__ == "__main__":
    main()
