# -*- coding: utf-8 -*-
# POSTAVIT_METKI_PROVALOV_AO_V1
"""
ПАТЧ: на полосе AO метятся САМИ ПРОВАЛЫ И ГОРБЫ, а не игра соседей.

Запускать из КОРНЯ РЕПО:
    python postavit_metki_provalov_ao.py

СЛОВО ШЕФА (15.09)
    «Нужно, чтобы именно провалы сигналил — именно дивер. А красные и
    зелёные это по одному. Нужно сравнивать именно высоту-глубину.»

ЧТО БЫЛО НЕ ТАК
    Разворотный бар трейдеру дают готовым — жёлтая стрелка. Приседающий
    дают готовым — красная точка. А провалы AO не помечены ничем, и
    единственное, что кричит с полосы, — цвет столбика: зелёный, если
    он выше ПРЕДЫДУЩЕГО, красный, если ниже. Цвет — про соседей,
    бар к бару. Дивер живёт в другом месте: в глубине двух провалов.

    Отсюда прямая ошибка в прогоне 09.01: «AO поднимается от более
    глубокой ямы». Столбики внутри провала зеленели — провал ещё рылся
    вниз, но медленнее. Глаз прочитал цвет вместо глубины и вошёл
    против дивера. Стоп.

ЧТО МЕНЯЕТ (Биржа/grafik.py)
    На дне каждого провала и на вершине каждого горба ставится метка —
    ромб на самом крайнем столбике группы. Группа — подряд идущие
    столбики по одну сторону нуля.

    Метка — ФАКТ, а не совет. Она не говорит «тут дивер» и ничего не
    соединяет линиями: соединять и сравнивать — дело глаза. Кадр лишь
    перестал прятать то, что надо сравнивать.

    Цвет столбиков НЕ ТРОНУТ: он привычен по терминалу, и ломать
    привычку глаза дороже, чем добавить метку.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_metki_ao, ast.parse перед записью.
    Рисует своими средствами matplotlib, ничего нового не ставится.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# METKI_PROVALOV_AO_V1"


def _nayti_grafik():
    kand = [p for p in _KOREN.rglob("grafik.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл grafik.py. Запускай из корня репозитория.")
        return None
    if len(kand) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kand, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            return kand[int(input("Который? номер: ").strip()) - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kand[0]


# 1. цвет метки ─────────────────────────────────────────────
STARO_1 = '''C_AO_UP = "#3ddc6b"
C_AO_DOWN = "#ff5c5c"'''

NOVO_1 = '''C_AO_UP = "#3ddc6b"
C_AO_DOWN = "#ff5c5c"
# METKI_PROVALOV_AO_V1: метка на дне провала и на вершине горба.
# Своего цвета, не из палитры столбиков — чтобы не путалась с ними и
# читалась как отдельная вещь, а не как ещё один оттенок силы.
C_AO_METKA = "#ffd24a"'''


# 2. сами метки ─────────────────────────────────────────────
STARO_2 = '''        axo.bar(xs, ys, color=cveta, width=0.7, zorder=3)'''

NOVO_2 = '''        axo.bar(xs, ys, color=cveta, width=0.7, zorder=3)

        # METKI_PROVALOV_AO_V1 (слово Шефа 15.09): метим САМИ ПРОВАЛЫ
        # И ГОРБЫ. Цвет столбика говорит только про соседа — выше он
        # предыдущего или ниже. Дивер живёт не там: он в ГЛУБИНЕ двух
        # провалов, которые надо сравнить между собой. Раз сравнивать
        # нужно их — значит их и видно.
        #
        # Группа — подряд идущие столбики по одну сторону нуля.
        # Крайний в группе (самый глубокий у провала, самый высокий у
        # горба) получает ромб.
        #
        # Это ФАКТ, не совет: ничего не соединяем и не подписываем
        # «дивер». Сравнить две метки — дело глаза, не кадра.
        _gruppy, _tek = [], []
        _znak_pred = 0
        for _k, _v in enumerate(ys):
            _zn = 1 if _v > 0 else (-1 if _v < 0 else 0)
            if _zn == 0:
                if _tek:
                    _gruppy.append((_znak_pred, _tek))
                    _tek = []
                _znak_pred = 0
                continue
            if _zn != _znak_pred and _tek:
                _gruppy.append((_znak_pred, _tek))
                _tek = []
            _znak_pred = _zn
            _tek.append(_k)
        if _tek:
            _gruppy.append((_znak_pred, _tek))

        _mx, _my = [], []
        for _zn, _idx in _gruppy:
            # одиночный столбик экстремумом не считаем: это не провал,
            # а рябь у нуля — метить нечего
            if len(_idx) < 2:
                continue
            _kray = (min(_idx, key=lambda j: ys[j]) if _zn < 0
                     else max(_idx, key=lambda j: ys[j]))
            _mx.append(xs[_kray])
            _my.append(ys[_kray])
        if _mx:
            axo.scatter(_mx, _my, marker="D", s=46,
                        facecolors=C_AO_METKA, edgecolors=C_FON,
                        linewidths=1.1, zorder=5)'''


ZAMENY = [
    ("цвет метки", STARO_1, NOVO_1),
    ("метки провалов и горбов", STARO_2, NOVO_2),
]


def main():
    print("=" * 58)
    print("МЕТКИ ПРОВАЛОВ И ГОРБОВ AO")
    print("=" * 58)

    fajl = _nayti_grafik()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return

    print("\n--- ЗАМЕНЫ ---")
    ne = []
    for imya, staro, _n in ZAMENY:
        c = tekst.count(staro)
        print(f"  {'✓' if c == 1 else '⚠ ' + str(c)}  {imya}")
        if c != 1:
            ne.append(imya)
    if ne:
        print(f"\n⚠ не сошлось: {', '.join(ne)} — ничего не тронул.")
        return

    novyy = tekst
    for _i, staro, novo in ZAMENY:
        novyy = novyy.replace(staro, novo, 1)
    novyy = novyy.rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_metki_ao")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Что смотреть глазами:")
    print("  Открой любой кадр — на полосе AO жёлтые ромбы на дне")
    print("  каждого провала и на вершине каждого горба.")
    print("  Рябь у нуля (одиночные столбики) не метится.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_METKI_PROVALOV_AO_V1 - marker
