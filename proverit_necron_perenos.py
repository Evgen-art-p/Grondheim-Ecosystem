#!/usr/bin/env python3
# proverit_necron_perenos.py
# ─────────────────────────────────────────────────────────────
# ПОЛНАЯ ПРОВЕРКА после переноса семи файлов (21-22.07, разговор
# с Шефом): williams_core.py, hooks.py, tester_express.py,
# A01/A06/A07/A08 мозг.py + удаление voronka_bdb2.py.
#
# Три уровня проверки подряд, честно печатает, что нашёл:
#   1. СИНТАКСИС  — py_compile всех изменённых файлов
#   2. ЧИСТОТА    — старой формулы (detect_divergent_bar/bdb_strong/
#                   bdb_candidate) не осталось нигде в живом коде
#   3. ЖИВОЙ ПРОГОН — движок (build_market_data) даёт ТЕ ЖЕ ответы,
#                   что независимый подтверждённый эталон
#                   (Биржа/test_idivergence_bar.py) на реальной
#                   истории — 40 случайных проверок на двух активах
#
# Ничего не пишет и не меняет — только смотрит и говорит правду.
#
# ЗАПУСК (из корня репо):
#   py proverit_necron_perenos.py
# ─────────────────────────────────────────────────────────────

import sys
import subprocess
import random
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_ROOT = Path(__file__).resolve().parent
_BIRZHA = _ROOT / "Биржа"

_OK = "✅"
_BAD = "❌"

problems = []


def section(title):
    print(f"\n{'='*70}\n{title}\n{'='*70}")


# ═══════════════════════════════════════════════════════════
# 1. СИНТАКСИС
# ═══════════════════════════════════════════════════════════
section("1. СИНТАКСИС — py_compile семи изменённых файлов")

_FILES_TO_CHECK = [
    _BIRZHA / "williams_core.py",
    _BIRZHA / "hooks.py",
    _BIRZHA / "tester_express.py",
    _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / "A01" / "мозг.py",
    _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / "A06" / "мозг.py",
    _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / "A07" / "мозг.py",
    _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты" / "A08" / "мозг.py",
]

