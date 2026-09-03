# -*- coding: utf-8 -*-
# MARKER: ETAZH_V_BARAH_V1
"""
ЭТАЖ СЧИТАЕТСЯ В БАРАХ, А НЕ В КАЛЕНДАРЕ.

ЧТО БЫЛО СЛОМАНО
────────────────
`rastyanut.py` подбирал этаж так: взял разницу между двумя датами в
минутах и поделил на 120. Но рынок по выходным стоит, а календарь
идёт. Замер: откат 02.10 → 07.10 обещал 116 баров H1, реально их
69 — почти вдвое меньше. Растяжка обещала «кусок в окне 100-140»,
а показывала полупустой кадр.

Врало ДВАЖДЫ: сначала при выборе этажа, потом в подписи «кусок занял
N баров этажа X» — та же календарная арифметика.

ЧТО ДЕЛАЕТСЯ
────────────
Растяжка теперь СЧИТАЕТ бары краном, а не выводит их из календаря:
    · календарь остаётся только первой прикидкой, с какого этажа
      начать считать — дальше он не участвует;
    · на этом этаже бары окна пересчитываются по-настоящему;
    · не попали в 100-140 — из настоящего числа баров берутся
      настоящие ТОРГОВЫЕ минуты куска, и этаж подбирается заново.
      Обычно хватает одного круга, больше четырёх не делаем;
    · «баров» в ответе — то, что посчитано, а не то, что обещано.

ЧТО НЕ ТРОГАЕТСЯ
────────────────
Сам `podobrat_etazh(минуты)` остаётся как есть. Он чистая арифметика,
и в `pyat_pul.py` его зовут ЧЕСТНО — там на вход идёт число реальных
баров, помноженное на длину бара, то есть уже торговое время. Сломай
его — сломается измерение волны.

Идемпотентен. .bak рядом. Путь ищет сам.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "ETAZH_V_BARAH_V1"


def _nayti_birzhu() -> Path:
    primety = ("rastyanut.py", "masshtab.py", "grafik.py")
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
        if (p / "rastyanut.py").exists():
            return p
        raise SystemExit("не та папка — там нет rastyanut.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


# ── что вставляем: две руки счёта, перед самой rastyanut ──────────
NOVYE_RUKI = '''
# ═══ ETAZH_V_BARAH_V1 ═══
# Календарь врёт: между двумя датами лежат выходные и праздники, а
# рынок в них стоит. Считаем бары краном — единственная честная мера.

def _barov_v_okne(symbol: str, etazh: str, t1, t2):
    """Сколько баров этажа РЕАЛЬНО легло между t1 и t2. None — не дали."""
    import masshtab
    from feed_source import bars as _bars
    m = masshtab.minut(etazh) or 60
    kalendar = max(1.0, (t2 - t1).total_seconds() / 60.0)
    # глубина запроса — по календарю С ЗАПАСОМ: реальных баров всегда
    # МЕНЬШЕ календарных, так что промахнуться можно только в плюс.
    glubina = int(kalendar / m) + 200
    try:
        _probniki, _ = _bars(symbol, etazh, 5)
        if _probniki:
            _posledniy = _vremya(_probniki[-1].get("date", ""))
            if _posledniy and _posledniy > t2:
                glubina += int((_posledniy - t2).total_seconds() / 60 / m)
    except Exception:
        pass
    glubina = max(300, min(glubina, 20000))
    try:
        bs, _ = _bars(symbol, etazh, glubina)
    except Exception:
        return None
    if not bs:
        return None
    n = 0
    for b in bs:
        t = _vremya(b.get("date", ""))
        if t and t1 <= t <= t2:
            n += 1
    return n


def podobrat_etazh_po_baram(symbol: str, t1, t2, nachalnyy: str = ""):
    """Этаж, на котором кусок ЛЯЖЕТ в окно 100-140 баров, и сколько их.

    Возвращает (этаж, баров). Баров None — кран промолчал, тогда
    этаж выбран по старой календарной прикидке, и это честно видно.
    """
    import masshtab
    kalendar = max(1.0, (t2 - t1).total_seconds() / 60.0)
    etazh = (nachalnyy or "").strip().upper()
    if not masshtab.est(etazh):
        etazh = podobrat_etazh(kalendar)   # только первая прикидка
    nizhe, verhe = masshtab.OKNO
    videnye, barov = set(), None
    for _ in range(4):
        if etazh in videnye:
            break
        videnye.add(etazh)
        n = _barov_v_okne(symbol, etazh, t1, t2)
        if not n:
            break
        barov = n
        if nizhe <= n <= verhe:
            break
        # настоящее ТОРГОВОЕ время куска — из настоящих баров
        torgovye = n * (masshtab.minut(etazh) or 60)
        sled = podobrat_etazh(torgovye)
        if not masshtab.est(sled) or sled == etazh:
            break
        etazh = sled
    return etazh, barov

'''

# ── что заменяем внутри rastyanut() ──────────────────────────────
STARYY_PODBOR = '''    minut = max(1.0, (t2 - t1).total_seconds() / 60.0)
    etazh = (etazh_podskazka or "").strip().upper()
    if not masshtab.est(etazh):
        etazh = podobrat_etazh(minut)

    # сколько баров этого этажа ляжет в кусок и сколько взять с полем
    m = masshtab.minut(etazh) or 60
    v_kuske = int(minut / m)
    barov = max(60, int(v_kuske * (1 + 2 * POLE)))
'''

NOVYY_PODBOR = '''    minut = max(1.0, (t2 - t1).total_seconds() / 60.0)
    etazh = (etazh_podskazka or "").strip().upper()
    # ETAZH_V_BARAH_V1: этаж и длина куска — СЧИТАННЫЕ бары, не календарь.
    # Подсказка трейдера уважается: он говорит, на каком этаже смотреть,
    # мы только меряем, сколько там баров вышло.
    etazh, v_kuske = podobrat_etazh_po_baram(symbol, t1, t2, etazh)
    m = masshtab.minut(etazh) or 60
    if not v_kuske:                      # кран промолчал — старая прикидка
        v_kuske = int(minut / m)
    barov = max(60, int(v_kuske * (1 + 2 * POLE)))
'''

YAKOR_VSTAVKI = '''def rastyanut(symbol: str, s_kogda: str, po_kogda: str = "",'''


def main():
    b = _nayti_birzhu()
    print(f"\nБиржа: {b}\n")
    f = b / "rastyanut.py"
    src = f.read_text(encoding="utf-8")

    if MARKER in src:
        print("  · уже накачено, ничего не делаю")
        return

    if STARYY_PODBOR not in src:
        raise SystemExit(
            "  ! не нашёл прежний подбор этажа в rastyanut.py — файл\n"
            "    правили после меня. Скажи Брату, посмотрит глазами.")
    if YAKOR_VSTAVKI not in src:
        raise SystemExit("  ! не нашёл начало rastyanut() — не трогаю файл")

    novyy = src.replace(STARYY_PODBOR, NOVYY_PODBOR)
    novyy = novyy.replace(YAKOR_VSTAVKI, NOVYE_RUKI + "\n" + YAKOR_VSTAVKI, 1)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    ast.parse(novyy)          # не кладём на диск то, что не разбирается
    shutil.copy2(f, f.with_suffix(".py.bak_etazh"))
    f.write_text(novyy, encoding="utf-8")
    print("  + rastyanut.py: этаж и длина куска считаются в барах "
          "(.bak_etazh рядом)")
    print("\nГотово. Растяжка больше не обещает баров, которых нет.")
    print("podobrat_etazh(минуты) не тронут — в pyat_pul.py его зовут честно.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
