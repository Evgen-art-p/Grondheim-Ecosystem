# -*- coding: utf-8 -*-
# ruka_srabotala_otvet_pust.py — рука отработала, а рассказ пуст.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python ruka_srabotala_otvet_pust.py
#
# ═══ ЧТО ПРОИСХОДИЛО ═══
#
# В логе:
#     [РУКА] 🖐 otdat_prikaz({'что': 'WAIT', ...}) → принято
#     [РУКИ] не сработали (Модель вернула пустой ответ) — иду обычным глазом
#
# Читается как поломка, а на деле рука СРАБОТАЛА: приказ лёг на
# табло, и ниже в том же пробуде видно «[РЕШЕНИЕ] с руки: WAIT».
#
# Пустым оказался только РАССКАЗ — модель после вызова руки не
# дописала свой текст. Город считал весь заход провалившимся и шёл
# ЗАНОВО, обычным глазом, без рук. Лишний кадр, лишнее обращение к
# модели, лишние деньги — на каждом таком пробуде.
#
# Ровно та же цена, что была у переспроса. Одну пару вызовов сменили
# на другую.
#
# ═══ ПОЧЕМУ ЧИНИТСЯ ЛЕГКО ═══
#
# В llm.py уже живёт RUKI_NE_TERYAT_SLOVO_V1: город запоминает
# posledneye_slovo — то, что собеседник сказал СЛОВАМИ в том же
# ответе, где звал руку. Этот текст просто выбрасывался, когда круг
# кончался пустотой.
#
# Теперь: руки в этом заходе уже отработали — значит дело сделано.
# Берём последнее сказанное слово, а нет его — пустой рассказ, и
# идём дальше. Приказ на табло, счёт посчитан, перезаходить незачем.
#
# Настоящая пустота — когда рук не было вовсе и сказать нечего — как
# была ошибкой, так ей и остаётся.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт llm.py.bak_otvet_pust.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "RUKA_SRABOTALA_OTVET_PUST_V1"

STAROE = (
    '        if not msg.get("tool_calls"):\n'
    '            content = msg.get("content") or ""\n'
    '            if not content.strip():\n'
    '                raise RuntimeError("Модель вернула пустой ответ (кадр+руки)")\n'
)

NOVOE = (
    '        if not msg.get("tool_calls"):\n'
    '            content = msg.get("content") or ""\n'
    '            if not content.strip():\n'
    '                # RUKA_SRABOTALA_OTVET_PUST_V1: рассказ не дописался.\n'
    '                # Если руки в этом заходе УЖЕ отработали — дело\n'
    '                # сделано: приказ лежит на табло, счёт посчитан.\n'
    '                # Перезаходить заново незачем: это лишний кадр и\n'
    '                # лишнее обращение к модели на каждом таком баре.\n'
    '                # Берём последнее сказанное словами (город его и\n'
    '                # так помнит — RUKI_NE_TERYAT_SLOVO_V1), а нет\n'
    '                # его — идём с пустым рассказом.\n'
    '                if sdelano or zvali_ruki:\n'
    '                    content = (posledneye_slovo or "").strip() or "{}"\n'
    '                    print(f"[РУКИ] рассказ не дописался, но руки "\n'
    '                          f"отработали ({sdelano}) — иду с тем, "\n'
    '                          f"что есть")\n'
    '                else:\n'
    '                    # Рук не было и сказать нечего — это правда\n'
    '                    # пустой ответ, как и раньше.\n'
    '                    raise RuntimeError(\n'
    '                        "Модель вернула пустой ответ (кадр+руки)")\n'
)


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет llm.py сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "llm.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob("llm.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько llm.py:")
        for nomer, put in enumerate(nashlos, 1):
            print(f"  {nomer}. {put}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/llm.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if tekst.count(STAROE) != 1:
        print(f"✗ нашёл {tekst.count(STAROE)} мест вместо одного —")
        print("  файл мог измениться. Ничего не тронул.")
        print("  Скажи Брату, поправим по месту.")
        return 1

    novyy = tekst.replace(STAROE, NOVOE, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_otvet_pust")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ пустой рассказ после руки больше не провал:")
    print("    · руки отработали — город идёт дальше, не перезаходит")
    print("    · берётся последнее сказанное словами, если оно было")
    print("    · настоящая пустота (рук не было) — по-прежнему ошибка")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("В логе строчки «[РУКИ] не сработали» быть не должно.")
    print("Вместо неё — «рассказ не дописался, но руки отработали»,")
    print("и сразу дальше, без второго кадра.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
