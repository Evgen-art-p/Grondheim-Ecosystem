# -*- coding: utf-8 -*-
"""
ПАТЧ: KOMPAS_NE_VOROTA_V1 — компас перестаёт быть воротами.

Слово Шефа 18.07: «компас..он и есть компас для ориентира».
Все датчики города кладут ФАКТЫ на стол, решают трейдеры. Компас
был исключением — он запирал вход. Больше нет.

ЧТО МЕНЯЕТ (мозг A01, Искра):
  1. `_descend` — снят фильтр `if bdb_dir == compass`. Спуск ищет
     точку ЛЮБОГО направления. Компас снимается справочно и кладётся
     рядом как РАНГ (soglasie True/False/None).
  2. Вызывающая сторона — снято «нет компаса → нечего ловить».
     Раньше отсутствие дивера-с-якорем убивало точку, которая на
     этаже была. Теперь спуск идёт всегда.
  3. Промпт Искры — `trend_direction` берётся от НАПРАВЛЕНИЯ ТОЧКИ,
     а не от компаса (раньше трейдеры получали направление компаса).
     Добавлен явный текст: компас не замок, точка против компаса —
     не отказ, а факт с пометкой.

ПОЧЕМУ (замер на живой истории 18.07, XAUUSD H4, реальное ядро):
  с жёстким компасом  —  2 события за 17 лет
  без него            — 15 событий за 17 лет
Ворота выкашивали до 87% честных точек.

ЗАПУСК: из корня репо
    python patch_kompas_ne_vorota.py

Идемпотентно: повторный запуск ничего не делает.
Бэкап: рядом с файлом, .bak (перезаписывается при каждом применении).
"""
import ast
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = (REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
          / "слоты" / "A01" / "мозг.py")

MARKER = "KOMPAS_NE_VOROTA_V1"

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 1 — функция _descend целиком
# ═══════════════════════════════════════════════════════════
OLD_DESCEND_HEAD = ('def _descend(symbol: str, start_tf: str, compass: str, '
                    'top_form: dict) -> dict:')
NEXT_DEF = "def run_iskra("

NEW_DESCEND = '''def _soglasie_slovami(soglasie) -> str:
    """KOMPAS_NE_VOROTA_V1: ранг точки относительно компаса, словами
    для промпта. Не вердикт — факт на стол."""
    if soglasie is True:
        return "точка ПО компасу (согласие)"
    if soglasie is False:
        return "точка ПРОТИВ компаса (это не отказ — просто против ветра)"
    return "сверять не с чем"


def _descend(symbol: str, start_tf: str, compass, top_form: dict) -> dict:
    """
    KOMPAS_NE_VOROTA_V1 (слово Шефа 18.07): «компас — он и есть компас,
    для ориентира». Раньше здесь были ШОРЫ: спуск засчитывал точку
    ТОЛЬКО если bdb_dir == compass, иначе шагал глубже до дна M5. Это
    были жёсткие ворота — на живой истории они выкашивали до 87%
    честных точек (замер 18.07: 15 событий без компаса против 2 с ним).

    Теперь спуск ищет ТОЧКУ ЛЮБОГО НАПРАВЛЕНИЯ. Компас снимается
    справочно и кладётся рядом как РАНГ, не как условие прохода:
      soglasie=True  — точка в сторону компаса («золотая»)
      soglasie=False — точка против компаса (спекулятивная, меньшим лотом)
      soglasie=None  — компаса нет вовсе (дивера-с-якорем не было)
    Что делать с этим фактом — решают трейдеры, не Искра. Она сенсор.

    start_tf — этаж старта. top_form — уже снятый слепок (без лишнего
    стука в терминал на первом этаже).

    Возвращает:
      {"found": bool, "timeframe": str|None, "zero_point": float|None,
       "napravlenie": str|None, "soglasie": bool|None}
    """
    from mt5_feed import step_down

    tf   = start_tf
    form = top_form          # старший этаж — по готовому слепку, без стука
    visited = 0
    while tf is not None and visited < 12:   # страховка от бесконечного цикла
        bdb_dir = form.get("bdb_dir")
        if bdb_dir is not None:
            # ТОЧКА ЕСТЬ. Компас не запирает — только судит ранг.
            soglasie = (bdb_dir == compass) if compass else None
            return {"found": True, "timeframe": tf,
                    "zero_point": form.get("bdb_price"),
                    "napravlenie": bdb_dir, "soglasie": soglasie}
        nxt = step_down(tf)
        if nxt is None:        # дно M5 — глубже кислорода нет
            break
        tf = nxt
        form = _read_form_on(symbol, tf)   # второй этаж и ниже — стучимся
        visited += 1
    return {"found": False, "timeframe": None, "zero_point": None,
            "napravlenie": None, "soglasie": None}


'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 2 — вызывающая сторона в run_iskra
# ═══════════════════════════════════════════════════════════
OLD_CALL = '''    _working_bdb = _top_form.get("bdb_dir")
    if _working_bdb is not None:
        _descent = {"found": True, "timeframe": _start_tf,
                    "zero_point": _top_form.get("bdb_price"),
                    "compass": _working_bdb, "start_tf": _start_tf}
    else:
        _compass = _compass_from(_top_form)
        if _compass is None:
            # Нет компаса (нет дивера-с-якорем) — Искре нечего ловить.
            _descent = {"found": False, "timeframe": None,
                        "zero_point": None, "compass": None, "start_tf": _start_tf}
        else:
            _res = _descend(symbol, _start_tf, _compass, _top_form)
            _descent = {"found": _res["found"], "timeframe": _res["timeframe"],
                        "zero_point": _res["zero_point"], "compass": _compass,
                        "start_tf": _start_tf}'''

NEW_CALL = '''    # KOMPAS_NE_VOROTA_V1: компас снимается ВСЕГДА и ВСЕГДА справочно —
    # он ориентир, не замок. Раньше «нет компаса» = «Искре нечего
    # ловить» (спуск даже не начинался), и это было вторыми воротами
    # поверх первых: точку убивало отсутствие ДИВЕРА-С-ЯКОРЕМ, хотя
    # сама точка B/D/B на этаже могла быть. Теперь компас только судит
    # ранг найденной точки (soglasie), а ищем — всегда.
    _compass = _compass_from(_top_form)
    _working_bdb = _top_form.get("bdb_dir")
    if _working_bdb is not None:
        # Точка прямо на рабочем этаже — главный путь, как и было.
        _descent = {"found": True, "timeframe": _start_tf,
                    "zero_point": _top_form.get("bdb_price"),
                    "napravlenie": _working_bdb,
                    "soglasie": (_working_bdb == _compass) if _compass else None,
                    "compass": _compass, "start_tf": _start_tf}
    else:
        # На рабочем пусто — спускаемся и ищем точку ЛЮБОГО направления.
        _res = _descend(symbol, _start_tf, _compass, _top_form)
        _descent = {"found": _res["found"], "timeframe": _res["timeframe"],
                    "zero_point": _res["zero_point"],
                    "napravlenie": _res.get("napravlenie"),
                    "soglasie": _res.get("soglasie"),
                    "compass": _compass, "start_tf": _start_tf}'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 3 — блок промпта
