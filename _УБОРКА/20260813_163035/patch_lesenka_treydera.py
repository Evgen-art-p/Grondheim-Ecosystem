#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TREYDER_HODIT_PO_ETAZHAM_V1
"""
ТРЕЙДЕР ХОДИТ ПО ЭТАЖАМ — символ от Шефа, этажи его.

    python patch_lesenka_treydera.py            посмотреть
    python patch_lesenka_treydera.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

КАК БЫЛО

    Трейдер видел ОДИН этаж — тот, что выбран на полке. Сверху ему
    падал только компас: куда смотрит старший Аллигатор. Лесенка в
    городе есть (`mt5_feed.step_down`), но она была рукой Искры, а
    Искру упразднили шестого — теперь по ней никто не спускается.

КАК СТАНЕТ

    Инструмент назначает Шеф. Этажи — дело трейдера.

    Стол накрывается сразу на три рабочих: D1, H4, H1. Все три
    приходят ему числами — Аллигатор, AO, фракталы, натяжение, цена.
    Он смотрит сверху вниз и сам говорит в narrative, на каком
    работает сегодня и спускается ли ниже.

    Цены входа и стопа от этажа не зависят — они одни для всех. На
    разных этажах видны разные вещи, вот и вся разница.

ЧЕСТНО ПРО ЦЕНУ

    Два лишних накрытия стола на каждый прогон каждого трейдера: не
    модель, а поход за барами. На троих — шесть лишних запросов за бар.
    Голов это не добавляет, деньги те же; время прогона чуть длиннее.

    Кадр по-прежнему рисуется по этажу с полки — картинок три не шлём,
    это было бы втрое дороже по зрению. Смотрит на другой этаж — судит
    по числам.
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
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
MARKER = "# TREYDER_HODIT_PO_ETAZHAM_V1 - marker"
BAK = ".bak_lesenka"

STEZHKI = (
    ("лесенка накрывается", '    iskra_tf = table.get("iskra", {}).get("found_timeframe")\n    if iskra_tf:\n        timeframe = iskra_tf\n', '    iskra_tf = table.get("iskra", {}).get("found_timeframe")\n    if iskra_tf:\n        timeframe = iskra_tf\n\n    # ── ЛЕСЕНКА (TREYDER_HODIT_PO_ETAZHAM_V1) ───────────────────\n    # Раньше трейдер видел ОДИН этаж — тот, что выбран на полке, — и\n    # сверху компас: куда смотрит старший Аллигатор. Спускаться по\n    # лесенке было делом Искры, а Искры больше нет.\n    #\n    # Теперь: инструмент назначает Шеф, а этажи — дело трейдера. Стол\n    # накрывается на три рабочих этажа сразу, и он сам говорит, на\n    # каком работает. Цены входа и стопа от этажа не зависят — они\n    # одни для всех; на разных этажах видны разные вещи, вот и всё.\n    _RABOCHIE_ETAZHI = ("D1", "H4", "H1")\n\n    def _lesenka_slovami() -> str:\n        try:\n            import stol as _s2\n        except Exception:\n            return ""\n        L = ["=== ЛЕСЕНКА · три рабочих этажа этого инструмента ===",\n             f"Инструмент {symbol} назначен Шефом. Этажи — твои."]\n        for _tf in _RABOCHIE_ETAZHI:\n            try:\n                _t2 = _s2.nakryt(symbol, _tf, self_key=_SELF_KEY)\n                _tekst = _s2.slovami(_t2)\n            except Exception as _e2:\n                _tekst = f"этаж не накрылся: {_e2}"\n            _metka = "   ← на нём кадр перед тобой" if _tf == timeframe else ""\n            L.append(f"\\n-- {_tf}{_metka} --\\n{_tekst}")\n        L.append(\n            "\\nСтарший этаж говорит о направлении, рабочий — о входе, "\n            "младший — о точности. Спускаться или нет, и на каком "\n            "работать сегодня — решаешь ты. Скажи это в narrative "\n            "прямо: «работаю по H4», «спускаюсь на H1, там видно "\n            "приседающий». Кадр нарисован по этажу с полки; если "\n            "смотришь на другой — суди по числам, они честные.\\n")\n        return "\\n".join(L) + "\\n"\n'),
    ("лесенка ложится на стол", '        + "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\\n"\n', '        + _lesenka_slovami()\n        + "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\\n"\n'),
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 62)
    print("ТРЕЙДЕР ХОДИТ ПО ЭТАЖАМ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    if not SLOTY.exists():
        print("x не вижу слоты торгового_хаоса — запускай из КОРНЯ")
        return 1

    vse_ok = True
    for slot in ("A06", "A07", "A08"):
        put = SLOTY / slot / "мозг.py"
        if not put.exists():
            print(f"  {slot}: мозга нет — пропускаю")
            continue
        tekst = put.read_text(encoding="utf-8")
        if MARKER in tekst:
            print(f"  {slot}: уже накатано")
            continue
        sboy = False
        for nazv, staroe, novoe in STEZHKI:
            n = tekst.count(staroe)
            if n != 1:
                print(f"  x {slot}: якорь «{nazv}» найден {n} раз — не трогаю")
                sboy = True
                vse_ok = False
                break
            tekst = tekst.replace(staroe, novoe, 1)
            print(f"    · {nazv}")
        if sboy:
            continue
        tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
        if not proverit_python(tekst, slot):
            vse_ok = False
            continue
        if suho:
            print(f"  {slot}: + готов")
            continue
        shutil.copy2(put, put.with_suffix(put.suffix + BAK))
        put.write_text(tekst, encoding="utf-8")
        print(f"  {slot}: + накатано")

    print("-" * 62)
    if not vse_ok:
        return 1
    if suho:
        print("Это был показ. Накатывать: "
              "python patch_lesenka_treydera.py --sdelat")
        return 0
    print("Жми РЫНОК и смотри narrative: он должен назвать этаж, на")
    print("котором работает. Спроси потом в разговоре — «почему этот".replace(chr(34), ""))
    print("этаж?» — и услышишь, как он читает лесенку.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
