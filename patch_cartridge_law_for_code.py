# -*- coding: utf-8 -*-
"""
Патч: Закон Картриджа — теперь и для КОДА, не только для промптов.

ПРОБЛЕМА (честно, как есть): iskra_live.py лежал в Биржа/ — в одном
дереве репо, а его промпт (слоты/A01/промпт.md) — в другом
(GRONDHEIM_CITY/.../торговый_хаос/слоты/A01/). Мозг слота и его
промпт — одна сущность, разорванная на два дерева. Никакое
раскладывание по папкам это не лечит (Шеф прав — "хер ты разделишь").

РЕШЕНИЕ: мозг слота переезжает В СЛОТ, рядом с промптом.
  ДО:  Биржа/iskra_live.py
  ПОСЛЕ: GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A01/мозг.py

Кабинет (ui_torg.py) перестаёт хардкодить "from iskra_live import
run_iskra" и подобное для всех 9 агентов. Вместо этого — один честный
загрузчик _slot_brain(ceh_id, slot): открывает слоты/{slot}/мозг.py
ПРЯМО ПО ПУТИ (importlib, без создания пакета), кэширует на процесс.
Родится Морж — кладёшь его мозг.py в слоты/A02/, кабинет подхватит
сам, ни одной правки кода. Это и есть Закон Картриджа для кода, а не
просто for показухи в комментарии.

В Биржа/ остаётся только то, что ДЕЙСТВИТЕЛЬНО общее для всех цехов
и слотов: williams_core.py, mt5_feed.py, hooks.py, feed_source.py,
global_anchor.py, tester_express.py, llm.py, billing_ledger.py,
cartridge_registry.py, ui_torg.py. Никаких "движок/агенты" —
это была моя выдумка, ей не соответствовал ни один манифест.

Идемпотентен: повторный запуск ничего не меняет и не падает.
"""
import sys
import re
import py_compile
import shutil
from pathlib import Path
from datetime import datetime

REPO = Path(".").resolve()

OLD_BRAIN_PATH = REPO / "Биржа" / "iskra_live.py"
NEW_BRAIN_DIR  = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / "A01"
NEW_BRAIN_PATH = NEW_BRAIN_DIR / "мозг.py"
UI_TORG_PATH   = REPO / "Биржа" / "ui_torg.py"


# ════════════════════════════════════════════════════════════
# ШАГ 1 — переезд мозга Искры в слот + починка путей внутри файла
# ════════════════════════════════════════════════════════════

