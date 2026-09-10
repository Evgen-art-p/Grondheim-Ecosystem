# -*- coding: utf-8 -*-
# NAPOMINANIE_RUKI_V1
"""
РЕШИЛ — ЗОВИ РУКУ · напоминание прямо в глаза

ПРОГОН 10.09, шесть мест. На пятом трейдер сказал прямым текстом:
«это похоже на конец хода, и я вижу возможность для входа в лонг» —
и приказ НЕ отдал. В логе рядом: «в ответе есть поля решения, но
рукой приказ не отдан».

То есть отказов было не шесть, а пять. Шестой — немой вход: он
решил, сказал словами и не позвал руку.

ПОЧЕМУ. Руки у него есть, проверено. В бумаге правило записано. Но
бумага длинная, а первое сообщение — короткое и прямо перед
глазами; модель отвечает по нему. Про руку в нём не было ни слова.

ЧТО ДЕЛАЕТ ПАТЧ. Добавляет в блок «почему ты смотришь» — то самое
первое, что он читает, — короткое напоминание: решил войти, ждать,
подвинуть стоп или закрыть — зови руку, слова не считаются.

Правится `_povod_blok` в мозгах A06/A07/A08.

ТРЕБУЕТ: POVOD_VIDEN_V1.

БЕЗОПАСНОСТЬ: .bak_napom, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_napominanie_ruki.py --suho
    python postavit_napominanie_ruki.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "NAPOMINANIE_RUKI_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

STAROE = '''def _povod_blok(povod: str) -> str:'''

NOVOE = '''_RUKA_NAPOMINANIE = (
    "\\n— — —\\n"
    "РЕШИЛ — ЗОВИ РУКУ. Войти, подождать, подвинуть стоп, долить или "
    "закрыть можно ТОЛЬКО рукой otdat_prikaz. Сказать словами «вижу "
    "вход» или «жду» — не приказ: исполнитель слов не слышит, и в "
    "истории это останется разговором, а не делом. Не хочешь "
    "работать — тоже позови руку с WAIT, чтобы отказ был виден.\\n\\n")


def _povod_blok(povod: str) -> str:'''

HVOST_PRAVKI = [
    ('''        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Ничего не звенело — смотришь по просьбе. Скажи честно, "
                "что видишь сейчас.\\n\\n")''',
     '''        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Ничего не звенело — смотришь по просьбе. Скажи честно, "
                "что видишь сейчас.\\n" + _RUKA_NAPOMINANIE)'''),

    ('''        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Тебя разбудил разворотный бар — он на последнем закрытом "
                "баре и отмечен стрелкой на кадре. Ждать его не надо, он "
                "уже есть. Место это или передышка — смотри.\\n\\n")''',
     '''        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Тебя разбудил разворотный бар — он на последнем закрытом "
                "баре и отмечен стрелкой на кадре. Ждать его не надо, он "
                "уже есть. Место это или передышка — смотри.\\n"
                + _RUKA_NAPOMINANIE)'''),

    ('''        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Тебя разбудило место, которое стало видно только "
                "сейчас — оно позади, не на свежем баре. Смотри, что "
                "там.\\n\\n")''',
     '''        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Тебя разбудило место, которое стало видно только "
                "сейчас — оно позади, не на свежем баре. Смотри, что "
                "там.\\n" + _RUKA_NAPOMINANIE)'''),

    ('''    return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
            f"Тебя разбудило: {p}.\\n\\n")''',
     '''    return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
            f"Тебя разбудило: {p}.\\n" + _RUKA_NAPOMINANIE)'''),
]


def _pravka(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0
    if "POVOD_VIDEN_V1" not in txt:
        print(f"  {slot}: ОТКАЗ — сперва postavit_povod_vzglyada.py")
        return -1
    if txt.count(STAROE) != 1:
        print(f"  {slot}: ОТКАЗ — блок повода не нашёлся")
        return 0

    novy = txt.replace(STAROE, NOVOE, 1)
    postavleno = 0
    for staroe, novoe in HVOST_PRAVKI:
        if novy.count(staroe) == 1:
            novy = novy.replace(staroe, novoe, 1)
            postavleno += 1
    if not postavleno:
        print(f"  {slot}: ОТКАЗ — ни один ответ повода не опознан")
        return 0

    novy = novy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_napom"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'} "
          f"({postavleno} из {len(HVOST_PRAVKI)} поводов)")
    return 1


def main():
    print()
    print("РЕШИЛ — ЗОВИ РУКУ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    if not SLOTY.exists():
        print("!! слотов нет — запускать из корня репы")
        return
    vsego = 0
    for s in ("A06", "A07", "A08"):
        r = _pravka(s)
        if r < 0:
            return
        vsego += r
    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто мозгов: {vsego}. Бэкапы — .bak_napom")
    print("Напоминание стоит первым, там же, где повод.")
    print()


if __name__ == "__main__":
    main()
