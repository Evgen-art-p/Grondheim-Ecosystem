# -*- coding: utf-8 -*-
"""
magic_ostayotsya_pri_meste.py · MARKER: MAGIC_PRI_MESTE_V2

СЛОВО ШЕФА
──────────
    «Ты магик привязываешь к месту. Нужно, чтобы оно не прилипало к
    жителю: если сменю трейдера на другого — магик остаётся за местом.
    И при создании новых мест-вакансий чтобы это уже применялось.»

ЧТО БЫЛО НЕ ТАК (причина, а не следствие)
─────────────────────────────────────────
Вчера я поправил ДАННЫЕ — проставил магики и починил маски. А причину
не тронул, и она вот:

    `prinyat()` пишет только отметку в паспорт. МАСКУ РАБОТЫ
    (цех, слот, magic, активность) не трогает ВООБЩЕ.
    `uvolit()` — тоже не трогает.

Отсюда всё и вышло: Нину сажали руками — маска заполнилась; Синди и
Веру через Страницу Работы — маска осталась пустой, магика нет. А
уволенный Илья так и остался числиться на A07, где сидит Синди: судья
мог отдать вывод из сделки не тому человеку.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. ЗАВЕЛИ ВАКАНСИЮ — МЕСТО СРАЗУ ПОЛУЧАЕТ МАГИК. Не человек, а
   кресло: у него номер счёта, и он при нём навсегда. Известный слот —
   по схеме (A06→100001, A07→100002, A08→100003), новый — следующий
   свободный, чтобы номера не сталкивались.

2. ПРИНЯЛИ — маска жителя заполняется ИЗ ПОСТА: цех, слот, магик
   места, маска активна. Сел в кресло — работаешь под его номером.

3. УВОЛИЛИ — маска гаснет: место и магик снимаются, маска неактивна.
   Ушёл — номер остался при кресле, а не уехал с человеком.

Итог: пересадил трейдера — магик остался за местом и достался новому.
Ничего руками дописывать больше не придётся.

ПОЧЕМУ ЭТО ВАЖНО, А НЕ КОСМЕТИКА
────────────────────────────────
Судья при закрытии сделки ищет человека ПО МАГИКУ: закрылось →
resolve_by_magic → маска → носитель → его якоря. Магика нет — вывод
складывается и не находит, кому его отдать. Опыт не пишется никуда.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py magic_ostayotsya_pri_meste.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "MAGIC_PRI_MESTE_V2"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "ГОРОД" / "rabota.py").exists() and (p / "main.py").exists()


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


# ── 1. рука маски: одна на приём и увольнение ──
RUKA_MASKI = '''

# ── MAGIC_PRI_MESTE_V2: маска работы = проекция ПОСТА ────────
# Правда о найме живёт в посте. Маска жителя её отражает — и должна
# меняться ровно тогда, когда меняется пост.
#
# Раньше prinyat/uvolit маску НЕ ТРОГАЛИ: Нину сажали руками — маска
# заполнилась, Синди и Веру через Страницу Работы — осталась пустой,
# без магика. А уволенный Илья продолжал числиться на A07, где уже
# сидела Синди: судья мог отдать вывод из сделки не тому человеку.
#
# Магик при этом принадлежит КРЕСЛУ, а не жильцу: пересел — номер
# остался за местом и достался новому.
def _maska_po_postu(imya: str, post: dict | None) -> bool:
    """post=None — гасим маску (уволен). Иначе — заполняем из поста."""
    dom = dom_zhitelya(imya)
    if dom is None:
        return False
    mf = dom / "маски" / "работа" / "mask.json"
    mk = _chitat(mf) or {}
    if post is None:
        mk["Workshop_ID"] = ""
        mk["Turbo_Role"] = ""
        mk["magic"] = None
        mk["_активна"] = False
    else:
        mk["Workshop_ID"] = post.get("цех") or post.get("квартал") or ""
        mk["Turbo_Role"] = post.get("слот") or post.get("название") or ""
        mk["magic"] = post.get("magic")
        # реестр берёт ТОЛЬКО активные маски: неактивная = человека по
        # магику не найдут, и вывод судьи повиснет
        mk["_активна"] = True
    try:
        mf.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return _pisat(mf, mk)


def magic_dlya_slota(slot: str) -> int:
    """Номер счёта для КРЕСЛА. Схема из старого тестера, она уже жила
    в городе: A06→100001, A07→100002, A08→100003. Новый слот получает
    следующий свободный, чтобы номера не сталкивались."""
    izvestnye = {"A06": 100001, "A07": 100002, "A08": 100003}
    s = (slot or "").strip().upper()
    if s in izvestnye:
        return izvestnye[s]
    zanyato = set()
    if POSTY.exists():
        for d in POSTY.iterdir():
            p = _chitat(d / "пост.json") or {}
            m = p.get("magic")
            if isinstance(m, int):
                zanyato.add(m)
    n = 100001
    while n in zanyato:
        n += 1
    return n

'''

# ── 2. вакансия получает магик при заведении ──
ST_ZAVESTI = '''    if d is None:
        d = blank(post_id, polya)
        msg = "должность заведена"'''
NOV_ZAVESTI = '''    if d is None:
        d = blank(post_id, polya)
        # MAGIC_PRI_MESTE_V2: кресло получает номер счёта СРАЗУ, при
        # заведении. Потом его никто не выдаёт вручную и не забывает.
        if not d.get("magic"):
            d["magic"] = magic_dlya_slota(d.get("слот") or "")
        msg = "должность заведена"'''

ST_ZAVESTI2 = '''        for k, v in (polya or {}).items():
            if k in POLYA_BLANKA and v not in (None, "", []) and not d.get(k):
                d[k] = v
        msg = "должность обновлена"'''
NOV_ZAVESTI2 = '''        for k, v in (polya or {}).items():
            if k in POLYA_BLANKA and v not in (None, "", []) and not d.get(k):
                d[k] = v
        if not d.get("magic"):      # MAGIC_PRI_MESTE_V2: старым местам тоже
            d["magic"] = magic_dlya_slota(d.get("слот") or "")
        msg = "должность обновлена"'''

# ── 3. приём и увольнение двигают маску ──
ST_PRINYAT = '''    _otmetka(imya, d)
    return True, f"{imya} принят на «{d.get('название', post_id)}»"'''
NOV_PRINYAT = '''    _otmetka(imya, d)
    # MAGIC_PRI_MESTE_V2: сел в кресло — работаешь под ЕГО номером.
    _maska_po_postu(imya, d)
    return True, f"{imya} принят на «{d.get('название', post_id)}»"'''

ST_UVOLIT = '''    _otmetka(imya, None)
    return True, f"{imya} уволен, место свободно"'''
NOV_UVOLIT = '''    _otmetka(imya, None)
    # MAGIC_PRI_MESTE_V2: ушёл — номер остался при кресле, а не уехал
    # с человеком. Иначе уволенный продолжает числиться на месте, где
    # уже сидит другой.
    _maska_po_postu(imya, None)
    return True, f"{imya} уволен, место свободно"'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    f = koren / "ГОРОД" / "rabota.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0

    pary = [("заведение", ST_ZAVESTI, NOV_ZAVESTI),
            ("обновление", ST_ZAVESTI2, NOV_ZAVESTI2),
            ("приём", ST_PRINYAT, NOV_PRINYAT),
            ("увольнение", ST_UVOLIT, NOV_UVOLIT)]
    beda = [imya for imya, st, _ in pary if t.count(st) != 1]
    if beda:
        print(f"✗ якоря не найдены дословно: {', '.join(beda)}")
        return 1

    novyy = t
    for _, st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy = novyy.rstrip("\n") + "\n" + RUKA_MASKI + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_magic2_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    print(f"✓ магик закреплён за местом (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(f), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь:")
    print("  завёл вакансию   → место сразу получило номер счёта")
    print("  принял человека  → маска заполнилась ИЗ ПОСТА, с магиком")
    print("  уволил           → маска погасла, номер остался при месте")
    print("  посадил другого  → он работает под тем же номером")
    print("\nРуками дописывать больше ничего не надо.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
