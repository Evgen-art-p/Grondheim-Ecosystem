# -*- coding: utf-8 -*-
"""
peredelat_dosku_v_lichnuyu.py · MARKER: KARTINA_SVOYA_V1

СЛОВА ШЕФА, КОТОРЫЕ ЭТО ИСПРАВЛЯЮТ
──────────────────────────────────
    «Каждый должен. Нет первого и последнего, а уже индивидуум
    принимает решение с выбором, что он работает. То есть место не
    вход. Место — это СТОЛ, один на всех со всеми фактами. Есть бар,
    посмотрели: Вася решил, что это волна одна, Петя — другая, один
    одно ждёт, другой другое, а может, кто все три входа делать
    будет. Наша задача — ДАТЬ.»

ЧТО БЫЛО НЕВЕРНО В МОЕЙ ДОСКЕ
─────────────────────────────
Я сделал доску ОДНУ НА ИНСТРУМЕНТ. Из этого само собой выросло то,
чего быть не должно:

    · объявление одного становилось обязательным для всех;
    · выстраивалась очередь — сперва тот, кто ставит точку ноль,
      потом остальные;
    · «первую волну нельзя объявить без точки ноль» — то есть один
      трейдер блокировал другого.

Это опять система вместо свободы. На одном и том же баре Вася видит
одну волну, Петя другую, и оба правы: это ИХ чтение, а не свойство
рынка.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Картина становится ЛИЧНОЙ — своя у каждого, при нём, а не при
инструменте:

    …/слоты/{слот}/данные/картина.json

Тот же смысл — точка ноль, волна, откат, — но это его чтение. Никто
ни на кого не опирается и никого не ждёт. Хочет вести все три входа
сразу — ведёт. Видит структуру иначе соседа — и хорошо.

Порядок «сперва точка ноль» остаётся ВНУТРИ его картины: нельзя
объявить свою первую волну, не назвав СВОЮ точку ноль. Это не запрет
от чужого, а связность собственного чтения.

ПОДСМОТРА У СОСЕДЕЙ НЕТ — намеренно, слово Шефа: «пока не делай, они
в своих не понять пока что». Пока каждый не разобрался в своём,
подсматривание сведёт троих в одно мнение.

ЗАЧЕМ ЭТО ВООБЩЕ
────────────────
Чтобы его чтение не терялось между барами. Без памяти он каждый раз
начинает с чистого листа — из-за этого Нина десять раз подряд писала
«нет первой волны и отката к ней»: волна была, но для неё
предыдущего бара не существовало.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py peredelat_dosku_v_lichnuyu.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KARTINA_SVOYA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    # Приметы только ПОСТОЯННЫЕ. Раньше здесь стоял doska.py — а патч
    # сам её и откладывает, и со второго запуска город переставал
    # опознаваться. Та же ошибка, что была с masshtab.py: примета не
    # должна быть тем, что патч создаёт или убирает.
    return ((p / "Биржа" / "ruki_treydera.py").exists()
            and (p / "Биржа" / "hooks.py").exists()
            and (p / "main.py").exists())


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


KARTINA_PY = '''# -*- coding: utf-8 -*-
# KARTINA_SVOYA_V1
"""
КАРТИНА — как ЭТОТ трейдер читает рынок. Своя у каждого.

СЛОВА ШЕФА
    «Нет первого и последнего... Место — это СТОЛ, один на всех со
    всеми фактами. Есть бар, посмотрели: Вася решил, что это волна
    одна, Петя — другая, один одно ждёт, другой другое, а может, кто
    все три входа делать будет. Наша задача — дать.»

ЗАКОН ЭТОГО ФАЙЛА
    Стол общий, чтение личное. На одном и том же баре двое видят
    разное, и оба правы: волны — это интерпретация, а не свойство
    рынка. Поэтому картина живёт ПРИ ТРЕЙДЕРЕ, а не при инструменте, и
    ничьё объявление не обязывает соседа.

    Чужие картины не показываются намеренно (слово Шефа 16.08): пока
    каждый не разобрался в своём чтении, подсматривание сведёт всех в
    одно мнение.

