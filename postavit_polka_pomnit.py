# -*- coding: utf-8 -*-
# POSTAVIT_POLKA_POMNIT_V1
"""
ПАТЧ: полка помнит, что раскрыто.

Запускать из КОРНЯ РЕПО:
    python postavit_polka_pomnit.py

ЧТО БЫЛО НЕ ТАК
    Раскрываешь папку инструмента — город идёт смотреть этажи, находит
    их (в логе: «📂 USDCNH: этажей 13») и ПЕРЕРИСОВЫВАЕТ полку.
    А при перерисовке папка открывается только если внутри активный
    инструмент. Активный не менялся — значит папка схлопывается
    обратно ровно в тот миг, когда в ней наконец появилось
    содержимое.

    Снаружи выглядит так, будто этажи не открываются вовсе. На деле
    они открылись и тут же закрылись.

ЧТО ДЕЛАЕТ
    Полка запоминает, какие папки ты раскрыл, и после перерисовки
    возвращает их открытыми. Свернул руками — забывает.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_polka_pomnit, ast.parse перед записью.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# POLKA_POMNIT_V1"


def _nayti():
    kand = [p for p in _KOREN.rglob("ui_torg.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл ui_torg.py. Запускай из корня репозитория.")
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


# 1. при рисовании — открыть то, что помним ─────────────────
STARO_1 = '''                with ui.expansion(
                    _podpis,
                    value=has_active,'''

NOVO_1 = '''                # POLKA_POMNIT_V1: раскрытые папки помним. Разведка
                # этажей перерисовывает полку, и папка закрывалась
                # ровно тогда, когда в ней появлялось содержимое.
                _pomnim = state.setdefault("раскрыто", set())
                with ui.expansion(
                    _podpis,
                    value=(has_active or sym in _pomnim),'''


# 2. при клике — запомнить или забыть ───────────────────────
STARO_2 = '''    def _raskryli_papku(imya: str, otkryta: bool):
        """Обработчик раскрытия. Задачей — рисовать нельзя блокируя."""
        if not otkryta:
            return'''

NOVO_2 = '''    def _raskryli_papku(imya: str, otkryta: bool):
        """Обработчик раскрытия. Задачей — рисовать нельзя блокируя."""
        # POLKA_POMNIT_V1: запоминаем ДО всего остального — иначе
        # перерисовка после разведки закроет то, что Шеф открыл.
        _pomnim = state.setdefault("раскрыто", set())
        if otkryta:
            _pomnim.add(imya)
        else:
            _pomnim.discard(imya)
        if not otkryta:
            return'''


ZAMENY = [
    ("открывать то, что помним", STARO_1, NOVO_1),
    ("запоминать при клике", STARO_2, NOVO_2),
]


def main():
    print("=" * 58)
    print("ПОЛКА ПОМНИТ РАСКРЫТОЕ")
    print("=" * 58)

    fajl = _nayti()
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

    bak = fajl.with_suffix(fajl.suffix + ".bak_polka_pomnit")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город:")
    print("  Раскрой USDCNH — этажи должны остаться на виду,")
    print("  а не схлопнуться после «📂 USDCNH: этажей 13».")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_POLKA_POMNIT_V1 - marker
