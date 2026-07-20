# Биржа/zigzag_core.py
# ─────────────────────────────────────────────────────────────
# АВТОМАТ НОГ ЗИГЗАГА A-B-C — изолированное ядро
# Канон согласован Шефом и Локой 19-20.07 (Летопись §5с.4).
#
# ЗАКОН (как williams_core.py): этот файл не знает про Грондхейм,
# агентов, cartridge, Искру. Принимает bars + числовые ряды пасти
# (jaw/teeth/lips/bars_open — из williams_core) и фракталы (тоже из
# williams_core) → отдаёт СОБЫТИЯ. Толкует их кто-то другой (hooks.py /
# Искра). Здесь только механика волны.
#
# ЗАЧЕМ (курс, поправленный Шефом 20.07): не отсекать флэт порогом N —
# СТРОИТЬ ВОЛНУ. Флэт исключает себя САМ: на нём нога C никогда не
# подтвердится (цена не пробьёт экстремум ноги A), а любая ложная
# нога A, родившаяся на дребезге пасти, умирает раньше, чем доходит
# до B — просто потому что пасть у неё сама не держится открытой.
# Никакого отдельного порога N ЗДЕСЬ НЕТ — фильтрация встроена в
# саму механику жизни ноги, не навешана сверху.
#
# КАНОН (дословно, §5с.4):
#   Нога = фрактал Ганса, подтверждённый вне пасти Аллигатора.
#   Старт ноги A требует настоящего предварительного раскрытия пасти
#     (jaw НЕ sleeping в момент фрактала) — не постфактум.
#   Ведение ноги — бегущий экстремум обновляется, пока пасть открыта
#     В ЕЁ СТОРОНУ; закрытие ноги — пасть переплелась (стала sleeping)
#     ИЛИ развернулась в другую сторону — экстремум фиксируется в архив.
#   Между ногами возможна пауза (ожидание) — смена стороны не обязана
#     быть мгновенной, тик-в-тик.
#   Волна C подтверждается ТОЛЬКО когда третья нога ЦЕНОЙ пробивает
#     зафиксированный экстремум ноги A. Если пасть переплелась раньше
#     пробоя — ВСЯ структура (A, B, попытка) стирается целиком, НЕ
#     архивируется.
#   После закрытия подтверждённой C — весь цикл в архив, автомат
#     сбрасывается в ИЩУ_A с нуля.
#   Счёт волн 1-5 после C — вне контура этого автомата (отдельный модуль).
#
# НАПРАВЛЕНИЕ НОГИ:
#   UP-фрактал (вершина, вне пасти сверху) → нога ВНИЗ  (BEAR)
#   DOWN-фрактал (низ, вне пасти снизу)    → нога ВВЕРХ (BULL)
#   (та же логика, что уже проверена в calibrate_leg_a_threshold.py —
#   фрактал-вершина при бычьей пасти это не разворот, а свежий хай
#   ВНУТРИ бычьего хода; правило само это отбрасывает без всякого N.)
#
# НАПРАВЛЕНИЕ ПАСТИ: lips vs teeth (тот же фоллбэк, что
# build_market_data использует для резинки Джастин, когда
# divergent_bar молчит) — BULL если lips > teeth, иначе BEAR.
# ─────────────────────────────────────────────────────────────

from typing import Optional


# ── Состояния автомата (дословно из канона §5с.4) ─────────────
ISCHU_A                    = "ИЩУ_A"
VEDU_A                     = "ВЕДУ_A"
ZHDU_B                     = "ЖДУ_B"
VEDU_B                     = "ВЕДУ_B"
ZHDU_POPYTKU_C             = "ЖДУ_ПОПЫТКУ_C"
VEDU_POPYTKU_C             = "ВЕДУ_ПОПЫТКУ_C"
VEDU_PODTVERZHDENNUYU_C    = "ВЕДУ_ПОДТВЕРЖДЁННУЮ_C"

_PROTIVOPOLOZHNAYA = {"BULL": "BEAR", "BEAR": "BULL"}


