# -*- coding: utf-8 -*-
"""
urovni_sleva.py — подписи уровней ордера (вход, стоп, заявка, был стоп)
переезжают к ЛЕВОМУ краю кадра.

Слово Шефа 23.09: справа подписи закрывают свежую цену — ровно то место,
куда смотрят и Шеф, и трейдер. Слева на кадре старая история, там они
никому не мешают. Сами линии по-прежнему идут через весь кадр.

Что делает (Биржа/grafik.py, блок UROVNI_ORDEROV_V1): подпись ставится
у левого края и выравнивается влево. Больше ничего не трогает.

Запуск: положить в корень репы, запустить. Сам находит файл, сперва
проверяет, потом пишет. Копия `grafik.py.bak_urovni_sleva`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "UROVNI_SLEVA_V1"
PUT = os.path.join("Биржа", "grafik.py")
ZAMENY = [
    ("            # подписи ВНУТРИ кадра у правого края: справа от свечей\n",
     "            # UROVNI_SLEVA_V1 (23.09, слово Шефа): подписи — у ЛЕВОГО\n"
     "            # края: справа они закрывали свежую цену.\n"
     "            # (было: подписи ВНУТРИ кадра у правого края: справа от свечей)\n"),
    ("                ax.text(0.995, _f, f'{_pod} {_c:.{_znakov}f}',\n",
     "                ax.text(0.005, _f, f'{_pod} {_c:.{_znakov}f}',\n"),
    ("                        fontsize=10, va='center', ha='right',\n",
     "                        fontsize=10, va='center', ha='left',\n"),
]


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if os.path.isfile(os.path.join(papka, PUT)) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        if godnyy(papka):
            return papka
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = os.path.join(koren, imya)
                if godnyy(p) and p not in kandidaty:
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
    otv = input("Не нашёл репу. Перетащи сюда папку репы и нажми Enter: ")
    otv = otv.strip().strip('"').strip("'")
    return godnyy(otv) if otv else None


def main():
    repa = nayti()
    if not repa:
        print("✗ Репу не нашёл. Ничего не менял.")
        return
    put = os.path.join(repa, PUT)
    with open(put, "rb") as f:
        syroe = f.read()
    crlf = b"\r\n" in syroe
    tekst = syroe.decode("utf-8").replace("\r\n", "\n")
    if METKA in tekst:
        print("✓ Уже стоит. Ничего не менял.")
        return
    novyy = tekst
    for staroe, novoe in ZAMENY:
        if novyy.count(staroe) != 1:
            print("✗ В кадре не нашлось место подписей уровней — пришли "
                  "Брату файл Биржа/grafik.py.\n  Ничего не менял.")
            return
        novyy = novyy.replace(staroe, novoe)
    ast.parse(novyy)
    bak = put + ".bak_urovni_sleva"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((novyy.replace("\n", "\r\n") if crlf else novyy).encode("utf-8"))
    try:
        py_compile.compile(put, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, put)
        print(f"✗ Не скомпилировалось, вернул как было: {e}")
        return
    print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Подписи уровней теперь у левого края кадра.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
