# -*- coding: utf-8 -*-
"""
postavit_konec_pervoy_volny.py · MARKER: KONEC_VOLNY_1_V1

СЛОВО ШЕФА (20.08)
──────────────────
«Это ошибка большинства трейдеров — мониторить по барам. Смотри: мы
увидели точку, значит должна появиться первая от точки волна, а волна —
это пятиволновка, а как заканчивается пятая, мы знаем. Итого: после
точки ноль ловим конец пятой волны от этой точки.»

И на вопрос про этаж: «Кто сказал, что именно на этаж, а не полтора?
Не этажи задают волну, а волна задаёт этажи.»

ЧТО БЫЛО НЕПРАВИЛЬНО
────────────────────
Час назад я сделал наблюдение вторым ключом: сказала «наблюдаю» — будим
на каждом баре. Это и есть побарный мониторинг: дорого (каждый бар —
оплаченный взгляд) и неверно по сути. Трейдер не пялится в каждую свечу,
он ждёт СОБЫТИЕ.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
После точки ноль город ищет одно событие — КОНЕЦ ПЕРВОЙ ВОЛНЫ. И ищет
его тем же прибором, которым поймал саму точку, потому что по
фрактальности волна 1 — сама пятиволновка:

    разворотный бар в ОБРАТНУЮ сторону от точки
    + структура позади укладывается ПОСЛЕ точки ноль

Второе условие — чистое сравнение двух чисел, которые уже считаются:
сколько баров живёт точка и сколько баров у структуры позади. Уложилась
в прожитое — значит волна отмерена от точки, а не от чего-то прошлого.
Ни допусков, ни порогов, ни рамок по длине: волна задаёт этажи, а не
наоборот.

Следствие: разворотник в обратную сторону внутри живой точки больше НЕ
рождает новую точку. Раньше он её перезаписывал. Теперь, если его
структура укладывается после точки, — это конец волны 1, макушка
первого движения, а не новое начало.

Ключ пробуждения перестраивается:

    точка родилась          → зовём (как было)
    конец первой волны      → зовём ← новое, ради этого всё
    своя позиция или заявка → зовём (как было)
    просто «наблюдаю»       → НЕ зовём: город считает молча и бесплатно

Наблюдение никуда не девается — оно остаётся её словом «слежу», и по
нему прогон идёт вперёд. Но само по себе оно больше не открывает дверь
на каждом баре.

Прогон вперёд теперь шагает МОЛЧА: на каждом шаге зовёт руку рынка
(это код, не модель), ведёт точку и смотрит ключ. Ключ закрыт — шагаем
дальше бесплатно. Открылся — будим трейдера, и он говорит: ждёт или
входит.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ наблюдения и прогона вперёд — патч это проверит.
Запуск: py postavit_konec_pervoy_volny.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KONEC_VOLNY_1_V1"
NUZHEN_C = "NABLYUDENIE_V1"
NUZHEN_U = "PROGON_VPERYOD_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "council.py").exists()
            and (p / "Биржа" / "ui_torg.py").exists())


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


# ══ hooks.py: ловим конец первой волны ═══════════════════════

H_YAKOR = '''        if napr in ("BULL", "BEAR") and cena is not None                 and wf.get("struktura_chitaetsya"):
            if (not zhiva) or storona != napr:'''

H_NOV = '''        # KONEC_VOLNY_1_V1: разворотник в ОБРАТНУЮ сторону внутри живой
        # точки — это не новое начало, а конец первой волны от неё,
        # если структура позади укладывается ПОСЛЕ точки. По
        # фрактальности волна 1 — сама пятиволновка, и конец её пятой
        # ловится тем же прибором, что и сама точка.
        # Сравниваем два числа, которые уже считаются: сколько баров
        # живёт точка и сколько баров у структуры. Ни допусков, ни
        # рамок по длине: волна задаёт этажи, а не этажи волну.
        if (zhiva and napr in ("BULL", "BEAR") and storona != napr
                and cena is not None and wf.get("struktura_chitaetsya")
                and not isk.get("konec_volny_1")):
            _dlina = wf.get("dlina") or 0
            _prozhito = int(isk.get("barov_s_tochki") or 0)
            if _dlina and _dlina <= _prozhito:
                isk["konec_volny_1"] = {
                    "цена": cena, "бар": bar, "сторона": napr,
                    "структура": _dlina,
                    "баров_от_точки": _prozhito,
                }
                save_trading_state(t)
                print(f"[ВОЛНА 1] ⛰ {para}: кончилась @ {cena} · бар {bar} "
                      f"· {_prozhito} бар(ов) от точки "
                      f"(структура {_dlina})")
                return {"alive": True, "konec_volny_1": True,
                        "direction": storona}

        if napr in ("BULL", "BEAR") and cena is not None                 and wf.get("struktura_chitaetsya"):
            if (not zhiva) or storona != napr:'''

# рождение обратной стороны больше не перебивает живую точку вслепую
H_YAKOR2 = '''            if (not zhiva) or storona != napr:
                isk["alive"] = True'''

H_NOV2 = '''            if (not zhiva) or storona != napr:
                # KONEC_VOLNY_1_V1: сюда обратный разворотник попадает
                # только если конец волны 1 уже был отмечен или его
                # структура НЕ уложилась после точки — тогда это правда
                # новое начало, а не макушка первой волны.
                isk["alive"] = True'''


# ══ council.py: ключ ═════════════════════════════════════════

C_YAKOR = '''        # NABLYUDENIE_V1: второй ключ — трейдер сам взял на карандаш.
        # Снимает только он: словом УХОЖУ или входом.
        if slot:
            n = hooks.nablyudenie(symbol, timeframe, slot)
            if n:
                za = (n.get("за_чем") or "").strip()
                return {"будим": True,
                        "почему": "наблюдает" + (f": {za[:80]}" if za else "")}

        return {"будим": False, "почему": "точки нет, наблюдения нет, "
                                          "позиции нет"}'''

C_NOV = '''        # KONEC_VOLNY_1_V1: второе СОБЫТИЕ, ради которого всё. Волна 1
        # от точки кончилась — значит есть от чего ждать откат. Слово
        # Шефа: побарный мониторинг — ошибка большинства трейдеров;
        # трейдер ждёт событие, а не пялится в каждую свечу.
        kv = tch.get("konec_volny_1") or {}
        if kv and str(kv.get("бар") or "") == bar_goroda and bar_goroda:
            return {"будим": True,
                    "почему": f"волна 1 кончилась @ {kv.get('цена')} "
                              f"({kv.get('баров_от_точки')} бар. от точки)"}

        # «Наблюдаю» само по себе дверь НЕ открывает: пока трейдер
        # следит, город считает молча и бесплатно.
        return {"будим": False, "почему": "точки нет, события нет, "
                                          "позиции нет"}'''

C_YAKOR2 = '''        tch = hooks._blok_tochki(t, hooks._para_tochki(symbol, timeframe))
        bar_goroda = str(((t.get("рынок") or {}).get("бар")) or "")'''
C_NOV2 = '''        tch = hooks._blok_tochki(t, hooks._para_tochki(symbol, timeframe))
        bar_goroda = str(((t.get("рынок") or {}).get("бар")) or "")
        _ = slot   # KONEC_VOLNY_1_V1: наблюдение больше не ключ'''


# ══ ui_torg.py: прогон шагает молча ══════════════════════════

U_YAKOR = '''                    state["chat_history"].append({
                        "role": "system",
                        "content": f"👁 {_stalo} · наблюдает {imya}"})
                    update_chat_display()
                    _kadr = None'''

U_NOV = '''                    # KONEC_VOLNY_1_V1: шагаем МОЛЧА. Рука рынка — код,
                    # не модель: ведёт точку и ищет конец первой волны
                    # бесплатно. Ключ закрыт — идём дальше даром.
                    try:
                        import hooks as _hh
                        _hh.rynok_novyy_bar(_sym, _tf)
                        _kk = __import__("council")._klyuch_probuzhdeniya(
                            _sym, _tf, _sl)
                    except Exception as _ekl:
                        print(f"[ПРОГОН] ключ не прочёлся: {_ekl}")
                        _kk = {"будим": True, "почему": "ключ не прочёлся"}
                    if not _kk.get("будим"):
                        continue
                    state["chat_history"].append({
                        "role": "system",
                        "content": f"👁 {_stalo} · {_kk.get('почему')} "
                                   f"→ спрашиваю {imya}"})
                    update_chat_display()
                    _kadr = None'''


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
    bak = f.with_suffix(f".py.bak_volna1_{datetime.now():%Y%m%d_%H%M%S}")
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

    c = koren / "Биржа" / "council.py"
    u = koren / "Биржа" / "ui_torg.py"
    if NUZHEN_C not in c.read_text(encoding="utf-8"):
        print("✗ Сперва накати postavit_nablyudenie.py")
        return 1
    if NUZHEN_U not in u.read_text(encoding="utf-8"):
        print("✗ Сперва накати postavit_progon_vperyod.py")
        return 1

    if not _pravit(koren / "Биржа" / "hooks.py",
                   [(H_YAKOR2, H_NOV2), (H_YAKOR, H_NOV)], "hooks.py"):
        return 1
    if not _pravit(c, [(C_YAKOR2, C_NOV2), (C_YAKOR, C_NOV)], "council.py"):
        print("\n⚠️  hooks.py поправлен, council.py нет — верни его из")
        print("   свежей .bak_volna1_* и покажи мне вывод.")
        return 1
    if not _pravit(u, [(U_YAKOR, U_NOV)], "ui_torg.py"):
        print("\n⚠️  hooks и council поправлены, ui_torg нет — верни их из")
        print("   свежих .bak_volna1_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nЧто теперь в логе:")
    print("  [ТОЧКА]  ✦ родилась BULL @ 1.1034      → 🔑 спрашиваю")
    print("  (город шагает молча и бесплатно)")
    print("  [ВОЛНА 1] ⛰ кончилась @ 1.1189 · 23 бар(а) от точки")
    print("  [КЛЮЧ]   🔑 волна 1 кончилась @ 1.1189 → 🔑 спрашиваю снова")
    print("\nВторой раз трейдера зовут не «на всякий случай», а на")
    print("событии: волна 1 состоялась, вот её макушка — ждёшь или входишь.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