def jaw_state(bars_open_i: int) -> str:
    """sleeping/opening/mature — ТОЧНО пороги compute_alligator()
    (williams_core.py): 0 → sleeping, 1..7 → opening, 8+ → mature."""
    if bars_open_i == 0:
        return "sleeping"
    if bars_open_i < 8:
        return "opening"
    return "mature"


def jaw_direction(jaw_i, teeth_i, lips_i) -> Optional[str]:
    """BULL/BEAR — фоллбэк build_market_data для резинки Джастин:
    lips > teeth → BULL, иначе BEAR. None если пасть не готова
    (нет истории на SMMA)."""
    if jaw_i is None or teeth_i is None or lips_i is None:
        return None
    return "BULL" if lips_i > teeth_i else "BEAR"


def leg_direction_for_fractal(kind: str) -> str:
    """UP-фрактал (вершина) → нога ВНИЗ (BEAR).
    DOWN-фрактал (низ)     → нога ВВЕРХ (BULL)."""
    return "BEAR" if kind == "UP" else "BULL"


class ZigzagTracker:
    """
    Автомат ног зигзага A-B-C. Живёт между барами (как proverit_tochku
    у hooks.py) — состояние переносится в словаре, метод on_bar()
    зовётся раз на бар. Без единого вызова LLM.

    Ядро НЕ хранит trading_state.json само — это забота hooks.py
    (по Закону Картриджа: ядро слепо к Грондхейму). Здесь только
    словарь state, который вызывающий код обязан сохранять/восстанавливать
    между барами сам (тот же приём, что и в hooks.proverit_tochku).
    """

    @staticmethod
    def novoye_sostoyanie() -> dict:
        """Пустое состояние автомата — старт с нуля (ИЩУ_A)."""
        return {
            "phase": ISCHU_A,
            "a": None,   # {"extreme": float, "dir": "BULL"|"BEAR", "start_idx", "start_date"}
            "b": None,
            "c": None,
        }

    @staticmethod
    def on_bar(state: dict, i: int, bars: list,
              jaw, teeth, lips, bars_open,
              fractals_up_by_idx: dict, fractals_down_by_idx: dict) -> Optional[dict]:
        """
        Один шаг автомата на баре i. Обновляет state НА МЕСТЕ.
        Возвращает событие (dict) или None, если на этом баре ничего
        не произошло. Событие всегда содержит "event" и "bar_index"/"date".

        Возможные event: LEG_A_START, LEG_A_CLOSE, LEG_B_START,
        LEG_B_CLOSE, C_ATTEMPT_START, C_CONFIRMED, C_DISCARDED,
        CYCLE_ARCHIVED.
        """
        st = jaw_state(bars_open[i])
        di = jaw_direction(jaw[i], teeth[i], lips[i])
        date = bars[i]["date"]
        phase = state["phase"]

        # ── ИЩУ_A: ждём фрактал вне пасти, пасть открыта в его сторону ──
        if phase == ISCHU_A:
            for kind, idx_map in (("UP", fractals_up_by_idx), ("DOWN", fractals_down_by_idx)):
                if i not in idx_map:
                    continue
                need_dir = leg_direction_for_fractal(kind)
                if st == "sleeping" or di != need_dir:
                    continue
                fr_price, fr_outside = idx_map[i]
                if not fr_outside:
                    continue
                state["a"] = {"extreme": fr_price, "dir": need_dir,
                              "start_idx": i, "start_date": date}
                state["phase"] = VEDU_A
                return {"event": "LEG_A_START", "bar_index": i, "date": date,
                        "dir": need_dir, "price": fr_price}
            return None

        # ── ВЕДУ_A: бегущий экстремум ноги A, пока пасть открыта туда же ──
        if phase == VEDU_A:
            leg = state["a"]
            zhiva = (st != "sleeping" and di == leg["dir"])
            if zhiva:
                leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bars[i])
                return None
            # пасть переплелась (или развернулась) — нога A закрыта, в архив
            state["phase"] = ZHDU_B
            return {"event": "LEG_A_CLOSE", "bar_index": i, "date": date,
                    "dir": leg["dir"], "extreme": leg["extreme"],
                    "start_date": leg["start_date"]}

        # ── ЖДУ_B: пауза допустима, ждём фрактал В ПРОТИВОПОЛОЖНУЮ сторону ──
        if phase == ZHDU_B:
            need_dir = _PROTIVOPOLOZHNAYA[state["a"]["dir"]]
            need_kind = "UP" if need_dir == "BEAR" else "DOWN"
            idx_map = fractals_up_by_idx if need_kind == "UP" else fractals_down_by_idx
            if i not in idx_map:
                return None
            if st == "sleeping" or di != need_dir:
                return None
            fr_price, fr_outside = idx_map[i]
            if not fr_outside:
                return None
            state["b"] = {"extreme": fr_price, "dir": need_dir,
                          "start_idx": i, "start_date": date}
            state["phase"] = VEDU_B
            return {"event": "LEG_B_START", "bar_index": i, "date": date,
                    "dir": need_dir, "price": fr_price}

        # ── ВЕДУ_B: бегущий экстремум ноги B ──
        if phase == VEDU_B:
            leg = state["b"]
            zhiva = (st != "sleeping" and di == leg["dir"])
            if zhiva:
                leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bars[i])
                return None
            state["phase"] = ZHDU_POPYTKU_C
            return {"event": "LEG_B_CLOSE", "bar_index": i, "date": date,
                    "dir": leg["dir"], "extreme": leg["extreme"],
                    "start_date": leg["start_date"]}

        # ── ЖДУ_ПОПЫТКУ_C: ждём фрактал ОБРАТНО в сторону ноги A ──
        if phase == ZHDU_POPYTKU_C:
            need_dir = state["a"]["dir"]
            need_kind = "UP" if need_dir == "BEAR" else "DOWN"
            idx_map = fractals_up_by_idx if need_kind == "UP" else fractals_down_by_idx
            if i not in idx_map:
                return None
            if st == "sleeping" or di != need_dir:
                return None
            fr_price, fr_outside = idx_map[i]
            if not fr_outside:
                return None
            state["c"] = {"extreme": fr_price, "dir": need_dir,
                          "start_idx": i, "start_date": date, "confirmed": False}
            state["phase"] = VEDU_POPYTKU_C
            return {"event": "C_ATTEMPT_START", "bar_index": i, "date": date,
                    "dir": need_dir, "price": fr_price}

        # ── ВЕДУ_ПОПЫТКУ_C: суд — пробила ли ЦЕНА экстремум ноги A? ──
        if phase == VEDU_POPYTKU_C:
            leg = state["c"]
            a_extreme = state["a"]["extreme"]
            probila = _cena_probila(leg["dir"], bars[i], a_extreme)
            if probila:
                leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bars[i])
                leg["confirmed"] = True
                state["phase"] = VEDU_PODTVERZHDENNUYU_C
                return {"event": "C_CONFIRMED", "bar_index": i, "date": date,
                        "dir": leg["dir"], "a_extreme": a_extreme,
                        "c_start_date": leg["start_date"]}
            zhiva = (st != "sleeping" and di == leg["dir"])
            if zhiva:
                leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bars[i])
                return None
            # пасть переплелась ДО пробоя A — вся структура стирается, НЕ архивируется
            discarded = {"event": "C_DISCARDED", "bar_index": i, "date": date,
                        "reason": "пасть переплелась до пробоя ноги A",
                        "a_start_date": state["a"]["start_date"],
                        "a_extreme": a_extreme}
            state["phase"] = ISCHU_A
            state["a"] = None
            state["b"] = None
            state["c"] = None
            return discarded

        # ── ВЕДУ_ПОДТВЕРЖДЁННУЮ_C: волна подтверждена, ждём переплетения — архив ──
        if phase == VEDU_PODTVERZHDENNUYU_C:
            leg = state["c"]
            zhiva = (st != "sleeping" and di == leg["dir"])
            if zhiva:
                leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bars[i])
                return None
            archived = {"event": "CYCLE_ARCHIVED", "bar_index": i, "date": date,
                       "dir": leg["dir"],
                       "a": dict(state["a"]), "b": dict(state["b"]), "c": dict(leg)}
            state["phase"] = ISCHU_A
            state["a"] = None
            state["b"] = None
            state["c"] = None
            return archived

        return None


