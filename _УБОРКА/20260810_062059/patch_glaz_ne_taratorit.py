# -*- coding: utf-8 -*-
# GLAZ_NE_TARATORIT_V1
"""
ГЛАЗ ПЕРЕСТАЁТ ТАРАТОРИТЬ. Спросил про скорость света — получи про свет.

    python patch_glaz_ne_taratorit.py --suho    посмотреть
    python patch_glaz_ne_taratorit.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копии рядом: .bak_glaz.

ЧТО НАШЛОСЬ (и это моя вина)

    Ты спросил: «нина, какова скорость света». Она сперва выдала абзац
    про Аллигатора и AO, и только последней строкой ответила про
    299 792 километра в секунду.

    Причина не в модели и не в ней. К КАЖДОМУ твоему сообщению в
    разговоре приклеивается команда глаза:

        «СПЕРВА ПОСМОТРИ на картинку своими глазами: что здесь
         происходит? Не по списку — как рассказал бы человеку...»

    Эта команда правильная для РАБОТЫ: там её дело — смотреть на рынок,
    и смотреть первым делом. Но я приклеил её и к разговору. Что бы ты
    ни спросил — сперва отчёт по графику. Хоть про свет, хоть про
    погоду.

ЧТО СТАНОВИТСЯ

    В работе всё как было: сперва глаз, потом приборы.

    В разговоре подводка другая: кадр перед тобой — тот же, что у Шефа;
    спросили про рынок — смотри и отвечай по нему; спросили не про
    рынок — просто отвечай на вопрос, пересказывать график не надо.

    Картинку не отбираем — отбираем обязанность про неё говорить.

ЧТО ЭТО НЕ ЧИНИТ

    Разнобой в описании одного бара («зубы разошлись» в отчёте и
    «переплетены» в чате) — отдельная беда, и она про зрение модели.
    Опыт с переключением модели всё ещё стоит провести.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
SLOTS = ("A06", "A07", "A08")
MARKER = "# GLAZ_NE_TARATORIT_V1 - marker"
BAK = ".bak_glaz"

# ── 1. вторая подводка — для разговора ────────────────────────
STAROE_KONST = '''    "этом: глаз важнее, чем сойтись с цифрой.\\n\\n"
)
'''
NOVOE_KONST = '''    "этом: глаз важнее, чем сойтись с цифрой.\\n\\n"
)

# GLAZ_NE_TARATORIT_V1: в РАЗГОВОРЕ подводка другая. Прежняя велела
# сперва пересказать картинку — и на вопрос о скорости света шёл абзац
# про Аллигатора. Кадр оставляем, обязанность говорить о нём — снимаем.
_GLAZ_RAZGOVOR = (
    "Перед тобой кадр того рынка, на который ты сейчас смотришь — "
    "тот же самый, что видит Шеф.\\n"
    "Спрашивают про рынок — смотри на него и отвечай по нему, а не проси "
    "прислать данные.\\n"
    "Спрашивают НЕ про рынок — просто отвечай на вопрос. Пересказывать "
    "график при этом не надо: тебя спросили не о нём.\\n\\n"
)
'''

# ── 2. глаз умеет принять свою подводку ───────────────────────
STAROE_DEF = '''def _glaz(_chat, symbol, timeframe, slot):
'''
NOVOE_DEF = '''def _glaz(_chat, symbol, timeframe, slot, preambula=None):
'''

STAROE_ZOV = '''                    system=system, user_text=_GLAZ_PREAMBULA + user,
'''
NOVOE_ZOV = '''                    system=system,
                    user_text=(preambula if preambula is not None
                               else _GLAZ_PREAMBULA) + user,
'''

# ── 3. в разговоре берём разговорную подводку ─────────────────
STAROE_CHAT = '''        _chat_fn = _glaz(chat, _sym, _tf, _SLOT) if (_sym and _tf) else chat
'''
NOVOE_CHAT = '''        # GLAZ_NE_TARATORIT_V1: в разговоре — разговорная подводка.
        _chat_fn = (_glaz(chat, _sym, _tf, _SLOT, preambula=_GLAZ_RAZGOVOR)
                    if (_sym and _tf) else chat)
'''

STEZHKI = (
    ("подводка для разговора", STAROE_KONST, NOVOE_KONST),
    ("глаз принимает подводку", STAROE_DEF, NOVOE_DEF),
    ("подводка подставляется", STAROE_ZOV, NOVOE_ZOV),
    ("разговор берёт свою", STAROE_CHAT, NOVOE_CHAT),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("=" * 58)
    print("ГЛАЗ НЕ ТАРАТОРИТ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("=" * 58)

    if not SLOTY.exists():
        print("x не вижу слоты — запускай из КОРНЯ репо")
        return 1

    vse_ok = True
    for slot in SLOTS:
        put = SLOTY / slot / "мозг.py"
        if not put.exists():
            print(f"  {slot}: мозга нет — пропускаю")
            continue
        tekst = put.read_text(encoding="utf-8")
        if MARKER in tekst:
            print(f"  {slot}: уже накатано")
            continue
        sboy = False
        for nazv, staroe, novoe in STEZHKI:
            n = tekst.count(staroe)
            if n != 1:
                print(f"  x {slot}: якорь «{nazv}» найден {n} раз — не трогаю")
                sboy = True
                vse_ok = False
                break
            tekst = tekst.replace(staroe, novoe, 1)
            print(f"    · {nazv}")
        if sboy:
            continue
        tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
        if not proverit_python(tekst, slot):
            vse_ok = False
            continue
        if a.suho:
            print(f"  {slot}: + готов")
            continue
        shutil.copy2(put, put.with_suffix(put.suffix + BAK))
        put.write_text(tekst, encoding="utf-8")
        print(f"  {slot}: + накатано")

    print("-" * 58)
    if not vse_ok:
        return 1
    if a.suho:
        print("Сухой прогон прошёл. Накатывать: "
              "python patch_glaz_ne_taratorit.py")
        return 0
    print("Спроси её опять про скорость света — должна ответить про свет,")
    print("и ни слова про Аллигатора. Спроси про рынок — должна смотреть.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
