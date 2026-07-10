# -*- coding: utf-8 -*-
"""
patch_council_chat_memory_v3.py
-----------------------------------------------------------
ENGINE_ONE_DOOR_V1 -- фаза 3: память чата после ТЕСТЕРА.

ДИАГНОЗ (замечен Шефом в живом диалоге с Верочкой/A01 после тестера):
  Чат с агентом сразу после ТЕСТЕРА честно, но НЕВЕРНО по сути отвечал
  "рынок не запускали" -- хотя агент только что отработал через ту же
  дверь (council.wake_council). Причина: state[*_last_run] (память для
  чата) писала ТОЛЬКО кнопка РЫНОК (run_market). run_tester_session
  эту память не писала вовсе -- старый пробел, был ДО всех патчей этой
  сессии, не регрессия. Тестер посылал в кабинет только тонкий пакет
  {agent, narrative, status} -- без signal/market, которых чату не
  хватало для контекста.

ЧТО МЕНЯЕТСЯ:
  1. Биржа/tester_express.py -- _emit_report() теперь несёт опциональный
     result (ПОЛНЫЙ словарь run_* агента), все 9 вызовов передают его.
  2. Биржа/ui_torg.py -- разбор результата одного агента вынесен из
     run_market в ОБЩУЮ функцию _apply_agent_result(aid, r, narrative).
     Теперь её зовут ОБА пути: run_market (РЫНОК) и run_tester_session
     (_on_progress, когда пришёл result). Один источник правды для
     памяти чата -- та же философия одной двери, что и для Совета.

ЧТО НЕ МЕНЯЕТСЯ:
  - Обратная совместимость: если result не пришёл (старый вызывающий
    без result) -- работает прежняя тонкая логика _on_progress.
  - Порядок/логика самого Совета не тронуты -- это чисто про то, что
    кабинет ЗАПОМИНАЕТ после прогона, не про то, что Совет делает.

Идемпотентно: безопасно запускать повторно.

ПРОВЕРЕНО (см. отчёт в чате):
  - _apply_agent_result вызванный из имитации "тестового" report-события
    корректно заполняет iskra_last_run/brut_last_run с полным signal/market.
  - run_market() после рефакторинга (извлечения _apply_agent_result)
    работает идентично версии ДО рефакторинга -- тот же прогон на
    моках даёт те же 9 обновлений state, chat_history длиной 9.

Кодировка ui_torg.py: base64 (файл использует оба вида тройных кавычек
внутри себя, надёжного текстового разделителя для вставки нет).
tester_express.py вставлен обычным текстовым литералом (коллизий нет).

Запуск из КОРНЯ репозитория:
    python patch_council_chat_memory_v3.py
"""

import sys
import base64
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TESTER_TARGET = REPO_ROOT / "Биржа" / "tester_express.py"
UI_TARGET = REPO_ROOT / "Биржа" / "ui_torg.py"

