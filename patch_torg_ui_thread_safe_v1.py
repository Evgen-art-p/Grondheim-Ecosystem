# -*- coding: utf-8 -*-
"""
patch_torg_ui_thread_safe_v1.py
─────────────────────────────────────────────────────────────
ПОЧИНКА SLOT STACK · Биржа/ui_torg.py · run_tester_session()

ДИАГНОЗ (проверено чтением живого кода, не по памяти):
  Тестер крутит тяжёлый перебор истории в фоновом потоке:
      await loop.run_in_executor(None, lambda: run_tester(..., on_progress=_on_progress))
  Колбэк _on_progress вызывается СИНХРОННО ИЗНУТРИ этого потока
  (tester_express.py дёргает его напрямую). Раньше _on_progress
  сам делал всю отрисовку — state["chat_history"].append(...),
  update_chat_display(), ui.notify(), update_viewer() и т.д.

  NiceGUI отслеживает, в какой контейнер класть новый элемент,
  через контекстную переменную (слот-стек), привязанную к asyncio-
  задаче конкретного клиента. run_in_executor не копирует contextvars
  в поток пула (это не asyncio.to_thread) — поэтому там, где раньше
  жила отрисовка, слот-стек пуст. Отсюда "The current slot cannot be
  determined because the slot stack for this task is empty" на
  КАЖДОМ агенте теста. Цикл не падает только потому что уже был
  обёрнут в try/except в _on_progress — но правая панель "Отчёты"
  оставалась пустой: update_viewer() тоже валился молча.

ЛЕЧЕНИЕ:
  1. _on_progress теперь ТОЛЬКО кладёт событие в потокобезопасную
     очередь (queue.Queue.put — не требует UI-контекста вообще).
     Никакого ui.*-кода в фоновом потоке больше не выполняется.
  2. Вся прежняя логика разбора событий (report/verdict/trade/
     progress) переехала в _apply_progress_event() — не переписана
     по сути, просто вызывается из другого места.
  3. Пока executor-задача крутится, ГЛАВНЫЙ поток (та же корутина
     run_tester_session, где слот-контекст этого клиента жив)
     вычитывает очередь короткими проверками (get_nowait + короткий
     sleep, если очередь пуста) и применяет каждое событие через
     _apply_progress_event() — здесь ui.* работает штатно.
     После завершения executor-задачи — добор хвоста очереди
     (событие могло прийти между последней проверкой .done() и
     фактическим концом потока).

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_torg_ui_thread_safe_v1.py

Идемпотентно: маркер BIRZHA_UI_THREAD_SAFE_V1 — повторный запуск
скажет "уже пропатчено" и ничего не тронет второй раз.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "ui_torg.py"
MARKER = "# BIRZHA_UI_THREAD_SAFE_V1 — маркер идемпотентности"

# ── 1. Добавляем import queue рядом с asyncio ──────────────────
OLD_IMPORTS = """import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import asyncio

from nicegui import ui, app, events"""

NEW_IMPORTS = """import sys
import json
import queue
from pathlib import Path
from datetime import datetime, timezone
import asyncio

