# -*- coding: utf-8 -*-
"""
postavit_ruku_rastyazhki.py · MARKER: RASTYAZHKA_V1

СЛОВА ШЕФА, ПО КОТОРЫМ ЭТО СДЕЛАНО
──────────────────────────────────
    «Коррекция созрела — видно, когда саму коррекцию растянешь, весь
    зигзаг на 100-140 баров. Увидишь чётко волны в зигзаге. И вот
    волну С от начала до конца в диапазон 100-140 вписываешь — и видно
    совсем хорошо: 3-я волна, AO самый, дивергенция, разворотник.
    Здесь смотреть нужно, потом считать, а не наоборот.»

    «Сейчас это просто последние 120 баров на H4. А нужно растягивать
    именно ту волну, которая нужна. Да и не всегда ровно по ТФ и ровно
    количество — поэтому и визуал, и математика.»

ЧТО БЫЛО НЕ ТАК
───────────────
1. КАДР ВСЕГДА ОДИН И ТОТ ЖЕ: последние 140 баров рабочего этажа.
   Растянуть конкретную волну было нечем. Матрёшка Шефа — зигзаг
   целиком, потом волна C внутри него — не строилась в принципе.

2. У ТРЕЙДЕРА НЕТ ГЛАЗ, КРОМЕ ПЕРВОГО КАДРА. Все три его руки
   возвращают ТЕКСТ: числа стола, замер волны, дневник. Картинку в
   ответ руки положить нельзя — значит «просто посмотреть на другой
   масштаб» он физически не мог. Мог попросить — не мог увидеть.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. `Биржа/rastyanut.py` — растяжка объекта:
   · берёт кусок «от» и «до» (даты или «столько-то баров назад»);
   · считает, сколько в нём ВРЕМЕНИ, и подбирает этаж так, чтобы
     объект лёг в 100-140 баров: `минут_в_куске / 120` → ближайшая
     ступень лесенки. Не всегда ровно — поэтому и берётся ближайшая,
     а окончательно судит глаз;
   · рисует кадр ИМЕННО ЭТОГО куска, с небольшим полем слева и
     справа, чтобы было видно, откуда пришли и куда ушли.

2. Рука `rastyanut(с, по)` у трейдера — и главное, ОНА ВОЗВРАЩАЕТ
   КАРТИНКУ. Для этого научена дверь «кадр + руки»: если рука вернула
   метку `[КАДР: путь]`, картинка досылается в тот же разговор
   отдельным сообщением — трейдер видит её и продолжает.
   Так же делает человек: «дай гляну на M15» — и ему открывают M15.

3. Заодно рука `pokazat_etazh(этаж)` — просто посмотреть другой
   масштаб целиком, без объекта.

ПОРЯДОК ОСТАЁТСЯ ЕГО
────────────────────
Код ничего не ищет и не размечает: он растягивает то, что назвали, и
показывает. Где начало волны и где конец — говорит трейдер. Сперва
смотрит, потом считает.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_ruku_rastyazhki.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RASTYAZHKA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ruki_treydera.py").exists()
            and (p / "Биржа" / "grafik.py").exists())


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


RASTYANUT_PY = '''# -*- coding: utf-8 -*-
# RASTYAZHKA_V1
"""
РАСТЯЖКА — показать НУЖНУЮ волну так, чтобы её было видно.

СЛОВА ШЕФА
    «Коррекция созрела — видно, когда саму коррекцию растянешь, весь
    зигзаг на 100-140 баров... И вот волну С от начала до конца в
    диапазон 100-140 вписываешь — и видно совсем хорошо: 3-я волна,
    AO самый, дивергенция, разворотник.»

    «Не всегда ровно по ТФ и ровно количество — поэтому и визуал, и
    математика.»

ЗАКОН ЭТОГО ФАЙЛА
    Растягивает то, что НАЗВАЛИ, и показывает. Не ищет волн, не
    размечает, не советует. Где начало объекта и где конец — говорит
    трейдер: он смотрит, потом считает, а не наоборот.

    Этаж подбирается арифметикой: сколько в куске времени, поделить
    на 120 — вот минут на бар, берём ближайшую ступень лесенки. Ровно
    не выйдет почти никогда, и это нормально: окончательно судит глаз.