def move_iskra_brain():
    if NEW_BRAIN_PATH.exists() and not OLD_BRAIN_PATH.exists():
        print("[1/2] Мозг Искры уже в слоте — идемпотентность держит.")
        return

    if not OLD_BRAIN_PATH.exists():
        print(f"[1/2] НЕ НАЙДЕН: {OLD_BRAIN_PATH} — переезд уже был или файл ещё не доставлен.")
        return

    src = OLD_BRAIN_PATH.read_text(encoding="utf-8")

    old_block = '''_HERE        = Path(__file__).resolve().parent           # Биржа/
_REPO        = _HERE.parent                                # корень репо
# НОВЫЙ ГОРОД: промпт роли — собственность ЦЕХА (манифест торгового_хаоса
# уже объявляет слоты/A01/промпт.md), не резидента и не старой плоской
# папки A01/. Кто сидит на слоте — решает mask.json (Закон Пары), не этот
# файл. Знания (WILLIAMS_MATH.md) — рядом со слотом, тот же приём.
_CEH_DIR     = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
PROMPT_PATH  = _CEH_DIR / "слоты" / "A01" / "промпт.md"
KNOWLEDGE    = _CEH_DIR / "слоты" / "A01" / "знания" / "WILLIAMS_MATH.md"
STATE_DIR    = _HERE / "данные"
STATS_PATH   = STATE_DIR / "iskra_stats.json"         # накопительная статистика (наш слой)'''

    new_block = '''# ЗАКОН КАРТРИДЖА ДЛЯ КОДА: этот файл живёт ПРЯМО В СЛОТЕ, рядом со
# своим промптом и знаниями — не в отдельном дереве репо-кода. Слот
# несёт с собой ВСЁ: слоты/A01/{мозг.py, промпт.md, знания/, данные/}.
_SLOT_DIR    = Path(__file__).resolve().parent            # слоты/A01/
_CEH_DIR     = _SLOT_DIR.parent.parent                     # торговый_хаос/
_REPO        = _CEH_DIR.parents[3]                          # корень репо
_BIRZHA_CODE = _REPO / "Биржа"                              # общий код (движок, llm)

PROMPT_PATH  = _SLOT_DIR / "промпт.md"
KNOWLEDGE    = _SLOT_DIR / "знания" / "WILLIAMS_MATH.md"
# Точность датчика — личный журнал РОЛИ (Ролик §4.4а), едет со слотом.
STATE_DIR    = _SLOT_DIR / "данные"
STATS_PATH   = STATE_DIR / "iskra_stats.json"
# feed_config.json — общий вочлист всех символов/цехов, НЕ личное
# слота. Ему место в общем коде, не в А01.
_SHARED_DATA = _BIRZHA_CODE / "данные"'''

    if old_block not in src:
        print("[1/2] ⚠️  Ожидаемый блок путей не найден — файл менялся с момента диагностики.")
        print("      Переезд отменён, ничего не трогаю вслепую.")
        sys.exit(1)

    src = src.replace(old_block, new_block)

    # Единственное место, где STATE_DIR использовался для ЧУЖОГО (общего)
    # feed_config.json — переключаем на _SHARED_DATA, чтобы не искать
    # общий вочлист внутри личной папки слота.
    src = src.replace(
        'cfg_path = STATE_DIR / "feed_config.json"',
        'cfg_path = _SHARED_DATA / "feed_config.json"',
    )

    # Общий код (williams_core, mt5_feed, hooks, llm...) остаётся в
    # Биржа/ — слоту нужно видеть его в sys.path, раз сам слот теперь
    # далеко в GRONDHEIM_CITY. Заплатка САМОДОСТАТОЧНА (не зависит от
    # _BIRZHA_CODE, который определяется НИЖЕ по файлу) — считает путь
    # сама от собственного __file__, до слота: A01→слоты→торговый_хаос→
    # цеха→Биржа(city)→GRONDHEIM_CITY→корень репо (5 уровней вверх).
    sys_path_shim = '''import sys as _sys
_repo_root_shim = Path(__file__).resolve().parents[6]
_birzha_code_shim = _repo_root_shim / "Биржа"
if str(_birzha_code_shim) not in _sys.path:
    _sys.path.insert(0, str(_birzha_code_shim))

'''
    src = src.replace(
        "from llm import chat\n",
        sys_path_shim + "from llm import chat\n",
        1,
    )

    NEW_BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    NEW_BRAIN_PATH.write_text(src, encoding="utf-8")
    py_compile.compile(str(NEW_BRAIN_PATH), doraise=True)
    print(f"[1/2] ✅ Мозг Искры переехал: {NEW_BRAIN_PATH.relative_to(REPO)}")

    OLD_BRAIN_PATH.unlink()
    print(f"[1/2] 🗑  Старый файл удалён: {OLD_BRAIN_PATH.relative_to(REPO)}")


# ════════════════════════════════════════════════════════════
# ШАГ 2 — кабинет: динамический загрузчик мозгов слотов
# ════════════════════════════════════════════════════════════

