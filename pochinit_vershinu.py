# -*- coding: utf-8 -*-
# MARKER: VERSHINA_NE_NIZHE_KRAYA_V1
"""
ВЕРШИНА НЕ МОЖЕТ БЫТЬ НИЖЕ ТОГО, КУДА ЦЕНА ПОТОМ ДОШЛА.

ЧТО БЫЛО СЛОМАНО
────────────────
Конец волны 1 счётчик отмечает разворотным баром в обратную сторону —
и это правильно, так и в каноне. Но дальше он эту отметку проверял
ТОЛЬКО другим разворотным баром: пришёл ещё один против точки и ушёл
дальше — вершина переезжает; не пришёл — вершина стоит, где стояла.

А если цена просто идёт дальше вверх и обратных разворотников не даёт,
вершина остаётся внизу, хотя рынок давно её прошёл. Глазом это видно
за секунду, у кода такой проверки не было.

Живой пример (EURUSD H4, 27.08):
    точка ноль   BULL @ 1.13533
    вершина      1.14751     ← отметил счётчик
    край после точки 1.15587 ← сколько на самом деле прошла цена
    цена сейчас  1.16564

Вершина ниже и края, и текущей цены. От неё считалось всё остальное,
и потому на столе стояло «ГЛУБИНА ОТКАТА: 148.9%» — отката, которого
нет, потому что цена по другую сторону.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Добавляет одну проверку, на каждом баре, пока точка жива и откат ещё
не отмечен:

    вершина ушла ниже КРАЯ ПОСЛЕ ТОЧКИ → вершина переезжает на край

Край после точки — не новое число. Код и так копит его каждый бар
(«та самая макушка волны 1», как записано в самом файле): для BULL это
самый высокий high с рождения точки, для BEAR — самый низкий low.
Просто до сих пор его никто не сверял с отмеченной вершиной.

Ни порогов, ни допусков, ни новых источников данных. Сравнение двух
чисел, которые уже лежат рядом.

Переезд вершины НЕ значит «волна кончилась заново» — это тот же
KRAY_VOLNY_V1: волна как раз продолжается. Событий трейдеру не
добавляется, лишних побудок нет.

ПЛЮС РАЗОВАЯ ПОЧИНКА УЖЕ ЗАПИСАННОГО
────────────────────────────────────
Правка кода works с этого бара и дальше. Но в сохранённой памяти уже
лежат кривые вершины — их скрипт чинит сразу, тем же правилом, чтобы
результат было видно, не гоняя прогон. Показывает, что подвинул.

Идемпотентен. .bak рядом. Пути ищет сам.

После накатки:
    py stol.py EURUSD H4      (из папки Биржа)
"""
import ast
import json
import shutil
import sys
from pathlib import Path

MARKER = "VERSHINA_NE_NIZHE_KRAYA_V1"


