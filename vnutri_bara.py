# -*- coding: utf-8 -*-
"""
vnutri_bara.py — вход и стоп в одной свече: город смотрит внутрь.

Слово Шефа 24.09 («уже хочу»). Если заявка сработала и стоп задет в
одной и той же свече рабочего этажа, по самой свече не видно, что было
раньше. Город всегда брал худший вариант — «сработала, потом выбило».
Теперь он заглядывает в младший этаж из test_data (M15 с 2022 года;
где его нет — H1 с 2010-го): находит, где сработала заявка, и смотрит,
задет ли стоп ПОСЛЕ этого до конца свечи.
  · задет — стоп, как и раньше (в логе — когда именно);
  · не задет — позиция живёт дальше;
  · вход и стоп в одной младшей свече — по-прежнему худший вариант;
  · младших данных нет — как раньше.

Пример 06.11.2024 (ночь выборов): по M15 вход сработал в 00:00, стоп
задет в 01:45 — выбило честно, город это теперь покажет.

Что правит: Биржа/hooks.py (расчёт позиций).

Запуск: положить в корень репы, запустить. Копия `.bak_vnutri_bara`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "VNUTRI_BARA_V1"
HELPER = '# ════════════════════════════════════════════════════════════\n# VNUTRI_BARA_V1 — вход и стоп в одном баре: заглянуть внутрь.\n# ════════════════════════════════════════════════════════════\n# Слово Шефа 24.09 («уже хочу»). Заявка сработала и стоп задет в ОДНОЙ\n# свече рабочего этажа — по самой свече не видно, что было раньше.\n# Город брал худший вариант. Теперь смотрит младший этаж из\n# test_data (M15, если нет — H1): где сработала заявка и был ли стоп\n# задет ПОСЛЕ этого до конца свечи. Младшая свеча, где задеты и вход,\n# и стоп сразу, — по-прежнему худший вариант. Данных нет — как раньше.\n_VNUTRI_KESH: dict = {}\n\n\ndef _vnutri_bara(symbol, timeframe, bar_time, direction, entry, stop):\n    """→ ("стоп", когда) | ("живёт", когда_вход) | (None, почему)."""\n    try:\n        from datetime import datetime as _dtv, timedelta as _tdv\n        from bisect import bisect_left as _bl\n        from feed_source import _find_csv as _fcsv\n        from williams_core import read_mt5_csv as _rcsv\n    except Exception as e:\n        return None, f"нечем смотреть ({e})"\n    minut = {"H1": 60, "H2": 120, "H4": 240, "H6": 360, "H8": 480,\n             "H12": 720, "D1": 1440}.get(str(timeframe or "").upper())\n    if not minut or entry is None or stop is None:\n        return None, "этаж не тот"\n    try:\n        t0 = _dtv.strptime(str(bar_time)[:16], "%Y.%m.%d %H:%M")\n    except Exception:\n        return None, "время бара не читается"\n    t1 = t0 + _tdv(minutes=minut)\n    s0, s1 = t0.strftime("%Y.%m.%d %H:%M"), t1.strftime("%Y.%m.%d %H:%M")\n    long_ = str(direction).upper() == "LONG"\n    for mlad, m_min in (("M15", 15), ("H1", 60)):\n        if m_min >= minut:\n            continue\n        try:\n            put = _fcsv(symbol, mlad)\n        except Exception:\n            put = None\n        if not put:\n            continue\n        kl = str(put)\n        if kl not in _VNUTRI_KESH:\n            try:\n                _b = _rcsv(kl)\n                _VNUTRI_KESH[kl] = (_b, [str(x.get("date")) for x in _b])\n            except Exception:\n                continue\n        bars, daty = _VNUTRI_KESH[kl]\n        i = _bl(daty, s0)\n        vn = []\n        while i < len(bars) and daty[i] < s1:\n            vn.append(bars[i])\n            i += 1\n        if not vn:\n            continue\n        aktiv = None\n        for b in vn:\n            vh = (b["high"] >= entry) if long_ else (b["low"] <= entry)\n            st = (b["low"] <= stop) if long_ else (b["high"] >= stop)\n            if aktiv is None:\n                if not vh:\n                    continue\n                aktiv = b["date"]\n                if st:\n                    return "стоп", f"{mlad} {b[\'date\']} (вход и стоп в одной {mlad})"\n                continue\n            if st:\n                return "стоп", f"{mlad} {b[\'date\']}"\n        if aktiv is None:\n            return None, f"{mlad}: вход внутри свечи не найден"\n        return "живёт", f"{mlad}: вход {aktiv}, стоп до конца свечи не задет"\n    return None, "младшего этажа за это время нет"\n\n\n'
_STOP = (
    '        elif reason is None and direction == "SHORT" and high is not None and high >= stop:\n'
    '            exit_price, reason = stop, "STOP_LOSS"\n'
)
ZAMENY = {
    os.path.join("Биржа", "hooks.py"): [
        ('\ndef _settle_positions(', '\n' + HELPER + 'def _settle_positions('),
        (_STOP, _STOP +
         '        # VNUTRI_BARA_V1: заявка сработала на ЭТОЙ же свече, и стоп\n'
         '        # тоже задет — смотрим внутрь по младшему этажу.\n'
         '        if (reason == "STOP_LOSS"\n'
         '                and str(pos.get("opened_at") or "") == str(bar_time)):\n'
         '            _vv, _kak = _vnutri_bara(symbol, timeframe, bar_time,\n'
         '                                     direction, entry, stop)\n'
         '            if _vv == "живёт":\n'
         '                exit_price, reason = None, None\n'
         '                print(f"[ВНУТРИ БАРА] 🔍 {pos.get(\'trader\')} {direction}: "\n'
         '                      f"{_kak} — позиция живёт")\n'
         '            elif _vv == "стоп":\n'
         '                print(f"[ВНУТРИ БАРА] 🔍 {pos.get(\'trader\')} {direction}: "\n'
         '                      f"вошла, стоп задет {_kak} — выбило честно")\n'
         '            else:\n'
         '                print(f"[ВНУТРИ БАРА] 🔍 {pos.get(\'trader\')} {direction}: "\n'
         '                      f"{_kak} — беру худший вариант")\n'),
    ],
}


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if all(os.path.isfile(os.path.join(papka, p))
                        for p in ZAMENY) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        if godnyy(papka):
            return papka
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = os.path.join(koren, imya)
                if godnyy(p) and p not in kandidaty:
                    kandidaty.append(p)
        except Exception:
            pass
    if len(kandidaty) == 1:
        otv = input(f"Нашёл: {kandidaty[0]}\nЭтот? (Enter — да, н — нет): ")
        if otv.strip().lower() not in ("н", "n", "нет", "no"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p}")
        otv = input("Какой? Цифра: ").strip()
        if otv.isdigit() and 1 <= int(otv) <= len(kandidaty):
            return kandidaty[int(otv) - 1]
    otv = input("Не нашёл репу. Перетащи сюда папку репы и нажми Enter: ")
    otv = otv.strip().strip('"').strip("'")
    return godnyy(otv) if otv else None


def main():
    repa = nayti()
    if not repa:
        print("✗ Репу не нашёл. Ничего не менял.")
        return
    gotovo = []
    for otn, zameny in ZAMENY.items():
        put = os.path.join(repa, otn)
        with open(put, "rb") as f:
            syroe = f.read()
        crlf = b"\r\n" in syroe
        tekst = syroe.decode("utf-8").replace("\r\n", "\n")
        if METKA in tekst:
            print(f"· {otn}: уже стоит")
            continue
        novyy = tekst
        for staroe, novoe in zameny:
            if novyy.count(staroe) != 1:
                print(f"✗ {otn}: не нашлось место правки — пришли Брату "
                      f"этот файл.\n  Ничего не менял.")
                return
            novyy = novyy.replace(staroe, novoe)
        if otn.endswith(".py"):
            ast.parse(novyy)
        gotovo.append((put, novyy, crlf))
    if not gotovo:
        print("✓ Всё уже стоит. Ничего не менял.")
        return
    for put, novyy, crlf in gotovo:
        bak = put + ".bak_vnutri_bara"
        if not os.path.exists(bak):
            shutil.copy2(put, bak)
        with open(put, "wb") as f:
            f.write((novyy.replace("\n", "\r\n") if crlf else novyy)
                    .encode("utf-8"))
        try:
            if put.endswith(".py"):
                py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Вход и стоп в одной свече — город смотрит внутрь по M15.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
