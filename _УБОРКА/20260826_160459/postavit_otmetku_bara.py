# -*- coding: utf-8 -*-
"""
postavit_otmetku_bara.py · MARKER: VERDIKT_S_BAROM_V1

БЛОКЕР, найденный на первом же прогоне (20.08)
──────────────────────────────────────────────
В логе прогона, на каждом из трёх мест:

    [ИСПОЛНИТЕЛЬ] ⏳ brut: вердикт без отметки бара — не считаю

Закон `SVEZHEST_V1` у Исполнителя правильный: в дело идёт вердикт
ТОЛЬКО текущего бара. Он спасает от торговли по вчерашнему слову —
в логе 18.08 Совет A07/A08 не звал, а Исполнитель доложил их прошлые
вердикты; там был REJECTED и обошлось, но лежал бы APPROVED с ценой —
поставил бы ордер по позавчерашнему решению.

А мозг трейдера отметку бара в вердикт НЕ КЛАДЁТ. В `_save_verdict_to_table`
девять полей, и ни одного про бар.

Отсюда: ЛЮБОЙ вердикт улетает в мусор. Скажи трейдер APPROVED с ценой
и стопом — Исполнитель всё равно ответит «не считаю». Вход не мог
случиться ни разу, сколько бы всё остальное ни чинили. Круг опыта
крутится вхолостую не потому, что трейдер осторожничает, а потому что
его слово физически не доезжает до руки.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Вердикт начинает нести бар, на котором сказан. Во всех трёх мозгах:

    _save_verdict_to_table(signal)  →  _save_verdict_to_table(signal, md.get("bar_time"))

и внутри — одно новое поле «бар». Имя поля не выдумано: ровно его
Исполнитель и ищет (`v.get("бар") or v.get("bar_time")`).

Больше ничего. Ни логики, ни условий, ни суждений — только доставка.

ПОСЛЕ НАКАТКИ
─────────────
Строка «вердикт без отметки бара» из прогона исчезнет. Если трейдер
скажет REJECTED — Исполнитель просто не найдёт что исполнять, и это
нормально. Если скажет APPROVED — впервые за всё время дойдёт до руки.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_otmetku_bara.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VERDIKT_S_BAROM_V1"
SUHO = "--suho" in sys.argv

# слот → ключ, под которым его вердикт лежит на столе
SLOTY = {"A06": "brut", "A07": "avan", "A08": "cons"}


def _eto_koren(p: Path) -> bool:
    return (p / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
            / "слоты").is_dir()


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


def _pravki(klyuch: str) -> list:
    """Три замены на мозг: подпись, тело, вызов."""
    return [
        # 1. подпись руки — принимает бар
        ("def _save_verdict_to_table(signal: dict):",
         "def _save_verdict_to_table(signal: dict, bar_time=None):"),
        # 2. тело — кладёт бар рядом с вердиктом
        (f'    t.setdefault("{klyuch}", {{}})',
         f'    t.setdefault("{klyuch}", {{}})\n'
         f'    # VERDIKT_S_BAROM_V1: вердикт несёт бар, на котором сказан.\n'
         f'    # Без этого Исполнитель по закону SVEZHEST_V1 не берёт его\n'
         f'    # в дело вовсе — «вердикт без отметки бара, не считаю».\n'
         f'    t["{klyuch}"]["бар"] = str(bar_time or "")'),
        # 3. вызов — передаёт бар
        ("    _save_verdict_to_table(signal)",
         '    _save_verdict_to_table(signal, md.get("bar_time"))'),
    ]


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
    bak = f.with_suffix(f".py.bak_barverdikt_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ {imya}: НЕ компилируется ({e}) — откатил из {bak.name}")
        return False
    print(f"✓ {imya}: вердикт понесёт бар (копия: {bak.name})")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    sloty = koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

    tronuli = 0
    for slot, klyuch in SLOTY.items():
        mozg = sloty / slot / "мозг.py"
        if not mozg.exists():
            print(f"· {slot}: мозга нет — пропускаю (вакансия, не ошибка)")
            continue
        if not _pravit(mozg, _pravki(klyuch), f"{slot}/мозг.py"):
            print(f"\n⚠️  {slot} не поправлен. Остальные тронутые — целы,")
            print("   у каждого рядом своя .bak_barverdikt_*. Покажи мне вывод.")
            return 1
        tronuli += 1

    if SUHO:
        return 0
    print(f"\n✓ мозгов поправлено: {tronuli}")
    print("\nПроверить: прогони историю на два-три места. Строка")
    print("  [ИСПОЛНИТЕЛЬ] ⏳ вердикт без отметки бара — не считаю")
    print("должна исчезнуть. Скажет трейдер REJECTED — Исполнителю просто")
    print("нечего исполнять, это нормально. Скажет APPROVED — впервые")
    print("дойдёт до руки.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
