# -*- coding: utf-8 -*-
"""
patch_council_one_door_v1.py
-----------------------------------------------------------
ENGINE_ONE_DOOR_V1 -- единая дверь пробуждения Совета.

ПРОБЛЕМА (диагноз этой сессии):
  В -2 был council.py -- ОДНА дверь wake_council(), которую звали и
  кабинет (кнопка РЫНОК), и тестер. Сделан специально, чтобы убить
  маскарад "Совет будится в двух местах руками". При переносе в новый
  город council.py потерялся, и лестница расплодилась на копии:
    - ui_torg.py (Биржа/) -- своя ручная лестница run_iskra..run_executor
    - tester_express.py   -- своя ВТОРАЯ копия той же лестницы
    - hooks.run_live_council() -- честная ЗАГЛУШКА (не зовёт агентов)
  Две руками писанные копии расходятся -> "неадекват" на прогонах.

ЧТО ДЕЛАЕТ ЭТОТ ПАТЧ (фаза 1):
  1. Рождает Биржа/council.py -- единую дверь (порт из -2, адаптирован
     под топологию слотов: _slot_brain вместо import_module).
  2. Перезаписывает Биржа/tester_express.py -- его ручная лестница
     заменена вызовом council.wake_council(on_event=...). Стриминг
     отчёта/лента сделок/settle-по-gap-барам СОХРАНЕНЫ (снаружи двери).
  3. Удаляет КОРНЕВОЙ ui_torg.py (дубль-двойник, 23КБ TORG_STOL_V2) --
     он в тени (Биржа/ впереди корня в sys.path), но опасен: при смене
     порядка sys.path город тихо подхватит недостроенную версию.
     БЭКАП кладётся в _ARCHIVE/ (ничего не теряем безвозвратно).

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ (следующий заход):
  - НЕ трогает Биржа/ui_torg.py (кабинет): его лестница сплетена с
    живым UI (пузырьки, аватары, notify). Переключение на wake_council
    через on_event -- отдельно, аккуратно, чтобы не онеметь кабинет.
  - НЕ трогает hooks.run_live_council() (боевой путь, реальные деньги).

Идемпотентно: повторный запуск просто перезапишет тем же содержимым.
Бэкап корневого ui_torg делается только если файл ещё на месте.

Запуск из КОРНЯ репозитория:
    python patch_council_one_door_v1.py

Проверено (см. отчёт в чате): council.wake_council зовёт девятку в
верном порядке (Искра->..->Исполнитель), ворота по спуску работают
(спуск не нашёл -> только Искра, Совет не собрался), колбэк ловит все
события. tester_express.py проходит компиляцию, осколков старой
лестницы не осталось.
"""

import sys
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BIRZHA = REPO_ROOT / "Биржа"

FILES = {}
FILES['Биржа/council.py'] = r'''# Биржа/council.py
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
'''

