# -*- coding: utf-8 -*-
# SOVET_BEZ_SENSOROV_V1
"""
СОВЕТ БЕЗ СЕНСОРОВ И БЕЗ ВОРОТ.

    python patch_sovet_bez_sensorov.py --suho     посмотреть
    python patch_sovet_bez_sensorov.py            сделать

Запускать из КОРНЯ репо, после nastroit_birzhu.py и
postavit_stol_i_glaz.py.

ЗАЧЕМ (дыра, найденная 06.08)
    Кнопка РЫНОК зовёт Совет. Совет первым делом будил ИСКРУ, и её
    СПУСК был воротами: не нашёл точку — все расходятся.

    Сенсоры уехали в архив. Значит спуска нет никогда, ворота не
    откроются ни разу, и трейдеры не проснутся ВООБЩЕ. Не упало бы —
    просто молчало бы каждый бар, и понять почему было бы нечем.

ЧТО СТАНОВИТСЯ
    Ворот нет, сенсоров нет. Порядок простой:

        Архивариус → три трейдера → Исполнитель

    Каждый трейдер накрывает себе стол сам (Биржа/stol.py) и сам
    решает, есть ли тут работа. Право промолчать переехало туда, где
    ему место: к тому, кого этому учили, а не в замок на чужом сигнале.

ЧТО НЕ МЕНЯЕТСЯ
    Имя функции, её подпись и форма сводки — те же. Кабинет и тестер
    зовут как звали и ничего не замечают. Позиции по-прежнему открывает
    Исполнитель, закрывает `_settle` на следующем баре.

    Определения `_ISKRA`, `_SENSORS` и дешёвая проверка точки остаются
    в файле неиспользованными — не трогаю их, чтобы не задеть лишнего.
"""
import argparse
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "SOVET_BEZ_SENSOROV_V1"
TARGET = Path("Биржа") / "council.py"
BAK = Path("Биржа") / "council.py.bak_bez_sensorov"


HEAD_OLD = 'def wake_council(symbol: str, timeframe: str,\n                 on_event: Optional[Callable] = None,\n                 window=None, point=None) -> dict:\n    """\n    БУДИТ СОВЕТ на текущем баре. symbol/timeframe — паспорт, течёт\n    в каждого агента (они сами берут бар своего этажа — спуск Искры\n    решает где). on_event(dict) — вести наружу (лента кабинета/тестера),\n    может быть None.\n\n    Возвращает сводку: кто что сказал + полные результаты каждого\n    агента (в results, чтобы UI мог обновить свои панели). Позиции\n    открывает Исполнитель (рука-код), закрывает _settle на следующем\n    баре — движок этого не трогает, только будит по порядку.\n\n    on_event получает словари вида:\n      {"type": "agent", "id": "A02", "ok": True, "result": {...},\n       "narrative": "...", "verdict": "APPROVED"|None}\n      {"type": "council_idle", "why": "..."}   — спуск не нашёл точку\n    result — ПОЛНЫЙ словарь run_* (UI берёт из него signal/market/stats).\n    """\n    def _emit(ev):\n        if on_event:\n            try:\n                on_event(ev)\n            except Exception:\n                pass\n\n    summary = {"woke": [], "verdicts": {}, "orders": None,\n               "idle": False, "results": {}}\n\n    # ── Искра (голова) ──\n    ceh, slot, fn = _ISKRA\n    ri = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)\n    summary["woke"].append("A01")\n    summary["results"]["A01"] = ri\n    _emit({"type": "agent", "id": "A01", "ok": ri.get("ok"),\n           "result": ri, "narrative": ri.get("narrative", "")})\n\n    # ворота по спуску (COUNCIL_BY_DESCENT_V1): нашёл точку — Совет\n    # собирается. нет — расходимся. Это ФАКТ спуска, не суждение\n    # Искры-LLM (её t1_status идёт в Совет как голос, не как замок).\n    # KRIK_ISKRY_V1: различаем ДВА РАЗНЫХ случая, которые раньше\n    # сливались в один и врали Шефу:\n    #   а) Искра УПАЛА (ok=False) — в её аварийном return нет "descent"\n    #      вообще, и ворота читали это как «спуск не нашёл». Ложь:\n    #      спуск отработал, упало позже. Кричим ПОЧЕМУ.\n    #   б) Искра отработала, но спуск честно не нашёл точку — расходимся.\n    if not ri.get("ok"):\n        _err = ri.get("error", "?")\n        print(f"[СОВЕТ] ⛔ ИСКРА УПАЛА: {_err}")\n        print("[СОВЕТ]    Совет не собрался НЕ из-за спуска — из-за сбоя.")\n        _emit({"type": "council_idle",\n               "why": f"Искра упала: {_err}",\n               "descent": {}, "iskra_error": _err})\n        summary["idle"] = True\n        summary["iskra_error"] = _err\n        return summary\n\n    descent = ri.get("descent", {}) or {}\n    _svezhy_spusk = bool(descent.get("found"))\n\n    # COUNCIL_GATE_TROYNOY_V1: Триггер А не сработал — пробуем Б/В.\n    # Дешёвая проверка (без LLM): точка жива И (фрактал Ганса ИЛИ\n    # Большой палец) прямо на ЭТОМ баре.\n    _cheap = None\n    if not _svezhy_spusk:\n        _cheap = _deshyovaya_proverka_tochki(symbol, timeframe,\n                                             window=window, point=point)\n\n    if not _svezhy_spusk and not (_cheap and _cheap.get("trigger")):\n        _tochka_info = (_cheap or {}).get("tochka", {})\n        _emit({"type": "council_idle",\n               "why": ("спуск не нашёл точку, точка не жива/триггера нет "\n                      f"({_tochka_info.get(\'reason\', \'?\')})"),\n               "descent": descent, "tochka": _tochka_info})\n        summary["idle"] = True\n        return summary\n\n    if not _svezhy_spusk and _cheap and _cheap.get("trigger"):\n        print(f"[СОВЕТ] 🎯 Триггер {_cheap[\'kind\']} на живой точке "\n              f"(родилась: {_cheap[\'tochka\'].get(\'reason\',\'?\')}) — "\n              f"будим Совет БЕЗ свежего спуска Искры")\n        _emit({"type": "council_triggered_by_point",\n               "kind": _cheap["kind"], "napravlenie": _cheap["napravlenie"],\n               "tochka": _cheap["tochka"]})\n\n'

