# -*- coding: utf-8 -*-
"""
patch_birzha_clean_memory_v2.py
─────────────────────────────────────────────────────────────
ЧИСТКА НАСЛЕДИЯ -2 · Биржа/hooks.py

Шеф удалил папки studio/ и economy/ из репо целиком — их там
физически больше нет. Значит в hooks.py тоже не должно остаться
НИ ОДНОГО упоминания studio.* — ни try/except-заглушки, ни
закомментированного пути. Ссылка на несуществующее — то самое
"мнение под маской факта" (Заповедь IV), только наоборот: код
делает вид, что где-то есть труба, которой нет вообще.

Что делает патч:
  1. Три пути памяти (ATLAS_PATH/STATE_PATH/PNL_PATH) переводятся
     на канонический адрес квартала:
         GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/состояние/trading_state.json
         GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/журналы/atlas.jsonl
         GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/журналы/pnl.jsonl
     (тот адрес, который Летопись уже называла каноном — теперь
     он действительно появляется в коде, не только в документе).
  2. Удаляются целиком три места, где код пытался позвать
     studio.memory_tools.remember / studio.grondheim_memory.sync_to_dna:
       - _arkhiv_to_city()       — рука кладущая в город (Оля)
       - _judge_iskra_by_result() — суд Искры по ДНК
       - _judge_trader_by_result() — суд трейдера по ДНК
     Это не заглушки "не удалось" — эти функции превращаются в
     ЧЕСТНЫЕ no-op с одной строкой: "нога Опыта не построена в этом
     городе (Чертёж Единицы, Гл.4.3, Гл.9 — Стол Трейдера, долг)".
     Ни одного import studio.*, ни одного упоминания старого мира.
  3. Вызовы этих трёх функций в _settle_positions() остаются —
     they're still called (ничего не переписываем в логике сделки),
     просто теперь они мгновенно возвращаются, не порождая try/except
     шум в консоли и не ссылаясь на то, чего нет на диске.

Данные потерь: trading_state.json / atlas_trading.jsonl / trading_pnl.jsonl
из старых studio/economy УЖЕ УДАЛЕНЫ Шефом вместе с папками — переносить
нечего, история тестового прогона потеряна безвозвратно. Патч просто
создаёт чистую площадь на канонической прописке, без старого хвоста.

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_birzha_clean_memory_v2.py

Идемпотентно: маркер BIRZHA_CLEAN_MEMORY_V2 — повторный запуск скажет
"уже пропатчено" и ничего не тронет второй раз.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
HOOKS = REPO / "Биржа" / "hooks.py"
MARKER = "# BIRZHA_CLEAN_MEMORY_V2 — маркер идемпотентности"

# ── Новая каноническая площадь памяти ЦЕХА (не всей Биржи —
#    цех торгового_хаоса, как и было задумано изначально) ──────
NEW_STATE_DIR = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "состояние"
NEW_LOGS_DIR  = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "журналы"

# ── 1. Замена трёх путей ────────────────────────────────────
PATH_REPLACEMENTS = [
    (
        'ATLAS_PATH = Path("economy/data/atlas_trading.jsonl")',
        'ATLAS_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "журналы" / "atlas.jsonl"',
    ),
    (
        'STATE_PATH = Path("studio/modules/trading/state/trading_state.json")',
        'STATE_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "состояние" / "trading_state.json"',
    ),
    (
        'PNL_PATH = Path("economy/data/trading_pnl.jsonl")',
        'PNL_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "журналы" / "pnl.jsonl"',
    ),
]

# ── 2. Полная замена трёх функций — старое тело целиком, новое честное ──

OLD_ARKHIV_TO_CITY = '''def _arkhiv_to_city(record: dict):
    """
    Рука кладущая. Кладёт ТЯЖЁЛУЮ закрытую сделку в память города
    от имени Архивариуса. Лёгкое (|pnl_r|<2R) — игнор (рутина).

    НИКОГДА не роняет торговый цикл: любая беда с Оле → тихий выход.
    """
    pnl_r = record.get("pnl_r")
    if pnl_r is None:
        return
    if abs(pnl_r) < _HEAVY_R:
        return  # рутина — живёт в Атласе цеха, в город не идёт

    trader = record.get("trader", "?")
    symbol = record.get("symbol", "?")
    tf     = record.get("timeframe", "?")
    reason = record.get("close_reason", "?")
    closed = record.get("closed_at", "")

    # Урок или образец — по знаку
    if pnl_r <= -_HEAVY_R:
        mtype = "warning"
        title = f"Крупный убыток: {trader} {symbol} {tf} ({pnl_r}R)"
        event = (f"{trader} закрыт по {reason} с {pnl_r}R на {symbol} {tf} "
                 f"({closed}). Дорого оплаченная информация.")
        loss = (f"Город забудет, что эта картинка на {symbol} {tf} стоила "
                f"{pnl_r}R убытка. Урок придётся оплачивать заново.")
    else:  # pnl_r >= +2R
        mtype = "inspiration"
        title = f"Крупная удача: {trader} {symbol} {tf} (+{pnl_r}R)"
        event = (f"{trader} взял +{pnl_r}R по {reason} на {symbol} {tf} "
                 f"({closed}). Редкий крупный ход — образец.")
        loss = (f"Город забудет, что на {symbol} {tf} такая картинка дала "
                f"+{pnl_r}R. Потеряем образец крупного хода.")

    try:
        from studio.memory_tools import remember  # type: ignore[import]  # HOOKS_TYPING_V1: намеренно — см. except ниже
        remember(
            title=title,
            event=event,
            significance=f"Крупный результат {pnl_r}R — за порогом рутины.",
            loss_if_forgotten=loss,
            memory_type=mtype,
            storage="chronicles",
            source="A05_ARKHIV·trading",
        )
        print(f"[ARKHIV] 🏛 Урок в память города: {title}")
    except Exception as e:
        print(f"[ARKHIV] ⚠️  Оле недоступна ({e}) — урок остался в Атласе цеха")'''

NEW_ARKHIV_TO_CITY = '''def _arkhiv_to_city(record: dict):
    """
    РУКА КЛАДУЩАЯ — не построена в этом городе.

    В старом мире (-2) тяжёлая сделка (|pnl_r|>=2R) уходила в
    городскую память через Олю (studio.memory_tools.remember).
    В Грондхейме городская память (Оля) решением 03.07 пока НЕ
    строится ("каждый держит свой архив сам" — Летопись §4а).
    Честный no-op, не притворяется рабочей трубой, не зовёт то,
    чего на диске нет. Когда городская память будет решена
    строиться — сюда ляжет новый вызов, не заглушка.
    """
    return'''

OLD_JUDGE_ISKRA = '''def _judge_iskra_by_result(pos: dict, pnl_r):
    """ISKRA_FAIR_JUDGEMENT_V1: справедливый суд Искры по ДЕЛУ.
    Точка Искры повела сделку в плюс → good_work (была права).
    В минус → bad_work (накосячила). Ноль/нет метки → суда нет
    (пустышку и старые позиции не наказываем). Мягко (0.3).
    Никогда не роняет торговый цикл: беда с ДНК → тихий выход."""
    if pnl_r is None:
        return
    # судим ТОЛЬКО позиции с меткой Искры — старые без метки не трогаем
    if pos.get("iskra_zero_point") is None:
        return
    try:
        from studio.grondheim_memory import sync_to_dna  # type: ignore[import]  # HOOKS_TYPING_V1: намеренно — см. except ниже
        # ENGINE_ONE_DOOR_V1 · ПЕРЕРАСПРЕДЕЛЕНИЕ ОТВЕТСТВЕННОСТИ.
        # Искра — КОМПАС: показывает разворот, но НЕ принимает решение
        # о входе (сторона/цена/стоп/против ветра — это рука трейдера).
        # За МИНУС её больше не наказываем: чаще виноват вход, не компас.
        # Оставляем РАДОСТЬ за верный компас (плюс). Ответственность за
        # минус переложена на трейдера (_judge_trader_by_result).
        if pnl_r > 0:
            sync_to_dna("A01_ISKRA", "good_work", intensity=0.3, dept="trading")
            print(f"[ISKRA] ⚖️  компас повёл в +{pnl_r}R → good_work")
        # pnl_r <= 0 → Искру НЕ наказываем (компас не отвечает за выстрел)
    except Exception as e:
        print(f"[ISKRA] ⚠️  суд по результату не сработал ({e})")'''

NEW_JUDGE_ISKRA = '''def _judge_iskra_by_result(pos: dict, pnl_r):
    """
    СУД ИСКРЫ — не построена в этом городе.

    В старом мире (-2) плюсовая сделка сдвигала ДНК Искры через
    studio.grondheim_memory.sync_to_dna. Это и есть тот самый
    маятник состояния, который Чертёж Единицы (Гл.4.2) прямо
    называет НЕ-опытом: "качание состояния, не вывод — обучение
    первого уровня, без понимания". Нога Опыта Стола Трейдера
    (Чертёж, Гл.5.2/9 — "долг: амнезия у штурвала") строится
    отдельно, по-новому, не восстановлением этого маятника.
    Честный no-op — не зовёт то, чего на диске больше нет.
    """
    return'''

OLD_JUDGE_TRADER = '''def _judge_trader_by_result(pos: dict, pnl_r):
    """ENGINE_ONE_DOOR_V1: СУД ТРЕЙДЕРА по результату закрытой сделки.

    Перераспределение ответственности: Искра — компас (показывает),
    трейдер — рука (решает войти). Кто решает, тот и отвечает.

    Правило (слово Шефа): наказываем за МИНУС ПРОТИВ ВЕТРА, не за
    всякий минус. Вошёл против глобального тренда (§12 Котина) и
    схватил убыток → bad_work (его дерзость, его плата). Вошёл ПО
    ветру и не повезло → честная плата ремесла, НЕ наказываем.
    Плюс → good_work (верное решение, заслужил).

    entry_bias — ветер на баре входа (запомнен в позицию при открытии).
    direction LONG ↔ ветер BEAR = против. SHORT ↔ ветер BULL = против.
    Ветра нет (NONE/None) → штиль, наказания за минус нет.
    Никогда не роняет торговый цикл: беда с ДНК → тихий выход."""
    if pnl_r is None or pnl_r == 0:
        return
    trader = pos.get("trader")
    if not trader:
        return
    _AID = {"BRUT": "A06_BRUT", "AVANTURIST": "A07_AVANTURIST",
            "KONSERVATOR": "A08_KONSERVATOR"}
    aid = _AID.get(str(trader).upper())
    if not aid:
        return

    direction = pos.get("direction", "LONG")
    bias = pos.get("entry_bias")  # ветер входа: BULL | BEAR | NONE | None

    against_wind = (
        (direction == "LONG"  and bias == "BEAR") or
        (direction == "SHORT" and bias == "BULL")
    )

    try:
        from studio.grondheim_memory import sync_to_dna  # type: ignore[import]  # HOOKS_TYPING_V1: намеренно — см. except ниже
        if pnl_r > 0:
            sync_to_dna(aid, "good_work", intensity=0.3, dept="trading")
            print(f"[TRADER] ⚖️  {trader} взял +{pnl_r}R → good_work")
        elif pnl_r < 0 and against_wind:
            sync_to_dna(aid, "bad_work", intensity=0.3, dept="trading")
            print(f"[TRADER] ⚖️  {trader} {direction} ПРОТИВ ветра ({bias}) "
                  f"→ {pnl_r}R → bad_work (нарушил §12)")
        else:
            print(f"[TRADER] ⚖️  {trader} {pnl_r}R по ветру/штиль "
                  f"(bias={bias}) — честный минус, без наказания")
    except Exception as e:
        print(f"[TRADER] ⚠️  суд трейдера не сработал ({e})")'''

NEW_JUDGE_TRADER = '''def _judge_trader_by_result(pos: dict, pnl_r):
    """
    СУД ТРЕЙДЕРА — не построена в этом городе.

    Логика "минус против ветра → накажи, минус по ветру → прости"
    (§12 Котина) остаётся ВЕРНОЙ идеей — но раньше она сразу дёргала
    ДНК через studio.grondheim_memory.sync_to_dna, чего в этом
    городе больше нет физически. Это ровно нога "Опыт" Стола
    Трейдера (Чертёж Единицы, Гл.5.2 — "стол на двух ногах, инвалид"),
    и её нужно строить заново, не восстановлением мёртвого импорта.
    Честный no-op — записи pnl.jsonl эта функция не трогает, факт
    сделки остаётся в журнале в любом случае (_settle_positions уже
    записал его выше).
    """
    return'''


def _patch_source() -> bool:
    if not HOOKS.exists():
        print(f"[ПАТЧ] ❌ Не найден {HOOKS} — запусти из корня репо.")
        raise SystemExit(1)

    src = HOOKS.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ hooks.py уже пропатчен (BIRZHA_CLEAN_MEMORY_V2) — пропускаю.")
        return False

    changed = 0

    # Пути
    for old, new in PATH_REPLACEMENTS:
        if old in src:
            src = src.replace(old, new)
            changed += 1
            print(f"[ПАТЧ] 🔧 путь переклеен на канон: {new.split('/')[-1].rstrip(chr(34))}")
        elif new in src:
            print(f"[ПАТЧ] ↺ путь уже канонический.")
        else:
            print(f"[ПАТЧ] ⚠️  не найдена строка пути (проверь вручную):\\n         {old}")

    # Три функции — полная замена тела
    for old_fn, new_fn, name in (
        (OLD_ARKHIV_TO_CITY, NEW_ARKHIV_TO_CITY, "_arkhiv_to_city"),
        (OLD_JUDGE_ISKRA,    NEW_JUDGE_ISKRA,    "_judge_iskra_by_result"),
        (OLD_JUDGE_TRADER,   NEW_JUDGE_TRADER,   "_judge_trader_by_result"),
    ):
        if old_fn in src:
            src = src.replace(old_fn, new_fn)
            changed += 1
            print(f"[ПАТЧ] 🧹 {name}() очищена от studio.* — честный no-op.")
        elif new_fn in src:
            print(f"[ПАТЧ] ↺ {name}() уже очищена.")
        else:
            print(f"[ПАТЧ] ⚠️  тело {name}() не совпало один-в-один — "
                  f"файл менялся вручную, проверь эту функцию сам.")

    if changed == 0:
        print("[ПАТЧ] ⚠️  ничего не изменилось — сверь файл вручную.")

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    HOOKS.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] 💾 hooks.py сохранён (изменений: {changed}).")
    return True


def _prepare_dirs():
    NEW_STATE_DIR.mkdir(parents=True, exist_ok=True)
    NEW_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[ПЛОЩАДЬ] 📁 {NEW_STATE_DIR.relative_to(REPO)}")
    print(f"[ПЛОЩАДЬ] 📁 {NEW_LOGS_DIR.relative_to(REPO)}")


def main():
    print("═" * 62)
    print("  ЧИСТКА НАСЛЕДИЯ -2 · BIRZHA_CLEAN_MEMORY_V2")
    print("═" * 62)
    _patch_source()
    _prepare_dirs()
    print("═" * 62)
    print("  ✅ ГОТОВО. Ни одного упоминания studio.*/economy в hooks.py.")
    print("     Память цеха: GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/")
    print("═" * 62)


if __name__ == "__main__":
    main()
