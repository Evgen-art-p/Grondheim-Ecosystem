# -*- coding: utf-8 -*-
"""
postavit_volnu_na_stol.py · MARKER: VOLNA_NA_STOLE_V1

ЧТО ПОКАЗАЛ ОТЧЁТ (20.08, EURUSD H4)
────────────────────────────────────
Событие впервые дошло до трейдера:

    [КЛЮЧ] 🔑 A06: волна 1 кончилась @ 1.15959 (16 бар. от точки)

А Нина на этом самом баре ответила:

    «...есть бычий разворотный бар и приседающий, но НЕТ ЧЁТКОЙ ПЕРВОЙ
     ВОЛНЫ И ОТКАТА К НЕЙ. НАБЛЮДАЮ: за формированием первой бычьей
     волны...»

Она не спорит и не тупит. На СТОЛЕ конца волны нет. Событие живёт в
ключе и в консоли, а стол показывает только точку ноль. Мы её позвали
и не сказали, зачем позвали.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. КОНЕЦ ВОЛНЫ 1 — НА СТОЛ, координатой, как сама точка:

       ВОЛНА 1: BULL от 1.14968 → макушка 1.15959
                16 бар(ов) от точки   сейчас 1.15840

   Ни одного суждения: где началась, где кончилась, сколько прошло,
   где цена теперь. Что это значит и стоит ли ждать отката — решает
   тот, кто смотрит.

2. ОТЧЁТ ПЕРЕСТАЁТ ВРАТЬ ДАТАМИ. Места 10, 11 и 12 были подписаны
   одинаково — 2025.11.21 12:00, — хотя это три разных бара; видно по
   дневнику самой Нины, где стоит 2025.11.27 04:00. Отчёт клеил шагам
   наблюдения дату кандидата. Теперь берётся настоящий бар, на котором
   трейдера спросили, а дата места остаётся отдельной колонкой.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_volnu_na_stol.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VOLNA_NA_STOLE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "stol.py").exists()
            and (p / "Биржа" / "otchyot.py").exists())


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


# ── 1. стол: конец волны 1 ───────────────────────────────────

S_YAKOR = '''        "структура_позади_баров": isk.get("struktura_pozadi"),
        "цена_сейчас": ((md or {}).get("price") or {}).get("close"),'''

S_NOV = '''        "структура_позади_баров": isk.get("struktura_pozadi"),
        # VOLNA_NA_STOLE_V1: конец первой волны — координатой, как сама
        # точка. Трейдера будили словами «волна 1 кончилась», а на столе
        # этого не было, и он честно отвечал «первой волны нет».
        "волна_1": (lambda _k: ({
            "кончилась": True,
            "макушка": _k.get("цена"),
            "бар": _k.get("бар"),
            "баров_от_точки": _k.get("баров_от_точки"),
        } if _k else {"кончилась": False}))(isk.get("konec_volny_1") or {}),
        "цена_сейчас": ((md or {}).get("price") or {}).get("close"),'''

S_YAKOR2 = '''            if _t.get("жива") else "ТОЧКА НОЛЬ: нет"))(
                p.get("точка_ноль") or {}),'''

S_NOV2 = '''            if _t.get("жива") else "ТОЧКА НОЛЬ: нет"))(
                p.get("точка_ноль") or {}),
        # VOLNA_NA_STOLE_V1: кончилась первая волна — говорим где,
        # а не молчим. Трейдера будили словами «волна 1 кончилась»,
        # а на столе этого не было, и он честно отвечал «первой
        # волны нет».
        (lambda _v, _t: (
            f"ВОЛНА 1: от {_t.get('цена')} → макушка {_v.get('макушка')}"
            f"   {_v.get('баров_от_точки')} бар(ов) от точки"
            f"   бар {_v.get('бар')}"
            if _v.get("кончилась") else "ВОЛНА 1: ещё идёт"))(
                (p.get("точка_ноль") or {}).get("волна_1") or {},
                p.get("точка_ноль") or {}),'''

# ── 2. отчёт: настоящий бар вместо даты места ────────────────

O_YAKOR = '''        self.mesta.append({
            "когда_на_рынке": k.get("дата", ""),'''

O_NOV = '''        # VOLNA_NA_STOLE_V1: даты. Шаги наблюдения подписывались датой
        # КАНДИДАТА — в прогоне 20.08 места 10, 11 и 12 вышли с одной
        # датой 2025.11.21 12:00, хотя это три разных бара (видно по
        # дневнику самой Нины: там стоит 2025.11.27 04:00).
        # Берём бар, на котором трейдера спросили НА САМОМ ДЕЛЕ; дату
        # места оставляем отдельно, она тоже нужна.
        _nastoyashchiy_bar = ""
        try:
            from hooks import load_trading_state as _lts
            _nastoyashchiy_bar = str(
                ((_lts() or {}).get("рынок") or {}).get("бар") or "")
        except Exception:
            pass
        self.mesta.append({
            "когда_на_рынке": _nastoyashchiy_bar or k.get("дата", ""),
            "место_найдено_на": k.get("дата", ""),'''


def _pravit(f: Path, pary: list, imya: str) -> bool:
    t = f.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"· {imya}: маркер уже стоит — пропускаю")
        return True
    for yakor, _ in pary:
        n = t.count(yakor)
        if n != 1:
            print(f"✗ {imya}: якорь найден {n} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return False
    novyy = t
    for yakor, zamena in pary:
        novyy = novyy.replace(yakor, zamena, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ {imya}: после правки не разбирается — {e}")
        return False
    if SUHO:
        print(f"· {imya}: правка готова (сухой прогон)")
        return True
    bak = f.with_suffix(f".py.bak_volnastol_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ {imya}: НЕ компилируется ({e}) — откатил из {bak.name}")
        return False
    print(f"✓ {imya}: правка легла (копия: {bak.name})")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")

    if not _pravit(koren / "Биржа" / "stol.py",
                   [(S_YAKOR, S_NOV), (S_YAKOR2, S_NOV2)], "stol.py"):
        return 1
    if not _pravit(koren / "Биржа" / "otchyot.py",
                   [(O_YAKOR, O_NOV)], "otchyot.py"):
        print("\n⚠️  стол поправлен, отчёт нет — верни stol.py из свежей")
        print("   .bak_volnastol_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nТеперь на столе, когда волна кончилась:")
    print("  — ТОЧКА НОЛЬ: BULL @ 1.14968   16 бар(ов) назад ...")
    print("  — ВОЛНА 1: от 1.14968 → макушка 1.15959   16 бар(ов) от точки")
    print("\nИ отчёт подпишет каждый шаг наблюдения СВОИМ баром, а дату")
    print("места положит отдельной колонкой.")
    print("\nПроверить стол без модели: py stol_pokazat.py EURUSD H4")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
