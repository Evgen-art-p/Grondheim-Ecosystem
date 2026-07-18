# -*- coding: utf-8 -*-
"""
ПАТЧ: ISKRA_WAVE_MEASURE_DOSTAVKA_V1

Продолжение ISKRA_WAVE_MEASURE_V1 (williams_core.py уже несёт dlina/
struktura_chitaetsya в wave_form). Здесь — доставка теми же трубами,
что уже проложены для компаса (KOMPAS_DOSTAVKA_TREYDERAM_V1):

  wave_form (ядро) → v2_descent (мозг A01) → trading_state → трейдеры

Без этого патча факты вычисляются, но никуда не уходят — ровно та же
дыра, что была с компасом до третьего патча.

ЧТО МЕНЯЕТ:
  A01 (Искра): _descend несёт dlina/struktura_chitaetsya с этажа, где
  нашлась точка (не с рабочего — этажи разные, слепки разные).
  run_iskra кладёт их в v2_descent на обоих путях (рабочий этаж /
  спуск). _save_iskra_memory сохраняет в trading_state. Промпт Искры
  получает короткую строку о структуре — для голоса, не для логики.

  A06/A07/A08 (Брут/Аван/Консерватор): sensors.iskra получает поля
  dlina и struktura_chitaetsya — трейдеры видят их как факт на столе,
  ничего не решают за них.

ЗАПУСК: из корня репо, ПОСЛЕ patch_iskra_wave_measure.py
    python patch_wave_measure_dostavka.py

Идемпотентно. Бэкапы рядом (.bak).
"""
import ast
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
CEHA = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"
MARKER = "ISKRA_WAVE_MEASURE_DOSTAVKA_V1"


# ═══════════════════════════════════════════════════════════
# A01 — три правки в одном файле
# ═══════════════════════════════════════════════════════════
A01_TARGET = CEHA / "A01" / "мозг.py"

