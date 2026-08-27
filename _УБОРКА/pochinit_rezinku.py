# -*- coding: utf-8 -*-
"""
pochinit_rezinku.py · MARKER: REZINKA_CHESTNAYA_V1

ПОПРАВКА ШЕФА (20.08)
─────────────────────
«Снова код мнения? Отрыв — величина, дело относительное. Он визуально
смотрится, хватает или нет. Больше-меньше не числом, а фактом.»

Он прав. Я поставил в искателя проверку «бар вне пасти» — и сам же
померил, что она не отсеивает ничего: на всех пятнадцати местах бар
геометрически вне пасти. Значит вопрос не в стороне, а в величине
отрыва, а величину без числа не задать. Число тут выдумывать нельзя:
хватает отрыва или нет — видно глазом на кадре, и решает это трейдер.

Поэтому этот патч:
  · СНИМАЕТ проверку отрыва из искателя, если она уже легла
  · оставляет только починку прибора — резинку

ЧТО БЫЛО СЛОМАНО В РЕЗИНКЕ
──────────────────────────
На столе стояло: «натяжение от губ −445.3 п. (пик 105.7, доля −4.215)».
Доля по определению не бывает −4.2. Считалась она как «сейчас поделить
на пик», где пик копится ТОЛЬКО в сторону движения, а «сейчас» уходит в
минус, когда цена перешла на другую сторону губ. Получалось число,
которое выглядит как доля и не значит ничего.

Нина трижды об него споткнулась: «отрицательное натяжение вызывает
вопросы», «доля от пика −1.732».

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Доля считается, только пока цена по СВОЮ сторону губ. Перешла на
   другую — доли нет (None), и это честно.
2. «На пике» больше не срабатывает при отрицательном расстоянии.
3. Стол говорит словами: «расстояние до губ: 229 п. (цена по другую
   сторону губ)» вместо «−229.2 п., доля −1.732».

Само расстояние в пунктах остаётся как было — это факт, он не врал.
Мозги трейдеров уже умеют «доли нет»: там стоит проверка на None и
честная фраза вместо числа.

Никаких порогов, никаких суждений. Прибор перестаёт врать — что с этим
делать, по-прежнему решает тот, кто смотрит.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_rezinku.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "REZINKA_CHESTNAYA_V1"
STARYY = "OTRYV_I_REZINKA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "williams_core.py").exists()
            and (p / "Биржа" / "stol.py").exists()
            and (p / "Биржа" / "kandidaty.py").exists())


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


# ── снять отрыв из искателя, если он там лежит ───────────────

def _snyat_otryv(koren: Path) -> bool:
    """Если предыдущая версия патча (с мнением об отрыве) уже легла —
    вернуть все её файлы из копий, снятых ПЕРЕД ней. Тогда честная
    резинка ляжет заново, уже без отрыва."""
    tronuli = 0
    for imya in ("kandidaty.py", "williams_core.py", "stol.py"):
        f = koren / "Биржа" / imya
        if STARYY not in f.read_text(encoding="utf-8"):
            continue
        kopii = sorted(f.parent.glob(f"{imya}.bak_otryv_*"))
        if not kopii:
            print(f"✗ в {imya} старый патч есть, а копии .bak_otryv_* нет")
            print("  сам ничего не трону — покажи мне вывод")
            return False
        do = kopii[0]
        if STARYY in do.read_text(encoding="utf-8"):
            print(f"✗ в копии {do.name} старый патч уже есть — стою")
            return False
        if SUHO:
            print(f"· {imya} вернулся бы из {do.name} (сухой прогон)")
            continue
        shutil.copy2(do, f)
        py_compile.compile(str(f), doraise=True)
        print(f"✓ {imya}: вернул из {do.name}")
        tronuli += 1
    if not tronuli and not SUHO:
        print("· старого патча нет — возвращать нечего")
    return True


# ── ядро: доля только по свою сторону губ ────────────────────

W_YAKOR = '''    tension_ratio = (distance_now / distance_max) if distance_max > eps else 0.0'''

W_NOV = '''    # REZINKA_CHESTNAYA_V1: доля считается, только пока цена по СВОЮ
    # сторону губ. Ушла на другую (distance_now < 0) — доли нет: пик
    # копится в одну сторону, и «сейчас/пик» давало числа вроде −4.215,
    # которые выглядят как доля, но не значат ничего. Расстояние в
    # пунктах со знаком остаётся — это честный факт.
    if distance_now < 0:
        tension_ratio = None
    elif distance_max > eps:
        tension_ratio = distance_now / distance_max
    else:
        tension_ratio = 0.0'''

W_YAKOR2 = '''    is_peak = distance_now >= distance_max * (1 - 0.02)   # на пике (±2%)'''

W_NOV2 = '''    is_peak = (distance_now > 0
               and distance_now >= distance_max * (1 - 0.02))  # на пике (±2%)'''

W_YAKOR3 = '''        "tension_ratio": round(tension_ratio, 3),'''

W_NOV3 = '''        "tension_ratio": (round(tension_ratio, 3)
                          if tension_ratio is not None else None),
        "za_gubami":     bool(distance_now < 0),   # REZINKA_CHESTNAYA_V1'''

# ── стол: словами, а не знаком минуса ────────────────────────

S_YAKOR = '''        "натяжение": {"сейчас": rb.get("distance_now"),
                      "пик": rb.get("distance_max"),
                      "доля_от_пика": rb.get("tension_ratio")},'''

S_NOV = '''        "натяжение": {"сейчас": rb.get("distance_now"),
                      "пик": rb.get("distance_max"),
                      "доля_от_пика": rb.get("tension_ratio"),
                      # REZINKA_CHESTNAYA_V1: сторона названа прямо
                      "цена_по_другую_сторону_губ": rb.get("za_gubami")},'''

S_YAKOR2 = '''        f"натяжение от губ: {nt.get('сейчас')} п. (пик {nt.get('пик')}, "
        f"доля {nt.get('доля_от_пика')})",'''

S_NOV2 = '''        # REZINKA_CHESTNAYA_V1: словами, а не знаком минуса. Трейдер
        # читал «−229.2 п., доля −1.732» и спотыкался: доля не бывает
        # −1.7. Теперь сторона названа прямо, а доля показывается
        # только когда она есть. Хватает отрыва или нет — видно на
        # кадре, и решает это трейдер, не прибор.
        (lambda _n: (
            f"расстояние до губ: {abs(_n.get('сейчас') or 0):.0f} п. "
            + ("(цена по другую сторону губ)"
               if _n.get('цена_по_другую_сторону_губ')
               else f"(пик {_n.get('пик')}, доля {_n.get('доля_от_пика')})")
        ))(nt),'''


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
    bak = f.with_suffix(f".py.bak_rezinka_{datetime.now():%Y%m%d_%H%M%S}")
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

    if not _snyat_otryv(koren):
        return 1

    if not _pravit(koren / "Биржа" / "williams_core.py",
                   [(W_YAKOR, W_NOV), (W_YAKOR2, W_NOV2),
                    (W_YAKOR3, W_NOV3)], "williams_core.py"):
        return 1
    if not _pravit(koren / "Биржа" / "stol.py",
                   [(S_YAKOR, S_NOV), (S_YAKOR2, S_NOV2)], "stol.py"):
        print("\n⚠️  ядро поправлено, стол нет — верни williams_core.py из")
        print("   свежей .bak_rezinka_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nЧто изменится на столе:")
    print("  было:  натяжение от губ: -229.2 п. (пик 105.7, доля -1.732)")
    print("  стало: расстояние до губ: 229 п. (цена по другую сторону губ)")
    print("         расстояние до губ: 494 п. (пик 908.2, доля 0.543)")
    print("\nПроверить без модели и без денег:")
    print("  py stol_pokazat.py EURUSD H4")
    print("\nИскатель ищет как искал: разворотный бар и структура позади.")
    print("Хватает отрыва или нет — видит трейдер на кадре.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
