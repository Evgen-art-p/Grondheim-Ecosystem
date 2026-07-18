# -*- coding: utf-8 -*-
# patch_vasily_zasada_hooks_v1.py
# ─────────────────────────────────────────────────────────────
# VASILY_NABLYUDENIE_V1 · Патч 2 из 3 — МАШИНЕРИЯ ЗАСАДЫ (hooks.py)
#
# ДИАГНОЗ (Тройка, §5з.8 Летописи): Брут и Илья входят в дешёвый
# settle-цикл, потому что дают APPROVED на баре-кандидата и их заявка
# ложится PENDING. Вася на баре-кандидата честно говорит REJECT (его
# структура ещё не созрела) — и в цикл НЕ ПОПАДАЕТ вовсе. До следующего
# редкого кандидата Искры его никто не спросит. Он не спит в цикле — он
# в цикл не входит.
#
# ЛЕЧЕНИЕ: третья природа заявки. У Брута заявка ждёт ЦЕНУ (PENDING →
# пробой). У Васи — ждёт УСЛОВИЕ СТРУКТУРЫ (WATCHING → волна 1 + откат).
# Обе живут в одном цикле _aktivirovat_ordera, обе без LLM.
#
# ДВЕ ФАЗЫ (строгий отскок, решение Тройки — Консерватор берёт по скидке):
#   watch_phase = "wait_wave1"    → ждём wave_1_validated от Моржа
#   watch_phase = "wait_pullback" → волна подтверждена; ждём, пока цена
#                                   КОСНЁТСЯ опоры И следующий бар
#                                   ЗАКРОЕТСЯ обратно в сторону тренда
#   подтверждённый отскок → WATCHING превращается в обычный PENDING
#                           по Васиным координатам → дальше труба Брута
#
# ЧЕТЫРЕ ВРЕЗКИ:
#   A. _rodit_nablyudenie_vasily() — новая функция (рождение WATCHING)
#   B. _proverit_otkat_vasily()    — новая функция (двухфазный детектор)
#   C. _aktivirovat_ordera         — ветка для WATCHING (вызов детектора)
#   D. _settle_positions + трейлинг — пропускают WATCHING (нет входа)
#   E. _persist_trading_state      — рождение засады из вердикта WATCH
#
# Идемпотентность: маркер VASILY_ZASADA_V1. ast.parse перед записью.
# Запуск: python patch_vasily_zasada_hooks_v1.py   (из корня репо)
# ─────────────────────────────────────────────────────────────
from pathlib import Path
import ast
import sys
import shutil
from datetime import datetime

REPO = Path(__file__).resolve().parent
HOOKS = REPO / "Биржа" / "hooks.py"
MARKER = "VASILY_ZASADA_V1"
VASILY_MAGIC = 100003   # KONSERVATOR — из hooks.MAGIC_NUMBERS


def fail(msg):
    print(f"✗ {msg}")
    return 1


