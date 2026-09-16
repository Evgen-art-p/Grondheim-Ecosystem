# -*- coding: utf-8 -*-
# POSTAVIT_METKI_PROVALOV_AO_V2
"""
ПАТЧ: метки провалов AO — переделка. Только значимые, и их видно.

Запускать из КОРНЯ РЕПО (после первого патча с ромбами):
    python postavit_metki_provalov_ao_v2.py

ЧТО БЫЛО КРИВО В ПЕРВОЙ ВЕРСИИ
    1. Метил всё подряд. Группой считался любой набор столбиков по
       одну сторону нуля — а AO часто пересекает ноль, группы дробятся
       на мелочь, и метки лезли на рябь вместо настоящих провалов.
    2. Метка сидела ровно на конце столбика и терялась в нём: мелкая,
       тёплого цвета, на фоне зелёного и красного — не видно.

ЧТО ДЕЛАЕТ ТЕПЕРЬ
    · Метит только ЗНАЧИМЫЕ провалы и горбы — те, что глубже пятой
      части самого большого на кадре. Рябь у нуля не метится: её и
      глаз провалом не считает.
    · Метка стоит ПОД дном провала и НАД вершиной горба, а не на
      столбике — сразу видно, что это отдельная вещь.
    · Крупнее, ярче, с тёмной обводкой.

ЧЕГО ПО-ПРЕЖНЕМУ НЕ ДЕЛАЕТ
    Ничего не соединяет линиями и не подписывает словом «дивер».
    Метка — факт, как жёлтая стрелка у разворотного бара. Сравнить
    две метки и решить, что это значит, — дело глаза.

    И главное, ради чего она вообще нужна: трейдер смотрит на правый
    край — там и цена, и последний бар, и цвет столбика. Дивер живёт
    не там: он в отношении нынешнего провала к ПРЕЖНЕМУ, который
    остался позади. Метка на старом провале — единственное на кадре,
    что показывает не на край, а назад.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_metki_ao2, ast.parse перед записью.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# METKI_PROVALOV_AO_V2"
NUZHEN = "METKI_PROVALOV_AO_V1"


def _nayti():
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


STARO = '''        _mx, _my = [], []
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

NOVO = '''        # METKI_PROVALOV_AO_V2: метим только ЗНАЧИМЫЕ провалы и горбы.
        # В первой версии группой считался любой набор столбиков по
        # одну сторону нуля — а AO часто пересекает ноль, группы
        # дробятся, и метки лезли на рябь вместо настоящих провалов.
        _predel = max((abs(v) for v in ys), default=0.0)
        _porog = _predel * 0.20          # мельче пятой части — не провал
        _razmah = (max(ys) - min(ys)) if ys else 0.0
        _otstup = _razmah * 0.07         # метка стоит В СТОРОНЕ от столбика

        _mx, _my = [], []
        for _zn, _idx in _gruppy:
            if len(_idx) < 2:
                continue
            _kray = (min(_idx, key=lambda j: ys[j]) if _zn < 0
                     else max(_idx, key=lambda j: ys[j]))
            if abs(ys[_kray]) < _porog:
                continue
            _mx.append(xs[_kray])
            # под дном провала и над вершиной горба — чтобы метка не
            # тонула в столбике и читалась как отдельная вещь
            _my.append(ys[_kray] - _otstup if _zn < 0
                       else ys[_kray] + _otstup)
        if _mx:
            axo.scatter(_mx, _my, marker="D", s=130,
                        facecolors=C_AO_METKA, edgecolors="#ffffff",
                        linewidths=1.4, zorder=6)
            # запас снизу и сверху, чтобы метки не срезало краем полосы
            if _razmah:
                axo.set_ylim(min(ys) - _otstup * 2.2,
                             max(ys) + _otstup * 2.2)'''


def main():
    print("=" * 58)
    print("МЕТКИ ПРОВАЛОВ AO — переделка")
    print("=" * 58)

    fajl = _nayti()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ переделка уже стоит — ничего не делаю.")
        return
    if NUZHEN not in tekst:
        print("\n⚠ сперва нужен postavit_metki_provalov_ao.py.")
        print("  Ничего не тронул.")
        return

    n = tekst.count(STARO)
    print("\n--- ЗАМЕНА ---")
    print(f"  {'✓' if n == 1 else '⚠ ' + str(n)}  отбор и вид меток")
    if n != 1:
        print("\n⚠ не сошлось — ничего не тронул.")
        return

    novyy = tekst.replace(STARO, NOVO, 1).rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_metki_ao2")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город и посмотри кадр:")
    print("  Ромбы должны стоять ПОД дном крупных провалов")
    print("  и НАД вершинами горбов — крупно, с белой окантовкой.")
    print("  На мелкой ряби у нуля меток быть не должно.")
    print("  Если всё ещё криво — пришли кадр, переделаю ещё раз.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_METKI_PROVALOV_AO_V2 - marker
