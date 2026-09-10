# -*- coding: utf-8 -*-
# POVOD_VIDEN_V1 — трейдер знает, почему смотрит
"""
ПОВОД ДОХОДИТ ДО ТРЕЙДЕРА

БЕДА. Город считает повод взгляда — разворотный бар на таком-то
баре, излом, заявка, вход, закрытие — и печатает его В ЛОГ:

    [КЛЮЧ] 🔑 A06: разворотный бар BULL @ 6.70292

А трейдеру не говорит НИЧЕГО. Он открывает глаза и не знает, звонило
что-нибудь или его просто спросили. Отсюда сочинение, пойманное
Шефом 10.09: «жду, пока сложится разворотный бар» — при том, что
именно этот бар его и разбудил.

Слово Шефа: «пусть честно ситуацию говорит всегда — вот что есть, то
и говорит, не важно, как он проснулся».

ЧТО ДЕЛАЕТ ПАТЧ:

 1. `Биржа/council.py` — повод едет вместе с инструментом и этажом,
    а не остаётся в логе.

 2. Мозги A06/A07/A08 — принимают повод и кладут его в первое
    сообщение отдельной строкой, ПЕРЕД тем, что на руках:

        === ПОЧЕМУ ТЫ СМОТРИШЬ ===
        Тебя разбудило: разворотный бар BULL @ 6.70292.
        Он уже случился — ждать его не надо.

    Повода нет (спросили просто так) — так и написано, честно:
    ничего не звенело, смотришь по просьбе.

ЧЕГО НЕ ТРОГАЕТ: сам ключ пробуждения, кто когда будится, бумагу,
руки. Только доставку факта.

БЕЗОПАСНОСТЬ: старые вызовы мозга без повода продолжают работать
(значение по умолчанию пустое), .bak_povod, идемпотентен, синтаксис
до записи, `--suho` не трогает диск.

    python postavit_povod_vzglyada.py --suho
    python postavit_povod_vzglyada.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "POVOD_VIDEN_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
COUNCIL = _REPO / "Биржа" / "council.py"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

RUN = {"A06": "run_brut", "A07": "run_avan", "A08": "run_cons"}

# ── council: повод едет с вызовом ────────────────────────────
STAROE_CALL = '''        r = _call(ceh, slot, fn,
                  symbol=_p["symbol"], timeframe=_p["timeframe"])'''
NOVOE_CALL = '''        # POVOD_VIDEN_V1: повод больше не остаётся в логе — трейдер
        # должен знать, что именно его разбудило. Иначе он сочиняет
        # себе ожидание бара, который уже случился.
        r = _call(ceh, slot, fn,
                  symbol=_p["symbol"], timeframe=_p["timeframe"],
                  povod=_k.get("почему", ""))'''

# ── мозг: принимает повод ────────────────────────────────────
STARAYA_SIGNATURA = '''def {RUN}(symbol: str = "XAUUSD", timeframe: str = "H4",
             bars_count: int = 300) -> dict:'''
NOVAYA_SIGNATURA = '''def {RUN}(symbol: str = "XAUUSD", timeframe: str = "H4",
             bars_count: int = 300, povod: str = "") -> dict:'''

YAKOR_STOL = '        + "=== ЧТО У ТЕБЯ НА РУКАХ ===\\n"'
VSTAVKA_STOL = '        + _povod_blok(povod)      # POVOD_VIDEN_V1\n' + YAKOR_STOL

TELO = '''

# ── POVOD_VIDEN_V1: почему он смотрит ─────────────────────────
# Город и раньше знал повод — считал его в ключе пробуждения и писал
# в лог. Трейдеру не доставалось ничего, и он открывал глаза вслепую.
# Разницы между «разбудили» и «спросили» для его работы нет: вопрос
# один и тот же — что сейчас на рынке. Но повод — это факт, и он
# должен его знать, а не додумывать.

def _povod_blok(povod: str) -> str:
    """Факт повода — без цены и без стороны.

    Прибор знает и цену бара, и его направление. Ни то, ни другое
    трейдеру не сообщается: цену мы только что убрали из его
    рассказа, а сторона — это его работа. Сказать «разворотный бар
    BULL» значит назвать направление ЗА него, до того как он
    посмотрел на график. Сторону он берёт с хода, который обвёл сам,
    а не с бара.

    Свои дела — заявка, вход, закрытие — идут как есть: там числа
    его собственные, а не подсказка про рынок.
    """
    p = (povod or "").strip()
    if not p:
        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Ничего не звенело — смотришь по просьбе. Скажи честно, "
                "что видишь сейчас.\\n\\n")
    if "разворотный бар" in p:
        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Тебя разбудил разворотный бар — он на последнем закрытом "
                "баре и отмечен стрелкой на кадре. Ждать его не надо, он "
                "уже есть. Место это или передышка — смотри.\\n\\n")
    if "излом" in p:
        return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
                "Тебя разбудило место, которое стало видно только "
                "сейчас — оно позади, не на свежем баре. Смотри, что "
                "там.\\n\\n")
    return ("=== ПОЧЕМУ ТЫ СМОТРИШЬ ===\\n"
            f"Тебя разбудило: {p}.\\n\\n")


# POVOD_VIDEN_V1 - marker
'''


def _pravka_council() -> int:
    if not COUNCIL.exists():
        print("  council.py: файла нет")
        return 0
    txt = COUNCIL.read_text(encoding="utf-8")
    if MARKER in txt:
        print("  council.py: уже стоит")
        return 0
    if txt.count(STAROE_CALL) != 1:
        print(f"  council.py: ОТКАЗ — якорь встречается "
              f"{txt.count(STAROE_CALL)} раз(а)")
        return 0
    novy = txt.replace(STAROE_CALL, NOVOE_CALL, 1)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  council.py: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(COUNCIL, COUNCIL.with_suffix(".py.bak_povod"))
        COUNCIL.write_text(novy, encoding="utf-8")
    print(f"  council.py: {'готов' if SUHO else 'поправлен'}")
    return 1


def _pravka_mozga(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}/мозг.py: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}/мозг.py: уже стоит")
        return 0

    staraya = STARAYA_SIGNATURA.replace("{RUN}", RUN[slot])
    novaya = NOVAYA_SIGNATURA.replace("{RUN}", RUN[slot])
    if txt.count(staraya) != 1:
        print(f"  {slot}/мозг.py: ОТКАЗ — сигнатура {RUN[slot]} не найдена")
        return 0
    if txt.count(YAKOR_STOL) != 1:
        print(f"  {slot}/мозг.py: ОТКАЗ — якорь стола встречается "
              f"{txt.count(YAKOR_STOL)} раз(а)")
        return 0

    novy = txt.replace(staraya, novaya, 1)
    novy = novy.replace(YAKOR_STOL, VSTAVKA_STOL, 1)
    novy = novy.rstrip("\n") + "\n" + TELO

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}/мозг.py: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_povod"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}/мозг.py: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("ПОВОД ВЗГЛЯДА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    if not SLOTY.exists():
        print("!! слотов нет — запускать из корня репы")
        return

    print("1. СОВЕТ — повод едет с вызовом:")
    vsego = _pravka_council()

    print()
    print("2. МОЗГИ — повод в первом сообщении:")
    for s in ("A06", "A07", "A08"):
        vsego += _pravka_mozga(s)

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_povod")
    print("Теперь он знает, звонило что-то или его просто спросили.")
    print()


if __name__ == "__main__":
    main()
