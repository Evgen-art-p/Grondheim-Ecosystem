# -*- coding: utf-8 -*-
# STOL_I_GLAZ_V1
"""
СТОЛ КОДОМ + ГЛАЗ — во все три мозга разом.

    python postavit_stol_i_glaz.py --suho     посмотреть
    python postavit_stol_i_glaz.py            сделать

Запускать из КОРНЯ репо, после nastroit_birzhu.py.

ЗАЧЕМ
    Сенсоры уехали в архив, а мозги трейдеров по-прежнему ждут их
    показаний с шины. Стол не падает — читалка подставляет пустые
    словари, — но половина мест за ним пустая: нет компаса, нет
    разворотного бара, нет фазы объёма, нет фрактала за пастью.

ЧТО СТАВИТ, две правки на каждый мозг:

    1. СТОЛ КОДОМ. Вместо «прочитать шину» — «накрыть себе стол».
       Считает `Биржа/stol.py` теми же именами полей, что клали
       сенсоры: мозг подмены не замечает.

    2. ГЛАЗ. К запросу прикрепляется кадр — тот же PNG, что видит Шеф
       в кабинете. И в запросе прямо сказано: сперва посмотри
       глазами, приборы потом. Порядок Шефа: «глянуть, увидеть
       паттерн и работать; не увидел — не работает».

ЧЕГО НЕ ТРОГАЕТ
    Дневник, ведение позиции, вердикт, статистику, характер роли —
    всё остаётся как есть. Это годы налаженного.

ОТКАТ
    Рядом с каждым мозгом ложится `.bak_stol_i_glaz`. Не пошло —
    вернул файл, и всё как было.
"""
import argparse
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "STOL_I_GLAZ_V1"
KOREN = Path(__file__).resolve().parent
BIRZHA = KOREN / "Биржа"
CEHA = KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха"

_SUHO = False

# ═══════════════════════════════════════════════════════════
# ПРАВКА 1 — стол накрывается кодом
# ═══════════════════════════════════════════════════════════
A1_OLD = '''    table = _read_table()
'''

A1_NEW = '''    # STOL_I_GLAZ_V1: стол накрывает КОД, а не сенсоры-голоса.
    # Сенсоры уехали в архив (решение Шефа 06.08), и ждать их больше
    # некого. Имена полей те же, что клали они, — ниже по файлу ничего
    # не меняется. Не собрался — вернётся пустой стол той же формы,
    # как и раньше при холодном старте.
    try:
        import stol as _stol
        table = _stol.nakryt(symbol, timeframe, self_key=_SELF_KEY)
    except Exception as _e_stol:
        print(f"[СТОЛ] ⚠️  не накрылся ({_e_stol}) — читаю шину как раньше")
        table = _read_table()
'''

# ═══════════════════════════════════════════════════════════
# ПРАВКА 2 — глаз: кадр к запросу
# ═══════════════════════════════════════════════════════════
A2_OLD = '''        response = chat(system=system_full, user=user_msg, knowledge=knowledge,'''

A2_NEW = '''        # STOL_I_GLAZ_V1 — ГЛАЗ. Порядок Шефа: сперва посмотреть,
        # приборы потом. Сам вызов не трогаем — подменяем функцию
        # обёрткой, которая рисует кадр и уходит в зрение. Кадра нет —
        # обёртка честно зовёт прежнее, и мозг ничего не замечает.
        chat = _glaz(chat, symbol, timeframe, _SLOT)
        response = chat(system=system_full, user=user_msg, knowledge=knowledge,'''