def on_bar_md(state: dict, md: dict) -> Optional[dict]:
    """
    ЖИВОЙ шаг автомата — из уже готового market_data (тот же приём,
    что hooks.proverit_tochku: ни одного отдельного пересчёта рядов,
    только то, что build_market_data и так посчитал на этом баре).

    Почему не через ряды (podgotovit_ryady) в бою: тестер и живой поток
    кормят Совет СКОЛЬЗЯЩИМ окном (build_market_data на каждом баре
    заново, окно ~120-300 баров) — фрактал на последних 2 барах окна
    в принципе не может быть найден (detect_fractals режет лукбэком,
    ровно как у Ганса). Значит "новый фрактал" узнаётся не мгновенно,
    а с честной задержкой в 2 бара — здесь используется РОВНО тот же
    md["fractals"]["last_up"/"last_down"], что уже даёт эту задержку
    сама build_market_data (то же поле читает _hans_breakout). Никакого
    дополнительного забегания вперёд не вносится.

    Новизну фрактала ловим по ДАТЕ (md["fractals"]["last_up"]["date"]),
    не по bar_index — индекс внутри окна меняется от вызова к вызову
    (окно скользит), а дата абсолютна и стабильна.

    state — тот же словарь ZigzagTracker.novoye_sostoyanie(), плюс два
    служебных поля "seen_up_date"/"seen_down_date" (эта функция сама
    их заводит) для отслеживания, какой фрактал уже обработан.
    """
    al = md.get("alligator", {}) or {}
    jaw, teeth, lips = al.get("jaw"), al.get("teeth"), al.get("lips")
    sleeping = al.get("sleeping", True)
    price = md.get("price", {}) or {}
    high, low = price.get("high"), price.get("low")
    date = md.get("bar_time")
    if jaw is None or teeth is None or lips is None or high is None or low is None:
        return None

    st = "sleeping" if sleeping else "opening/mature"
    di = jaw_direction(jaw, teeth, lips)
    bar = {"high": high, "low": low}

    fr = md.get("fractals", {}) or {}
    last_up = fr.get("last_up") or {}
    last_down = fr.get("last_down") or {}
    novy_up = (last_up.get("date") and last_up.get("date") != state.get("seen_up_date"))
    novy_down = (last_down.get("date") and last_down.get("date") != state.get("seen_down_date"))
    if last_up.get("date"):
        state["seen_up_date"] = last_up["date"]
    if last_down.get("date"):
        state["seen_down_date"] = last_down["date"]

    phase = state["phase"]

    def _fraktal_vne_pasti(fr_price, need_dir):
        kind = "LONG" if need_dir == "BEAR" else "SHORT"
        from williams_core import fractal_outside_jaw
        return fractal_outside_jaw(fr_price, jaw, kind)

    # ── ИЩУ_A ──
    if phase == ISCHU_A:
        for is_new, kind, frdict in ((novy_up, "UP", last_up),
                                     (novy_down, "DOWN", last_down)):
            if not is_new:
                continue
            need_dir = leg_direction_for_fractal(kind)
            if sleeping or di != need_dir:
                continue
            fr_price = frdict.get("price")
            if fr_price is None or not _fraktal_vne_pasti(fr_price, need_dir):
                continue
            state["a"] = {"extreme": fr_price, "dir": need_dir,
                          "start_date": frdict.get("date")}
            state["phase"] = VEDU_A
            return {"event": "LEG_A_START", "date": date, "dir": need_dir,
                    "price": fr_price, "fractal_date": frdict.get("date")}
        return None

    # ── ВЕДУ_A ──
    if phase == VEDU_A:
        leg = state["a"]
        if not sleeping and di == leg["dir"]:
            leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bar)
            return None
        state["phase"] = ZHDU_B
        return {"event": "LEG_A_CLOSE", "date": date, "dir": leg["dir"],
                "extreme": leg["extreme"], "start_date": leg["start_date"]}

    # ── ЖДУ_B ──
    if phase == ZHDU_B:
        need_dir = _PROTIVOPOLOZHNAYA[state["a"]["dir"]]
        is_new, frdict = (novy_up, last_up) if need_dir == "BEAR" else (novy_down, last_down)
        if not is_new or sleeping or di != need_dir:
            return None
        fr_price = frdict.get("price")
        if fr_price is None or not _fraktal_vne_pasti(fr_price, need_dir):
            return None
        state["b"] = {"extreme": fr_price, "dir": need_dir,
                      "start_date": frdict.get("date")}
        state["phase"] = VEDU_B
        return {"event": "LEG_B_START", "date": date, "dir": need_dir,
                "price": fr_price, "fractal_date": frdict.get("date")}

    # ── ВЕДУ_B ──
    if phase == VEDU_B:
        leg = state["b"]
        if not sleeping and di == leg["dir"]:
            leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bar)
            return None
        state["phase"] = ZHDU_POPYTKU_C
        return {"event": "LEG_B_CLOSE", "date": date, "dir": leg["dir"],
                "extreme": leg["extreme"], "start_date": leg["start_date"]}

    # ── ЖДУ_ПОПЫТКУ_C ──
    if phase == ZHDU_POPYTKU_C:
        need_dir = state["a"]["dir"]
        is_new, frdict = (novy_up, last_up) if need_dir == "BEAR" else (novy_down, last_down)
        if not is_new or sleeping or di != need_dir:
            return None
        fr_price = frdict.get("price")
        if fr_price is None or not _fraktal_vne_pasti(fr_price, need_dir):
            return None
        state["c"] = {"extreme": fr_price, "dir": need_dir,
                      "start_date": frdict.get("date"), "confirmed": False}
        state["phase"] = VEDU_POPYTKU_C
        return {"event": "C_ATTEMPT_START", "date": date, "dir": need_dir,
                "price": fr_price, "fractal_date": frdict.get("date")}

    # ── ВЕДУ_ПОПЫТКУ_C ──
    if phase == VEDU_POPYTKU_C:
        leg = state["c"]
        a_extreme = state["a"]["extreme"]
        if _cena_probila(leg["dir"], bar, a_extreme):
            leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bar)
            leg["confirmed"] = True
            state["phase"] = VEDU_PODTVERZHDENNUYU_C
            return {"event": "C_CONFIRMED", "date": date, "dir": leg["dir"],
                    "a_extreme": a_extreme, "c_start_date": leg["start_date"]}
        if not sleeping and di == leg["dir"]:
            leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bar)
            return None
        discarded = {"event": "C_DISCARDED", "date": date,
                    "reason": "пасть переплелась до пробоя ноги A",
                    "a_start_date": state["a"]["start_date"], "a_extreme": a_extreme}
        state["phase"] = ISCHU_A
        state["a"] = None
        state["b"] = None
        state["c"] = None
        return discarded

    # ── ВЕДУ_ПОДТВЕРЖДЁННУЮ_C ──
    if phase == VEDU_PODTVERZHDENNUYU_C:
        leg = state["c"]
        if not sleeping and di == leg["dir"]:
            leg["extreme"] = _obnovit_ekstremum(leg["extreme"], leg["dir"], bar)
            return None
        archived = {"event": "CYCLE_ARCHIVED", "date": date, "dir": leg["dir"],
                   "a": dict(state["a"]), "b": dict(state["b"]), "c": dict(leg)}
        state["phase"] = ISCHU_A
        state["a"] = None
        state["b"] = None
        state["c"] = None
        return archived

    return None


