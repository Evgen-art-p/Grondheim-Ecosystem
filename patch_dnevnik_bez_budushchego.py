# -*- coding: utf-8 -*-
"""
ПАТЧ: DNEVNIK_BEZ_BUDUSHCHEGO_V1

НАЙДЕНО в первом полном прогоне тестера после сегодняшних патчей
(18.07, EURUSD H4, 10 кандидатов). Аван на баре 2000.12.08 сравнил
в narrative два случая из своей памяти: «1999.12.31 (-1R) дороже,
чем 2011.08.01 (+3.29R)». Текущий бар теста — ДЕКАБРЬ 2000. Сделка
2011 года физически не могла ещё случиться в хронологии прогона —
но он её уже знал и взвешивал при решении.

ПРИЧИНА (проверена, не гипотеза): `_read_recent_diary(n)` читает
последние N строк ФАЙЛА diary_*.jsonl без разбора дат. Файл копится
в РЕАЛЬНОМ времени между прогонами тестера — проверено по
tester_express.py, там нет ни одной строки сброса diary_*.jsonl.
Значит если вчера гонялся прогон до 2011 года, а сегодня — заново
с 1995-го, все записи 2011-го остаются в файле и читаются как
«последние», независимо от того, какой год сейчас проверяет тестер.

Это заглядывание в будущее внутри одной симуляции — тот же грех,
против которого уже стоит закон в global_anchor.global_trend
(as_of_date, «видим только то, что видел бы реал в тот момент»).
Здесь этот закон не был поставлен для дневника.

ЧТО МЕНЯЕТ: `_read_recent_diary(n, as_of_bar_time=None)` — фильтрует
события по bar_time <= as_of_bar_time ДО взятия последних n. Вызов
из run_brut/run_avan/run_cons передаёт md.get("bar_time") — текущий
бар прогона. as_of_bar_time=None (по умолчанию) сохраняет старое
поведение — для мест, где бар неизвестен (обратная совместимость).

ЗАПУСК: из корня репо
    python patch_dnevnik_bez_budushchego.py

Идемпотентно. Бэкапы рядом (.bak).
"""
import ast
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
CEHA = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"
MARKER = "DNEVNIK_BEZ_BUDUSHCHEGO_V1"


def edits_for(docstring: str, call_indent: str = "    "):
    """Собирает пару (old, new) для функции + пару для места вызова.
    docstring — точный текст однострочного докстринга этого слота
    (у A06/A07/A08 он отличается по формулировке)."""
    old_fn = f'''def _read_recent_diary(n: int = 5) -> list:
    """{docstring}"""
    if not DIARY_PATH.exists():
        return []
    try:
        lines = DIARY_PATH.read_text(encoding="utf-8").strip().splitlines()
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
    except OSError:
        return []'''

    new_fn = f'''def _read_recent_diary(n: int = 5, as_of_bar_time=None) -> list:
    """{docstring}

    DNEVNIK_BEZ_BUDUSHCHEGO_V1 (18.07): те же n событий, но ДО
    as_of_bar_time — иначе трейдер в прошлом видит исходы сделок из
    будущего прогона (дневник копится в реальном времени, тестер его
    не сбрасывает между запусками). as_of_bar_time=None — старое
    поведение (последние n строк файла), для мест без известного бара.
    """
    if not DIARY_PATH.exists():
        return []
    try:
        lines = DIARY_PATH.read_text(encoding="utf-8").strip().splitlines()
        events = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if as_of_bar_time:
            events = [e for e in events
                     if (e.get("bar_time") or "") <= as_of_bar_time]
        return events[-n:]
    except OSError:
        return []'''

    old_call = f"{call_indent}recent = _read_recent_diary(5)"
    new_call = (f"{call_indent}# DNEVNIK_BEZ_BUDUSHCHEGO_V1: только события ДО текущего бара\n"
               f'{call_indent}recent = _read_recent_diary(5, as_of_bar_time=md.get("bar_time"))')

    return [(old_fn, new_fn), (old_call, new_call)]


TARGETS = {
    "A06": "Последние n событий из личной тетради — Брут берёт их с собой на стол.",
    "A07": "Последние n событий из личной тетради.",
    "A08": "Последние n событий из личной тетради.",
}


def patch_one(slot: str, docstring: str) -> bool:
    target = CEHA / slot / "мозг.py"
    if not target.exists():
        print(f"[ПАТЧ] ✗ {slot}: не найден {target}")
        return False
    src = target.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[ПАТЧ] ✓ {slot}: {MARKER} уже применён — пропускаю")
        return True

    edits = edits_for(docstring)
    for i, (old, new) in enumerate(edits, 1):
        if old not in src:
            print(f"[ПАТЧ] ✗ {slot}: якорь #{i} не найден — файл уже другой")
            return False
    for old, new in edits:
        src = src.replace(old, new, 1)
    src += f"\n# {MARKER} - marker\n"

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ {slot}: результат не парсится: {e}")
        return False

    shutil.copy2(target, target.with_suffix(".py.bak"))
    target.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {slot}: {MARKER} применён")
    return True


def main():
    ok = True
    for slot, docstring in TARGETS.items():
        ok &= patch_one(slot, docstring)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