ЗАЧЕМ
    Чтобы чтение не терялось между барами. Без памяти трейдер каждый
    раз начинает с чистого листа и честно пишет «нет первой волны» —
    хотя волна была, просто предыдущего бара для него не существовало.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_KOREN = Path(__file__).resolve().parent.parent
PUSTO = {"точка_ноль": None, "волна": None, "откат": None, "заметки": []}


def _put(ceh: str, slot: str) -> Path:
    return (_KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh / "слоты"
            / slot / "данные" / "картина.json")


def _vsya(ceh: str, slot: str) -> dict:
    try:
        return json.loads(_put(ceh, slot).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sohranit(ceh: str, slot: str, d: dict):
    p = _put(ceh, slot)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    except Exception as e:
        print(f"[КАРТИНА] не записалась: {e}")


def chitat(ceh: str, slot: str, symbol: str) -> dict:
    s = (symbol or "").strip().upper()
    d = json.loads(json.dumps(PUSTO))
    d.update((_vsya(ceh, slot).get(s) or {}))
    return d


def obyavit(ceh: str, slot: str, symbol: str, chto: str, kto: str = "",
            cena=None, bar: str = "", pochemu: str = "") -> tuple:
    """Записать в СВОЮ картину. Ничего ни у кого не спрашиваем."""
    s = (symbol or "").strip().upper()
    if not s:
        return False, "не сказано, по какому инструменту"
    chto = (chto or "").strip().lower()
    vsya = _vsya(ceh, slot)
    moya = vsya.get(s) or json.loads(json.dumps(PUSTO))
    seychas = datetime.now().isoformat(timespec="seconds")
    zapis = {"кто": kto or slot, "почему": (pochemu or "").strip()[:500],
             "когда": seychas}
    if cena is not None:
        try:
            zapis["цена"] = float(cena)
        except Exception:
            return False, f"цена не число: {cena}"
    if bar:
        zapis["бар"] = bar

    if chto in ("точка_ноль", "точка ноль", "ноль"):
        # новая точка ноль — значит и волна, и откат другие
        moya = json.loads(json.dumps(PUSTO))
        moya["точка_ноль"] = zapis
        itog = f"твоя точка ноль {s}: {zapis.get('цена')} ({bar})"
    elif chto in ("волна", "первая_волна", "первая волна"):
        if not moya.get("точка_ноль"):
            return False, ("в твоей картине нет точки ноль — от чего "
                           "волна? назови сперва её")
        moya["волна"] = zapis
        itog = f"твоя волна {s} до {zapis.get('цена')}"
    elif chto in ("откат",):
        if not moya.get("волна"):
            return False, "в твоей картине нет волны — откатывать нечему"
        moya["откат"] = zapis
        itog = f"ты видишь откат к своей волне {s}"
    elif chto in ("заметка", "мысль"):
        moya.setdefault("заметки", []).append(zapis)
        moya["заметки"] = moya["заметки"][-10:]
        itog = "записал в твою картину"
    elif chto in ("стереть", "сломалась", "чисто"):
        moya = json.loads(json.dumps(PUSTO))
        itog = f"твоя картина {s} чистая"
    else:
        return False, (f"не понял «{chto}». Можно: точка_ноль, волна, "
                       f"откат, заметка, стереть")

    vsya[s] = moya
    _sohranit(ceh, slot, vsya)
    return True, itog


def slovami(ceh: str, slot: str, symbol: str) -> str:
    """Своя картина словами. Только то, что он сам записал."""
    d = chitat(ceh, slot, symbol)
    tn = d.get("точка_ноль")
    L = [f"=== ТВОЯ КАРТИНА · {(symbol or '').upper()} ==="]
    if not tn:
        L.append("Пусто. Ты ещё не называл(а) свою точку ноль —")
        L.append("посмотри и назови, если видишь конец коррекции.")
    else:
        L.append(f"ТОЧКА НОЛЬ: {tn.get('цена')} на баре {tn.get('бар')}")
        if tn.get("почему"):
            L.append(f"   ты сказал(а): {tn['почему']}")
        v = d.get("волна")
        L.append(f"ВОЛНА: до {v.get('цена')}" if v else "ВОЛНА: не названа")
        if v and v.get("почему"):
            L.append(f"   ты сказал(а): {v['почему']}")
        o = d.get("откат")
        L.append("ОТКАТ: видишь" if o else "ОТКАТ: не назван")
        if o and o.get("почему"):
            L.append(f"   ты сказал(а): {o['почему']}")
    zam = d.get("заметки") or []
    if zam:
        L.append("ТВОИ ЗАМЕТКИ:")
        for z in zam[-3:]:
            L.append(f"   · {z.get('почему', '')} ({z.get('когда', '')[:16]})")
    return "\\n".join(L)


# KARTINA_SVOYA_V1 - marker
'''


ST_SHEMA = '''        {"type": "function", "function": {
            "name": "posmotret_dosku",
            "description": (
                "Что уже объявлено по этому инструменту: точка ноль (конец "
                "коррекции), пошла ли от неё первая волна, начался ли откат "
                "к ней. Общая память стола — смотри ПЕРВЫМ делом, чтобы "
                "знать, от чего плясать."),
            "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {
            "name": "obyavit_na_dosku",
            "description": (
                "Объявить то, что ТЫ УВИДЕЛ(А) на растянутой картинке. "
                "«точка_ноль» — коррекция кончилась, отсюда пойдёт первая "
                "волна. «первая_волна» — от точки ноль движение пошло и "
                "дошло досюда. «откат» — к первой волне пошёл откат. "
                "«стереть» — структура сломалась. Объявляй только то, что "
                "видишь сам: на твоём слове будут стоять остальные."),
            "parameters": {"type": "object", "properties": {
                "что": {"type": "string",
                        "description": "точка_ноль | первая_волна | откат | стереть"},
                "цена": {"type": "number",
                         "description": "для точки ноль и первой волны"},
                "бар": {"type": "string",
                        "description": "дата бара, вид 2025.05.05 20:00"},
                "почему": {"type": "string",
                           "description": "что именно ты увидел(а) — своими словами"}},
                "required": ["что"]}}},'''

NOV_SHEMA = '''        # KARTINA_SVOYA_V1: твоё чтение, не общее. Стол один на всех,
        # факты одинаковые — а волны у каждого свои. Чужих картин ты
        # не видишь: пока каждый не разобрался в своём, подсматривание
        # свело бы всех в одно мнение.
        {"type": "function", "function": {
            "name": "moya_kartina",
            "description": (
                "ТВОЁ чтение этого рынка, как ты его оставил(а) в прошлый "
                "раз: где ТВОЯ точка ноль, пошла ли от неё волна, видишь ли "
                "откат. Смотри ПЕРВЫМ делом — иначе начнёшь с чистого листа "
                "и не увидишь того, что уже разглядел(а) раньше."),
            "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {
            "name": "zapisat_v_kartinu",
            "description": (
                "Записать в СВОЮ картину то, что ты увидел(а). "
                "«точка_ноль» — здесь, по-твоему, кончилась коррекция. "
                "«волна» — от неё пошло движение и дошло досюда. "
                "«откат» — к своей волне видишь откат. "
                "«заметка» — мысль на память. «стереть» — твоя структура "
                "сломалась. Это ТВОЁ чтение: сосед может видеть иначе, и "
                "это нормально."),
            "parameters": {"type": "object", "properties": {
                "что": {"type": "string",
                        "description": "точка_ноль | волна | откат | заметка | стереть"},
                "цена": {"type": "number", "description": "если есть"},
                "бар": {"type": "string",
                        "description": "дата бара, вид 2025.05.05 20:00"},
                "почему": {"type": "string",
                           "description": "что именно ты увидел(а) — своими словами"}},
                "required": ["что"]}}},'''

ST_RUKI = '''    def _posmotret_dosku(args: dict) -> str:
        try:
            import doska
            return doska.slovami(symbol)
        except Exception as e:
            return f"доска не прочиталась: {e}"

    def _obyavit(args: dict) -> str:
        chto = str(args.get("что", "")).strip().lower()
        kto = (imya_zhitelya or slot)
        try:
            import doska
            if chto in ("точка_ноль", "точка ноль", "нол", "ноль"):
                ok, m = doska.obyavit_tochku_nol(
                    symbol, kto, args.get("цена"),
                    str(args.get("бар", "")), str(args.get("почему", "")))
            elif chto in ("первая_волна", "первая волна", "волна"):
                ok, m = doska.obyavit_pervuyu_volnu(
                    symbol, kto, args.get("цена"),
                    str(args.get("почему", "")))
            elif chto in ("откат",):
                ok, m = doska.obyavit_otkat(symbol, kto,
                                            str(args.get("почему", "")))
            elif chto in ("стереть", "сломалась"):
                ok, m = doska.steret(symbol, kto)
            else:
                return (f"не понял «{chto}». Можно: точка_ноль, "
                        f"первая_волна, откат, стереть")
        except Exception as e:
            return f"объявить не вышло: {e}"
        print(f"[ДОСКА] {'✓' if ok else '✗'} {m}")
        return ("Записано на доску. " + m) if ok else ("Не записано: " + m)'''

NOV_RUKI = '''    def _moya_kartina(args: dict) -> str:
        try:
            import kartina
            return kartina.slovami(ceh, slot, symbol)
        except Exception as e:
            return f"картина не прочиталась: {e}"

    def _zapisat_v_kartinu(args: dict) -> str:
        try:
            import kartina
            ok, m = kartina.obyavit(
                ceh, slot, symbol, str(args.get("что", "")),
                kto=(imya_zhitelya or slot), cena=args.get("цена"),
                bar=str(args.get("бар", "")),
                pochemu=str(args.get("почему", "")))
        except Exception as e:
            return f"записать не вышло: {e}"
        print(f"[КАРТИНА] {'✓' if ok else '✗'} {imya_zhitelya or slot}: {m}")
        return ("Записал(а) в твою картину. " + m) if ok else ("Не записано: " + m)'''

ST_KLYUCHI = '''            "posmotret_dosku": _posmotret_dosku,      # DOSKA_V1
            "obyavit_na_dosku": _obyavit,'''
NOV_KLYUCHI = '''            "moya_kartina": _moya_kartina,            # KARTINA_SVOYA_V1
            "zapisat_v_kartinu": _zapisat_v_kartinu,'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    kartina = koren / "Биржа" / "kartina.py"
    doska = koren / "Биржа" / "doska.py"
    ruki = koren / "Биржа" / "ruki_treydera.py"

    print("\n1. Личная картина — Биржа/kartina.py")
    if kartina.exists() and MARKER in kartina.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        try:
            ast.parse(KARTINA_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if not SUHO:
            kartina.write_text(KARTINA_PY, encoding="utf-8")
        print("  ✓ положена (своя у каждого, при слоте)")

    print("\n2. Руки: своя картина вместо общей доски")
    t = ruki.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        pary = [("схема", ST_SHEMA, NOV_SHEMA),
                ("руки", ST_RUKI, NOV_RUKI),
                ("ключи", ST_KLYUCHI, NOV_KLYUCHI)]
        beda = [imya for imya, st, _ in pary if t.count(st) != 1]
        if beda:
            print(f"  ✗ якоря не найдены: {', '.join(beda)}")
            return 1
        novyy = t
        for _, st, nov in pary:
            novyy = novyy.replace(st, nov, 1)
        novyy += f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(ruki, ruki.with_suffix(
                f".py.bak_kartina_{datetime.now():%Y%m%d_%H%M%S}"))
            ruki.write_text(novyy, encoding="utf-8")
            print("  ✓ переставлены")

    print("\n3. Общая доска — в сторону, не удаляя")
    if doska.exists() and not SUHO:
        novoe = doska.with_suffix(".py.snesen")
        if not novoe.exists():
            doska.rename(novoe)
            print(f"  ✓ doska.py → {novoe.name} (уборщик уберёт, когда скажешь)")
        else:
            print("  · уже отложена")
    elif SUHO:
        print("  · отложил бы (сухой прогон)")

    if not SUHO:
        import py_compile
        for f in (kartina, ruki):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь у каждого своё чтение, и оно не теряется между")
        print("барами. Вася видит одну волну, Петя другую — оба правы.")
        print("Захочет вести все три входа сразу — ведёт.")
        print("\nПодсмотра у соседей нет — как ты и сказал.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