def _obnovit_ekstremum(current: float, direction: str, bar: dict) -> float:
    """Бегущий экстремум ноги: для BEAR (вниз) — новый минимум (low),
    для BULL (вверх) — новый максимум (high)."""
    if direction == "BEAR":
        return min(current, bar["low"])
    return max(current, bar["high"])


def _cena_probila(direction: str, bar: dict, a_extreme: float) -> bool:
    """Пробила ли ЦЕНА (интрабар — low/high, не только close) экстремум
    ноги A. BEAR (нога C идёт вниз, как и A): пробой = low < a_extreme.
    BULL: пробой = high > a_extreme."""
    if direction == "BEAR":
        return bar["low"] < a_extreme
    return bar["high"] > a_extreme


# ════════════════════════════════════════════════════════════
# ПОДГОТОВКА ВХОДНЫХ РЯДОВ — из настоящего williams_core.py
# ════════════════════════════════════════════════════════════

def podgotovit_ryady(bars: list, point: float):
    """
    Считает jaw/teeth/lips/bars_open по ВСЕЙ истории разом (нужно
    автомату, который идёт бар за баром) и карты фракталов с флагом
    "вне пасти" на каждом — используя НАСТОЯЩИЙ williams_core.py
    (_smma_series, detect_fractals, fractal_outside_jaw), не
    переписанную математику.

    Возвращает (jaw, teeth, lips, bars_open, up_by_idx, down_by_idx),
    где up_by_idx/down_by_idx: {bar_index: (price, вне_ли_пасти: bool)}.
    """
    from williams_core import _smma_series, detect_fractals, fractal_outside_jaw

    medians = [(b["high"] + b["low"]) / 2 for b in bars]
    jaw = _smma_series(medians, 13)
    teeth = _smma_series(medians, 8)
    lips = _smma_series(medians, 5)

    n = len(bars)
    open_threshold = 50 * point if point else 0.0005
    bars_open = [0] * n
    for i in range(n):
        j, t, l = jaw[i], teeth[i], lips[i]
        if j is None or t is None or l is None:
            bars_open[i] = 0
            continue
        spread = max(abs(j - t), abs(t - l), abs(j - l))
        if spread < open_threshold:
            bars_open[i] = 0
        else:
            bars_open[i] = (bars_open[i - 1] + 1) if i > 0 else 1

    fr = detect_fractals(bars)
    up_by_idx, down_by_idx = {}, {}
    for f in fr["all_up"]:
        idx = f["bar_index"]
        outside = jaw[idx] is not None and fractal_outside_jaw(f["price"], jaw[idx], "LONG")
        up_by_idx[idx] = (f["price"], outside)
    for f in fr["all_down"]:
        idx = f["bar_index"]
        outside = jaw[idx] is not None and fractal_outside_jaw(f["price"], jaw[idx], "SHORT")
        down_by_idx[idx] = (f["price"], outside)

    return jaw, teeth, lips, bars_open, up_by_idx, down_by_idx


