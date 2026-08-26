# -*- coding: utf-8 -*-
"""
postavit_dosku.py · MARKER: DOSKA_V1

ЗАЧЕМ (разговор 16.08)
──────────────────────
Замер показал: разворотник НЕЛЬЗЯ отсеять по числам. Все признаки на
рабочем этаже дают одинаковые 11-13%, а «натяжение» даже хуже. Значит
отличить конец волны от середины боковика формулой не выйдет.

Отсеивается он так, как сказал Шеф: растянуть волну C и посмотреть,
третья ли это волна там — есть ли дивергенция, ангуляция, самый AO.
То есть ОТСЕВ — ЭТО ВЗГЛЯД НА ДРУГОМ МАСШТАБЕ, а не формула.

Отсюда: точку ноль — конец коррекции, откуда пойдёт первая волна —
определяет ТОТ, КТО ПОСМОТРЕЛ. Не код.

    код нашёл кандидата → трейдер растянул, посмотрел →
    сказал «да, коррекция кончилась» → ЭТО И ЕСТЬ ТОЧКА НОЛЬ

А от неё пляшут откатчицы: пошла первая волна, ждём откат к ней.
Сейчас у них нет отсчёта, и они честно отвечают «нет первой волны» —
никто не сказал, откуда она начала расти.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Заводит ДОСКУ ИНСТРУМЕНТА — общую память о структуре, на которую
смотрят все за столом:

    точка ноль   — кто объявил, когда, по какой цене, и его словами
                   ПОЧЕМУ (что он увидел на растянутом)
    первая волна — пошла ли от неё, докуда дошла
    откат        — начался ли к первой волне

Доска живёт при цехе, рядом со столом: одна на инструмент. Объявил
один — видят все. Это не оценка и не сигнал: доска ЗАПИСЫВАЕТ, кто
что объявил, и не судит, прав ли он.

ЧЕСТНО ПРО СЛАБОЕ МЕСТО
───────────────────────
На объявленной точке ноль будут стоять решения остальных. Ошибётся
объявивший — ошибутся все. Это цена того, что корень ставит глаз, а
не формула. Но формула, как показал замер, не работает вовсе.

Поэтому доска помнит, КТО объявил и ПОЧЕМУ, — чтобы по итогу сделки
было видно, чей взгляд оказался верным, а чей нет.

ЧТО ЭТО НЕ ДЕЛАЕТ
─────────────────
Не ставит точку ноль само. Пока никто не объявил — доска пуста, и
это честное состояние, а не поломка. Объявлять некому, пока за столом
нет того, чей вход — конец коррекции: все трое выбрали откат.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_dosku.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "DOSKA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "ruki_treydera.py").exists())


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


DOSKA_PY = '''# -*- coding: utf-8 -*-
# DOSKA_V1
"""
ДОСКА ИНСТРУМЕНТА — общая память о структуре.

ЗАЧЕМ
    Разворотник нельзя отсеять по числам: замер 16.08 показал, что все
    признаки на рабочем этаже дают одинаковые 11-13%. Отсев — это
    взгляд на растянутой волне C, а не формула. Значит конец коррекции
    (ТОЧКУ НОЛЬ) объявляет тот, кто посмотрел.

    А от точки ноль пляшут остальные: пошла первая волна, ждём откат к
    ней. Без общей доски объявленное одним не видно другим, и
    откатчицы честно отвечают «нет первой волны» — им никто не сказал,
    откуда она начала расти.

ЗАКОН ЭТОГО ФАЙЛА
    Доска ЗАПИСЫВАЕТ и ПОКАЗЫВАЕТ. Она не судит, прав ли объявивший, и
    сама ничего не объявляет. Пусто — значит никто не смотрел или
    никто не увидел; это честное состояние, а не поломка.

    Помним КТО объявил и ПОЧЕМУ — его словами. По итогу сделки будет
    видно, чей взгляд оказался верным.
