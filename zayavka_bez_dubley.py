# -*- coding: utf-8 -*-
"""
zayavka_bez_dubley.py — «переставить заявку» больше не рождает вторую.

Прогон 23.09 (июль, Луна): Синди дважды отдала MOVE_ORDER, а на кадре
вместо одной заявки стало три (уровни 2 → 4 → 6), и все три сработали.

Причина — мозг трейдера (слоты A06/A07/A08) не знал новых слов. Список
действий у него был старый (ENTER, WAIT, HOLD, MOVE_STOP, ADD, CLOSE):
MOVE_ORDER там нет, и он скатывался в запасной путь «вердикт APPROVED —
значит ENTER». APPROVED висел с прошлого входа — и каждая перестановка
уходила исполнителю как НОВЫЙ вход с новыми числами.

Что делает:
  1. Мозги A06, A07, A08 — MOVE_ORDER и CANCEL в списке действий; при
     них вердикт ставится «не вход», чтобы старый APPROVED не протёк.
  2. Исполнитель — не открывает новую заявку, если у этого трейдера
     уже висит своя (раньше проверял только открытые позиции).

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет все, потом пишет. Копии `.bak_zayavka_dubl`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "ZAYAVKA_BEZ_DUBLEY_V1"
_CEH = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха")


def _mozg(slot, pre):
    return (os.path.join(_CEH, "торговый_хаос", "слоты", slot, "мозг.py"), [
        ('_MANAGE_ACTIONS = ("ENTER", "WAIT", "HOLD", "MOVE_STOP", "ADD", "CLOSE")\n',
         '# ZAYAVKA_BEZ_DUBLEY_V1: руки для висящей заявки. Без них MOVE_ORDER\n'
         '# скатывался в «APPROVED — значит ENTER» и рождал вторую заявку.\n'
         '_MANAGE_ACTIONS = ("ENTER", "WAIT", "HOLD", "MOVE_STOP", "ADD", "CLOSE",\n'
         '                   "MOVE_ORDER", "CANCEL")\n'),
        ('    elif action == "WAIT":\n'
         '        signal["' + pre + '_verdict"] = "REJECTED"\n',
         '    elif action == "WAIT":\n'
         '        signal["' + pre + '_verdict"] = "REJECTED"\n'
         '    elif action in ("MOVE_ORDER", "CANCEL"):\n'
         '        # ZAYAVKA_BEZ_DUBLEY_V1: не вход — заявка уже висит. Старый\n'
         '        # APPROVED с прошлого ENTER протечь не должен.\n'
         '        signal["' + pre + '_verdict"] = "REJECTED"\n'),
    ])


ZAMENY = dict([
    _mozg("A06", "brut"),
    _mozg("A07", "brut"),
    _mozg("A08", "cons"),
    (os.path.join(_CEH, "контора", "слоты", "исполнитель", "мозг.py"), [
        ('    open_magics = {p.get("magic") for p in tstate["positions"]\n'
         '                   if p.get("status") == "OPEN"}\n',
         '    # ZAYAVKA_BEZ_DUBLEY_V1: висящая заявка — тоже «уже есть».\n'
         '    # Вторую рядом не рождаем: свою двигают MOVE_ORDER, снимают CANCEL.\n'
         '    open_magics = {p.get("magic") for p in tstate["positions"]\n'
         '                   if p.get("status") in ("OPEN", "PENDING")}\n'),
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
        bak = put + ".bak_zayavka_dubl"
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
    print("  MOVE_ORDER и CANCEL больше не превращаются в новый вход; дубль заявки не рождается.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
