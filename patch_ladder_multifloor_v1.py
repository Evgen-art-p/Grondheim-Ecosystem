# -*- coding: utf-8 -*-
"""
patch_ladder_multifloor_v1.py
-----------------------------------------------------------
LADDER_MULTIFLOOR_V1 -- тестер спускается по НАСТОЯЩЕЙ лесенке.

ВОПРОС ШЕФА: "может, все котировки загрузить по таймфреймам на золоте?
точней лесенка работать будет?" -- ДА. Проверено.

ДИАГНОЗ (до патча): тестер был заперт на ОДНОМ этаже -- том единственном
CSV, что передан в --csv. mt5_feed._fetch/pull_bars ИГНОРИРОВАЛИ
запрошенный tf_name и всегда отдавали срез ЕДИНСТВЕННОГО файла;
step_down всегда возвращал None. Спуск Искры физически не мог
опуститься глубже загруженного файла, даже когда по канону должен был.

Отдельно уже существовал Биржа/feed_source.py (_find_csv,
_bars_from_folder) -- умеет находить файл под любой этаж в test_data/,
но использовался только для "хвоста" файла (последние N баров) --
годится для живого прогона всего файла подряд, но не для честного
"дай этаж на ЭТУ историческую дату" внутри бэктеста (иначе -- забегание
вперёд по времени).

ЧТО МЕНЯЕТСЯ (Биржа/tester_express.py):
  1. При старте прогона грузятся ВСЕ найденные в test_data/ этажи
     лесенки символа (_TF_LADDER: MN1..M5) -- через _find_csv из
     feed_source.py (переиспользована, не продублирована).
  2. Новая _bars_as_of(tf_name, cutoff_date, count) -- честный срез
     этажа НЕ ПОЗЖЕ текущей исторической даты. Даты MT5 сравниваются
     как строки (формат фикс-ширины = лексикографический порядок
     совпадает с хронологическим) -- забегание вперёд невозможно.
  3. _fake_fetch/_fake_pull теперь СМОТРЯТ на запрошенный tf_name и
     берут ЕГО этаж (раньше -- игнорировали, всегда отдавали главный).
  4. step_down (_multi_step_down) спускается по настоящей лесенке,
     но ЧЕСТНО: этаж существует для спуска, только если а) файл на
     него нашёлся И б) этот файл покрывает текущую историческую дату.
     M5/M15/M30/M10 короче историей (экспорт MT5 ограничен ~100k
     баров) -- на старых датах спуск честно останавливается там, где
     данные кончились, не выдумывает более глубокие этажи.

ПРОВЕРЕНО (см. отчёт в чате) -- НА РЕАЛЬНЫХ 11 файлах test_data/:
  - Полная цепочка MN1->W1->D1->H12->H8->H4->H1->M30->M15->M10->M5 на
    свежей дате (2026.05.01) доходит до самого дна.
  - На старой дате (2015.03.10) честно останавливается на H1 -- M30
    и глубже физически не существовали в экспорте на этот момент.
  - На промежуточной (2023.01.15) останавливается на M15 -- M10
    появляется в файле только с 2023.08.
  - Ни один срез не содержит бара с датой позже cutoff (без
    забегания вперёд) -- проверено на D1/H1 отдельно.
  - Текущий формирующийся бар старшего этажа (дата без времени,
    совпадает с cutoff) корректно ВКЛЮЧАЕТСЯ -- как в живом терминале.

Идемпотентно: безопасно запускать повторно.

Запуск из КОРНЯ репозитория (после фаз 1/2/3 -- ENGINE_ONE_DOOR_V1 --
и патча компаса, если применялись):
    python patch_ladder_multifloor_v1.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "Биржа" / "tester_express.py"

NEW_CONTENT = r'''# studio/modules/trading/tester_express.py
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
# ЛЕСЕНКА (LADDER_MULTIFLOOR_V1): если в test_data/ нашлись файлы под
# другие этажи символа (M5/M15/.../MN1) — спуск Искры по-настоящему
# спускается по реальным историческим барам каждого этажа, honest
# срез по дате (без забегания вперёд). Каких-то этажей может не
# хватать по длине истории самого экспорта MT5 (M5/M15 короче) —
# тогда спуск честно останавливается там, где данные кончились.
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

    # ── МНОГОЭТАЖНАЯ ЛЕСЕНКА (LADDER_MULTIFLOOR_V1) ──────────
    # Раньше тестер был заперт на одном этаже (тот, что явно передан
    # в --csv): step_down всегда None, спуск не мог опуститься глубже
    # загруженного файла, даже если по канону должен был. Шеф выгрузил
    # test_data/ с ПОЛНЫМ комплектом (M5..MN1) — грузим все, что
    # нашлись, чтобы лесенка спускалась по НАСТОЯЩИМ историческим
    # барам, не упираясь в потолок одного файла.
    #
    # Поиск файла под каждый этаж переиспользует feed_source._find_csv
    # (то же самое угадывание имени — словом для старших ТФ, кодом для
    # младших) — не плодим вторую логику поиска файлов в репо.
    import bisect
    try:
        from feed_source import _find_csv as _ffs_find_csv
    except ImportError:
        _ffs_find_csv = None
    try:
        from mt5_feed import _TF_LADDER as _MT5_LADDER
    except ImportError:
        _MT5_LADDER = None
    _TF_LADDER = _MT5_LADDER or ["MN1", "W1", "D1", "H12", "H8", "H4",
                                  "H1", "M30", "M15", "M10", "M5"]

    _floors: dict = {timeframe.upper(): bars_all}   # главный этаж уже на руках
    if _ffs_find_csv is not None:
        for _tf in _TF_LADDER:
            if _tf in _floors:
                continue
            _p = _ffs_find_csv(symbol, _tf)
            if _p is None:
                continue
            _b = read_mt5_csv(str(_p))
            if _b:
                _floors[_tf] = _b
    print(f"[TESTER] 🪜 этажи лесенки в наличии: {sorted(_floors.keys())}")

    def _bars_as_of(tf_name: str, cutoff_date: str, count: int):
        """
        Честный срез этажа tf_name НЕ ПОЗЖЕ cutoff_date — без забегания
        вперёд. Даты MT5 (YYYY.MM.DD[ HH:MM]) сравниваются как строки:
        формат фикс-ширины, лексикографический порядок = хронологический.
        Текущий ФОРМИРУЮЩИЙСЯ бар старшего этажа (дата без времени,
        совпадает с сегодняшней датой cutoff) КОРРЕКТНО включается —
        так же ведёт себя живой терминал (текущая свеча видна, пока
        не закрылась). Этаж не покрывает эту дату (M5/M15 короче
        историей) → честно пусто — лесенка/step_down поймут это как
        честную вакансию этажа, не как ошибку.
        """
        floor = _floors.get((tf_name or timeframe).upper())
        if not floor:
            return [], None
        dates = [b["date"] for b in floor]
        idx = bisect.bisect_right(dates, cutoff_date)
        if idx == 0:
            return [], None
        start = max(0, idx - count) if count else 0
        return floor[start:idx], point

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

    # ── КРАН: подменяем _fetch на честный срез нужного ЭТАЖА ──
    # LADDER_MULTIFLOOR_V1: раньше отдавали срез ЕДИНСТВЕННОГО
    # загруженного файла, игнорируя tf_name целиком (один CSV = один
    # этаж). Теперь смотрим, какой этаж просят, и берём его из
    # _floors (если он в наличии) — срез честный, по дате текущего
    # "сейчас" (см. _bars_as_of выше), без забегания вперёд.
    state = {"cursor": warmup}

    def _fake_fetch(mt5, sym, tf_name, count):
        cutoff = bars_all[state["cursor"]]["date"]
        return _bars_as_of(tf_name or timeframe, cutoff, count)

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

    # ── ГЕРМЕТИЧНЫЙ КРАН (TESTER_TO_CABINET_V1) ──────────────
    # Спуск Искры (_read_form_on) берёт бары через pull_bars, не
    # через _fetch. Накрываем и её: тот же честный срез по дате.
    #
    # LADDER_MULTIFLOOR_V1: step_down теперь НЕ заперт наглухо —
    # спускается по настоящей лесенке (_TF_LADDER), но ЧЕСТНО: этаж
    # существует для спуска ТОЛЬКО если на него нашёлся файл И этот
    # файл покрывает текущую историческую дату (M5/M15 короче
    # историей — до 2025/2022 их считай нет, спуск остановится
    # на последнем этаже, что реально существовал в тот момент).
    def _fake_pull(sym, tf_name, count=2000):
        return _fake_fetch(None, sym, tf_name, count)

    def _multi_step_down(tf_name):
        tf = (tf_name or "").upper()
        if tf not in _TF_LADDER:
            return None
        i = _TF_LADDER.index(tf)
        if i + 1 >= len(_TF_LADDER):
            return None
        next_tf = _TF_LADDER[i + 1]
        cutoff = bars_all[state["cursor"]]["date"]
        probe, _ = _bars_as_of(next_tf, cutoff, 1)
        if not probe:
            return None   # этажа нет ИЛИ он не покрывает эту дату — честно
        return next_tf

    mt5_feed.pull_bars = _fake_pull
    mt5_feed.step_down = _multi_step_down

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


def main():
    if not TARGET.exists():
        print(f"ВНИМАНИЕ: {TARGET} не найден -- патчи фаз 1/2/3 применены?")
        sys.exit(1)
    TARGET.write_text(NEW_CONTENT, encoding="utf-8")
    print("=" * 62)
    print("LADDER_MULTIFLOOR_V1 -- патч применён")
    print("=" * 62)
    print("  [обновлён] Биржа/tester_express.py")
    print()
    print("При старте тестера увидишь строку вида:")
    print('  [TESTER] 🪜 этажи лесенки в наличии: [...]')
    print("-- список этажей, для которых нашлись файлы в test_data/.")
    print()
    print("Спуск Искры теперь честно опускается по реальным историческим")
    print("барам каждого найденного этажа вместо потолка одного файла.")
    print("На старых датах глубина спуска может быть меньше (M5/M15/M30")
    print("короче историей) -- это честная граница экспорта MT5, не баг.")


if __name__ == "__main__":
    if not (REPO_ROOT / "GRONDHEIM_CITY").exists() or not (REPO_ROOT / "Биржа").exists():
        print("ВНИМАНИЕ: рядом со скриптом нет GRONDHEIM_CITY/ и Биржа/.")
        print("    Запусти патч из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)
    main()