HEAD_NEW = 'def wake_council(symbol: str, timeframe: str,\n                 on_event: Optional[Callable] = None,\n                 window=None, point=None) -> dict:\n    """\n    ОЧЕРЁДНОСТЬ РАБОТЫ на текущем баре. Имя осталось прежним, чтобы\n    кабинет и тестер звали как звали, но собрания больше нет.\n\n    SOVET_BEZ_SENSOROV_V1 (решение Шефа 06.08). Было: Искра будила\n    себя от рынка, её СПУСК был воротами — не нашёл точку, все\n    расходятся. Сенсоры уехали в архив, значит спуска нет никогда, и\n    ворота не открылись бы ни разу: трейдеры не проснулись бы вообще.\n\n    Стало: ворот нет и сенсоров нет. Каждый трейдер накрывает себе\n    стол сам (Биржа/stol.py) и сам решает — смотреть ему тут или\n    расходиться. Право промолчать переехало туда, где ему место: к\n    тому, кого этому учили, а не в замок на чужом сигнале.\n\n    symbol/timeframe — паспорт, течёт в каждого. on_event(dict) —\n    вести наружу (лента кабинета/тестера), может быть None.\n\n    Возвращает ту же сводку, что и раньше: кто что сказал плюс полные\n    результаты каждого (в results, чтобы UI обновил свои панели).\n    Позиции открывает Исполнитель (рука-код), закрывает _settle на\n    следующем баре — здесь их не трогают.\n    """\n    def _emit(ev):\n        if on_event:\n            try:\n                on_event(ev)\n            except Exception:\n                pass\n\n    summary = {"woke": [], "verdicts": {}, "orders": None,\n               "idle": False, "results": {}}\n\n'

SENS_OLD = '    # ── сенсоры ──\n    for aid, ceh, slot, fn in _SENSORS:\n        r = _call(ceh, slot, fn, symbol=symbol, timeframe=timeframe)\n        summary["woke"].append(aid)\n        summary["results"][aid] = r\n        _emit({"type": "agent", "id": aid, "ok": r.get("ok"),\n               "result": r, "narrative": r.get("narrative", "")})\n\n'

SENS_NEW = '    # ── сенсоров больше нет ───────────────────────────────────\n    # Искра, Морж, Паникёр и Ганс стали математикой и уехали из цеха.\n    # Их работу делает Биржа/stol.py — каждый трейдер зовёт его сам,\n    # внутри своего мозга. Будить тут некого.\n\n'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — ничего не делаю")
        return 0

    novyy = src
    for imya, old, new in (("голова Совета: ворота и Искра", HEAD_OLD, HEAD_NEW),
                           ("блок сенсоров", SENS_OLD, SENS_NEW)):
        n = novyy.count(old)
        if n != 1:
            print(f"✗ «{imya}»: найдено {n} раз (нужно 1). "
                  f"Файл не тот — ничего не менял.")
            return 1
        novyy = novyy.replace(old, new, 1)
        print(f"  · {imya} — ок")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    if a.suho:
        print("\n[СУХОЙ ПРОГОН] всё сходится, ничего не записал.")
        print(f"  было {len(src)} символов → станет {len(novyy)}")
        return 0

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK.name}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print("\n  Порядок теперь: Архивариус → три трейдера → Исполнитель.")
    print("  Ворот нет: каждый трейдер решает сам, есть ли тут работа.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
