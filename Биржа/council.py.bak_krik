# Биржа/council.py
# ─────────────────────────────────────────────────────────────
# ЧИСТАЯ БУДИЛКА СОВЕТА — одно место, где оживает девятка.
# ENGINE_ONE_DOOR_V1 · перенесён из -2 (studio/modules/trading/council.py)
#   на новую топологию слотов (Закон Картриджа: _slot_brain).
#
# ЗАКОН (наказ Шефа): одно место пробуждения Совета на ОБА мира.
# Раньше Совет будился в ДВУХ местах руками — в кнопке РЫНОК (с UI)
# и в тестере (своя лестница). Это и был маскарад. Теперь — одна
# лестница, без UI. Реал и тест зовут ЕЁ, отличаясь только источником
# бара (его подал движок снаружи) и тем, куда слать вести (on_event).
#
# Порядок ОДИН-В-ОДИН с кнопкой РЫНОК (ui_torg):
#   Искра → Морж → Паникёр → Ганс → Архивариус
#        → [Брут · Авантюрист · Консерватор] → Исполнитель
#
# Движок НЕ дублирует агентов — зовёт ЖИВЫЕ run_* через _slot_brain.
# Слеп к активу/ТФ.
#
# ── ОТЛИЧИЕ ОТ -2 (топология) ──
# В -2 агенты жили плоско (studio.modules.trading.morj_live) и звались
# через importlib.import_module. В новом городе они живут в слотах цехов
# (Закон Картриджа), и зовутся через _slot_brain(ceh_id, slot).мозг.
# Раскладка «кто в каком цехе/слоте» — единственное, что тут ново.
# Порядок, ворота по спуску, мягкость к сбоям — как в -2, один-в-один.
# ─────────────────────────────────────────────────────────────

import importlib.util
from pathlib import Path
from typing import Optional, Callable

_HERE = Path(__file__).resolve().parent            # Биржа/
_REPO = _HERE.parent                                # корень репо
_BRAIN_CACHE: dict = {}


def _slot_brain(ceh_id: str, slot: str):
    """
    Закон Картриджа для кода — тот же механизм, что в ui_torg.py и
    tester_express.py (_slot_brain, байт-в-байт). Мозг слота живёт в
    GRONDHEIM_CITY/Биржа/цеха/{ceh_id}/слоты/{slot}/мозг.py — не
    захардкожен списком имён. Нет файла — честная вакансия (None),
    не ошибка. Кэш на процесс.
    """
    key = (ceh_id, slot)
    if key in _BRAIN_CACHE:
        return _BRAIN_CACHE[key]
    brain_path = (_REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh_id
                 / "слоты" / slot / "мозг.py")
    if not brain_path.exists():
        _BRAIN_CACHE[key] = None
        return None
    spec = importlib.util.spec_from_file_location(
        f"_brain_{ceh_id}_{slot}", brain_path)
    if spec is None or spec.loader is None:
        _BRAIN_CACHE[key] = None
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _BRAIN_CACHE[key] = mod
    return mod


# ── РАСКЛАДКА СОВЕТА: кто в каком цехе/слоте ──
# Единственное место правды о том, где живёт каждый агент. Порядок в
# кортежах = порядок пробуждения (после Искры). ceh_id/slot идут в
# _slot_brain, run — имя функции в мозге слота.

# Искра — голова, будится первой отдельно (ворота по её спуску).
_ISKRA = ("торговый_хаос", "A01", "run_iskra")

# сенсоры после Искры — порядок как в кнопке РЫНОК
_SENSORS = [
    ("A02", "торговый_хаос", "A02", "run_morj"),
    ("A03", "торговый_хаос", "A03", "run_panikyor"),
    ("A04", "торговый_хаос", "A04", "run_hans"),
]

# Архивариус — память, без рынка (сам читает шину). Живёт в конторе.
_ARKHIV = ("A05", "контора", "архивариус", "run_arkhiv")

# трое трейдеров за столом
_TRADERS = [
    ("A06", "торговый_хаос", "A06", "run_brut", "brut"),
    ("A07", "торговый_хаос", "A07", "run_avan", "avan"),
    ("A08", "торговый_хаос", "A08", "run_cons", "cons"),
]

# Исполнитель — рука-код, замыкает петлю. Живёт в конторе.
_EXECUTOR = ("A09", "контора", "исполнитель", "run_executor")