FILES['Биржа/tester_express.py'] = r'''# studio/modules/trading/tester_express.py
# ─────────────────────────────────────────────────────────────
# ЭКСПРЕСС-ТЕСТЕР — живой Совет на истории (CSV), без MT5
# TESTER_EXPRESS_V1 · 2026-06-18
#
# ЧТО ЭТО. Не вторая реализация трейдеров (та разойдётся с живой).
# Это МИКРОФОН: берёт ЖИВЫХ агентов (Искра, Морж, Ганс, Паникёр,
# Архивариус, Брут — те самые *_live.py) и кормит их историей из CSV
# вместо терминала. Печатает ИХ ПОДЛИННЫЕ голоса (narrative) дословно.
# Ни одного слова за них. Тестер — микрофон, не сценарист.
#
# КАК НАХОДИТ. Не Шеф тычет бар (вдруг ошибётся). Кухня САМА ищет:
# крутит историю бар за баром ДЕШЁВОЙ Искрой; на срабатывании Искры
# (DETECTED/CONFIRMED) будит ПОЛНЫЙ Совет на этом баре и печатает их
# разговор. Ловит N срабатываний — стоп. Так проверяется КУХНЯ:
# найдёт ли цех сам то, что по канону должен найти.
#
# КАК КОРМИТ. Монки-патч mt5_feed._fetch на время прогона: вместо
# терминала отдаёт срез CSV до текущего бара (тот же формат (bars,
# point), агенты подмены не замечают). Снял патч — всё как было.
# MT5 не нужен: point берём из таблички для теста (ядро не трогаем).
#
# ЗАПУСК (из корня репы):
#   python -m studio.modules.trading.tester_express <csv> <symbol> <tf> [--signals N]
# Пример:
#   python -m studio.modules.trading.tester_express test_data/XAUUSD_H4.csv XAUUSD H4 --signals 1
# ─────────────────────────────────────────────────────────────

import sys
import argparse
import importlib.util
from pathlib import Path
from datetime import datetime

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent   # TESTER_EXPRESS_CARTRIDGE_V1: корень репо, для поиска мозгов
_BRAIN_CACHE: dict = {}


def _slot_brain(ceh_id: str, slot: str):
    """TESTER_EXPRESS_CARTRIDGE_V1: Закон Картриджа для кода — тот же
    механизм, что в ui_torg.py (_slot_brain). Мозг слота живёт в
    GRONDHEIM_CITY/Биржа/цеха/{ceh_id}/слоты/{slot}/мозг.py — не
    захардкожен списком имён, цех сам говорит, что там лежит. Нет
    файла — честная вакансия (None), не ошибка. Кэш на процесс."""
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
# TESTER_TRADE_FEED_V1 · лента сделок: открытие и закрытие видны в кабинете
# TESTER_STERILE_V1 · бэктест по умолчанию НЕ калечит ДНК (--learn чтобы учить)
# TESTER_CLEAN_TABLE_V1 · чистый стол на старте + settle на каждом баре
# TESTER_SETTLE_GAPS_V1 · settle прокатывается по всем барам между кандидатами
# TESTER_SETTLE_FULL_WINDOW_V1 · ведение кормит settle полным окном 300 (честный exit_bell)
# TESTER_TO_CABINET_V1 · кран+caught+развилка/прогресс через on_progress в кабинет


# ── point для теста (ТОЛЬКО здесь, ядро остаётся слепым к тикеру) ──
# Это не возврат POINT_MAP в ядро — это локальный костыль тестера,
# чтобы не поднимать MT5 ради одного числа. Не знаешь свой — кидай --point.
_TEST_POINT = {
    "XAUUSD": 0.01,   "XAGUSD": 0.001,
    "EURUSD": 0.00001, "GBPUSD": 0.00001, "USDJPY": 0.001,
    "AUDUSD": 0.00001, "USDCHF": 0.00001, "USDCAD": 0.00001,
    "BTCUSD": 0.01,   "ETHUSD": 0.01,
}


def _resolve_point(symbol: str, override) -> float:
    if override:
        return float(override)
    p = _TEST_POINT.get(symbol.upper())
    if p is None:
        print(f"⚠️  point для {symbol} неизвестен тестеру. Укажи --point "
              f"(золото 0.01, форекс 0.00001, JPY 0.001).")
        sys.exit(1)
    return p


def _bar(line_dt: str) -> str:
    """Короткая дата бара для лога."""
    return line_dt or "?"


# ── TESTER_CLEAN_TABLE_V1: чистый стол + закрытие позиций в тестере ──
def _clean_table_for_symbol(symbol):
    """Сносит стол прогоняемого символа ПЕРЕД заходом. Бэктест
    начинается с чистого листа: ни чужих позиций, ни старых
    вердиктов. Позиции без поля symbol (старая эпоха) — сносим
    тоже: доверять им нельзя, они из другого прогона/актива."""
    from hooks import (
        load_trading_state, save_trading_state)
    t = load_trading_state()
    sym = (symbol or '').upper()
    before = t.get('positions', []) or []
    # держим только ЧУЖИЕ символы с явной меткой; своё и безымянное сносим
    kept = [p for p in before
            if p.get('symbol') and p.get('symbol', '').upper() != sym]
    dropped = len(before) - len(kept)
    t['positions'] = kept
    # сбрасываем вердикты трейдеров и состояние Искры на чистый лист
    for k in ('brut', 'avan', 'cons'):
        t[k] = {}
    t['iskra'] = {'t1_status': 'NOT_FOUND',
                  'zero_point_price': None, 'history_dna': ''}
    save_trading_state(t)
    if dropped:
        print(f'[TESTER·CLEAN] снёс {dropped} позиций прошлой эпохи '
              f'(символ {sym} и безымянные) — стол чист')
    return dropped


def _settle_bar(window, symbol, timeframe, point):
    """Зовёт hooks._settle_positions на текущем баре — рынок
    закрывает позиции по стопу/колоколу САМ, как в живом
    on_before_run. В тестерном пути этого вызова не было —
    позиции жили вечно. Собираем мини-state с market_data бара."""
    from williams_core import build_market_data
    from hooks import (
        _settle_positions, load_trading_state)
    md = build_market_data(window, symbol=symbol,
                           timeframe=timeframe, point=point)
    if not md:
        return
    positions = load_trading_state().get('positions', []) or []
    if not positions:
        return
    st = {'chain_data': {'market_data': md,
                         'open_positions': positions}}
    try:
        _settle_positions(st)   # закрывает по стопу/колоколу, пишет pnl_r
    except Exception as _e:
        print(f'[TESTER·SETTLE] пропуск ({_e})')


# ── TESTER_TRADE_FEED_V1: лента сделок (открытие/закрытие в кабинет) ──
def _table_snapshot():
    """Множество magic открытых позиций сейчас — для сравнения
    до/после (что открылось, что закрылось)."""
    try:
        from hooks import load_trading_state
        return {p.get('magic'): dict(p)
                for p in load_trading_state().get('positions', []) or []
                if p.get('status') == 'OPEN'}
    except Exception:
        return {}


def _read_last_closures(n=10):
    """Последние n закрытых сделок из trading_pnl.jsonl —
    settle уже записал туда pnl_r, closed_at, reason."""
    from pathlib import Path as _P
    import json as _j
    p = _P('economy/data/trading_pnl.jsonl')
    if not p.exists():
        return []
    try:
        lines = p.read_text(encoding='utf-8').strip().splitlines()
        out = []
        for ln in lines[-n:]:
            try:
                out.append(_j.loads(ln))
            except Exception:
                pass
        return out
    except Exception:
        return []


def run_tester(csv_path: str, symbol: str, timeframe: str,
               n_signals: int = 1, point_override=None,
               warmup: int = 60, loose: bool = False,
               on_progress=None, should_stop=None,  # TESTER_HANDLES_V1
               learn: bool = False):  # TESTER_STERILE_V1: умолчание — смотреть
    from williams_core import read_mt5_csv, build_market_data
    import mt5_feed

    # РУЛЬ (биржа слушает ход / прерывает перебор).  # TESTER_HANDLES_V1
    def _emit(msg):
        if on_progress:
            try:
                on_progress(msg)
            except Exception:
                pass
    def _stop_requested():
        if should_stop:
            try:
                return bool(should_stop())
            except Exception:
                return False
        return False

    def _emit_report(agent, narrative, status=""):  # TESTER_REPORTS_V1
        """Структурный отчёт агента наружу — биржа разложит по аватарам."""
        if on_progress and narrative:
            try:
                on_progress({"type": "report", "agent": agent,
                             "narrative": str(narrative).strip(),
                             "status": status})
            except Exception:
                pass

    point = _resolve_point(symbol, point_override)

    full_path = csv_path if Path(csv_path).is_absolute() else str(_HERE / csv_path)
    if not Path(full_path).exists():
        # пробуем ещё от корня запуска
        if Path(csv_path).exists():
            full_path = csv_path
        else:
            print(f"❌ CSV не найден: {csv_path}")
            sys.exit(1)

    bars_all = read_mt5_csv(full_path)
    if not bars_all:
        print(f"❌ CSV пуст или не прочитан: {full_path}")
        sys.exit(1)

    total = len(bars_all)
    # TESTER_CLEAN_TABLE_V1: чистим стол прогоняемого символа ПЕРЕД заходом
    _clean_table_for_symbol(symbol)
    print("═" * 64)
    print(f"  ЭКСПРЕСС-ТЕСТЕР · {symbol} {timeframe} · {total} баров")
    print(f"  point={point} · ловлю срабатываний Искры: {n_signals}")
    print(f"  кухня сама ищет — я только микрофон")
    print("═" * 64)

    # ── отчёт-файл рядом с CSV ──
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(full_path).with_name(
        f"{Path(full_path).stem}_tester_{stamp}.txt")
    report = open(report_path, "w", encoding="utf-8")

    def out(line=""):
        print(line)
        report.write(line + "\n")

    # TESTER_TRADE_FEED_V1: лента сделок в кабинет+консоль+файл
    _pnl_seen = {"n": len(_read_last_closures(9999))}
    def _feed_opened(pos):
        _d = pos.get('direction', '?')
        _t = pos.get('trader', '?')
        _e = pos.get('entry')
        line = f"🟢 ОТКРЫТА: {_t} {_d} @ {_e}"
        out("  " + line)
        _emit({"type": "trade", "kind": "open", "text": line})
    def _feed_check_closures(cur_bar_i):
        # читаем новые закрытия с прошлой проверки и шлём ленту
        all_cl = _read_last_closures(9999)
        new = all_cl[_pnl_seen['n']:]
        _pnl_seen['n'] = len(all_cl)
        for rec in new:
            _t = rec.get('trader', '?')
            _r = rec.get('pnl_r')
            _reason = rec.get('close_reason', '?')
            _opened = rec.get('opened_at', '?')
            _closed = rec.get('closed_at', '?')
            _rstr = (f"{'+' if (_r or 0) >= 0 else ''}{_r}R"
                     if _r is not None else '—')
            line = (f"🔴 ЗАКРЫТА: {_t} {_rstr} ({_reason}) · "
                    f"{_opened} → {_closed}")
            out("  " + line)
            _emit({"type": "trade", "kind": "close", "text": line})

    # ── КРАН: подменяем _fetch на чтение среза CSV ──
    # Агенты внутри зовут _fetch(mt5, symbol, tf, count). Мы перехватываем:
    # отдаём последние count баров ИЗ ИСТОРИИ ДО текущего "сейчас".
    # "Сейчас" двигаем переменной _cursor (индекс последнего видимого бара).
    state = {"cursor": warmup}

    def _fake_fetch(mt5, sym, tf_name, count):
        end = state["cursor"] + 1          # включительно текущий бар
        start = max(0, end - count)
        window = bars_all[start:end]
        return window, point

    # _terminal вернёт не-None заглушку, чтобы агенты прошли проверку
    # "if mt5 is None" и дошли до _fetch (который мы подменили).
    class _FakeMT5:  # достаточно, чтобы быть "не None"
        pass

    # ── TESTER_STERILE_V1: стерильность — бэктест не калечит ДНК ──
    # learn=False (умолчание): глушим петлю обучения на время
    # прогона. Агенты думают, сделки считаются, но sync_to_dna
    # не мутирует живую ДНК. learn=True — учебный прогон.
    try:
        import studio.grondheim_memory as _gm  # type: ignore[import]  # TESTER_EXPRESS_SOUL_IGNORE_V1: намеренно — см. except ниже
    except ImportError:
        # Новый город: studio.grondheim_memory (душа агентов) ещё не
        # перенесена для торговых агентов — честная заглушка вместо
        # падения. sync_to_dna и так вызывается через try/except в
        # каждом *_live.py, так что учебная петля просто молчит.
        class _NoSoulShim:
            def sync_to_dna(self, *a, **k):
                pass
        _gm = _NoSoulShim()
        print('[TESTER] ℹ️  studio.grondheim_memory не найдена (новый город) — '
              'петля обучения ДНК молчит, прогон честно идёт без неё')
    _orig_sync = _gm.sync_to_dna
    if not learn:
        _gm.sync_to_dna = lambda *a, **k: None   # заглушка-микрофон
        print('[TESTER] 🧪 стерильный прогон: ДНК агентов НЕ мутирует '
              '(--learn чтобы учить)')
    else:
        print('[TESTER] 🎓 учебный прогон: ДНК агентов мутирует, как в реале')

    orig_fetch = mt5_feed._fetch
    orig_term  = mt5_feed._terminal
    orig_pull  = mt5_feed.pull_bars     # TESTER_TO_CABINET_V1
    orig_step  = mt5_feed.step_down     # TESTER_TO_CABINET_V1
    mt5_feed._fetch    = _fake_fetch
    mt5_feed._terminal = lambda: _FakeMT5()

    # ── ГЕРМЕТИЧНЫЙ КРАН (TESTER_TO_CABINET_V1) ──
    # Спуск Искры (_read_form_on) берёт бары через pull_bars, не
    # через _fetch. Накрываем и её: тот же срез истории до курсора.
    # step_down ЗАПЕРТ — один CSV = один этаж, спуск проверяет
    # точку на загруженном ТФ по реальной истории, не прыгает на
    # этажи, которых в этой истории нет.
    def _fake_pull(sym, tf_name, count=2000):
        return _fake_fetch(None, sym, tf_name, count)
    def _locked_step_down(tf_name):
        return None
    mt5_feed.pull_bars = _fake_pull
    mt5_feed.step_down = _locked_step_down

    caught = 0
    scanned = 0
    found_cnt = 0          # TESTER_TO_CABINET_V1: у скольких спуск нашёл точку
    _last_settled = warmup - 1   # TESTER_SETTLE_GAPS_V1: докуда докатан settle
    try:
        # Проверка, что мозг Искры на месте (Совет её зовёт внутри
        # council.wake_council — единая дверь). Сито-1 ниже Искру-LLM
        # не трогает: оно чистое ядро (build_market_data), без модели.
        if _slot_brain("торговый_хаос", "A01") is None:
            raise RuntimeError("мозг A01 (Искра) ещё не в слоте")

        # ════════════════════════════════════════════════════
        # СИТО 1 — МАТЕМАТИКА ЯДРА (без LLM, мгновенно)
        # ─────────────────────────────────────────────────────
        # Прочёсываем всю историю чистым ядром. На каждом баре
        # build_market_data (питон, микросекунды) — собираем индексы,
        # где есть разворот: divergence_ao (бычья Точка Ноль) ИЛИ
        # exit_bell (медвежья). Модель НЕ зовём. Это отсев пустых
        # баров ДО дорогого Совета. 24к баров → секунды → горстка
        # кандидатов (по канону развороты редки).
        # ════════════════════════════════════════════════════
        out("⚙️  Сито 1: математика ядра просеивает историю (без модели)...")
        candidates = []
        for i in range(warmup, total):
            end = i + 1
            start = max(0, end - 300)
            window = bars_all[start:end]
            md = build_market_data(window, symbol=symbol,
                                   timeframe=timeframe, point=point)
            if not md:
                continue
            # СТРОГОЕ сито: bdb_strong — Точка Ноль с тремя условиями разом
            # (дивергенция + ангуляция 5-7 баров + B/D/B бар). По канону
            # таких 3-4 в год. Это то, что РАЗВОРОТ, а не "кандидат".
            # Грубые divergence_ao/exit_bell дают ~27% баров (шум) — не они.
            db = md.get("divergent_bar", {})
            wf = md.get("wave_form", {})
            if loose:
                # мягко: любой B/D/B-направленный бар (без жёсткой ангуляции)
                strong = wf.get("bdb_dir") or db.get("bdb_candidate")
                side = (wf.get("bdb_dir") or db.get("direction") or "?")
            else:
                # строго: Точка Ноль bdb_strong (дивергенция+ангуляция+B/D/B)
                strong = db.get("bdb_strong") or wf.get("bdb_dir")
                side = db.get("direction") or wf.get("bdb_dir") or "?"
            if strong:
                candidates.append((i, side))
        mode_txt = "мягкое (bdb_dir/candidate)" if loose else "строгое (bdb_strong — Точка Ноль)"
        out(f"⚙️  Сито 1 готово: {len(candidates)} баров-кандидатов "
            f"из {total - warmup} · сито {mode_txt}.")
        if not candidates:
            hint = ("" if loose else
                    " Попробуй мягче: добавь флаг --loose "
                    "(ловит B/D/B без жёсткой ангуляции 5-7 баров).")
            out("\n⚠️ Ядро не нашло строгих разворотов (Точка Ноль) на этой "
                f"истории.{hint} Модель не звали — это честный ответ кухни.")
            return _finish(report, report_path)
        out("")

        # ════════════════════════════════════════════════════
        # СИТО 2 — ЖИВОЙ СОВЕТ (с LLM, дорого, но РЕДКО)
        # Только на кандидатах сита 1. Тут Искра подтверждает своим
        # голосом (она судит строже ядра — может и отмести), и если
        # сказала да — будим весь Совет и печатаем их разговор.
        # ════════════════════════════════════════════════════
        out(f"🎤 Сито 2: бужу живой Совет на {len(candidates)} кандидатах...")
        out("")
        for idx, (i, side) in enumerate(candidates):
            if _stop_requested():   # TESTER_HANDLES_V1: кнопка СТОП биржи
                out(f"⏸ СТОП по команде Шефа — прошёл {scanned} из {len(candidates)} кандидатов.")
                break
            state["cursor"] = i
            scanned += 1
            _emit(f"кандидат {idx+1}/{len(candidates)} · бар {i}")

            # TESTER_SETTLE_GAPS_V1: прокатываем settle по ВСЕМ барам от
            # прошлого кандидата до текущего — рынок закрывает позиции
            # ровно там, где реально дошёл до стопа/колокола, а не
            # через годы на следующем кандидате (убивает зомби-позиции).
            # _settle_bar мгновенно выходит на пустом столе — дёшево.
            for _b in range(_last_settled + 1, i + 1):
                # TESTER_SETTLE_FULL_WINDOW_V1: ПОЛНОЕ окно 300 баров (было 60).
                # exit_bell (дивергенция AO) требует большого окна —
                # на 60 барах он не считался, позиция висела до Air Bag
                # годами. На 300 звонок звенит вовремя (§9 Котина).
                _settle_bar(bars_all[max(0, _b - 299):_b + 1],
                            symbol, timeframe, point)
            _last_settled = i
            _feed_check_closures(i)   # TESTER_TRADE_FEED_V1: лента закрытий

            _table_before = set(_table_snapshot().keys())   # TESTER_TRADE_FEED_V1
            # ── ЕДИНАЯ ДВЕРЬ СОВЕТА (ENGINE_ONE_DOOR_V1) ──
            # Раньше здесь была ручная лестница вызовов агентов —
            # копия той, что в кабинете (ui_torg). Это был маскарад:
            # две лестницы расходятся. Теперь тестер зовёт ТУ ЖЕ дверь
            # council.wake_council, что и кабинет. Стриминг в отчёт —
            # через on_event: печатаем голоса ровно как раньше.
            #
            # Ворота по спуску (COUNCIL_BY_DESCENT_V1) теперь ВНУТРИ
            # wake_council: Искра будится первой, и если спуск не нашёл
            # точку — Совет не собирается (on_event шлёт council_idle).
            import council

            _found_flag = {"found": True}   # спуск нашёл точку?

            def _on_council_event(ev):
                etype = ev.get("type")
                if etype == "council_idle":
                    _found_flag["found"] = False
                    _d = ev.get("descent", {}) or {}
                    _msg = (f"кандидат {idx+1}/{len(candidates)} ({bd}, {side}): "
                            f"спуск не нашёл точку (компас={_d.get('compass')})")
                    print("  " + _msg + " — пропускаю")
                    _emit({"type": "progress", "text": _msg})   # TESTER_TO_CABINET_V1
                    return
                if etype != "agent":
                    return
                aid = ev.get("id")
                r = ev.get("result", {}) or {}
                narrative = (ev.get("narrative", "") or "").strip()
                if not r.get("ok"):
                    if aid != "A01":
                        _icon = {"A02": "🦭", "A03": "😱", "A04": "🎯",
                                 "A05": "📚", "A06": "🪨", "A07": "⚡",
                                 "A08": "🛡", "A09": "📋"}.get(aid, "•")
                        out(f"  {_icon} {aid}: сбой — {r.get('error','?')}")
                        out("")
                    return

                if aid == "A01":
                    _t1 = (r.get("signal", {}) or {}).get("t1_status", "NOT_FOUND")
                    out("")
                    out("🎯 " + "─" * 60)
                    out(f"🎯 бар {i} ({bd}) — ИСКРА: {_t1}")
                    out("🎯 " + "─" * 60)
                    out("")
                    out(f"  ✴️ ИСКРА:\n     {narrative}")
                    _emit_report("A01", narrative, _t1)   # TESTER_REPORTS_V1
                    out("")
                elif aid == "A02":
                    out(f"  🦭 МОРЖ:\n     {narrative}")
                    _emit_report("A02", narrative)
                    out("")
                elif aid == "A03":
                    out(f"  😱 ПАНИКЁР:\n     {narrative}")
                    _emit_report("A03", narrative)
                    out("")
                elif aid == "A04":
                    out(f"  🎯 ГАНС:\n     {narrative}")
                    _emit_report("A04", narrative)
                    out("")
                elif aid == "A05":
                    out(f"  📚 АРХИВАРИУС:\n     {narrative}")
                    _emit_report("A05", narrative)
                    out("")
                elif aid == "A06":
                    out(f"  🪨 БРУТ:\n     {narrative}")
                    _emit_report("A06", narrative)
                    bs = r.get("signal", {}) or {}
                    v = bs.get("brut_verdict", "—")
                    if v == "APPROVED":
                        out(f"     └─ ВЕРДИКТ: {v} {bs.get('brut_direction','')} "
                            f"вход {bs.get('brut_entry','—')} · "
                            f"стоп {bs.get('brut_stop','—')} · "
                            f"лот {bs.get('brut_lot','—')}")
                    else:
                        out(f"     └─ ВЕРДИКТ: {v} ({bs.get('brut_reason','')})")
                    de = r.get("diary_entry", {}) or {}
                    if de:
                        out(f"     └─ в дневник: {de.get('action','').strip()}")
                    out("")
                elif aid == "A07":
                    out(f"  ⚡ АВАНТЮРИСТ:\n     {narrative}")
                    _emit_report("A07", narrative)
                    avs = r.get("signal", {}) or {}
                    vv = avs.get("avan_verdict", "—")
                    if vv == "APPROVED":
                        out(f"     └─ ВЕРДИКТ: {vv} {avs.get('avan_direction','')} "
                            f"вход {avs.get('avan_entry','—')} · "
                            f"стоп {avs.get('avan_stop','—')} · "
                            f"лот {avs.get('avan_lot','—')}")
                    else:
                        out(f"     └─ ВЕРДИКТ: {vv} ({avs.get('avan_reason','')})")
                    out("")
                elif aid == "A08":
                    out(f"  🛡 КОНСЕРВАТОР:\n     {narrative}")
                    _emit_report("A08", narrative)
                    cos = r.get("signal", {}) or {}
                    vc = cos.get("cons_verdict", "—")
                    if vc == "APPROVED":
                        out(f"     └─ ВЕРДИКТ: {vc} {cos.get('cons_direction','')} "
                            f"вход {cos.get('cons_entry','—')} · "
                            f"стоп {cos.get('cons_stop','—')} · "
                            f"лот {cos.get('cons_lot','—')}")
                    else:
                        out(f"     └─ ВЕРДИКТ: {vc} ({cos.get('cons_reason','')})")
                    out("")
                elif aid == "A09":
                    esig = r.get("signal", {}) or {}
                    fdna = esig.get("final_dna", {}) or {}
                    out(f"  📋 ИСПОЛНИТЕЛЬ: ордеров "
                        f"{fdna.get('orders_sent','—')} из 3 · "
                        f"task_score {fdna.get('task_score','—')}")
                    _emit_report("A09",
                        esig.get("history_dna", "") or
                        f"ордеров {fdna.get('orders_sent','—')} из 3")
                    if esig.get("history_dna"):
                        out(f"     └─ летопись: {esig.get('history_dna','').strip()}")
                    out("")

            _summary = council.wake_council(symbol, timeframe,
                                            on_event=_on_council_event)

            # Спуск не нашёл точку → Совет не собрался, следующий кандидат.
            if not _found_flag["found"] or _summary.get("idle"):
                continue
            found_cnt += 1   # TESTER_TO_CABINET_V1: спуск долетел до Совета

            # TESTER_TRADE_FEED_V1: лента открытий — что появилось на столе
            # после того, как Исполнитель отработал внутри wake_council.
            try:
                _now = _table_snapshot()
                for _m, _p in _now.items():
                    if _m not in _table_before:
                        _feed_opened(_p)
            except Exception:
                pass
            # TESTER_CLEAN_TABLE_V1: метим свежие позиции символом (для Шага 2)
            try:
                from hooks import (
                    load_trading_state, save_trading_state)
                _ts = load_trading_state()
                _dirty = False
                for _p in _ts.get('positions', []) or []:
                    if not _p.get('symbol'):
                        _p['symbol'] = symbol
                        _dirty = True
                if _dirty:
                    save_trading_state(_ts)
            except Exception:
                pass

            caught += 1   # TESTER_TO_CABINET_V1: Совет собрался и отработал
            if caught >= n_signals:
                out(f"✓ поймал {caught} срабатываний из {scanned} "
                    f"проверенных кандидатов — стоп.")
                break
        else:
            out(f"\n⚠️ прошёл все {len(candidates)} кандидатов сита 1, "
                f"живая Искра подтвердила {caught} "
                f"(искал {n_signals}). Ядро видело разворот, но Искра "
                f"живьём судит строже — это её право. Честный ответ кухни.")

    finally:
        # ── снимаем весь кран: всё как было (TESTER_TO_CABINET_V1) ──
        _gm.sync_to_dna = _orig_sync   # TESTER_STERILE_V1: вернуть обучение
        mt5_feed._fetch    = orig_fetch
        mt5_feed._terminal = orig_term
        mt5_feed.pull_bars = orig_pull
        mt5_feed.step_down = orig_step
        report.close()

    # ── РАЗВИЛКА (TESTER_TO_CABINET_V1) — в кабинет через on_progress + в консоль ──
    _verdict = (f"РАЗВИЛКА · Сито 1: {len(candidates)} кандидатов · "
                f"спуск нашёл точку: {found_cnt} · Совет собрался: {caught}")
    if found_cnt == 0:
        _hint = ("Совет молчит — спуск не нашёл точку ни у кого. Кандидаты "
                 "есть, ворота исправны: редок дивер-компас. Следующий шаг — "
                 "подключить global_bias (синюю) к спуску.")
    else:
        _hint = f"Спуск долетел до Совета {found_cnt} раз — ворота работают."
    _emit({"type": "verdict", "text": _verdict, "hint": _hint,
           "candidates": len(candidates), "found": found_cnt, "council": caught})
    print("")
    print("─" * 64)
    print("  " + _verdict)
    print("  → " + _hint)
    print("─" * 64)
    print("")
    print(f"📄 полный разговор записан: {report_path}")
    print("═" * 64)


def _finish(report, report_path):
    """Ранний выход: отчёт закроет finally в run_tester. Здесь только метка."""
    print("")
    print(f"📄 отчёт записан: {report_path}")
    return


def main():
    ap = argparse.ArgumentParser(
        description="Экспресс-тестер: живой Совет на истории CSV (без MT5)")
    ap.add_argument("csv",    help="путь к CSV (формат MT5)")
    ap.add_argument("symbol", help="тикер (XAUUSD, EURUSD...)")
    ap.add_argument("tf",     help="таймфрейм этого CSV (H4, D1...)")
    ap.add_argument("--signals", type=int, default=1,
                    help="сколько срабатываний Искры поймать (по умолч. 1)")
    ap.add_argument("--point", default=None,
                    help="шаг цены, если тестер не знает тикер")
    ap.add_argument("--warmup", type=int, default=60,
                    help="сколько баров пропустить на разгон индикаторов")
    ap.add_argument("--loose", action="store_true",
                    help="мягкое сито (если строгое bdb_strong дало ноль)")
    ap.add_argument("--learn", action="store_true",   # TESTER_STERILE_V1
                    help="учебный прогон: ДНК агентов мутирует "
                         "(по умолчанию стерильно — смотрим, не калеча)")
    args = ap.parse_args()

    run_tester(args.csv, args.symbol, args.tf,
               n_signals=args.signals, point_override=args.point,
               warmup=args.warmup, loose=args.loose,
               learn=args.learn)   # TESTER_STERILE_V1


if __name__ == "__main__":
    main()

# TESTER_EXPRESS_CARTRIDGE_V1 — маркер идемпотентности

# TESTER_EXPRESS_SOUL_IGNORE_V1 — маркер идемпотентности
'''


