# -*- coding: utf-8 -*-
"""
kadr_krupno.py — кадр по щелчку разворачивается во весь экран.

Было: щёлкаешь по кадру — открывается окошко размером с иконку, и
картинку не разглядеть. Причина: у картинки в окне стояла только
max-width, без ширины — Quasar схлопывал её почти в ноль.

Стало: окно на 96% ширины экрана, картинка на всю его ширину, высота
по пропорциям, но не выше 86% экрана.

Правит Биржа/ui_torg.py, одно место (_kadr_krupno).

Запуск: положить в корень репы, запустить. Копия:
ui_torg.py.bak_kadr_krupno. Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "KADR_KRUPNO_V1"
PUT = os.path.join("Биржа", "ui_torg.py")
STAROE = '            with ui.dialog() as _d, ui.card().style(\n                "background:#0d1117; padding:10px; max-width:96vw;"\n            ):\n                ui.image(str(put)).style("max-width:92vw; max-height:86vh;")\n'
NOVOE = '            # KADR_KRUPNO_V1: картинке нужна ШИРИНА. С одним\n            # max-width Quasar схлопывал её в иконку — кадр\n            # «не разворачивался», как ни щёлкай.\n            with ui.dialog() as _d, ui.card().style(\n                "background:#0d1117; padding:10px; width:96vw; "\n                "max-width:96vw;"\n            ):\n                ui.image(str(put)).style(\n                    "width:100%; height:auto; max-height:86vh; "\n                    "object-fit:contain;")\n'


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
    otv = input("Перетащи сюда папку репы и нажми Enter:\n").strip().strip('"').strip("'")
    return godnyy(otv)


def main():
    put = nayti()
    if not put:
        print("✗ Биржа/ui_torg.py не найден. Ничего не менял.")
        return
    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")
    if METKA in t:
        print("✓ Уже накатано раньше — ничего не менял.")
        return
    if t.count(STAROE) != 1:
        print(f"✗ Место не нашлось как ожидалось (совпадений: {t.count(STAROE)}). "
              "Ничего не менял. Покажи Брату.")
        return
    t = t.replace(STAROE, NOVOE, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return
    bak = put + ".bak_kadr_krupno"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    try:
        py_compile.compile(put, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, put)
        print(f"✗ Не скомпилировался, вернул как было: {e}")
        return
    print(f"✓ Готово: {put}")
    print(f"  копия до правки: {bak}")
    print("  Щёлкни по кадру — развернётся во весь экран.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
