# -*- coding: utf-8 -*-
# patch_hooks_typing.py — HOOKS_TYPING_V1
# ─────────────────────────────────────────────────────────────
# Закрывает 6 ошибок Pylance в Биржа/hooks.py. ТРИ независимых корня:
#
# КОРЕНЬ 1 (1 ошибка, строка 521): arkhiv_live.
#   Уже безопасно обёрнут в try/except с реальным запасным расчётом
#   ("старый расчёт" вместо движка) — не падает. НО: файла arkhiv_live.py
#   больше нет нигде (переименован в мозг.py), значит except срабатывает
#   ВСЕГДА — движковый build_digest никогда не используется, даже когда
#   Шеф положит мозг архивариуса на место. Порчу через _slot_brain
#   (тот же механизм, что в ui_torg.py/tester_express.py). Проверено:
#   GRONDHEIM_CITY/Биржа/цеха/контора/слоты/архивариус/ ФИЗИЧЕСКИ ещё
#   не существует в репо — сегодня это по-прежнему честная вакансия
#   (None → тот же "старый расчёт"), но заработает само, как только
#   слот появится. Ничего не ломает прямо сейчас, чинит будущее.
#
# КОРЕНЬ 2 (2 ошибки, строка 556): max(reasons, key=reasons.get).
#   `reasons = {}` без аннотации — та же болезнь пустого словаря, что
#   рождала "Never" в ui_torg.py. Pylance теряет тип reasons.get (весь
#   перегруженный сигнатурный набор целиком), max() не может подобрать
#   перегрузку. Аннотация `dict[str, int]` — ровно то, чем reasons и
#   заполняется строкой ниже (`reasons[r] = reasons.get(r, 0) + 1`).
#
# КОРЕНЬ 3 (3 ошибки, строки 691/718/768): studio.memory_tools,
#   studio.grondheim_memory ×2. Те же намеренные кросс-репо заглушки,
#   что studio.grondheim_memory в tester_express.py (TESTER_EXPRESS_
#   SOUL_IGNORE_V1) — уже безопасно обёрнуты в try/except Exception с
#   комментарием, why-текстом в лог. Не чинится (модуль здесь и не
#   должен резолвиться), только подавляется ложное предупреждение.
#
# ЗАПУСК из корня:  python patch_hooks_typing.py
# Идемпотентен, бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "HOOKS_TYPING_V1"
ROOT   = Path(__file__).resolve().parent
TARGET = ROOT / "Биржа" / "hooks.py"

# ── 0. шапка: importlib.util + sys + _HERE/_REPO + _slot_brain ──
OLD_HEADER = '''import json
from datetime import datetime
# ISKRA_FAIR_JUDGEMENT_V1 · суд Искры по pnl_r закрытой сделки
from pathlib import Path
from typing import Optional

from williams_core import build_market_data, read_mt5_csv'''

NEW_HEADER = '''import json
import sys
import importlib.util
from datetime import datetime
# ISKRA_FAIR_JUDGEMENT_V1 · суд Искры по pnl_r закрытой сделки
from pathlib import Path
from typing import Optional

from williams_core import build_market_data, read_mt5_csv

# HOOKS_TYPING_V1: тот же _slot_brain, что в ui_torg.py/tester_express.py —
# Закон Картриджа, мозг слота живёт в GRONDHEIM_CITY/Биржа/цеха/.../слоты/.../мозг.py
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_BRAIN_CACHE: dict = {}


def _slot_brain(ceh_id: str, slot: str):
    """Нет файла — честная вакансия (None), не ошибка. Кэш на процесс."""
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
    return mod'''

# ── КОРЕНЬ 1: arkhiv_live → _slot_brain ──
OLD_1 = '''    try:
        from arkhiv_live import build_digest
        chain["atlas_digest"] = build_digest(signature)'''
NEW_1 = '''    try:
        _b_arkhiv = _slot_brain("контора", "архивариус")
        if _b_arkhiv is None:
            raise RuntimeError("мозг архивариуса ещё не в слоте")
        chain["atlas_digest"] = _b_arkhiv.build_digest(signature)'''