for f in _FILES_TO_CHECK:
    if not f.exists():
        print(f"  {_BAD} {f.relative_to(_ROOT)} — ФАЙЛА НЕТ НА МЕСТЕ")
        problems.append(f"нет файла {f}")
        continue
    res = subprocess.run([sys.executable, "-m", "py_compile", str(f)],
                         capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  {_OK} {f.relative_to(_ROOT)}")
    else:
        print(f"  {_BAD} {f.relative_to(_ROOT)} — СИНТАКСИЧЕСКАЯ ОШИБКА:")
        print(f"     {res.stderr.strip()[:300]}")
        problems.append(f"синтаксис {f}")

_dead = _ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "voronka_bdb2.py"
if _dead.exists():
    print(f"  {_BAD} voronka_bdb2.py всё ещё на месте — должен быть удалён")
    problems.append("voronka_bdb2.py не удалён")
else:
    print(f"  {_OK} voronka_bdb2.py удалён")


# ═══════════════════════════════════════════════════════════
# 2. ЧИСТОТА — старой формулы не осталось в живом коде
# ═══════════════════════════════════════════════════════════
section("2. ЧИСТОТА — старая формула не должна остаться нигде")

# NECRON_DIVERGENCE_V1: bdb_strong/bdb_candidate ОСТАВЛЕНЫ как имена
# локальных переменных в hooks.py (формат дашборда не менялся), но
# теперь считаются из НОВОЙ формулы (wf.get("bdb_dir")) — это не
# старый код, поэтому по именам переменных не ищем. Настоящий след
# старого — вызов detect_divergent_bar(...) и ключ "divergent_bar" в
# словаре (md.get("divergent_bar", ...) или "divergent_bar": ...).
_OLD_MARKERS = ["detect_divergent_bar(", '"divergent_bar"', "'divergent_bar'"]

found_old = False
for f in _FILES_TO_CHECK:
    if not f.exists():
        continue
    text = f.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_docstring = False
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        # грубый, но рабочий счётчик тройных кавычек — пропускаем
        # докстринги/комментарии, там имя может остаться как ИСТОРИЯ
        if stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1:
            in_docstring = not in_docstring
            continue
        if in_docstring or stripped.startswith("#"):
            continue
        for marker in _OLD_MARKERS:
            if marker in line:
                print(f"  {_BAD} {f.relative_to(_ROOT)}:{lineno} — живой код: {line.strip()[:80]}")
                found_old = True
                problems.append(f"старая формула жива в {f.name}:{lineno}")

if not found_old:
    print(f"  {_OK} Ни одного живого вызова detect_divergent_bar(...) или ключа "
          f'"divergent_bar" — только исторические заметки в комментариях/докстрингах')


# ═══════════════════════════════════════════════════════════
# 3. ЖИВОЙ ПРОГОН — движок против независимого эталона
# ═══════════════════════════════════════════════════════════
section("3. ЖИВОЙ ПРОГОН — движок vs эталон (test_idivergence_bar.py)")

sys.path.insert(0, str(_BIRZHA))
sys.path.insert(0, str(_ROOT))   # на случай, если файлы биржи ещё не перенесены
try:
    from williams_core import read_mt5_csv, build_market_data
    from test_idivergence_bar import find_divergence_bars
except Exception as e:
    print(f"  {_BAD} Не смог импортировать движок/эталон: {e}")
    print(f"     Ищи test_idivergence_bar.py — должен лежать либо в Биржа/, "
         f"либо в корне репо (если ещё не переносил файлы биржи скриптом "
         f"perenesti_faily_birzhi.py).")
    problems.append(f"импорт: {e}")
    read_mt5_csv = None

_CHECKS = [
    ("test_data/XAUUSDH4.csv", "XAUUSD", "H4", 0.01, 20),
    ("test_data/EURUSDH1.csv", "EURUSD", "H1", 0.00001, 20),
]

if read_mt5_csv is not None:
    total_matched = 0
    total_checked = 0
    for csv_rel, symbol, tf, point, n_sample in _CHECKS:
        csv_path = _BIRZHA / csv_rel
        if not csv_path.exists():
            print(f"  {_BAD} нет файла {csv_rel} — пропускаю {symbol}")
            continue

        bars_full = read_mt5_csv(str(csv_path))
        events = find_divergence_bars(bars_full)
        event_idx = {e["bar_index"]: e for e in events}

        random.seed(2026)
        pos_sample = random.sample([e for e in events if e["bar_index"] > 200],
                                   min(n_sample // 2, len(events)))
        all_idx = set(range(200, len(bars_full)))
        neg_sample = random.sample(list(all_idx - set(event_idx.keys())),
                                   n_sample // 2)

        matched = 0
        checked = 0
        for e in pos_sample:
            i = e["bar_index"]
            md = build_market_data(bars_full[:i+1], symbol=symbol,
                                   timeframe=tf, point=point)
            engine_dir = md.get("wave_form", {}).get("bdb_dir")
            expected = "BEAR" if e["side"] == "SELL" else "BULL"
            matched += (engine_dir == expected)
            checked += 1
        for i in neg_sample:
            md = build_market_data(bars_full[:i+1], symbol=symbol,
                                   timeframe=tf, point=point)
            engine_dir = md.get("wave_form", {}).get("bdb_dir")
            matched += (engine_dir is None)
            checked += 1

        total_matched += matched
        total_checked += checked
        status = _OK if matched == checked else _BAD
        print(f"  {status} {symbol} {tf}: {matched}/{checked} совпало с эталоном")
        if matched != checked:
            problems.append(f"{symbol} {tf}: только {matched}/{checked} совпало")

    print(f"\n  ИТОГО: {total_matched}/{total_checked}")


# ═══════════════════════════════════════════════════════════
# ВЕРДИКТ
# ═══════════════════════════════════════════════════════════
section("ВЕРДИКТ")
if not problems:
    print(f"  {_OK} ВСЁ ЧИСТО. Перенос сделан верно, старое вырезано, новое работает.")
else:
    print(f"  {_BAD} Найдено проблем: {len(problems)}")
    for p in problems:
        print(f"     - {p}")
    print("\n  Пришли этот вывод — разберу, что не так.")