_SLOT_BRAIN_HELPER = '''import importlib.util

_BRAIN_CACHE = {}


def _slot_brain(ceh_id: str, slot: str):
    """Закон Картриджа для кода: мозг слота живёт РЯДОМ с промптом
    (слоты/{slot}/мозг.py) — кабинет не хардкодит имена модулей, а
    спрашивает у цеха, что там реально лежит. Нет файла — честная
    вакансия мозга (None), не ошибка. Кэш на процесс — не грузим
    заново на каждый клик."""
    key = (ceh_id, slot)
    if key in _BRAIN_CACHE:
        return _BRAIN_CACHE[key]
    brain_path = (_REPO / "GRONDHEIM_CITY" / KVARTAL / "цеха" / ceh_id
                 / "слоты" / slot / "мозг.py")
    if not brain_path.exists():
        _BRAIN_CACHE[key] = None
        return None
    spec = importlib.util.spec_from_file_location(
        f"_brain_{ceh_id}_{slot}", brain_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _BRAIN_CACHE[key] = mod
    return mod

'''


def patch_ui_torg():
    if not UI_TORG_PATH.exists():
        print(f"[2/2] НЕ НАЙДЕН: {UI_TORG_PATH}")
        sys.exit(1)

    src = UI_TORG_PATH.read_text(encoding="utf-8")

    if "_slot_brain(" in src and "_BRAIN_CACHE" in src:
        print("[2/2] Кабинет уже подключён к динамическому загрузчику — идемпотентность держит.")
        return

    backup = UI_TORG_PATH.with_suffix(f".py.bak_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(UI_TORG_PATH, backup)
    print(f"[2/2] Бэкап: {backup.relative_to(REPO)}")

    anchor = "import cartridge_registry as reg\n"
    if anchor not in src:
        print("[2/2] ⚠️  Не нашёл якорь импорта cartridge_registry — файл изменился.")
        sys.exit(1)
    src = src.replace(anchor, anchor + "\n" + _SLOT_BRAIN_HELPER, 1)

    replacements = [
        # ── Искра (A01) ──
        (
            'from iskra_live import run_iskra\n'
            '            result = await asyncio.get_event_loop().run_in_executor(\n'
            '                None, lambda: run_iskra(symbol="XAUUSD", timeframe="H4"))',
            '_brain = _slot_brain("торговый_хаос", "A01")\n'
            '            if _brain is None:\n'
            '                raise RuntimeError("мозг A01 ещё не в слоте")\n'
            '            result = await asyncio.get_event_loop().run_in_executor(\n'
            '                None, lambda: _brain.run_iskra(symbol="XAUUSD", timeframe="H4"))'
        ),
        # ── Морж (A02) ──
        (
            'from morj_live import run_morj\n'
            '                mr = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: run_morj(symbol="XAUUSD", timeframe="H4"))',
            '_brain = _slot_brain("торговый_хаос", "A02")\n'
            '                if _brain is None:\n'
            '                    raise RuntimeError("мозг A02 ещё не в слоте")\n'
            '                mr = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: _brain.run_morj(symbol="XAUUSD", timeframe="H4"))'
        ),
        # ── Паникёр (A03) ──
        (
            'from panikyor_live import run_panikyor\n'
            '                pr = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: run_panikyor(symbol="XAUUSD", timeframe="H4"))',
            '_brain = _slot_brain("торговый_хаос", "A03")\n'
            '                if _brain is None:\n'
            '                    raise RuntimeError("мозг A03 ещё не в слоте")\n'
            '                pr = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: _brain.run_panikyor(symbol="XAUUSD", timeframe="H4"))'
        ),
        # ── Ганс (A04) ──
        (
            'from hans_live import run_hans\n'
            '                hr = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: run_hans(symbol="XAUUSD", timeframe="H4"))',
            '_brain = _slot_brain("торговый_хаос", "A04")\n'
            '                if _brain is None:\n'
            '                    raise RuntimeError("мозг A04 ещё не в слоте")\n'
            '                hr = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: _brain.run_hans(symbol="XAUUSD", timeframe="H4"))'
        ),
        # ── Архивариус (A05, контора) ──
        (
            'from arkhiv_live import run_arkhiv\n'
            '                ar = await asyncio.get_event_loop().run_in_executor(None, lambda: run_arkhiv())',
            '_brain = _slot_brain("контора", "архивариус")\n'
            '                if _brain is None:\n'
            '                    raise RuntimeError("мозг архивариуса ещё не в слоте")\n'
            '                ar = await asyncio.get_event_loop().run_in_executor(None, lambda: _brain.run_arkhiv())'
        ),
        # ── Исполнитель (A09, контора) ──
        (
            'from executor_live import run_executor\n'
            '                rex = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: run_executor(symbol="XAUUSD", timeframe="H4"))',
            '_brain = _slot_brain("контора", "исполнитель")\n'
            '                if _brain is None:\n'
            '                    raise RuntimeError("мозг исполнителя ещё не в слоте")\n'
            '                rex = await asyncio.get_event_loop().run_in_executor(\n'
            '                    None, lambda: _brain.run_executor(symbol="XAUUSD", timeframe="H4"))'
        ),
        # ── чат с Искрой ──
        (
            'from iskra_live import chat_with_iskra\n'
            '            dialog = [m for m in state["chat_history"]\n'
            '                      if m.get("role") in ("user", "assistant") and m.get("content")]\n'
            '            reply = await asyncio.get_event_loop().run_in_executor(\n'
            '                None, lambda: chat_with_iskra(msg, state.get("iskra_last_run"), dialog))',
            '_brain = _slot_brain("торговый_хаос", "A01")\n'
            '            if _brain is None:\n'
            '                raise RuntimeError("мозг A01 ещё не в слоте")\n'
            '            dialog = [m for m in state["chat_history"]\n'
            '                      if m.get("role") in ("user", "assistant") and m.get("content")]\n'
            '            reply = await asyncio.get_event_loop().run_in_executor(\n'
            '                None, lambda: _brain.chat_with_iskra(msg, state.get("iskra_last_run"), dialog))'
        ),
    ]

    missing = []
    for old, new in replacements:
        if old not in src:
            missing.append(old[:70])
            continue
        src = src.replace(old, new, 1)
    if missing:
        print("[2/2] ⚠️  Не нашёл фрагменты (файл менялся?), пропущены:")
        for m in missing:
            print("      ", m)

    # ── торговцы (A06/A07/A08) — цикл с importlib.import_module ──
    old_traders = '''                try:
                    import importlib
                    _mod = importlib.import_module(tr["mod"])
                    _run = getattr(_mod, tr["run"])
                    rt = await asyncio.get_event_loop().run_in_executor(
                        None, lambda _r=_run: _r(symbol="XAUUSD", timeframe="H4"))
                except Exception as e:
                    ui.notify(f"{tr['icon']} {_nm} не сел: {e}", type="negative")
                    continue'''
    new_traders = '''                try:
                    _brain = _slot_brain("торговый_хаос", tr["id"])
                    if _brain is None:
                        raise RuntimeError(f"мозг {tr['id']} ещё не в слоте")
                    _run = getattr(_brain, tr["run"])
                    rt = await asyncio.get_event_loop().run_in_executor(
                        None, lambda _r=_run: _r(symbol="XAUUSD", timeframe="H4"))
                except Exception as e:
                    ui.notify(f"{tr['icon']} {_nm} не сел: {e}", type="negative")
                    continue'''
    if old_traders in src:
        src = src.replace(old_traders, new_traders, 1)
    else:
        print("[2/2] ⚠️  Не нашёл блок трейдеров (A06-A08) — пропущен.")

    # ── _chat_map (A02-A09) — теперь (ceh_id, slot, fn_name, last_key, icon) ──
    old_chat_map = '''        _chat_map = {
            "A02": ("morj_live", "chat_with_morj", "morj_last_run", "🦭"),
            "A03": ("panikyor_live", "chat_with_panikyor", "panic_last_run", "😱"),
            "A04": ("hans_live", "chat_with_hans", "hans_last_run", "🎯"),
            "A05": ("arkhiv_live", "chat_with_arkhiv", "arkhiv_last_run", "📚"),
            "A06": ("brut_live", "chat_with_brut", "brut_last_run", "🪨"),
            "A07": ("avan_live", "chat_with_avan", "avan_last_run", "🎲"),
            "A08": ("cons_live", "chat_with_cons", "cons_last_run", "⚖️"),
            "A09": ("executor_live", "chat_with_executor", "executor_last_run", "🎬"),
        }'''
    new_chat_map = '''        _chat_map = {
            "A02": ("торговый_хаос", "A02", "chat_with_morj", "morj_last_run", "🦭"),
            "A03": ("торговый_хаос", "A03", "chat_with_panikyor", "panic_last_run", "😱"),
            "A04": ("торговый_хаос", "A04", "chat_with_hans", "hans_last_run", "🎯"),
            "A05": ("контора", "архивариус", "chat_with_arkhiv", "arkhiv_last_run", "📚"),
            "A06": ("торговый_хаос", "A06", "chat_with_brut", "brut_last_run", "🪨"),
            "A07": ("торговый_хаос", "A07", "chat_with_avan", "avan_last_run", "🎲"),
            "A08": ("торговый_хаос", "A08", "chat_with_cons", "cons_last_run", "⚖️"),
            "A09": ("контора", "исполнитель", "chat_with_executor", "executor_last_run", "🎬"),
        }'''
    if old_chat_map in src:
        src = src.replace(old_chat_map, new_chat_map, 1)
    else:
        print("[2/2] ⚠️  Не нашёл _chat_map — пропущен.")

    old_chat_call = '''        if agent_id in _chat_map:
            _mod_name, _fn_name, _last_key, _ic = _chat_map[agent_id]
            ui.notify(f"{_ic} {label} думает...", type="info")
            try:
                import importlib
                _m = importlib.import_module(_mod_name)
                _chat = getattr(_m, _fn_name)
                dialog = [m for m in state["chat_history"]
                          if m.get("role") in ("user", "assistant") and m.get("content")]
                reply = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _chat(msg, state.get(_last_key), dialog))
            except Exception as e:
                reply = f"⚠️ {label} не смог(ла) ответить: {e}"'''
    new_chat_call = '''        if agent_id in _chat_map:
            _ceh_id, _slot, _fn_name, _last_key, _ic = _chat_map[agent_id]
            ui.notify(f"{_ic} {label} думает...", type="info")
            try:
                _brain = _slot_brain(_ceh_id, _slot)
                if _brain is None:
                    raise RuntimeError(f"мозг {_slot} ещё не в слоте")
                _chat = getattr(_brain, _fn_name)
                dialog = [m for m in state["chat_history"]
                          if m.get("role") in ("user", "assistant") and m.get("content")]
                reply = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _chat(msg, state.get(_last_key), dialog))
            except Exception as e:
                reply = f"⚠️ {label} не смог(ла) ответить: {e}"'''
    if old_chat_call in src:
        src = src.replace(old_chat_call, new_chat_call, 1)
    else:
        print("[2/2] ⚠️  Не нашёл вызов _chat_map — пропущен.")

    UI_TORG_PATH.write_text(src, encoding="utf-8")
    py_compile.compile(str(UI_TORG_PATH), doraise=True)
    print("[2/2] ✅ Кабинет переключён на динамический загрузчик мозгов слотов.")


def main():
    move_iskra_brain()
    patch_ui_torg()
    print("\nГотово. Мозг слота = слоты/{id}/мозг.py, кабинет их находит сам.")
    print("Родится Морж — просто кладёшь слоты/A02/мозг.py, в ui_torg.py лезть не нужно.")


if __name__ == "__main__":
    main()
