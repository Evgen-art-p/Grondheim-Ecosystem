# -*- coding: utf-8 -*-
# POSTAVIT_VERNUT_KNOPKU_CHTENIYA_V1
"""
ПАТЧ: вернуть кнопку «📖 Прочитать» в Академии.

Запускать из КОРНЯ РЕПО:
    python postavit_vernut_knopku_chteniya.py

ЧТО СЛОМАЛ Я
    Кнопка «Прочитать» стоит ПОД списком файлов, в панели с
    ограниченной высотой. Я вырастил всё, что над ней:
      · три поля подписи (источник / подпись / тема);
      · две новые строки в каждой записи списка — ключ и подпись.
    Панель переполнилась, и кнопку вытолкнуло за нижний край.
    Файл кладёшь — список растёт — кнопка пропадает.

ЧТО ДЕЛАЕТ
    · Ключ и подпись в записи — одной строкой вместо двух.
    · Список: 300px → 170px. Прокрутка в нём и так есть, а место
      нужнее кнопке: список можно пролистать, кнопку — нет.

    Ничего не убирает: и ключ, и подпись, и поля остаются на месте.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_knopka_chteniya, ast.parse перед записью.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# VERNUT_KNOPKU_CHTENIYA_V1"


def _nayti():
    kand = [p for p in _KOREN.rglob("ui_akademia.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл ui_akademia.py. Запускай из корня репозитория.")
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


# 1. ключ и подпись — одной строкой ─────────────────────────
STARO_1 = """                    {f'<div style="color:rgba(0,255,136,0.65);font-size:9px;margin-top:2px;word-break:break-all;">🔑 {_kl}</div>' if _kl else ''}
                    {f'<div style="color:rgba(255,255,255,0.45);font-size:9px;margin-top:1px;">{_pd}</div>' if _pd else ''}"""

NOVO_1 = """                    {f'<div style="color:rgba(0,255,136,0.60);font-size:9px;margin-top:2px;word-break:break-all;">🔑 {_kl}{(" · " + _pd) if _pd else ""}</div>' if (_kl or _pd) else ''}"""


# 2. список пониже — место нужнее кнопке ────────────────────
STARO_2 = '''                        "max-height:300px; overflow-y:auto; overflow-x:hidden; padding:4px 8px;")'''

NOVO_2 = '''                        # VERNUT_KNOPKU_CHTENIYA_V1: было 300px. Кнопка
                        # «Прочитать» стоит ПОД списком, и на полной
                        # панели её выталкивало за край. Список можно
                        # пролистать, кнопку — нет.
                        "max-height:170px; overflow-y:auto; overflow-x:hidden; padding:4px 8px;")'''


ZAMENY = [
    ("ключ и подпись одной строкой", STARO_1, NOVO_1),
    ("список пониже", STARO_2, NOVO_2),
]


def main():
    print("=" * 58)
    print("ВЕРНУТЬ КНОПКУ ЧТЕНИЯ")
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
        print("  Похоже, список рисуется иначе — покажи файл, пересоберу.")
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

    bak = fajl.with_suffix(fajl.suffix + ".bak_knopka_chteniya")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город:")
    print("  Закинь файл — «📖 Прочитать» должна остаться на месте,")
    print("  а ключ и подпись стоять одной строкой под именем файла.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_VERNUT_KNOPKU_CHTENIYA_V1 - marker