def postroit_nogi(bars: list, point: float, start_idx: int = 0, end_idx: Optional[int] = None) -> list:
    """
    ⚠ ТОЛЬКО ДЛЯ АГРЕГАТНОЙ СТАТИСТИКИ ПО ИСТОРИИ (сколько волн всего,
    доля подтверждений и т.п.) — НЕ для боя и не для тестера!

    detect_fractals() здесь считается ОДИН РАЗ по всему массиву bars —
    значит на баре i эта функция уже "знает" фрактал, который в реальности
    подтверждается только 2 бара спустя (тот же лаг, что у Ганса). Даты
    событий в этом прогоне сдвинуты на 1-2 бара РАНЬШЕ честного момента.
    Для боя и для tester_express.py используйте on_bar_md() — она берёт
    md["fractals"]["last_up"/"last_down"] из build_market_data, которая
    уже честно режет последние баров лукбэком, без забегания вперёд
    (проверено 20.07 скользящим окном против этой же функции — тот же
    ноль событий на флэте, но даты волны после — на 1-2 бара позже).

    Прогоняет автомат по срезу истории [start_idx, end_idx] (по умолчанию —
    вся история) и возвращает список событий по порядку.
    """
    jaw, teeth, lips, bars_open, up_by_idx, down_by_idx = podgotovit_ryady(bars, point)
    if end_idx is None:
        end_idx = len(bars) - 1

    state = ZigzagTracker.novoye_sostoyanie()
    events = []
    for i in range(start_idx, end_idx + 1):
        ev = ZigzagTracker.on_bar(state, i, bars, jaw, teeth, lips, bars_open,
                                  up_by_idx, down_by_idx)
        if ev:
            events.append(ev)
    return events

# ZIGZAG_CORE_V1 - marker