# ═══════════════════════════════════════════════════════════
OLD_PROMPT = '''        "=== СПУСК ПО ЛЕСЕНКЕ (Искра v2 — слепая геометрия уже отработала) ===\\n"
        f"Компас (старший этаж {md.get('v2_descent',{}).get('start_tf','?')}): "
        f"{md.get('v2_descent',{}).get('compass') or 'нет дивера-с-якорем'}\\n"
        f"Точка найдена: "
        f"{('ДА на ' + str(md['v2_descent']['timeframe']) + ', цена ' + str(md['v2_descent']['zero_point'])) if md.get('v2_descent',{}).get('found') else 'нет — молчи (NOT_FOUND)'}\\n"
        "Это РЕЗУЛЬТАТ твоего спуска. Если точка найдена — твой signal "
        "t1_status=DETECTED, trend_direction=компас, zero_point_price=цена. "
        "Если не найдена — t1_status=NOT_FOUND. Озвучь это своим голосом.\\n\\n"'''

NEW_PROMPT = '''        "=== СПУСК ПО ЛЕСЕНКЕ (Искра v2 — слепая геометрия уже отработала) ===\\n"
        f"Точка найдена: "
        f"{('ДА на ' + str(md['v2_descent']['timeframe']) + ', цена ' + str(md['v2_descent']['zero_point']) + ', направление ' + str(md['v2_descent'].get('napravlenie'))) if md.get('v2_descent',{}).get('found') else 'нет — молчи (NOT_FOUND)'}\\n"
        f"Компас (ориентир со старшего этажа {md.get('v2_descent',{}).get('start_tf','?')}): "
        f"{md.get('v2_descent',{}).get('compass') or 'компаса нет (дивера-с-якорем не было)'}"
        f" — {_soglasie_slovami(md.get('v2_descent',{}).get('soglasie'))}\\n"
        "КОМПАС — ОРИЕНТИР, НЕ ЗАМОК. Он НЕ решает, есть точка или нет, "
        "и НЕ задаёт её направление. Точка против компаса — это НЕ отказ, "
        "это факт с пометкой «против ветра»: положи его на стол как есть, "
        "трейдеры решат сами.\\n"
        "Если точка найдена — твой signal t1_status=DETECTED, "
        "trend_direction = НАПРАВЛЕНИЕ ТОЧКИ (не компаса), "
        "zero_point_price=цена. Если не найдена — t1_status=NOT_FOUND. "
        "Озвучь это своим голосом.\\n\\n"'''


def main():
    if not TARGET.exists():
        print(f"[ПАТЧ] ✗ не найден: {TARGET}")
        print("[ПАТЧ]   запускать из КОРНЯ репо Grondheim-Ecosystem")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — ничего не делаю")
        return 0

    # ── проверка всех якорей ДО единой правки ──
    if OLD_DESCEND_HEAD not in src:
        print("[ПАТЧ] ✗ якорь 1 (_descend) не найден — файл уже другой")
        return 1
    if OLD_CALL not in src:
        print("[ПАТЧ] ✗ якорь 2 (вызов _descend) не найден")
        return 1
    if OLD_PROMPT not in src:
        print("[ПАТЧ] ✗ якорь 3 (промпт) не найден")
        return 1

    # ── правка 1: _descend целиком ──
    a = src.index(OLD_DESCEND_HEAD)
    b = src.index(NEXT_DEF, a)
    src = src[:a] + NEW_DESCEND + src[b:]

    # ── правка 2 ──
    src = src.replace(OLD_CALL, NEW_CALL, 1)

    # ── правка 3 ──
    src = src.replace(OLD_PROMPT, NEW_PROMPT, 1)

    src += f"\n# {MARKER} - marker\n"

    # ── проверка синтаксиса ДО записи ──
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ результат не парсится: {e}")
        return 1

    shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {MARKER} применён")
    print(f"[ПАТЧ]   бэкап: {TARGET.with_suffix('.py.bak').name}")
    print("[ПАТЧ]   компас снят с ворот: спуск ищет точку ЛЮБОГО")
    print("[ПАТЧ]   направления, компас судит только ранг (soglasie)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
