# -*- coding: utf-8 -*-
"""
postavit_vedenie_po_fraktalam.py · MARKER: VEDENIE_FRAKTALY_V1

ЗАЧЕМ
─────
Вход у нас есть, стоп на входе есть, а ВЕДЕНИЯ не было: позиция стояла
с тем же стопом до конца и закрывалась только по нему или по колоколу.

Слово Шефа: ведём по фракталам.

ИСТОЧНИК, ДОСЛОВНО
──────────────────
«РЫНОЧНЫЙ ФРАКТАЛ», §4.2 «Выход и Стоп-лосс (Trailing Stop)»:

    Правило: Стоп-лосс перемещается на уровень, расположенный на ДВА
    ФРАКТАЛА НАЗАД в противоположном направлении.
    Это позволяет «плыть по течению» и защищает прибыль при развороте.

Ни порогов, ни процентов, ни выдуманных чисел — только фракталы,
которые у нас и так считаются и лежат на столе.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
На каждом закрытом баре, по каждой открытой позиции:

    LONG  → берём два последних НИЖНИХ фрактала, стоп на дальний из
            них (второй назад)
    SHORT → два последних ВЕРХНИХ, стоп на второй назад

Стоп двигается ТОЛЬКО в сторону прибыли. Назад — никогда: это
защита, а не поводок. Фракталов меньше двух — не трогаем, стоит как
стоял.

Ведение включается само, никого не спрашивая, — это не решение о
сделке, а исполнение правила, которое трейдер принял, когда входил.

В журнал каждый перенос пишется строкой:

    [ВЕДЕНИЕ] ⇢ SHORT 1.17416 · стоп 1.17549 → 1.17205 (2 фрактала назад)

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не закрывает позицию сам и не решает, когда выходить. Выход по
правилу (зелёная линия, обратный разворотник, ангуляция) — отдельная
работа: в коде сейчас стоит самодельный «колокол» на дивергенции AO,
которого в источниках нет, и его надо пересобирать, а не достраивать.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_vedenie_po_fraktalam.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VEDENIE_FRAKTALY_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "hooks.py").exists()


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


YAKOR = '''def _vesti_tochku(md: dict, symbol: str = "", timeframe: str = "") -> dict:'''

RUKA = '''# ═══════════════════════════════════════════════════════════
# VEDENIE_FRAKTALY_V1 — стоп на два фрактала назад
# ═══════════════════════════════════════════════════════════
# «РЫНОЧНЫЙ ФРАКТАЛ», §4.2: «Стоп-лосс перемещается на уровень,
# расположенный на два фрактала назад в противоположном направлении.
# Это позволяет плыть по течению и защищает прибыль при развороте.»
#
# Ни порогов, ни процентов. Только фракталы, которые и так считаются.
# Стоп ходит ТОЛЬКО в сторону прибыли — назад никогда.

def _vesti_stopy(md: dict) -> int:
    """Подтянуть стопы открытых позиций. Возвращает, сколько сдвинуто.

    Это не решение о сделке, а исполнение правила, которое трейдер
    принял, когда входил. Потому и делается кодом, без вопросов.
    """
    try:
        fr = (md or {}).get("fractals") or {}
        verh = list(fr.get("all_up") or [])
        niz = list(fr.get("all_down") or [])
        _bar_sym = str((md or {}).get("symbol", "") or "").strip().upper()

        t = load_trading_state()
        sdvinuto = 0
        for pos in (t.get("positions") or []):
            if pos.get("status") not in ("OPEN", "WATCHING"):
                continue
            _psym = (pos.get("symbol") or "").strip().upper()
            if _psym and _bar_sym and _psym != _bar_sym:
                continue          # чужой рынок — не наше дело
            napr = (pos.get("direction") or "").upper()
            stop = pos.get("stop")
            if stop is None:
                continue
            # два фрактала назад в ПРОТИВОПОЛОЖНОМ направлении
            if napr == "LONG":
                if len(niz) < 2:
                    continue
                novyy = niz[-2].get("price")
                dvigat = novyy is not None and novyy > stop
            elif napr == "SHORT":
                if len(verh) < 2:
                    continue
                novyy = verh[-2].get("price")
                dvigat = novyy is not None and novyy < stop
            else:
                continue
            if not dvigat:
                continue          # назад стоп не ходит
            pos["stop"] = novyy
            pos["stop_vedyot"] = "два фрактала назад"
            sdvinuto += 1
            print(f"[ВЕДЕНИЕ] ⇢ {napr} {pos.get('entry')} · "
                  f"стоп {stop} → {novyy} (2 фрактала назад)")
        if sdvinuto:
            save_trading_state(t)
        return sdvinuto
    except Exception as e:
        print(f"[ВЕДЕНИЕ] стопы не подтянулись ({e}) — позиции целы")
        return 0


'''

# зовём ведение на каждом баре, ДО закрытия позиций
YAKOR2 = '''    itog["позиций"] = len(stalo)'''

NOV2 = '''    itog["позиций"] = len(stalo)

    # VEDENIE_FRAKTALY_V1: подтянуть стопы по фракталам. После
    # закрытия — чтобы бар судил позицию тем стопом, с которым она в
    # этот бар вошла, а не подтянутым задним числом.
    _vesti_stopy(md)'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "hooks.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    for yakor in (YAKOR, YAKOR2):
        if t.count(yakor) != 1:
            print(f"✗ якорь найден {t.count(yakor)} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return 1

    novyy = t.replace(YAKOR, RUKA + YAKOR, 1).replace(YAKOR2, NOV2, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_vedenie_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ позиция ведётся по фракталам (копия: {bak.name})")
    print("\nВ логе при каждом переносе:")
    print("  [ВЕДЕНИЕ] ⇢ SHORT 1.17416 · стоп 1.17549 → 1.17205 "
          "(2 фрактала назад)")
    print("\nСтоп ходит только в сторону прибыли. Фракталов меньше двух —")
    print("стоит как стоял. Выход по правилу — отдельная работа.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