# ── шапка, которую вставляем в мозг ──────────────────────────
SHAPKA_TPL = '''
# ════════════════════════════════════════════════════════════
# STOL_I_GLAZ_V1 — глаз роли
# ════════════════════════════════════════════════════════════
_SLOT = "{slot}"
_SELF_KEY = "{self_key}"

_GLAZ_PREAMBULA = (
    "СПЕРВА ПОСМОТРИ на картинку своими глазами: что здесь происходит? "
    "Не по списку — как рассказал бы человеку, который стоит рядом. "
    "Работы не видишь — так и скажи, это законный и самый частый ответ.\\n"
    "Приборы ниже — ВТОРЫМ шагом, чтобы уточнить то, что ты уже "
    "разглядел. Если прибор говорит не то, что видит глаз, скажи об "
    "этом: глаз важнее, чем сойтись с цифрой.\\n\\n"
)


def _glaz(_chat, symbol, timeframe, slot):
    """Обёртка над вызовом модели: подкладывает кадр.

    Кадр — тот же PNG, что Шеф видит в кабинете: смотрят на одну
    картинку, иначе проверить роль нечем. Не нарисовался или зрение
    не сработало — честно зовём прежний вызов, без глаз.
    """
    def obertka(system="", user="", knowledge="", **kw):
        put = None
        try:
            import grafik
            put = grafik.kadr(symbol, timeframe)
        except Exception as e:
            print(f"[КАДР] не нарисовался ({{e}}) — работаю без глаз")
        if put:
            try:
                import base64
                from pathlib import Path as _P
                from llm import chat_with_images
                return chat_with_images(
                    system=system, user_text=_GLAZ_PREAMBULA + user,
                    knowledge=knowledge,
                    images=[{{"base64": base64.b64encode(
                                 _P(put).read_bytes()).decode("ascii"),
                              "mime_type": "image/png",
                              "name": _P(put).name}}],
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))
            except Exception as e:
                print(f"[ГЛАЗ] зрение не сработало ({{e}}) — иду по числам")
        return _chat(system=system, user=user, knowledge=knowledge, **kw)
    return obertka

'''


def _agent_id(src: str) -> str:
    """Как роль зовёт себя в вызове модели — берём из самого файла."""
    i = src.find('agent_id="')
    if i < 0:
        return '"неизвестный"'
    j = src.find('"', i + 10)
    return '"' + src[i + 10:j] + '"'


def pravit(mozg: Path) -> str:
    src = mozg.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже"
    if src.count(A1_OLD) != 1 or src.count(A2_OLD) != 1:
        return "мимо"
    # отступ якоря обязан совпадать с отступом строки в файле, иначе
    # замена сработает по ХВОСТУ отступа и развалит блок (уже ловил)
    _i = src.find(A2_OLD)
    if _i > 0 and src[_i - 1] not in "\n":
        return "мимо: отступ якоря не совпал"

    slot = mozg.parent.name
    shapka = SHAPKA_TPL.format(slot=slot, self_key=slot.lower())

    novyy = src.replace(A1_OLD, A1_NEW, 1).replace(A2_OLD, A2_NEW, 1)
    # шапку кладём сразу после импортов — перед первым определением
    i = novyy.find("\ndef ")
    if i < 0:
        return "мимо"
    novyy = novyy[:i] + shapka + novyy[i:]

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        return f"ошибка: {e}"
    if _SUHO:
        return "ок"

    bak = mozg.with_suffix(".py.bak_stol_i_glaz")
    if not bak.exists():
        shutil.copy2(mozg, bak)
    mozg.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(mozg), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, mozg)
        return f"ошибка: py_compile — {e}"
    return "ок"


def main() -> int:
    global _SUHO
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()
    _SUHO = a.suho

    if not BIRZHA.exists() or not CEHA.exists():
        print("✗ это не корень репо")
        return 1

    print("═" * 56)
    print("СТОЛ КОДОМ + ГЛАЗ" + ("   [СУХОЙ ПРОГОН]" if _SUHO else ""))
    print("═" * 56)

    if not (BIRZHA / "stol.py").exists():
        print("\n✗ нет Биржа/stol.py — положи его туда, без него правка "
              "бессмысленна")
        return 1
    if not (BIRZHA / "grafik.py").exists():
        print("\n⚠ нет Биржа/grafik.py — глаз работать не будет, "
              "мозг честно скажет «без глаз» и пойдёт по числам")

    print()
    itogo = {"ок": 0, "уже": 0, "мимо": 0}
    for mozg in sorted(CEHA.glob("*/слоты/*/мозг.py")):
        rez = pravit(mozg)
        slot = mozg.parent.name
        if rez.startswith("ошибка"):
            print(f"  ✗ {slot}: {rez}")
            return 1
        itogo[rez] = itogo.get(rez, 0) + 1
        if rez != "мимо":
            print(f"  {'·' if rez == 'ок' else '='} {slot} — {rez}")

    print(f"\n✓ поправлено {itogo['ок']}, уже стояло {itogo['уже']}, "
          f"без этих строк {itogo['мимо']}")
    if _SUHO:
        print("\nЭто был сухой прогон. Запусти без --suho.")
    else:
        print("\nРядом с каждым мозгом лежит .bak_stol_i_glaz — откат в один шаг.")
        print("\nПроверить стол БЕЗ модели и без денег, из корня:")
        print("    python Биржа/stol.py EURUSD H1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
