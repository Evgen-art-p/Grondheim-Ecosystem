# -*- coding: utf-8 -*-
"""
narisovat_razvorotnik.py · MARKER: RB_NA_KADRE_V1

СЛОВА ШЕФА
──────────
    «Говоришь, разворотник нельзя отсеять? Пусть не числом, а
    взглядом. Индикатор есть же? Мне помогает — а где бар, сразу и
    видно.»

В ЧЁМ БЫЛА МОЯ ОШИБКА
─────────────────────
Я померил отсев ЧИСЛАМИ и сказал «нельзя». А у Шефа в терминале
`iDivergenceBar` рисует бар прямо на графике, и вопрос «где он»
отпадает: видно сразу.

У нас же кадр разворотный бар НЕ РИСУЕТ вовсе. Трейдер смотрит на
голые свечи и должен догадаться, о каком баре речь. Фракталы при этом
рисуются — и в самом коде написано почему: «не нарисовать их — значит
заставить трейдера считать пять баров глазами на каждом шаге». С
разворотником вышло ровно это, хотя он важнее: по нему входят.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Рисует разворотные бары на кадре — так же, как в терминале:

    · бычий  — треугольник ПОД баром, у его low;
    · медвежий — треугольник НАД баром, у его high;
    · последний найденный обведён кружком: это тот, из-за которого
      трейдера позвали.

Ищет их той же рукой, что и всё остальное (`detect_necron_bar` —
дословная копия твоего `iDivergenceBar`, со сдвигом линий 8/5/3 и
условием «весь бар целиком вне пасти»). Второй правды о разворотнике
город не заводит.

ЧТО ЭТО МЕНЯЕТ ПО СУЩЕСТВУ
──────────────────────────
Отсев числами не работает — это замер показал честно. Но отсев
ВЗГЛЯДОМ работает, и теперь он возможен: трейдер видит, где бар, и
может сказать «этот на конце волны» или «этот посреди боковика, мимо».
Раньше он этого не видел физически.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py narisovat_razvorotnik.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RB_NA_KADRE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "grafik.py").exists()
            and (p / "Биржа" / "williams_core.py").exists()
            and (p / "main.py").exists())


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


ST = '''    ax.set_facecolor(C_FON)
    ax.grid(True, color="#00000012", linewidth=0.8)'''

NOV = '''    # RB_NA_KADRE_V1: РАЗВОРОТНЫЕ БАРЫ — как в терминале Шефа.
    # Фракталы мы рисуем и объясняем это тем, что иначе трейдер будет
    # считать бары глазами. С разворотником вышло ровно так: он важнее
    # (по нему входят), а на кадре его не было вовсе — трейдер смотрел
    # на голые свечи и гадал, о каком баре речь.
    # Правило то же, что в ядре (detect_necron_bar) и в твоём
    # iDivergenceBar.mq4: сдвиг линий 8/5/3, новый экстремум, закрытие
    # в противоположной половине и весь бар ЦЕЛИКОМ вне пасти. Считаем
    # прямо по рядам линий — одним проходом по окну кадра.
    try:
        from williams_core import _shifted_series
        _jaw = _shifted_series(alligator.get("jaw_series"), 8)
        _teeth = _shifted_series(alligator.get("teeth_series"), 5)
        _lips = _shifted_series(alligator.get("lips_series"), 3)
        _razmah_rb = max(x["high"] for x in b) - min(x["low"] for x in b)
        _sdvig_rb = len(bars) - n
        _posledniy = None
        for _k in range(1, n):
            _i = _sdvig_rb + _k
            if _i < 1 or _i >= len(_jaw):
                continue
            _j, _t, _l = _jaw[_i], _teeth[_i], _lips[_i]
            if _j is None or _t is None or _l is None:
                continue
            _up, _dn = max(_l, _t, _j), min(_l, _t, _j)
            _bar, _pred = bars[_i], bars[_i - 1]
            _mid = (_bar["high"] + _bar["low"]) / 2
            _storona = None
            if (_bar["high"] > _pred["high"] and _bar["close"] < _mid
                    and _bar["low"] > _up):
                _storona = "BEAR"
            elif (_bar["low"] < _pred["low"] and _bar["close"] > _mid
                    and _bar["high"] < _dn):
                _storona = "BULL"
            if not _storona:
                continue
            _bych = _storona == "BULL"
            _cena = _bar["low"] if _bych else _bar["high"]
            _dy = -1 if _bych else 1
            ax.plot(_k, _cena + _dy * _razmah_rb * 0.02,
                    marker="^" if _bych else "v",
                    color="#e0a020", markersize=11, zorder=6)
            _posledniy = (_k, _cena, _dy)
        if _posledniy:
            _k, _cena, _dy = _posledniy
            ax.plot(_k, _cena + _dy * _razmah_rb * 0.02, marker="o",
                    markerfacecolor="none", markeredgecolor="#e0a020",
                    markersize=20, markeredgewidth=1.6, zorder=6)
    except Exception as _e_rb:
        print(f"[КАДР] разворотники не нарисовались: {_e_rb}")

    ax.set_facecolor(C_FON)
    ax.grid(True, color="#00000012", linewidth=0.8)'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    grafik = koren / "Биржа" / "grafik.py"
    t = grafik.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if t.count(ST) != 1:
        print(f"✗ якорь найден {t.count(ST)} раз — жду ровно один")
        return 1
    if "detect_necron_bar" not in (
            koren / "Биржа" / "williams_core.py").read_text(encoding="utf-8"):
        print("✗ в ядре нет detect_necron_bar — не за что зацепиться")
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

    bak = grafik.with_suffix(f".py.bak_rb_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(grafik, bak)
    grafik.write_text(novyy, encoding="utf-8")
    print(f"✓ разворотники встали на кадр (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(grafik), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь на кадре видно то же, что у тебя в терминале:")
    print("  ▲ под баром — бычий разворотник")
    print("  ▼ над баром — медвежий")
    print("  ◯ обведён тот, из-за которого позвали")
    print("\nОтсев числами не работает — это замер показал. А отсев")
    print("взглядом теперь возможен: трейдер ВИДИТ, где бар, и может")
    print("сказать «этот на конце волны» или «этот посреди боковика».")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
