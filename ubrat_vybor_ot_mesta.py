# -*- coding: utf-8 -*-
"""
ubrat_vybor_ot_mesta.py   ·   MARKER: VYBOR_NE_PRI_MESTE_V1

ДВА СЛОВА ШЕФА, ОДНО ЗА ДРУГИМ
------------------------------
1. «Пустое место будится — неверно это.»
   В логе: точка родилась по XAUUSD, ключ открылся, позвали A07 —
   а A07 вакансия. Потому что инструмент лежит в ПОСТЕ места и
   остаётся там, когда человек ушёл, а этаж без жителя подставлялся
   «от комфорта». Место без человека выглядело готовым и тянуло за
   собой чужой рынок: лишняя математика каждый бар и чужая точка ноль
   в общем столе цеха.

2. «Убери вообще выбор трейдера и влияние на место — движок единый,
   решает только трейдер.»
   Выбор входа перестаёт быть настройкой, которую читает движок.
   Точка, волна, откат, попытки, ведение лежат в hooks/council/столе
   одинаково для всех. Что из этого его — человек решает на баре,
   глядя на стол, а не по заранее объявленной метке.

ЧТО ДЕЛАЕМ
----------
  A. Биржа/vybor.py    · rabota_dlya: место без человека не готово;
                         паттерн из готовности убран совсем — он там
                         больше не читается и не возвращается.
  B. Биржа/council.py  · молчание пустого места объявляется до того,
                         как Совет полезет судить его рынок.
  C. три мозга         · блок «=== ТВОЙ ВЫБОР ВХОДА ===» снят и из
                         работы, и из разговора. Вместе с ним уходит
                         строка «не твоё место входа — пас, и так и
                         скажи» — это и был приказ, делавший бота.

ЧЕГО НЕ ТРОГАЕМ
---------------
  · Метки жителей. Что человек сказал и когда — его память, и она
    и дальше доезжает до него обычным путём, через душу носителя.
    Просто движок ею больше не распоряжается.
  · Ловилку строки «ВЫБОР: …» в кабинете. Сказал — записали в память.
    Записать сказанное это не влияние, это память. Скажешь снять —
    сниму отдельной строкой.
  · Вкладку ВЫБОР на Странице Работы — это смотрелец, не механизм.
  · Инструменты в постах пустых мест: пусть лежат, место их снова
    возьмёт, когда на него сядет человек.

Идемпотентен, кладёт `.bak_vybornepri_ГГГГММДД_ЧЧММСС`.

  py -3 ubrat_vybor_ot_mesta.py            — сделать
  py -3 ubrat_vybor_ot_mesta.py --suho     — только показать
"""

import ast
import re
import sys
import time
from pathlib import Path

MARKER = "VYBOR_NE_PRI_MESTE_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ─────────────────────── A. vybor.py ───────────────────────

VYBOR_STAROE = '''    # RABOTA_PO_PARE_V1: слово Шефа — «выбрал если инструмент и
    # паттерн, то пусть работает». Значит готовность стоит на трёх
    # ногах, и паттерн (место входа) — такая же нога, как инструмент.
    pattern = (chitat(ceh, slot).get("текст") or "").strip()'''

VYBOR_NOVOE = '''    # VYBOR_NE_PRI_MESTE_V1: паттерна тут больше нет вовсе. Он стоял
    # ногой готовности («выбрал инструмент и паттерн — работай»), потом
    # был снят из готовности, но продолжал читаться и ездить с парой.
    # Слово Шефа: движок единый, выбор входа месту не подчинён и месту
    # не сообщается. Что человек считает своим — он говорит на баре.
    pattern = ""'''

VYBOR_GOTOV_STAROE = '''    return {"инструмент": instr, "этаж": etazh, "паттерн": pattern,
            "откуда_инструмент": otk_i if instr else "",
            "откуда_этаж": otk_e,
            "готов": bool(instr and etazh)}'''

VYBOR_GOTOV_NOVOE = '''    # VYBOR_NE_PRI_MESTE_V1: место без человека НЕ работает. Инструмент
    # живёт в посте и остаётся там после увольнения, а этаж без жителя
    # подставлялся от комфорта — пустое место выглядело готовым, и
    # Совет судил по нему рынок и рождал точки, которые некому смотреть.
    # Вакансия — это не рабочая пара. Проверка стоит здесь, в одной
    # двери, чтобы кабинет, Совет, обход и исполнитель отвечали одно.
    if not kto_sidit(ceh, slot):
        return {"инструмент": instr, "этаж": etazh, "паттерн": "",
                "откуда_инструмент": otk_i if instr else "",
                "откуда_этаж": otk_e,
                "готов": False}
    return {"инструмент": instr, "этаж": etazh, "паттерн": pattern,
            "откуда_инструмент": otk_i if instr else "",
            "откуда_этаж": otk_e,
            "готов": bool(instr and etazh)}'''

