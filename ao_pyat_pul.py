# -*- coding: utf-8 -*-
"""
ao_pyat_pul.py — в знания Синди (A06) раздел «Дивер по волнам»,
слово в слово по источнику (Profitunity, «пять пуль»), без добавок.

Дописывает раздел в
GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A06/знания/AO.md
перед меткой ZNANIYA_PERVOGO_UROVNYA_A06_V1. Остальное не трогает.

Запуск: положить в корень репы, запустить. Сам находит AO.md.
Копия: AO.md.bak_pyat_pul. Повторный запуск ничего не ломает.
"""
import os
import shutil

METKA = "AO_PYAT_PUL_V1"
YAKOR = "<!-- ZNANIYA_PERVOGO_UROVNYA_A06_V1 -->"
RAZDEL = '## Дивер по волнам\n\nИсточник: Profitunity (школа Вильямса), «пять пуль» — первая пуля.\n\nТретья волна — самый высокий пик AO в поле зрения (100-140 баров).\n\nПосле неё четвёртая: AO проваливается. Может уйти за ноль — это\nне важно.\n\nПотом пятая: цена снова идёт вверх.\n\nДивер: цена в конце пятой выше цены на пике третьей волны, а AO на\nсамой высокой цене ниже пика третьей.\n\nAO смотрят на САМОЙ ВЫСОКОЙ цене. Если самая высокая цена уже позади,\nа сейчас цена ниже неё — дивер был там, а не здесь.\n\nВниз — зеркально: самая глубокая яма AO — третья; цена в пятой ниже\nцены на дне третьей, а AO на самой низкой цене мельче.\n\n<!-- AO_PYAT_PUL_V1 -->\n\n'
PUT = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос",
                   "слоты", "A06", "знания", "AO.md")

def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    p = os.path.join(papka, PUT)
    return p if os.path.isfile(p) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        p = godnyy(papka)
        if p:
            return p
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = godnyy(os.path.join(koren, imya))
                if p and p not in kandidaty:
                    kandidaty.append(p)
        except Exception:
            pass
    if len(kandidaty) == 1:
        otv = input(f"Нашёл: {kandidaty[0]}\nЭтот? (Enter — да, н — нет): ")
        if otv.strip().lower() not in ("н", "n", "нет", "no"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p}")
        otv = input("Какой? Цифра: ").strip()
        if otv.isdigit() and 1 <= int(otv) <= len(kandidaty):
            return kandidaty[int(otv) - 1]
    otv = input("Перетащи сюда папку репы и нажми Enter:\n")
    return godnyy(otv.strip().strip('"').strip("'"))


def zapisat(put, t, crlf, bak_imya):
    bak = put + bak_imya
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    vyvod = t.replace("\n", "\r\n") if crlf else t
    with open(put, "wb") as f:
        f.write(vyvod.encode("utf-8"))
    return bak


def main():
    put = nayti()
    if not put:
        print("✗ Знания A06 (AO.md) не найдены. Ничего не менял.")
        return
    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")
    if METKA in t:
        print("✓ Уже вписано раньше — ничего не менял.")
        return
    if t.count(YAKOR) != 1:
        print("✗ Метка ZNANIYA_PERVOGO_UROVNYA_A06_V1 не нашлась. Ничего не менял. Покажи Брату.")
        return
    t = t.replace(YAKOR, RAZDEL + YAKOR, 1)
    bak = zapisat(put, t, crlf, ".bak_pyat_pul")
    print(f"✓ Готово: {put}")
    print(f"  копия до правки: {bak}")
    print("  Синди получила «Дивер по волнам» по источнику.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