TESTER_CONTENT = r'''# studio/modules/trading/tester_express.py
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

    def _emit_report(agent, narrative, status="", result=None):  # TESTER_REPORTS_V1
        """
        Структурный отчёт агента наружу — биржа разложит по аватарам.

        result (опционально) — ПОЛНЫЙ словарь run_* агента (signal,
        market, stats, ...). Раньше сюда шёл только narrative/status —
        кабинет не мог восстановить *_last_run после ТЕСТЕРА, и чат
        с агентом сразу после тестового прогона честно, но неверно по
        сути отвечал "рынок не запускали". Теперь result прокидывается
        и в кабинете идёт в ту же _apply_agent_result, что использует
        и РЫНОК — один источник правды для памяти чата.
        """
        if on_progress and narrative:
            try:
                msg = {"type": "report", "agent": agent,
                       "narrative": str(narrative).strip(), "status": status}
                if result is not None:
                    msg["result"] = result
                on_progress(msg)
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
                    _emit_report("A01", narrative, _t1, result=r)   # TESTER_REPORTS_V1
                    out("")
                elif aid == "A02":
                    out(f"  🦭 МОРЖ:\n     {narrative}")
                    _emit_report("A02", narrative, result=r)
                    out("")
                elif aid == "A03":
                    out(f"  😱 ПАНИКЁР:\n     {narrative}")
                    _emit_report("A03", narrative, result=r)
                    out("")
                elif aid == "A04":
                    out(f"  🎯 ГАНС:\n     {narrative}")
                    _emit_report("A04", narrative, result=r)
                    out("")
                elif aid == "A05":
                    out(f"  📚 АРХИВАРИУС:\n     {narrative}")
                    _emit_report("A05", narrative, result=r)
                    out("")
                elif aid == "A06":
                    out(f"  🪨 БРУТ:\n     {narrative}")
                    _emit_report("A06", narrative, result=r)
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
                    _emit_report("A07", narrative, result=r)
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
                    _emit_report("A08", narrative, result=r)
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
                        f"ордеров {fdna.get('orders_sent','—')} из 3",
                        result=r)
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

_UI_B64_CHUNKS = (
    "IyAtKi0gY29kaW5nOiB1dGYtOCAtKi0KIyBUT1JHX1NUT0xfVjIg4oCUINCa0JDQkdCY0J3QldCiINCh0J7QktCV0KLQkCAo0L/Q"
    "tdGA0LXQvdC+0YEgdWlfZXhjaGFuZ2UucHkg0L3QsCDQvdC+0LLRi9C1INC/0YDQsNCy0LjQu9CwINC10LTQuNC90LjRhikKIiIi"
    "CtCR0JjQoNCW0JAgwrcg0JrQkNCR0JjQndCV0KIg0KHQntCS0JXQotCQIMK3IC90b3JnL3t0c2VoX2lkfQoK0K3QotCeINCi0J7Q"
    "oiDQltCVINCa0JDQkdCY0J3QldCiLCDRh9GC0L4g0LHRi9C7IHN0dWRpby9lY29ub215L3VpX2V4Y2hhbmdlLnB5INCyIC0yIOKA"
    "lCDRgtC+0YIg0LbQtQrRhdC10LTQtdGALdC/0YPQt9GL0YDRjNC60LgsINGC0LAg0LbQtSDQu9C10LLQsNGPINC60L7Qu9C+0L3Q"
    "utCwICjQt9Cw0LPRgNGD0LfRh9C40Lor0L/QvtC70LrQsCDQsNC60YLQuNCy0L7QsiksINGC0L7RgiDQttC1CtGB0YLQvtC7ICjR"
    "gtGD0LvQsdCw0YAg0KDQq9Cd0J7Qmi/RgtC10YHRgi3RgNC10LDQuyArINGH0LDRgiArINC+0YLRh9GR0YIt0LLRjNGO0LXRgCks"
    "INGC0LAg0LbQtSDQv9GA0LDQstCw0Y8g0LrQvtC70L7QvdC60LAKKNCw0LLQsNGC0LDRgCvQv9GA0LjQsdC+0YDRiykuINCh0LjR"
    "gdGC0LXQvNGDINGC0L7RgNCz0L7QstC70LggKNCS0LjQu9GM0Y/QvNGBLCDQv9GB0LjRhdC+0LvQvtCz0LjRjyDQsNCz0LXQvdGC"
    "0L7QsiwKcnVuX2lza3JhL3J1bl9tb3JqLy4uLikg0J3QlSDQn9CV0KDQldCU0JXQm9Cr0JLQkNCb0Jgg4oCUINC+0L3QsCDQv9GA"
    "0LjRhdC+0LTQuNGCINC40Lcg0LTQstC40LbQutC+0LLRi9GFCtC80L7QtNGD0LvQtdC5IChpc2tyYV9saXZlLnB5INC4INGCLtC0"
    "LiksINC60L7RgtC+0YDRi9C1INC70LXQttCw0YIg0YDRj9C00L7QvCDQsiDQkdC40YDQttC1LgoK0KfQotCeINCU0JXQmdCh0KLQ"
    "ktCY0KLQldCb0KzQndCeINCf0J7QnNCV0J3Qr9Cb0J7QodCsICjQvdC+0LLRi9C1INC/0YDQsNCy0LjQu9CwINC10LTQuNC90LjR"
    "hik6CiAg0KHRgtCw0YDRi9C5INC80LjRgDogVFJBRElOR19DT1VOQ0lMIOKAlCDQt9Cw0YXQsNGA0LTQutC+0LbQtdC90L3Ri9C5"
    "INGB0L/QuNGB0L7QuiBpZC9sYWJlbC9pY29uLAogINCw0LLQsNGC0LDRgCDigJQg0YHRgtCw0YLQuNC60LAgc3R1ZGlvL21vZHVs"
    "ZXMvdHJhZGluZy9BWFgvLi4uIC4KICDQndC+0LLRi9C5INC80LjRgDog0L/Rg9C30YvRgNGM0LrQuCDigJQg0KDQldCQ0JvQrNCd"
    "0KvQmSDRgdC+0YHRgtCw0LIsINGH0LjRgtCw0LXRgtGB0Y8g0YfQtdGA0LXQtyDQl9Cw0LrQvtC9INCf0LDRgNGLCiAgKGNhcnRy"
    "aWRnZV9yZWdpc3RyeS5yZXNvbHZlX3BhcmEvbGlzdF9ub3NpdGVsaSkuINCa0YLQviDRgdC40LTQuNGCINCyIEEwMSDigJQKICDR"
    "gNC10YjQsNC10YIgbWFzay5qc29uINGA0LXQt9C40LTQtdC90YLQsCAoV29ya3Nob3BfSUQrVHVyYm9fUm9sZSksINC90LUg0LrQ"
    "vtC0INC30LTQtdGB0YwuCiAg0JDQstCw0YLQsNGAL9C40LzRjyDigJQg0LjQtyDQv9Cw0YHQv9C+0YDRgtCwINGA0LXQt9C40LTQ"
    "tdC90YLQsCwg0LAg0L3QtSDQuNC3INGB0YLQsNGC0LjRh9C90L7QuSDQv9Cw0L/QutC4LgoK0KHQntCh0KLQkNCSINCh0J7QktCV"
    "0KLQkCDQkdCY0KDQltCYICjQtNCy0LAg0YbQtdGF0LAg0YDQsNC30L7QvCwg0LrQsNC6INCx0YvQu9C+INC+0LTQvdC40Lwg0Y3Q"
    "utGA0LDQvdC+0Lwg0LIgLTIpOgogINGC0L7RgNCz0L7QstGL0Llf0YXQsNC+0YE6IEEwMSBBMDIgQTAzIEEwNCBBMDYgQTA3IEEw"
    "OCAoNyDRgdC70L7RgtC+0LIt0LLQvtGA0LrQtdGA0L7QsikKICDQutC+0L3RgtC+0YDQsDogICAgICAg0LDRgNGF0LjQstCw0YDQ"
    "uNGD0YEsINC40YHQv9C+0LvQvdC40YLQtdC70YwgKNGI0YLQsNCxLCDQvtCx0YnQuNC5INC90LAg0LLRgdGOINCR0LjRgNC20YMp"
    "CiAg0JfQtNC10YHRjCDRjdGC0L4g0L7QtNC40L0g0Lgg0YLQvtGCINC20LUg0Y3QutGA0LDQvSAo0KHQvtCy0LXRgiDQstGB0LXQ"
    "s9C00LAg0LLQuNC00LXQu9GB0Y8g0YbQtdC70LjQutC+0LwpIOKAlAogIFJPU1RFUl9TUEVDINC90LjQttC1INGB0LLQvtC00LjR"
    "giDQvtCx0LAg0YbQtdGF0LAg0LIg0L7QtNC40L0g0YXQtdC00LXRgCwg0L/QvtGA0Y/QtNC+0Log0Lgg0LjQutC+0L3QutC4IOKA"
    "lAogINC60LDQuiDQsiDRgdGC0LDRgNC+0LwgVFJBRElOR19DT1VOQ0lMIChBMDU90LDRgNGF0LjQstCw0YDQuNGD0YEsIEEwOT3Q"
    "uNGB0L/QvtC70L3QuNGC0LXQu9GMKS4KCtCf0YDQvtC80L/RgiDRgNC+0LvQuCDigJQg0KHQntCR0KHQotCS0JXQndCd0J7QodCi"
    "0Kwg0KbQldCl0JAgKNGB0LvQvtGC0YsvQTBYL9C/0YDQvtC80L/Rgi5tZCDQsiBtYW5pZmVzdCksCtC90LUg0YDQtdC30LjQtNC1"
    "0L3RgtCwLiDQoNC10LfQuNC00LXQvdGCIOKAlCDQv9GA0L7RgdGC0L4g0LrRgtC+INGB0LXQs9C+0LTQvdGPINC90LAg0YHQvNC1"
    "0L3QtSAo0JfQsNC60L7QvSDQlNC10LbRg9GA0YHRgtCy0LApLgoKYNGI0LXRgdGC0YzCt9C/0YDQvtCy0LXRgNC10L3QvsK30LTQ"
    "vsK30LrQvtGA0L3Rj2AKIiIiCmltcG9ydCBzeXMKaW1wb3J0IGpzb24KZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmZyb20gZGF0"
    "ZXRpbWUgaW1wb3J0IGRhdGV0aW1lLCB0aW1lem9uZQppbXBvcnQgYXN5bmNpbwoKZnJvbSBuaWNlZ3VpIGltcG9ydCB1aSwgYXBw"
    "LCBldmVudHMKCl9IRVJFID0gUGF0aChfX2ZpbGVfXykucmVzb2x2ZSgpLnBhcmVudCAgICAgICAgICAjINCR0LjRgNC20LAvCl9S"
    "RVBPID0gX0hFUkUucGFyZW50ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyDQutC+0YDQtdC90Ywg0YDQtdC/0L4KZm9y"
    "IF9wIGluIChfUkVQTywgX0hFUkUpOgogICAgaWYgc3RyKF9wKSBub3QgaW4gc3lzLnBhdGg6CiAgICAgICAgc3lzLnBhdGguaW5z"
    "ZXJ0KDAsIHN0cihfcCkpCgppbXBvcnQgY2FydHJpZGdlX3JlZ2lzdHJ5IGFzIHJlZwoKaW1wb3J0IGltcG9ydGxpYi51dGlsCmZy"
    "b20gdHlwaW5nIGltcG9ydCBBbnkgICMgVUlfVE9SR19UWVBJTkdfVjEKCl9CUkFJTl9DQUNIRSA9IHt9CgoKZGVmIF9zbG90X2Jy"
    "YWluKGNlaF9pZDogc3RyLCBzbG90OiBzdHIpOgogICAgIiIi0JfQsNC60L7QvSDQmtCw0YDRgtGA0LjQtNC20LAg0LTQu9GPINC6"
    "0L7QtNCwOiDQvNC+0LfQsyDRgdC70L7RgtCwINC20LjQstGR0YIg0KDQr9CU0J7QnCDRgSDQv9GA0L7QvNC/0YLQvtC8CiAgICAo"
    "0YHQu9C+0YLRiy97c2xvdH0v0LzQvtC30LMucHkpIOKAlCDQutCw0LHQuNC90LXRgiDQvdC1INGF0LDRgNC00LrQvtC00LjRgiDQ"
    "uNC80LXQvdCwINC80L7QtNGD0LvQtdC5LCDQsAogICAg0YHQv9GA0LDRiNC40LLQsNC10YIg0YMg0YbQtdGF0LAsINGH0YLQviDR"
    "gtCw0Lwg0YDQtdCw0LvRjNC90L4g0LvQtdC20LjRgi4g0J3QtdGCINGE0LDQudC70LAg4oCUINGH0LXRgdGC0L3QsNGPCiAgICDQ"
    "stCw0LrQsNC90YHQuNGPINC80L7Qt9Cz0LAgKE5vbmUpLCDQvdC1INC+0YjQuNCx0LrQsC4g0JrRjdGIINC90LAg0L/RgNC+0YbQ"
    "tdGB0YEg4oCUINC90LUg0LPRgNGD0LfQuNC8CiAgICDQt9Cw0L3QvtCy0L4g0L3QsCDQutCw0LbQtNGL0Lkg0LrQu9C40LouIiIi"
    "CiAgICBrZXkgPSAoY2VoX2lkLCBzbG90KQogICAgaWYga2V5IGluIF9CUkFJTl9DQUNIRToKICAgICAgICByZXR1cm4gX0JSQUlO"
    "X0NBQ0hFW2tleV0KICAgIGJyYWluX3BhdGggPSAoX1JFUE8gLyAiR1JPTkRIRUlNX0NJVFkiIC8gS1ZBUlRBTCAvICLRhtC10YXQ"
    "sCIgLyBjZWhfaWQKICAgICAgICAgICAgICAgICAvICLRgdC70L7RgtGLIiAvIHNsb3QgLyAi0LzQvtC30LMucHkiKQogICAgaWYg"
    "bm90IGJyYWluX3BhdGguZXhpc3RzKCk6CiAgICAgICAgX0JSQUlOX0NBQ0hFW2tleV0gPSBOb25lCiAgICAgICAgcmV0dXJuIE5v"
    "bmUKICAgIHNwZWMgPSBpbXBvcnRsaWIudXRpbC5zcGVjX2Zyb21fZmlsZV9sb2NhdGlvbigKICAgICAgICBmIl9icmFpbl97Y2Vo"
    "X2lkfV97c2xvdH0iLCBicmFpbl9wYXRoKQogICAgaWYgc3BlYyBpcyBOb25lIG9yIHNwZWMubG9hZGVyIGlzIE5vbmU6CiAgICAg"
    "ICAgIyBVSV9UT1JHX1RZUElOR19WMTog0L/Rg9GC0Ywg0LXRgdGC0YwsINC90L4g0L3QtSDQvtC/0L7Qt9C90LDQvSDQutCw0Log"
    "0LzQvtC00YPQu9GMIOKAlAogICAgICAgICMg0YLQsCDQttC1INGH0LXRgdGC0L3QsNGPINCy0LDQutCw0L3RgdC40Y8sINGH0YLQ"
    "viDQuCAi0YTQsNC50LvQsCDQvdC10YIiINGB0YLRgNC+0LrQvtC5INCy0YvRiNC1CiAgICAgICAgX0JSQUlOX0NBQ0hFW2tleV0g"
    "PSBOb25lCiAgICAgICAgcmV0dXJuIE5vbmUKICAgIG1vZCA9IGltcG9ydGxpYi51dGlsLm1vZHVsZV9mcm9tX3NwZWMoc3BlYykK"
    "ICAgIHNwZWMubG9hZGVyLmV4ZWNfbW9kdWxlKG1vZCkKICAgIF9CUkFJTl9DQUNIRVtrZXldID0gbW9kCiAgICByZXR1cm4gbW9k"
    "CgoKS1ZBUlRBTCA9ICLQkdC40YDQttCwIgoKIyDilIDilIAg0KHQntCh0KLQkNCSINCh0J7QktCV0KLQkCDigJQg0L/QvtGA0Y/Q"
    "tNC+0Lov0LjQutC+0L3QutC4INC60LDQuiDQsiDRgdGC0LDRgNC+0LwgVFJBRElOR19DT1VOQ0lMIOKUgOKUgOKUgOKUgOKUgOKU"
    "gAojIChjZWhfaWQsINGA0LXQsNC70YzQvdGL0Llf0YHQu9C+0YJf0LJf0YbQtdGF0LUsIGlkX9C00LvRj1/QtNCy0LjQttC60LAo"
    "QTAxLi5BMDkpLCDQuNC60L7QvdC60LApClJPU1RFUl9TUEVDID0gWwogICAgKCLRgtC+0YDQs9C+0LLRi9C5X9GF0LDQvtGBIiwg"
    "IkEwMSIsICAgICAgICAgIkEwMSIsICLinLTvuI8iKSwKICAgICgi0YLQvtGA0LPQvtCy0YvQuV/RhdCw0L7RgSIsICJBMDIiLCAg"
    "ICAgICAgICJBMDIiLCAi8J+mrSIpLAogICAgKCLRgtC+0YDQs9C+0LLRi9C5X9GF0LDQvtGBIiwgIkEwMyIsICAgICAgICAgIkEw"
    "MyIsICLwn5ixIiksCiAgICAoItGC0L7RgNCz0L7QstGL0Llf0YXQsNC+0YEiLCAiQTA0IiwgICAgICAgICAiQTA0IiwgIvCfjq8i"
    "KSwKICAgICgi0LrQvtC90YLQvtGA0LAiLCAgICAgICAi0LDRgNGF0LjQstCw0YDQuNGD0YEiLCAgIkEwNSIsICLwn5OaIiksCiAg"
    "ICAoItGC0L7RgNCz0L7QstGL0Llf0YXQsNC+0YEiLCAiQTA2IiwgICAgICAgICAiQTA2IiwgIvCfqqgiKSwKICAgICgi0YLQvtGA"
    "0LPQvtCy0YvQuV/RhdCw0L7RgSIsICJBMDciLCAgICAgICAgICJBMDciLCAi8J+OsiIpLAogICAgKCLRgtC+0YDQs9C+0LLRi9C5"
    "X9GF0LDQvtGBIiwgIkEwOCIsICAgICAgICAgIkEwOCIsICLimpbvuI8iKSwKICAgICgi0LrQvtC90YLQvtGA0LAiLCAgICAgICAi"
    "0LjRgdC/0L7Qu9C90LjRgtC10LvRjCIsICJBMDkiLCAi8J+OrCIpLApdCgoKZGVmIF9yZWFkX2pzb24ocDogUGF0aCk6CiAgICB0"
    "cnk6CiAgICAgICAgcmV0dXJuIGpzb24ubG9hZHMocC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikpCiAgICBleGNlcHQgRXhj"
    "ZXB0aW9uOgogICAgICAgIHJldHVybiBOb25lCgoKZGVmIF9hdmF0YXJfdXJsX2ZvcihwYXBrYTogc3RyLCBzdGF0aWNfcHJlZml4"
    "OiBzdHIpIC0+IHN0cjoKICAgICIiItCk0L7RgtC+INGA0LXQt9C40LTQtdC90YLQsCDigJQg0L/QsNC/0LrQsC/QsNCy0LDRgtCw"
    "0YAuKiDihpIg0L/Rg9GC0Ywg0YHRgtCw0YLQuNC60LggKNC60LDQuiB1aV96aGl0ZWwpLiIiIgogICAgaWYgbm90IHBhcGthOgog"
    "ICAgICAgIHJldHVybiAiIgogICAgZG9tID0gUGF0aChwYXBrYSkKICAgIHAgPSBfcmVhZF9qc29uKGRvbSAvICJwYXNzcG9ydC5q"
    "c29uIikgb3Ige30KICAgIGF2ID0gcC5nZXQoImF2YXRhciIsICIiKQogICAgaWYgYXYgYW5kIChkb20gLyBhdikuZXhpc3RzKCk6"
    "CiAgICAgICAgcmV0dXJuIGYiL3tzdGF0aWNfcHJlZml4fS97ZG9tLm5hbWV9L3thdn0iCiAgICBmb3IgZXh0IGluICgiLnBuZyIs"
    "ICIuanBnIiwgIi5qcGVnIiwgIi53ZWJwIik6CiAgICAgICAgaWYgKGRvbSAvICgiYXZhdGFyIiArIGV4dCkpLmV4aXN0cygpOgog"
    "ICAgICAgICAgICByZXR1cm4gZiIve3N0YXRpY19wcmVmaXh9L3tkb20ubmFtZX0vYXZhdGFye2V4dH0iCiAgICByZXR1cm4gIiIK"
    "CgpfTE9LQUNJSV9ESVIgPSBfUkVQTyAvICJHUk9OREhFSU1fQ0lUWSIgLyAi0LvQvtC60LDRhtC40LgiCl9CR19TVEFUSUNfTU9V"
    "TlRFRCA9IHsiZG9uZSI6IEZhbHNlfQoKCmRlZiBfYnVpbGRpbmdfYmdfdXJsKGJ1aWxkaW5nX2lkOiBzdHIpIC0+IHN0cjoKICAg"
    "ICIiItCk0L7QvSDQutCw0LHQuNC90LXRgtCwIOKAlCDQutCw0YDRgtC40L3QutCwINCX0JTQkNCd0JjQryDRhtC10YXQsCAobWFu"
    "aWZlc3RbJ9C30LTQsNC90LjQtSddKSwg0L3QtQogICAg0LfQsNGF0LDRgNC00LrQvtC20LXQvdC90YvQuSDRgdGC0LDRgNGL0Lkg"
    "L2ltYWdlcy9iZ19tYWluLmpwZy4g0KfQtdGB0YLQvdC+INC/0YPRgdGC0L4sINC10YHQu9C4INGDCiAgICDQu9C+0LrQsNGG0LjQ"
    "uCDQtdGJ0ZEg0L3QtdGCIGltYWdlLiouIiIiCiAgICBpZiBub3QgYnVpbGRpbmdfaWQ6CiAgICAgICAgcmV0dXJuICIiCiAgICBk"
    "b20gPSBfTE9LQUNJSV9ESVIgLyBidWlsZGluZ19pZAogICAgaWYgbm90IGRvbS5leGlzdHMoKToKICAgICAgICByZXR1cm4gIiIK"
    "ICAgIGlmIG5vdCBfQkdfU1RBVElDX01PVU5URURbImRvbmUiXToKICAgICAgICB0cnk6CiAgICAgICAgICAgIGFwcC5hZGRfc3Rh"
    "dGljX2ZpbGVzKCIvdG9yZy1iZyIsIHN0cihfTE9LQUNJSV9ESVIpKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAg"
    "ICAgIHBhc3MKICAgICAgICBfQkdfU1RBVElDX01PVU5URURbImRvbmUiXSA9IFRydWUKICAgIGZvciBleHQgaW4gKCIuanBnIiwg"
    "Ii5qcGVnIiwgIi5wbmciLCAiLndlYnAiKToKICAgICAgICBpZiAoZG9tIC8gKCJpbWFnZSIgKyBleHQpKS5leGlzdHMoKToKICAg"
    "ICAgICAgICAgcmV0dXJuIGYiL3RvcmctYmcve2J1aWxkaW5nX2lkfS9pbWFnZXtleHR9IgogICAgcmV0dXJuICIiCgoKZGVmIF9i"
    "dWlsZF9yb3N0ZXIoc3RhdGljX3ByZWZpeDogc3RyKSAtPiBsaXN0OgogICAgIiIi0KHQstC+0LTQuNGCINC+0LHQsCDRhtC10YXQ"
    "sCDQkdC40YDQttC4INCyINC+0LTQuNC9INGB0L/QuNGB0L7QuiDQv9GD0LfRi9GA0YzQutC+0LIg4oCUINCX0LDQutC+0L0g0J/Q"
    "sNGA0YsKICAgINGA0LXRiNCw0LXRgiwg0LrRgtC+INCz0LTQtSDRgdC40LTQuNGCLCDRjdGC0LAg0YTRg9C90LrRhtC40Y8g0L/R"
    "gNC+0YHRgtC+INGB0L7QsdC40YDQsNC10YIg0Y3QutGA0LDQvS4iIiIKICAgIG91dCA9IFtdCiAgICBmb3IgY2VoX2lkLCBzbG90"
    "LCBvbGRfaWQsIGljb24gaW4gUk9TVEVSX1NQRUM6CiAgICAgICAgY2VoID0gcmVnLmdldF9jZWgoY2VoX2lkLCBLVkFSVEFMKQog"
    "ICAgICAgIHJvbCA9ICIiCiAgICAgICAgaWYgY2VoOgogICAgICAgICAgICBmb3IgcyBpbiBjZWguZ2V0KCLRgdC70L7RgtGLIiwg"
    "W10pOgogICAgICAgICAgICAgICAgaWYgcy5nZXQoItGB0LvQvtGCIikgPT0gc2xvdDoKICAgICAgICAgICAgICAgICAgICByb2wg"
    "PSBzLmdldCgi0YDQvtC70YwiLCAiIikKICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgIHJlc2lkZW50ID0gcmVnLnJl"
    "c29sdmVfcGFyYShjZWhfaWQsIHNsb3QsIEtWQVJUQUwpCiAgICAgICAgaWYgcmVzaWRlbnQ6CiAgICAgICAgICAgIHRyeToKICAg"
    "ICAgICAgICAgICAgIGFwcC5hZGRfc3RhdGljX2ZpbGVzKAogICAgICAgICAgICAgICAgICAgIGYiL3tzdGF0aWNfcHJlZml4fS97"
    "UGF0aChyZXNpZGVudFsn0L/QsNC/0LrQsCddKS5uYW1lfSIsCiAgICAgICAgICAgICAgICAgICAgcmVzaWRlbnRbItC/0LDQv9C6"
    "0LAiXSkKICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgICAgIHBhc3MKICAgICAgICBvdXQuYXBwZW5k"
    "KHsKICAgICAgICAgICAgIm9sZF9pZCI6IG9sZF9pZCwgICAgICAjINC00LvRjyDQstGL0LfQvtCy0L7QsiDQtNCy0LjQttC60LAg"
    "KHJ1bl9pc2tyYSDQuCDRgi7Qvy4pCiAgICAgICAgICAgICJjZWhfaWQiOiBjZWhfaWQsCiAgICAgICAgICAgICJzbG90Ijogc2xv"
    "dCwKICAgICAgICAgICAgInJvbGUiOiByb2wsCiAgICAgICAgICAgICJpY29uIjogaWNvbiwKICAgICAgICAgICAgInJlc2lkZW50"
    "IjogcmVzaWRlbnQsICAjIE5vbmUgPSDQstCw0LrQsNC90YHQuNGPCiAgICAgICAgfSkKICAgIHJldHVybiBvdXQKCgpkZWYgX2Fn"
    "ZW50X2xhYmVsKHJvc3RlcjogbGlzdCwgb2xkX2lkOiBzdHIpIC0+IHN0cjoKICAgIGZvciByIGluIHJvc3RlcjoKICAgICAgICBp"
    "ZiByWyJvbGRfaWQiXSA9PSBvbGRfaWQ6CiAgICAgICAgICAgIGlmIHJbInJlc2lkZW50Il06CiAgICAgICAgICAgICAgICByZXR1"
    "cm4gclsicmVzaWRlbnQiXVsi0LjQvNGPIl0KICAgICAgICAgICAgcmV0dXJuIHJbInJvbGUiXSBvciBvbGRfaWQKICAgIHJldHVy"
    "biBvbGRfaWQKCgpkZWYgX2FnZW50X3Jvdyhyb3N0ZXI6IGxpc3QsIG9sZF9pZDogc3RyKToKICAgIGZvciByIGluIHJvc3RlcjoK"
    "ICAgICAgICBpZiByWyJvbGRfaWQiXSA9PSBvbGRfaWQ6CiAgICAgICAgICAgIHJldHVybiByCiAgICByZXR1cm4gTm9uZQoKCmRl"
    "ZiBfYmFyX2h0bWwoY2hhcmdlOiBmbG9hdCkgLT4gc3RyOgogICAgIiIi0JbQuNCy0YvQtSDQv9C+0LrQsNC30LDRgtC10LvQuCDR"
    "gNC10LfQuNC00LXQvdGC0LAg4oCUINGC0L7RgiDQttC1INCy0LjQtCwg0YfRgtC+INCyIHVpX3poaXRlbC5weQogICAgKNC30LDR"
    "gNGP0LQv0L7Qv9GC0LjQutCwKSwg0L3QtSDRgdCy0L7QuSDQvtGC0LTQtdC70YzQvdGL0Lkg0LLQuNC00LbQtdGCINC00LvRjyDQ"
    "kdC40YDQttC4LiIiIgogICAgbXV0ID0gYWJzKGNoYXJnZSkKICAgIGhhbGYgPSBtaW4oMS4wLCBtdXQpICogNTAKICAgIGxlZnQg"
    "PSA1MCBpZiBjaGFyZ2UgPj0gMCBlbHNlIDUwIC0gaGFsZgogICAgem5hayA9ICIrIiBpZiBjaGFyZ2UgPj0gMCBlbHNlICJcdTIy"
    "MTIiCiAgICB6Y29sb3IgPSAicmdiYSg4MCwyNTAsMTIzLDAuOSkiIGlmIGNoYXJnZSA+PSAwIGVsc2UgInJnYmEoMjU1LDEyMCwx"
    "MjAsMC45KSIKICAgIGlmIG11dCA8IDAuMjU6CiAgICAgICAgb3B0aWthLCBvY29sb3IgPSAiXHUwNDQ3XHUwNDM4XHUwNDQxXHUw"
    "NDQyXHUwNDNlIiwgInJnYmEoODAsMjUwLDEyMywwLjkpIgogICAgZWxpZiBtdXQgPCAwLjU1OgogICAgICAgIG9wdGlrYSwgb2Nv"
    "bG9yID0gIlx1MDQ0MFx1MDQzZVx1MDQzMlx1MDQzZFx1MDQzZSIsICJyZ2JhKDIwMSwxNjgsNzYsMC45KSIKICAgIGVsaWYgbXV0"
    "IDwgMC44OgogICAgICAgIG9wdGlrYSwgb2NvbG9yID0gIlx1MDQ0OFx1MDQ0Mlx1MDQ0Ylx1MDQ0MFx1MDQzOFx1MDQ0MiIsICJy"
    "Z2JhKDI1NSwxNjAsNjAsMC45KSIKICAgIGVsc2U6CiAgICAgICAgb3B0aWthLCBvY29sb3IgPSAiXHUwNDNhXHUwNDNlXHUwNDNi"
    "XHUwNDMxXHUwNDMwXHUwNDQxXHUwNDM4XHUwNDQyIiwgInJnYmEoMjU1LDgwLDgwLDAuOSkiCiAgICByZXR1cm4gKAogICAgICAg"
    "ICc8ZGl2IGNsYXNzPSJ6cG9rIj4nCiAgICAgICAgZic8ZGl2IGNsYXNzPSJ6cG9rLXJvdyI+PGRpdiBjbGFzcz0ienBvay1sYWIi"
    "Plx1MDQzN1x1MDQzMFx1MDQ0MFx1MDQ0Zlx1MDQzNDxiPnt6bmFrfXttdXQ6LjJmfTwvYj48L2Rpdj4nCiAgICAgICAgZic8ZGl2"
    "IGNsYXNzPSJ6cG9rLWJhciB6cG9rLWJhci0temFyeWFkIj48ZGl2IGNsYXNzPSJ6cG9rLW1pZCI+PC9kaXY+JwogICAgICAgIGYn"
    "PGRpdiBjbGFzcz0ienBvay1maWxsIiBzdHlsZT0ibGVmdDp7bGVmdH0lOyB3aWR0aDp7aGFsZn0lOyBiYWNrZ3JvdW5kOnt6Y29s"
    "b3J9OyI+PC9kaXY+PC9kaXY+PC9kaXY+JwogICAgICAgIGYnPGRpdiBjbGFzcz0ienBvay1yb3ciPjxkaXYgY2xhc3M9Inpwb2st"
    "bGFiIj5cdTA0M2VcdTA0M2ZcdTA0NDJcdTA0MzhcdTA0M2FcdTA0MzA8YiBzdHlsZT0iY29sb3I6e29jb2xvcn07Ij57b3B0aWth"
    "fTwvYj48L2Rpdj4nCiAgICAgICAgZic8ZGl2IGNsYXNzPSJ6cG9rLWJhciI+PGRpdiBjbGFzcz0ienBvay1maWxsIiBzdHlsZT0i"
    "d2lkdGg6e2ludCgoMS1tdXQpKjEwMCl9JTsgYmFja2dyb3VuZDp7b2NvbG9yfTsiPjwvZGl2PjwvZGl2PjwvZGl2PicKICAgICAg"
    "ICAnPC9kaXY+JwogICAgKQoKClRPUkdfQ1NTID0gciIiIgpAaW1wb3J0IHVybCgnaHR0cHM6Ly9mb250cy5nb29nbGVhcGlzLmNv"
    "bS9jc3MyP2ZhbWlseT1JbnRlcjp3Z2h0QDQwMDs2MDA7ODAwOzkwMCZmYW1pbHk9SmV0QnJhaW5zK01vbm86d2dodEA0MDA7NjAw"
    "JmRpc3BsYXk9c3dhcCcpOwoKOnJvb3R7CiAgLS1iZzogIzA1MDUxMDsKICAtLXRleHQ6ICNmZmZmZmY7CiAgLS1tdXRlZDogIzg4"
    "OTlhNjsKICAtLWdsYXNzOiByZ2JhKDEzLCAxNywgMjMsIDAuNjApOwogIC0tc3Ryb2tlOiByZ2JhKDI1NSwyNTUsMjU1LDAuMTAp"
    "OwogIC0tZzogIzAwZmY4ODsKICAtLWI6ICMwMGNjZmY7CiAgLS1wOiAjYmQwMGZmOwogIC0tb3JhbmdlOiAjZmY5NTAwOwp9Cgpo"
    "dG1sLCBib2R5IHsgaGVpZ2h0OiAxMDAlOyBtYXJnaW46IDA7IH0KYm9keXsKICB3aWR0aDoxMDB2dzsKICBoZWlnaHQ6MTAwdmg7"
    "CiAgb3ZlcmZsb3c6aGlkZGVuICFpbXBvcnRhbnQ7CiAgYmFja2dyb3VuZDogdHJhbnNwYXJlbnQgIWltcG9ydGFudDsKICBmb250"
    "LWZhbWlseTogSW50ZXIsIHN5c3RlbS11aSwgLWFwcGxlLXN5c3RlbSwgU2Vnb2UgVUksIFJvYm90bywgQXJpYWwsIHNhbnMtc2Vy"
    "aWY7Cn0KCiNiZ3sKICBwb3NpdGlvbjogZml4ZWQ7CiAgaW5zZXQ6IDA7CiAgei1pbmRleDogLTE7CiAgYmFja2dyb3VuZC1zaXpl"
    "OiBjb3ZlcjsKICBiYWNrZ3JvdW5kLXBvc2l0aW9uOiBjZW50ZXI7CiAgYmFja2dyb3VuZC1jb2xvcjogIzA1MDUxMDsKfQojYmc6"
    "OmFmdGVyewogIGNvbnRlbnQ6Jyc7CiAgcG9zaXRpb246YWJzb2x1dGU7CiAgaW5zZXQ6MDsKICBiYWNrZ3JvdW5kOiByZ2JhKDUs"
    "NSwxNiwwLjg4KTsKfQoKLmFwcC1jb250YWluZXJ7CiAgcG9zaXRpb246IGZpeGVkOwogIGluc2V0OiAwOwogIGRpc3BsYXk6IGdy"
    "aWQ7CiAgd2lkdGg6IDEwMHZ3OwogIGhlaWdodDogMTAwdmg7CiAgZ3JpZC10ZW1wbGF0ZS1jb2x1bW5zOiAzMDBweCAxZnIgMjYw"
    "cHg7CiAgZ3JpZC10ZW1wbGF0ZS1yb3dzOiA4MHB4IDFmcjsKICBncmlkLXRlbXBsYXRlLWFyZWFzOgogICAgImhlYWRlciBoZWFk"
    "ZXIgaGVhZGVyIgogICAgImxlZnQgICBzdGFnZSAgcmlnaHQiOwogIGdhcDogMjBweDsKICBwYWRkaW5nOiAyMHB4OwogIGJveC1z"
    "aXppbmc6IGJvcmRlci1ib3g7Cn0KCi5hcmVhLWhlYWRlcnsgZ3JpZC1hcmVhOiBoZWFkZXI7IH0KLmFyZWEtbGVmdHsgZ3JpZC1h"
    "cmVhOiBsZWZ0OyBtaW4taGVpZ2h0OjA7IH0KLmFyZWEtc3RhZ2V7IGdyaWQtYXJlYTogc3RhZ2U7IG1pbi1oZWlnaHQ6MDsgcG9z"
    "aXRpb246IHJlbGF0aXZlOyBvdmVyZmxvdzogaGlkZGVuOyB9Ci5hcmVhLXJpZ2h0eyBncmlkLWFyZWE6IHJpZ2h0OyBtaW4taGVp"
    "Z2h0OjA7IH0KCi5nbGFzc3sKICBiYWNrZ3JvdW5kOiB2YXIoLS1nbGFzcyk7CiAgYm9yZGVyOiAxcHggc29saWQgdmFyKC0tc3Ry"
    "b2tlKTsKICBib3JkZXItcmFkaXVzOiAyMHB4OwogIGJhY2tkcm9wLWZpbHRlcjogYmx1cigxNnB4KTsKICBib3gtc2hhZG93OiAw"
    "IDIwcHggNjBweCByZ2JhKDAsMCwwLDAuNDUpOwogIG1pbi1oZWlnaHQ6IDA7Cn0KCi5zcXVhZC1kZWNrewogIGhlaWdodDogMTAw"
    "JTsKICBkaXNwbGF5OiBmbGV4OwogIGp1c3RpZnktY29udGVudDogY2VudGVyOwogIGFsaWduLWl0ZW1zOiBjZW50ZXI7CiAgcGFk"
    "ZGluZzogMTBweCAxNnB4OwogIGdhcDogMTVweDsKICBvdmVyZmxvdy14OiBhdXRvOwp9CgouYXZhdGFyewogIHdpZHRoOiA0NHB4"
    "OwogIGhlaWdodDogNDRweDsKICBib3JkZXItcmFkaXVzOiA5OTlweDsKICBib3JkZXI6IDJweCBzb2xpZCByZ2JhKDI1NSwyNTUs"
    "MjU1LDAuMTQpOwogIGJhY2tncm91bmQtc2l6ZTogY292ZXI7CiAgYmFja2dyb3VuZC1wb3NpdGlvbjogY2VudGVyIDE4JTsgIC8q"
    "INCy0LXRgNGF0L3Rj9GPINGC0YDQtdGC0Ywg4oCUINC70LjRhtCwINC90LUg0YDQtdC20LXRgiDQv9C+INGG0LXQvdGC0YDRgyAq"
    "LwogIGJhY2tncm91bmQtY29sb3I6IHJnYmEoMjU1LDI1NSwyNTUsMC4wNSk7CiAgZmxleDogMCAwIGF1dG87CiAgZGlzcGxheTog"
    "Z3JpZDsKICBwbGFjZS1pdGVtczogY2VudGVyOwogIGNvbG9yOiByZ2JhKDI1NSwyNTUsMjU1LDAuOTIpOwogIGZvbnQtd2VpZ2h0"
    "OiA4MDA7CiAgZm9udC1zaXplOiAxMXB4OwogIGN1cnNvcjogcG9pbnRlcjsKICB0cmFuc2l0aW9uOiBhbGwgMC4zcyBlYXNlOwog"
    "IHBvc2l0aW9uOiByZWxhdGl2ZTsKfQouYXZhdGFyOmhvdmVyeyBib3JkZXItY29sb3I6IHJnYmEoMCwyMDQsMjU1LDAuNDApOyB0"
    "cmFuc2Zvcm06IHNjYWxlKDEuMDUpOyB9Ci5hdmF0YXIuYWN0aXZlewogIGJvcmRlci1jb2xvcjogcmdiYSgwLDIwNCwyNTUsMC43"
    "NSk7CiAgYm94LXNoYWRvdzogMCAwIDAgMnB4IHJnYmEoMCwyMDQsMjU1LDAuMjUpIGluc2V0LCAwIDAgMzBweCByZ2JhKDAsMjA0"
    "LDI1NSwwLjM1KTsKfQouYXZhdGFyLndvcmtpbmd7CiAgYm9yZGVyLWNvbG9yOiByZ2JhKDI1NSwxNDksMCwwLjc1KTsKICBhbmlt"
    "YXRpb246IHB1bHNlIDEuNXMgZWFzZS1pbi1vdXQgaW5maW5pdGU7Cn0KLmF2YXRhci5kb25lewogIGJvcmRlci1jb2xvcjogcmdi"
    "YSgwLDI1NSwxMzYsMC43NSk7CiAgYm94LXNoYWRvdzogMCAwIDAgMnB4IHJnYmEoMCwyNTUsMTM2LDAuMjUpIGluc2V0LCAwIDAg"
    "MzBweCByZ2JhKDAsMjU1LDEzNiwwLjM1KTsKfQouYXZhdGFyLnZhY2FudHsKICBib3JkZXItc3R5bGU6IGRhc2hlZDsKICBvcGFj"
    "aXR5OiAwLjQ7CiAgY3Vyc29yOiBkZWZhdWx0Owp9CgpAa2V5ZnJhbWVzIHB1bHNlIHsgMCUsIDEwMCUgeyBvcGFjaXR5OiAxOyB9"
    "IDUwJSB7IG9wYWNpdHk6IDAuNjsgfSB9CgoubGVmdC1jb2x7IGhlaWdodDogMTAwJTsgZGlzcGxheTogZmxleDsgZmxleC1kaXJl"
    "Y3Rpb246IGNvbHVtbjsgZ2FwOiAxMnB4OyBtaW4taGVpZ2h0OiAwOyB9CgouY2xpZW50LXBhbmVseyBmbGV4LXNocmluazogMDsg"
    "b3ZlcmZsb3c6IGhpZGRlbjsgfQouYXNzZXQtYmF5eyBoZWlnaHQ6IDEyMHB4OyBmbGV4LXNocmluazogMDsgb3ZlcmZsb3c6IGhp"
    "ZGRlbjsgfQouc2V0dGluZ3MtcGFuZWx7IGZsZXgtZ3JvdzogMTsgbWluLWhlaWdodDogMDsgZGlzcGxheTogZmxleDsgZmxleC1k"
    "aXJlY3Rpb246IGNvbHVtbjsgb3ZlcmZsb3c6IGhpZGRlbjsgfQoKLnBhbmVsLXRpdGxlewogIHBhZGRpbmc6IDEycHggMTZweDsK"
    "ICBjb2xvcjogcmdiYSgyNTUsMjU1LDI1NSwwLjkyKTsKICBmb250LXdlaWdodDogOTAwOwogIGxldHRlci1zcGFjaW5nOiAuMTJl"
    "bTsKICB0ZXh0LXRyYW5zZm9ybTogdXBwZXJjYXNlOwogIGZvbnQtc2l6ZTogMTFweDsKICBib3JkZXItYm90dG9tOiAxcHggc29s"
    "aWQgcmdiYSgyNTUsMjU1LDI1NSwwLjA4KTsKfQoucGFuZWwtYm9keXsgcGFkZGluZzogMTJweCAxNnB4OyBtaW4taGVpZ2h0OiAw"
    "OyBvdmVyZmxvdzogYXV0bzsgfQoKLmZpbGUtbGlzdHsgcGFkZGluZzogOHB4IDEycHg7IG1heC1oZWlnaHQ6IDUwcHg7IG92ZXJm"
    "bG93LXk6IGF1dG87IGZvbnQtZmFtaWx5OiBtb25vc3BhY2U7IGZvbnQtc2l6ZTogMTFweDsgfQoKLnJpZ2h0LWNvbHsgaGVpZ2h0"
    "OiAxMDAlOyBkaXNwbGF5OiBmbGV4OyBmbGV4LWRpcmVjdGlvbjogY29sdW1uOyBqdXN0aWZ5LWNvbnRlbnQ6IGZsZXgtc3RhcnQ7"
    "IGdhcDogMTJweDsgfQoucmlnaHQtdG9wLXNsb3R7CiAgZmxleC1zaHJpbms6IDA7CiAgaGVpZ2h0OiAyNDBweDsKICBib3JkZXIt"
    "cmFkaXVzOiAyMHB4OwogIGJvcmRlcjogMXB4IGRhc2hlZCByZ2JhKDI1NSwyNTUsMjU1LDAuMTQpOwogIGJhY2tncm91bmQ6IHJn"
    "YmEoMjU1LDI1NSwyNTUsMC4wNCk7CiAgZGlzcGxheTogZ3JpZDsKICBwbGFjZS1pdGVtczogY2VudGVyOwogIGNvbG9yOiByZ2Jh"
    "KDI1NSwyNTUsMjU1LDAuNTUpOwogIGZvbnQtc2l6ZTogMTFweDsKICBwYWRkaW5nOiAxMnB4OwogIHRleHQtYWxpZ246IGNlbnRl"
    "cjsKICBvdmVyZmxvdzogaGlkZGVuOwp9CgoubmVvbi1idG57CiAgaGVpZ2h0OiA1NnB4OwogIHdpZHRoOiAxMDAlOwogIGJvcmRl"
    "ci1yYWRpdXM6IDE4cHg7CiAgYmFja2dyb3VuZDogdHJhbnNwYXJlbnQ7CiAgY29sb3I6IHJnYmEoMjU1LDI1NSwyNTUsMC45Mik7"
    "CiAgYm9yZGVyOiAxcHggc29saWQgcmdiYSgyNTUsMjU1LDI1NSwwLjEwKTsKICBmb250LXdlaWdodDogOTAwOwogIGxldHRlci1z"
    "cGFjaW5nOiAuMTBlbTsKICBjdXJzb3I6IHBvaW50ZXI7CiAgdHJhbnNpdGlvbjogYWxsIDAuM3MgZWFzZTsKfQoubmVvbi1idG46"
    "ZGlzYWJsZWR7IG9wYWNpdHk6IDAuNDsgY3Vyc29yOiBub3QtYWxsb3dlZDsgfQoKLnN0YWdlLW1vbml0b3J7IGhlaWdodDogMTAw"
    "JTsgZGlzcGxheTogZmxleDsgZmxleC1kaXJlY3Rpb246IGNvbHVtbjsgb3ZlcmZsb3c6IGhpZGRlbjsgfQouc3RhZ2UtdG9vbGJh"
    "cnsKICBoZWlnaHQ6IDYwcHg7CiAgZGlzcGxheTogZ3JpZDsKICBncmlkLXRlbXBsYXRlLWNvbHVtbnM6IDIwMHB4IDFmciAyMDBw"
    "eDsKICBhbGlnbi1pdGVtczogY2VudGVyOwogIHBhZGRpbmc6IDAgMTJweDsKICBib3JkZXItYm90dG9tOiAxcHggc29saWQgcmdi"
    "YSgyNTUsMjU1LDI1NSwwLjA4KTsKICBmbGV4LXNocmluazogMDsKICBiYWNrZ3JvdW5kOiByZ2JhKDEzLCAxNywgMjMsIDAuOTUp"
    "OwogIGJhY2tkcm9wLWZpbHRlcjogYmx1cigxNnB4KTsKICB6LWluZGV4OiAxMDsKfQoKLm1vbml0b3ItdXRpbHN7IGRpc3BsYXk6"
    "ZmxleDsgZ2FwOiAxMnB4OyB9Ci5zdGFnZS1jb250ZW50ewogIGZsZXg6IDE7CiAgbWluLWhlaWdodDogMDsKICBvdmVyZmxvdzog"
    "aGlkZGVuOwogIHBhZGRpbmc6IDE4cHg7CiAgcGFkZGluZy1ib3R0b206IDEzMHB4Owp9Cgouc3BsaXQtdmlld3sgaGVpZ2h0OiAx"
    "MDAlOyBkaXNwbGF5OiBmbGV4OyBnYXA6IDE4cHg7IG1pbi1oZWlnaHQ6IDA7IG92ZXJmbG93OiBoaWRkZW47IH0KLmNoYXQtbG9n"
    "LCAudmlld2VyewogIGZsZXg6IDE7CiAgbWluLWhlaWdodDogMDsKICBtaW4td2lkdGg6IDA7CiAgYm9yZGVyLXJhZGl1czogMThw"
    "eDsKICBib3JkZXI6IDFweCBzb2xpZCByZ2JhKDI1NSwyNTUsMjU1LDAuMDgpOwogIGJhY2tncm91bmQ6IHJnYmEoMjU1LDI1NSwy"
    "NTUsMC4wMyk7CiAgb3ZlcmZsb3cteTogYXV0bzsKICBvdmVyZmxvdy14OiBoaWRkZW47CiAgcGFkZGluZzogMTRweDsKICBmb250"
    "LWZhbWlseTogbW9ub3NwYWNlOwogIGZvbnQtc2l6ZTogMTNweDsKICBjb2xvcjogcmdiYSgyNTUsMjU1LDI1NSwwLjg2KTsKICB3"
    "aGl0ZS1zcGFjZTogcHJlLXdyYXA7CiAgd29yZC13cmFwOiBicmVhay13b3JkOwogIHdvcmQtYnJlYWs6IGJyZWFrLXdvcmQ7Cn0K"
    "LnZpZXdlcnsgYm9yZGVyLWNvbG9yOiByZ2JhKDAsMjA0LDI1NSwwLjMwKTsgfQoKLmZsb2F0aW5nLWNvbnNvbGV7CiAgcG9zaXRp"
    "b246IGFic29sdXRlOwogIGxlZnQ6IDUwJTsKICBib3R0b206IDIwcHg7CiAgdHJhbnNmb3JtOiB0cmFuc2xhdGVYKC01MCUpOwog"
    "IHdpZHRoOiBtaW4oODIwcHgsIGNhbGMoMTAwJSAtIDgwcHgpKTsKICB6LWluZGV4OiA1MDsKICBkaXNwbGF5OiBmbGV4OwogIGFs"
    "aWduLWl0ZW1zOiBjZW50ZXI7CiAgZ2FwOiA4cHg7CiAgcGFkZGluZzogMTBweCAxMnB4OwogIGJvcmRlci1yYWRpdXM6IDUwcHg7"
    "CiAgYmFja2dyb3VuZDogcmdiYSgxMywgMTcsIDIzLCAwLjg1KTsKICBib3JkZXI6IDFweCBzb2xpZCByZ2JhKDI1NSwyNTUsMjU1"
    "LDAuMTUpOwogIGJhY2tkcm9wLWZpbHRlcjogYmx1cigyMHB4KTsKICBib3gtc2hhZG93OiAwIDEwcHggNDBweCByZ2JhKDAsMCww"
    "LDAuNSk7Cn0KCi5mbG9hdGluZy1jb25zb2xlIGlucHV0ewogIHdpZHRoOiAxMDAlOwogIGJvcmRlci1yYWRpdXM6IDQwcHg7CiAg"
    "Ym9yZGVyOiAxcHggc29saWQgcmdiYSgyNTUsMjU1LDI1NSwwLjEwKTsKICBiYWNrZ3JvdW5kOiByZ2JhKDI1NSwyNTUsMjU1LDAu"
    "MDYpOwogIHBhZGRpbmc6IDEycHggMTZweDsKICBjb2xvcjogcmdiYSgyNTUsMjU1LDI1NSwwLjkyKTsKICBvdXRsaW5lOiBub25l"
    "OwogIGZvbnQtZmFtaWx5OiBtb25vc3BhY2U7Cn0KCi5zZW5kLWJ1dHRvbnsKICBib3JkZXItcmFkaXVzOiA0MHB4ICFpbXBvcnRh"
    "bnQ7CiAgYm9yZGVyOiAycHggc29saWQgcmdiYSgwLDIwNCwyNTUsMC41NSkgIWltcG9ydGFudDsKICBiYWNrZ3JvdW5kOiBsaW5l"
    "YXItZ3JhZGllbnQoMTM1ZGVnLCByZ2JhKDAsMjA0LDI1NSwwLjMwKSwgcmdiYSgxODksMCwyNTUsMC4yNSkpICFpbXBvcnRhbnQ7"
    "CiAgY29sb3I6IHJnYmEoMjU1LDI1NSwyNTUsMC45OCkgIWltcG9ydGFudDsKICBmb250LXdlaWdodDogOTAwICFpbXBvcnRhbnQ7"
    "CiAgcGFkZGluZzogMTJweCAyNHB4ICFpbXBvcnRhbnQ7CiAgY3Vyc29yOiBwb2ludGVyICFpbXBvcnRhbnQ7Cn0KCi5jaGF0LW1z"
    "Zy11c2VyIHsKICBiYWNrZ3JvdW5kOiByZ2JhKDAsIDIwNCwgMjU1LCAwLjEpOwogIGJvcmRlci1sZWZ0OiAzcHggc29saWQgcmdi"
    "YSgwLCAyMDQsIDI1NSwgMC42KTsKICBwYWRkaW5nOiA4cHggMTJweDsKICBtYXJnaW46IDhweCAwOwogIGJvcmRlci1yYWRpdXM6"
    "IDAgOHB4IDhweCAwOwp9Ci5jaGF0LW1zZy1hc3Npc3RhbnQgewogIGJhY2tncm91bmQ6IHJnYmEoMCwgMjU1LCAxMzYsIDAuMDgp"
    "OwogIGJvcmRlci1sZWZ0OiAzcHggc29saWQgcmdiYSgwLCAyNTUsIDEzNiwgMC42KTsKICBwYWRkaW5nOiA4cHggMTJweDsKICBt"
    "YXJnaW46IDhweCAwOwogIGJvcmRlci1yYWRpdXM6IDAgOHB4IDhweCAwOwp9Ci5jaGF0LW1zZy1zeXN0ZW0gewogIGNvbG9yOiBy"
    "Z2JhKDI1NSwyNTUsMjU1LDAuNSk7CiAgZm9udC1zdHlsZTogaXRhbGljOwogIHBhZGRpbmc6IDRweCAwOwp9CgouenBva3sgcGFk"
    "ZGluZzoxMHB4IDE2cHg7IGRpc3BsYXk6ZmxleDsgZmxleC1kaXJlY3Rpb246Y29sdW1uOyBnYXA6OXB4OyB9Ci56cG9rLXJvd3sg"
    "ZGlzcGxheTpmbGV4OyBmbGV4LWRpcmVjdGlvbjpjb2x1bW47IGdhcDozcHg7IH0KLnpwb2stbGFieyBkaXNwbGF5OmZsZXg7IGp1"
    "c3RpZnktY29udGVudDpzcGFjZS1iZXR3ZWVuOyBmb250LXNpemU6MC41NnJlbTsKICB0ZXh0LXRyYW5zZm9ybTp1cHBlcmNhc2U7"
    "IGxldHRlci1zcGFjaW5nOjAuMDhlbTsgY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjUpOyB9Ci56cG9rLWxhYiBieyBjb2xvcjpy"
    "Z2JhKDI1NSwyNTUsMjU1LDAuODUpOyBmb250LXdlaWdodDo3MDA7IH0KLnpwb2stYmFyeyBoZWlnaHQ6NnB4OyBib3JkZXItcmFk"
    "aXVzOjRweDsgYmFja2dyb3VuZDpyZ2JhKDI1NSwyNTUsMjU1LDAuMDgpOyBvdmVyZmxvdzpoaWRkZW47CiAgcG9zaXRpb246cmVs"
    "YXRpdmU7IH0KLnpwb2stYmFyLS16YXJ5YWQgLnpwb2stZmlsbHsgcG9zaXRpb246YWJzb2x1dGU7IHRvcDowOyBib3R0b206MDsg"
    "fQouenBvay1taWR7IHBvc2l0aW9uOmFic29sdXRlOyBsZWZ0OjUwJTsgdG9wOi0ycHg7IGJvdHRvbTotMnB4OyB3aWR0aDoxcHg7"
    "CiAgYmFja2dyb3VuZDpyZ2JhKDI1NSwyNTUsMjU1LDAuNCk7IHotaW5kZXg6MjsgfQouenBvay1maWxseyBoZWlnaHQ6MTAwJTsg"
    "Ym9yZGVyLXJhZGl1czo0cHg7IH0KCi5uaWNlZ3VpLWNvbnRlbnQgeyBvdmVyZmxvdzogaGlkZGVuICFpbXBvcnRhbnQ7IGhlaWdo"
    "dDogMTAwJSAhaW1wb3J0YW50OyB9Ci5hcmVhLXN0YWdlIHsgb3ZlcmZsb3c6IGhpZGRlbiAhaW1wb3J0YW50OyB9Ci5hcmVhLXN0"
    "YWdlID4gKiB7IG92ZXJmbG93OiBoaWRkZW4gIWltcG9ydGFudDsgbWluLWhlaWdodDogMCAhaW1wb3J0YW50OyBtYXgtaGVpZ2h0"
    "OiAxMDAlICFpbXBvcnRhbnQ7IH0KLnN0YWdlLW1vbml0b3IgeyBvdmVyZmxvdzogaGlkZGVuICFpbXBvcnRhbnQ7IGhlaWdodDog"
    "MTAwJSAhaW1wb3J0YW50OyB9Ci5zdGFnZS1tb25pdG9yID4gKiB7IG1pbi1oZWlnaHQ6IDAgIWltcG9ydGFudDsgfQouc3RhZ2Ut"
    "dG9vbGJhciB7IGZsZXgtc2hyaW5rOiAwICFpbXBvcnRhbnQ7IG92ZXJmbG93OiBoaWRkZW4gIWltcG9ydGFudDsgfQouc3RhZ2Ut"
    "Y29udGVudCB7IGZsZXg6IDEgMSAwICFpbXBvcnRhbnQ7IG1pbi1oZWlnaHQ6IDAgIWltcG9ydGFudDsgb3ZlcmZsb3c6IGhpZGRl"
    "biAhaW1wb3J0YW50OyBtYXgtaGVpZ2h0OiBjYWxjKDEwMCUgLSA2MHB4KSAhaW1wb3J0YW50OyB9Ci5zdGFnZS1jb250ZW50ID4g"
    "KiB7IG1pbi1oZWlnaHQ6IDAgIWltcG9ydGFudDsgbWF4LWhlaWdodDogMTAwJSAhaW1wb3J0YW50OyBvdmVyZmxvdzogaGlkZGVu"
    "ICFpbXBvcnRhbnQ7IH0KLnNwbGl0LXZpZXcgeyBoZWlnaHQ6IDEwMCUgIWltcG9ydGFudDsgbWluLWhlaWdodDogMCAhaW1wb3J0"
    "YW50OyBvdmVyZmxvdzogaGlkZGVuICFpbXBvcnRhbnQ7IH0KLnNwbGl0LXZpZXcgPiAqIHsgbWluLWhlaWdodDogMCAhaW1wb3J0"
    "YW50OyBvdmVyZmxvdzogaGlkZGVuICFpbXBvcnRhbnQ7IH0KLmNoYXQtbG9nLCAudmlld2VyIHsgZmxleDogMSAxIDAgIWltcG9y"
    "dGFudDsgbWluLWhlaWdodDogMCAhaW1wb3J0YW50OyBtYXgtaGVpZ2h0OiAxMDAlICFpbXBvcnRhbnQ7IG92ZXJmbG93LXk6IGF1"
    "dG8gIWltcG9ydGFudDsgb3ZlcmZsb3cteDogaGlkZGVuICFpbXBvcnRhbnQ7IH0KIiIiCgoKZGVmIHBhZ2VfdG9yZyh0c2VoX2lk"
    "OiBzdHIgPSAi0YLQvtGA0LPQvtCy0YvQuV/RhdCw0L7RgSIpIC0+IE5vbmU6CiAgICAiIiLQmtCw0LHQuNC90LXRgiDQodC+0LLQ"
    "tdGC0LAg0JHQuNGA0LbQuCDigJQg0YLQvtGCINC20LUsINGH0YLQviDQsdGL0LsgL2V4Y2hhbmdlINCyIC0yLiIiIgoKICAgIHN0"
    "YXRpY19wcmVmaXggPSAidG9yZy1zdGF0aWMiCiAgICByb3N0ZXIgPSBfYnVpbGRfcm9zdGVyKHN0YXRpY19wcmVmaXgpCgogICAg"
    "IyDilIDilIAg0YHQvtGB0YLQvtGP0L3QuNC1INGB0YLRgNCw0L3QuNGG0YsgKNC60LDQuiDQsdGL0LvQviDQsiB1aV9leGNoYW5n"
    "ZS5weSkg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACiAgICBzdGF0ZSA9IHsKICAgICAgICAiYWN0aXZlX2FnZW50Ijog"
    "IkEwMSIsCiAgICAgICAgImNoYXRfaGlzdG9yeSI6IFtdLAogICAgICAgICJyZXBvcnRzIjoge30sCiAgICAgICAgInVwbG9hZGVk"
    "X2ZpbGVzIjogW10sCiAgICAgICAgImxvYWRlZF9hc3NldHMiOiBbXSwKICAgICAgICAiYWN0aXZlX2Fzc2V0IjogTm9uZSwKICAg"
    "ICAgICAiaXNrcmFfc2lnbmFsIjoge30sCiAgICAgICAgImlza3JhX2xhc3RfcnVuIjogTm9uZSwKICAgICAgICAiaXNrcmFfc3Rh"
    "dHMiOiB7fSwKICAgICAgICAibWFya2V0Ijoge30sCiAgICAgICAgInJ1bm5pbmciOiBGYWxzZSwKICAgICAgICAibW9kZSI6ICJy"
    "ZWFsIiwKICAgICAgICAiYmFyc190b19saXZlIjogMSwKICAgICAgICAic3RvcF9yZXF1ZXN0ZWQiOiBGYWxzZSwKICAgICAgICAi"
    "dGVzdGVyX3J1bm5pbmciOiBGYWxzZSwKICAgICAgICAibW9yal9sYXN0X3J1biI6IE5vbmUsCiAgICAgICAgInBhbmljX2xhc3Rf"
    "cnVuIjogTm9uZSwKICAgICAgICAiaGFuc19sYXN0X3J1biI6IE5vbmUsCiAgICAgICAgImFya2hpdl9sYXN0X3J1biI6IE5vbmUs"
    "CiAgICAgICAgImFya2hpdl9zaWduYWwiOiB7fSwKICAgICAgICAiYXJraGl2X3N0YXRzIjoge30sCiAgICAgICAgImFya2hpdl9k"
    "aWdlc3QiOiB7fSwKICAgIH0KCiAgICBjaGF0X2xvZ19yZWY6IGRpY3Rbc3RyLCBBbnldID0geyJlbGVtZW50IjogTm9uZX0KICAg"
    "IHRvb2xiYXJfcmVmczogZGljdFtzdHIsIEFueV0gPSB7fQogICAgdmlld2VyX3JlZjogICBkaWN0W3N0ciwgQW55XSA9IHsiZWxl"
    "bWVudCI6IE5vbmV9CiAgICBmaWxlc19yZWY6ICAgIGRpY3Rbc3RyLCBBbnldID0geyJlbGVtZW50IjogTm9uZX0KICAgIGF2YXRh"
    "cl9yZWY6ICAgZGljdFtzdHIsIEFueV0gPSB7ImVsZW1lbnQiOiBOb25lfQogICAgdml0YWxzX3JlZjogICBkaWN0W3N0ciwgQW55"
    "XSA9IHsiZWxlbWVudCI6IE5vbmV9ICAgIyDQt9Cw0YDRj9C0L9C+0L/RgtC40LrQsCDRgNC10LfQuNC00LXQvdGC0LAg4oCUINC6"
    "0LDQuiDQstC10LfQtNC1INCyINCz0L7RgNC+0LTQtQogICAgc3RhdHNfcmVmOiAgICBkaWN0W3N0ciwgQW55XSA9IHsiZWxlbWVu"
    "dCI6IE5vbmV9CiAgICBhdmF0YXJzX3JlZjogIGRpY3Rbc3RyLCBBbnldID0geyJlbGVtZW50cyI6IHt9fQogICAgaW5wdXRfcmVm"
    "OiAgICBkaWN0W3N0ciwgQW55XSA9IHsiZWxlbWVudCI6IE5vbmV9CgogICAgdWkuYWRkX2hlYWRfaHRtbChmIjxzdHlsZT57VE9S"
    "R19DU1N9PC9zdHlsZT4iKQogICAgX2NlaDAgPSByZWcuZ2V0X2NlaCh0c2VoX2lkLCBLVkFSVEFMKQogICAgX2JnX3VybCA9IF9i"
    "dWlsZGluZ19iZ191cmwoX2NlaDAuZ2V0KCLQt9C00LDQvdC40LUiLCAiIikpIGlmIF9jZWgwIGVsc2UgIiIKICAgIF9iZ19zdHls"
    "ZSA9IGYiIHN0eWxlPVwiYmFja2dyb3VuZC1pbWFnZTp1cmwoJ3tfYmdfdXJsfScpO1wiIiBpZiBfYmdfdXJsIGVsc2UgIiIKICAg"
    "IHVpLmh0bWwoZic8ZGl2IGlkPSJiZyJ7X2JnX3N0eWxlfT48L2Rpdj4nKQoKICAgICMg4pSA4pSAINGH0LDRgiDilIDilIDilIDi"
    "lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi"
    "lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKICAgIGRl"
    "ZiB1cGRhdGVfY2hhdF9kaXNwbGF5KCk6CiAgICAgICAgaWYgbm90IGNoYXRfbG9nX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAg"
    "ICByZXR1cm4KICAgICAgICBjaGF0X2xvZ19yZWZbImVsZW1lbnQiXS5jbGVhcigpCiAgICAgICAgd2l0aCBjaGF0X2xvZ19yZWZb"
    "ImVsZW1lbnQiXToKICAgICAgICAgICAgaWYgbm90IHN0YXRlWyJjaGF0X2hpc3RvcnkiXToKICAgICAgICAgICAgICAgIHVpLmh0"
    "bWwoJzxkaXYgY2xhc3M9ImNoYXQtbXNnLXN5c3RlbSI+U1lTVEVNOiDQkdC40YDQttCwINCz0L7RgtC+0LLQsC48L2Rpdj4nKQog"
    "ICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgZm9yIG1zZyBpbiBzdGF0ZVsiY2hhdF9oaXN0b3J5Il06CiAgICAgICAg"
    "ICAgICAgICAgICAgcm9sZSA9IG1zZy5nZXQoInJvbGUiLCAidXNlciIpCiAgICAgICAgICAgICAgICAgICAgY29udGVudCA9IG1z"
    "Zy5nZXQoImNvbnRlbnQiLCAiIikKICAgICAgICAgICAgICAgICAgICB3aG8gPSBtc2cuZ2V0KCJhZ2VudCIsICIiKQogICAgICAg"
    "ICAgICAgICAgICAgIGlmIHJvbGUgPT0gInVzZXIiOgogICAgICAgICAgICAgICAgICAgICAgICB1aS5odG1sKGYnPGRpdiBjbGFz"
    "cz0iY2hhdC1tc2ctdXNlciI+PGI+0KjQldCkOjwvYj4ge2NvbnRlbnR9PC9kaXY+JykKICAgICAgICAgICAgICAgICAgICBlbHNl"
    "OgogICAgICAgICAgICAgICAgICAgICAgICB1aS5odG1sKGYnPGRpdiBjbGFzcz0iY2hhdC1tc2ctYXNzaXN0YW50Ij48Yj57d2hv"
    "fTo8L2I+IHtjb250ZW50fTwvZGl2PicpCgogICAgZGVmIHVwZGF0ZV92aWV3ZXIoY29udGVudDogc3RyKToKICAgICAgICBpZiBu"
    "b3Qgdmlld2VyX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAgICByZXR1cm4KICAgICAgICB2aWV3ZXJfcmVmWyJlbGVtZW50Il0u"
    "Y2xlYXIoKQogICAgICAgIHdpdGggdmlld2VyX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAgICB1aS5tYXJrZG93bihjb250ZW50"
    "KQoKICAgICMg4pSA4pSAINCw0LLQsNGC0LDRgCDQsNC60YLQuNCy0L3QvtCz0L4gKNC/0YDQsNCy0LDRjyDQutC+0LvQvtC90LrQ"
    "sCkg4oCUINGC0LXQv9C10YDRjCDQoNCV0JfQmNCU0JXQndCiIOKUgOKUgOKUgOKUgAogICAgZGVmIHVwZGF0ZV9hdmF0YXIoKToK"
    "ICAgICAgICBpZiBub3QgYXZhdGFyX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAgICByZXR1cm4KICAgICAgICBvbGRfaWQgPSBz"
    "dGF0ZVsiYWN0aXZlX2FnZW50Il0KICAgICAgICByb3cgPSBfYWdlbnRfcm93KHJvc3Rlciwgb2xkX2lkKQogICAgICAgIGxhYmVs"
    "ID0gX2FnZW50X2xhYmVsKHJvc3Rlciwgb2xkX2lkKQogICAgICAgIGF2YXRhcl9yZWZbImVsZW1lbnQiXS5jbGVhcigpCiAgICAg"
    "ICAgd2l0aCBhdmF0YXJfcmVmWyJlbGVtZW50Il06CiAgICAgICAgICAgIGF2ID0gX2F2YXRhcl91cmxfZm9yKHJvd1sicmVzaWRl"
    "bnQiXVsi0L/QsNC/0LrQsCJdLCBzdGF0aWNfcHJlZml4KSBpZiAocm93IGFuZCByb3dbInJlc2lkZW50Il0pIGVsc2UgIiIKICAg"
    "ICAgICAgICAgaW1nX2h0bWwgPSAoZic8aW1nIHNyYz0ie2F2fSIgc3R5bGU9IndpZHRoOjEwMCU7aGVpZ2h0OjEwMCU7b2JqZWN0"
    "LWZpdDpjb3ZlcjsnCiAgICAgICAgICAgICAgICAgICAgICAgZidib3JkZXItcmFkaXVzOjEycHg7b3BhY2l0eTowLjg1OyIgb25l"
    "cnJvcj0idGhpcy5zdHlsZS5kaXNwbGF5PVwnbm9uZVwnIj4nCiAgICAgICAgICAgICAgICAgICAgICAgaWYgYXYgZWxzZSAiIikK"
    "ICAgICAgICAgICAgdmFjYW5jeV9ub3RlID0gIiIgaWYgKHJvdyBhbmQgcm93WyJyZXNpZGVudCJdKSBlbHNlICc8ZGl2IHN0eWxl"
    "PSJmb250LXNpemU6MC42NXJlbTtjb2xvcjpyZ2JhKDI1NSw4MCw4MCwwLjYpOyI+0LLQsNC60LDQvdGB0LjRjzwvZGl2PicKICAg"
    "ICAgICAgICAgdWkuaHRtbChmJycnCiAgICAgICAgICAgICAgICA8ZGl2IHN0eWxlPSJwb3NpdGlvbjpyZWxhdGl2ZTsgd2lkdGg6"
    "MTAwJTsgaGVpZ2h0OjEwMCU7IG1pbi1oZWlnaHQ6MjAwcHg7Ij4KICAgICAgICAgICAgICAgICAgICB7aW1nX2h0bWx9CiAgICAg"
    "ICAgICAgICAgICAgICAgPGRpdiBzdHlsZT0icG9zaXRpb246YWJzb2x1dGU7IGJvdHRvbTowOyBsZWZ0OjA7IHJpZ2h0OjA7CiAg"
    "ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgcGFkZGluZzoxNXB4OyBiYWNrZ3JvdW5kOmxpbmVhci1ncmFkaWVudCh0cmFu"
    "c3BhcmVudCwgcmdiYSgwLDAsMCwwLjgpKTsKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBib3JkZXItcmFkaXVzOjAg"
    "MCAxMnB4IDEycHg7Ij4KICAgICAgICAgICAgICAgICAgICAgICAgPGRpdiBzdHlsZT0iZm9udC1zaXplOjAuNjVyZW07IGNvbG9y"
    "OnJnYmEoMjU1LDI1NSwyNTUsMC41KTsKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgbGV0dGVyLXNwYWNpbmc6"
    "MC4xNWVtOyI+0JDQmtCi0JjQktCd0KvQmSDQkNCT0JXQndCiPC9kaXY+CiAgICAgICAgICAgICAgICAgICAgICAgIDxkaXYgc3R5"
    "bGU9ImZvbnQtc2l6ZToxLjNyZW07IGZvbnQtd2VpZ2h0OjcwMDsgY29sb3I6IzAwZmY4ODsiPntvbGRfaWR9PC9kaXY+CiAgICAg"
    "ICAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImZvbnQtc2l6ZTowLjhyZW07IGNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC44"
    "KTsiPntsYWJlbH08L2Rpdj4KICAgICAgICAgICAgICAgICAgICAgICAge3ZhY2FuY3lfbm90ZX0KICAgICAgICAgICAgICAgICAg"
    "ICA8L2Rpdj4KICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAnJycpCgogICAgIyDilIDilIAg0LbQuNCy0YvQtSDQ"
    "v9C+0LrQsNC30LDRgtC10LvQuCDRgNC10LfQuNC00LXQvdGC0LAgKNC30LDRgNGP0LQv0L7Qv9GC0LjQutCwKSDigJQg0LrQsNC6"
    "INCy0LXQt9C00LUg0LIg0LPQvtGA0L7QtNC1IOKUgOKUgAogICAgZGVmIHVwZGF0ZV92aXRhbHMoKToKICAgICAgICBpZiBub3Qg"
    "dml0YWxzX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAgICByZXR1cm4KICAgICAgICB2aXRhbHNfcmVmWyJlbGVtZW50Il0uY2xl"
    "YXIoKQogICAgICAgIHJvdyA9IF9hZ2VudF9yb3cocm9zdGVyLCBzdGF0ZVsiYWN0aXZlX2FnZW50Il0pCiAgICAgICAgd2l0aCB2"
    "aXRhbHNfcmVmWyJlbGVtZW50Il06CiAgICAgICAgICAgIGlmIHJvdyBhbmQgcm93WyJyZXNpZGVudCJdOgogICAgICAgICAgICAg"
    "ICAgcCA9IF9yZWFkX2pzb24oUGF0aChyb3dbInJlc2lkZW50Il1bItC/0LDQv9C60LAiXSkgLyAicGFzc3BvcnQuanNvbiIpIG9y"
    "IHt9CiAgICAgICAgICAgICAgICBjaGFyZ2UgPSBmbG9hdChwLmdldCgiX2NoYXJnZSIsIDAuMCkgb3IgMC4wKQogICAgICAgICAg"
    "ICAgICAgdWkuaHRtbChfYmFyX2h0bWwoY2hhcmdlKSkKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHVpLmh0bWwo"
    "JzxkaXYgc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC4zKTsgZm9udC1zaXplOjEwcHg7ICcKICAgICAgICAgICAgICAg"
    "ICAgICAgICAgJ3BhZGRpbmc6OHB4IDE2cHg7Ij7igJQg0LLQsNC60LDQvdGB0LjRjywg0L/QvtC60LDQt9GL0LLQsNGC0Ywg0L3Q"
    "tdGH0LXQs9C+IOKAlDwvZGl2PicpCgogICAgIyDilIDilIAg0L/RgNC40LHQvtGA0Ysg0L/QvtC0INCw0LLQsNGC0LDRgNC+0Lwg"
    "KNC/0LXRgNC10L3QtdGB0LXQvdC+INCx0LXQtyDQuNC30LzQtdC90LXQvdC40Lkg0L/QviDRgdGD0YLQuCkg4pSACiAgICBkZWYg"
    "dXBkYXRlX3N0YXRzX3BhbmVsKCk6CiAgICAgICAgaWYgbm90IHN0YXRzX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAgICByZXR1"
    "cm4KICAgICAgICBzaWcgPSBzdGF0ZVsiaXNrcmFfc2lnbmFsIl0KICAgICAgICBzdCAgPSBzdGF0ZVsiaXNrcmFfc3RhdHMiXQog"
    "ICAgICAgIG1rICA9IHN0YXRlWyJtYXJrZXQiXQogICAgICAgIHN0YXRzX3JlZlsiZWxlbWVudCJdLmNsZWFyKCkKCiAgICAgICAg"
    "aWYgc3RhdGVbImFjdGl2ZV9hZ2VudCJdID09ICJBMDIiOgogICAgICAgICAgICBtc2lnID0gc3RhdGUuZ2V0KCJtb3JqX3NpZ25h"
    "bCIsIHt9KQogICAgICAgICAgICBtc3QgID0gc3RhdGUuZ2V0KCJtb3JqX3N0YXRzIiwge30pCiAgICAgICAgICAgIHJiICAgPSBz"
    "dGF0ZS5nZXQoIm1vcmpfcnViYmVyIiwge30pCiAgICAgICAgICAgIG1tayAgPSBzdGF0ZS5nZXQoIm1vcmpfbWFya2V0Iiwge30p"
    "CiAgICAgICAgICAgIGlmIG5vdCBtc2lnOgogICAgICAgICAgICAgICAgd2l0aCBzdGF0c19yZWZbImVsZW1lbnQiXToKICAgICAg"
    "ICAgICAgICAgICAgICB1aS5odG1sKCc8ZGl2IHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuMyk7IGZvbnQtc2l6ZTox"
    "MXB4OyAnCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAncGFkZGluZzoxMHB4OyB0ZXh0LWFsaWduOmNlbnRlcjsiPtCc0L7R"
    "gNC2INC10YnRkSDQvdC1INGB0LzQvtGC0YDQtdC7IOKAlCAnCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAn0L3QsNC20LzQ"
    "uCDQoNCr0J3QntCaICjQvdGD0LbQtdC9INGB0LjQs9C90LDQuyDQmNGB0LrRgNGLKTwvZGl2PicpCiAgICAgICAgICAgICAgICBy"
    "ZXR1cm4KICAgICAgICAgICAgbXN0YXR1cyA9IG1zaWcuZ2V0KCJtb3JqX3N0YXR1cyIsICLigJQiKQogICAgICAgICAgICBzdF9j"
    "b2xvciA9IHsiQVdBS0UiOiAiIzAwZmY4OCIsICJXQUtJTkciOiAiI2ZmYjQwMCIsCiAgICAgICAgICAgICAgICAgICAgICAgICJT"
    "TEVFUElORyI6ICJyZ2JhKDI1NSwyNTUsMjU1LDAuNCkifS5nZXQobXN0YXR1cywgInJnYmEoMjU1LDI1NSwyNTUsMC40KSIpCiAg"
    "ICAgICAgICAgIHBlYWsgPSBtc2lnLmdldCgidGVuc2lvbl9wZWFrIikKICAgICAgICAgICAgcGVha190eHQgPSAi8J+UtCDQndCQ"
    "INCf0KDQldCU0JXQm9CVIiBpZiBwZWFrIGVsc2UgItCy0Y/Qu9C+IgogICAgICAgICAgICBwZWFrX2NvbG9yID0gIiNmZjUwNTAi"
    "IGlmIHBlYWsgZWxzZSAicmdiYSgyNTUsMjU1LDI1NSwwLjQpIgogICAgICAgICAgICByYXRpbyA9IHJiLmdldCgidGVuc2lvbl9y"
    "YXRpbyIpCiAgICAgICAgICAgIHJhdGlvX3R4dCA9IGYie3JhdGlvfSIgaWYgcmF0aW8gaXMgbm90IE5vbmUgZWxzZSAi4oCUIgog"
    "ICAgICAgICAgICBkaXN0ID0gcmIuZ2V0KCJkaXN0YW5jZV9ub3ciKQogICAgICAgICAgICBkaXN0X3R4dCA9IGYie2Rpc3R9INC/"
    "0YIiIGlmIGRpc3QgaXMgbm90IE5vbmUgZWxzZSAi4oCUIgogICAgICAgICAgICB3YXZlMSA9ICLinJMiIGlmIG1zaWcuZ2V0KCJ3"
    "YXZlXzFfdmFsaWRhdGVkIikgZWxzZSAi4oCUIgogICAgICAgICAgICBhbHN0ID0gKG1zaWcuZ2V0KCJhbGxpZ2F0b3Jfc3RhdGUi"
    "KSBvciB7fSkKICAgICAgICAgICAgYm9wZW4gPSBhbHN0LmdldCgiYmFyc19vcGVuIiwgIuKAlCIpCiAgICAgICAgICAgIHdpdGgg"
    "c3RhdHNfcmVmWyJlbGVtZW50Il06CiAgICAgICAgICAgICAgICB1aS5odG1sKGYnJycKICAgICAgICAgICAgICAgIDxkaXYgc3R5"
    "bGU9InBhZGRpbmc6MTBweCAxMnB4OyBmb250LWZhbWlseTpcJ0pldEJyYWlucyBNb25vXCcsbW9ub3NwYWNlOyI+CiAgICAgICAg"
    "ICAgICAgICAgIDxkaXYgc3R5bGU9ImRpc3BsYXk6ZmxleDsganVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47IG1hcmdpbi1i"
    "b3R0b206N3B4OyI+CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC40NSk7"
    "IGZvbnQtc2l6ZToxMHB4OyI+0J/QkNCh0KLQrDwvc3Bhbj4KICAgICAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6"
    "e3N0X2NvbG9yfTsgZm9udC1zaXplOjExcHg7IGZvbnQtd2VpZ2h0OjcwMDsiPnttc3RhdHVzfTwvc3Bhbj4KICAgICAgICAgICAg"
    "ICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImRpc3BsYXk6ZmxleDsganVzdGlmeS1jb250ZW50OnNw"
    "YWNlLWJldHdlZW47IG1hcmdpbi1ib3R0b206N3B4OyI+CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJn"
    "YmEoMjU1LDI1NSwyNTUsMC40NSk7IGZvbnQtc2l6ZToxMHB4OyI+0KDQldCX0JjQndCa0JA8L3NwYW4+CiAgICAgICAgICAgICAg"
    "ICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOntwZWFrX2NvbG9yfTsgZm9udC1zaXplOjExcHg7IGZvbnQtd2VpZ2h0OjcwMDsiPntw"
    "ZWFrX3R4dH08L3NwYW4+CiAgICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgICA8ZGl2IHN0eWxlPSJkaXNw"
    "bGF5OmZsZXg7IGp1c3RpZnktY29udGVudDpzcGFjZS1iZXR3ZWVuOyBtYXJnaW4tYm90dG9tOjdweDsiPgogICAgICAgICAgICAg"
    "ICAgICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpOyBmb250LXNpemU6MTBweDsiPtCd0JDQotCv"
    "0JbQldCd0JjQlTwvc3Bhbj4KICAgICAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6cmdiYSgwLDIwNCwyNTUsMC45"
    "KTsgZm9udC1zaXplOjExcHg7Ij57cmF0aW9fdHh0fSDCtyB7ZGlzdF90eHR9PC9zcGFuPgogICAgICAgICAgICAgICAgICA8L2Rp"
    "dj4KICAgICAgICAgICAgICAgICAgPGRpdiBzdHlsZT0iZGlzcGxheTpmbGV4OyBqdXN0aWZ5LWNvbnRlbnQ6c3BhY2UtYmV0d2Vl"
    "bjsgbWFyZ2luLWJvdHRvbToxMHB4OyI+CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1"
    "NSwyNTUsMC40NSk7IGZvbnQtc2l6ZToxMHB4OyI+0JLQntCb0J3QkCAxIC8g0JHQkNCg0J7QkiDQntCi0JrQoNCr0KI8L3NwYW4+"
    "CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC43KTsgZm9udC1zaXplOjEx"
    "cHg7Ij57d2F2ZTF9IMK3IHtib3Blbn08L3NwYW4+CiAgICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgICA8"
    "ZGl2IHN0eWxlPSJib3JkZXItdG9wOjFweCBzb2xpZCByZ2JhKDI1NSwyNTUsMjU1LDAuMDgpOyBwYWRkaW5nLXRvcDo4cHg7CiAg"
    "ICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC4zNSk7IGZvbnQtc2l6ZTo5cHg7IGxp"
    "bmUtaGVpZ2h0OjEuNzsiPgogICAgICAgICAgICAgICAgICAgINCy0LfQs9C70Y/QtNC+0LI6IHttc3QuZ2V0KCJydW5zIiwwKX0g"
    "wrcKICAgICAgICAgICAgICAgICAgICDQv9GA0L7RgdC90YPQu9GB0Y86IHttc3QuZ2V0KCJhd2FrZSIsMCl9IMK3CiAgICAgICAg"
    "ICAgICAgICAgICAg0YHQv9Cw0Ls6IHttc3QuZ2V0KCJzbGVlcGluZyIsMCl9IMK3CiAgICAgICAgICAgICAgICAgICAg0L/QuNC6"
    "0L7Qsjoge21zdC5nZXQoInRlbnNpb25fcGVha3MiLDApfQogICAgICAgICAgICAgICAgICAgIDxicj57bW1rLmdldCgic3ltYm9s"
    "IiwiIil9IHttbWsuZ2V0KCJ0aW1lZnJhbWUiLCIiKX0gwrcge21tay5nZXQoImJhcl90aW1lIiwiIil9CiAgICAgICAgICAgICAg"
    "ICAgIDwvZGl2PgogICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICAnJycpCiAgICAgICAgICAgIHJldHVybgoK"
    "ICAgICAgICBpZiBzdGF0ZVsiYWN0aXZlX2FnZW50Il0gPT0gIkEwMyI6CiAgICAgICAgICAgIHBzaWcgPSBzdGF0ZS5nZXQoInBh"
    "bmljX3NpZ25hbCIsIHt9KQogICAgICAgICAgICBwc3QgID0gc3RhdGUuZ2V0KCJwYW5pY19zdGF0cyIsIHt9KQogICAgICAgICAg"
    "ICBwbWsgID0gc3RhdGUuZ2V0KCJwYW5pY19tYXJrZXQiLCB7fSkKICAgICAgICAgICAgaWYgbm90IHBzaWc6CiAgICAgICAgICAg"
    "ICAgICB3aXRoIHN0YXRzX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAgICAgICAgICAgIHVpLmh0bWwoJzxkaXYgc3R5bGU9ImNv"
    "bG9yOnJnYmEoMjU1LDI1NSwyNTUsMC4zKTsgZm9udC1zaXplOjExcHg7ICcKICAgICAgICAgICAgICAgICAgICAgICAgICAgICdw"
    "YWRkaW5nOjEwcHg7IHRleHQtYWxpZ246Y2VudGVyOyI+0J/QsNC90LjQutGR0YAg0LXRidGRINC90LUg0LzQtdGA0LjQuyDRgtC+"
    "0LvQv9GDIOKAlCAnCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAn0L3QsNC20LzQuCDQoNCr0J3QntCaICjQvdGD0LbQtdC9"
    "INGB0LjQs9C90LDQuyDQmNGB0LrRgNGLKTwvZGl2PicpCiAgICAgICAgICAgICAgICByZXR1cm4KICAgICAgICAgICAgcGhhc2Ug"
    "PSBwc2lnLmdldCgicGFuaWNfcGhhc2UiLCAi4oCUIikKICAgICAgICAgICAgcGhfY29sb3IgPSB7IlBBTklDIjogIiNmZjUwNTAi"
    "LCAiR1JFRUQiOiAiI2ZmYjQwMCIsCiAgICAgICAgICAgICAgICAgICAgICAgICJURU5TSU9OIjogIiNmZmI0MDAiLCAiREVDRVBU"
    "SU9OIjogIiNjYzg4ZmYiLAogICAgICAgICAgICAgICAgICAgICAgICAiRElTQkVMSUVGIjogInJnYmEoMCwyMDQsMjU1LDAuOSki"
    "LAogICAgICAgICAgICAgICAgICAgICAgICAiQVNMRUVQIjogInJnYmEoMjU1LDI1NSwyNTUsMC40KSJ9LmdldChwaGFzZSwgInJn"
    "YmEoMjU1LDI1NSwyNTUsMC43KSIpCiAgICAgICAgICAgIHNlbnRpbWVudCA9IHBzaWcuZ2V0KCJjcm93ZF9zZW50aW1lbnQiLCAi"
    "4oCUIikgb3IgIuKAlCIKICAgICAgICAgICAgYWN0aW9uID0gcHNpZy5nZXQoImFjdGlvbl9mb3JfdHJhZGVycyIsICLigJQiKQog"
    "ICAgICAgICAgICBhY3RfY29sb3IgPSB7IkdSRUVOX0xJR0hUX0lGX0dBTlMiOiAiIzAwZmY4OCIsCiAgICAgICAgICAgICAgICAg"
    "ICAgICAgICAiSElHSF9TS0VQVElDSVNNIjogIiNmZmI0MDAiLAogICAgICAgICAgICAgICAgICAgICAgICAgIk5FVVRSQUwiOiAi"
    "cmdiYSgyNTUsMjU1LDI1NSwwLjQpIn0uZ2V0KGFjdGlvbiwgInJnYmEoMjU1LDI1NSwyNTUsMC40KSIpCiAgICAgICAgICAgIHdp"
    "dGggc3RhdHNfcmVmWyJlbGVtZW50Il06CiAgICAgICAgICAgICAgICB1aS5odG1sKGYnJycKICAgICAgICAgICAgICAgIDxkaXYg"
    "c3R5bGU9InBhZGRpbmc6MTBweCAxMnB4OyBmb250LWZhbWlseTpcJ0pldEJyYWlucyBNb25vXCcsbW9ub3NwYWNlOyI+CiAgICAg"
    "ICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImRpc3BsYXk6ZmxleDsganVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47IG1hcmdp"
    "bi1ib3R0b206N3B4OyI+CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC40"
    "NSk7IGZvbnQtc2l6ZToxMHB4OyI+0KLQntCb0J/QkDwvc3Bhbj4KICAgICAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29s"
    "b3I6e3BoX2NvbG9yfTsgZm9udC1zaXplOjExcHg7IGZvbnQtd2VpZ2h0OjcwMDsiPntwaGFzZX08L3NwYW4+CiAgICAgICAgICAg"
    "ICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgICA8ZGl2IHN0eWxlPSJtYXJnaW4tYm90dG9tOjdweDsiPgogICAgICAgICAg"
    "ICAgICAgICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpOyBmb250LXNpemU6MTBweDsiPtCd0JDQ"
    "mtCQ0Js8L3NwYW4+CiAgICAgICAgICAgICAgICAgICAgPGRpdiBzdHlsZT0iY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjcpOyBm"
    "b250LXNpemU6MTBweDsgZm9udC1zdHlsZTppdGFsaWM7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgbWFyZ2luLXRv"
    "cDozcHg7IGxpbmUtaGVpZ2h0OjEuNDsiPsKre3NlbnRpbWVudH3CuzwvZGl2PgogICAgICAgICAgICAgICAgICA8L2Rpdj4KICAg"
    "ICAgICAgICAgICAgICAgPGRpdiBzdHlsZT0iZGlzcGxheTpmbGV4OyBqdXN0aWZ5LWNvbnRlbnQ6c3BhY2UtYmV0d2VlbjsgbWFy"
    "Z2luLWJvdHRvbToxMHB4OyI+CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUs"
    "MC40NSk7IGZvbnQtc2l6ZToxMHB4OyI+0KHQktCV0KLQntCk0J7QoDwvc3Bhbj4KICAgICAgICAgICAgICAgICAgICA8c3BhbiBz"
    "dHlsZT0iY29sb3I6e2FjdF9jb2xvcn07IGZvbnQtc2l6ZToxMXB4OyBmb250LXdlaWdodDo3MDA7Ij57YWN0aW9ufTwvc3Bhbj4K"
    "ICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImJvcmRlci10b3A6MXB4IHNvbGlk"
    "IHJnYmEoMjU1LDI1NSwyNTUsMC4wOCk7IHBhZGRpbmctdG9wOjhweDsKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgY29s"
    "b3I6cmdiYSgyNTUsMjU1LDI1NSwwLjM1KTsgZm9udC1zaXplOjlweDsgbGluZS1oZWlnaHQ6MS43OyI+CiAgICAgICAgICAgICAg"
    "ICAgICAg0LfQsNC80LXRgNC+0LI6IHtwc3QuZ2V0KCJydW5zIiwwKX0gwrcKICAgICAgICAgICAgICAgICAgICDQv9Cw0L3QuNC6"
    "OiB7cHN0LmdldCgicGFuaWMiLDApfSDCtwogICAgICAgICAgICAgICAgICAgINC20LDQtNC90L7RgdGC0Lg6IHtwc3QuZ2V0KCJn"
    "cmVlZCIsMCl9IMK3CiAgICAgICAgICAgICAgICAgICAg0YHQutGD0LrQuDoge3BzdC5nZXQoImFzbGVlcCIsMCl9CiAgICAgICAg"
    "ICAgICAgICAgICAgPGJyPntwbWsuZ2V0KCJzeW1ib2wiLCIiKX0ge3Btay5nZXQoInRpbWVmcmFtZSIsIiIpfSDCtyB7cG1rLmdl"
    "dCgiYmFyX3RpbWUiLCIiKX0KICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICA8L2Rpdj4KICAgICAgICAg"
    "ICAgICAgICcnJykKICAgICAgICAgICAgcmV0dXJuCgogICAgICAgIGlmIHN0YXRlWyJhY3RpdmVfYWdlbnQiXSA9PSAiQTA0IjoK"
    "ICAgICAgICAgICAgaHNpZyA9IHN0YXRlLmdldCgiaGFuc19zaWduYWwiLCB7fSkKICAgICAgICAgICAgaHN0ICA9IHN0YXRlLmdl"
    "dCgiaGFuc19zdGF0cyIsIHt9KQogICAgICAgICAgICBobWsgID0gc3RhdGUuZ2V0KCJoYW5zX21hcmtldCIsIHt9KQogICAgICAg"
    "ICAgICBpZiBub3QgaHNpZzoKICAgICAgICAgICAgICAgIHdpdGggc3RhdHNfcmVmWyJlbGVtZW50Il06CiAgICAgICAgICAgICAg"
    "ICAgICAgdWkuaHRtbCgnPGRpdiBzdHlsZT0iY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjMpOyBmb250LXNpemU6MTFweDsgJwog"
    "ICAgICAgICAgICAgICAgICAgICAgICAgICAgJ3BhZGRpbmc6MTBweDsgdGV4dC1hbGlnbjpjZW50ZXI7Ij7Qk9Cw0L3RgSDQtdGJ"
    "0ZEg0L3QtSDQstGL0YXQvtC00LjQuyDQvdCwINGB0LvQtdC0IOKAlCAnCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAn0L3Q"
    "sNC20LzQuCDQoNCr0J3QntCaICjQvdGD0LbQtdC9INGB0LjQs9C90LDQuyDQmNGB0LrRgNGLKTwvZGl2PicpCiAgICAgICAgICAg"
    "ICAgICByZXR1cm4KICAgICAgICAgICAgdmFsaWQgPSBoc2lnLmdldCgiZnJhY3RhbF92YWxpZCIpCiAgICAgICAgICAgIHZfdHh0"
    "ID0gIvCfjq8g0JLQndCVINCa0KDQkNCh0J3QntCZIiBpZiB2YWxpZCBlbHNlICLQv9GD0YHRgtC+IgogICAgICAgICAgICB2X2Nv"
    "bG9yID0gIiMwMGZmODgiIGlmIHZhbGlkIGVsc2UgInJnYmEoMjU1LDI1NSwyNTUsMC40KSIKICAgICAgICAgICAgc2lkZSA9IGhz"
    "aWcuZ2V0KCJmcmFjdGFsX3NpZGUiKSBvciAi4oCUIgogICAgICAgICAgICBmcHJpY2UgPSBoc2lnLmdldCgiZnJhY3RhbF9wcmlj"
    "ZSIpCiAgICAgICAgICAgIGZwcmljZV90eHQgPSBmIntmcHJpY2V9IiBpZiBmcHJpY2UgaXMgbm90IE5vbmUgZWxzZSAi4oCUIgog"
    "ICAgICAgICAgICBhYnNyID0gaHNpZy5nZXQoImFic29ycHRpb25fcmF0aW8iKQogICAgICAgICAgICBhYnNyX3R4dCA9IGYie2Fi"
    "c3J9IiBpZiBhYnNyIGlzIG5vdCBOb25lIGVsc2UgIuKAlCIKICAgICAgICAgICAgYWJzX2NvbG9yID0gIiNmZjUwNTAiIGlmIChh"
    "YnNyIGlzIG5vdCBOb25lIGFuZCBhYnNyID49IDAuNykgZWxzZSAicmdiYSgyNTUsMjU1LDI1NSwwLjcpIgogICAgICAgICAgICB3"
    "aXRoIHN0YXRzX3JlZlsiZWxlbWVudCJdOgogICAgICAgICAgICAgICAgdWkuaHRtbChmJycnCiAgICAgICAgICAgICAgICA8ZGl2"
    "IHN0eWxlPSJwYWRkaW5nOjEwcHggMTJweDsgZm9udC1mYW1pbHk6XCdKZXRCcmFpbnMgTW9ub1wnLG1vbm9zcGFjZTsiPgogICAg"
    "ICAgICAgICAgICAgICA8ZGl2IHN0eWxlPSJkaXNwbGF5OmZsZXg7IGp1c3RpZnktY29udGVudDpzcGFjZS1iZXR3ZWVuOyBtYXJn"
    "aW4tYm90dG9tOjdweDsiPgogICAgICAgICAgICAgICAgICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAu"
    "NDUpOyBmb250LXNpemU6MTBweDsiPtCk0KDQkNCa0KLQkNCbPC9zcGFuPgogICAgICAgICAgICAgICAgICAgIDxzcGFuIHN0eWxl"
    "PSJjb2xvcjp7dl9jb2xvcn07IGZvbnQtc2l6ZToxMXB4OyBmb250LXdlaWdodDo3MDA7Ij57dl90eHR9PC9zcGFuPgogICAgICAg"
    "ICAgICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgICAgICAgPGRpdiBzdHlsZT0iZGlzcGxheTpmbGV4OyBqdXN0aWZ5LWNvbnRl"
    "bnQ6c3BhY2UtYmV0d2VlbjsgbWFyZ2luLWJvdHRvbTo3cHg7Ij4KICAgICAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29s"
    "b3I6cmdiYSgyNTUsMjU1LDI1NSwwLjQ1KTsgZm9udC1zaXplOjEwcHg7Ij7QodCi0J7QoNCe0J3QkDwvc3Bhbj4KICAgICAgICAg"
    "ICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjcpOyBmb250LXNpemU6MTFweDsiPntzaWRl"
    "fTwvc3Bhbj4KICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImRpc3BsYXk6Zmxl"
    "eDsganVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47IG1hcmdpbi1ib3R0b206N3B4OyI+CiAgICAgICAgICAgICAgICAgICAg"
    "PHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC40NSk7IGZvbnQtc2l6ZToxMHB4OyI+0KbQldCd0JAgKNCe0KDQ"
    "mNCV0J3QotCY0KApPC9zcGFuPgogICAgICAgICAgICAgICAgICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDAsMjA0LDI1NSww"
    "LjkpOyBmb250LXNpemU6MTFweDsiPntmcHJpY2VfdHh0fTwvc3Bhbj4KICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAg"
    "ICAgICAgICAgIDxkaXYgc3R5bGU9ImRpc3BsYXk6ZmxleDsganVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47IG1hcmdpbi1i"
    "b3R0b206MTBweDsiPgogICAgICAgICAgICAgICAgICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNDUp"
    "OyBmb250LXNpemU6MTBweDsiPtCf0J7Qk9Cb0J7QqdCV0J3QmNCVPC9zcGFuPgogICAgICAgICAgICAgICAgICAgIDxzcGFuIHN0"
    "eWxlPSJjb2xvcjp7YWJzX2NvbG9yfTsgZm9udC1zaXplOjExcHg7Ij57YWJzcl90eHR9PC9zcGFuPgogICAgICAgICAgICAgICAg"
    "ICA8L2Rpdj4KICAgICAgICAgICAgICAgICAgPGRpdiBzdHlsZT0iYm9yZGVyLXRvcDoxcHggc29saWQgcmdiYSgyNTUsMjU1LDI1"
    "NSwwLjA4KTsgcGFkZGluZy10b3A6OHB4OwogICAgICAgICAgICAgICAgICAgICAgICAgICAgICBjb2xvcjpyZ2JhKDI1NSwyNTUs"
    "MjU1LDAuMzUpOyBmb250LXNpemU6OXB4OyBsaW5lLWhlaWdodDoxLjc7Ij4KICAgICAgICAgICAgICAgICAgICDQstGL0YXQvtC0"
    "0L7Qsjoge2hzdC5nZXQoInJ1bnMiLDApfSDCtwogICAgICAgICAgICAgICAgICAgINC00L7QsdGL0YfQsDoge2hzdC5nZXQoInZh"
    "bGlkIiwwKX0gwrcKICAgICAgICAgICAgICAgICAgICDQvNGR0YDRgtCy0YvRhToge2hzdC5nZXQoImRlYWQiLDApfSDCtwogICAg"
    "ICAgICAgICAgICAgICAgINC/0YPRgdGC0L46IHtoc3QuZ2V0KCJub25lIiwwKX0KICAgICAgICAgICAgICAgICAgICA8YnI+e2ht"
    "ay5nZXQoInN5bWJvbCIsIiIpfSB7aG1rLmdldCgidGltZWZyYW1lIiwiIil9IMK3IHtobWsuZ2V0KCJiYXJfdGltZSIsIiIpfQog"
    "ICAgICAgICAgICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgJycnKQogICAgICAg"
    "ICAgICByZXR1cm4KCiAgICAgICAgaWYgc3RhdGVbImFjdGl2ZV9hZ2VudCJdID09ICJBMDUiOgogICAgICAgICAgICBhc2lnID0g"
    "c3RhdGUuZ2V0KCJhcmtoaXZfc2lnbmFsIiwge30pCiAgICAgICAgICAgIGFzdCAgPSBzdGF0ZS5nZXQoImFya2hpdl9zdGF0cyIs"
    "IHt9KQogICAgICAgICAgICBhZGcgID0gc3RhdGUuZ2V0KCJhcmtoaXZfZGlnZXN0Iiwge30pCiAgICAgICAgICAgIGlmIG5vdCBh"
    "c2lnIGFuZCBub3QgYWRnOgogICAgICAgICAgICAgICAgd2l0aCBzdGF0c19yZWZbImVsZW1lbnQiXToKICAgICAgICAgICAgICAg"
    "ICAgICB1aS5odG1sKCc8ZGl2IHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuMyk7IGZvbnQtc2l6ZToxMXB4OyAnCiAg"
    "ICAgICAgICAgICAgICAgICAgICAgICAgICAncGFkZGluZzoxMHB4OyB0ZXh0LWFsaWduOmNlbnRlcjsiPtCQ0YDRhdC40LLQsNGA"
    "0LjRg9GBINC10YnRkSDQvdC1INC70LjRgdGC0LDQuyDQkNGC0LvQsNGBIOKAlCAnCiAgICAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAn0L3QsNC20LzQuCDQoNCr0J3QntCaICjQvdGD0LbQtdC9INGB0LjQs9C90LDQuyDQmNGB0LrRgNGLKTwvZGl2PicpCiAgICAg"
    "ICAgICAgICAgICByZXR1cm4KICAgICAgICAgICAgc2FtcGxlID0gYXNpZy5nZXQoInNhbXBsZV9zaXplIiwgYWRnLmdldCgic2Ft"
    "cGxlX3NpemUiLCAwKSkKICAgICAgICAgICAgY2xvc2VkID0gYWRnLmdldCgiY2xvc2VkX3RyYWRlcyIsICLigJQiKQogICAgICAg"
    "ICAgICBzdWNjZXNzID0gYXNpZy5nZXQoInN1Y2Nlc3NfcmF0ZSIsIGFkZy5nZXQoInN1Y2Nlc3NfcmF0ZSIpKQogICAgICAgICAg"
    "ICBzdWNjZXNzX3R4dCA9IGYie3JvdW5kKHN1Y2Nlc3MqMTAwKX0lIiBpZiBpc2luc3RhbmNlKHN1Y2Nlc3MsIChpbnQsIGZsb2F0"
    "KSkgZWxzZSAi4oCUIgogICAgICAgICAgICBjb25mID0gYXNpZy5nZXQoImFya2hpdl9jb25maWRlbmNlIiwgYWRnLmdldCgiYXJr"
    "aGl2X2NvbmZpZGVuY2UiLCAi4oCUIikpCiAgICAgICAgICAgIGNvbmZfY29sb3IgPSB7IkhJR0giOiAiIzAwZmY4OCIsICJNRURJ"
    "VU0iOiAiI2ZmYjQwMCIsCiAgICAgICAgICAgICAgICAgICAgICAgICAgIkxPVyI6ICJyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpIn0u"
    "Z2V0KGNvbmYsICJyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpIikKICAgICAgICAgICAgcmVhc29uID0gYXNpZy5nZXQoInRvcF9mYWls"
    "dXJlX3JlYXNvbiIsIGFkZy5nZXQoInRvcF9mYWlsdXJlX3JlYXNvbiIsICLigJQiKSkgb3IgIuKAlCIKICAgICAgICAgICAgZW1w"
    "dHkgPSAoc2FtcGxlID09IDApCiAgICAgICAgICAgIHNhbXBsZV9jb2xvciA9ICJyZ2JhKDI1NSwyNTUsMjU1LDAuNCkiIGlmIGVt"
    "cHR5IGVsc2UgInJnYmEoMCwyMDQsMjU1LDAuOSkiCiAgICAgICAgICAgIHNhbXBsZV90eHQgPSAi0L/Rg9GB0YLQviDigJQg0L/Q"
    "tdGA0LLRi9C5INGB0LvRg9GH0LDQuSIgaWYgZW1wdHkgZWxzZSBmIntzYW1wbGV9ICjQt9Cw0LrRgNGL0YLQviB7Y2xvc2VkfSki"
    "CiAgICAgICAgICAgIHdpdGggc3RhdHNfcmVmWyJlbGVtZW50Il06CiAgICAgICAgICAgICAgICB1aS5odG1sKGYnJycKICAgICAg"
    "ICAgICAgICAgIDxkaXYgc3R5bGU9InBhZGRpbmc6MTBweCAxMnB4OyBmb250LWZhbWlseTpcJ0pldEJyYWlucyBNb25vXCcsbW9u"
    "b3NwYWNlOyI+CiAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImRpc3BsYXk6ZmxleDsganVzdGlmeS1jb250ZW50OnNwYWNl"
    "LWJldHdlZW47IG1hcmdpbi1ib3R0b206N3B4OyI+CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEo"
    "MjU1LDI1NSwyNTUsMC40NSk7IGZvbnQtc2l6ZToxMHB4OyI+0KHQmtCb0JDQlDwvc3Bhbj4KICAgICAgICAgICAgICAgICAgICA8"
    "c3BhbiBzdHlsZT0iY29sb3I6e3NhbXBsZV9jb2xvcn07IGZvbnQtc2l6ZToxMXB4OyBmb250LXdlaWdodDo3MDA7Ij57c2FtcGxl"
    "X3R4dH08L3NwYW4+CiAgICAgICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgICA8ZGl2IHN0eWxlPSJkaXNwbGF5"
    "OmZsZXg7IGp1c3RpZnktY29udGVudDpzcGFjZS1iZXR3ZWVuOyBtYXJnaW4tYm90dG9tOjdweDsiPgogICAgICAgICAgICAgICAg"
    "ICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpOyBmb250LXNpemU6MTBweDsiPtCj0JTQkNCn0JA8"
    "L3NwYW4+CiAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC43KTsgZm9udC1z"
    "aXplOjExcHg7Ij57c3VjY2Vzc190eHR9PC9zcGFuPgogICAgICAgICAgICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgICAgICAg"
    "PGRpdiBzdHlsZT0iZGlzcGxheTpmbGV4OyBqdXN0aWZ5LWNvbnRlbnQ6c3BhY2UtYmV0d2VlbjsgbWFyZ2luLWJvdHRvbTo3cHg7"
    "Ij4KICAgICAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjQ1KTsgZm9udC1zaXpl"
    "OjEwcHg7Ij7Qo9CS0JXQoNCV0J3QndCe0KHQotCsPC9zcGFuPgogICAgICAgICAgICAgICAgICAgIDxzcGFuIHN0eWxlPSJjb2xv"
    "cjp7Y29uZl9jb2xvcn07IGZvbnQtc2l6ZToxMXB4OyBmb250LXdlaWdodDo3MDA7Ij57Y29uZn08L3NwYW4+CiAgICAgICAgICAg"
    "ICAgICAgIDwvZGl2PgogICAgICAgICAgICAgICAgICA8ZGl2IHN0eWxlPSJtYXJnaW4tYm90dG9tOjEwcHg7Ij4KICAgICAgICAg"
    "ICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjQ1KTsgZm9udC1zaXplOjEwcHg7Ij7Qp9CQ"
    "0KHQotCQ0K8g0J/QoNCY0KfQmNCd0JAg0J/QntCi0JXQoNCsPC9zcGFuPgogICAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9"
    "ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC43KTsgZm9udC1zaXplOjEwcHg7IGZvbnQtc3R5bGU6aXRhbGljOwogICAgICAgICAg"
    "ICAgICAgICAgICAgICAgICAgICAgIG1hcmdpbi10b3A6M3B4OyBsaW5lLWhlaWdodDoxLjQ7Ij7Cq3tyZWFzb259wrs8L2Rpdj4K"
    "ICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImJvcmRlci10b3A6MXB4IHNvbGlk"
    "IHJnYmEoMjU1LDI1NSwyNTUsMC4wOCk7IHBhZGRpbmctdG9wOjhweDsKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgY29s"
    "b3I6cmdiYSgyNTUsMjU1LDI1NSwwLjM1KTsgZm9udC1zaXplOjlweDsgbGluZS1oZWlnaHQ6MS43OyI+CiAgICAgICAgICAgICAg"
    "ICAgICAg0LLQt9Cz0LvRj9C00L7Qsjoge2FzdC5nZXQoInJ1bnMiLDApfSDCtwogICAgICAgICAgICAgICAgICAgIEhJR0g6IHth"
    "c3QuZ2V0KCJoaWdoIiwwKX0gwrcKICAgICAgICAgICAgICAgICAgICBNRURJVU06IHthc3QuZ2V0KCJtZWRpdW0iLDApfSDCtwog"
    "ICAgICAgICAgICAgICAgICAgIExPVzoge2FzdC5nZXQoImxvdyIsMCl9IMK3CiAgICAgICAgICAgICAgICAgICAg0L/Rg9GB0YLQ"
    "vjoge2FzdC5nZXQoImVtcHR5IiwwKX0KICAgICAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgICA8L2Rpdj4KICAg"
    "ICAgICAgICAgICAgICcnJykKICAgICAgICAgICAgcmV0dXJuCgogICAgICAgIGlmIHN0YXRlWyJhY3RpdmVfYWdlbnQiXSAhPSAi"
    "QTAxIjoKICAgICAgICAgICAgd2l0aCBzdGF0c19yZWZbImVsZW1lbnQiXToKICAgICAgICAgICAgICAgIHVpLmh0bWwoJzxkaXYg"
    "c3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC4zKTsgZm9udC1zaXplOjExcHg7ICcKICAgICAgICAgICAgICAgICAgICAg"
    "ICAgJ3BhZGRpbmc6MTBweDsgdGV4dC1hbGlnbjpjZW50ZXI7Ij7Qn9GA0LjQsdC+0YDRiyDQv9C+0Y/QstGP0YLRgdGPINC/0YDQ"
    "uCDQv9C+0LTQutC70Y7Rh9C10L3QuNC4INCw0LPQtdC90YLQsDwvZGl2PicpCiAgICAgICAgICAgIHJldHVybgoKICAgICAgICB0"
    "MSA9IHNpZy5nZXQoInQxX3N0YXR1cyIsICLigJQiKQogICAgICAgIHQxX2NvbG9yID0geyJERVRFQ1RFRCI6ICIjZmZiNDAwIiwg"
    "IkNPTkZJUk1FRCI6ICIjMDBmZjg4IiwKICAgICAgICAgICAgICAgICAgICAiTk9UX0ZPVU5EIjogInJnYmEoMjU1LDI1NSwyNTUs"
    "MC40KSJ9LmdldCh0MSwgInJnYmEoMjU1LDI1NSwyNTUsMC40KSIpCiAgICAgICAgemVybyA9IHNpZy5nZXQoInplcm9fcG9pbnRf"
    "cHJpY2UiKQogICAgICAgIHplcm9fdHh0ID0gZiJ7emVyb30iIGlmIHplcm8gZWxzZSAi4oCUIgogICAgICAgIGJlbGwgPSAi8J+U"
    "lCDQl9CS0J7QndCY0KIiIGlmIHNpZy5nZXQoImV4aXRfYmVsbCIpIGVsc2UgIuKAlCIKICAgICAgICBiZWxsX2NvbG9yID0gIiNm"
    "ZjUwNTAiIGlmIHNpZy5nZXQoImV4aXRfYmVsbCIpIGVsc2UgInJnYmEoMjU1LDI1NSwyNTUsMC40KSIKCiAgICAgICAgd2l0aCBz"
    "dGF0c19yZWZbImVsZW1lbnQiXToKICAgICAgICAgICAgdWkuaHRtbChmJycnCiAgICAgICAgICAgIDxkaXYgc3R5bGU9InBhZGRp"
    "bmc6MTBweCAxMnB4OyBmb250LWZhbWlseTonSmV0QnJhaW5zIE1vbm8nLG1vbm9zcGFjZTsiPgogICAgICAgICAgICAgIDxkaXYg"
    "c3R5bGU9ImRpc3BsYXk6ZmxleDsganVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47IG1hcmdpbi1ib3R0b206N3B4OyI+CiAg"
    "ICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjQ1KTsgZm9udC1zaXplOjEwcHg7Ij7Q"
    "odCi0JDQotCj0KE8L3NwYW4+CiAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6e3QxX2NvbG9yfTsgZm9udC1zaXpl"
    "OjExcHg7IGZvbnQtd2VpZ2h0OjcwMDsiPnt0MX08L3NwYW4+CiAgICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgICAgICAgPGRp"
    "diBzdHlsZT0iZGlzcGxheTpmbGV4OyBqdXN0aWZ5LWNvbnRlbnQ6c3BhY2UtYmV0d2VlbjsgbWFyZ2luLWJvdHRvbTo3cHg7Ij4K"
    "ICAgICAgICAgICAgICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpOyBmb250LXNpemU6MTBweDsi"
    "PtCi0J7Qp9Ca0JAg0J3QntCb0Kw8L3NwYW4+CiAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6cmdiYSgwLDIwNCwy"
    "NTUsMC45KTsgZm9udC1zaXplOjExcHg7Ij57emVyb190eHR9PC9zcGFuPgogICAgICAgICAgICAgIDwvZGl2PgogICAgICAgICAg"
    "ICAgIDxkaXYgc3R5bGU9ImRpc3BsYXk6ZmxleDsganVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47IG1hcmdpbi1ib3R0b206"
    "MTBweDsiPgogICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC40NSk7IGZvbnQtc2l6"
    "ZToxMHB4OyI+0JrQntCb0J7QmtCe0Js8L3NwYW4+CiAgICAgICAgICAgICAgICA8c3BhbiBzdHlsZT0iY29sb3I6e2JlbGxfY29s"
    "b3J9OyBmb250LXNpemU6MTFweDsiPntiZWxsfTwvc3Bhbj4KICAgICAgICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgICA8ZGl2"
    "IHN0eWxlPSJib3JkZXItdG9wOjFweCBzb2xpZCByZ2JhKDI1NSwyNTUsMjU1LDAuMDgpOyBwYWRkaW5nLXRvcDo4cHg7CiAgICAg"
    "ICAgICAgICAgICAgICAgICAgICAgY29sb3I6cmdiYSgyNTUsMjU1LDI1NSwwLjM1KTsgZm9udC1zaXplOjlweDsgbGluZS1oZWln"
    "aHQ6MS43OyI+CiAgICAgICAgICAgICAgICDQv9GA0L7Qs9C+0L3QvtCyOiB7c3QuZ2V0KCJydW5zIiwwKX0gwrcKICAgICAgICAg"
    "ICAgICAgINC90LDRiNC70LA6IHtzdC5nZXQoImRldGVjdGVkIiwwKX0gwrcKICAgICAgICAgICAgICAgINC/0L7QtNGC0LLQtdGA"
    "0LTQuNC70L7RgdGMOiB7c3QuZ2V0KCJjb25maXJtZWQiLDApfSDCtwogICAgICAgICAgICAgICAg0LDQvdC90YPQu9C40YDQvtCy"
    "0LDQvdC+OiB7c3QuZ2V0KCJhbm51bGxlZCIsMCl9CiAgICAgICAgICAgICAgICA8YnI+e21rLmdldCgic3ltYm9sIiwiIil9IHtt"
    "ay5nZXQoInRpbWVmcmFtZSIsIiIpfSDCtyB7bWsuZ2V0KCJiYXJfdGltZSIsIiIpfQogICAgICAgICAgICAgIDwvZGl2PgogICAg"
    "ICAgICAgICA8L2Rpdj4KICAgICAgICAgICAgJycnKQoKICAgICMg4pSA4pSAINCi0KPQnNCR0JvQldCgINCi0JXQodCi0JXQoC/Q"
    "oNCV0JDQmyArINCf0JXQoNCV0JHQntCgINCY0KHQotCe0KDQmNCYICsg0KHQotCe0J8g4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA"
    "4pSA4pSA4pSA4pSA4pSACgogICAgZGVmIHNldF9tb2RlKG1vZGU6IHN0cik6CiAgICAgICAgc3RhdGVbIm1vZGUiXSA9IG1vZGUK"
    "ICAgICAgICB0cnk6CiAgICAgICAgICAgIGZyb20gZmVlZF9zb3VyY2UgaW1wb3J0IHNldF9mZWVkX21vZGUKICAgICAgICAgICAg"
    "X3N5bSA9IE5vbmUKICAgICAgICAgICAgX2Fzc2V0cyA9IHN0YXRlLmdldCgibG9hZGVkX2Fzc2V0cyIsIFtdKQogICAgICAgICAg"
    "ICBfYWkgPSBzdGF0ZS5nZXQoImFjdGl2ZV9hc3NldCIpCiAgICAgICAgICAgIGlmIF9hc3NldHMgYW5kIF9haSBpcyBub3QgTm9u"
    "ZSBhbmQgMCA8PSBfYWkgPCBsZW4oX2Fzc2V0cyk6CiAgICAgICAgICAgICAgICBfc3ltID0gX2Fzc2V0c1tfYWldLmdldCgic3lt"
    "Ym9sIikKICAgICAgICAgICAgc2V0X2ZlZWRfbW9kZShtb2RlLCBfc3ltKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgX2U6"
    "CiAgICAgICAgICAgIHByaW50KGYiW1RPUkddIGZlZWRfc291cmNlINC90LUg0L/QvtC00LrQu9GO0YfRkdC9OiB7X2V9IikKICAg"
    "ICAgICBpc190ZXN0ZXIgPSAobW9kZSA9PSAidGVzdGVyIikKICAgICAgICBmb3Iga2V5IGluICgiYmFyc19pbnB1dCIsICJzdG9w"
    "X2J0biIsICJiYXJzX2xhYmVsIik6CiAgICAgICAgICAgIGVsID0gdG9vbGJhcl9yZWZzLmdldChrZXkpCiAgICAgICAgICAgIGlm"
    "IGVsOgogICAgICAgICAgICAgICAgZWwuc3R5bGUoZiJkaXNwbGF5OiB7J2ZsZXgnIGlmIGlzX3Rlc3RlciBlbHNlICdub25lJ30i"
    "KQogICAgICAgIGZvciBrZXksIG0gaW4gKCgibW9kZV9yZWFsIiwgInJlYWwiKSwgKCJtb2RlX3Rlc3RlciIsICJ0ZXN0ZXIiKSk6"
    "CiAgICAgICAgICAgIGVsID0gdG9vbGJhcl9yZWZzLmdldChrZXkpCiAgICAgICAgICAgIGlmIGVsOgogICAgICAgICAgICAgICAg"
    "YWN0aXZlID0gKG0gPT0gbW9kZSkKICAgICAgICAgICAgICAgIGVsLnN0eWxlKAogICAgICAgICAgICAgICAgICAgICJwYWRkaW5n"
    "OjZweCAxNHB4O2JvcmRlci1yYWRpdXM6N3B4O2ZvbnQtc2l6ZToxMnB4O2ZvbnQtd2VpZ2h0OjcwMDsiCiAgICAgICAgICAgICAg"
    "ICAgICAgImN1cnNvcjpwb2ludGVyOyIgKyAoCiAgICAgICAgICAgICAgICAgICAgICAgICJiYWNrZ3JvdW5kOnJnYmEoMCwyNTUs"
    "MTM2LDAuMTUpO2NvbG9yOiMwMGZmODg7IgogICAgICAgICAgICAgICAgICAgICAgICAiYm9yZGVyOjFweCBzb2xpZCByZ2JhKDAs"
    "MjU1LDEzNiwwLjQpOyIKICAgICAgICAgICAgICAgICAgICAgICAgaWYgYWN0aXZlIGVsc2UKICAgICAgICAgICAgICAgICAgICAg"
    "ICAgImJhY2tncm91bmQ6cmdiYSgyNTUsMjU1LDI1NSwwLjAzKTtjb2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpOyIKICAgICAg"
    "ICAgICAgICAgICAgICAgICAgImJvcmRlcjoxcHggc29saWQgcmdiYSgyNTUsMjU1LDI1NSwwLjA4KTsiCiAgICAgICAgICAgICAg"
    "ICAgICAgKQogICAgICAgICAgICAgICAgKQogICAgICAgIHVpLm5vdGlmeShmItCg0LXQttC40Lw6IHsn0KLQldCh0KLQldCgICjQ"
    "uNGB0YLQvtGA0LjRjyknIGlmIGlzX3Rlc3RlciBlbHNlICfQoNCV0JDQmyAo0LbQuNCy0L7QuSDRgNGL0L3QvtC6KSd9IiwKICAg"
    "ICAgICAgICAgICAgICAgdHlwZT0iaW5mbyIpCgogICAgZGVmIHJlcXVlc3Rfc3RvcCgpOgogICAgICAgIGlmIG5vdCBzdGF0ZS5n"
    "ZXQoInRlc3Rlcl9ydW5uaW5nIik6CiAgICAgICAgICAgIHVpLm5vdGlmeSgi0J/QtdGA0LXQsdC+0YAg0L3QtSDQuNC00ZHRgiIs"
    "IHR5cGU9Indhcm5pbmciKQogICAgICAgICAgICByZXR1cm4KICAgICAgICBzdGF0ZVsic3RvcF9yZXF1ZXN0ZWQiXSA9IFRydWUK"
    "ICAgICAgICB1aS5ub3RpZnkoIuKPuCDQodCi0J7QnyDigJQg0L7RgdGC0LDQvdCw0LLQu9C40LLQsNGOINC90LAg0YHQu9C10LTR"
    "g9GO0YnQtdC8INC60LDQvdC00LjQtNCw0YLQtS4uLiIsIHR5cGU9ImluZm8iKQoKICAgIGRlZiBfYXBwbHlfYWdlbnRfcmVzdWx0"
    "KGFpZCwgciwgbmFycmF0aXZlKToKICAgICAgICAiIiIKICAgICAgICDQoNCw0YHQutC70LDQtNGL0LLQsNC10YIg0YDQtdC30YPQ"
    "u9GM0YLQsNGCINCe0JTQndCe0JPQniDQsNCz0LXQvdGC0LAg0L/QviBzdGF0ZSDQutCw0LHQuNC90LXRgtCwOiDQsNCy0LDRgtCw"
    "0YDRiywKICAgICAgICDQv9GD0LfRi9GA0YzQutC4INGH0LDRgtCwLCDQstGM0Y7QtdGAINC+0YLRh9GR0YLQsCwgKl9sYXN0X3J1"
    "biAo0YDQsNCx0L7Rh9Cw0Y8g0L/QsNC80Y/RgtGMINC00LvRjyDRh9Cw0YLQsAogICAgICAgINGBINCw0LPQtdC90YLQvtC8INC/"
    "0L4g0LrQu9C40LrRgyDQvdCwINC/0YPQt9GL0YDRkdC6KS4KCiAgICAgICAg0J7QkdCp0JDQryDRhNGD0L3QutGG0LjRjyDQtNC7"
    "0Y8g0J7QkdCe0JjQpSDQv9GD0YLQtdC5INC/0YDQvtCx0YPQttC00LXQvdC40Y8g0KHQvtCy0LXRgtCwIC0tINCg0KvQndCe0JoK"
    "ICAgICAgICAocnVuX21hcmtldCkg0Lgg0KLQldCh0KLQldCgIChydW5fdGVzdGVyX3Nlc3Npb24pLiDQoNCw0L3RjNGI0LUg0YLQ"
    "tdGB0YLQtdGAINGN0YLRgwogICAgICAgINC/0LDQvNGP0YLRjCDQvdC1INC/0LjRgdCw0Lsg0LLQvtCy0YHQtTogc3RhdGVbKl9s"
    "YXN0X3J1bl0g0L7RgdGC0LDQstCw0LvRgdGPINC/0YPRgdGCINC/0L7RgdC70LUKICAgICAgICDRgtC10YHRgtC+0LLQvtCz0L4g"
    "0L/RgNC+0LPQvtC90LAsINC4INGH0LDRgiDRgSDQsNCz0LXQvdGC0L7QvCDRgdGA0LDQt9GDINC/0L7RgdC70LUg0KLQldCh0KLQ"
    "ldCg0JAg0YfQtdGB0YLQvdC+LAogICAgICAgINC90L4g0L3QtdCy0LXRgNC90L4g0L/QviDRgdGD0YLQuCDQvtGC0LLQtdGH0LDQ"
    "uyAi0YDRi9C90L7QuiDQvdC1INC30LDQv9GD0YHQutCw0LvQuCIgLS0g0YXQvtGC0Y8g0LDQs9C10L3RggogICAgICAgINGC0L7Q"
    "u9GM0LrQviDRh9GC0L4g0L7RgtGA0LDQsdC+0YLQsNC7INGH0LXRgNC10Lcg0YLRgyDQttC1INC00LLQtdGA0YwgKGNvdW5jaWwu"
    "d2FrZV9jb3VuY2lsKS4KICAgICAgICDQotC10L/QtdGA0Ywg0L7QsdCwINC/0YPRgtC4INC60LvQsNC00YPRgiDQv9Cw0LzRj9GC"
    "0Ywg0YHRjtC00LAg0LbQtSAtLSDQvtC00LjQvSDQuNGB0YLQvtGH0L3QuNC6INC/0YDQsNCy0LTRiy4KICAgICAgICAiIiIKICAg"
    "ICAgICAjIOKUgOKUgCBBMDEg0JjQodCa0KDQkCDilIDilIAKICAgICAgICBpZiBhaWQgPT0gIkEwMSI6CiAgICAgICAgICAgIGlm"
    "IG5vdCByLmdldCgib2siKToKICAgICAgICAgICAgICAgIGVyciA9IHIuZ2V0KCJlcnJvciIsICLQvdC10LjQt9Cy0LXRgdGC0L3Q"
    "sNGPINC+0YjQuNCx0LrQsCIpCiAgICAgICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0uYXBwZW5kKHsKICAgICAgICAg"
    "ICAgICAgICAgICAicm9sZSI6ICJhc3Npc3RhbnQiLCAiYWdlbnQiOiAiQTAxIiwgImNvbnRlbnQiOiBmIuKaoO+4jyB7ZXJyfSJ9"
    "KQogICAgICAgICAgICAgICAgdXBkYXRlX2NoYXRfZGlzcGxheSgpCiAgICAgICAgICAgICAgICB1aS5ub3RpZnkoZXJyLCB0eXBl"
    "PSJuZWdhdGl2ZSIsIHRpbWVvdXQ9NjAwMCkKICAgICAgICAgICAgICAgIHJldHVybgogICAgICAgICAgICBzdGF0ZVsiYWN0aXZl"
    "X2FnZW50Il0gPSAiQTAxIgogICAgICAgICAgICBzdGF0ZVsiaXNrcmFfc2lnbmFsIl0gPSByLmdldCgic2lnbmFsIiwge30pCiAg"
    "ICAgICAgICAgIHN0YXRlWyJpc2tyYV9zdGF0cyJdICA9IHIuZ2V0KCJzdGF0cyIsIHt9KQogICAgICAgICAgICBzdGF0ZVsibWFy"
    "a2V0Il0gICAgICAgPSByLmdldCgibWFya2V0Iiwge30pCiAgICAgICAgICAgIHN0YXRlWyJyZXBvcnRzIl1bIkEwMSJdID0gci5n"
    "ZXQoIm5hcnJhdGl2ZSIsICIiKSBvciByLmdldCgicmF3IiwgIiIpCiAgICAgICAgICAgIHN0YXRlWyJpc2tyYV9sYXN0X3J1biJd"
    "ID0gewogICAgICAgICAgICAgICAgIm5hcnJhdGl2ZSI6IHIuZ2V0KCJuYXJyYXRpdmUiLCAiIiksCiAgICAgICAgICAgICAgICAi"
    "c2lnbmFsIjogICAgci5nZXQoInNpZ25hbCIsIHt9KSwKICAgICAgICAgICAgICAgICJtYXJrZXQiOiAgICByLmdldCgibWFya2V0"
    "Iiwge30pLAogICAgICAgICAgICB9CiAgICAgICAgICAgIHVwZGF0ZV9hdmF0YXIoKQogICAgICAgICAgICB1cGRhdGVfdml0YWxz"
    "KCkKICAgICAgICAgICAgdXBkYXRlX2F2YXRhcl9zdGF0ZXMoKQogICAgICAgICAgICB1cGRhdGVfc3RhdHNfcGFuZWwoKQogICAg"
    "ICAgICAgICBzaWcgPSBzdGF0ZVsiaXNrcmFfc2lnbmFsIl0KICAgICAgICAgICAgdXBkYXRlX3ZpZXdlcigKICAgICAgICAgICAg"
    "ICAgIGYiIyDinLTvuI8ge19hZ2VudF9sYWJlbChyb3N0ZXIsJ0EwMScpfSAoQTAxKVxuXG4iCiAgICAgICAgICAgICAgICBmIioq"
    "0KHRgtCw0YLRg9GBOioqIHtzaWcuZ2V0KCd0MV9zdGF0dXMnLCfigJQnKX0gIMK3ICAiCiAgICAgICAgICAgICAgICBmIioq0JTQ"
    "uNCy0LXRgNCz0LXQvdGG0LjRjzoqKiB7c2lnLmdldCgnZGl2ZXJnZW5jZScsJ+KAlCcpfVxuXG4iCiAgICAgICAgICAgICAgICBm"
    "Ii0tLVxuXG57ci5nZXQoJ25hcnJhdGl2ZScsJycpIG9yICcqKNC90LXRgiDRgtC10LrRgdGC0LApKid9IgogICAgICAgICAgICAp"
    "CiAgICAgICAgICAgIHN0YXRlWyJjaGF0X2hpc3RvcnkiXS5hcHBlbmQoewogICAgICAgICAgICAgICAgInJvbGUiOiAiYXNzaXN0"
    "YW50IiwgImFnZW50IjogIkEwMSIsCiAgICAgICAgICAgICAgICAiY29udGVudCI6IGYi4py077iPINCe0YLRgNCw0LHQvtGC0LDQ"
    "u9CwINGA0YvQvdC+0Log4oCUINGB0YLQsNGC0YPRgSB7c2lnLmdldCgndDFfc3RhdHVzJywn4oCUJyl9LiDQntGC0YfRkdGCINGB"
    "0L/RgNCw0LLQsC4ifSkKICAgICAgICAgICAgdXBkYXRlX2NoYXRfZGlzcGxheSgpCiAgICAgICAgICAgIHVpLm5vdGlmeShmIuKc"
    "tO+4jyDQmNGB0LrRgNCwOiB7c2lnLmdldCgndDFfc3RhdHVzJywn4oCUJyl9IiwgdHlwZT0icG9zaXRpdmUiKQogICAgICAgICAg"
    "ICByZXR1cm4KCiAgICAgICAgIyDilIDilIAg0L7RiNC40LHQutCwINC70Y7QsdC+0LPQviDQuNC3INC+0YHRgtCw0LvRjNC90YvR"
    "hSDQsNCz0LXQvdGC0L7QsiDilIDilIAKICAgICAgICBpZiBub3Qgci5nZXQoIm9rIik6CiAgICAgICAgICAgIF9uYW1lcyA9IHsi"
    "QTAyIjogKCLwn6atIiwgItCc0L7RgNC2IiksICJBMDMiOiAoIvCfmLEiLCAi0J/QsNC90LjQutGR0YAiKSwKICAgICAgICAgICAg"
    "ICAgICAgICAgICJBMDQiOiAoIvCfjq8iLCAi0JPQsNC90YEiKSwgIkEwNSI6ICgi8J+TmiIsICLQkNGA0YXQuNCy0LDRgNC40YPR"
    "gSIpLAogICAgICAgICAgICAgICAgICAgICAgIkEwNiI6ICgi8J+qqCIsIF9hZ2VudF9sYWJlbChyb3N0ZXIsICJBMDYiKSksCiAg"
    "ICAgICAgICAgICAgICAgICAgICAiQTA3IjogKCLimqEiLCBfYWdlbnRfbGFiZWwocm9zdGVyLCAiQTA3IikpLAogICAgICAgICAg"
    "ICAgICAgICAgICAgIkEwOCI6ICgi8J+boSIsIF9hZ2VudF9sYWJlbChyb3N0ZXIsICJBMDgiKSksCiAgICAgICAgICAgICAgICAg"
    "ICAgICAiQTA5IjogKCLwn5OLIiwgItCY0YHQv9C+0LvQvdC40YLQtdC70YwiKX0KICAgICAgICAgICAgaWNvbiwgbm0gPSBfbmFt"
    "ZXMuZ2V0KGFpZCwgKCLigKIiLCBhaWQpKQogICAgICAgICAgICB1aS5ub3RpZnkoZiJ7aWNvbn0ge25tfSDRgdC80L7Qu9GH0LDQ"
    "uyAo0L3QtdGCINC00LDQvdC90YvRhSDQuNC70Lgg0YHQsdC+0LkpIiwgdHlwZT0id2FybmluZyIpCiAgICAgICAgICAgIHJldHVy"
    "bgoKICAgICAgICBzaWcgPSByLmdldCgic2lnbmFsIiwge30pIG9yIHt9CgogICAgICAgICMg4pSA4pSAIEEwMiDQnNCe0KDQliDi"
    "lIDilIAKICAgICAgICBpZiBhaWQgPT0gIkEwMiI6CiAgICAgICAgICAgIHJiID0gci5nZXQoInJ1YmJlcl9iYW5kIiwge30pCiAg"
    "ICAgICAgICAgIHN0YXRlWyJyZXBvcnRzIl1bIkEwMiJdID0gbmFycmF0aXZlCiAgICAgICAgICAgIHN0YXRlWyJtb3JqX3NpZ25h"
    "bCJdID0gc2lnCiAgICAgICAgICAgIHN0YXRlWyJtb3JqX3N0YXRzIl0gID0gci5nZXQoInN0YXRzIiwge30pCiAgICAgICAgICAg"
    "IHN0YXRlWyJtb3JqX3J1YmJlciJdID0gcmIKICAgICAgICAgICAgc3RhdGVbIm1vcmpfbWFya2V0Il0gPSByLmdldCgibWFya2V0"
    "Iiwge30pCiAgICAgICAgICAgIHN0YXRlWyJtb3JqX2xhc3RfcnVuIl0gPSB7CiAgICAgICAgICAgICAgICAibmFycmF0aXZlIjog"
    "ICByLmdldCgibmFycmF0aXZlIiwgIiIpLAogICAgICAgICAgICAgICAgInNpZ25hbCI6ICAgICAgc2lnLAogICAgICAgICAgICAg"
    "ICAgIm1hcmtldCI6ICAgICAgci5nZXQoIm1hcmtldCIsIHt9KSwKICAgICAgICAgICAgICAgICJydWJiZXJfYmFuZCI6IHJiLAog"
    "ICAgICAgICAgICAgICAgImlza3JhX3N0YXR1cyI6IHIuZ2V0KCJpc2tyYV9zdGF0dXMiLCBzdGF0ZS5nZXQoImlza3JhX3NpZ25h"
    "bCIsIHt9KS5nZXQoInQxX3N0YXR1cyIpKSwKICAgICAgICAgICAgfQogICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0u"
    "YXBwZW5kKHsKICAgICAgICAgICAgICAgICJyb2xlIjogImFzc2lzdGFudCIsICJhZ2VudCI6ICJBMDIiLAogICAgICAgICAgICAg"
    "ICAgImNvbnRlbnQiOiAoZiLwn6atINCf0L7RgdC80L7RgtGA0LXQuy4g0J/QsNGB0YLRjDoge3NpZy5nZXQoJ21vcmpfc3RhdHVz"
    "Jywn4oCUJyl9LCDRgNC10LfQuNC90LrQsCAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBmInsn0L3QsNGC0Y/QvdGD0YLQ"
    "sCcgaWYgc2lnLmdldCgndGVuc2lvbl9wZWFrJykgZWxzZSAn0LLRj9C70L4nfS4g0J7RgtGH0ZHRgiDRgdC/0YDQsNCy0LAuIil9"
    "KQogICAgICAgICAgICB1cGRhdGVfY2hhdF9kaXNwbGF5KCkKICAgICAgICAgICAgdXBkYXRlX2F2YXRhcl9zdGF0ZXMoKQogICAg"
    "ICAgICAgICB1aS5ub3RpZnkoZiLwn6atINCc0L7RgNC2OiB7c2lnLmdldCgnbW9yal9zdGF0dXMnLCfigJQnKX0iLCB0eXBlPSJw"
    "b3NpdGl2ZSIpCgogICAgICAgICMg4pSA4pSAIEEwMyDQn9CQ0J3QmNCa0IHQoCDilIDilIAKICAgICAgICBlbGlmIGFpZCA9PSAi"
    "QTAzIjoKICAgICAgICAgICAgc3RhdGVbInJlcG9ydHMiXVsiQTAzIl0gPSBuYXJyYXRpdmUKICAgICAgICAgICAgc3RhdGVbInBh"
    "bmljX3NpZ25hbCJdID0gc2lnCiAgICAgICAgICAgIHN0YXRlWyJwYW5pY19zdGF0cyJdICA9IHIuZ2V0KCJzdGF0cyIsIHt9KQog"
    "ICAgICAgICAgICBzdGF0ZVsicGFuaWNfbWFya2V0Il0gPSByLmdldCgibWFya2V0Iiwge30pCiAgICAgICAgICAgIHN0YXRlWyJw"
    "YW5pY19sYXN0X3J1biJdID0gewogICAgICAgICAgICAgICAgIm5hcnJhdGl2ZSI6IHIuZ2V0KCJuYXJyYXRpdmUiLCAiIiksICJz"
    "aWduYWwiOiBzaWcsICJtYXJrZXQiOiByLmdldCgibWFya2V0Iiwge30pfQogICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5"
    "Il0uYXBwZW5kKHsKICAgICAgICAgICAgICAgICJyb2xlIjogImFzc2lzdGFudCIsICJhZ2VudCI6ICJBMDMiLAogICAgICAgICAg"
    "ICAgICAgImNvbnRlbnQiOiAoZiLwn5ixINCi0L7Qu9C/0LA6IHtzaWcuZ2V0KCdwYW5pY19waGFzZScsJ+KAlCcpfS4gIgogICAg"
    "ICAgICAgICAgICAgICAgICAgICAgICAgZiJ7c2lnLmdldCgnY3Jvd2Rfc2VudGltZW50JywnJyl9INCe0YLRh9GR0YIg0YHQv9GA"
    "0LDQstCwLiIpfSkKICAgICAgICAgICAgdXBkYXRlX2NoYXRfZGlzcGxheSgpCiAgICAgICAgICAgIHVwZGF0ZV9hdmF0YXJfc3Rh"
    "dGVzKCkKICAgICAgICAgICAgdWkubm90aWZ5KGYi8J+YsSDQn9Cw0L3QuNC60ZHRgDoge3NpZy5nZXQoJ3BhbmljX3BoYXNlJywn"
    "4oCUJyl9IiwgdHlwZT0icG9zaXRpdmUiKQoKICAgICAgICAjIOKUgOKUgCBBMDQg0JPQkNCd0KEg4pSA4pSACiAgICAgICAgZWxp"
    "ZiBhaWQgPT0gIkEwNCI6CiAgICAgICAgICAgIHN0YXRlWyJyZXBvcnRzIl1bIkEwNCJdID0gbmFycmF0aXZlCiAgICAgICAgICAg"
    "IHN0YXRlWyJoYW5zX3NpZ25hbCJdID0gc2lnCiAgICAgICAgICAgIHN0YXRlWyJoYW5zX3N0YXRzIl0gID0gci5nZXQoInN0YXRz"
    "Iiwge30pCiAgICAgICAgICAgIHN0YXRlWyJoYW5zX21hcmtldCJdID0gci5nZXQoIm1hcmtldCIsIHt9KQogICAgICAgICAgICBz"
    "dGF0ZVsiaGFuc19sYXN0X3J1biJdID0gewogICAgICAgICAgICAgICAgIm5hcnJhdGl2ZSI6IHIuZ2V0KCJuYXJyYXRpdmUiLCAi"
    "IiksICJzaWduYWwiOiBzaWcsICJtYXJrZXQiOiByLmdldCgibWFya2V0Iiwge30pfQogICAgICAgICAgICB2YWxpZCA9IHNpZy5n"
    "ZXQoImZyYWN0YWxfdmFsaWQiKQogICAgICAgICAgICBwcmV5ID0gKGYi0LTQvtCx0YvRh9CwIHtzaWcuZ2V0KCdmcmFjdGFsX3Np"
    "ZGUnLCfigJQnKX0gQCB7c2lnLmdldCgnZnJhY3RhbF9wcmljZScsJ+KAlCcpfSIKICAgICAgICAgICAgICAgICAgICBpZiB2YWxp"
    "ZCBlbHNlICLQtNC+0LHRi9GH0Lgg0L3QtdGCIikKICAgICAgICAgICAgc3RhdGVbImNoYXRfaGlzdG9yeSJdLmFwcGVuZCh7CiAg"
    "ICAgICAgICAgICAgICAicm9sZSI6ICJhc3Npc3RhbnQiLCAiYWdlbnQiOiAiQTA0IiwgImNvbnRlbnQiOiBmIvCfjq8g0KTRgNCw"
    "0LrRgtCw0Ls6IHtwcmV5fS4g0J7RgtGH0ZHRgiDRgdC/0YDQsNCy0LAuIn0pCiAgICAgICAgICAgIHVwZGF0ZV9jaGF0X2Rpc3Bs"
    "YXkoKQogICAgICAgICAgICB1cGRhdGVfYXZhdGFyX3N0YXRlcygpCiAgICAgICAgICAgIHVpLm5vdGlmeShmIvCfjq8g0JPQsNC9"
    "0YE6IHsn0YTRgNCw0LrRgtCw0Lsg0LLQvdC1INCa0YDQsNGB0L3QvtC5JyBpZiB2YWxpZCBlbHNlICfQv9GD0YHRgtC+J30iLCB0"
    "eXBlPSJwb3NpdGl2ZSIpCgogICAgICAgICMg4pSA4pSAIEEwNSDQkNCg0KXQmNCS0JDQoNCY0KPQoSDilIDilIAKICAgICAgICBl"
    "bGlmIGFpZCA9PSAiQTA1IjoKICAgICAgICAgICAgc3RhdGVbInJlcG9ydHMiXVsiQTA1Il0gPSBuYXJyYXRpdmUKICAgICAgICAg"
    "ICAgc3RhdGVbImFya2hpdl9zaWduYWwiXSA9IHNpZwogICAgICAgICAgICBzdGF0ZVsiYXJraGl2X3N0YXRzIl0gID0gci5nZXQo"
    "InN0YXRzIiwge30pCiAgICAgICAgICAgIHN0YXRlWyJhcmtoaXZfZGlnZXN0Il0gPSByLmdldCgiZGlnZXN0Iiwge30pCiAgICAg"
    "ICAgICAgIHN0YXRlWyJhcmtoaXZfbGFzdF9ydW4iXSA9IHsKICAgICAgICAgICAgICAgICJuYXJyYXRpdmUiOiByLmdldCgibmFy"
    "cmF0aXZlIiwgIiIpLCAic2lnbmFsIjogc2lnLCAic2lnbmF0dXJlIjogci5nZXQoInNpZ25hdHVyZSIsIHt9KX0KICAgICAgICAg"
    "ICAgY29uZiA9IHNpZy5nZXQoImFya2hpdl9jb25maWRlbmNlIiwgIuKAlCIpCiAgICAgICAgICAgIG5fID0gc2lnLmdldCgic2Ft"
    "cGxlX3NpemUiLCAi4oCUIikKICAgICAgICAgICAgc3RhdGVbImNoYXRfaGlzdG9yeSJdLmFwcGVuZCh7CiAgICAgICAgICAgICAg"
    "ICAicm9sZSI6ICJhc3Npc3RhbnQiLCAiYWdlbnQiOiAiQTA1IiwKICAgICAgICAgICAgICAgICJjb250ZW50IjogKGYi8J+TmiDQ"
    "n9C+0YXQvtC20LjRhSDRgdC70YPRh9Cw0LXQsiDQsiDQkNGC0LvQsNGB0LU6IHtuX30uINCj0LLQtdGA0LXQvdC90L7RgdGC0Yw6"
    "IHtjb25mfS4g0J7RgtGH0ZHRgiDRgdC/0YDQsNCy0LAuIil9KQogICAgICAgICAgICB1cGRhdGVfY2hhdF9kaXNwbGF5KCkKICAg"
    "ICAgICAgICAgdXBkYXRlX2F2YXRhcl9zdGF0ZXMoKQogICAgICAgICAgICB1aS5ub3RpZnkoZiLwn5OaINCQ0YDRhdC40LLQsNGA"
    "0LjRg9GBOiB7Y29uZn0gKHtuX30g0YHQu9GD0YfQsNC10LIpIiwgdHlwZT0icG9zaXRpdmUiKQoKICAgICAgICAjIOKUgOKUgCBB"
    "MDYvQTA3L0EwOCDQotCg0JXQmdCU0JXQoNCrIOKUgOKUgAogICAgICAgIGVsaWYgYWlkIGluICgiQTA2IiwgIkEwNyIsICJBMDgi"
    "KToKICAgICAgICAgICAgcHJlID0geyJBMDYiOiAiYnJ1dCIsICJBMDciOiAiYXZhbiIsICJBMDgiOiAiY29ucyJ9W2FpZF0KICAg"
    "ICAgICAgICAgaWNvbiA9IHsiQTA2IjogIvCfqqgiLCAiQTA3IjogIuKaoSIsICJBMDgiOiAi8J+boSJ9W2FpZF0KICAgICAgICAg"
    "ICAgX25tID0gX2FnZW50X2xhYmVsKHJvc3RlciwgYWlkKQogICAgICAgICAgICBzdGF0ZVsicmVwb3J0cyJdW2FpZF0gPSBuYXJy"
    "YXRpdmUKICAgICAgICAgICAgc3RhdGVbZiJ7cHJlfV9zaWduYWwiXSA9IHNpZwogICAgICAgICAgICBzdGF0ZVtmIntwcmV9X3N0"
    "YXRzIl0gID0gci5nZXQoInN0YXRzIiwge30pCiAgICAgICAgICAgIF9sYXN0X2tleSA9IHsiQTA2IjogImJydXRfbGFzdF9ydW4i"
    "LCAiQTA3IjogImF2YW5fbGFzdF9ydW4iLCAiQTA4IjogImNvbnNfbGFzdF9ydW4ifVthaWRdCiAgICAgICAgICAgIHN0YXRlW19s"
    "YXN0X2tleV0gPSB7CiAgICAgICAgICAgICAgICAibmFycmF0aXZlIjogci5nZXQoIm5hcnJhdGl2ZSIsICIiKSwgInNpZ25hbCI6"
    "IHNpZywgIm1hcmtldCI6IHIuZ2V0KCJtYXJrZXQiLCB7fSl9CiAgICAgICAgICAgIHZlcmRpY3QgPSBzaWcuZ2V0KGYie3ByZX1f"
    "dmVyZGljdCIsICLigJQiKQogICAgICAgICAgICBpZiB2ZXJkaWN0ID09ICJBUFBST1ZFRCI6CiAgICAgICAgICAgICAgICBsaW5l"
    "ID0gKGYie2ljb259IHtfbm19OiDQktCl0J7QlCB7c2lnLmdldChmJ3twcmV9X2RpcmVjdGlvbicsJycpfSDCtyAiCiAgICAgICAg"
    "ICAgICAgICAgICAgICAgIGYi0LLRhdC+0LQge3NpZy5nZXQoZid7cHJlfV9lbnRyeScsJ+KAlCcpfSDCtyDRgdGC0L7QvyB7c2ln"
    "LmdldChmJ3twcmV9X3N0b3AnLCfigJQnKX0gwrcgIgogICAgICAgICAgICAgICAgICAgICAgICBmItC70L7RgiB7c2lnLmdldChm"
    "J3twcmV9X2xvdCcsJ+KAlCcpfS4g0J7RgtGH0ZHRgiDRgdC/0YDQsNCy0LAuIikKICAgICAgICAgICAgICAgIHVpLm5vdGlmeShm"
    "IntpY29ufSB7X25tfTog0JLQpdCe0JQge3NpZy5nZXQoZid7cHJlfV9kaXJlY3Rpb24nLCcnKX0iLCB0eXBlPSJwb3NpdGl2ZSIp"
    "CiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBsaW5lID0gZiJ7aWNvbn0ge19ubX06INC/0LDRgSAoe3NpZy5nZXQo"
    "Zid7cHJlfV9yZWFzb24nLCfigJQnKX0pLiDQntGC0YfRkdGCINGB0L/RgNCw0LLQsC4iCiAgICAgICAgICAgICAgICB1aS5ub3Rp"
    "ZnkoZiJ7aWNvbn0ge19ubX06INC/0LDRgSIsIHR5cGU9ImluZm8iKQogICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0u"
    "YXBwZW5kKHsicm9sZSI6ICJhc3Npc3RhbnQiLCAiYWdlbnQiOiBhaWQsICJjb250ZW50IjogbGluZX0pCiAgICAgICAgICAgIHVw"
    "ZGF0ZV9jaGF0X2Rpc3BsYXkoKQogICAgICAgICAgICB1cGRhdGVfYXZhdGFyX3N0YXRlcygpCgogICAgICAgICMg4pSA4pSAIEEw"
    "OSDQmNCh0J/QntCb0J3QmNCi0JXQm9CsIOKUgOKUgAogICAgICAgIGVsaWYgYWlkID09ICJBMDkiOgogICAgICAgICAgICBmZG5h"
    "ID0gc2lnLmdldCgiZmluYWxfZG5hIiwge30pCiAgICAgICAgICAgIHNlbnQgPSBmZG5hLmdldCgib3JkZXJzX3NlbnQiLCAi4oCU"
    "IikKICAgICAgICAgICAgdHNrICA9IGZkbmEuZ2V0KCJ0YXNrX3Njb3JlIiwgIuKAlCIpCiAgICAgICAgICAgIHN0YXRlWyJyZXBv"
    "cnRzIl1bIkEwOSJdID0gci5nZXQoIm5hcnJhdGl2ZSIsICIiKSArICJcblxu4oCUINCb0LXRgtC+0L/QuNGB0Yw6ICIgKyBzaWcu"
    "Z2V0KCJoaXN0b3J5X2RuYSIsICIiKQogICAgICAgICAgICBzdGF0ZVsiZXhlY3V0b3Jfc2lnbmFsIl0gPSBzaWcKICAgICAgICAg"
    "ICAgc3RhdGVbImV4ZWN1dG9yX3N0YXRzIl0gID0gci5nZXQoInN0YXRzIiwge30pCiAgICAgICAgICAgIHN0YXRlWyJleGVjdXRv"
    "cl9sYXN0X3J1biJdID0gewogICAgICAgICAgICAgICAgIm5hcnJhdGl2ZSI6IHIuZ2V0KCJuYXJyYXRpdmUiLCAiIiksICJzaWdu"
    "YWwiOiBzaWcsICJtYXJrZXQiOiByLmdldCgibWFya2V0Iiwge30pfQogICAgICAgICAgICBsaW5lID0gZiLwn5OLINCY0YHQv9C+"
    "0LvQvdC40YLQtdC70Yw6INC+0YDQtNC10YDQvtCyIHtzZW50fSDQuNC3IDMgwrcgdGFza19zY29yZSB7dHNrfS4ge3NpZy5nZXQo"
    "J2hpc3RvcnlfZG5hJywnJyl9IgogICAgICAgICAgICB1aS5ub3RpZnkoZiLwn5OLINCY0YHQv9C+0LvQvdC40YLQtdC70Yw6IHtz"
    "ZW50fSDQuNC3IDMiLCB0eXBlPSJwb3NpdGl2ZSIpCiAgICAgICAgICAgIHN0YXRlWyJjaGF0X2hpc3RvcnkiXS5hcHBlbmQoeyJy"
    "b2xlIjogImFzc2lzdGFudCIsICJhZ2VudCI6ICJBMDkiLCAiY29udGVudCI6IGxpbmV9KQogICAgICAgICAgICB1cGRhdGVfY2hh"
    "dF9kaXNwbGF5KCkKICAgICAgICAgICAgdXBkYXRlX2F2YXRhcl9zdGF0ZXMoKQoKICAgIGFzeW5jIGRlZiBydW5fdGVzdGVyX3Nl"
    "c3Npb24oKToKICAgICAgICBhc3NldHMgPSBzdGF0ZS5nZXQoImxvYWRlZF9hc3NldHMiLCBbXSkKICAgICAgICBhaSA9IHN0YXRl"
    "LmdldCgiYWN0aXZlX2Fzc2V0IikKICAgICAgICBoaXN0ID0gYXNzZXRzW2FpXSBpZiAoYXNzZXRzIGFuZCBhaSBpcyBub3QgTm9u"
    "ZSBhbmQgMCA8PSBhaSA8IGxlbihhc3NldHMpKSBlbHNlIE5vbmUKICAgICAgICBpZiBub3QgaGlzdDoKICAgICAgICAgICAgdWku"
    "bm90aWZ5KCLQl9Cw0LPRgNGD0LfQuCDQsNC60YLQuNCyINC4INC60LvQuNC60L3QuCDQv9C+INC90LXQvNGDINCyINGB0L/QuNGB"
    "0LrQtSDRgdC70LXQstCwIiwgdHlwZT0id2FybmluZyIpCiAgICAgICAgICAgIHJldHVybgogICAgICAgIGlmIHN0YXRlLmdldCgi"
    "dGVzdGVyX3J1bm5pbmciKToKICAgICAgICAgICAgdWkubm90aWZ5KCLQn9C10YDQtdCx0L7RgCDRg9C20LUg0LjQtNGR0YIuLi4i"
    "LCB0eXBlPSJ3YXJuaW5nIikKICAgICAgICAgICAgcmV0dXJuCgogICAgICAgIHN0YXRlWyJ0ZXN0ZXJfcnVubmluZyJdID0gVHJ1"
    "ZQogICAgICAgIHN0YXRlWyJzdG9wX3JlcXVlc3RlZCJdID0gRmFsc2UKICAgICAgICBzeW1ib2wgPSBoaXN0LmdldCgic3ltYm9s"
    "IiwgIlhBVVVTRCIpCiAgICAgICAgdGYgICAgID0gaGlzdC5nZXQoInRpbWVmcmFtZSIsICJINCIpCiAgICAgICAgcGF0aCAgID0g"
    "aGlzdC5nZXQoInBhdGgiLCAiIikKICAgICAgICBuICAgICAgPSBpbnQoc3RhdGUuZ2V0KCJiYXJzX3RvX2xpdmUiLCAxKSBvciAx"
    "KQoKICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0uYXBwZW5kKHsKICAgICAgICAgICAgInJvbGUiOiAiYXNzaXN0YW50Iiwg"
    "ImFnZW50IjogIlNZU1RFTSIsCiAgICAgICAgICAgICJjb250ZW50IjogZiLilrYg0KLQldCh0KLQldCgOiDQs9C+0L3RjiB7c3lt"
    "Ym9sfSB7dGZ9IMK3INC70L7QstC70Y4ge259INGB0YDQsNCx0LDRgtGL0LLQsNC90LjQuS4g0KHQotCe0J8g4oCUINC/0YDQtdGA"
    "0LLQsNGC0YwuIn0pCiAgICAgICAgdXBkYXRlX2NoYXRfZGlzcGxheSgpCiAgICAgICAgdWkubm90aWZ5KGYi4pa2INCi0LXRgdGC"
    "0LXRgDoge3N5bWJvbH0ge3RmfSIsIHR5cGU9ImluZm8iKQoKICAgICAgICBkZWYgX29uX3Byb2dyZXNzKG1zZyk6CiAgICAgICAg"
    "ICAgIGlmIGlzaW5zdGFuY2UobXNnLCBkaWN0KSBhbmQgbXNnLmdldCgidHlwZSIpID09ICJyZXBvcnQiOgogICAgICAgICAgICAg"
    "ICAgYWlkID0gbXNnLmdldCgiYWdlbnQiKQogICAgICAgICAgICAgICAgbmFycmF0aXZlID0gbXNnLmdldCgibmFycmF0aXZlIiwg"
    "IiIpCiAgICAgICAgICAgICAgICByZXN1bHQgPSBtc2cuZ2V0KCJyZXN1bHQiKQogICAgICAgICAgICAgICAgaWYgYWlkIGFuZCBu"
    "YXJyYXRpdmUgYW5kIHJlc3VsdCBpcyBub3QgTm9uZToKICAgICAgICAgICAgICAgICAgICAjIEVOR0lORV9PTkVfRE9PUl9WMSAo"
    "0L/QsNC80Y/RgtGMINGH0LDRgtCwKTogcmVzdWx0INC/0YDQuNGB0YPRgtGB0YLQstGD0LXRgiDigJQKICAgICAgICAgICAgICAg"
    "ICAgICAjINGC0LXRgdGC0LXRgCDRgtC10L/QtdGA0Ywg0L3QtdGB0ZHRgiDQn9Ce0JvQndCr0Jkg0YHQu9C+0LLQsNGA0YwgcnVu"
    "Xyog0LDQs9C10L3RgtCwLCDQvdC1CiAgICAgICAgICAgICAgICAgICAgIyDRgtC+0LvRjNC60L4g0LPQvtC70L7RgS4g0JfQvtCy"
    "0ZHQvCDQotCjINCW0JUg0YTRg9C90LrRhtC40Y4sINGH0YLQviDQuCDQoNCr0J3QntCaIOKAlAogICAgICAgICAgICAgICAgICAg"
    "ICMg0LfQsNC/0L7Qu9C90LjRgiAqX2xhc3RfcnVuLCDRh9GC0L7QsdGLINGH0LDRgiDRgSDQsNCz0LXQvdGC0L7QvCDQv9C+0YHQ"
    "u9C1CiAgICAgICAgICAgICAgICAgICAgIyDQotCV0KHQotCV0KDQkCDQt9C90LDQuywg0YfRgtC+INGC0L7RgiDRgtC+0LvRjNC6"
    "0L4g0YfRgtC+INCy0LjQtNC10LssINCwINC90LUg0L7RgtCy0LXRh9Cw0LsKICAgICAgICAgICAgICAgICAgICAjINGH0LXRgdGC"
    "0L3Qviwg0L3QviDQvdC10LLQtdGA0L3QviAi0YDRi9C90L7QuiDQvdC1INC30LDQv9GD0YHQutCw0LvQuCIuCiAgICAgICAgICAg"
    "ICAgICAgICAgaWYgYWlkID09ICJBMDEiOgogICAgICAgICAgICAgICAgICAgICAgICBzdGF0ZVsicmVwb3J0cyJdID0ge30KICAg"
    "ICAgICAgICAgICAgICAgICAgICAgc3RhdGVbImFjdGl2ZV9hZ2VudCJdID0gTm9uZQogICAgICAgICAgICAgICAgICAgICAgICB0"
    "cnk6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICB1cGRhdGVfYXZhdGFyX3N0YXRlcygpCiAgICAgICAgICAgICAgICAgICAg"
    "ICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBwYXNzCiAgICAgICAgICAgICAgICAgICAg"
    "dHJ5OgogICAgICAgICAgICAgICAgICAgICAgICBfYXBwbHlfYWdlbnRfcmVzdWx0KGFpZCwgcmVzdWx0LCBuYXJyYXRpdmUpCiAg"
    "ICAgICAgICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICAgICAgICAgICAgICBwcmludChmIltU"
    "T1JHwrdURVNURVJdIF9hcHBseV9hZ2VudF9yZXN1bHQg0YHQsdC+0LkgKHthaWR9KToge2V9IikKICAgICAgICAgICAgICAgICAg"
    "ICByZXR1cm4KICAgICAgICAgICAgICAgIGlmIGFpZCBhbmQgbmFycmF0aXZlOgogICAgICAgICAgICAgICAgICAgIGlmIGFpZCA9"
    "PSAiQTAxIjoKICAgICAgICAgICAgICAgICAgICAgICAgc3RhdGVbInJlcG9ydHMiXSA9IHt9CiAgICAgICAgICAgICAgICAgICAg"
    "ICAgIHN0YXRlWyJhY3RpdmVfYWdlbnQiXSA9IE5vbmUKICAgICAgICAgICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAg"
    "ICAgICAgICAgICAgICAgdXBkYXRlX2F2YXRhcl9zdGF0ZXMoKQogICAgICAgICAgICAgICAgICAgICAgICBleGNlcHQgRXhjZXB0"
    "aW9uOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgcGFzcwogICAgICAgICAgICAgICAgICAgIHN0YXRlWyJyZXBvcnRzIl1b"
    "YWlkXSA9IG5hcnJhdGl2ZQogICAgICAgICAgICAgICAgICAgIHN0YXRlWyJhY3RpdmVfYWdlbnQiXSA9IGFpZAogICAgICAgICAg"
    "ICAgICAgICAgIGxhYmVsID0gX2FnZW50X2xhYmVsKHJvc3RlciwgYWlkKQogICAgICAgICAgICAgICAgICAgIHRyeToKICAgICAg"
    "ICAgICAgICAgICAgICAgICAgdXBkYXRlX3ZpZXdlcihmIiMge2xhYmVsfSAoe2FpZH0pXG5cbntuYXJyYXRpdmV9IikKICAgICAg"
    "ICAgICAgICAgICAgICAgICAgdXBkYXRlX2F2YXRhcigpCiAgICAgICAgICAgICAgICAgICAgICAgIHVwZGF0ZV92aXRhbHMoKQog"
    "ICAgICAgICAgICAgICAgICAgICAgICB1cGRhdGVfYXZhdGFyX3N0YXRlcygpCiAgICAgICAgICAgICAgICAgICAgZXhjZXB0IEV4"
    "Y2VwdGlvbjoKICAgICAgICAgICAgICAgICAgICAgICAgcGFzcwogICAgICAgICAgICAgICAgICAgIHN0YXR1cyA9IG1zZy5nZXQo"
    "InN0YXR1cyIsICIiKQogICAgICAgICAgICAgICAgICAgIHRhaWwgPSBmIiDCtyB7c3RhdHVzfSIgaWYgc3RhdHVzIGVsc2UgIiIK"
    "ICAgICAgICAgICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0uYXBwZW5kKHsKICAgICAgICAgICAgICAgICAgICAgICAg"
    "InJvbGUiOiAiYXNzaXN0YW50IiwgImFnZW50IjogYWlkLAogICAgICAgICAgICAgICAgICAgICAgICAiY29udGVudCI6IGYi0L7R"
    "gtGA0LDQsdC+0YLQsNC7e3RhaWx9LiDQntGC0YfRkdGCINGB0L/RgNCw0LLQsC4ifSkKICAgICAgICAgICAgICAgICAgICB0cnk6"
    "CiAgICAgICAgICAgICAgICAgICAgICAgIHVwZGF0ZV9jaGF0X2Rpc3BsYXkoKQogICAgICAgICAgICAgICAgICAgIGV4Y2VwdCBF"
    "eGNlcHRpb246CiAgICAgICAgICAgICAgICAgICAgICAgIHBhc3MKICAgICAgICAgICAgICAgIHJldHVybgogICAgICAgICAgICBp"
    "ZiBpc2luc3RhbmNlKG1zZywgZGljdCkgYW5kIG1zZy5nZXQoInR5cGUiKSA9PSAidmVyZGljdCI6CiAgICAgICAgICAgICAgICB0"
    "eHQgPSBtc2cuZ2V0KCJ0ZXh0IiwgIiIpCiAgICAgICAgICAgICAgICBoaW50ID0gbXNnLmdldCgiaGludCIsICIiKQogICAgICAg"
    "ICAgICAgICAgc3RhdGVbImNoYXRfaGlzdG9yeSJdLmFwcGVuZCh7CiAgICAgICAgICAgICAgICAgICAgInJvbGUiOiAiYXNzaXN0"
    "YW50IiwgImFnZW50IjogItCg0JDQl9CS0JjQm9Ca0JAiLAogICAgICAgICAgICAgICAgICAgICJjb250ZW50IjogZiLwn5OKIHt0"
    "eHR9XG7ihpIge2hpbnR9In0pCiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgdXBkYXRlX2NoYXRfZGlz"
    "cGxheSgpCiAgICAgICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICAgICAgICAgIHBhc3MKICAgICAgICAg"
    "ICAgICAgIHJldHVybgogICAgICAgICAgICBpZiBpc2luc3RhbmNlKG1zZywgZGljdCkgYW5kIG1zZy5nZXQoInR5cGUiKSA9PSAi"
    "dHJhZGUiOgogICAgICAgICAgICAgICAgc3RhdGVbImNoYXRfaGlzdG9yeSJdLmFwcGVuZCh7CiAgICAgICAgICAgICAgICAgICAg"
    "InJvbGUiOiAiYXNzaXN0YW50IiwgImFnZW50IjogItCh0JTQldCb0JrQkCIsCiAgICAgICAgICAgICAgICAgICAgImNvbnRlbnQi"
    "OiBtc2cuZ2V0KCJ0ZXh0IiwgIiIpfSkKICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICB1cGRhdGVfY2hh"
    "dF9kaXNwbGF5KCkKICAgICAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgICAgICAgICAgcGFzcwogICAg"
    "ICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgICAgIGlmIGlzaW5zdGFuY2UobXNnLCBkaWN0KSBhbmQgbXNnLmdldCgidHlwZSIp"
    "ID09ICJwcm9ncmVzcyI6CiAgICAgICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0uYXBwZW5kKHsKICAgICAgICAgICAg"
    "ICAgICAgICAicm9sZSI6ICJhc3Npc3RhbnQiLCAiYWdlbnQiOiAiwrfCt8K3IiwKICAgICAgICAgICAgICAgICAgICAiY29udGVu"
    "dCI6IG1zZy5nZXQoInRleHQiLCAiIil9KQogICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgIHVwZGF0ZV9j"
    "aGF0X2Rpc3BsYXkoKQogICAgICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgICAgICAgICBwYXNzCiAg"
    "ICAgICAgICAgICAgICByZXR1cm4KICAgICAgICAgICAgcHJpbnQoZiJbVE9SR8K3VEVTVEVSXSB7bXNnfSIpCgogICAgICAgIGRl"
    "ZiBfc2hvdWxkX3N0b3AoKToKICAgICAgICAgICAgcmV0dXJuIHN0YXRlLmdldCgic3RvcF9yZXF1ZXN0ZWQiLCBGYWxzZSkKCiAg"
    "ICAgICAgdHJ5OgogICAgICAgICAgICBmcm9tIHRlc3Rlcl9leHByZXNzIGltcG9ydCBydW5fdGVzdGVyCiAgICAgICAgICAgIGF3"
    "YWl0IGFzeW5jaW8uZ2V0X2V2ZW50X2xvb3AoKS5ydW5faW5fZXhlY3V0b3IoCiAgICAgICAgICAgICAgICBOb25lLAogICAgICAg"
    "ICAgICAgICAgbGFtYmRhOiBydW5fdGVzdGVyKAogICAgICAgICAgICAgICAgICAgIGNzdl9wYXRoPXBhdGgsIHN5bWJvbD1zeW1i"
    "b2wsIHRpbWVmcmFtZT10ZiwKICAgICAgICAgICAgICAgICAgICBuX3NpZ25hbHM9biwgb25fcHJvZ3Jlc3M9X29uX3Byb2dyZXNz"
    "LAogICAgICAgICAgICAgICAgICAgIHNob3VsZF9zdG9wPV9zaG91bGRfc3RvcCwKICAgICAgICAgICAgICAgICkKICAgICAgICAg"
    "ICAgKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgdWkubm90aWZ5KGYi0KLQtdGB0YLQtdGAINGD"
    "0L/QsNC7OiB7ZX0iLCB0eXBlPSJuZWdhdGl2ZSIpCiAgICAgICAgICAgIHN0YXRlWyJjaGF0X2hpc3RvcnkiXS5hcHBlbmQoewog"
    "ICAgICAgICAgICAgICAgInJvbGUiOiAiYXNzaXN0YW50IiwgImFnZW50IjogIlNZU1RFTSIsCiAgICAgICAgICAgICAgICAiY29u"
    "dGVudCI6IGYi4pqg77iPINCi0LXRgdGC0LXRgCDRg9C/0LDQuzoge2V9In0pCiAgICAgICAgICAgIHVwZGF0ZV9jaGF0X2Rpc3Bs"
    "YXkoKQogICAgICAgIGZpbmFsbHk6CiAgICAgICAgICAgIHN0YXRlWyJ0ZXN0ZXJfcnVubmluZyJdID0gRmFsc2UKICAgICAgICAg"
    "ICAgc3RvcHBlZCA9IHN0YXRlLmdldCgic3RvcF9yZXF1ZXN0ZWQiLCBGYWxzZSkKICAgICAgICAgICAgc3RhdGVbInN0b3BfcmVx"
    "dWVzdGVkIl0gPSBGYWxzZQoKICAgICAgICB0YWlsID0gIuKPuCDQvtGB0YLQsNC90L7QstC70LXQvSDQv9C+INCh0KLQntCfIiBp"
    "ZiBzdG9wcGVkIGVsc2UgIuKckyDQt9Cw0YXQvtC0INC/0YDQvtC20LjRgiIKICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0u"
    "YXBwZW5kKHsKICAgICAgICAgICAgInJvbGUiOiAiYXNzaXN0YW50IiwgImFnZW50IjogIlNZU1RFTSIsCiAgICAgICAgICAgICJj"
    "b250ZW50IjogZiJ7dGFpbH0uINCh0L7QstC10YIg0L7RgtGA0LDQsdC+0YLQsNC7INC40YHRgtC+0YDQuNGOLiJ9KQogICAgICAg"
    "IHVwZGF0ZV9jaGF0X2Rpc3BsYXkoKQogICAgICAgIHVwZGF0ZV9hdmF0YXJfc3RhdGVzKCkKICAgICAgICB1aS5ub3RpZnkodGFp"
    "bCwgdHlwZT0icG9zaXRpdmUiIGlmIG5vdCBzdG9wcGVkIGVsc2UgIndhcm5pbmciKQoKICAgIGFzeW5jIGRlZiBtYXJrZXRfZGlz"
    "cGF0Y2goKToKICAgICAgICBpZiBzdGF0ZS5nZXQoIm1vZGUiKSA9PSAidGVzdGVyIjoKICAgICAgICAgICAgYXdhaXQgcnVuX3Rl"
    "c3Rlcl9zZXNzaW9uKCkKICAgICAgICBlbHNlOgogICAgICAgICAgICBhd2FpdCBydW5fbWFya2V0KCkKCiAgICBhc3luYyBkZWYg"
    "cnVuX21hcmtldCgpOgogICAgICAgICMg4pSA4pSAINCV0JTQmNCd0JDQryDQlNCS0JXQoNCsINCh0J7QktCV0KLQkCAoRU5HSU5F"
    "X09ORV9ET09SX1YxKSDilIDilIAKICAgICAgICAjINCg0LDQvdGM0YjQtSDQt9C00LXRgdGMINCx0YvQu9CwINGA0YPRh9C90LDR"
    "jyDQu9C10YHRgtC90LjRhtCwINCy0YvQt9C+0LLQvtCyINCw0LPQtdC90YLQvtCyIOKAlCDQstGC0L7RgNCw0Y8KICAgICAgICAj"
    "INC60L7Qv9C40Y8g0YLQvtC5LCDRh9GC0L4g0LbQuNC70LAg0LIgdGVzdGVyX2V4cHJlc3MucHkuINCt0YLQviDQsdGL0Lsg0LzQ"
    "sNGB0LrQsNGA0LDQtDoKICAgICAgICAjINC00LLQtSDQu9C10YHRgtC90LjRhtGLINGA0LDRgdGF0L7QtNGP0YLRgdGPLiDQotC1"
    "0L/QtdGA0Ywg0LrQsNCx0LjQvdC10YIg0LfQvtCy0ZHRgiDQotCjINCW0JUg0LTQstC10YDRjAogICAgICAgICMgY291bmNpbC53"
    "YWtlX2NvdW5jaWwsINGH0YLQviDQuCDRgtC10YHRgtC10YAuINCf0L7RgNGP0LTQvtC6LCDQstC+0YDQvtGC0LAg0L/QvgogICAg"
    "ICAgICMg0YHQv9GD0YHQutGDLCDQvtCx0YDQsNCx0L7RgtC60LAg0YHQsdC+0LXQsiDigJQg0L7QtNC90L4g0LzQtdGB0YLQviDQ"
    "v9GA0LDQstC00YsgKGNvdW5jaWwucHkpLgogICAgICAgICMKICAgICAgICAjINCS0J7QoNCe0KLQkDog0YDQsNC90YzRiNC1INC6"
    "0LDQsdC40L3QtdGCINGB0LDQvCDQv9GA0L7QstC10YDRj9C7IHQxIGluIChERVRFQ1RFRCwKICAgICAgICAjIENPTkZJUk1FRCks"
    "INGH0YLQvtCx0Ysg0YDQtdGI0LjRgtGMLCDQsdGD0LTQuNGC0Ywg0LvQuCDQvtGB0YLQsNC70YzQvdGL0YUuINCt0YLQviDQsdGL"
    "0LvQsAogICAgICAgICMg0KHQotCQ0KDQkNCvINC70L7Qs9C40LrQsCDigJQg0YLQtdGB0YLQtdGAINGD0LbQtSDQtNCw0LLQvdC+"
    "INC20LjQstGR0YIg0L/QviDQl9CQ0JrQntCd0KMg0KHQn9Cj0KHQmtCQCiAgICAgICAgIyAoQ09VTkNJTF9CWV9ERVNDRU5UX1Yx"
    "KTog0YHQv9GD0YHQuiDQvdCw0YjRkdC7INGC0L7Rh9C60YMgPSDQpNCQ0JrQoiwg0KHQvtCy0LXRggogICAgICAgICMg0YHQvtCx"
    "0LjRgNCw0LXRgtGB0Y8g0YHQsNC8LCB0MV9zdGF0dXMg4oCUINCz0L7Qu9C+0YEg0JjRgdC60YDRiywg0L3QtSDQt9Cw0LzQvtC6"
    "LiDQotC10L/QtdGA0YwKICAgICAgICAjINC60LDQsdC40L3QtdGCINGC0L7QttC1INC/0L4g0Y3RgtC+0LzRgyDQt9Cw0LrQvtC9"
    "0YMgKHN1bW1hcnlbImlkbGUiXSDQuNC3IHdha2VfY291bmNpbCkuCiAgICAgICAgIwogICAgICAgICMg0J/QntCi0J7Qmjog0LLQ"
    "tdGB0Ywg0L/RgNC+0LPQvtC9IOKAlCDQvtC00LjQvSBydW5faW5fZXhlY3V0b3IgKNGC0L7RgiDQttC1INC/0YDQuNGR0LwsCiAg"
    "ICAgICAgIyDRh9GC0L4g0YPQttC1INGA0LDQsdC+0YLQsNC10YIg0LIgcnVuX3Rlc3Rlcl9zZXNzaW9uL19vbl9wcm9ncmVzcyku"
    "INCa0L7Qu9Cx0Y3QugogICAgICAgICMgb25fZXZlbnQg0LzRg9GC0LjRgNGD0LXRgiBzdGF0ZSDQuCDQtNGR0YDQs9Cw0LXRgiB1"
    "cGRhdGVfKiDRgdC40L3RhdGA0L7QvdC90L4g4oCUCiAgICAgICAgIyDQv9GA0L7QstC10YDQtdC90L3Ri9C5INC/0LDRgtGC0LXR"
    "gNC9INGN0YLQvtCz0L4g0LrQsNCx0LjQvdC10YLQsCwg0L3QtSDQvdC+0LLRi9C5INGA0LjRgdC6LgogICAgICAgIGlmIHN0YXRl"
    "WyJydW5uaW5nIl06CiAgICAgICAgICAgIHVpLm5vdGlmeSgi0J/RgNC+0LPQvtC9INGD0LbQtSDQuNC00ZHRgi4uLiIsIHR5cGU9"
    "Indhcm5pbmciKQogICAgICAgICAgICByZXR1cm4KICAgICAgICBzdGF0ZVsicnVubmluZyJdID0gVHJ1ZQogICAgICAgIHVpLm5v"
    "dGlmeSgi8J+ToSDQn9C+0LTQvdC40LzQsNGOINC60L7QvdGC0YPRgCwg0LHRg9C20YMg0JjRgdC60YDRgy4uLiIsIHR5cGU9Imlu"
    "Zm8iKQoKICAgICAgICBpbXBvcnQgY291bmNpbAoKICAgICAgICBkZWYgX29uX2V2ZW50KGV2KToKICAgICAgICAgICAgZXR5cGUg"
    "PSBldi5nZXQoInR5cGUiKQoKICAgICAgICAgICAgaWYgZXR5cGUgPT0gImNvdW5jaWxfaWRsZSI6CiAgICAgICAgICAgICAgICAj"
    "INCh0L/Rg9GB0Log0L3QtSDQvdCw0YjRkdC7INGC0L7Rh9C60YMg4oCUINCY0YHQutGA0LAg0YPQttC1INC+0YLRgNCw0LHQvtGC"
    "0LDQu9CwICjQvdC40LbQtSksCiAgICAgICAgICAgICAgICAjINC00LDQu9GM0YjQtSDQvdC40LrQvtCz0L4g0L3QtSDQsdGD0LTQ"
    "uNC8LiDQpNC40L3QsNC70YzQvdGL0Lkgbm90aWZ5IOKAlCDQv9C+0YHQu9C1CiAgICAgICAgICAgICAgICAjIHdha2VfY291bmNp"
    "bCDQstC10YDQvdGR0YIgc3VtbWFyeS4KICAgICAgICAgICAgICAgIHJldHVybgoKICAgICAgICAgICAgaWYgZXR5cGUgIT0gImFn"
    "ZW50IjoKICAgICAgICAgICAgICAgIHJldHVybgoKICAgICAgICAgICAgYWlkID0gZXYuZ2V0KCJpZCIpCiAgICAgICAgICAgIHIg"
    "PSBldi5nZXQoInJlc3VsdCIsIHt9KSBvciB7fQogICAgICAgICAgICBuYXJyYXRpdmUgPSBldi5nZXQoIm5hcnJhdGl2ZSIsICIi"
    "KSBvciByLmdldCgicmF3IiwgIiIpCgogICAgICAgICAgICBfYXBwbHlfYWdlbnRfcmVzdWx0KGFpZCwgciwgbmFycmF0aXZlKQoK"
    "CiAgICAgICAgdHJ5OgogICAgICAgICAgICBzdW1tYXJ5ID0gYXdhaXQgYXN5bmNpby5nZXRfZXZlbnRfbG9vcCgpLnJ1bl9pbl9l"
    "eGVjdXRvcigKICAgICAgICAgICAgICAgIE5vbmUsIGxhbWJkYTogY291bmNpbC53YWtlX2NvdW5jaWwoIlhBVVVTRCIsICJINCIs"
    "IG9uX2V2ZW50PV9vbl9ldmVudCkpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICBzdGF0ZVsicnVu"
    "bmluZyJdID0gRmFsc2UKICAgICAgICAgICAgdWkubm90aWZ5KGYi0KHQsdC+0Lkg0L/RgNC+0LPQvtC90LA6IHtlfSIsIHR5cGU9"
    "Im5lZ2F0aXZlIikKICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgc3RhdGVbInJ1bm5pbmciXSA9IEZhbHNlCgogICAgICAgIGlm"
    "IHN1bW1hcnkuZ2V0KCJpZGxlIik6CiAgICAgICAgICAgIHVpLm5vdGlmeSgi8J+ToyDQodC/0YPRgdC6INC90LUg0L3QsNGI0ZHQ"
    "uyDRgtC+0YfQutGDIOKAlCDQodC+0LLQtdGCINC90LUg0YHQvtCx0LjRgNCw0LXRgtGB0Y8iLCB0eXBlPSJpbmZvIikKCiAgICBk"
    "ZWYgdXBkYXRlX2F2YXRhcl9zdGF0ZXMoKToKICAgICAgICBmb3IgYWlkLCBlbCBpbiBhdmF0YXJzX3JlZlsiZWxlbWVudHMiXS5p"
    "dGVtcygpOgogICAgICAgICAgICByb3cgPSBfYWdlbnRfcm93KHJvc3RlciwgYWlkKQogICAgICAgICAgICBiYXNlID0gImF2YXRh"
    "ciB2YWNhbnQiIGlmIChyb3cgYW5kIG5vdCByb3dbInJlc2lkZW50Il0pIGVsc2UgImF2YXRhciIKICAgICAgICAgICAgZWwuY2xh"
    "c3NlcyhyZXBsYWNlPWJhc2UpCiAgICAgICAgICAgIGlmIGFpZCA9PSBzdGF0ZVsiYWN0aXZlX2FnZW50Il06CiAgICAgICAgICAg"
    "ICAgICBlbC5jbGFzc2VzKGFkZD0iYWN0aXZlIikKICAgICAgICAgICAgaWYgYWlkIGluIHN0YXRlWyJyZXBvcnRzIl06CiAgICAg"
    "ICAgICAgICAgICBlbC5jbGFzc2VzKGFkZD0iZG9uZSIpCgogICAgZGVmIHN3aXRjaF9hZ2VudChhZ2VudF9pZDogc3RyKToKICAg"
    "ICAgICByb3cgPSBfYWdlbnRfcm93KHJvc3RlciwgYWdlbnRfaWQpCiAgICAgICAgaWYgcm93IGFuZCBub3Qgcm93WyJyZXNpZGVu"
    "dCJdOgogICAgICAgICAgICB1aS5ub3RpZnkoItCS0LDQutCw0L3RgdC40Y8g4oCUINGB0Y7QtNCwINC10YnRkSDQvdC40LrQvtCz"
    "0L4g0L3QtSDQvdCw0L3Rj9C70LgiLCB0eXBlPSJ3YXJuaW5nIikKICAgICAgICBzdGF0ZVsiYWN0aXZlX2FnZW50Il0gPSBhZ2Vu"
    "dF9pZAogICAgICAgIHVwZGF0ZV9hdmF0YXIoKQogICAgICAgIHVwZGF0ZV92aXRhbHMoKQogICAgICAgIHVwZGF0ZV9hdmF0YXJf"
    "c3RhdGVzKCkKICAgICAgICB1cGRhdGVfc3RhdHNfcGFuZWwoKQogICAgICAgIGxhYmVsID0gX2FnZW50X2xhYmVsKHJvc3Rlciwg"
    "YWdlbnRfaWQpCiAgICAgICAgaWYgYWdlbnRfaWQgaW4gc3RhdGVbInJlcG9ydHMiXToKICAgICAgICAgICAgdXBkYXRlX3ZpZXdl"
    "cihmIiMge2xhYmVsfSAoe2FnZW50X2lkfSlcblxue3N0YXRlWydyZXBvcnRzJ11bYWdlbnRfaWRdfSIpCiAgICAgICAgZWxzZToK"
    "ICAgICAgICAgICAgdXBkYXRlX3ZpZXdlcihmIiMge2xhYmVsfSAoe2FnZW50X2lkfSlcblxuKtCe0YLRh9GR0YIg0L/QvtC60LAg"
    "0L3QtSDRgdC+0LfQtNCw0L0uKiIpCgogICAgIyDilIDilIAg0LfQsNCz0YDRg9C30YfQuNC6ICjQu9C10LLQsNGPINC60L7Qu9C+"
    "0L3QutCwKSDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi"
    "lIDilIDilIDilIDilIDilIAKICAgIGRlZiBzZXRfYWN0aXZlKGkpOgogICAgICAgIGFzc2V0cyA9IHN0YXRlLmdldCgibG9hZGVk"
    "X2Fzc2V0cyIsIFtdKQogICAgICAgIGlmIDAgPD0gaSA8IGxlbihhc3NldHMpOgogICAgICAgICAgICBzdGF0ZVsiYWN0aXZlX2Fz"
    "c2V0Il0gPSBpCiAgICAgICAgICAgIHVwZGF0ZV9maWxlc19kaXNwbGF5KCkKICAgICAgICAgICAgYSA9IGFzc2V0c1tpXQogICAg"
    "ICAgICAgICB1aS5ub3RpZnkoZiLQkNC60YLQuNCy0LXQvToge2FbJ3N5bWJvbCddfSB7YVsndGltZWZyYW1lJ119IiwgdHlwZT0i"
    "aW5mbyIpCgogICAgZGVmIHVwZGF0ZV9maWxlc19kaXNwbGF5KCk6CiAgICAgICAgaWYgbm90IGZpbGVzX3JlZlsiZWxlbWVudCJd"
    "OgogICAgICAgICAgICByZXR1cm4KICAgICAgICBmaWxlc19yZWZbImVsZW1lbnQiXS5jbGVhcigpCiAgICAgICAgd2l0aCBmaWxl"
    "c19yZWZbImVsZW1lbnQiXToKICAgICAgICAgICAgYXNzZXRzID0gc3RhdGUuZ2V0KCJsb2FkZWRfYXNzZXRzIiwgW10pCiAgICAg"
    "ICAgICAgIGlmIG5vdCBhc3NldHM6CiAgICAgICAgICAgICAgICB1aS5sYWJlbCgi0J3QtdGCINCw0LrRgtC40LLQvtCyIikuc3R5"
    "bGUoImNvbG9yOiByZ2JhKDI1NSwyNTUsMjU1LDAuNCk7IGZvbnQtc2l6ZToxMXB4OyIpCiAgICAgICAgICAgIGVsc2U6CiAgICAg"
    "ICAgICAgICAgICBhY3RpdmUgPSBzdGF0ZS5nZXQoImFjdGl2ZV9hc3NldCIpCiAgICAgICAgICAgICAgICBmb3IgaSwgYSBpbiBl"
    "bnVtZXJhdGUoYXNzZXRzKToKICAgICAgICAgICAgICAgICAgICBpc19hY3RpdmUgPSAoaSA9PSBhY3RpdmUpCiAgICAgICAgICAg"
    "ICAgICAgICAgcm93ID0gdWkuZWxlbWVudCgiZGl2Iikuc3R5bGUoCiAgICAgICAgICAgICAgICAgICAgICAgICJwYWRkaW5nOjdw"
    "eCAxMHB4OyBtYXJnaW46M3B4IDA7IGJvcmRlci1yYWRpdXM6N3B4OyBjdXJzb3I6cG9pbnRlcjsgIgogICAgICAgICAgICAgICAg"
    "ICAgICAgICAiZm9udC1mYW1pbHk6J0pldEJyYWlucyBNb25vJyxtb25vc3BhY2U7ICIKICAgICAgICAgICAgICAgICAgICAgICAg"
    "KyAoImJhY2tncm91bmQ6cmdiYSgwLDI1NSwxMzYsMC4xMCk7IGJvcmRlcjoxcHggc29saWQgcmdiYSgwLDI1NSwxMzYsMC40NSk7"
    "IgogICAgICAgICAgICAgICAgICAgICAgICAgICBpZiBpc19hY3RpdmUgZWxzZQogICAgICAgICAgICAgICAgICAgICAgICAgICAi"
    "YmFja2dyb3VuZDpyZ2JhKDI1NSwyNTUsMjU1LDAuMDIpOyBib3JkZXI6MXB4IHNvbGlkIHJnYmEoMjU1LDI1NSwyNTUsMC4wNyk7"
    "IikpCiAgICAgICAgICAgICAgICAgICAgcm93Lm9uKCJjbGljayIsIGxhbWJkYSBfLCBpZHg9aTogc2V0X2FjdGl2ZShpZHgpKQog"
    "ICAgICAgICAgICAgICAgICAgIHdpdGggcm93OgogICAgICAgICAgICAgICAgICAgICAgICB1aS5odG1sKAogICAgICAgICAgICAg"
    "ICAgICAgICAgICAgICAgZicnJzxkaXYgc3R5bGU9ImRpc3BsYXk6ZmxleDtqdXN0aWZ5LWNvbnRlbnQ6c3BhY2UtYmV0d2Vlbjth"
    "bGlnbi1pdGVtczpjZW50ZXI7Ij4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPHNwYW4gc3R5bGU9ImNvbG9yOnsnIzAw"
    "ZmY4OCcgaWYgaXNfYWN0aXZlIGVsc2UgJ3JnYmEoMjU1LDI1NSwyNTUsMC44NSknfTsKICAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICAgICAgICAgICAgICAgIGZvbnQtc2l6ZToxMnB4O2ZvbnQtd2VpZ2h0OjcwMDsiPnthWyJzeW1ib2wiXX08L3NwYW4+CiAg"
    "ICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxzcGFuIHN0eWxlPSJjb2xvcjpyZ2JhKDAsMjA0LDI1NSwwLjkpO2ZvbnQtc2l6"
    "ZToxMXB4O2ZvbnQtd2VpZ2h0OjcwMDsiPnthWyJ0aW1lZnJhbWUiXX08L3NwYW4+CiAgICAgICAgICAgICAgICAgICAgICAgICAg"
    "ICA8L2Rpdj4KICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxkaXYgc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwyNTUsMC41"
    "KTtmb250LXNpemU6OXB4O21hcmdpbi10b3A6MnB4OyI+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHthWyJkYXRlX2Zy"
    "b20iXX0g4oaSIHthWyJkYXRlX3RvIl19IMK3IHthWyJiYXJzIl19CiAgICAgICAgICAgICAgICAgICAgICAgICAgICA8L2Rpdj4n"
    "JycpCgogICAgX0hJU1RPUllfVEZTID0gWyJNTjEiLCAiVzEiLCAiRDEiLCAiSDEyIiwgIkg4IiwgIkg0IiwgIkgxIiwKICAgICAg"
    "ICAgICAgICAgICAgICAiTTMwIiwgIk0xNSIsICJNMTAiLCAiTTUiLCAiTTEiXQogICAgX1dPUkRfVEZTID0geyJNT05USExZIjog"
    "Ik1OMSIsICJXRUVLTFkiOiAiVzEiLCAiREFJTFkiOiAiRDEiLCAiSE9VUkxZIjogIkgxIn0KCiAgICBkZWYgX3BhcnNlX3N5bWJv"
    "bF90ZihmaWxlbmFtZTogc3RyKToKICAgICAgICBzdGVtID0gZmlsZW5hbWUucnNwbGl0KCIuIiwgMSlbMF0udXBwZXIoKS5zdHJp"
    "cCgpCiAgICAgICAgZm9yIHdvcmQsIHRmIGluIHNvcnRlZChfV09SRF9URlMuaXRlbXMoKSwga2V5PWxhbWJkYSB4OiAtbGVuKHhb"
    "MF0pKToKICAgICAgICAgICAgaWYgc3RlbS5lbmRzd2l0aCh3b3JkKToKICAgICAgICAgICAgICAgIHJldHVybiBzdGVtWzotbGVu"
    "KHdvcmQpXS5yc3RyaXAoIl8tICIpLCB0ZgogICAgICAgIGZvciB0ZiBpbiBzb3J0ZWQoX0hJU1RPUllfVEZTLCBrZXk9bGVuLCBy"
    "ZXZlcnNlPVRydWUpOgogICAgICAgICAgICBpZiBzdGVtLmVuZHN3aXRoKHRmKToKICAgICAgICAgICAgICAgIHJldHVybiBzdGVt"
    "WzotbGVuKHRmKV0ucnN0cmlwKCJfLSAiKSwgdGYKICAgICAgICByZXR1cm4gc3RlbSwgIj8iCgogICAgX1RFU1RfREFUQV9ESVIg"
    "PSBfSEVSRSAvICJ0ZXN0X2RhdGEiCgogICAgZGVmIF9wYXNzcG9ydF9mcm9tX2NzdihwYXRoKToKICAgICAgICBmcm9tIHdpbGxp"
    "YW1zX2NvcmUgaW1wb3J0IHJlYWRfbXQ1X2NzdgogICAgICAgIHAgPSBQYXRoKHBhdGgpCiAgICAgICAgYmFycyA9IHJlYWRfbXQ1"
    "X2NzdihzdHIocCkpCiAgICAgICAgaWYgbm90IGJhcnM6CiAgICAgICAgICAgIHJldHVybiBOb25lCiAgICAgICAgc3ltYm9sLCB0"
    "ZiA9IF9wYXJzZV9zeW1ib2xfdGYocC5uYW1lKQogICAgICAgIHJldHVybiB7CiAgICAgICAgICAgICJuYW1lIjogcC5uYW1lLCAi"
    "cGF0aCI6IHN0cihwKSwgInN5bWJvbCI6IHN5bWJvbCwgInRpbWVmcmFtZSI6IHRmLAogICAgICAgICAgICAiYmFycyI6IGxlbihi"
    "YXJzKSwgImRhdGVfZnJvbSI6IGJhcnNbMF0uZ2V0KCJkYXRlIiwgIj8iKSwgImRhdGVfdG8iOiBiYXJzWy0xXS5nZXQoImRhdGUi"
    "LCAiPyIpLAogICAgICAgIH0KCiAgICBkZWYgX3NjYW5fdGVzdF9kYXRhKCk6CiAgICAgICAgYXNzZXRzID0gW10KICAgICAgICB0"
    "cnk6CiAgICAgICAgICAgIGlmIF9URVNUX0RBVEFfRElSLmV4aXN0cygpOgogICAgICAgICAgICAgICAgZm9yIGYgaW4gc29ydGVk"
    "KF9URVNUX0RBVEFfRElSLmdsb2IoIiouY3N2IikpOgogICAgICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAg"
    "ICAgICAgcHAgPSBfcGFzc3BvcnRfZnJvbV9jc3YoZikKICAgICAgICAgICAgICAgICAgICAgICAgaWYgcHA6CiAgICAgICAgICAg"
    "ICAgICAgICAgICAgICAgICBhc3NldHMuYXBwZW5kKHBwKQogICAgICAgICAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMg"
    "X2U6CiAgICAgICAgICAgICAgICAgICAgICAgIHByaW50KGYiW1RPUkfCt1NDQU5dIHtmLm5hbWV9OiB7X2V9IikKICAgICAgICBl"
    "eGNlcHQgRXhjZXB0aW9uIGFzIF9lOgogICAgICAgICAgICBwcmludChmIltUT1JHwrdTQ0FOXSDQv9Cw0L/QutCwOiB7X2V9IikK"
    "ICAgICAgICBzdGF0ZVsibG9hZGVkX2Fzc2V0cyJdID0gYXNzZXRzCiAgICAgICAgc3RhdGVbImFjdGl2ZV9hc3NldCJdID0gMCBp"
    "ZiBhc3NldHMgZWxzZSBOb25lCgogICAgYXN5bmMgZGVmIGhhbmRsZV91cGxvYWQoZSk6CiAgICAgICAgbmFtZSA9IGUubmFtZQog"
    "ICAgICAgIHRyeToKICAgICAgICAgICAgY29udGVudCA9IGUuY29udGVudC5yZWFkKCkgaWYgaGFzYXR0cihlLmNvbnRlbnQsICJy"
    "ZWFkIikgZWxzZSBlLmNvbnRlbnQKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIF9jZToKICAgICAgICAgICAgdWkubm90aWZ5"
    "KGYi0J3QtSDQv9GA0L7Rh9C40YLQsNGC0Ywg0YTQsNC50Ls6IHtfY2V9IiwgdHlwZT0ibmVnYXRpdmUiKQogICAgICAgICAgICBy"
    "ZXR1cm4KICAgICAgICBpZiBub3QgbmFtZS5sb3dlcigpLmVuZHN3aXRoKCIuY3N2Iik6CiAgICAgICAgICAgIHVpLm5vdGlmeSgi"
    "0J3Rg9C20LXQvSBDU1Yg0Y3QutGB0L/QvtGA0YLQsCBNVDUiLCB0eXBlPSJ3YXJuaW5nIikKICAgICAgICAgICAgcmV0dXJuCiAg"
    "ICAgICAgZGVzdF9kaXIgPSBfVEVTVF9EQVRBX0RJUgogICAgICAgIGRlc3RfZGlyLm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhpc3Rf"
    "b2s9VHJ1ZSkKICAgICAgICBkZXN0ID0gZGVzdF9kaXIgLyBuYW1lCiAgICAgICAgdHJ5OgogICAgICAgICAgICBkZXN0LndyaXRl"
    "X2J5dGVzKGNvbnRlbnQpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBfd2U6CiAgICAgICAgICAgIHVpLm5vdGlmeShmItCd"
    "0LUg0YHQvtGF0YDQsNC90LjRgtGMINGE0LDQudC7OiB7X3dlfSIsIHR5cGU9Im5lZ2F0aXZlIikKICAgICAgICAgICAgcmV0dXJu"
    "CiAgICAgICAgdHJ5OgogICAgICAgICAgICBmcm9tIHdpbGxpYW1zX2NvcmUgaW1wb3J0IHJlYWRfbXQ1X2NzdgogICAgICAgICAg"
    "ICBiYXJzID0gcmVhZF9tdDVfY3N2KHN0cihkZXN0KSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIF9yZToKICAgICAgICAg"
    "ICAgdWkubm90aWZ5KGYi0K/QtNGA0L4g0L3QtSDQv9GA0L7Rh9C70L4gQ1NWOiB7X3JlfSIsIHR5cGU9Im5lZ2F0aXZlIikKICAg"
    "ICAgICAgICAgcmV0dXJuCiAgICAgICAgaWYgbm90IGJhcnM6CiAgICAgICAgICAgIHVpLm5vdGlmeShmIntuYW1lfTog0L/Rg9GB"
    "0YLQviDQuNC70Lgg0L3QtSDRhNC+0YDQvNCw0YIgTVQ1IiwgdHlwZT0id2FybmluZyIpCiAgICAgICAgICAgIHJldHVybgogICAg"
    "ICAgIHN5bWJvbCwgdGYgPSBfcGFyc2Vfc3ltYm9sX3RmKG5hbWUpCiAgICAgICAgcGFzc3BvcnQgPSB7CiAgICAgICAgICAgICJu"
    "YW1lIjogbmFtZSwgInBhdGgiOiBzdHIoZGVzdCksICJzeW1ib2wiOiBzeW1ib2wsICJ0aW1lZnJhbWUiOiB0ZiwKICAgICAgICAg"
    "ICAgImJhcnMiOiBsZW4oYmFycyksICJkYXRlX2Zyb20iOiBiYXJzWzBdLmdldCgiZGF0ZSIsICI/IiksICJkYXRlX3RvIjogYmFy"
    "c1stMV0uZ2V0KCJkYXRlIiwgIj8iKSwKICAgICAgICB9CiAgICAgICAgYXNzZXRzID0gc3RhdGUuc2V0ZGVmYXVsdCgibG9hZGVk"
    "X2Fzc2V0cyIsIFtdKQogICAgICAgIGV4aXN0aW5nID0gbmV4dCgoayBmb3IgaywgeCBpbiBlbnVtZXJhdGUoYXNzZXRzKSBpZiB4"
    "LmdldCgicGF0aCIpID09IHBhc3Nwb3J0WyJwYXRoIl0pLCBOb25lKQogICAgICAgIGlmIGV4aXN0aW5nIGlzIG5vdCBOb25lOgog"
    "ICAgICAgICAgICBhc3NldHNbZXhpc3RpbmddID0gcGFzc3BvcnQKICAgICAgICAgICAgc3RhdGVbImFjdGl2ZV9hc3NldCJdID0g"
    "ZXhpc3RpbmcKICAgICAgICBlbHNlOgogICAgICAgICAgICBhc3NldHMuYXBwZW5kKHBhc3Nwb3J0KQogICAgICAgICAgICBzdGF0"
    "ZVsiYWN0aXZlX2Fzc2V0Il0gPSBsZW4oYXNzZXRzKSAtIDEKICAgICAgICB1cGRhdGVfZmlsZXNfZGlzcGxheSgpCiAgICAgICAg"
    "dWkubm90aWZ5KGYi4pqhINCX0LDRgNGP0LbQtdC90L46IHtzeW1ib2x9IHt0Zn0gwrcge2xlbihiYXJzKX0g0LHQsNGA0L7QsiIs"
    "IHR5cGU9InBvc2l0aXZlIikKICAgICAgICBfdXAgPSBmaWxlc19yZWYuZ2V0KCJ1cGxvYWRlciIpCiAgICAgICAgaWYgX3VwOgog"
    "ICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBfdXAucmVzZXQoKQogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgog"
    "ICAgICAgICAgICAgICAgcGFzcwoKICAgIGRlZiBjbGVhcl9maWxlcygpOgogICAgICAgIHN0YXRlWyJ1cGxvYWRlZF9maWxlcyJd"
    "ID0gW10KICAgICAgICBzdGF0ZVsibG9hZGVkX2Fzc2V0cyJdID0gW10KICAgICAgICBzdGF0ZVsiYWN0aXZlX2Fzc2V0Il0gPSBO"
    "b25lCiAgICAgICAgdXBkYXRlX2ZpbGVzX2Rpc3BsYXkoKQogICAgICAgIHVpLm5vdGlmeSgi0J7Rh9C40YnQtdC90L4iLCB0eXBl"
    "PSJpbmZvIikKCiAgICAjIOKUgOKUgCDRh9Cw0YIg0YEg0LDQutGC0LjQstC90YvQvCDQsNCz0LXQvdGC0L7QvCDilIDilIDilIDi"
    "lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi"
    "lIDilIDilIAKICAgIGFzeW5jIGRlZiBzZW5kX21lc3NhZ2UoKToKICAgICAgICBpZiBub3QgaW5wdXRfcmVmWyJlbGVtZW50Il06"
    "CiAgICAgICAgICAgIHJldHVybgogICAgICAgIG1zZyA9IGlucHV0X3JlZlsiZWxlbWVudCJdLnZhbHVlLnN0cmlwKCkKICAgICAg"
    "ICBpZiBub3QgbXNnOgogICAgICAgICAgICByZXR1cm4KICAgICAgICBpbnB1dF9yZWZbImVsZW1lbnQiXS52YWx1ZSA9ICIiCiAg"
    "ICAgICAgc3RhdGVbImNoYXRfaGlzdG9yeSJdLmFwcGVuZCh7InJvbGUiOiAidXNlciIsICJjb250ZW50IjogbXNnfSkKICAgICAg"
    "ICB1cGRhdGVfY2hhdF9kaXNwbGF5KCkKCiAgICAgICAgYWdlbnRfaWQgPSBzdGF0ZVsiYWN0aXZlX2FnZW50Il0KICAgICAgICBy"
    "b3cgPSBfYWdlbnRfcm93KHJvc3RlciwgYWdlbnRfaWQpCiAgICAgICAgaWYgcm93IGFuZCBub3Qgcm93WyJyZXNpZGVudCJdOgog"
    "ICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0uYXBwZW5kKHsKICAgICAgICAgICAgICAgICJyb2xlIjogImFzc2lzdGFu"
    "dCIsICJhZ2VudCI6IGFnZW50X2lkLAogICAgICAgICAgICAgICAgImNvbnRlbnQiOiAi0LfQtNC10YHRjCDQstCw0LrQsNC90YHQ"
    "uNGPIOKAlCDQv9GA0L7Qv9C40YHQsNGC0Ywg0YDQtdC30LjQtNC10L3RgtCwINC90LAg0Y3RgtC+0YIg0YHQu9C+0YIg0LzQvtC2"
    "0L3QviDQsiDQutCw0LHQuNC90LXRgtC1INCR0YDQsNGC0LAuIn0pCiAgICAgICAgICAgIHVwZGF0ZV9jaGF0X2Rpc3BsYXkoKQog"
    "ICAgICAgICAgICByZXR1cm4KCiAgICAgICAgX2NoYXRfbWFwID0gewogICAgICAgICAgICAiQTAyIjogKCLRgtC+0YDQs9C+0LLR"
    "i9C5X9GF0LDQvtGBIiwgIkEwMiIsICJjaGF0X3dpdGhfbW9yaiIsICJtb3JqX2xhc3RfcnVuIiwgIvCfpq0iKSwKICAgICAgICAg"
    "ICAgIkEwMyI6ICgi0YLQvtGA0LPQvtCy0YvQuV/RhdCw0L7RgSIsICJBMDMiLCAiY2hhdF93aXRoX3BhbmlreW9yIiwgInBhbmlj"
    "X2xhc3RfcnVuIiwgIvCfmLEiKSwKICAgICAgICAgICAgIkEwNCI6ICgi0YLQvtGA0LPQvtCy0YvQuV/RhdCw0L7RgSIsICJBMDQi"
    "LCAiY2hhdF93aXRoX2hhbnMiLCAiaGFuc19sYXN0X3J1biIsICLwn46vIiksCiAgICAgICAgICAgICJBMDUiOiAoItC60L7QvdGC"
    "0L7RgNCwIiwgItCw0YDRhdC40LLQsNGA0LjRg9GBIiwgImNoYXRfd2l0aF9hcmtoaXYiLCAiYXJraGl2X2xhc3RfcnVuIiwgIvCf"
    "k5oiKSwKICAgICAgICAgICAgIkEwNiI6ICgi0YLQvtGA0LPQvtCy0YvQuV/RhdCw0L7RgSIsICJBMDYiLCAiY2hhdF93aXRoX2Jy"
    "dXQiLCAiYnJ1dF9sYXN0X3J1biIsICLwn6qoIiksCiAgICAgICAgICAgICJBMDciOiAoItGC0L7RgNCz0L7QstGL0Llf0YXQsNC+"
    "0YEiLCAiQTA3IiwgImNoYXRfd2l0aF9hdmFuIiwgImF2YW5fbGFzdF9ydW4iLCAi8J+OsiIpLAogICAgICAgICAgICAiQTA4Ijog"
    "KCLRgtC+0YDQs9C+0LLRi9C5X9GF0LDQvtGBIiwgIkEwOCIsICJjaGF0X3dpdGhfY29ucyIsICJjb25zX2xhc3RfcnVuIiwgIuKa"
    "lu+4jyIpLAogICAgICAgICAgICAiQTA5IjogKCLQutC+0L3RgtC+0YDQsCIsICLQuNGB0L/QvtC70L3QuNGC0LXQu9GMIiwgImNo"
    "YXRfd2l0aF9leGVjdXRvciIsICJleGVjdXRvcl9sYXN0X3J1biIsICLwn46sIiksCiAgICAgICAgfQogICAgICAgIGxhYmVsID0g"
    "X2FnZW50X2xhYmVsKHJvc3RlciwgYWdlbnRfaWQpCgogICAgICAgIGlmIGFnZW50X2lkIGluIF9jaGF0X21hcDoKICAgICAgICAg"
    "ICAgX2NlaF9pZCwgX3Nsb3QsIF9mbl9uYW1lLCBfbGFzdF9rZXksIF9pYyA9IF9jaGF0X21hcFthZ2VudF9pZF0KICAgICAgICAg"
    "ICAgdWkubm90aWZ5KGYie19pY30ge2xhYmVsfSDQtNGD0LzQsNC10YIuLi4iLCB0eXBlPSJpbmZvIikKICAgICAgICAgICAgdHJ5"
    "OgogICAgICAgICAgICAgICAgX2JyYWluID0gX3Nsb3RfYnJhaW4oX2NlaF9pZCwgX3Nsb3QpCiAgICAgICAgICAgICAgICBpZiBf"
    "YnJhaW4gaXMgTm9uZToKICAgICAgICAgICAgICAgICAgICByYWlzZSBSdW50aW1lRXJyb3IoZiLQvNC+0LfQsyB7X3Nsb3R9INC1"
    "0YnRkSDQvdC1INCyINGB0LvQvtGC0LUiKQogICAgICAgICAgICAgICAgX2NoYXQgPSBnZXRhdHRyKF9icmFpbiwgX2ZuX25hbWUp"
    "CiAgICAgICAgICAgICAgICBkaWFsb2cgPSBbbSBmb3IgbSBpbiBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0KICAgICAgICAgICAgICAg"
    "ICAgICAgICAgICBpZiBtLmdldCgicm9sZSIpIGluICgidXNlciIsICJhc3Npc3RhbnQiKSBhbmQgbS5nZXQoImNvbnRlbnQiKV0K"
    "ICAgICAgICAgICAgICAgIHJlcGx5ID0gYXdhaXQgYXN5bmNpby5nZXRfZXZlbnRfbG9vcCgpLnJ1bl9pbl9leGVjdXRvcigKICAg"
    "ICAgICAgICAgICAgICAgICBOb25lLCBsYW1iZGE6IF9jaGF0KG1zZywgc3RhdGUuZ2V0KF9sYXN0X2tleSksIGRpYWxvZykpCiAg"
    "ICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgICAgIHJlcGx5ID0gZiLimqDvuI8ge2xhYmVsfSDQ"
    "vdC1INGB0LzQvtCzKNC70LApINC+0YLQstC10YLQuNGC0Yw6IHtlfSIKICAgICAgICAgICAgc3RhdGVbImNoYXRfaGlzdG9yeSJd"
    "LmFwcGVuZCh7InJvbGUiOiAiYXNzaXN0YW50IiwgImFnZW50IjogYWdlbnRfaWQsICJjb250ZW50IjogcmVwbHl9KQogICAgICAg"
    "ICAgICB1cGRhdGVfY2hhdF9kaXNwbGF5KCkKICAgICAgICAgICAgcmV0dXJuCgogICAgICAgIGlmIGFnZW50X2lkICE9ICJBMDEi"
    "OgogICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0uYXBwZW5kKHsKICAgICAgICAgICAgICAgICJyb2xlIjogImFzc2lz"
    "dGFudCIsICJhZ2VudCI6IGFnZW50X2lkLAogICAgICAgICAgICAgICAgImNvbnRlbnQiOiBmIntsYWJlbH0g0LXRidGRINC90LUg"
    "0L/QvtC00LrQu9GO0YfRkdC9KNCwKSDQuiDQttC40LLQvtC80YMg0YDQsNC30LPQvtCy0L7RgNGDLiJ9KQogICAgICAgICAgICB1"
    "cGRhdGVfY2hhdF9kaXNwbGF5KCkKICAgICAgICAgICAgcmV0dXJuCgogICAgICAgIHVpLm5vdGlmeSgi4py077iPINCY0YHQutGA"
    "0LAg0LTRg9C80LDQtdGCLi4uIiwgdHlwZT0iaW5mbyIpCiAgICAgICAgdHJ5OgogICAgICAgICAgICBfYnJhaW4gPSBfc2xvdF9i"
    "cmFpbigi0YLQvtGA0LPQvtCy0YvQuV/RhdCw0L7RgSIsICJBMDEiKQogICAgICAgICAgICBpZiBfYnJhaW4gaXMgTm9uZToKICAg"
    "ICAgICAgICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcigi0LzQvtC30LMgQTAxINC10YnRkSDQvdC1INCyINGB0LvQvtGC0LUiKQog"
    "ICAgICAgICAgICBkaWFsb2cgPSBbbSBmb3IgbSBpbiBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0KICAgICAgICAgICAgICAgICAgICAg"
    "IGlmIG0uZ2V0KCJyb2xlIikgaW4gKCJ1c2VyIiwgImFzc2lzdGFudCIpIGFuZCBtLmdldCgiY29udGVudCIpXQogICAgICAgICAg"
    "ICByZXBseSA9IGF3YWl0IGFzeW5jaW8uZ2V0X2V2ZW50X2xvb3AoKS5ydW5faW5fZXhlY3V0b3IoCiAgICAgICAgICAgICAgICBO"
    "b25lLCBsYW1iZGE6IF9icmFpbi5jaGF0X3dpdGhfaXNrcmEobXNnLCBzdGF0ZS5nZXQoImlza3JhX2xhc3RfcnVuIiksIGRpYWxv"
    "ZykpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICBzdGF0ZVsiY2hhdF9oaXN0b3J5Il0uYXBwZW5k"
    "KHsKICAgICAgICAgICAgICAgICJyb2xlIjogImFzc2lzdGFudCIsICJhZ2VudCI6ICJBMDEiLCAiY29udGVudCI6IGYi4pqg77iP"
    "INCd0LUg0YHQvNC+0LPQu9CwINC+0YLQstC10YLQuNGC0Yw6IHtlfSJ9KQogICAgICAgICAgICB1cGRhdGVfY2hhdF9kaXNwbGF5"
    "KCkKICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgc3RhdGVbImNoYXRfaGlzdG9yeSJdLmFwcGVuZCh7InJvbGUiOiAiYXNzaXN0"
    "YW50IiwgImFnZW50IjogIkEwMSIsICJjb250ZW50IjogcmVwbHl9KQogICAgICAgIHVwZGF0ZV9jaGF0X2Rpc3BsYXkoKQoKICAg"
    "ICMg4pWQ4pWQ4pWQIExBWU9VVCDigJQg0YLQsCDQttC1INC60LDQu9GM0LrQsCwg0YfRgtC+INCx0YvQu9CwINCyIC0yL3N0dWRp"
    "by9lY29ub215L3VpX2V4Y2hhbmdlLnB5IOKVkOKVkOKVkAogICAgd2l0aCB1aS5lbGVtZW50KCJkaXYiKS5jbGFzc2VzKCJhcHAt"
    "Y29udGFpbmVyIik6CgogICAgICAgIHdpdGggdWkuZWxlbWVudCgiZGl2IikuY2xhc3NlcygiYXJlYS1oZWFkZXIiKToKICAgICAg"
    "ICAgICAgd2l0aCB1aS5lbGVtZW50KCJkaXYiKS5jbGFzc2VzKCJnbGFzcyBzcXVhZC1kZWNrIikuc3R5bGUoCiAgICAgICAgICAg"
    "ICAgICAiZGlzcGxheTpmbGV4OyBhbGlnbi1pdGVtczpjZW50ZXI7IHdpZHRoOjEwMCU7IGdhcDo4cHg7IHBhZGRpbmc6MCA4cHg7"
    "IHBvc2l0aW9uOnJlbGF0aXZlOyIKICAgICAgICAgICAgKToKICAgICAgICAgICAgICAgIHdpdGggdWkuZWxlbWVudCgiZGl2Iiku"
    "c3R5bGUoCiAgICAgICAgICAgICAgICAgICAgImRpc3BsYXk6ZmxleDsgYWxpZ24taXRlbXM6Y2VudGVyOyBnYXA6NnB4OyBmbGV4"
    "LXdyYXA6d3JhcDsganVzdGlmeS1jb250ZW50OmNlbnRlcjsgZmxleDoxOyIKICAgICAgICAgICAgICAgICk6CiAgICAgICAgICAg"
    "ICAgICAgICAgZm9yIHIgaW4gcm9zdGVyOgogICAgICAgICAgICAgICAgICAgICAgICBvbGRfaWQgPSByWyJvbGRfaWQiXQogICAg"
    "ICAgICAgICAgICAgICAgICAgICBvY2N1cGllZCA9IGJvb2woclsicmVzaWRlbnQiXSkKICAgICAgICAgICAgICAgICAgICAgICAg"
    "Y2xzID0gZidhdmF0YXIgeyJhY3RpdmUiIGlmIG9sZF9pZCA9PSAiQTAxIiBlbHNlICIifSB7IiIgaWYgb2NjdXBpZWQgZWxzZSAi"
    "dmFjYW50In0nCiAgICAgICAgICAgICAgICAgICAgICAgIGF2YXRhciA9IHVpLmVsZW1lbnQoImRpdiIpLmNsYXNzZXMoY2xzKQog"
    "ICAgICAgICAgICAgICAgICAgICAgICBzdHlsZSA9ICIiCiAgICAgICAgICAgICAgICAgICAgICAgIGlmIG9jY3VwaWVkOgogICAg"
    "ICAgICAgICAgICAgICAgICAgICAgICAgYXYgPSBfYXZhdGFyX3VybF9mb3IoclsicmVzaWRlbnQiXVsi0L/QsNC/0LrQsCJdLCBz"
    "dGF0aWNfcHJlZml4KQogICAgICAgICAgICAgICAgICAgICAgICAgICAgaWYgYXY6CiAgICAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICAgc3R5bGUgPSBmImJhY2tncm91bmQtaW1hZ2U6dXJsKCd7YXZ9Jyk7IgogICAgICAgICAgICAgICAgICAgICAgICBhdmF0"
    "YXIuc3R5bGUoc3R5bGUpCiAgICAgICAgICAgICAgICAgICAgICAgIGF2YXRhci5vbigiY2xpY2siLCBsYW1iZGEgZSwgdz1vbGRf"
    "aWQ6IHN3aXRjaF9hZ2VudCh3KSkKICAgICAgICAgICAgICAgICAgICAgICAgd2l0aCBhdmF0YXI6CiAgICAgICAgICAgICAgICAg"
    "ICAgICAgICAgICBpZiBub3Qgb2NjdXBpZWQ6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgdWkubGFiZWwob2xkX2lk"
    "KS5zdHlsZSgiZm9udC1zaXplOiA5cHgiKQogICAgICAgICAgICAgICAgICAgICAgICBhdmF0YXJzX3JlZlsiZWxlbWVudHMiXVtv"
    "bGRfaWRdID0gYXZhdGFyCiAgICAgICAgICAgICAgICB1aS5idXR0b24oIuKGkCDQk9C+0YDQvtC0Iiwgb25fY2xpY2s9bGFtYmRh"
    "OiB1aS5uYXZpZ2F0ZS50bygiL2dyb25kaGVpbSIpKS5wcm9wcygiZmxhdCIpLnN0eWxlKAogICAgICAgICAgICAgICAgICAgICJj"
    "b2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNSk7IikKCiAgICAgICAgd2l0aCB1aS5lbGVtZW50KCJkaXYiKS5jbGFzc2VzKCJhcmVh"
    "LWxlZnQiKToKICAgICAgICAgICAgd2l0aCB1aS5lbGVtZW50KCJkaXYiKS5jbGFzc2VzKCJsZWZ0LWNvbCIpOgogICAgICAgICAg"
    "ICAgICAgd2l0aCB1aS5lbGVtZW50KCJkaXYiKS5jbGFzc2VzKCJnbGFzcyBhc3NldC1iYXkiKS5zdHlsZSgiaGVpZ2h0OmF1dG87"
    "IGZsZXg6MTsiKToKICAgICAgICAgICAgICAgICAgICB3aXRoIHVpLnJvdygpLnN0eWxlKAogICAgICAgICAgICAgICAgICAgICAg"
    "ICAid2lkdGg6MTAwJTsganVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47IGFsaWduLWl0ZW1zOmNlbnRlcjsgIgogICAgICAg"
    "ICAgICAgICAgICAgICAgICAicGFkZGluZzo4cHggMTZweCA2cHggMTZweDsgYm9yZGVyLWJvdHRvbToxcHggc29saWQgcmdiYSgy"
    "NTUsMjU1LDI1NSwwLjA4KTsiCiAgICAgICAgICAgICAgICAgICAgKToKICAgICAgICAgICAgICAgICAgICAgICAgdWkubGFiZWwo"
    "ItCX0JDQk9Cg0KPQl9Cn0JjQmiIpLnN0eWxlKAogICAgICAgICAgICAgICAgICAgICAgICAgICAgImNvbG9yOnJnYmEoMjU1LDI1"
    "NSwyNTUsMC45Mik7IGZvbnQtd2VpZ2h0OjkwMDsgbGV0dGVyLXNwYWNpbmc6LjEyZW07ICIKICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICAgICJ0ZXh0LXRyYW5zZm9ybTp1cHBlcmNhc2U7IGZvbnQtc2l6ZToxMXB4OyIpCiAgICAgICAgICAgICAgICAgICAgICAg"
    "IHVpLmJ1dHRvbigiQ0xFQVIiLCBvbl9jbGljaz1jbGVhcl9maWxlcykucHJvcHMoImZsYXQgZGVuc2Ugc2l6ZT14cyIpLnN0eWxl"
    "KAogICAgICAgICAgICAgICAgICAgICAgICAgICAgImNvbG9yOnJnYmEoMjU1LDgwLDgwLDAuNSk7IGZvbnQtc2l6ZTo5cHg7IikK"
    "ICAgICAgICAgICAgICAgICAgICBmaWxlc19yZWZbInVwbG9hZGVyIl0gPSB1aS51cGxvYWQoCiAgICAgICAgICAgICAgICAgICAg"
    "ICAgIG9uX3VwbG9hZD1oYW5kbGVfdXBsb2FkLCBtdWx0aXBsZT1UcnVlLCBhdXRvX3VwbG9hZD1UcnVlLAogICAgICAgICAgICAg"
    "ICAgICAgICkucHJvcHMoImZsYXQgY29sb3I9Y3lhbiIpLnN0eWxlKCJtYXJnaW46IDAgOHB4IDhweCA4cHg7IikKICAgICAgICAg"
    "ICAgICAgICAgICBmaWxlc19yZWZbImVsZW1lbnQiXSA9IHVpLmVsZW1lbnQoImRpdiIpLmNsYXNzZXMoImZpbGUtbGlzdCIpLnN0"
    "eWxlKAogICAgICAgICAgICAgICAgICAgICAgICAiaGVpZ2h0OmF1dG87IG1heC1oZWlnaHQ6bm9uZTsgb3ZlcmZsb3c6dmlzaWJs"
    "ZTsgcGFkZGluZzo0cHggOHB4OyIpCiAgICAgICAgICAgICAgICAgICAgX3NjYW5fdGVzdF9kYXRhKCkKICAgICAgICAgICAgICAg"
    "ICAgICB1cGRhdGVfZmlsZXNfZGlzcGxheSgpCgogICAgICAgIHdpdGggdWkuZWxlbWVudCgiZGl2IikuY2xhc3NlcygiYXJlYS1z"
    "dGFnZSIpOgogICAgICAgICAgICB3aXRoIHVpLmVsZW1lbnQoImRpdiIpLmNsYXNzZXMoImdsYXNzIHN0YWdlLW1vbml0b3IiKS5z"
    "dHlsZSgiaGVpZ2h0OjEwMCU7IG92ZXJmbG93OmhpZGRlbjsiKToKICAgICAgICAgICAgICAgIHdpdGggdWkuZWxlbWVudCgiZGl2"
    "IikuY2xhc3Nlcygic3RhZ2UtdG9vbGJhciIpLnN0eWxlKCJmbGV4LXNocmluazowOyIpOgogICAgICAgICAgICAgICAgICAgIHdp"
    "dGggdWkuZWxlbWVudCgiZGl2Iikuc3R5bGUoImRpc3BsYXk6ZmxleDsgZ2FwOjZweDsgYWxpZ24taXRlbXM6Y2VudGVyOyIpOgog"
    "ICAgICAgICAgICAgICAgICAgICAgICB1aS5idXR0b24oIvCfk6Eg0KDQq9Cd0J7QmiIsIG9uX2NsaWNrPW1hcmtldF9kaXNwYXRj"
    "aCkucHJvcHMoImZsYXQiKS5zdHlsZSgnJycKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHBhZGRpbmc6IDhweCAxOHB4OyBi"
    "b3JkZXItcmFkaXVzOiA4cHg7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBiYWNrZ3JvdW5kOiBsaW5lYXItZ3JhZGllbnQo"
    "MTM1ZGVnLCByZ2JhKDAsMjU1LDEzNiwwLjE1KSwgcmdiYSgwLDIwNCwyNTUsMC4xMCkpICFpbXBvcnRhbnQ7CiAgICAgICAgICAg"
    "ICAgICAgICAgICAgICAgICBib3JkZXI6IDFweCBzb2xpZCByZ2JhKDAsMjU1LDEzNiwwLjM1KTsKICAgICAgICAgICAgICAgICAg"
    "ICAgICAgICAgIGNvbG9yOiByZ2JhKDI1NSwyNTUsMjU1LDAuOSk7IGZvbnQtd2VpZ2h0OiA3MDA7CiAgICAgICAgICAgICAgICAg"
    "ICAgICAgICcnJykKICAgICAgICAgICAgICAgICAgICAgICAgdG9vbGJhcl9yZWZzWyJtb2RlX3JlYWwiXSA9IHVpLmVsZW1lbnQo"
    "ImRpdiIpLnN0eWxlKAogICAgICAgICAgICAgICAgICAgICAgICAgICAgInBhZGRpbmc6NnB4IDE0cHg7Ym9yZGVyLXJhZGl1czo3"
    "cHg7Zm9udC1zaXplOjEycHg7Zm9udC13ZWlnaHQ6NzAwOyIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJjdXJzb3I6cG9p"
    "bnRlcjtiYWNrZ3JvdW5kOnJnYmEoMCwyNTUsMTM2LDAuMTUpO2NvbG9yOiMwMGZmODg7IgogICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICAgImJvcmRlcjoxcHggc29saWQgcmdiYSgwLDI1NSwxMzYsMC40KTsiKQogICAgICAgICAgICAgICAgICAgICAgICB0b29s"
    "YmFyX3JlZnNbIm1vZGVfcmVhbCJdLm9uKCJjbGljayIsIGxhbWJkYTogc2V0X21vZGUoInJlYWwiKSkKICAgICAgICAgICAgICAg"
    "ICAgICAgICAgd2l0aCB0b29sYmFyX3JlZnNbIm1vZGVfcmVhbCJdOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgdWkuaHRt"
    "bCgi0KDQldCQ0JsiKQogICAgICAgICAgICAgICAgICAgICAgICB0b29sYmFyX3JlZnNbIm1vZGVfdGVzdGVyIl0gPSB1aS5lbGVt"
    "ZW50KCJkaXYiKS5zdHlsZSgKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJwYWRkaW5nOjZweCAxNHB4O2JvcmRlci1yYWRp"
    "dXM6N3B4O2ZvbnQtc2l6ZToxMnB4O2ZvbnQtd2VpZ2h0OjcwMDsiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAiY3Vyc29y"
    "OnBvaW50ZXI7YmFja2dyb3VuZDpyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpOyIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJj"
    "b2xvcjpyZ2JhKDI1NSwyNTUsMjU1LDAuNDUpO2JvcmRlcjoxcHggc29saWQgcmdiYSgyNTUsMjU1LDI1NSwwLjA4KTsiKQogICAg"
    "ICAgICAgICAgICAgICAgICAgICB0b29sYmFyX3JlZnNbIm1vZGVfdGVzdGVyIl0ub24oImNsaWNrIiwgbGFtYmRhOiBzZXRfbW9k"
    "ZSgidGVzdGVyIikpCiAgICAgICAgICAgICAgICAgICAgICAgIHdpdGggdG9vbGJhcl9yZWZzWyJtb2RlX3Rlc3RlciJdOgogICAg"
    "ICAgICAgICAgICAgICAgICAgICAgICAgdWkuaHRtbCgi0KLQldCh0KLQldCgIikKICAgICAgICAgICAgICAgICAgICAgICAgdG9v"
    "bGJhcl9yZWZzWyJiYXJzX2xhYmVsIl0gPSB1aS5lbGVtZW50KCJkaXYiKS5zdHlsZSgiZGlzcGxheTpub25lO2FsaWduLWl0ZW1z"
    "OmNlbnRlcjtnYXA6NXB4OyIpCiAgICAgICAgICAgICAgICAgICAgICAgIHdpdGggdG9vbGJhcl9yZWZzWyJiYXJzX2xhYmVsIl06"
    "CiAgICAgICAgICAgICAgICAgICAgICAgICAgICB1aS5sYWJlbCgi0LvQvtCy0LjRgtGMOiIpLnN0eWxlKCJjb2xvcjpyZ2JhKDI1"
    "NSwyNTUsMjU1LDAuNDUpO2ZvbnQtc2l6ZToxMXB4OyIpCiAgICAgICAgICAgICAgICAgICAgICAgIHRvb2xiYXJfcmVmc1siYmFy"
    "c19pbnB1dCJdID0gdWkuZWxlbWVudCgiZGl2Iikuc3R5bGUoImRpc3BsYXk6bm9uZTthbGlnbi1pdGVtczpjZW50ZXI7IikKICAg"
    "ICAgICAgICAgICAgICAgICAgICAgd2l0aCB0b29sYmFyX3JlZnNbImJhcnNfaW5wdXQiXToKICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICAgIF9iaSA9IHVpLm51bWJlcih2YWx1ZT0xLCBtaW49MSwgbWF4PTk5OSwgZm9ybWF0PSIlZCIpLnByb3BzKCJkZW5zZSBi"
    "b3JkZXJsZXNzIikuc3R5bGUoCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIndpZHRoOjYwcHg7Zm9udC1mYW1pbHk6"
    "SmV0QnJhaW5zIE1vbm87Zm9udC1zaXplOjEycHg7Y29sb3I6cmdiYSgwLDIwNCwyNTUsMC45KTsiKQogICAgICAgICAgICAgICAg"
    "ICAgICAgICAgICAgX2JpLm9uKCJ1cGRhdGU6bW9kZWwtdmFsdWUiLCBsYW1iZGEgZTogc3RhdGUudXBkYXRlKHsiYmFyc190b19s"
    "aXZlIjogaW50KGUuYXJncyBvciAxKX0pKQogICAgICAgICAgICAgICAgICAgICAgICB0b29sYmFyX3JlZnNbInN0b3BfYnRuIl0g"
    "PSB1aS5lbGVtZW50KCJkaXYiKS5zdHlsZSgKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJkaXNwbGF5Om5vbmU7YWxpZ24t"
    "aXRlbXM6Y2VudGVyO3BhZGRpbmc6NnB4IDE0cHg7Ym9yZGVyLXJhZGl1czo3cHg7IgogICAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAgImZvbnQtc2l6ZToxMnB4O2ZvbnQtd2VpZ2h0OjcwMDtjdXJzb3I6cG9pbnRlcjsiCiAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICAiYmFja2dyb3VuZDpyZ2JhKDI1NSw4MCw4MCwwLjEyKTtjb2xvcjojZmY1MDUwO2JvcmRlcjoxcHggc29saWQgcmdiYSgy"
    "NTUsODAsODAsMC40KTsiKQogICAgICAgICAgICAgICAgICAgICAgICB0b29sYmFyX3JlZnNbInN0b3BfYnRuIl0ub24oImNsaWNr"
    "IiwgbGFtYmRhOiByZXF1ZXN0X3N0b3AoKSkKICAgICAgICAgICAgICAgICAgICAgICAgd2l0aCB0b29sYmFyX3JlZnNbInN0b3Bf"
    "YnRuIl06CiAgICAgICAgICAgICAgICAgICAgICAgICAgICB1aS5odG1sKCLij7gg0KHQotCe0J8iKQogICAgICAgICAgICAgICAg"
    "ICAgIHdpdGggdWkuZWxlbWVudCgiZGl2Iikuc3R5bGUoImRpc3BsYXk6ZmxleDsgZ2FwOjZweDsgYWxpZ24taXRlbXM6Y2VudGVy"
    "OyBqdXN0aWZ5LWNvbnRlbnQ6Y2VudGVyOyIpOgogICAgICAgICAgICAgICAgICAgICAgICB1aS5sYWJlbCgi8J+TiiDQkdCY0KDQ"
    "ltCQIMK3INCh0J7QktCV0KIiKS5zdHlsZSgKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJjb2xvcjpyZ2JhKDAsMjA0LDI1"
    "NSwwLjcpOyBmb250LXdlaWdodDo4MDA7IGZvbnQtc2l6ZTowLjhyZW07IGxldHRlci1zcGFjaW5nOjAuMDhlbTsiKQogICAgICAg"
    "ICAgICAgICAgICAgIHdpdGggdWkucm93KCkuc3R5bGUoImdhcDo4cHg7IGp1c3RpZnktY29udGVudDpmbGV4LWVuZDsiKToKICAg"
    "ICAgICAgICAgICAgICAgICAgICAgdWkuYnV0dG9uKCLihpAg0JHRgNCw0YIiLCBvbl9jbGljaz1sYW1iZGE6IHVpLm5hdmlnYXRl"
    "LnRvKCIvYnJhdCIpKS5wcm9wcygiZmxhdCIpLnN0eWxlKAogICAgICAgICAgICAgICAgICAgICAgICAgICAgInBhZGRpbmc6NnB4"
    "IDE0cHg7IGJvcmRlci1yYWRpdXM6OHB4OyBmb250LXNpemU6MTJweDsgIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgImJh"
    "Y2tncm91bmQ6cmdiYSg5OSwxMzAsMjU1LDAuMDgpOyBib3JkZXI6MXB4IHNvbGlkIHJnYmEoOTksMTMwLDI1NSwwLjI1KTsgIgog"
    "ICAgICAgICAgICAgICAgICAgICAgICAgICAgImNvbG9yOnJnYmEoMTgwLDE5MCwyMjAsMC44KTsiKQoKICAgICAgICAgICAgICAg"
    "IHdpdGggdWkuZWxlbWVudCgiZGl2IikuY2xhc3Nlcygic3RhZ2UtY29udGVudCIpLnN0eWxlKCJmbGV4OjE7IG1pbi1oZWlnaHQ6"
    "MDsgb3ZlcmZsb3c6aGlkZGVuOyIpOgogICAgICAgICAgICAgICAgICAgIHdpdGggdWkuZWxlbWVudCgiZGl2IikuY2xhc3Nlcygi"
    "c3BsaXQtdmlldyIpLnN0eWxlKCJoZWlnaHQ6MTAwJTsgbWluLWhlaWdodDowOyBvdmVyZmxvdzpoaWRkZW47Iik6CiAgICAgICAg"
    "ICAgICAgICAgICAgICAgIGNoYXRfbG9nX3JlZlsiZWxlbWVudCJdID0gdWkuZWxlbWVudCgiZGl2IikuY2xhc3NlcygiY2hhdC1s"
    "b2ciKS5zdHlsZSgKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJmbGV4OjE7IG1pbi1oZWlnaHQ6MDsgb3ZlcmZsb3cteTph"
    "dXRvOyIpCiAgICAgICAgICAgICAgICAgICAgICAgIHdpdGggY2hhdF9sb2dfcmVmWyJlbGVtZW50Il06CiAgICAgICAgICAgICAg"
    "ICAgICAgICAgICAgICB1aS5odG1sKCc8ZGl2IGNsYXNzPSJjaGF0LW1zZy1zeXN0ZW0iPlNZU1RFTTog0JHQuNGA0LbQsCDQs9C+"
    "0YLQvtCy0LA8L2Rpdj4nKQogICAgICAgICAgICAgICAgICAgICAgICB2aWV3ZXJfcmVmWyJlbGVtZW50Il0gPSB1aS5lbGVtZW50"
    "KCJkaXYiKS5jbGFzc2VzKCJ2aWV3ZXIiKS5zdHlsZSgKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJmbGV4OjE7IG1pbi1o"
    "ZWlnaHQ6MDsgb3ZlcmZsb3cteTphdXRvOyIpCiAgICAgICAgICAgICAgICAgICAgICAgIHdpdGggdmlld2VyX3JlZlsiZWxlbWVu"
    "dCJdOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgdWkubGFiZWwoItCe0YLRh9GR0YLRiyDQsNCz0LXQvdGC0L7QsiDQv9C+"
    "0Y/QstGP0YLRgdGPINC30LTQtdGB0YwiKQoKICAgICAgICAgICAgICAgIHdpdGggdWkuZWxlbWVudCgiZGl2IikuY2xhc3Nlcygi"
    "ZmxvYXRpbmctY29uc29sZSIpOgogICAgICAgICAgICAgICAgICAgIGlucHV0X3JlZlsiZWxlbWVudCJdID0gdWkuaW5wdXQocGxh"
    "Y2Vob2xkZXI9ItCh0L7QvtCx0YnQtdC90LjQtSDQodC+0LLQtdGC0YMuLi4iKS5wcm9wcygiYm9yZGVybGVzcyIpLnN0eWxlKCJm"
    "bGV4OjEiKQogICAgICAgICAgICAgICAgICAgIGlucHV0X3JlZlsiZWxlbWVudCJdLm9uKCJrZXlkb3duLmVudGVyIiwgc2VuZF9t"
    "ZXNzYWdlKQogICAgICAgICAgICAgICAgICAgIHVpLmJ1dHRvbigiU0VORCIsIG9uX2NsaWNrPXNlbmRfbWVzc2FnZSkuY2xhc3Nl"
    "cygic2VuZC1idXR0b24iKQoKICAgICAgICB3aXRoIHVpLmVsZW1lbnQoImRpdiIpLmNsYXNzZXMoImFyZWEtcmlnaHQiKToKICAg"
    "ICAgICAgICAgd2l0aCB1aS5lbGVtZW50KCJkaXYiKS5jbGFzc2VzKCJyaWdodC1jb2wiKToKICAgICAgICAgICAgICAgIGF2YXRh"
    "cl9yZWZbImVsZW1lbnQiXSA9IHVpLmVsZW1lbnQoImRpdiIpLmNsYXNzZXMoInJpZ2h0LXRvcC1zbG90IikKICAgICAgICAgICAg"
    "ICAgIHVwZGF0ZV9hdmF0YXIoKQoKICAgICAgICAgICAgICAgIHdpdGggdWkuZWxlbWVudCgiZGl2IikuY2xhc3NlcygiZ2xhc3Mi"
    "KS5zdHlsZSgibWFyZ2luLXRvcDoxMnB4OyBmbGV4LXNocmluazowOyBvdmVyZmxvdzpoaWRkZW47Iik6CiAgICAgICAgICAgICAg"
    "ICAgICAgdml0YWxzX3JlZlsiZWxlbWVudCJdID0gdWkuZWxlbWVudCgiZGl2IikKICAgICAgICAgICAgICAgICAgICB1cGRhdGVf"
    "dml0YWxzKCkKCiAgICAgICAgICAgICAgICB3aXRoIHVpLmVsZW1lbnQoImRpdiIpLmNsYXNzZXMoImdsYXNzIikuc3R5bGUoIm1h"
    "cmdpbi10b3A6MTJweDsgZmxleC1zaHJpbms6MDsgb3ZlcmZsb3c6aGlkZGVuOyIpOgogICAgICAgICAgICAgICAgICAgIHVpLmh0"
    "bWwoJzxkaXYgY2xhc3M9InBhbmVsLXRpdGxlIj7Qn9Cg0JjQkdCe0KDQqzwvZGl2PicpCiAgICAgICAgICAgICAgICAgICAgc3Rh"
    "dHNfcmVmWyJlbGVtZW50Il0gPSB1aS5lbGVtZW50KCJkaXYiKQogICAgICAgICAgICAgICAgICAgIHdpdGggc3RhdHNfcmVmWyJl"
    "bGVtZW50Il06CiAgICAgICAgICAgICAgICAgICAgICAgIHVpLmh0bWwoJzxkaXYgc3R5bGU9ImNvbG9yOnJnYmEoMjU1LDI1NSwy"
    "NTUsMC4zKTsgZm9udC1zaXplOjExcHg7ICcKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAncGFkZGluZzoxMHB4OyB0"
    "ZXh0LWFsaWduOmNlbnRlcjsiPtCd0LDQttC80Lgg0KDQq9Cd0J7QmiDigJQg0JjRgdC60YDQsCDQvtC20LjQstGR0YI8L2Rpdj4n"
    "KQoKCmlmIF9fbmFtZV9fIGluIHsiX19tYWluX18iLCAiX19tcF9tYWluX18ifToKICAgIEB1aS5wYWdlKCIvdG9yZy97dHNlaF9p"
    "ZH0iKQogICAgZGVmIF90b3JnX3BhZ2UodHNlaF9pZDogc3RyID0gItGC0L7RgNCz0L7QstGL0Llf0YXQsNC+0YEiKToKICAgICAg"
    "ICBwYWdlX3RvcmcodHNlaF9pZCkKICAgIEB1aS5wYWdlKCIvdG9yZyIpCiAgICBkZWYgX3RvcmcwKCk6CiAgICAgICAgcGFnZV90"
    "b3JnKCkKICAgIHVpLnJ1bih0aXRsZT0i0KHQvtCy0LXRgiDQkdC40YDQttC4IMK3INCT0YDQvtC90LTRhdC10LnQvCIsIHBvcnQ9"
    "ODEwNCwgcmVsb2FkPUZhbHNlKQoKIyBVSV9UT1JHX1RZUElOR19WMSDigJQg0LzQsNGA0LrQtdGAINC40LTQtdC80L/QvtGC0LXQ"
    "vdGC0L3QvtGB0YLQuAo="
)


def main():
    if not TESTER_TARGET.exists() or not UI_TARGET.exists():
        print("ВНИМАНИЕ: Биржа/tester_express.py или Биржа/ui_torg.py не найдены --")
        print("    патчи фазы 1/2 применены?")
        sys.exit(1)

    TESTER_TARGET.write_text(TESTER_CONTENT, encoding="utf-8")
    ui_content = base64.b64decode("".join(_UI_B64_CHUNKS)).decode("utf-8")
    UI_TARGET.write_text(ui_content, encoding="utf-8")

    print("=" * 62)
    print("ENGINE_ONE_DOOR_V1 -- фаза 3 (память чата) применена")
    print("=" * 62)
    print("  [обновлён] Биржа/tester_express.py")
    print("  [обновлён] Биржа/ui_torg.py")
    print()
    print("Чат с агентом теперь знает контекст ПОСЛЕ ТЕСТЕРА так же,")
    print("как после РЫНКА -- один источник памяти (_apply_agent_result).")
    print()
    print("Прогони тестер, затем сразу спроси агента в чате про рынок --")
    print("должен ответить по существу, а не \"рынок не запускали\".")


if __name__ == "__main__":
    if not (REPO_ROOT / "GRONDHEIM_CITY").exists() or not (REPO_ROOT / "Биржа").exists():
        print("ВНИМАНИЕ: рядом со скриптом нет GRONDHEIM_CITY/ и Биржа/.")
        print("    Запусти патч из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)
    main()