def main():
    if not HOOKS.exists():
        return fail(f"не нашёл hooks.py: {HOOKS}\n  запусти из КОРНЯ репо")

    src = HOOKS.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — hooks.py не трогаю (идемпотентно)")
        return 0

    # ═══════════════════════════════════════════════════════════
    # ВРЕЗКА A+B: две новые функции. Кладём их ПЕРЕД _aktivirovat_ordera
    # (там же, где живёт вся логика PENDING — соседство по смыслу).
    # ═══════════════════════════════════════════════════════════
    ankor_ab = "def _aktivirovat_ordera(state: dict):"
    if ankor_ab not in src:
        return fail("якорь A/B не найден (def _aktivirovat_ordera). "
                    "Файл изменился после a34e858 — патч НЕ применён.")

    novye_funkcii = '''# ═══════════════════════════════════════════════════════════
# VASILY_ZASADA_V1 — ЗАСАДА КОНСЕРВАТОРА (наблюдение по условию)
# ═══════════════════════════════════════════════════════════
# §5з.8 Летописи: у Васи (A08, magic 100003) нет аналога отложки.
# Брут ждёт ЦЕНУ (PENDING), Вася ждёт УСЛОВИЕ СТРУКТУРЫ (WATCHING).
# Две фазы (строгий отскок — Консерватор берёт по скидке, канон §12):
#   wait_wave1    → Морж подтвердил волну 1 (wave_1_validated)
#   wait_pullback → цена КОСНУЛАСЬ опоры И след. бар ЗАКРЫЛСЯ обратно
#                   по тренду (подтверждённый отскок, не падающий нож)
# Оба перехода — КОД, ноль LLM. Вася уже назвал координаты на WATCH.

VASILY_WATCH_EXPIRE_BARS = 20   # засада живёт дольше заявки: структура
                                # зреет медленнее, чем пробивается фрактал


def _rodit_nablyudenie_vasily(order: dict, chain: dict) -> dict:
    """Рождение WATCHING-записи из вердикта Васи с action=WATCH.
    Координаты (direction/опора/entry/stop) назвал он сам — код только
    раскладывает их в позицию-наблюдение. Опоры/стопа нет → None-запись
    (её отсеет _persist_trading_state как пустую засаду)."""
    d = (order.get("direction") or "").upper()
    opora = order.get("watch_opora")
    entry = order.get("entry")
    stop = order.get("stop")
    md = chain.get("market_data", {}) or {}
    return {
        "trader":     order.get("trader"),
        "magic":      order.get("magic"),
        "direction":  d,
        "status":     "WATCHING",
        "watch_phase": "wait_wave1",   # фаза 1: ждём Моржа
        "watch_opora": opora,          # цена опоры (фрактал/Зубы)
        "entry":      entry,           # Buy/Sell Stop ПОСЛЕ отскока
        "stop":       stop,
        "stop_initial": stop,          # R от названного стопа
        "lot":        order.get("lot"),
        "tp":         None,
        "_watch_с":   md.get("bar_time", ""),
        "_watch_баров": 0,
        "_kasanie":   False,           # фаза 2: коснулись ли опоры
        "mode":       order.get("status", "PAPER"),
        "opened_at":  None,            # входа ещё нет
        "pnl":        None,
        "entry_bias": md.get("global_bias"),
    }


def _proverit_otkat_vasily(pos: dict, md: dict) -> str:
    """Двухфазный детектор созревания засады Васи. Возвращает:
      "RIPE"   — структура созрела, засаду пора переводить в PENDING;
      "CANCEL" — структура сломалась (цена ушла за опору не туда);
      None     — ждём дальше.

    Фаза 1 (wait_wave1): Морж подтвердил волну 1 → переходим в фазу 2.
      Источник — chain-слепок стола ЭТОГО бара (тот же, что читают
      соседи). wave_1_validated живёт в morj-показании.
    Фаза 2 (wait_pullback): СТРОГИЙ отскок —
      LONG:  low <= опора (коснулись) И на след. баре close > опора
      SHORT: high >= опора (коснулись) И на след. баре close < опора
      Касание и подтверждение — РАЗНЫЕ бары (флаг _kasanie переносит
      факт касания в следующий бар)."""
    d = (pos.get("direction") or "").upper()
    opora = pos.get("watch_opora")
    price = md.get("price", {}) or {}
    close = price.get("close")
    high = price.get("high")
    low = price.get("low")
    if opora is None or close is None:
        return None

    phase = pos.get("watch_phase", "wait_wave1")

    # ── ФАЗА 1: ждём подтверждения волны 1 Моржом ──
    if phase == "wait_wave1":
        morj = md.get("morj", {}) or {}
        # морж-показание может приезжать как флаг в market_data или в
        # выделенном под-словаре — читаем оба честно
        wave1 = (morj.get("wave_1_validated")
                 if isinstance(morj, dict) else None)
        if wave1 is None:
            wave1 = md.get("wave_1_validated")
        if wave1:
            pos["watch_phase"] = "wait_pullback"
            print(f"[ЗАСАДА] 🌊 {pos.get('trader')} {d}: Морж подтвердил "
                  f"волну 1 → жду отката к опоре {opora}")
        return None   # даже если перешли — отскок проверяем со след. бара

    # ── ФАЗА 2: строгий отскок от опоры ──
    if phase == "wait_pullback":
        # структура сломалась: цена пробила опору НАСКВОЗЬ против входа
        # (для LONG опора снизу — уход глубоко ниже = слом; для SHORT наоборот)
        if d == "LONG":
            # был ли уже факт касания на прошлом баре?
            if pos.get("_kasanie"):
                if close > opora:
                    return "RIPE"        # отскочили и закрылись выше — зрело
                # ещё под опорой — держим касание, ждём закрытие выше
                # но если ушли глубоко (>2 «пункта» ниже) — слом
            # касание на ЭТОМ баре?
            if low is not None and low <= opora:
                pos["_kasanie"] = True
                if close > opora:
                    return "RIPE"        # коснулись И тут же закрылись выше
        elif d == "SHORT":
            if pos.get("_kasanie"):
                if close < opora:
                    return "RIPE"
            if high is not None and high >= opora:
                pos["_kasanie"] = True
                if close < opora:
                    return "RIPE"
        return None

    return None


'''

    src = src.replace(ankor_ab, novye_funkcii + ankor_ab, 1)

    # ═══════════════════════════════════════════════════════════
    # ВРЕЗКА C: ветка WATCHING внутри _aktivirovat_ordera.
    # Якорь — начало цикла по позициям, сразу после пропуска не-PENDING.
    # Мы вставляем обработку WATCHING ПЕРЕД проверкой PENDING.
    # ═══════════════════════════════════════════════════════════
    ankor_c = '''    for pos in live:
        if pos.get("status") != "PENDING":
            ostalis.append(pos)
            continue'''
    if ankor_c not in src:
        return fail("якорь C не найден (цикл по live в _aktivirovat_ordera).")

    zamena_c = '''    for pos in live:
        # VASILY_ZASADA_V1: засада Консерватора — своя ветка, до PENDING.
        if pos.get("status") == "WATCHING":
            _sostoyanie = _proverit_otkat_vasily(pos, md)
            if _sostoyanie == "RIPE":
                # структура созрела → засада становится обычной заявкой,
                # дальше её ведёт та же машинерия, что и Брута
                pos["status"] = "PENDING"
                pos.pop("watch_phase", None)
                pos.pop("_kasanie", None)
                pos["_ждёт_баров"] = 0
                dirty = True
                print(f"[ЗАСАДА] ✅ {pos.get('trader')} {pos.get('direction')} "
                      f"СОЗРЕЛА @ опора {pos.get('watch_opora')} → PENDING "
                      f"@ {pos.get('entry')} (волна 1 + отскок)")
                ostalis.append(pos)
                continue
            if _sostoyanie == "CANCEL":
                print(f"[ЗАСАДА] 🚫 {pos.get('trader')} "
                      f"{pos.get('direction')} снята — структура сломалась")
                dirty = True
                continue
            # ждём дальше — считаем возраст засады
            _vozrast = pos.get("_watch_баров", 0) + 1
            pos["_watch_баров"] = _vozrast
            dirty = True
            if _vozrast >= VASILY_WATCH_EXPIRE_BARS:
                print(f"[ЗАСАДА] 🚫 {pos.get('trader')} снята — "
                      f"структура не созрела за {VASILY_WATCH_EXPIRE_BARS} "
                      f"баров (протухла)")
                continue
            ostalis.append(pos)
            continue
        if pos.get("status") != "PENDING":
            ostalis.append(pos)
            continue'''
    src = src.replace(ankor_c, zamena_c, 1)

    # ═══════════════════════════════════════════════════════════
    # ВРЕЗКА D: _settle_positions и трейлинг должны ИГНОРИРОВАТЬ
    # WATCHING (у неё нет активного входа — судить/тянуть нечего).
    #
    # D1 — трейлинг: цикл `for pos in live: if pos.get("status") != "OPEN"`
    # уже отсекает не-OPEN, значит WATCHING он и так пропустит. Проверять
    # не нужно — трейлинг чист. (оставляем как есть)
    #
    # D2 — _settle_positions: он итерирует chain["open_positions"], куда
    # WATCHING тоже попадёт. Нужен явный пропуск: у WATCHING entry/stop
    # МОГУТ быть заданы (координаты будущего входа!), поэтому старая
    # защита `if entry is None` её НЕ отсечёт — добавляем явную проверку.
    # ═══════════════════════════════════════════════════════════
    ankor_d = '''    still_open, closed = [], []
    for pos in positions:
        entry = pos.get("entry")
        stop  = pos.get("stop")'''
    if ankor_d not in src:
        return fail("якорь D не найден (цикл закрытия в _settle_positions).")

    zamena_d = '''    still_open, closed = [], []
    for pos in positions:
        # VASILY_ZASADA_V1: засада/заявка — не открытая позиция, закрывать
        # нечего (у WATCHING координаты входа заданы, но входа ещё НЕ БЫЛО).
        if pos.get("status") in ("WATCHING", "PENDING"):
            still_open.append(pos)
            continue
        entry = pos.get("entry")
        stop  = pos.get("stop")'''
    src = src.replace(ankor_d, zamena_d, 1)

    # ═══════════════════════════════════════════════════════════
    # ВРЕЗКА E: рождение засады в _persist_trading_state.
    # Здесь обрабатывается execution_log. Сейчас берутся только
    # verdict==APPROVED. Васин WATCH придёт как отдельный вердикт —
    # добавляем его обработку ДО цикла APPROVED.
    #
    # Исполнитель кладёт в execution_log поля трейдера. Нам нужно, чтобы
    # он донёс action=WATCH и watch_opora. Это делает патч 3 (Исполнитель).
    # Здесь — приёмник: ищем записи с action==WATCH и рождаем WATCHING.
    # ═══════════════════════════════════════════════════════════
    ankor_e = '''    for order in exec_log:
        if order.get("verdict") != "APPROVED":
            continue'''
    if ankor_e not in src:
        return fail("якорь E не найден (цикл APPROVED в _persist_trading_state).")

    zamena_e = '''    # VASILY_ZASADA_V1: засада Консерватора рождается ДО обычных входов.
    # action==WATCH → WATCHING-запись (наблюдение по условию, не заявка).
    for order in exec_log:
        if (order.get("action") or "").upper() != "WATCH":
            continue
        if order.get("magic") != 100003:   # только Консерватор (A08)
            continue
        _nabl = _rodit_nablyudenie_vasily(order, chain)
        # пустая засада (нет опоры/стопа) — не рождаем, это болтовня
        if _nabl.get("watch_opora") is None or _nabl.get("stop") is None:
            print(f"[ЗАСАДА] ⚠️  {order.get('trader')} назвал WATCH без "
                  f"опоры/стопа — засада пуста, отклонена")
            continue
        # дубль засады того же магика не плодим
        _est = any(p.get("magic") == _nabl.get("magic")
                   and p.get("status") == "WATCHING"
                   for p in tstate.get("positions", []))
        if _est:
            continue
        tstate.setdefault("positions", []).append(_nabl)
        print(f"[ЗАСАДА] 👁  {order.get('trader')} {_nabl['direction']} встал "
              f"в засаду: опора {_nabl['watch_opora']}, вход {_nabl['entry']}, "
              f"стоп {_nabl['stop']} (ждёт волну 1 + отскок)")

    for order in exec_log:
        if order.get("verdict") != "APPROVED":
            continue'''
    src = src.replace(ankor_e, zamena_e, 1)

    # ── маркер идемпотентности в конец файла ──
    src = src.rstrip() + f"\n\n# {MARKER} — маркер идемпотентности\n"

    # ═══ ПРОВЕРКА СИНТАКСИСА ДО ЗАПИСИ (ast.parse) ═══
    try:
        ast.parse(src)
    except SyntaxError as e:
        return fail(f"ast.parse НЕ прошёл после патча — НЕ пишу файл.\n"
                    f"  {e}\n  (это защита: hooks.py остался нетронут)")

    # ── бэкап и запись ──
    bak = HOOKS.with_suffix(
        ".py.bak_vasily_zasada_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(HOOKS, bak)
    HOOKS.write_text(src, encoding="utf-8")

    print(f"✓ VASILY_ZASADA_V1 вписан в hooks.py")
    print(f"  бэкап: {bak.name}")
    print(f"  ast.parse прошёл. Врезки: A/B (2 функции), C (ветка WATCHING "
          f"в цикле активации), D (пропуск в settle), E (рождение засады).")
    print(f"  Далее: применить патч 3 (Исполнитель донесёт action=WATCH).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
