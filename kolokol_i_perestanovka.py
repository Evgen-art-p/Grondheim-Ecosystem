# -*- coding: utf-8 -*-
"""
kolokol_i_perestanovka.py — две ошибки города из прогона 24.09.

1. КОЛОКОЛ БЫЛ СЛЕПОЙ К СТОРОНЕ. Колокол на выход — это медвежье
   расхождение AO (конец импульса ВВЕРХ). Город закрывал по нему ЛЮБУЮ
   позицию — и LONG, и SHORT. А для SHORT медвежье расхождение — это
   не выход, а подтверждение. 04.07 20:00 колокол зазвонил на вершине и
   закрыл её SHORT на +0.88R, хотя ход вниз только начинался.
   Теперь: LONG закрывает медвежье расхождение, SHORT — бычье
   (зеркально, как и положено).

2. ПЕРЕСТАНОВКА ТЕРЯЛА ЧИСЛА. 17.07 Синди верно переставила заявку на
   новый разворотник (вход 1.16048, стоп 1.1556), а исполнитель получил
   «вход None, стоп None» и отказал. Причина: перед этим был WAIT, он
   оставил на табло вердикт REJECTED, а чистильщик мозга при REJECTED
   обнуляет цену и стоп — не глядя, что действие MOVE_ORDER. Заявка
   осталась на старом месте и выбила −1R.
   Теперь при MOVE_ORDER цена и стоп доходят до исполнителя.

Что правит: Биржа/hooks.py (колокол) и мозги A06, A07, A08.

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет все, потом пишет. Копии `.bak_kolokol`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "KOLOKOL_I_PERESTANOVKA_V1"
_SLOTY = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос", "слоты")


def _mozg(slot, pre):
    return (os.path.join(_SLOTY, slot, "мозг.py"), [
        ('    if v == "REJECTED":\n'
         '        signal["' + pre + '_direction"] = None\n',
         '    # KOLOKOL_I_PERESTANOVKA_V1: при MOVE_ORDER цена и стоп — это\n'
         '    # новое место заявки, не вход. Старый REJECTED (от WAIT) их\n'
         '    # стирать не должен — иначе исполнитель получит None.\n'
         '    _perestavlyayu = str(signal.get("' + pre + '_action") or ""\n'
         '                         ).upper().strip() == "MOVE_ORDER"\n'
         '    if v == "REJECTED" and not _perestavlyayu:\n'
         '        signal["' + pre + '_direction"] = None\n'),
        ('    else:\n'
         '        d = signal.get("' + pre + '_direction")\n',
         '    elif not _perestavlyayu:\n'
         '        d = signal.get("' + pre + '_direction")\n'),
    ])


ZAMENY = dict([
    _mozg("A06", "brut"),
    _mozg("A07", "brut"),
    _mozg("A08", "cons"),
    (os.path.join("Биржа", "hooks.py"), [
        ('        elif reason is None and bell and close is not None:\n'
         '            exit_price, reason = close, "EXIT_BELL"\n',
         '        # KOLOKOL_I_PERESTANOVKA_V1: колокол — по стороне сделки.\n'
         '        # Медвежье расхождение (exit_bell) кончает ход ВВЕРХ — это\n'
         '        # выход для LONG. Для SHORT выход — бычье (divergence_ao).\n'
         '        # Раньше колокол закрывал и SHORT по медвежьему — то есть\n'
         '        # по сигналу в ЕГО пользу.\n'
         '        elif reason is None and close is not None and (\n'
         '                (direction == "LONG" and bell)\n'
         '                or (direction == "SHORT"\n'
         '                    and bool(md.get("divergence_ao")))):\n'
         '            exit_price, reason = close, "EXIT_BELL"\n'),
    ]),
])


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if all(os.path.isfile(os.path.join(papka, p))
                        for p in ZAMENY) else None


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
    gotovo = []
    for otn, zameny in ZAMENY.items():
        put = os.path.join(repa, otn)
        with open(put, "rb") as f:
            syroe = f.read()
        crlf = b"\r\n" in syroe
        tekst = syroe.decode("utf-8").replace("\r\n", "\n")
        if METKA in tekst:
            print(f"· {otn}: уже стоит")
            continue
        novyy = tekst
        for staroe, novoe in zameny:
            if novyy.count(staroe) != 1:
                print(f"✗ {otn}: не нашлось место правки — пришли Брату "
                      f"этот файл.\n  Ничего не менял.")
                return
            novyy = novyy.replace(staroe, novoe)
        ast.parse(novyy)
        gotovo.append((put, novyy, crlf))
    if not gotovo:
        print("✓ Всё уже стоит. Ничего не менял.")
        return
    for put, novyy, crlf in gotovo:
        bak = put + ".bak_kolokol"
        if not os.path.exists(bak):
            shutil.copy2(put, bak)
        with open(put, "wb") as f:
            f.write((novyy.replace("\n", "\r\n") if crlf else novyy)
                    .encode("utf-8"))
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Колокол звонит по стороне сделки; перестановка заявки доносит цену и стоп.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