# ─────────────────────────────────────────────────────────────
def _nayti_koren() -> Path:
    """Корень города — там, где лежит Биржа/hooks.py."""
    def eto_koren(p: Path) -> bool:
        try:
            return (p / "Биржа" / "hooks.py").exists()
        except OSError:
            return False

    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd().resolve(), *zdes.parents):
        if eto_koren(kand):
            return kand

    nashli = []
    for baza in (zdes, zdes.parent, Path.cwd().resolve()):
        try:
            for d in baza.iterdir():
                if d.is_dir() and eto_koren(d) and d not in nashli:
                    nashli.append(d)
        except OSError:
            pass
    if len(nashli) == 1:
        return nashli[0]
    if len(nashli) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(nashli, 1):
            print(f"  {i}. {d}")
        n = (input("который? номер: ").strip() or "1")
        return nashli[int(n) - 1]
    print("Не нашёл корень города (папку с Биржа/hooks.py).")
    s = input("Перетащи сюда папку репозитория и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if eto_koren(p):
        return p
    raise SystemExit("Это не корень репо — там нет Биржа/hooks.py")


# ── 1. ПРАВКА КОДА ────────────────────────────────────────────
YAKOR = '''            return otvet
        zhiva = bool(isk.get("alive"))
        storona = isk.get("trend_direction")
'''

NOVOE = '''            return otvet
        zhiva = bool(isk.get("alive"))
        storona = isk.get("trend_direction")

        # VERSHINA_NE_NIZHE_KRAYA_V1: вершина не может быть НИЖЕ того,
        # куда цена потом дошла.
        #
        # Конец волны 1 ставит разворотный бар — так в каноне, это не
        # трогаем. Но проверялась эта отметка только ДРУГИМ разворотным
        # баром (NOVAYA_MAKUSHKA_V1). Если цена идёт дальше и обратных
        # разворотников не даёт, вершина остаётся внизу, хотя рынок её
        # давно прошёл. Глазом это видно сразу, у кода проверки не было.
        #
        # Край после точки код и так копит каждый бар — самый дальний
        # экстремум с рождения точки, «та самая макушка волны 1». Здесь
        # просто сверяем два числа, которые уже лежат рядом. Ни порогов,
        # ни допусков, ни новых данных.
        #
        # Переезд ≠ «волна кончилась заново» (KRAY_VOLNY_V1): волна как
        # раз продолжается. Событий трейдеру не добавляем, не будим.
        if (zhiva and isk.get("konec_volny_1")
                and not isk.get("konec_volny_2")):
            _kv = isk.get("konec_volny_1") or {}
            _vershina = _kv.get("цена")
            _kray = isk.get("kray_posle")
            if _vershina is not None and _kray is not None:
                try:
                    _dalshe = (_kray > _vershina if storona == "BULL"
                               else _kray < _vershina)
                except TypeError:
                    _dalshe = False
                if _dalshe:
                    _kv["цена"] = _kray
                    _kv["бар"] = bar
                    _kv["баров_от_точки"] = int(isk.get("barov_s_tochki") or 0)
                    _kv["сдвинулась_ценой"] = True
                    isk["konec_volny_1"] = _kv
                    save_trading_state(t)
                    _slovo = "вершина" if storona == "BULL" else "дно"
                    print(f"[ВОЛНА 1] ↗ {para}: {_slovo} подтянулась "
                          f"{_vershina} → {_kray} (цена ушла дальше)")
'''


def pravka_koda(koren: Path) -> None:
    p = koren / "Биржа" / "hooks.py"
    text = p.read_text(encoding="utf-8")
    if MARKER in text:
        print("  . hooks.py: уже накачен, пропускаю")
        return
    if text.count(YAKOR) != 1:
        raise SystemExit(
            f"  X hooks.py: якорь не найден или не один "
            f"({text.count(YAKOR)}). Файл НЕ ТРОНУТ.")
    novyy = text.replace(YAKOR, NOVOE)
    novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
    ast.parse(novyy)
    shutil.copy2(p, p.with_suffix(".py.bak"))
    p.write_text(novyy, encoding="utf-8")
    print("  + hooks.py: проверка вершины поставлена (.bak рядом)")


# ── 2. ПОЧИНКА УЖЕ ЗАПИСАННОГО ────────────────────────────────
def pochinit_pamyat(koren: Path) -> None:
    """Тем же правилом чиним вершины, уже лежащие в памяти города."""
    fayly = sorted(koren.rglob("trading_state.json"))
    if not fayly:
        print("  . памяти на диске не нашёл — починю следующий прогон сам")
        return

    vsego = 0
    for f in fayly:
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  . {f.name}: не прочитан ({e}) — пропускаю")
            continue

        tronuli = []
        tochki = (t.get("точки") or {})
        for para, isk in tochki.items():
            if not isinstance(isk, dict) or not isk.get("alive"):
                continue
            kv = isk.get("konec_volny_1")
            if not isinstance(kv, dict) or isk.get("konec_volny_2"):
                continue
            vershina, kray = kv.get("цена"), isk.get("kray_posle")
            storona = isk.get("trend_direction")
            if vershina is None or kray is None:
                continue
            try:
                dalshe = (kray > vershina if storona == "BULL"
                          else kray < vershina)
            except TypeError:
                continue
            if not dalshe:
                continue
            kv["цена"] = kray
            kv["сдвинулась_ценой"] = True
            isk["konec_volny_1"] = kv
            tronuli.append((para, storona, vershina, kray))

        if tronuli:
            shutil.copy2(f, f.with_suffix(".json.bak"))
            f.write_text(json.dumps(t, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            for para, storona, bylo, stalo in tronuli:
                slovo = "вершина" if storona == "BULL" else "дно"
                print(f"  + {para}: {slovo} {bylo} → {stalo}")
            vsego += len(tronuli)

    if not vsego:
        print("  . в памяти кривых вершин нет — чинить нечего")


def main():
    koren = _nayti_koren()
    print(f"\nГород: {koren}\n")
    pravka_koda(koren)
    pochinit_pamyat(koren)
    print("\nГотово. Посмотреть, что стало:")
    print("    py stol.py EURUSD H4        (из папки Биржа)")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