from nicegui import ui, app, events"""

# ── 2. Полная замена _on_progress + добавление очереди/дренажа ──

OLD_BLOCK = '''        def _on_progress(msg):
            if isinstance(msg, dict) and msg.get("type") == "report":
                aid = msg.get("agent")
                narrative = msg.get("narrative", "")
                result = msg.get("result")
                if aid and narrative and result is not None:
                    # ENGINE_ONE_DOOR_V1 (память чата): result присутствует —
                    # тестер теперь несёт ПОЛНЫЙ словарь run_* агента, не
                    # только голос. Зовём ТУ ЖЕ функцию, что и РЫНОК —
                    # заполнит *_last_run, чтобы чат с агентом после
                    # ТЕСТЕРА знал, что тот только что видел, а не отвечал
                    # честно, но неверно "рынок не запускали".
                    if aid == "A01":
                        state["reports"] = {}
                        state["active_agent"] = None
                        try:
                            update_avatar_states()
                        except Exception:
                            pass
                    try:
                        _apply_agent_result(aid, result, narrative)
                    except Exception as e:
                        print(f"[TORG·TESTER] _apply_agent_result сбой ({aid}): {e}")
                    return
                if aid and narrative:
                    if aid == "A01":
                        state["reports"] = {}
                        state["active_agent"] = None
                        try:
                            update_avatar_states()
                        except Exception:
                            pass
                    state["reports"][aid] = narrative
                    state["active_agent"] = aid
                    label = _agent_label(roster, aid)
                    try:
                        update_viewer(f"# {label} ({aid})\\n\\n{narrative}")
                        update_avatar()
                        update_vitals()
                        update_avatar_states()
                    except Exception:
                        pass
                    status = msg.get("status", "")
                    tail = f" · {status}" if status else ""
                    state["chat_history"].append({
                        "role": "assistant", "agent": aid,
                        "content": f"отработал{tail}. Отчёт справа."})
                    try:
                        update_chat_display()
                    except Exception:
                        pass
                return
            if isinstance(msg, dict) and msg.get("type") == "verdict":
                txt = msg.get("text", "")
                hint = msg.get("hint", "")
                state["chat_history"].append({
                    "role": "assistant", "agent": "РАЗВИЛКА",
                    "content": f"📊 {txt}\\n→ {hint}"})
                try:
                    update_chat_display()
                except Exception:
                    pass
                return
            if isinstance(msg, dict) and msg.get("type") == "trade":
                state["chat_history"].append({
                    "role": "assistant", "agent": "СДЕЛКА",
                    "content": msg.get("text", "")})
                try:
                    update_chat_display()
                except Exception:
                    pass
                return
            if isinstance(msg, dict) and msg.get("type") == "progress":
                state["chat_history"].append({
                    "role": "assistant", "agent": "···",
                    "content": msg.get("text", "")})
                try:
                    update_chat_display()
                except Exception:
                    pass
                return
            print(f"[TORG·TESTER] {msg}")

        def _should_stop():
            return state.get("stop_requested", False)

        try:
            from tester_express import run_tester
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: run_tester(
                    csv_path=path, symbol=symbol, timeframe=tf,
                    n_signals=n, on_progress=_on_progress,
                    should_stop=_should_stop,
                )
            )
        except Exception as e:
            ui.notify(f"Тестер упал: {e}", type="negative")
            state["chat_history"].append({
                "role": "assistant", "agent": "SYSTEM",
                "content": f"⚠️ Тестер упал: {e}"})
            update_chat_display()
        finally:
            state["tester_running"] = False
            stopped = state.get("stop_requested", False)
            state["stop_requested"] = False'''

NEW_BLOCK = '''        # BIRZHA_UI_THREAD_SAFE_V1: потокобезопасная очередь событий.
        # _on_progress зовётся ИЗ ФОНОВОГО ПОТОКА (run_in_executor) —
        # слот-контекст NiceGUI туда не копируется, поэтому там нельзя
        # трогать ui.* НИКАК. Колбэк только кладёт событие в очередь;
        # разбор и вся отрисовка — в _apply_progress_event(), которую
        # зовёт ГЛАВНЫЙ поток (см. цикл дренажа ниже).
        _evt_queue: "queue.Queue" = queue.Queue()

        def _on_progress(msg):
            _evt_queue.put(msg)

        def _apply_progress_event(msg):
            """Разбор событий тестера — та же логика, что раньше жила
            прямо в _on_progress, просто теперь исполняется на главном
            потоке (слот-контекст этого клиента жив, ui.* работает)."""
            if isinstance(msg, dict) and msg.get("type") == "report":
                aid = msg.get("agent")
                narrative = msg.get("narrative", "")
                result = msg.get("result")
                if aid and narrative and result is not None:
                    # ENGINE_ONE_DOOR_V1 (память чата): result присутствует —
                    # тестер теперь несёт ПОЛНЫЙ словарь run_* агента, не
                    # только голос. Зовём ТУ ЖЕ функцию, что и РЫНОК —
                    # заполнит *_last_run, чтобы чат с агентом после
                    # ТЕСТЕРА знал, что тот только что видел, а не отвечал
                    # честно, но неверно "рынок не запускали".
                    if aid == "A01":
                        state["reports"] = {}
                        state["active_agent"] = None
                        try:
                            update_avatar_states()
                        except Exception:
                            pass
                    try:
                        _apply_agent_result(aid, result, narrative)
                    except Exception as e:
                        print(f"[TORG·TESTER] _apply_agent_result сбой ({aid}): {e}")
                    return
                if aid and narrative:
                    if aid == "A01":
                        state["reports"] = {}
                        state["active_agent"] = None
                        try:
                            update_avatar_states()
                        except Exception:
                            pass
                    state["reports"][aid] = narrative
                    state["active_agent"] = aid
                    label = _agent_label(roster, aid)
                    try:
                        update_viewer(f"# {label} ({aid})\\n\\n{narrative}")
                        update_avatar()
                        update_vitals()
                        update_avatar_states()
                    except Exception:
                        pass
                    status = msg.get("status", "")
                    tail = f" · {status}" if status else ""
                    state["chat_history"].append({
                        "role": "assistant", "agent": aid,
                        "content": f"отработал{tail}. Отчёт справа."})
                    try:
                        update_chat_display()
                    except Exception:
                        pass
                return
            if isinstance(msg, dict) and msg.get("type") == "verdict":
                txt = msg.get("text", "")
                hint = msg.get("hint", "")
                state["chat_history"].append({
                    "role": "assistant", "agent": "РАЗВИЛКА",
                    "content": f"📊 {txt}\\n→ {hint}"})
                try:
                    update_chat_display()
                except Exception:
                    pass
                return
            if isinstance(msg, dict) and msg.get("type") == "trade":
                state["chat_history"].append({
                    "role": "assistant", "agent": "СДЕЛКА",
                    "content": msg.get("text", "")})
                try:
                    update_chat_display()
                except Exception:
                    pass
                return
            if isinstance(msg, dict) and msg.get("type") == "progress":
                state["chat_history"].append({
                    "role": "assistant", "agent": "···",
                    "content": msg.get("text", "")})
                try:
                    update_chat_display()
                except Exception:
                    pass
                return
            print(f"[TORG·TESTER] {msg}")

        def _should_stop():
            return state.get("stop_requested", False)

        try:
            from tester_express import run_tester
            loop = asyncio.get_event_loop()
            _tester_future = loop.run_in_executor(
                None,
                lambda: run_tester(
                    csv_path=path, symbol=symbol, timeframe=tf,
                    n_signals=n, on_progress=_on_progress,
                    should_stop=_should_stop,
                )
            )
            # Дренаж очереди на ГЛАВНОМ потоке, пока фоновый прогон
            # крутится — здесь слот-контекст этого клиента жив.
            while not _tester_future.done():
                drained_any = False
                while True:
                    try:
                        _msg = _evt_queue.get_nowait()
                    except queue.Empty:
                        break
                    drained_any = True
                    _apply_progress_event(_msg)
                if not drained_any:
                    await asyncio.sleep(0.05)
            await _tester_future
            # Добор хвоста: событие могло прийти между последней
            # проверкой .done() и фактическим завершением потока.
            while True:
                try:
                    _msg = _evt_queue.get_nowait()
                except queue.Empty:
                    break
                _apply_progress_event(_msg)
        except Exception as e:
            ui.notify(f"Тестер упал: {e}", type="negative")
            state["chat_history"].append({
                "role": "assistant", "agent": "SYSTEM",
                "content": f"⚠️ Тестер упал: {e}"})
            update_chat_display()
        finally:
            state["tester_running"] = False
            stopped = state.get("stop_requested", False)
            state["stop_requested"] = False'''


def _patch_source() -> bool:
    if not TARGET.exists():
        print(f"[ПАТЧ] ❌ Не найден {TARGET} — запусти из корня репо.")
        raise SystemExit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ ui_torg.py уже пропатчен (BIRZHA_UI_THREAD_SAFE_V1) — пропускаю.")
        return False

    changed = 0

    if OLD_IMPORTS in src:
        src = src.replace(OLD_IMPORTS, NEW_IMPORTS)
        changed += 1
        print("[ПАТЧ] 🔧 добавлен import queue")
    elif NEW_IMPORTS in src:
        print("[ПАТЧ] ↺ import queue уже на месте")
    else:
        print("[ПАТЧ] ⚠️  блок импортов не совпал — проверь вручную")

    if OLD_BLOCK in src:
        src = src.replace(OLD_BLOCK, NEW_BLOCK)
        changed += 1
        print("[ПАТЧ] 🧹 run_tester_session: очередь вместо прямых ui.*-вызовов из потока")
    elif NEW_BLOCK in src:
        print("[ПАТЧ] ↺ run_tester_session уже пропатчен")
    else:
        print("[ПАТЧ] ⚠️  тело run_tester_session не совпало один-в-один — "
              "файл менялся вручную, проверь функцию сам.")

    if changed == 0:
        print("[ПАТЧ] ⚠️  ничего не изменилось — сверь файл вручную.")
        return False

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] 💾 ui_torg.py сохранён (изменений: {changed}).")
    return True


def main():
    print("═" * 62)
    print("  ПОЧИНКА SLOT STACK · BIRZHA_UI_THREAD_SAFE_V1")
    print("═" * 62)
    _patch_source()
    print("═" * 62)
    print("  ✅ ГОТОВО. Проверь: запусти ТЕСТЕР — правая панель")
    print("     'Отчёты агентов' должна заполняться на каждом агенте.")
    print("═" * 62)


if __name__ == "__main__":
    main()