"""
from __future__ import annotations

import sys as _sys
from datetime import datetime
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))

PUSTO = {"точка_ноль": None, "первая_волна": None, "откат": None}


def _vsya() -> dict:
    from hooks import load_trading_state
    return (load_trading_state().get("доска") or {})


def _sohranit(d: dict):
    from hooks import load_trading_state, save_trading_state
    t = load_trading_state()
    t["доска"] = d
    save_trading_state(t)


def chitat(symbol: str) -> dict:
    """Что на доске по этому инструменту."""
    s = (symbol or "").strip().upper()
    d = dict(PUSTO)
    d.update((_vsya().get(s) or {}))
    return d


def obyavit_tochku_nol(symbol: str, kto: str, cena, kogda: str,
                       pochemu: str = "") -> tuple:
    """Объявить конец коррекции. Ставит НОВУЮ точку и стирает то, что
    от прежней выросло: раз корень другой — и волна, и откат другие."""
    s = (symbol or "").strip().upper()
    if not s:
        return False, "не сказано, по какому инструменту"
    try:
        cena = float(cena)
    except Exception:
        return False, f"цена не число: {cena}"
    vsya = _vsya()
    vsya[s] = {
        "точка_ноль": {"кто": kto, "цена": cena, "бар": kogda,
                       "почему": (pochemu or "").strip()[:500],
                       "объявлено": datetime.now().isoformat(
                           timespec="seconds")},
        "первая_волна": None,
        "откат": None,
    }
    _sohranit(vsya)
    return True, f"{kto}: точка ноль {s} @ {cena} ({kogda})"


def obyavit_pervuyu_volnu(symbol: str, kto: str, do_ceny,
                          pochemu: str = "") -> tuple:
    """От точки ноль пошла первая волна и дошла досюда."""
    s = (symbol or "").strip().upper()
    d = chitat(s)
    if not d.get("точка_ноль"):
        return False, ("точки ноль нет — от чего волна? Сперва кто-то "
                       "должен объявить конец коррекции")
    try:
        do_ceny = float(do_ceny)
    except Exception:
        return False, f"цена не число: {do_ceny}"
    vsya = _vsya()
    vsya.setdefault(s, dict(PUSTO))["первая_волна"] = {
        "кто": kto, "докуда": do_ceny,
        "почему": (pochemu or "").strip()[:500],
        "объявлено": datetime.now().isoformat(timespec="seconds")}
    _sohranit(vsya)
    return True, f"{kto}: первая волна {s} до {do_ceny}"


def obyavit_otkat(symbol: str, kto: str, pochemu: str = "") -> tuple:
    """К первой волне начался откат — то, чего ждут откатчицы."""
    s = (symbol or "").strip().upper()
    d = chitat(s)
    if not d.get("первая_волна"):
        return False, "первой волны нет — откатывать нечему"
    vsya = _vsya()
    vsya.setdefault(s, dict(PUSTO))["откат"] = {
        "кто": kto, "почему": (pochemu or "").strip()[:500],
        "объявлено": datetime.now().isoformat(timespec="seconds")}
    _sohranit(vsya)
    return True, f"{kto}: пошёл откат к первой волне {s}"


def steret(symbol: str, kto: str = "") -> tuple:
    """Структура сломалась — доска чистая. Тоже решение, и тоже чьё-то."""
    s = (symbol or "").strip().upper()
    vsya = _vsya()
    if s in vsya:
        vsya.pop(s)
        _sohranit(vsya)
    return True, f"{kto or 'кто-то'}: доска {s} стёрта"


def slovami(symbol: str) -> str:
    """Доска человеку и трейдеру. Только записанное, без выводов."""
    d = chitat(symbol)
    tn = d.get("точка_ноль")
    if not tn:
        return ("=== ДОСКА · " + (symbol or "?") + " ===\\n"
                "Пусто: точку ноль (конец коррекции) никто не объявлял.\\n"
                "Пока её нет, отсчитывать первую волну не от чего.")
    L = ["=== ДОСКА · " + symbol.upper() + " ===",
         f"ТОЧКА НОЛЬ: {tn['цена']} на баре {tn['бар']} — "
         f"объявил(а) {tn['кто']}"]
    if tn.get("почему"):
        L.append(f"   почему: {tn['почему']}")
    pv = d.get("первая_волна")
    if pv:
        L.append(f"ПЕРВАЯ ВОЛНА: дошла до {pv['докуда']} — {pv['кто']}")
        if pv.get("почему"):
            L.append(f"   почему: {pv['почему']}")
    else:
        L.append("ПЕРВАЯ ВОЛНА: ещё не объявлена")
    ot = d.get("откат")
    if ot:
        L.append(f"ОТКАТ: идёт — {ot['кто']}")
        if ot.get("почему"):
            L.append(f"   почему: {ot['почему']}")
    else:
        L.append("ОТКАТ: не объявлен")
    return "\\n".join(L)


# DOSKA_V1 - marker
'''


# ── руки: посмотреть доску и объявить на неё ──
ST_SHEMA = '''        {"type": "function", "function": {
            "name": "moy_dnevnik",'''

NOV_SHEMA = '''        # DOSKA_V1: общая память о структуре. Разворотник нельзя
        # отсеять числами — отсев это взгляд на растянутой волне C.
        # Кто посмотрел и увидел конец коррекции, тот и объявляет
        # точку ноль; от неё пляшут остальные.
        {"type": "function", "function": {
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
                "required": ["что"]}}},
        {"type": "function", "function": {
            "name": "moy_dnevnik",'''

ST_RUKI = '''    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,'''

NOV_RUKI = '''    def _posmotret_dosku(args: dict) -> str:
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
        return ("Записано на доску. " + m) if ok else ("Не записано: " + m)

    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,
            "posmotret_dosku": _posmotret_dosku,      # DOSKA_V1
            "obyavit_na_dosku": _obyavit,'''

ST_PODPIS = '''def ruki(symbol: str, ceh: str, slot: str, self_key: str,
         dnevnik_fn=None, rabochiy_etazh: str = "H4") -> dict:'''
NOV_PODPIS = '''def ruki(symbol: str, ceh: str, slot: str, self_key: str,
         dnevnik_fn=None, rabochiy_etazh: str = "H4",
         imya_zhitelya: str = "") -> dict:'''


def pravit(put: Path, pary: list, imya: str) -> bool:
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"  · {put.name}: маркер уже стоит")
        return True
    beda = [st[:40].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден → «{b}…»")
        return False
    novyy = t
    for st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    shutil.copy2(put, put.with_suffix(
        put.suffix + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}"))
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    doska = koren / "Биржа" / "doska.py"
    ruki = koren / "Биржа" / "ruki_treydera.py"

    print("\n1. Доска — Биржа/doska.py")
    if doska.exists() and MARKER in doska.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        try:
            ast.parse(DOSKA_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if not SUHO:
            doska.write_text(DOSKA_PY, encoding="utf-8")
        print("  ✓ положена (точка ноль · первая волна · откат)")

    print("\n2. Руки: посмотреть доску и объявить на неё")
    if not pravit(ruki, [(ST_PODPIS, NOV_PODPIS), (ST_SHEMA, NOV_SHEMA),
                         (ST_RUKI, NOV_RUKI)], "doska"):
        return 1

    print("\n3. Мозги передают рукам имя жителя")
    st = '''                                       rabochiy_etazh=timeframe),'''
    nov = '''                                       rabochiy_etazh=timeframe,
                                       imya_zhitelya=_kto_ya()),'''
    for slot in ("A06", "A07", "A08"):
        m = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
             / "слоты" / slot / "мозг.py")
        if not m.exists():
            continue
        t = m.read_text(encoding="utf-8")
        if MARKER in t:
            print(f"  · {slot}: уже")
            continue
        if t.count(st) != 1:
            print(f"  ⚠ {slot}: вызов рук выглядит иначе — пропускаю")
            continue
        # имя жителя: берём из поста, как и везде в городе
        vstavka = '''

def _kto_ya() -> str:
    """DOSKA_V1: имя того, кто сидит на этом месте. На доске должно
    стоять имя человека, а не номер слота."""
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = _P(__file__).resolve()
        for _ in range(9):
            _g = _g.parent
            if (_g / "ГОРОД" / "rabota.py").exists():
                break
        if str(_g / "ГОРОД") not in _s.path:
            _s.path.insert(0, str(_g / "ГОРОД"))
        import rabota as _r
        return _r.kto_na_slote(_CEH, _SLOT) or _SLOT
    except Exception:
        return _SLOT

'''
        novyy = t.replace(st, nov, 1)
        novyy = novyy.rstrip("\n") + "\n" + vstavka + f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ {slot}: после правки не разбирается: {e}")
            return 1
        if SUHO:
            print(f"  · {slot}: правка готова (сухой прогон)")
            continue
        shutil.copy2(m, m.with_suffix(
            f".py.bak_doska_{datetime.now():%Y%m%d_%H%M%S}"))
        m.write_text(novyy, encoding="utf-8")
        print(f"  ✓ {slot}")

    if not SUHO:
        import py_compile
        faily = [doska, ruki] + [
            koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
            / "слоты" / s / "мозг.py" for s in ("A06", "A07", "A08")]
        for f in faily:
            if not f.exists():
                continue
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.parent.name}/{f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nДоска заведена и пуста — это честно: точку ноль пока")
        print("никто не объявлял, и объявлять некому. Все трое выбрали")
        print("откат, а конец коррекции — вход Авантюриста.")
        print("\nПоявится житель с таким входом — объявит, и остальные")
        print("сразу увидят, от чего плясать. Переписывать ничего не надо.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