VYBOR_MOLCHIT_STAROE = '''    if not r["инструмент"]:
        return "инструмент не задан и не выбран"
    # MESTO_BEZ_VYBORA_V1: без выбора место больше не молчит —
    # работает общим кодом. Строка оставлена на случай, если
    # готовность когда-нибудь снова свяжут с паттерном.
    return "рабочий этаж не выбран"   # OTPERET_V1: теперь почти не бывает'''

VYBOR_MOLCHIT_NOVOE = '''    if not kto_sidit(ceh, slot):
        return "место свободно — сажать некого"
    if not r["инструмент"]:
        return "инструмент не задан и не выбран"
    return "рабочий этаж не выбран"   # OTPERET_V1: теперь почти не бывает'''

KTO_SIDIT = '''

# VYBOR_NE_PRI_MESTE_V1 ─────────────────────────────────────────
def kto_sidit(ceh: str, slot: str) -> str:
    """Имя того, кто сидит на месте. Пусто — вакансия.

    Спрашиваем ту же единственную дверь, что и весь город:
    cartridge_registry.resolve_para. Второй правды о найме не заводим.
    Сбой чтения — считаем, что человек ЕСТЬ: пропустить взгляд из-за
    нашей ошибки хуже, чем лишний раз посчитать.
    """
    try:
        import cartridge_registry as _cr
        nos = _cr.resolve_para(ceh, slot)
    except Exception:
        return "?"
    if not nos:
        return ""
    if isinstance(nos, dict):
        return str(nos.get("имя") or nos.get("name") or "").strip() or "?"
    return str(getattr(nos, "имя", "") or getattr(nos, "name", "") or
               nos).strip() or "?"
'''


# ─────────────────────── B. council.py ───────────────────────

COUNCIL_STAROE = '''        if not _p["готов"]:
            print(f"[СОВЕТ] 🤐 {_slot} молчит: {_p['почему']}")'''

COUNCIL_NOVOE = '''        if not _p["готов"]:
            # VYBOR_NE_PRI_MESTE_V1: сюда попадает и пустое место —
            # и попадает ДО того, как рынок будет рассужен его парой.
            # Раньше вакансия с инструментом из поста доводила дело до
            # ключа и падала уже в мозге («носителя нет»), успев
            # посчитать чужой рынок и родить точку в общем столе.
            print(f"[СОВЕТ] 🤐 {_slot} молчит: {_p['почему']}")'''


# ─────────────────────── C. мозги ───────────────────────

# Комментарий над блоком у каждого свой, поэтому ловим сам блок, а
# заодно снимаем предшествующие ему строки-пояснения — иначе следующий
# читатель найдёт объяснение того, чего в файле уже нет.
MOZG_BLOK = re.compile(
    r"[ \t]*#[^\n]*\n"                       # ноль и больше строк комментария
    r"(?:[ \t]*#[^\n]*\n)*"
    r"[ \t]*try:\n"
    r"[ \t]*from vybor import blok_dlya_prompta as _vybor_blok\n"
    r"[ \t]*(?:work_ctx|system_full) \+= _vybor_blok\(_CEH, _SLOT\)\n"
    r"[ \t]*except Exception:\n"
    r"[ \t]*pass\n"
)

MOZG_NOVOE = (
    "    # VYBOR_NE_PRI_MESTE_V1: блок «ТВОЙ ВЫБОР ВХОДА» снят — и из\n"
    "    # работы, и из разговора. Он подставлялся отдельно от прочей\n"
    "    # памяти и стоял приказом: «работаешь по нему, не твоё место\n"
    "    # входа — пас». Движок единый: точка, волна, откат, попытки и\n"
    "    # ведение считаются одинаково для всех, а что из этого его\n"
    "    # момент — человек решает на баре, глядя на стол. Что он\n"
    "    # считает своим, он и так помнит: метки доезжают обычным\n"
    "    # путём, через душу носителя.\n"
)


# ─────────────────────── механика ───────────────────────

def nayti_koren() -> Path:
    for k in (Path(__file__).resolve().parent, Path.cwd()):
        for p in [k, *k.parents]:
            if (p / "GRONDHEIM_CITY").is_dir() and (p / "Биржа").is_dir():
                return p
    print("Не нашёл корень репозитория (нужны папки GRONDHEIM_CITY и Биржа).")
    zhdat_i_vyyti(1)


