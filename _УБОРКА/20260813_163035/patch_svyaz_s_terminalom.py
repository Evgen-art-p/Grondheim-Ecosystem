#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SVYAZ_S_TERMINALOM_V1
"""
СВЯЗЬ С ТЕРМИНАЛОМ — кнопка ТЕРМИНАЛ не открывала соединение.

    python patch_svyaz_s_terminalom.py            посмотреть
    python patch_svyaz_s_terminalom.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

ЧТО БЫЛО НЕ ТАК (моя ошибка)

    Функция в насосе называется `_terminal()`, и я решил, что она
    поднимает связь с терминалом. А она только ИМПОРТИРУЕТ библиотеку —
    соединение не открывает: этим занимается `mt5.initialize()`, и все
    рабочие места зовут его сами.

    Кнопка ТЕРМИНАЛ его не звала. Терминал молчал на всё: список
    инструментов приходил пустым, баров не было — а выглядело это как
    «на связи, но котировок не даёт». Жалоба была честная, причина —
    моя.

ЧТО СТАНЕТ

    · связь открывается по-настоящему, и если не открылась — кабинет
      скажет, что именно ответил терминал, а не отделается общей
      фразой;
    · инструмент, не отмеченный в обзоре рынка, сперва берётся в обзор:
      без этого он баров не отдаёт;
    · если инструменты видны, а баров нет — так и написано, с числом
      найденных инструментов. По этой строке сразу видно, где рвётся:
      на связи, на логине или на истории.
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
UI = KOREN / "Биржа" / "ui_torg.py"
MARKER = "# SVYAZ_S_TERMINALOM_V1 - marker"
BAK = ".bak_svyaz"

STEZHKI = (
    ("связь открывается", '        mt5 = _mf._terminal()\n        if mt5 is None:\n            return [], ("терминал молчит: не установлен MetaTrader5 для "\n                        "питона или сам терминал не запущен")\n\n        try:\n            vse = mt5.symbols_get() or []\n        except Exception as e:\n            return [], f"терминал не отдал список инструментов: {e}"\n\n        vidnye = [s for s in vse if getattr(s, "visible", False)]\n        if not vidnye:\n            vidnye = list(vse)[:20]      # обзор пуст — берём хоть что-то\n\n', '        mt5 = _mf._terminal()\n        if mt5 is None:\n            return [], ("MetaTrader5 для питона не установлен — "\n                        "поставь его и перезапусти город")\n\n        # SVYAZ_S_TERMINALOM_V1: _terminal() только ИМПОРТИРУЕТ библиотеку,\n        # связь он не открывает — имя обмануло. Без initialize() терминал\n        # молчит на всё: список инструментов пуст, баров нет, а выглядит\n        # это как «на связи, но котировок не даёт».\n        try:\n            if not mt5.initialize():\n                oshibka = ""\n                try:\n                    oshibka = f" ({mt5.last_error()})"\n                except Exception:\n                    pass\n                return [], ("терминал не отвечает" + oshibka +\n                            ". Запусти MetaTrader и войди в счёт — "\n                            "питон говорит с УЖЕ ОТКРЫТЫМ терминалом")\n        except Exception as e:\n            return [], f"связь с терминалом не открылась: {e}"\n\n        try:\n            vse = mt5.symbols_get() or []\n        except Exception as e:\n            try:\n                mt5.shutdown()\n            except Exception:\n                pass\n            return [], f"терминал не отдал список инструментов: {e}"\n\n        if not vse:\n            try:\n                mt5.shutdown()\n            except Exception:\n                pass\n            return [], ("терминал на связи, но инструментов не отдал — "\n                        "проверь, что счёт залогинен")\n\n        vidnye = [s for s in vse if getattr(s, "visible", False)]\n        if not vidnye:\n            vidnye = list(vse)[:20]      # обзор пуст — берём хоть что-то\n\n'),
    ("инструмент в обзор", '            for tf in _TERM_ETAZHI:\n                kod = _mf._TF_MAP.get(tf)\n                if kod is None:\n                    continue\n                try:\n                    bary = mt5.copy_rates_from_pos(imya, kod, 0, 2)\n                except Exception:\n                    bary = None\n', '            # SVYAZ_S_TERMINALOM_V1: инструмент, не отмеченный в обзоре\n            # рынка, баров не отдаёт — сперва берём его в обзор.\n            try:\n                info = mt5.symbol_info(imya)\n                if info is not None and not getattr(info, "visible", True):\n                    mt5.symbol_select(imya, True)\n            except Exception:\n                pass\n            for tf in _TERM_ETAZHI:\n                kod = _mf._TF_MAP.get(tf)\n                if kod is None:\n                    continue\n                try:\n                    bary = mt5.copy_rates_from_pos(imya, kod, 0, 2)\n                except Exception:\n                    bary = None\n'),
    ("внятная жалоба", '        if not aktivy:\n            return [], ("терминал на связи, но ни один этаж не отдал баров "\n                        "— выходной или инструменты не открыты в обзоре")\n', '        if not aktivy:\n            return [], (f"терминал на связи, инструментов видит "\n                        f"{len(vidnye)}, но баров не отдал ни по одному — "\n                        f"похоже, счёт не залогинен или брокер не даёт "\n                        f"историю")\n'),
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

    print("=" * 60)
    print("СВЯЗЬ С ТЕРМИНАЛОМ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 60)

    if not UI.exists():
        print("x не вижу Биржа/ui_torg.py — запускай из КОРНЯ")
        return 1
    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0
    if "_sobrat_iz_terminala" not in tekst:
        print("x кнопки ТЕРМИНАЛ ещё нет — сперва patch_polka_iz_terminala")
        return 1

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x якорь «{nazv}» найден {n} раз — файл не трогаю")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_torg.py"):
        return 1

    if suho:
        print("\nЭто был показ. Накатывать: "
              "python patch_svyaz_s_terminalom.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nЖми ТЕРМИНАЛ ещё раз. Терминал при этом должен быть")
    print("ЗАПУЩЕН и залогинен — питон говорит с открытым окном,")
    print("сам он терминал не поднимает.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
