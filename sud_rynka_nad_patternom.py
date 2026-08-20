# -*- coding: utf-8 -*-
"""
sud_rynka_nad_patternom.py · MARKER: SUD_PATTERNA_V1

ГДЕ ОБРЫВ
─────────
Круг опыта заработал: сделка закрылась → судья рассудил → нашёл
человека по номеру места → вывод лёг ему в МАЯКИ черновиком:

    [МОСТ] 📝 черновик → Нина: «Минус -1.0R: вошёл LONG против
           компаса. Против ветра — редкая ставка, не хлеб» (раз: 1/3)

И там остался. Вторую половину суда — `dvizhok.verdikt_rynka` — не
зовёт НИКТО. А она и решает судьбу черновика:

    набрал подтверждений  → встаёт МЕТКОЙ, нажитым знанием
    набрал опровержений   → ГАСНЕТ в архив, честно
    метку рынок опроверг  → метка ПАДАЕТ обратно в черновики

Без неё маяки копятся вечно и в знание не переходят. «Знание твердеет
от СУДЬИ, а не от повторения» — а судья молчал.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Соединяет две половины. Черновик ложится с ключом-паттерном
(`_klyuch_trader`: «трейдер_минус_против_ветра» и прочие) — по ЭТОМУ
ЖЕ ключу рынок и судит:

    сделка в плюс  → паттерну засчитывается подтверждение
    сделка в минус → опровержение

Ключ один и тот же, придумывать нечего: он уже проставляется при
записи вывода.

ЧТО СУДИТСЯ, А ЧТО НЕТ
──────────────────────
Судится ПАТТЕРН РАБОТЫ — то, как человек входит: против ветра, по
системе, на удаче. Именно это должно твердеть или гаснуть от рынка.

Рутинная сделка (та, что не дала вывода) паттерн НЕ судит: судить
нечего, у неё нет ключа. Заряд она качает, как и качала.

ПРО ЧЕСТНОСТЬ
─────────────
Судья не выдумывает исходов: он берёт факт закрытия — плюс или минус —
и засчитывает его паттерну. Ни оценок, ни «стоило/не стоило». Ключа
нигде нет — честно молчит, а не создаёт задним числом.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py sud_rynka_nad_patternom.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "SUD_PATTERNA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "nositel.py").exists()
            and (p / "жители" / "dvizhok.py").exists())


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


ST = '''    if res.get("тип") == "черновик":
        print(f"[МОСТ] 📝 черновик → {n['имя']}: «{vyvod[:60]}...» "
              f"(раз: {res.get('раз')}/3)")
    elif res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']}: «{vyvod}» "
              f"(якорей: {res.get('якорей')})")
    return res'''

NOV = '''    if res.get("тип") == "черновик":
        print(f"[МОСТ] 📝 черновик → {n['имя']}: «{vyvod[:60]}...» "
              f"(раз: {res.get('раз')}/3)")
    elif res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']}: «{vyvod}» "
              f"(якорей: {res.get('якорей')})")

    # ── SUD_PATTERNA_V1: РЫНОК СУДИТ ПАТТЕРН ────────────────────
    # Вторую половину суда не звал НИКТО: черновик ложился в маяки и
    # оставался там навсегда. А она и решает его судьбу —
    #     подтверждения → встаёт МЕТКОЙ (нажитое знание)
    #     опровержения  → ГАСНЕТ в архив, честно
    #     метку опровергли → падает обратно в черновики
    # «Знание твердеет от СУДЬИ, а не от повторения» — а судья молчал.
    #
    # Ключ тот же, что при записи вывода (_klyuch_trader): придумывать
    # нечего. Судим ФАКТ закрытия — плюс или минус, — без оценок.
    try:
        if pnl_r is not None:
            _sud = d.verdikt_rynka(_klyuch_trader(vyvod),
                                   plus=(float(pnl_r) > 0),
                                   fakt=vyvod[:200])
            _ishod = _sud.get("исход") or _sud.get("причина") or ""
            if _sud.get("учтено"):
                print(f"[СУД] ⚖ {n['имя']} · {_klyuch_trader(vyvod)}: "
                      f"{_ishod} (за {_sud.get('за', 0)} / "
                      f"против {_sud.get('против', 0)})")
            elif _ishod:
                print(f"[СУД] · {n['имя']}: {_ishod}")
    except AttributeError:
        print("[СУД] ⚠️  в dvizhok нет verdikt_rynka — паттерн не судится")
    except Exception as _e:
        print(f"[СУД] ⚠️  паттерн не рассужен ({_e}) — вывод записан, цикл цел")

    return res'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    f = koren / "Биржа" / "nositel.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if t.count(ST) != 1:
        print(f"✗ якорь найден {t.count(ST)} раз — жду ровно один")
        return 1

    novyy = t.replace(ST, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_sud_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    print(f"✓ рынок судит паттерн (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(f), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь после каждой значимой сделки в консоли будет:")
    print("  [СУД] ⚖ Нина · трейдер_минус_против_ветра:")
    print("        маяк стал меткой (за 3 / против 0)")
    print("\nЧерновик, который рынок подтвердил трижды, становится")
    print("нажитым знанием. Который опроверг — честно гаснет.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