def _call(ceh_id: str, slot: str, fn_name: str, **kw) -> dict:
    """Зовёт живой run_* агента через слот. Любой сбой — мягко, не
    роняем Совет (честная вакансия/ошибка отдаётся как {ok:False})."""
    try:
        brain = _slot_brain(ceh_id, slot)
        if brain is None:
            return {"ok": False, "error": f"{ceh_id}/{slot}: мозг ещё не в слоте"}
        fn = getattr(brain, fn_name, None)
        if fn is None:
            return {"ok": False, "error": f"{ceh_id}/{slot}: нет {fn_name}"}
        return fn(**kw) or {}
    except Exception as e:
        return {"ok": False, "error": f"{fn_name}: {e}"}


def wake_council(symbol: str, timeframe: str,
                 on_event: Optional[Callable] = None) -> dict:
    """
    БУДИТ СОВЕТ на текущем баре. symbol/timeframe — паспорт, течёт
    в каждого агента (они сами берут бар своего этажа — спуск Искры
    решает где). on_event(dict) — вести наружу (лента кабинета/тестера),
    может быть None.

    Возвращает сводку: кто что сказал + полные результаты каждого
    агента (в results, чтобы UI мог обновить свои панели). Позиции
    открывает Исполнитель (рука-код), закрывает _settle на следующем
    баре — движок этого не трогает, только будит по порядку.

    on_event получает словари вида:
      {"type": "agent", "id": "A02", "ok": True, "result": {...},
       "narrative": "...", "verdict": "APPROVED"|None}
      {"type": "council_idle", "why": "..."}   — спуск не нашёл точку
    result — ПОЛНЫЙ словарь run_* (UI берёт из него signal/market/stats).
    """
    def _emit(ev):
        if on_event:
            try:
                on_event(ev)
            except Exception:
                pass

    summary = {"woke": [], "verdicts": {}, "orders": None,
               "idle": False, "results": {}}

    # ── Искра (голова) ──
    ceh, slot, fn = _ISKRA
    ri = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)
    summary["woke"].append("A01")
    summary["results"]["A01"] = ri
    _emit({"type": "agent", "id": "A01", "ok": ri.get("ok"),
           "result": ri, "narrative": ri.get("narrative", "")})

    # ворота по спуску (COUNCIL_BY_DESCENT_V1): нашёл точку — Совет
    # собирается. нет — расходимся. Это ФАКТ спуска, не суждение
    # Искры-LLM (её t1_status идёт в Совет как голос, не как замок).
    descent = ri.get("descent", {}) or {}
    if not descent.get("found"):
        _emit({"type": "council_idle",
               "why": "спуск не нашёл точку — Совет не собирается",
               "descent": descent})
        summary["idle"] = True
        return summary

    # ── сенсоры ──
    for aid, ceh, slot, fn in _SENSORS:
        r = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)
        summary["woke"].append(aid)
        summary["results"][aid] = r
        _emit({"type": "agent", "id": aid, "ok": r.get("ok"),
               "result": r, "narrative": r.get("narrative", "")})

    # ── Архивариус (память, без рынка — сам читает шину) ──
    aid, ceh, slot, fn = _ARKHIV
    ra = _call(ceh, slot, fn)
    summary["woke"].append(aid)
    summary["results"][aid] = ra
    _emit({"type": "agent", "id": aid, "ok": ra.get("ok"),
           "result": ra, "narrative": ra.get("narrative", "")})

    # ── трое трейдеров ──
    for aid, ceh, slot, fn, pre in _TRADERS:
        r = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)
        summary["woke"].append(aid)
        summary["results"][aid] = r
        sig = r.get("signal", {}) or {}
        summary["verdicts"][aid] = sig.get(f"{pre}_verdict")
        _emit({"type": "agent", "id": aid, "ok": r.get("ok"),
               "result": r, "verdict": sig.get(f"{pre}_verdict"),
               "narrative": r.get("narrative", "")})

    # ── Исполнитель (рука-код открывает по табло) ──
    aid, ceh, slot, fn = _EXECUTOR
    rex = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)
    summary["woke"].append(aid)
    summary["results"][aid] = rex
    esig = rex.get("signal", {}) or {}
    summary["orders"] = (esig.get("final_dna", {}) or {}).get("orders_sent")
    _emit({"type": "agent", "id": aid, "ok": rex.get("ok"),
           "result": rex, "orders": summary["orders"],
           "narrative": rex.get("narrative", "")})

    return summary
