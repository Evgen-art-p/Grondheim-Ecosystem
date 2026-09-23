# -*- coding: utf-8 -*-
"""
chistka_obrazcy.py — чистка после образцов: знания и сверка не спорят
с картинками.

1. Из знаний Синди (A06/знания/AO.md) убирает раздел «Дивер по волнам»
   (пересказ Брата, патч ao_pyat_pul.py). Теперь вместо него — образцы
   и слова Вильямса. Остальное в AO.md не трогает.
2. Из сверки (Биржа/sverka_divera.py) убирает правило «если самая
   высокая цена позади — дивер был там, здесь его нет». Это была
   добавка Брата; на образце EURUSD (01-02.07.2025) она отвергла
   её лучшую сделку. Сверка теперь просто пишет, сколько баров назад
   была крайняя цена.

Запуск: положить в корень репы, запустить. Сам находит оба файла.
Копии: AO.md.bak_chistka, sverka_divera.py.bak_chistka.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "CHISTKA_OBRAZCY_V1"
PUT_AO = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос",
                      "слоты", "A06", "знания", "AO.md")
PUT_SV = os.path.join("Биржа", "sverka_divera.py")
RAZDEL = '## Дивер по волнам\n\nИсточник: Profitunity (школа Вильямса), «пять пуль» — первая пуля.\n\nТретья волна — самый высокий пик AO в поле зрения (100-140 баров).\n\nПосле неё четвёртая: AO проваливается. Может уйти за ноль — это\nне важно.\n\nПотом пятая: цена снова идёт вверх.\n\nДивер: цена в конце пятой выше цены на пике третьей волны, а AO на\nсамой высокой цене ниже пика третьей.\n\nAO смотрят на САМОЙ ВЫСОКОЙ цене. Если самая высокая цена уже позади,\nа сейчас цена ниже неё — дивер был там, а не здесь.\n\nВниз — зеркально: самая глубокая яма AO — третья; цена в пятой ниже\nцены на дне третьей, а AO на самой низкой цене мельче.\n\n<!-- AO_PYAT_PUL_V1 -->\n\n'
SV_STAROE = '    if kh != p:\n        return {"ok": True, "est": False,\n                "slovami": slovami + f" · дивер был {_kogda(kh)}, а сейчас "\n                           f"цена {\'ниже\' if verh else \'выше\'} той — "\n                           "здесь его нет"}\n'
SV_NOVOE = '    # CHISTKA_OBRAZCY_V1: крайняя цена может быть позади на несколько\n    # баров — вход бывает на развороте ПОСЛЕ вершины (образец EURUSD\n    # 01-02.07.2025). Прежнее «дивер был там, здесь его нет» было\n    # добавкой Брата, не источником, — убрано. Только сообщаем, когда.\n    if kh != p:\n        slovami += f" · крайняя цена {p - kh} бар(ов) назад"\n'


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if (os.path.isfile(os.path.join(papka, PUT_AO)) and
                     os.path.isfile(os.path.join(papka, PUT_SV))) else None


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
    otv = input("Перетащи сюда папку репы и нажми Enter:\n").strip().strip('"').strip("'")
    return godnyy(otv)


def prochest(put):
    with open(put, "rb") as f:
        t = f.read().decode("utf-8")
    return t.replace("\r\n", "\n"), "\r\n" in t


def zapisat(put, t, crlf):
    bak = put + ".bak_chistka"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    return bak


def main():
    repo = nayti()
    if not repo:
        print("✗ Репа не найдена (нужны AO.md Синди и Биржа/sverka_divera.py). Ничего не менял.")
        return
    ao = os.path.join(repo, PUT_AO)
    sv = os.path.join(repo, PUT_SV)
    t_ao, crlf_ao = prochest(ao)
    t_sv, crlf_sv = prochest(sv)

    if METKA in t_sv and "AO_PYAT_PUL_V1" not in t_ao:
        print("✓ Уже почищено раньше — ничего не менял.")
        return

    # проверяем оба места ДО любой записи
    nado_ao = "AO_PYAT_PUL_V1" in t_ao
    nado_sv = METKA not in t_sv
    if nado_ao and t_ao.count(RAZDEL) != 1:
        print("✗ Раздел «Дивер по волнам» в AO.md не такой, как вписывали "
              "(правили руками?). Ничего не менял. Покажи Брату.")
        return
    if nado_sv and t_sv.count(SV_STAROE) != 1:
        print("✗ Место в сверке не нашлось как ожидалось. Ничего не менял. Покажи Брату.")
        return

    if nado_sv:
        t_new = t_sv.replace(SV_STAROE, SV_NOVOE, 1)
        try:
            ast.parse(t_new)
        except SyntaxError as e:
            print(f"✗ Сверка после правки не собирается: {e}. Ничего не менял.")
            return
        bak = zapisat(sv, t_new, crlf_sv)
        try:
            py_compile.compile(sv, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, sv)
            print(f"✗ Сверка не скомпилировалась, вернул как было: {e}")
            return
        print(f"✓ Сверка: убрано «дивер был там, здесь его нет» · копия {bak}")

    if nado_ao:
        bak = zapisat(ao, t_ao.replace(RAZDEL, "", 1), crlf_ao)
        print(f"✓ AO.md: раздел «Дивер по волнам» убран · копия {bak}")

    print("  Готово. Знания и сверка больше не спорят с образцами.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
