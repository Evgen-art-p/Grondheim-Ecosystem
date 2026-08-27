# -*- coding: utf-8 -*-
"""
pochinit_kray_volny.py · MARKER: KRAY_VOLNY_V1

ДВЕ МОИ НЕДОДЕЛКИ, ОБЕ ПРО ЯЗЫК
───────────────────────────────
Прогон 21.08 прошёл всю цепочку впервые — точка, волна, переезд, откат.
И там же вылезло два места, где город говорит неточно, а трейдер честно
спотыкается.

**1. «Макушка» врёт на медвежьей структуре.**

Точка BEAR — это движение ВНИЗ, и край первой волны там ДНО, а не
макушка. Нина читала «макушка» при падающей цене и путалась:

    «Разворотный бар на покупку и точка ноль на продажу,
     но это не мой вход»

Называем по стороне: BULL — вершина, BEAR — дно. Это не мнение, это
направление, которое мы у себя же на столе переврали.

**2. Переезд края назван концом.**

Когда край сдвинулся дальше (NOVAYA_MAKUSHKA_V1), ключ говорил то же
самое, что и при первом конце: «волна 1 кончилась». Нина на это
ответила «ещё не сформировалась волна 1» — и была права, потому что
волна как раз продолжалась.

Теперь: первый раз — «волна 1 кончилась», дальше — «край волны 1
сдвинулся». Разные события — разные слова.

ЧТО НЕ МЕНЯЕТСЯ
───────────────
Ни одного расчёта. Ни одного числа. Только имена того, что уже
считается, и подпись события в ключе.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ новой макушки — патч это проверит.
Запуск: py pochinit_kray_volny.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KRAY_VOLNY_V1"
NUZHEN = "NOVAYA_MAKUSHKA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "stol.py").exists()
            and (p / "Биржа" / "council.py").exists())


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


# ── hooks: переезд говорит про КРАЙ, а не про конец ──────────

H_YAKOR = '''                print(f"[ВОЛНА 1] ⛰ {para}: макушка переехала "
                      f"{_bylo} → {cena} · бар {bar}")
                return _zapomnit_otvet({"alive": True, "konec_volny_1": True,
                                        "makushka_pereehala": True,
                                        "direction": storona})'''

H_NOV = '''                # KRAY_VOLNY_V1: край, а не «макушка» — на медвежьей
                # структуре это дно. И переезд ≠ конец: волна как раз
                # продолжается, трейдер на «кончилась» честно спорил.
                _slovo = "вершина" if storona == "BULL" else "дно"
                _okonchanie = "ась" if storona == "BULL" else "ось"
                print(f"[ВОЛНА 1] ⛰ {para}: {_slovo} сдвинул{_okonchanie} "
                      f"{_bylo} → {cena} · бар {bar}")
                return _zapomnit_otvet({"alive": True, "konec_volny_1": True,
                                        "kray_sdvinulsya": True,
                                        "direction": storona})'''

H_YAKOR2 = '''            print(f"[ОТКАТ] ↩ {para}: кончился @ {cena} · бар {bar} "
                  f"· {max(0, _ot_makushki)} бар(ов) от макушки")'''

H_NOV2 = '''            _slovo = "вершины" if storona == "BULL" else "дна"
            print(f"[ОТКАТ] ↩ {para}: кончился @ {cena} · бар {bar} "
                  f"· {max(0, _ot_makushki)} бар(ов) от {_slovo}")'''


# ── council: разные события — разные слова ───────────────────

C_YAKOR = '''        kv = tch.get("konec_volny_1") or {}
        if kv and str(kv.get("бар") or "") == bar_goroda and bar_goroda:
            return {"будим": True,
                    "почему": f"волна 1 кончилась @ {kv.get('цена')} "
                              f"({kv.get('баров_от_точки')} бар. от точки)"}'''

C_NOV = '''        kv = tch.get("konec_volny_1") or {}
        if kv and str(kv.get("бар") or "") == bar_goroda and bar_goroda:
            # KRAY_VOLNY_V1: первый раз — кончилась; дальше край просто
            # сдвинулся, и волна продолжается. Разные события — разные
            # слова, иначе трейдер спорит с ключом и он прав.
            _st = tch.get("trend_direction")
            _kray = "вершина" if _st == "BULL" else "дно"
            _ok = "лась" if _st == "BULL" else "лось"
            if kv.get("сдвинулась"):
                return {"будим": True,
                        "почему": f"{_kray} волны 1 сдвину{_ok} → "
                                  f"{kv.get('цена')} "
                                  f"({kv.get('баров_от_точки')} бар. "
                                  f"от точки)"}
            return {"будим": True,
                    "почему": f"волна 1 кончилась, {_kray} @ "
                              f"{kv.get('цена')} "
                              f"({kv.get('баров_от_точки')} бар. от точки)"}'''

C_YAKOR2 = '''                    "почему": f"откат кончился @ {kv2.get('цена')} "
                              f"({kv2.get('баров_от_макушки')} бар. "
                              f"от макушки)"}'''

C_NOV2 = '''                    "почему": f"откат кончился @ {kv2.get('цена')} "
                              f"({kv2.get('баров_от_макушки')} бар. от "
                              f"{'вершины' if tch.get('trend_direction') == 'BULL' else 'дна'})"}'''


# ── hooks: помечаем переезд в самой отметке ──────────────────

H_YAKOR3 = '''                isk["konec_volny_1"] = {
                    "цена": cena, "бар": bar, "сторона": napr,
                    "структура": wf.get("dlina") or 0,
                    "баров_от_точки": int(isk.get("barov_s_tochki") or 0),
                }
                isk["kray_posle"] = cena'''

H_NOV3 = '''                isk["konec_volny_1"] = {
                    "цена": cena, "бар": bar, "сторона": napr,
                    "структура": wf.get("dlina") or 0,
                    "баров_от_точки": int(isk.get("barov_s_tochki") or 0),
                    "сдвинулась": True,   # KRAY_VOLNY_V1: не первый раз
                }
                isk["kray_posle"] = cena'''


# ── стол: край по стороне ────────────────────────────────────

S_YAKOR = '''            f"ВОЛНА 1: от {_t.get('цена')} → макушка {_v.get('макушка')}"'''

S_NOV = '''            f"ВОЛНА 1: от {_t.get('цена')} → "
            f"{'вершина' if _t.get('сторона') == 'BULL' else 'дно'} "
            f"{_v.get('макушка')}"'''

S_YAKOR2 = '''            f"   {_o.get('баров_от_макушки')} бар(ов) от макушки"'''

S_NOV2 = '''            f"   {_o.get('баров_от_макушки')} бар(ов) от "
            f"{'вершины' if _t.get('сторона') == 'BULL' else 'дна'}"'''

S_YAKOR3 = '''            if _o.get("кончилась") else "ОТКАТ: идёт"))(
                (p.get("точка_ноль") or {}).get("волна_2") or {}),'''

S_NOV3 = '''            if _o.get("кончилась") else "ОТКАТ: идёт"))(
                (p.get("точка_ноль") or {}).get("волна_2") or {},
                p.get("точка_ноль") or {}),'''

S_YAKOR4 = '''        (lambda _o: (
            f"ОТКАТ: кончился @ {_o.get('цена')}"'''

S_NOV4 = '''        (lambda _o, _t: (
            f"ОТКАТ: кончился @ {_o.get('цена')}"'''


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
    bak = f.with_suffix(f".py.bak_kray_{datetime.now():%Y%m%d_%H%M%S}")
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
    h = koren / "Биржа" / "hooks.py"
    if NUZHEN not in h.read_text(encoding="utf-8"):
        print("✗ Сперва накати postavit_novuyu_makushku.py")
        return 1

    if not _pravit(h, [(H_YAKOR3, H_NOV3), (H_YAKOR, H_NOV),
                       (H_YAKOR2, H_NOV2)], "hooks.py"):
        return 1
    if not _pravit(koren / "Биржа" / "council.py",
                   [(C_YAKOR, C_NOV), (C_YAKOR2, C_NOV2)], "council.py"):
        print("\n⚠️  hooks поправлен, council нет — верни его из свежей")
        print("   .bak_kray_* и покажи мне вывод.")
        return 1
    if not _pravit(koren / "Биржа" / "stol.py",
                   [(S_YAKOR4, S_NOV4), (S_YAKOR3, S_NOV3),
                    (S_YAKOR, S_NOV), (S_YAKOR2, S_NOV2)], "stol.py"):
        print("\n⚠️  hooks и council поправлены, стол нет — верни их из")
        print("   свежих .bak_kray_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nТеперь на медвежьей структуре:")
    print("  — ВОЛНА 1: от 1.17549 → дно 1.16598   13 бар(ов) от точки")
    print("  — ОТКАТ: кончился @ 1.17416   4 бар(ов) от дна")
    print("\nИ в ключе разные события — разными словами:")
    print("  волна 1 кончилась, дно @ 1.16773 (5 бар. от точки)")
    print("  дно волны 1 сдвинулось → 1.16598 (13 бар. от точки)")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
