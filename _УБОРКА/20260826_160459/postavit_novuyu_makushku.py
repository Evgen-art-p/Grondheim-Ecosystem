# -*- coding: utf-8 -*-
"""
postavit_novuyu_makushku.py · MARKER: NOVAYA_MAKUSHKA_V1

СЛОВО ШЕФА (21.08)
──────────────────
«Не может волна не дожить до отката — это как? Всегда есть импульс,
откат. Если точка-макушка была, а следующий такой же разворотник —
значит НОВАЯ МАКУШКА. Если разворотник в другую — то продолжение.»

ЧТО БЫЛО НЕПРАВИЛЬНО
────────────────────
Замер на живом месте (EURUSD H4, точка 21.11.2025):

    точка     2025.11.21 12:00
    ВОЛНА 1   2025.11.26 08:00   ← макушка отмечена
    точка     2025.11.27 04:00   ← и структура ОБНУЛИЛАСЬ

На следующем баре пришёл ещё один разворотник против точки. Отметка о
макушке уже стояла, и он провалился в блок рождения — родил новую точку
и стёр всю структуру. Откат ждать стало не от чего.

По замеру так терялась половина: до отката доживало 47% волн. Но волна
не может «не дожить» — за импульсом всегда идёт откат. Мы просто рвали
структуру на полпути.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Пока точка жива и макушка отмечена:

    разворотник ПРОТИВ точки  → новая макушка, если экстремум ушёл
                                дальше прежнего; волна 1 ещё тянется,
                                точку не трогаем
    разворотник В СТОРОНУ     → конец отката (KONEC_VOLNY_2_V1)

Дальше прежнего или нет — чистое сравнение двух цен, без порогов.
Ушёл дальше — макушка переезжает. Не ушёл — молчим и ждём: это уже ход
отката, а не новая вершина.

Отсев неистинных баров тот же, что у первого сигнала: читаемая
структура позади. Тот же прибор, третий раз.

Точку по-прежнему убивает только структурный слом — цена закрылась за
её ценой. Тогда всё начинается заново, и это правильно.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ конца волны 2 — патч это проверит.
Запуск: py postavit_novuyu_makushku.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "NOVAYA_MAKUSHKA_V1"
NUZHEN = "KONEC_VOLNY_2_V1"
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


YAKOR = '''        if (zhiva and napr in ("BULL", "BEAR") and storona != napr
                and cena is not None and wf.get("struktura_chitaetsya")
                and not isk.get("konec_volny_1")):'''

NOV = '''        # NOVAYA_MAKUSHKA_V1: макушка уже стоит, а пришёл ещё один
        # разворотник против точки. Слово Шефа: «значит новая макушка».
        # Волна 1 просто тянется дальше — точку рвать нельзя, иначе
        # откат ждать не от чего (так терялась половина: до отката
        # доживало 47% волн).
        # Переезжает макушка только если экстремум ушёл ДАЛЬШЕ прежнего:
        # чистое сравнение двух цен, без порогов. Не ушёл — молчим, это
        # уже ход отката, а не новая вершина.
        if (zhiva and napr in ("BULL", "BEAR") and storona != napr
                and cena is not None and wf.get("struktura_chitaetsya")
                and isk.get("konec_volny_1")
                and not isk.get("konec_volny_2")):
            _bylo = (isk.get("konec_volny_1") or {}).get("цена")
            _dalshe = (_bylo is None
                       or (cena > _bylo if storona == "BULL" else cena < _bylo))
            if _dalshe:
                isk["konec_volny_1"] = {
                    "цена": cena, "бар": bar, "сторона": napr,
                    "структура": wf.get("dlina") or 0,
                    "баров_от_точки": int(isk.get("barov_s_tochki") or 0),
                }
                isk["kray_posle"] = cena
                save_trading_state(t)
                print(f"[ВОЛНА 1] ⛰ {para}: макушка переехала "
                      f"{_bylo} → {cena} · бар {bar}")
                return _zapomnit_otvet({"alive": True, "konec_volny_1": True,
                                        "makushka_pereehala": True,
                                        "direction": storona})
            # не дальше прежней — это ход отката, ничего не трогаем
            return _zapomnit_otvet(proverit_tochku(md, para))

        if (zhiva and napr in ("BULL", "BEAR") and storona != napr
                and cena is not None and wf.get("struktura_chitaetsya")
                and not isk.get("konec_volny_1")):'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "hooks.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in t:
        print("✗ Сперва накати postavit_konec_volny_2.py")
        return 1
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
        return 1

    novyy = t.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_makushka_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ макушка переезжает, структура цела (копия: {bak.name})")
    print("\nВ логе появится:")
    print("  [ВОЛНА 1] ⛰ макушка переехала 1.15959 → 1.16136 · бар ...")
    print("\nСтруктура держится до слома по цене — и откат дожидается.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
