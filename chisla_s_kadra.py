# -*- coding: utf-8 -*-
"""
chisla_s_kadra.py — четыре числа при входе: с кадра, на глаз, из одной пары.

Слово Шефа 23.09. В разговоре Синди дважды споткнулась:
  · «со стола не взяты — приказ не отдала бы»: думала, что числа должен
    дать город, а город их не даёт — видит, а назвать боится;
  · смешала пары: цены взяла с тонкой линии, первую яму AO — с толстой.
Когда Шеф сказал ей это прямо, назвала верно. Но разговор в работу сам
не переходит — пусть стоит там, где она его видит в прогоне.

Что делает (Биржа/ruki_treydera.py, рука приказа): переписывает описание
четырёх полей цена_1, ao_1, цена_2, ao_2:
  · числа называть с кадра, на глаз, точность до пункта не нужна;
  · все четыре — из одной пары, с одних мест, пары не смешивать;
  · входит по краю — пара у края (тонкая линия), по всему ходу —
    большая (толстая).
Больше ничего не меняет: ENTER без четырёх чисел по-прежнему не
принимается, сверка по-прежнему ничего не запрещает.

Запуск: положить в корень репы, запустить. Сам находит файл, сперва
проверяет, потом пишет. Копия `ruki_treydera.py.bak_chisla_s_kadra`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "CHISLA_S_KADRA_V1"
PUT = os.path.join("Биржа", "ruki_treydera.py")
NACHALO = '"цена_1": {"type": "number",'
KONEC_POLYA = '"ao_2": {"type": "number",'
NOVOE = '                "цена_1": {"type": "number",\n                           "description": ("для ENTER: цена в ПЕРВОЙ точке "\n                                           "расхождения — вершина (вниз: "\n                                           "впадина). Все четыре числа "\n                                           "называй С КАДРА, на глаз: стол "\n                                           "их не даёт, точность до пункта "\n                                           "не нужна. Бери их из ОДНОЙ "\n                                           "пары: обе цены и обе ямы "\n                                           "(горба) AO — с одних мест, "\n                                           "точки разных пар не смешивай. "\n                                           "Входишь по краю — называй пару "\n                                           "у края (на кадре тонкая линия), "\n                                           "по всему ходу — большую пару "\n                                           "(толстая линия)")},\n                "ao_1": {"type": "number",\n                         "description": ("для ENTER: AO в этой же ПЕРВОЙ "\n                                         "точке — горб (яма) той же пары, "\n                                         "с кадра на глаз")},\n                "цена_2": {"type": "number",\n                           "description": ("для ENTER: цена во ВТОРОЙ точке "\n                                           "той же пары — новая вершина "\n                                           "(впадина), дальше по ходу")},\n                "ao_2": {"type": "number",\n                         "description": ("для ENTER: AO в этой же ВТОРОЙ "\n                                         "точке — горб (яма) под ней, той "\n                                         "же пары")},\n'


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


def pravka(tekst):
    if METKA in tekst:
        return tekst, "уже стоит"
    if tekst.count(NACHALO) != 1 or tekst.count(KONEC_POLYA) != 1:
        raise RuntimeError("в руке приказа не нашлись поля четырёх чисел — "
                           "стоит ли chetyre_chisla.py? Если стоит, пришли "
                           "Брату файл Биржа/ruki_treydera.py")
    # от начала строки с цена_1 — до конца описания ao_2
    i = tekst.rfind("\n", 0, tekst.index(NACHALO)) + 1
    j = tekst.index(KONEC_POLYA)
    k = tekst.find(")},\n", j)
    if k < 0:
        raise RuntimeError("не нашёлся конец поля ao_2 — пришли Брату "
                           "файл Биржа/ruki_treydera.py")
    k += len(")},\n")
    otstup = tekst[i:tekst.index(NACHALO)]
    novoe = NOVOE
    if otstup != " " * 16:
        novoe = "\n".join((otstup + s[16:]) if s.startswith(" " * 16) else s
                          for s in NOVOE.split("\n"))
    metka = otstup + "# " + METKA + ": числа с кадра, на глаз, из одной пары.\n"
    novyy = tekst[:i] + metka + novoe + tekst[k:]
    ast.parse(novyy)
    return novyy, "перепишу"


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
    try:
        novyy, chto = pravka(tekst)
    except Exception as e:
        print(f"✗ {e}\n  Ничего не менял.")
        return
    if novyy == tekst:
        print("✓ Уже стоит. Ничего не менял.")
        return
    bak = put + ".bak_chisla_s_kadra"
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
    print("  Четыре числа: с кадра, на глаз, из одной пары; край — тонкая, "
          "весь ход — толстая.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
