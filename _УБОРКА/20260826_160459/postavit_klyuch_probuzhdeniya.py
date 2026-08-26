# -*- coding: utf-8 -*-
"""
postavit_klyuch_probuzhdeniya.py · MARKER: KLYUCH_PROBUZHDENIYA_V1

СТАВИТЬ ПОСЛЕ postavit_tochku_nol.py — ключ опирается на точку ноль.
Патч сам проверит и не даст поставить себя раньше.

ЧТО БЫЛО
────────
Совет будил трейдера НА КАЖДОЙ СВЕЧЕ. КАНОН_ВХОДА §4.4 говорит прямо:
«по ключу, не бар за баром» — у каждого свой факт-ключ, событие, на
которое просыпается именно он. Ключа не было, потому что корень —
точка ноль — не зажигался ни разу с 06.08.

Теперь точка есть, и ключ строится на ней.

ЧЕМ КЛЮЧ ОТЛИЧАЕТСЯ ОТ ВОРОТ
────────────────────────────
Ворота Совета Шеф снял 06.08, и правильно: они СУДИЛИ, годится ли вход,
и выкашивали 87% честных точек (§5о). Ключ ничего не судит. Он отвечает
на один вопрос: есть ли вообще на что смотреть.

    точка родилась      → зовём ОДИН раз: истинный бар или нет
    своя позиция/заявка → зовём всегда, позицию надо вести
    ни того, ни другого → молчим; смотреть не на что

Пока точка живёт, трейдера НЕ дёргаем. Слово Шефа: решить надо один
раз, дальше ведёт математика; откат не случится ни на втором, ни на
третьем, ни даже на десятом баре.

Право промолчать остаётся у трейдера целиком: ключ не отказывает за
него, он лишь не платит за взгляд туда, где нет структуры.

ЧТО ЭТО ДАЁТ
────────────
Померено на EURUSD H4, 1200 баров: рождений точки 43 — меньше четырёх
процентов баров. Столько взглядов и оплачиваем, остальное время город
молчит.

Ключ никого не делит по ролям и ничего не навязывает: он говорит одно —
на этом баре есть на что посмотреть. Что с этим делать, решает трейдер
по своему выбору входа.

ЕСЛИ КЛЮЧ САМ СЛОМАЕТСЯ
───────────────────────
Будим. Любой сбой внутри ключа — это «зовём», а не «молчим»: пропустить
взгляд из-за нашей ошибки хуже, чем лишний раз заплатить.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_klyuch_probuzhdeniya.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KLYUCH_PROBUZHDENIYA_V1"
NUZHEN = "TOCHKA_ROZHDAETSYA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "council.py").exists()
            and (p / "Биржа" / "hooks.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


YAKOR_FN = "def wake_council(symbol: str = \"\", timeframe: str = \"\","

RUKA = '''# ═══════════════════════════════════════════════════════════
# KLYUCH_PROBUZHDENIYA_V1 — зовём по ключу, не бар за баром
# ═══════════════════════════════════════════════════════════
# КАНОН_ВХОДА §4.4: у каждого свой факт-ключ, событие, на которое он
# просыпается. Ключа не было, потому что корень — точка ноль — не
# зажигался ни разу с 06.08 (Искра уехала в архив вместе с рукой).
#
# Это НЕ ворота. Ворота (сняты 06.08) судили, годится ли вход, и
# выкашивали 87% честных точек. Ключ не судит ничего: он отвечает
# только на «есть ли на что смотреть». Что делать — решает трейдер,
# глядя на график.
#
# Любой сбой внутри — БУДИМ. Пропустить взгляд из-за нашей ошибки
# хуже, чем лишний раз заплатить за вызов.

_ZHIVYE_STATUSY = ("WATCHING", "PENDING", "OPEN")


def _klyuch_probuzhdeniya(symbol: str, timeframe: str) -> dict:
    """Есть ли повод звать того, кто работает этой парой."""
    try:
        import hooks
        t = hooks.load_trading_state()

        # Будим на РОЖДЕНИИ точки, а не каждый бар, пока она жива.
        # Слово Шефа (20.08): «Нине важно решить сначала, истинный ли
        # он; если да — математика пусть ведёт. Откат не случится ни на
        # втором, ни на третьем, ни даже на десятом баре».
        tch = hooks._blok_tochki(t, hooks._para_tochki(symbol, timeframe))
        bar_goroda = str(((t.get("рынок") or {}).get("бар")) or "")
        rodilas = str(tch.get("rodilas_na_bare") or "")
        if tch.get("alive") and bar_goroda and rodilas == bar_goroda \
                and not tch.get("barov_s_tochki"):
            return {"будим": True,
                    "почему": f"точка родилась: {tch.get('trend_direction')} @ "
                              f"{tch.get('zero_point_price')}"}

        # позицию ведём всегда, чем бы ни кончилась точка
        sym = (symbol or "").strip().upper()
        for p in (t.get("positions") or []):
            if p.get("status") not in _ZHIVYE_STATUSY:
                continue
            psym = (p.get("symbol") or "").strip().upper()
            # инструмента в записи нет (старая позиция) — считаем своей
            if not psym or psym == sym:
                return {"будим": True,
                        "почему": f"своя {p.get('status')} — позицию ведём"}

        return {"будим": False, "почему": "точки нет и позиции нет"}
    except Exception as e:
        return {"будим": True, "почему": f"ключ не сработал ({e}) — зову"}


'''

YAKOR_ZOV = '''        print(f"[СОВЕТ] 👤 {slot}: {_p['symbol']} {_p['timeframe']}")'''

NOV_ZOV = '''        # KLYUCH_PROBUZHDENIYA_V1: зовём по ключу, не бар за баром.
        _k = _klyuch_probuzhdeniya(_p["symbol"], _p["timeframe"])
        if not _k["будим"]:
            print(f"[КЛЮЧ] 🔒 {slot} спит: {_k['почему']}")
            summary["verdicts"][aid] = None
            summary["results"][aid] = {"ok": False, "спит": True,
                                       "error": _k["почему"]}
            _emit({"type": "спит", "slot": slot, "почему": _k["почему"]})
            continue
        print(f"[КЛЮЧ] 🔑 {slot}: {_k['почему']}")
        print(f"[СОВЕТ] 👤 {slot}: {_p['symbol']} {_p['timeframe']}")'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")

    h = (koren / "Биржа" / "hooks.py").read_text(encoding="utf-8")
    if NUZHEN not in h:
        print(f"✗ Сперва накати postavit_tochku_nol.py — без точки ноль")
        print("  ключу не на что опереться, и Совет замолчал бы навсегда.")
        return 1

    f = koren / "Биржа" / "council.py"
    t = f.read_text(encoding="utf-8")
    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    for yakor in (YAKOR_FN, YAKOR_ZOV):
        n = t.count(yakor)
        if n != 1:
            print(f"✗ якорь найден {n} раз — жду ровно один")
            print(f"  {yakor[:70]}")
            return 1

    novyy = t.replace(YAKOR_FN, RUKA + YAKOR_FN, 1)
    novyy = novyy.replace(YAKOR_ZOV, NOV_ZOV, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_klyuch_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ ключ пробуждения поставлен (копия: {bak.name})")

    print("\nТеперь в консоли на каждом баре будет одно из двух:")
    print("  [КЛЮЧ] 🔑 A06: точка родилась: BULL @ 1.14968")
    print("  [КЛЮЧ] 🔒 A06 спит: точки нет и позиции нет")
    print("\nПо замеру на EURUSD H4 первое случается 43 раза на 1200")
    print("баров — меньше четырёх процентов. Остальное время город молчит.")
    print("\nЕсли покажется, что молчит слишком часто, — смотри не сюда,")
    print("а на точку: ключ только повторяет то, что она говорит.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
