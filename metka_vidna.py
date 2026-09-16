# -*- coding: utf-8 -*-
# metka_vidna.py — контрольную метку снова видно глазом.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python metka_vidna.py
#
# ЗАЧЕМ. Контрольная метка — две буквы и две цифры в левом верхнем
# углу кадра, новые при каждой отрисовке. Её нет ни на столе, ни в
# промпте, ни в знаниях: ТОЛЬКО на картинке. Это единственный честный
# способ спросить трейдера «видишь ли ты кадр» и проверить ответ.
#
# ЧТО СЛОМАЛОСЬ. Ничего не ломалось — метка рисуется и в файл
# попадает. Но кадр шириной 1584 пикселя ужимается в панель Кабинета
# до пятисот, и метка вместе с ним: с 18 пунктов до ДЕВЯТИ пикселей.
# На тёмном фоне среди свечей её не разглядеть. Метка есть, а Шеф её
# не видит — значит проверить кадр нечем.
#
# ЧТО ДЕЛАЕМ.
#
# 1. МЕТКА КРУПНЕЕ: 18 → 44 пункта. В ужатой панели это станет
#    примерно 22 пикселя — читается. На полном кадре крупно, но она
#    и должна быть заметной: это не украшение, а проверка.
#
# 2. КАДР КЛИКАБЕЛЬНЫЙ: щелчок по кадру в панели открывает его во
#    весь экран. Такое уже умеют миниатюры в ленте — берём тот же
#    готовый показ, ничего нового не изобретаем.
#
# БЕЗОПАСНО. Правит два файла, каждый проверяет отдельно: собирает
# новый текст, гоняет ast.parse и только потом пишет. Рядом с каждым
# кладёт копию. Один файл не сошёлся — второй тоже не трогается.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "METKA_VIDNA_V1"

# ── grafik.py: метка крупнее ─────────────────────────────────
G_STAROE = (
    "        fig.text(0.012, 0.985, _kod, ha='left', va='top',\n"
    "                 fontsize=18, color='#ffd866', family='monospace',\n"
    "                 fontweight='bold', zorder=20)\n"
)
G_NOVOE = (
    "        # METKA_VIDNA_V1: было 18 — в ужатой панели Кабинета это\n"
    "        # девять пикселей, метку не разглядеть. А метка, которую\n"
    "        # не видит Шеф, не проверяет ничего.\n"
    "        fig.text(0.012, 0.985, _kod, ha='left', va='top',\n"
    "                 fontsize=44, color='#ffd866', family='monospace',\n"
    "                 fontweight='bold', zorder=20)\n"
)

# ── ui_torg.py: кадр в панели открывается крупно ─────────────
U_STAROE_1 = (
    '            ui.image(str(p)).style(\n'
    '                "width:100%; height:100%; object-fit:contain; "\n'
    '                "flex:1; min-height:0;")\n'
)
U_NOVOE_1 = (
    '            # METKA_VIDNA_V1: щелчок по кадру — во весь экран.\n'
    '            # Показ уже готов, им живут миниатюры в ленте.\n'
    '            ui.image(str(p)).style(\n'
    '                "width:100%; height:100%; object-fit:contain; "\n'
    '                "flex:1; min-height:0; cursor:pointer;").on(\n'
    '                "click", lambda _=None, _p=str(p): _kadr_krupno(_p))\n'
)

U_STAROE_2 = (
    '                ui.image(str(_put)).style(\n'
    '                    "width:100%; height:100%; object-fit:contain; "\n'
    '                    "flex:1; min-height:0;")\n'
)
U_NOVOE_2 = (
    '                # METKA_VIDNA_V1: тот же щелчок и у догнанного кадра.\n'
    '                ui.image(str(_put)).style(\n'
    '                    "width:100%; height:100%; object-fit:contain; "\n'
    '                    "flex:1; min-height:0; cursor:pointer;").on(\n'
    '                    "click", lambda _=None, _q=str(_put): _kadr_krupno(_q))\n'
)


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti(imya):
    """Ищет файл сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / imya
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob(imya)
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        return nashlos[0]
    if len(nashlos) > 1:
        print(f"Нашёл несколько {imya}:")
        for nomer, put in enumerate(nashlos, 1):
            print(f"  {nomer}. {put}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def podgotovit(put, pravki):
    """Собирает новый текст, ничего не записывая. Беда — (None, текст)."""
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        return None, "уже сделано"
    for nomer, (staroe, _) in enumerate(pravki, 1):
        if tekst.count(staroe) != 1:
            return None, (f"правка {nomer}: нашёл {tekst.count(staroe)} мест "
                          f"вместо одного")
    novyy = tekst
    for staroe, novoe in pravki:
        novyy = novyy.replace(staroe, novoe, 1)
    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        return None, f"после правки файл поломался (строка {beda.lineno})"
    return novyy, ""


def main():
    grafik = nayti("grafik.py")
    kabinet = nayti("ui_torg.py")
    if grafik is None or kabinet is None:
        print("✗ не нашёл Биржа/grafik.py или Биржа/ui_torg.py —")
        print("  запускай из корня репозитория")
        return 1

    g_novyy, g_beda = podgotovit(grafik, [(G_STAROE, G_NOVOE)])
    k_novyy, k_beda = podgotovit(
        kabinet, [(U_STAROE_1, U_NOVOE_1), (U_STAROE_2, U_NOVOE_2)])

    if g_beda == "уже сделано" and k_beda == "уже сделано":
        print("· уже сделано")
        return 0

    # Готовим ОБА и только потом пишем: не хочу половину правки.
    for imya, beda in (("grafik.py", g_beda), ("ui_torg.py", k_beda)):
        if beda and beda != "уже сделано":
            print(f"✗ {imya}: {beda}")
            print("  Ничего не тронул ни в одном файле.")
            print("  Скажи Брату, поправим по месту.")
            return 1

    for put, novyy, hvost in ((grafik, g_novyy, ".bak_metka"),
                              (kabinet, k_novyy, ".bak_metka")):
        if novyy is None:
            continue
        kopiya = put.with_suffix(put.suffix + hvost)
        if not kopiya.exists():
            shutil.copy2(put, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        put.write_text(novyy, encoding="utf-8")

    print("✓ метку снова видно:")
    print("    · контрольная метка выросла с 18 до 44 пунктов")
    print("    · щелчок по кадру открывает его во весь экран")
    print()
    print("Перезапусти Кабинет (main.py).")
    print("Теперь запусти прогон и смотри на угол кадра при каждом")
    print("пробуде: меняется код — кадр свежий, стоит — отстаёт.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
