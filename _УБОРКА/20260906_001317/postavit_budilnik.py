# -*- coding: utf-8 -*-
# MARKER: NEKRON_BUDIT_V1
"""
БУДИЛЬНИК: НЕКРОН-БАР И ИЗЛОМ УРОВНЯ 2.

СЛОВО ШЕФА (03.09)
    «Те точки ноль хорошие, и некрон бар — то есть они вместе неплохо
    будят, а там уже трейдер сам решает, спит он или работает».

ЧТО БЫЛО
────────
Трейдера будило РОЖДЕНИЕ ТОЧКИ НОЛЬ — а точка рождалась старым
способом: некрон-бар плюс «читается структура» по нашей разметке.
Тот самый отбор, который забракован на первых трёх местах прогона,
стоял воротами перед взглядом: он решал, откроет ли человек график
вообще. Отбор числами закрыт шестью замерами — значит и воротам
здесь не место.

ЧТО ДЕЛАЕТСЯ
────────────
Два повода взглянуть, оба без суждения:

    НЕКРОН-БАР — приходит на самом баре, говорит КОГДА.
    ИЗЛОМ УРОВНЯ 2 — дозревает позже, говорит ГДЕ.

Ни один не судит, годится ли вход. Смотреть или спать — решает
трейдер, глядя на кадр. Прежние поводы (заявка, вход, закрытие,
конец волны 1, конец отката, рождение точки) остаются как были:
патч ДОБАВЛЯЕТ повод, а не отнимает.

ПРО ИЗЛОМЫ (нового прибора в городе не было)
────────────────────────────────────────────
Кладётся `Биржа/izlomy.py`. Механика собрана по скрину Шефа с
красными квадратами, порогов и выдуманных чисел в ней нет:

    1. фракталы Вильямса (центр из пяти);
    2. в серии одного типа держим самый крайний — уровень 1;
    3. ту же лупу поверх результата: излом остаётся, если он крайнее
       ОБОИХ соседей своего типа — уровень 2.

«Дозрел» считается честно: разметка пересчитывается по данным ДО
текущего бара и по данным ВКЛЮЧАЯ его. Появился новый излом — значит
именно сейчас про него стало можно узнать. Никакого подглядывания
вперёд: излом узнаётся с задержкой, это природа фрактала, а не брак.

ЧЕСТНАЯ ЦЕНА
────────────
Будить будут чаще. На H4 некрон-баров около двухсот в год, изломов
уровня 2 — семьдесят, часть совпадает. Это примерно четыре взгляда в
неделю, каждый — платный вызов модели. Так и задумано: отбирает не
число, а глаз.

Идемпотентен. .bak рядом. Путь ищет сам.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "NEKRON_BUDIT_V1"

IZLOMY = '''# -*- coding: utf-8 -*-
# NEKRON_BUDIT_V1
"""
ИЗЛОМЫ — где рынок ломался по-настоящему.

СЛОВО ШЕФА (02.09), глядя на разметку: «уровень 2 — шикарные точки,
это прям точки ноль». Объяснить словами, чем настоящий экстремум
отличается от заусеницы, он не смог — «вижу и все», — прислал скрин с
красными квадратами. Механика собрана по нему.

ЗАКОН ЭТОГО ФАЙЛА
    Только разметка. Ни входа, ни направления, ни суждения о том,
    годится место или нет. Порогов и подобранных чисел внутри нет
    вовсе — правило безразмерно и одинаково работает на всех этажах.

ЗАДЕРЖКА — ЭТО ПРИРОДА, А НЕ БРАК
    Излом признаётся только когда пришёл следующий фрактал того же
    типа и оказался слабее. Медиана — около десяти баров H4. Из
    ролика про фрактальную геометрию: фракталы не предсказывают, они
    показывают структуру прошлого. Поэтому излом не может быть
    сигналом входа — он говорит ГДЕ, а КОГДА говорит разворотный бар.
