# -*- coding: utf-8 -*-
"""
prisedanie_pravda.py — стол говорит правду о приседающем.

Что было: на столе стояло «приседающий бар: True» — а считалось это как
«был ли хоть один приседающий во всей истории». То есть True всегда, на
любом баре. Синди честно читала стол и честно верила: приседающий есть.
14.07 00:00 разворотник был ФЕЙКОМ по MFI, последний приседающий —
11.07 04:00, за пять баров, — а она вошла «три условия сошлись».

Правило Шефа 23.09: приседающий считается в пределах трёх баров — на
самом разворотном баре или не раньше чем за два бара до него
(разворотник — третий). Один или дорожка — всё равно.

Что делает:
  1. Биржа/stol.py — вместо True/False стол пишет словами:
       «есть — на этом баре» · «есть — за 2 бар(а) до этого бара (…)» ·
       «есть — дорожка: 2 приседающих за последние 3 бара …» ·
       «нет — последний 07.11 04:00, 5 бар(ов) назад (дальше трёх баров)»
  2. Биржа/hooks.py — окно городского автопереезда заявки выравнивается
     под то же правило: три бара (разворотник и два до него).

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет оба, потом пишет. Копии `.bak_prisedanie`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "PRISEDANIE_PRAVDA_V1"
HELPER = '# PRISEDANIE_PRAVDA_V1 (слово Шефа 23.09): приседающий считается, если\n# он в пределах ТРЁХ баров — на самом разворотном баре или не раньше\n# чем за два бара до него (разворотник — третий). Один или дорожка —\n# всё равно. Раньше здесь стояло bool(last_squat) — «был ли хоть один\n# приседающий во всей истории», то есть True всегда, на любом баре.\n_PRISED_OKNO = 3\n\n\ndef _prisedanie(md: dict, bars, timeframe: str = "") -> str:\n    """Приседающий словами: есть ли в окне трёх баров и где последний."""\n    last = ((md or {}).get("squat") or {}).get("last_squat") or {}\n    if not last:\n        return "нет — на этом этаже ни одного"\n    d_last = str(last.get("date") or "")\n    nazad = None\n    v_okne = []\n    if bars:\n        try:\n            _daty = [str(b.get("date")) for b in bars]\n            if d_last in _daty:\n                nazad = len(_daty) - 1 - _daty.index(d_last)\n            _hvost = bars[-(_PRISED_OKNO + 1):]\n            for _k in range(1, len(_hvost)):\n                _b, _pb = _hvost[_k], _hvost[_k - 1]\n                if not _b.get("volume") or not _pb.get("volume"):\n                    continue\n                _m = (_b["high"] - _b["low"]) / _b["volume"]\n                _pm = (_pb["high"] - _pb["low"]) / _pb["volume"]\n                if _b["volume"] > _pb["volume"] and _m < _pm:\n                    v_okne.append(len(_hvost) - 1 - _k)\n        except Exception:\n            nazad = None\n    if nazad is None:\n        # баров под рукой нет — считаем по часам этажа\n        try:\n            from datetime import datetime\n            _f = "%Y.%m.%d %H:%M"\n            _chas = {"M1": 1 / 60, "M5": 5 / 60, "M15": 0.25, "M30": 0.5,\n                     "H1": 1, "H4": 4, "D1": 24, "W1": 168}.get(\n                str(timeframe or md.get("timeframe") or "H1").upper(), 1)\n            from datetime import timedelta\n            _t = datetime.strptime(d_last, _f)\n            _konec = datetime.strptime(str(md.get("bar_time")), _f)\n            _shag = timedelta(hours=_chas)\n            nazad = 0\n            # выходные не в счёт: в субботу и воскресенье баров нет\n            while _t < _konec and nazad < 500:\n                _t += _shag\n                if _t.weekday() < 5:\n                    nazad += 1\n        except Exception:\n            nazad = None\n    kogda = d_last[5:] if len(d_last) >= 16 else d_last\n    if nazad is not None and 0 <= nazad < _PRISED_OKNO:\n        if len(v_okne) >= 2:\n            return (f"есть — дорожка: {len(v_okne)} приседающих за последние "\n                    f"{_PRISED_OKNO} бара, последний {kogda}")\n        if nazad == 0:\n            return "есть — на этом баре"\n        return f"есть — за {nazad} бар(а) до этого бара ({kogda})"\n    if nazad is None:\n        return f"не ясно — последний {kogda}"\n    return (f"нет — последний {kogda}, {nazad} бар(ов) назад "\n            f"(дальше трёх баров)")\n\n\n'
ZAMENY = {
    os.path.join("Биржа", "stol.py"): [
        ('        "приседающий_бар": bool((md.get("squat") or {}).get("last_squat")),\n',
         '        # PRISEDANIE_PRAVDA_V1: словами, в окне трёх баров.\n'
         '        "приседающий_бар": _prisedanie(md, bars, timeframe),\n'),
        ("def slovami(stol: dict) -> str:\n",
         HELPER + "def slovami(stol: dict) -> str:\n"),
    ],
    os.path.join("Биржа", "hooks.py"): [
        ("_OKNO_BAROV_PRISED = 3\n",
         "# PRISEDANIE_PRAVDA_V1 (слово Шефа 23.09): три бара — разворотник и\n"
         "# два до него. Было 3 — это четыре бара (0..3).\n"
         "_OKNO_BAROV_PRISED = 2\n"),
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
        ast.parse(novyy)
        gotovo.append((put, novyy, crlf))
    if not gotovo:
        print("✓ Всё уже стоит. Ничего не менял.")
        return
    for put, novyy, crlf in gotovo:
        bak = put + ".bak_prisedanie"
        if not os.path.exists(bak):
            shutil.copy2(put, bak)
        with open(put, "wb") as f:
            f.write((novyy.replace("\n", "\r\n") if crlf else novyy)
                    .encode("utf-8"))
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Стол говорит о приседающем словами, окно — три бара.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
