#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SVOY_STOL_CEHA_V1
"""
СВОЙ СТОЛ У КАЖДОГО ЦЕХА — чтобы два одинаковых не мешали друг другу.

    python patch_svoy_stol_ceha.py            посмотреть
    python patch_svoy_stol_ceha.py --sdelat   накатить

Запускать из КОРНЯ. Ставится после patch_zakon_kartridzha.py.

ЗАЧЕМ

    Ты просишь цех-картридж: такой же, один в один, женский и мужской.
    Скопировать папку мало — стол общий на всю Биржу, один файл
    `Биржа/данные/trading_state.json`. Два цеха начнут писать вердикты
    и открытые позиции в одну тетрадь: женский трейдер сотрёт мужского.

    Причём задумка у тебя была правильная с самого начала — в манифесте
    цеха давно объявлены СВОИ журналы (`журналы/pnl.jsonl`,
    `журналы/atlas.jsonl`). Просто код брал общий файл.

ЧТО СТАНЕТ

    · у цеха свой стол: `цеха/{цех}/данные/trading_state.json`;
    · Совет говорит перед прогоном, чей цех сегодня работает;
    · первый раз цеховой стол берётся из общего — чтобы не начинать с
      чистого листа: открытые позиции и состояние переезжают к цеху,
      а общий остаётся лежать как был;
    · не сказали цех — работаем по-старому, на общем. Ничего не
      ломается, если ты этим не пользуешься.

    После этого копия цеха живёт своей жизнью: свой стол, свои позиции,
    свои журналы.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
HOOKS = KOREN / "Биржа" / "hooks.py"
SOVET = KOREN / "Биржа" / "council.py"
MARKER = "# SVOY_STOL_CEHA_V1 - marker"
BAK = ".bak_svoy_stol"

HOOKS_STEZHKI = (
    ('свой стол цеху', 'STATE_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "данные" / "trading_state.json"\n\n# Журнал PnL сделок (НЕ billing_ledger — тот про LLM-расходы)\nPNL_PATH = _REPO / "GRONDHEIM_CITY" / "Биржа" / "данные" / "trading_pnl.jsonl"\n', '# ═══════════════════════════════════════════════════════════\n# SVOY_STOL_CEHA_V1 — У КАЖДОГО ЦЕХА СВОЙ СТОЛ\n# ═══════════════════════════════════════════════════════════\n# Стол был один на всю Биржу: `Биржа/данные/trading_state.json`.\n# Пока цех один — незаметно. Поставь второй такой же (женский и\n# мужской) — и они начнут писать вердикты в одну тетрадь и затирать\n# друг друга.\n#\n# А в манифесте цеха уже давно объявлено своё: `журналы/pnl.jsonl`,\n# `журналы/atlas.jsonl`. Задумка была верной, просто код брал общий\n# файл. Теперь берёт цеховой.\n#\n# Цех говорит Совет перед прогоном (`postavit_ceh`). Не сказали —\n# работаем по-старому, на общем столе: ничего не ломается.\n_OBSHCHIY_DIR = _REPO / "GRONDHEIM_CITY" / "Биржа" / "данные"\nSTATE_PATH = _OBSHCHIY_DIR / "trading_state.json"      # запасной, общий\nPNL_PATH = _OBSHCHIY_DIR / "trading_pnl.jsonl"         # запасной, общий\n\n_TEKUSHCHIY_CEH = ""\n\n\ndef postavit_ceh(ceh_id: str = ""):\n    """Чей стол накрываем. Зовётся Советом в начале прогона."""\n    global _TEKUSHCHIY_CEH\n    _TEKUSHCHIY_CEH = (ceh_id or "").strip()\n\n\ndef _dom_ceha() -> Path:\n    if not _TEKUSHCHIY_CEH:\n        return _OBSHCHIY_DIR\n    return (_REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / _TEKUSHCHIY_CEH\n            / "данные")\n\n\ndef _put_stola() -> Path:\n    """Стол этого цеха. Первый раз — переносим общий, чтобы не начинать\n    с чистого листа: открытые позиции и состояние остаются при цехе."""\n    d = _dom_ceha()\n    p = d / "trading_state.json"\n    if not _TEKUSHCHIY_CEH:\n        return p\n    if not p.exists() and STATE_PATH.exists():\n        try:\n            d.mkdir(parents=True, exist_ok=True)\n            p.write_text(STATE_PATH.read_text(encoding="utf-8"),\n                         encoding="utf-8")\n            print(f"[СТОЛ] переехал в цех {_TEKUSHCHIY_CEH} "\n                  f"(общий остался как был)")\n        except Exception as e:\n            print(f"[СТОЛ] не смог перенести общий стол: {e}")\n    return p\n\n\ndef _put_pnl() -> Path:\n    return (_dom_ceha() / "trading_pnl.jsonl") if _TEKUSHCHIY_CEH \\\n        else PNL_PATH\n'),
    ('чтение и запись по цеху', 'def load_trading_state() -> dict:\n    """Читает рабочую память цеха. Если файла нет — дефолт."""\n    if not STATE_PATH.exists():\n        return json.loads(json.dumps(_DEFAULT_STATE))\n    try:\n        return json.loads(STATE_PATH.read_text(encoding="utf-8"))\n    except (json.JSONDecodeError, OSError) as e:\n        print(f"[STATE] ⚠️  Повреждён trading_state.json ({e}) — дефолт")\n        return json.loads(json.dumps(_DEFAULT_STATE))\n\n\ndef save_trading_state(tstate: dict):\n    """Сохраняет рабочую память цеха."""\n    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)\n    tstate["updated"] = datetime.now().isoformat()\n    STATE_PATH.write_text(\n        json.dumps(tstate, ensure_ascii=False, indent=2), encoding="utf-8")\n    print(f"[STATE] 💾 trading_state сохранён: "\n          f"t1={tstate[\'iskra\'][\'t1_status\']}, "\n          f"позиций={len(tstate[\'positions\'])}")\n', 'def load_trading_state() -> dict:\n    """Читает рабочую память ЭТОГО цеха. Файла нет — дефолт."""\n    p = _put_stola()\n    if not p.exists():\n        return json.loads(json.dumps(_DEFAULT_STATE))\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except (json.JSONDecodeError, OSError) as e:\n        print(f"[STATE] ⚠️  Повреждён {p.name} ({e}) — дефолт")\n        return json.loads(json.dumps(_DEFAULT_STATE))\n\n\ndef save_trading_state(tstate: dict):\n    """Сохраняет рабочую память ЭТОГО цеха."""\n    p = _put_stola()\n    p.parent.mkdir(parents=True, exist_ok=True)\n    tstate["updated"] = datetime.now().isoformat()\n    p.write_text(\n        json.dumps(tstate, ensure_ascii=False, indent=2), encoding="utf-8")\n    print(f"[STATE] 💾 стол сохранён ({_TEKUSHCHIY_CEH or \'общий\'}): "\n          f"t1={tstate[\'iskra\'][\'t1_status\']}, "\n          f"позиций={len(tstate[\'positions\'])}")\n'),
)

SOVET_STEZHKI = (
    ('Совет знает свой цех', 'def wake_council(symbol: str, timeframe: str,\n                 on_event: Optional[Callable] = None,\n                 window=None, point=None) -> dict:\n', 'def wake_council(symbol: str, timeframe: str,\n                 on_event: Optional[Callable] = None,\n                 window=None, point=None,\n                 ceh_id: str = _CEH_TORGOVYY) -> dict:\n'),
    ('сказать столу, чей цех', '    summary = {"woke": [], "verdicts": {}, "orders": None,\n', '    # SVOY_STOL_CEHA_V1: сказать столу, чей цех сегодня работает —\n    # чтобы стол и позиции легли к нему, а не в общую тетрадь.\n    try:\n        import hooks as _h\n        if hasattr(_h, "postavit_ceh"):\n            _h.postavit_ceh(ceh_id)\n    except Exception:\n        pass\n\n    summary = {"woke": [], "verdicts": {}, "orders": None,\n'),
    ('сканер по этому цеху', '    # ── трейдеры: сколько картриджей в цехе, столько и зовём ──\n    _za_stolom = _treydery()\n', '    # ── трейдеры: сколько картриджей в цехе, столько и зовём ──\n    _za_stolom = _treydery(ceh_id)\n'),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def pravit(put: Path, stezhki, suho: bool, imya: str) -> bool:
    if not put.exists():
        print(f"  x нет {imya}")
        return False
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {imya}: уже накатано")
        return True
    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x {imya}: якорь «{nazv}» найден {n} раз — не трогаю")
            return False
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv}")
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, imya):
        return False
    if suho:
        print(f"  {imya}: + готов")
        return True
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {imya}: + накатано")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 62)
    print("СВОЙ СТОЛ У КАЖДОГО ЦЕХА" +
          ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    if not SOVET.exists() or "_treydery" not in SOVET.read_text(
            encoding="utf-8"):
        print("x сперва patch_zakon_kartridzha.py — Совет ещё со списком")
        return 1

    ok = True
    print("\nстол:")
    ok &= pravit(HOOKS, HOOKS_STEZHKI, suho, "hooks.py")
    print("\nСовет:")
    ok &= pravit(SOVET, SOVET_STEZHKI, suho, "council.py")

    print("-" * 62)
    if not ok:
        return 1
    if suho:
        print("Это был показ. Накатывать: "
              "python patch_svoy_stol_ceha.py --sdelat")
        return 0
    print("Жми РЫНОК. В чёрном окне будет «стол сохранён (торговый_хаос)»,")
    print("а сам файл ляжет в цеха/торговый_хаос/данные/.")
    print("Общий стол останется на месте — на всякий случай.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