def pravit_mozg(put: Path) -> str:
    """В мозге ловим блок выбора регуляркой: комментарий над ним у
    каждого свой, а сам блок дословно одинаковый."""
    text = put.read_text(encoding="utf-8")
    if MARKER in text:
        return "уже"
    novyy, skolko = MOZG_BLOK.subn(MOZG_NOVOE, text)
    if skolko != 2:
        return f"мимо: блоков выбора нашлось {skolko}, а должно быть 2"
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        return f"мимо: правка ломает синтаксис ({e.lineno}: {e.msg})"
    if SUHO:
        return "сделано (сухой прогон)"
    put.with_name(put.name + f".bak_vybornepri_{SHTAMP}").write_text(
        text, encoding="utf-8")
    put.write_text(novyy, encoding="utf-8")
    return "сделано"


def pravit(put: Path, zameny, dopisat: str = "") -> str:
    if not put.is_file():
        return "мимо: файла нет"
    text = put.read_text(encoding="utf-8")
    if MARKER in text:
        return "уже"

    ne_nashlos = [s for s, _ in zameny if s not in text]
    if ne_nashlos:
        return f"мимо: не нашёл якорь «{ne_nashlos[0].strip().splitlines()[0][:52]}…»"

    novyy = text
    for staroe, novoe in zameny:
        novyy = novyy.replace(staroe, novoe, 1)
    if dopisat:
        novyy = novyy.rstrip("\n") + "\n" + dopisat
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        return f"мимо: правка ломает синтаксис ({e.lineno}: {e.msg})"

    if SUHO:
        return "сделано (сухой прогон)"
    put.with_name(put.name + f".bak_vybornepri_{SHTAMP}").write_text(
        text, encoding="utf-8")
    put.write_text(novyy, encoding="utf-8")
    return "сделано"


def zhdat_i_vyyti(kod=0):
    try:
        input("\nEnter — закрыть окно...")
    except EOFError:
        pass
    sys.exit(kod)


def main():
    koren = nayti_koren()
    print(f"Корень города: {koren}")
    if SUHO:
        print("СУХОЙ ПРОГОН — ничего не записываю.\n")
    itogi = []

    print("\nДВИЖОК:")
    r = pravit(koren / "Биржа" / "vybor.py",
               [(VYBOR_STAROE, VYBOR_NOVOE),
                (VYBOR_GOTOV_STAROE, VYBOR_GOTOV_NOVOE),
                (VYBOR_MOLCHIT_STAROE, VYBOR_MOLCHIT_NOVOE)],
               dopisat=KTO_SIDIT)
    print(f"  {r:<24} Биржа/vybor.py")
    itogi.append(r)

    r = pravit(koren / "Биржа" / "council.py", [(COUNCIL_STAROE, COUNCIL_NOVOE)])
    print(f"  {r:<24} Биржа/council.py")
    itogi.append(r)

    sloty = sorted((koren / "GRONDHEIM_CITY" / "Биржа" / "цеха").glob(
        "*/слоты/*/мозг.py"))
    mozgi = [p for p in sloty
             if "blok_dlya_prompta" in p.read_text(encoding="utf-8")
             or MARKER in p.read_text(encoding="utf-8")]
    print(f"\nМОЗГИ ТРЕЙДЕРОВ — {len(mozgi)}:")
    for p in mozgi:
        r = pravit_mozg(p)
        print(f"  {r:<24} {p.relative_to(koren)}")
        itogi.append(r)

    sdelano = sum(1 for x in itogi if x.startswith("сделано"))
    uzhe = sum(1 for x in itogi if x == "уже")
    mimo = sum(1 for x in itogi if x.startswith("мимо"))
    print("\n" + "─" * 62)
    print(f"поправлено: {sdelano}   уже стояло: {uzhe}   не тронуто: {mimo}")
    print("─" * 62)
    if mimo:
        print("Что-то не нашлось — эти файлы НЕ тронуты вовсе, "
              "правки наугад не делаю. Покажи строку выше Брату.")

    print("""
ЧТО ПРОВЕРИТЬ ПОСЛЕ НАКАТКИ
  1. Подними город и нажми РЫНОК. В консоли должно быть:
       [СОВЕТ] 🤐 A07 молчит: место свободно — сажать некого
       [СОВЕТ] 🤐 A08 молчит: место свободно — сажать некого
     и НИ ОДНОЙ строки [CORE] _Point=0.01 (XAUUSD) — золото больше
     никто не считает.
  2. Илья на A06 должен будиться как раньше — по своему EURUSD.
  3. В его стопке блока «ТВОЙ ВЫБОР ВХОДА» больше нет. Метка цела,
     смотреть:  py -3 vybor_pokazat.py
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