# ── КОРЕНЬ 2: reasons — явная типизация ──
OLD_2 = '''    # Самая частая причина среди отказов/убытков
    reasons = {}'''
NEW_2 = '''    # Самая частая причина среди отказов/убытков
    reasons: dict[str, int] = {}'''

# ── КОРЕНЬ 3: 3× намеренный кросс-репо fallback ──
OLD_3A = "        from studio.memory_tools import remember"
NEW_3A = "        from studio.memory_tools import remember  # type: ignore[import]  # HOOKS_TYPING_V1: намеренно — см. except ниже"

OLD_3B = '''        from studio.grondheim_memory import sync_to_dna
        # ENGINE_ONE_DOOR_V1 · ПЕРЕРАСПРЕДЕЛЕНИЕ ОТВЕТСТВЕННОСТИ.'''
NEW_3B = '''        from studio.grondheim_memory import sync_to_dna  # type: ignore[import]  # HOOKS_TYPING_V1: намеренно — см. except ниже
        # ENGINE_ONE_DOOR_V1 · ПЕРЕРАСПРЕДЕЛЕНИЕ ОТВЕТСТВЕННОСТИ.'''

OLD_3C = '''    try:
        from studio.grondheim_memory import sync_to_dna
        if pnl_r > 0:
            sync_to_dna(aid, "good_work", intensity=0.3, dept="trading")'''
NEW_3C = '''    try:
        from studio.grondheim_memory import sync_to_dna  # type: ignore[import]  # HOOKS_TYPING_V1: намеренно — см. except ниже
        if pnl_r > 0:
            sync_to_dna(aid, "good_work", intensity=0.3, dept="trading")'''

EOF_MARKER = "\n# HOOKS_TYPING_V1 — маркер идемпотентности\n"

BLOCKS = [
    ("шапка: _slot_brain",             OLD_HEADER, NEW_HEADER),
    ("КОРЕНЬ 1: arkhiv_live",          OLD_1, NEW_1),
    ("КОРЕНЬ 2: reasons типизация",    OLD_2, NEW_2),
    ("КОРЕНЬ 3a: studio.memory_tools", OLD_3A, NEW_3A),
    ("КОРЕНЬ 3b: sync_to_dna (Искра)", OLD_3B, NEW_3B),
    ("КОРЕНЬ 3c: sync_to_dna (трейдер)", OLD_3C, NEW_3C),
]


def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: 6 ошибок Pylance → 3 корня")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}\n  Запусти из корня проекта (рядом с папкой Биржа/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print("• маркер уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    ok = True
    for label, old, _new in BLOCKS:
        n = text.count(old)
        status = "✓" if n == 1 else "✗"
        print(f"  {status} якорь [{label}]: найден {n} раз (нужно ровно 1)")
        if n != 1:
            ok = False
    if not ok:
        print("✗ якоря не сошлись — файл отличается от ожидаемого. Ничего не режу.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_name(TARGET.name + f".bak_{ts}")
    shutil.copy2(TARGET, bak)
    print(f"• бэкап: {bak.name}")

    for _label, old, new in BLOCKS:
        text = text.replace(old, new, 1)
    text += EOF_MARKER

    TARGET.write_text(text, encoding="utf-8")
    print("• правки внесены (6 блоков)")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}\n  Файл откатан из бэкапа.")
        sys.exit(1)

    print()
    print("  ГОТОВО:")
    print("  1. arkhiv_live → _slot_brain: сегодня та же честная вакансия")
    print("     (слота архивариуса физически ещё нет), заработает само")
    print("     когда Шеф положит мозг.py на место.")
    print("  2. reasons: dict[str, int] — max()/key= снова видит перегрузки")
    print("  3. 3× намеренный studio.* fallback — только подавлен для чекера,")
    print("     рантайм (try/except уже был) не тронут ни на символ.")
    print("═" * 62)


if __name__ == "__main__":
    main()