"""
from __future__ import annotations

from typing import Optional


def _fraktaly(bars: list) -> list:
    """Фракталы Вильямса одним списком, по порядку баров."""
    try:
        from williams_core import detect_fractals
    except Exception:
        return []
    fr = detect_fractals(bars) or {}
    spisok = []
    for storona, tip in (("all_up", "верх"), ("all_down", "низ")):
        for f in (fr.get(storona) or []):
            i, c = f.get("bar_index"), f.get("price")
            if i is None or c is None:
                continue
            spisok.append({"бар": i, "тип": tip, "цена": c,
                           "дата": f.get("date")})
    spisok.sort(key=lambda x: x["бар"])
    return spisok


def _krayniy(a: dict, b: dict) -> dict:
    """Из двух изломов одного типа — тот, что дальше ушёл."""
    if a["тип"] == "верх":
        return a if a["цена"] >= b["цена"] else b
    return a if a["цена"] <= b["цена"] else b


def uroven_1(spisok: list) -> list:
    """Чередование: в серии одного типа держим самый крайний."""
    itog = []
    for f in spisok:
        if itog and itog[-1]["тип"] == f["тип"]:
            itog[-1] = _krayniy(itog[-1], f)
        else:
            itog.append(dict(f))
    return itog


def uroven_2(ur1: list) -> list:
    """Та же лупа поверх: крайнее ОБОИХ соседей своего типа."""
    itog = []
    for n, f in enumerate(ur1):
        sosedi = [x for m, x in enumerate(ur1)
                  if x["тип"] == f["тип"] and abs(m - n) <= 2 and m != n]
        if not sosedi:
            continue
        if f["тип"] == "верх":
            if all(f["цена"] > s["цена"] for s in sosedi):
                itog.append(dict(f))
        else:
            if all(f["цена"] < s["цена"] for s in sosedi):
                itog.append(dict(f))
    return itog


def izlomy(bars: list, uroven: int = 2) -> list:
    """Изломы указанного уровня на этих барах."""
    if not bars or len(bars) < 12:
        return []
    ur1 = uroven_1(_fraktaly(bars))
    return ur1 if uroven == 1 else uroven_2(ur1)


def dozrel(bars: list) -> Optional[dict]:
    """Излом ур.2, про который стало известно ИМЕННО НА ПОСЛЕДНЕМ баре.

    Момент созревания один и определён точно: излом признаётся, когда
    ДОСТРОИЛСЯ его правый сосед своего типа — то есть на баре
    «сосед + 2» (фракталу нужны два бара справа).

    Так было не сразу. Сперва разметка считалась дважды — до бара и
    включая его, — и что появилось, то и считалось созревшим. Прибор
    ДРЕБЕЗЖАЛ: цепочка чередования достраивается, излом успевал
    выпасть и вернуться, и за год выходило 174 побудки вместо 86
    настоящих изломов. Теперь каждый объявляется один раз.
    """
    if not bars or len(bars) < 14:
        return None
    ur1 = uroven_1(_fraktaly(bars))
    posl = len(bars) - 1
    for n, f in enumerate(ur1):
        if n - 2 < 0 or n + 2 >= len(ur1):
            continue
        lev, prav = ur1[n - 2], ur1[n + 2]
        if prav["бар"] + 2 != posl:      # созревает не сейчас
            continue
        krayneye = (f["цена"] > lev["цена"] and f["цена"] > prav["цена"]
                    if f["тип"] == "верх" else
                    f["цена"] < lev["цена"] and f["цена"] < prav["цена"])
        if krayneye:
            x = dict(f)
            x["баров_назад"] = posl - f["бар"]
            return x
    return None


# NEKRON_BUDIT_V1 - marker
'''


def _nayti_birzhu() -> Path:
    primety = ("council.py", "williams_core.py", "hooks.py")
    nashli, korni = [], []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        mesta = [koren]
        try:
            mesta += [x for x in koren.iterdir() if x.is_dir()]
        except OSError:
            pass
        for p in mesta:
            if all((p / f).exists() for f in primety) and p not in nashli:
                nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл папку Биржа рядом со скриптом.")
        s = input("Перетащи сюда папку Биржа и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "council.py").exists():
            return p
        raise SystemExit("не та папка — там нет council.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


POVOD = '''
# ═══ NEKRON_BUDIT_V1 ═══
# Два повода ВЗГЛЯНУТЬ. Ни один ничего не судит: некрон говорит
# КОГДА (приходит на самом баре), излом ур.2 говорит ГДЕ (дозревает
# позже). Годится место или нет — решает тот, кто смотрит.

def _povod_vzglyada(symbol: str, timeframe: str) -> str:
    """Строка-причина, если на этом баре есть на что взглянуть."""
    try:
        from feed_source import bars as _bars
        from williams_core import compute_alligator, detect_necron_bar
        import izlomy as _izl
        bs, point = _bars(symbol, timeframe, 300)
        try:
            import hooks as _h
            bs = _h._tolko_zakrytye(bs)
        except Exception:
            pass
        if not bs or len(bs) < 60:
            return ""
        _h_ = [b["high"] for b in bs]
        _l_ = [b["low"] for b in bs]
        al = compute_alligator(_h_, _l_, point=point)
        povody = []
        rb = detect_necron_bar(bs, al.get("jaw_series"),
                               al.get("teeth_series"), al.get("lips_series"))
        if rb.get("direction"):
            povody.append(f"разворотный бар {rb['direction']} @ {rb['price']}")
        iz = _izl.dozrel(bs)
        if iz:
            povody.append(f"излом {iz['тип']} @ {iz['цена']} "
                          f"({iz['баров_назад']} бар назад) стал виден")
        return "; ".join(povody)
    except Exception as _e:
        # Сбой прибора — НЕ повод будить на каждом баре: остальные
        # ключи (заявка, вход, закрытие, события структуры) на месте
        # и сработают сами.
        print(f"[КЛЮЧ] повод взгляда не посчитался: {_e}")
        return ""

'''

YAKOR_FUNKCII = "def _klyuch_probuzhdeniya(symbol: str, timeframe: str,"

STAR = '''        _ = slot   # KONEC_VOLNY_1_V1: наблюдение больше не ключ
'''

NOV = '''        _ = slot   # KONEC_VOLNY_1_V1: наблюдение больше не ключ

        # NEKRON_BUDIT_V1: сперва — есть ли на что ВЗГЛЯНУТЬ. Раньше
        # первым стояло рождение точки ноль, то есть наша разметка
        # решала, откроет ли человек график. Отбор числами закрыт
        # шестью замерами — ворот здесь больше нет.
        _vz = _povod_vzglyada(symbol, timeframe)
        if _vz:
            return {"будим": True, "почему": _vz}
'''


def main():
    b = _nayti_birzhu()
    print(f"\nБиржа: {b}\n")

    f_izl = b / "izlomy.py"
    if f_izl.exists() and MARKER in f_izl.read_text(encoding="utf-8"):
        print("  · izlomy.py уже на месте")
    else:
        ast.parse(IZLOMY)
        f_izl.write_text(IZLOMY, encoding="utf-8")
        print("  + izlomy.py: разметка изломов (лупа поверх фракталов)")

    f = b / "council.py"
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        print("  · council.py уже накачен")
        print("\nГотово (повтор).")
        return
    if STAR not in src or YAKOR_FUNKCII not in src:
        raise SystemExit("  ! ключ пробуждения выглядит иначе — не трогаю "
                         "council.py, скажи Брату")

    novyy = src.replace(YAKOR_FUNKCII, POVOD + "\n" + YAKOR_FUNKCII, 1)
    novyy = novyy.replace(STAR, NOV, 1)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    ast.parse(novyy)
    shutil.copy2(f, f.with_suffix(".py.bak_budilnik"))
    f.write_text(novyy, encoding="utf-8")
    print("  + council.py: будит некрон-бар и созревший излом "
          "(.bak_budilnik рядом)")
    print("\nГотово. Разметка больше не решает, откроет ли трейдер график.")
    print("Прежние поводы (заявка, вход, закрытие, события) остались.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