"""
from __future__ import annotations

import sys as _sys
from datetime import datetime, timedelta
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))

CEL_BAROV = 120          # середина окна 100-140
POLE = 0.15              # поле слева и справа, чтобы видеть подход и выход


def _vremya(s: str):
    import istoriya
    return istoriya.kak_vremya(s)


def podobrat_etazh(minut_v_kuske: float) -> str:
    """Какой этаж растянет кусок примерно на 120 баров."""
    import masshtab
    if minut_v_kuske <= 0:
        return "H4"
    nado = minut_v_kuske / CEL_BAROV
    luchshiy, raznica = "H4", None
    for tf in masshtab.LESTNICA:
        m = masshtab.minut(tf)
        if not m:
            continue
        r = abs(m - nado) / max(m, nado)
        if raznica is None or r < raznica:
            luchshiy, raznica = tf, r
    return luchshiy


def rastyanut(symbol: str, s_kogda: str, po_kogda: str = "",
              etazh_podskazka: str = "") -> dict:
    """Растянуть кусок и нарисовать его.

    Возвращает {этаж, баров, кадр, с, по, пояснение}. Кадра нет —
    в «кадр» будет None, а в «пояснение» причина.
    """
    import masshtab
    from feed_source import bars as _bars
    import grafik

    t1 = _vremya(s_kogda)
    t2 = _vremya(po_kogda) if po_kogda else None
    if t1 is None:
        return {"кадр": None,
                "пояснение": f"не понял дату «{s_kogda}» "
                             f"(жду вид 2025.05.05 20:00)"}
    if t2 is None:
        t2 = datetime.now()
    if t2 < t1:
        t1, t2 = t2, t1

    minut = max(1.0, (t2 - t1).total_seconds() / 60.0)
    etazh = (etazh_podskazka or "").strip().upper()
    if not masshtab.est(etazh):
        etazh = podobrat_etazh(minut)

    # сколько баров этого этажа ляжет в кусок и сколько взять с полем
    m = masshtab.minut(etazh) or 60
    v_kuske = int(minut / m)
    barov = max(60, int(v_kuske * (1 + 2 * POLE)))

    # Сколько баров назад лежит конец куска. Без этого счёта мы
    # просили у крана 400 баров и не дотягивались до прошлого года —
    # а потом МОЛЧА рисовали последние бары вместо запрошенных. Врать
    # картинкой хуже, чем отказать.
    _probniki, point = _bars(symbol, etazh, 5)
    nuzhno = max(400, barov + 60)
    if _probniki:
        _posledniy = _vremya(_probniki[-1].get("date", ""))
        if _posledniy and _posledniy > t2:
            nazad = int((_posledniy - t2).total_seconds() / 60 / m)
            nuzhno = max(nuzhno, nazad + barov + 60)

    bs, point = _bars(symbol, etazh, nuzhno)
    if not bs:
        return {"кадр": None, "этаж": etazh,
                "пояснение": f"котировок {symbol} {etazh} не дали"}

    # оставляем только бары до конца куска — «после» трейдеру видеть
    # незачем, иначе он будет смотреть в будущее
    do_konca = [b for b in bs if (_vremya(b.get("date", "")) or t1) <= t2]
    if not do_konca:
        _pervyy = bs[0].get("date", "?")
        return {"кадр": None, "этаж": etazh,
                "пояснение": (f"до {po_kogda or 'этого места'} не дотянулся: "
                              f"история {symbol} {etazh} начинается с "
                              f"{_pervyy}. Картинку не рисую, чтобы не "
                              f"показать чужой кусок.")}
    bs = do_konca[-barov:]
    if len(bs) < 30:
        return {"кадр": None, "этаж": etazh,
                "пояснение": f"на {etazh} в этом куске всего {len(bs)} "
                             f"баров — мало для картинки"}

    from williams_core import (compute_alligator, compute_ao_series,
                               detect_fractals)
    highs = [x["high"] for x in bs]
    lows = [x["low"] for x in bs]
    put = grafik.narisovat(bs, compute_alligator(highs, lows, point=point),
                           compute_ao_series(highs, lows), symbol, etazh,
                           barov=len(bs), fraktaly=detect_fractals(bs))
    return {"кадр": put, "этаж": etazh, "баров": v_kuske,
            "с": bs[0].get("date"), "по": bs[-1].get("date"),
            "пояснение": (f"кусок занял {v_kuske} баров этажа {etazh} "
                          f"(цель 100-140)")}


# RASTYAZHKA_V1 - marker
'''


# ── 1. руки трейдера: растяжка и «покажи этаж» ──
ST_RUKI_SHEMA = '''        {"type": "function", "function": {
            "name": "moy_dnevnik",'''

NOV_RUKI_SHEMA = '''        # RASTYAZHKA_V1: главные глаза трейдера. Раньше он видел ровно
        # один кадр — последние 140 баров рабочего этажа, — и растянуть
        # нужную волну не мог ничем.
        {"type": "function", "function": {
            "name": "rastyanut_volnu",
            "description": (
                "ПОКАЗАТЬ картинку куска рынка, растянутого так, чтобы он "
                "занял 100-140 баров. Так смотрят зигзаг целиком, а потом "
                "волну C внутри него. Этаж подбирается сам под длину "
                "куска — можешь не указывать. Ты УВИДИШЬ картинку."),
            "parameters": {"type": "object", "properties": {
                "с": {"type": "string",
                      "description": "начало куска, вид 2025.05.05 20:00"},
                "по": {"type": "string",
                       "description": "конец куска; пусто — до текущего бара"},
                "этаж": {"type": "string",
                         "description": "необязательно, если хочешь свой"}},
                "required": ["с"]}}},
        {"type": "function", "function": {
            "name": "pokazat_etazh",
            "description": (
                "ПОКАЗАТЬ картинку другого этажа целиком, последние 140 "
                "баров. Когда нужно просто взглянуть шире или мельче."),
            "parameters": {"type": "object", "properties": {
                "этаж": {"type": "string", "description": "например M30"}},
                "required": ["этаж"]}}},
        {"type": "function", "function": {
            "name": "moy_dnevnik",'''

ST_RUKI_HVOST = '''    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik}'''

NOV_RUKI_HVOST = '''    def _rastyanut(args: dict) -> str:
        """RASTYAZHKA_V1: возвращает МЕТКУ кадра — картинку дошлёт
        разговор. Текстом картинку не передать, а трейдеру нужно
        именно увидеть."""
        try:
            import rastyanut as _r
            d = _r.rastyanut(symbol, str(args.get("с", "")),
                             str(args.get("по", "")),
                             str(args.get("этаж", "")))
        except Exception as e:
            return f"растянуть не вышло: {e}"
        if not d.get("кадр"):
            return d.get("пояснение") or "кадр не нарисовался"
        return (f"[КАДР: {d['кадр']}] {d.get('пояснение', '')} · "
                f"с {d.get('с')} по {d.get('по')}")

    def _pokazat_etazh(args: dict) -> str:
        tf = str(args.get("этаж", "")).strip().upper()
        try:
            import masshtab
            if not masshtab.est(tf):
                return f"такого этажа нет: {tf}"
            import grafik
            put = grafik.kadr(symbol, tf)
        except Exception as e:
            return f"показать {tf} не вышло: {e}"
        if not put:
            return f"котировок {symbol} {tf} не дали"
        return f"[КАДР: {put}] {symbol} {tf}, последние 140 баров"

    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,
            "rastyanut_volnu": _rastyanut,      # RASTYAZHKA_V1
            "pokazat_etazh": _pokazat_etazh}'''


# ── 2. дверь учится досылать картинку по метке ──
ST_LLM = '''            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": otvet})'''

NOV_LLM = '''            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": otvet})
            # RASTYAZHKA_V1: рука вернула метку кадра — досылаем саму
            # КАРТИНКУ отдельным сообщением. В ответ руки изображение
            # не положить, а трейдеру нужно увидеть, а не прочитать.
            if isinstance(otvet, str) and otvet.startswith("[КАДР: "):
                try:
                    import base64 as _b64
                    from pathlib import Path as _P
                    _put = _P(otvet[7:otvet.index("]")])
                    if _put.exists():
                        _b = _b64.b64encode(_put.read_bytes()).decode("ascii")
                        messages.append({"role": "user", "content": [
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{_b}"}},
                            {"type": "text",
                             "text": "Вот картинка, которую ты попросил(а). "
                                     "Смотри."}]})
                        print(f"[РУКА] 🖼 дослал кадр: {_put.name}")
                except Exception as _ek:
                    print(f"[РУКА] кадр не дослался: {_ek}")'''


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
    rast = koren / "Биржа" / "rastyanut.py"
    ruki = koren / "Биржа" / "ruki_treydera.py"
    llm = koren / "Биржа" / "llm.py"

    print("\n1. Растяжка — Биржа/rastyanut.py")
    if rast.exists() and MARKER in rast.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        try:
            ast.parse(RASTYANUT_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if not SUHO:
            rast.write_text(RASTYANUT_PY, encoding="utf-8")
        print("  ✓ положена")

    print("\n2. Руки трейдера — растянуть и показать этаж")
    if not pravit(ruki, [(ST_RUKI_SHEMA, NOV_RUKI_SHEMA),
                         (ST_RUKI_HVOST, NOV_RUKI_HVOST)], "rast"):
        return 1

    print("\n3. Разговор учится досылать КАРТИНКУ")
    if not pravit(llm, [(ST_LLM, NOV_LLM)], "rast"):
        return 1

    if not SUHO:
        import py_compile
        for f in (rast, ruki, llm):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь трейдер может смотреть, а не только читать:")
        print("  «растяни мне с 2025.04.10 по 2025.05.05» — код подберёт")
        print("  этаж под 100-140 баров, нарисует ЭТОТ кусок и покажет.")
        print("  В консоли будет видно: [РУКА] 🖼 дослал кадр")
        print("\nКод при этом не ищет волн и ничего не размечает —")
        print("границы называет он сам. Смотрит, потом считает.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