def main():
    written = []
    for rel_path, content in FILES.items():
        target = REPO_ROOT / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        written.append((rel_path, "обновлён" if existed else "создан"))

    # ── удаление корневого дубля ui_torg.py (с бэкапом) ──
    root_ui = REPO_ROOT / "ui_torg.py"
    dup_note = ""
    if root_ui.exists():
        archive = REPO_ROOT / "_ARCHIVE"
        archive.mkdir(parents=True, exist_ok=True)
        backup = archive / "ui_torg_ROOT_DUP_backup.py"
        shutil.copy2(root_ui, backup)
        root_ui.unlink()
        dup_note = (f"корневой ui_torg.py УДАЛЁН (бэкап: "
                    f"_ARCHIVE/ui_torg_ROOT_DUP_backup.py)")
    else:
        dup_note = "корневой ui_torg.py уже отсутствует (ничего не делаю)"

    print("=" * 62)
    print("ENGINE_ONE_DOOR_V1 -- патч применён")
    print("=" * 62)
    for rel_path, status in written:
        print(f"  [{status:8}] {rel_path}")
    print(f"  [дубль   ] {dup_note}")
    print()
    print("Теперь тестер и будущий боевой путь зовут ОДНУ дверь Совета")
    print("(council.wake_council). Прогони тестер -- поведение то же, но")
    print("лестница уже не копия, а единый источник.")
    print()
    print("Следующий заход (отдельно):")
    print("  -- переключить Биржа/ui_torg.py (кабинет) на wake_council")
    print("     через on_event (сохранив пузырьки/аватары/notify)")
    print("  -- решить судьбу hooks.run_live_council() (боевой путь)")
    print("  -- охват памяти конторы (общий котёл + метка цеха)")


if __name__ == "__main__":
    if not (REPO_ROOT / "GRONDHEIM_CITY").exists() or not (REPO_ROOT / "Биржа").exists():
        print("ВНИМАНИЕ: рядом со скриптом нет GRONDHEIM_CITY/ и Биржа/.")
        print("    Запусти патч из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)
    main()
