# -*- coding: utf-8 -*-
"""
postavit_konec_volny_2.py · MARKER: KONEC_VOLNY_2_V1

ЗАЧЕМ
─────
У точки ноль есть хозяин — тот, кто ловит первый разворот. У конца
первой волны есть хозяин — тот, кто бьёт от макушки. А у того, кто
работает ОТКАТ, момента не было. Он это и говорил, дословно, на баре
события:

    «Волна 1, кажется, закончилась, но мне нужен откат к ней,
     чтобы войти по своей стратегии.»

Волна была на столе. Отката — нет.

КАНОН, §4.1
───────────
    Волна 2 сама — тоже маленький зигзаг (фрактальность), и Вася её
    конец ловит той же механикой РБ, только этажом мельче и без
    требования яркой ангуляции (движение молодое, пасть ещё не
    разошлась широко).

Тот же прибор, третий раз подряд. Ни одного нового расчёта.

И §6 закрывает три соблазна заранее: модуль 6.3 для этой роли выброшен,
фрактал — свойство разворотника, а не признак, дивергенция как
ОБЯЗАТЕЛЬНОЕ условие отвергнута. Искать особый сигнал отката не надо.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Разворотник В СТОРОНУ ТОЧКИ, пришедший ПОСЛЕ отмеченной макушки, —
   это конец волны 2, а не подпитка точки. Различает их одно: была
   макушка или нет. Ни порогов, ни чисел.

   (До макушки всё как было: такой бар углубляет саму точку, это
   правило TOCHKA_ZHIVA_V1, и оно верное — волна ещё не пошла.)

2. Конец волны 2 ложится на стол координатой, рядом с точкой и волной:

       ОТКАТ: кончился @ 1.15410   5 бар(ов) от макушки

   Пока идёт — «ОТКАТ: идёт». Ни одного суждения о том, годится вход
   или нет: это слово трейдера.

3. Ключ получает ТРЕТЬЮ причину открыть дверь. Теперь их три, и у
   каждой свой хозяин:

       точка родилась     → первый разворот
       волна 1 кончилась  → макушка
       волна 2 кончилась  → откат          ← новое

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ конца волны 1 и волны на столе — патч это проверит.
Запуск: py postavit_konec_volny_2.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KONEC_VOLNY_2_V1"
NUZHEN_H = "KONEC_VOLNY_1_V1"
NUZHEN_S = "VOLNA_NA_STOLE_V1"
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


# ── hooks: ловим конец волны 2 ───────────────────────────────
# Встаём ПЕРЕД блоком конца волны 1: тот смотрит обратную сторону,
# этот — свою, и они не пересекаются.

H_YAKOR = '''        # KONEC_VOLNY_1_V1: разворотник в ОБРАТНУЮ сторону внутри живой'''

H_NOV = '''        # KONEC_VOLNY_2_V1: разворотник В СТОРОНУ точки, пришедший
        # ПОСЛЕ отмеченной макушки, — это конец отката, а не подпитка.
        # КАНОН §4.1: волна 2 сама маленький зигзаг, и её конец ловится
        # той же механикой РБ, только этажом мельче и без требования
        # яркой ангуляции. Различает подпитку и откат одно: была
        # макушка или нет. Ни порогов, ни новых чисел.
        # До макушки всё по-старому — такой бар углубляет точку
        # (TOCHKA_ZHIVA_V1), и это верно: волна ещё не пошла.
        if (zhiva and napr in ("BULL", "BEAR") and storona == napr
                and cena is not None and isk.get("konec_volny_1")
                and not isk.get("konec_volny_2")):
            _kv1 = isk.get("konec_volny_1") or {}
            _ot_makushki = (int(isk.get("barov_s_tochki") or 0)
                            - int(_kv1.get("баров_от_точки") or 0))
            isk["konec_volny_2"] = {
                "цена": cena, "бар": bar,
                "баров_от_макушки": max(0, _ot_makushki),
            }
            save_trading_state(t)
            print(f"[ОТКАТ] ↩ {para}: кончился @ {cena} · бар {bar} "
                  f"· {max(0, _ot_makushki)} бар(ов) от макушки")
            return _zapomnit_otvet({"alive": True, "konec_volny_2": True,
                                    "direction": storona})

        # KONEC_VOLNY_1_V1: разворотник в ОБРАТНУЮ сторону внутри живой'''

# новая точка — новая жизнь: чистим и вторую отметку
H_YAKOR2 = '''                isk["konec_volny_1"] = None'''
H_NOV2 = '''                isk["konec_volny_1"] = None
                isk["konec_volny_2"] = None   # KONEC_VOLNY_2_V1'''


# ── стол: откат координатой ──────────────────────────────────

S_YAKOR = '''        } if _k else {"кончилась": False}))(isk.get("konec_volny_1") or {}),'''

S_NOV = '''        } if _k else {"кончилась": False}))(isk.get("konec_volny_1") or {}),
        # KONEC_VOLNY_2_V1: откат — третья координата, рядом с точкой и
        # волной. Трейдер говорил «волна кончилась, но мне нужен откат
        # к ней» — вот он, тем же прибором.
        "волна_2": (lambda _k: ({
            "кончилась": True,
            "цена": _k.get("цена"),
            "бар": _k.get("бар"),
            "баров_от_макушки": _k.get("баров_от_макушки"),
        } if _k else {"кончилась": False}))(isk.get("konec_volny_2") or {}),'''

S_YAKOR2 = '''            if _v.get("кончилась") else "ВОЛНА 1: ещё идёт"))(
                (p.get("точка_ноль") or {}).get("волна_1") or {},
                p.get("точка_ноль") or {}),'''

S_NOV2 = '''            if _v.get("кончилась") else "ВОЛНА 1: ещё идёт"))(
                (p.get("точка_ноль") or {}).get("волна_1") or {},
                p.get("точка_ноль") or {}),
        # KONEC_VOLNY_2_V1: и откат к ней — если он уже кончился.
        (lambda _o: (
            f"ОТКАТ: кончился @ {_o.get('цена')}"
            f"   {_o.get('баров_от_макушки')} бар(ов) от макушки"
            f"   бар {_o.get('бар')}"
            if _o.get("кончилась") else "ОТКАТ: идёт"))(
                (p.get("точка_ноль") or {}).get("волна_2") or {}),'''


# ── council: третья причина ──────────────────────────────────

C_YAKOR = '''        # «Наблюдаю» само по себе дверь НЕ открывает: пока трейдер'''

C_NOV = '''        # KONEC_VOLNY_2_V1: третье событие — откат к первой волне
        # кончился. Момент того, кто работает третье место.
        kv2 = tch.get("konec_volny_2") or {}
        if kv2 and str(kv2.get("бар") or "") == bar_goroda and bar_goroda:
            return {"будим": True,
                    "почему": f"откат кончился @ {kv2.get('цена')} "
                              f"({kv2.get('баров_от_макушки')} бар. "
                              f"от макушки)"}

        # «Наблюдаю» само по себе дверь НЕ открывает: пока трейдер'''


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
    bak = f.with_suffix(f".py.bak_volna2_{datetime.now():%Y%m%d_%H%M%S}")
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
    s = koren / "Биржа" / "stol.py"
    if NUZHEN_H not in h.read_text(encoding="utf-8"):
        print("✗ Сперва накати postavit_konec_pervoy_volny.py")
        return 1
    if NUZHEN_S not in s.read_text(encoding="utf-8"):
        print("✗ Сперва накати postavit_volnu_na_stol.py")
        return 1

    if not _pravit(h, [(H_YAKOR, H_NOV), (H_YAKOR2, H_NOV2)], "hooks.py"):
        return 1
    if not _pravit(s, [(S_YAKOR, S_NOV), (S_YAKOR2, S_NOV2)], "stol.py"):
        print("\n⚠️  hooks поправлен, стол нет — верни hooks.py из свежей")
        print("   .bak_volna2_* и покажи мне вывод.")
        return 1
    if not _pravit(koren / "Биржа" / "council.py",
                   [(C_YAKOR, C_NOV)], "council.py"):
        print("\n⚠️  hooks и стол поправлены, council нет — верни их из")
        print("   свежих .bak_volna2_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nТеперь у трейдера на столе вся структура:")
    print("  — ТОЧКА НОЛЬ: BULL @ 1.14968   16 бар(ов) назад")
    print("  — ВОЛНА 1: от 1.14968 → макушка 1.15959   16 бар. от точки")
    print("  — ОТКАТ: кончился @ 1.15410   5 бар(ов) от макушки")
    print("\nИ три события вместо побарного опроса, у каждого свой хозяин:")
    print("  точка родилась → первый разворот")
    print("  волна 1 кончилась → макушка")
    print("  волна 2 кончилась → ОТКАТ")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