A01_EDITS = [
    # 1) _descend: found=True — берём dlina/struktura с этажа находки
    ('''        if bdb_dir is not None:
            # ТОЧКА ЕСТЬ. Компас не запирает — только судит ранг.
            soglasie = (bdb_dir == compass) if compass else None
            return {"found": True, "timeframe": tf,
                    "zero_point": form.get("bdb_price"),
                    "napravlenie": bdb_dir, "soglasie": soglasie}''',
     '''        if bdb_dir is not None:
            # ТОЧКА ЕСТЬ. Компас не запирает — только судит ранг.
            soglasie = (bdb_dir == compass) if compass else None
            # ISKRA_WAVE_MEASURE_DOSTAVKA_V1: факты структуры с ТОГО ЖЕ
            # этажа, где нашлась точка — не с рабочего, слепки разные.
            return {"found": True, "timeframe": tf,
                    "zero_point": form.get("bdb_price"),
                    "napravlenie": bdb_dir, "soglasie": soglasie,
                    "dlina": form.get("dlina"),
                    "struktura_chitaetsya": form.get("struktura_chitaetsya")}'''),

    # 2) _descend: found=False — дефолты
    ('''    return {"found": False, "timeframe": None, "zero_point": None,
            "napravlenie": None, "soglasie": None}''',
     '''    return {"found": False, "timeframe": None, "zero_point": None,
            "napravlenie": None, "soglasie": None,
            "dlina": None, "struktura_chitaetsya": False}'''),

    # 3) run_iskra: сборка _descent на обоих путях
    ('''    _compass = _compass_from(_top_form)
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
                    "compass": _compass, "start_tf": _start_tf}''',
     '''    _compass = _compass_from(_top_form)
    _working_bdb = _top_form.get("bdb_dir")
    if _working_bdb is not None:
        # Точка прямо на рабочем этаже — главный путь, как и было.
        _descent = {"found": True, "timeframe": _start_tf,
                    "zero_point": _top_form.get("bdb_price"),
                    "napravlenie": _working_bdb,
                    "soglasie": (_working_bdb == _compass) if _compass else None,
                    "compass": _compass, "start_tf": _start_tf,
                    # ISKRA_WAVE_MEASURE_DOSTAVKA_V1: факты структуры
                    # с рабочего этажа (тот же слепок, что нашёл точку).
                    "dlina": _top_form.get("dlina"),
                    "struktura_chitaetsya": _top_form.get("struktura_chitaetsya")}
    else:
        # На рабочем пусто — спускаемся и ищем точку ЛЮБОГО направления.
        _res = _descend(symbol, _start_tf, _compass, _top_form)
        _descent = {"found": _res["found"], "timeframe": _res["timeframe"],
                    "zero_point": _res["zero_point"],
                    "napravlenie": _res.get("napravlenie"),
                    "soglasie": _res.get("soglasie"),
                    "compass": _compass, "start_tf": _start_tf,
                    "dlina": _res.get("dlina"),
                    "struktura_chitaetsya": _res.get("struktura_chitaetsya")}'''),

    # 4) _save_iskra_memory: сохранить в trading_state
    ('''    _descent = (md or {}).get("v2_descent", {})
    tstate["iskra"]["compass"]  = _descent.get("compass")
    tstate["iskra"]["soglasie"] = _descent.get("soglasie")
    tstate["iskra"]["found_timeframe"] = (
        signal.get("found_timeframe") or signal.get("timeframe")
    )
    save_trading_state(tstate)''',
     '''    _descent = (md or {}).get("v2_descent", {})
    tstate["iskra"]["compass"]  = _descent.get("compass")
    tstate["iskra"]["soglasie"] = _descent.get("soglasie")
    # ISKRA_WAVE_MEASURE_DOSTAVKA_V1: тем же путём, что компас — иначе
    # трейдеры факты структуры не увидят вовсе (та же дыра, что была
    # с компасом до KOMPAS_DOSTAVKA_TREYDERAM_V1).
    tstate["iskra"]["dlina"] = _descent.get("dlina")
    tstate["iskra"]["struktura_chitaetsya"] = _descent.get("struktura_chitaetsya")
    tstate["iskra"]["found_timeframe"] = (
        signal.get("found_timeframe") or signal.get("timeframe")
    )
    save_trading_state(tstate)'''),

    # 5) промпт Искры — короткая строка про структуру (голос, не логика)
    ('''        f"Компас (ориентир со старшего этажа {md.get('v2_descent',{}).get('start_tf','?')}): "
        f"{md.get('v2_descent',{}).get('compass') or 'компаса нет (дивера-с-якорем не было)'}"
        f" — {_soglasie_slovami(md.get('v2_descent',{}).get('soglasie'))}\\n"
        "КОМПАС — ОРИЕНТИР, НЕ ЗАМОК. Он НЕ решает, есть точка или нет, "''',
     '''        f"Компас (ориентир со старшего этажа {md.get('v2_descent',{}).get('start_tf','?')}): "
        f"{md.get('v2_descent',{}).get('compass') or 'компаса нет (дивера-с-якорем не было)'}"
        f" — {_soglasie_slovami(md.get('v2_descent',{}).get('soglasie'))}\\n"
        f"Структура (горб-3→ноль-4→дивер-5, длина "
        f"{md.get('v2_descent',{}).get('dlina')} баров): "
        f"{'читается строго' if md.get('v2_descent',{}).get('struktura_chitaetsya') else 'не читается строго — не повод молчать, просто факт слабее'}\\n"
        "КОМПАС — ОРИЕНТИР, НЕ ЗАМОК. Он НЕ решает, есть точка или нет, "'''),
]


# ═══════════════════════════════════════════════════════════
# A06/A07/A08 — одна и та же правка, общий шаблон
# ═══════════════════════════════════════════════════════════
TRADER_OLD = '''            "iskra":  {k: table["iskra"].get(k) for k in
                       ("t1_status", "zero_point_price", "trend_direction")},'''
TRADER_NEW = '''            "iskra":  {k: table["iskra"].get(k) for k in
                       ("t1_status", "zero_point_price", "trend_direction",
                        "dlina", "struktura_chitaetsya")},'''


def patch_multi(target: Path, edits: list, label: str) -> bool:
    if not target.exists():
        print(f"[ПАТЧ] ✗ {label}: не найден {target}")
        return False
    src = target.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✓ {label}: {MARKER} уже применён — пропускаю")
        return True
    for i, (old, new) in enumerate(edits, 1):
        if old not in src:
            print(f"[ПАТЧ] ✗ {label}: якорь #{i} не найден — файл уже другой")
            return False
    for old, new in edits:
        src = src.replace(old, new, 1)
    src += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ {label}: результат не парсится: {e}")
        return False
    shutil.copy2(target, target.with_suffix(".py.bak"))
    target.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {label}: {MARKER} применён ({len(edits)} правок)")
    return True


def main():
    ok = True
    ok &= patch_multi(A01_TARGET, A01_EDITS, "A01 (Искра)")
    for slot, name in (("A06", "Брут"), ("A07", "Аван"), ("A08", "Консерватор")):
        ok &= patch_multi(CEHA / slot / "мозг.py",
                          [(TRADER_OLD, TRADER_NEW)], f"{slot} ({name})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
