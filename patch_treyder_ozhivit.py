# -*- coding: utf-8 -*-
# TREYDER_ZHIV_V1
"""
ОЖИВИТЬ ТРЕЙДЕРА — два стежка в каждом из трёх мозгов.

    python patch_treyder_ozhivit.py --suho    посмотреть, ничего не менять
    python patch_treyder_ozhivit.py           накатить

Запускать из КОРНЯ репо. Идемпотентно: накатанное второй раз не трогает.
Рядом с каждым файлом кладётся .bak_treyder_zhiv.

ЧТО ЧИНИМ

  1) ТРЕЙДЕР НЕ ОТРАБОТАЛ НИ РАЗУ.
     В мозге стояло:

         chat = _glaz(chat, symbol, timeframe, _SLOT)

     Имя `chat` пришло сверху файла (from llm import chat), но раз ему
     присваивают ВНУТРИ функции, Python считает его местным на всю
     функцию — и в тот же миг, когда его читают справа, оно ещё пустое.
     Каждый вызов падал с UnboundLocalError, ошибку глотал общий
     перехват, и наружу шло «не смог решить». Ни глаза, ни приборов,
     ни вердикта — трейдер не доходил до первого слова.

     Стало: обёртка кладётся в СВОЁ имя `_chat_glazami`, а `chat`
     остаётся тем, чем был. Второй заход (когда житель просит поднять
     память) тоже идёт через глаза — раньше замысел был тот же, просто
     до него не доживали.

  2) КОТИРОВКИ МИМО КРАНА И МИМО МАЯКА.
     Мозг лез в терминал напрямую:

         from mt5_feed import _terminal, _fetch
         bars, point = _fetch(mt5, symbol, timeframe, bars_count)

     Значит: тумблер РЕАЛ/ТЕСТЕР ему не указ (в тестере всё равно
     ломился в терминал), истоки его не видели, гнездо Маяка по нему
     не загоралось, а без терминала он честно отвечал «нет котировок».

     Стало: `feed_source.bars(...)` — та же дверь, в которую ходит
     кадр. Один кран на кадр и на трейдера.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
    Не трогает ни промпт, ни знания, ни стол, ни кабинет, ни найм.
    Только два стежка на файл. Инструмент и этаж по-прежнему приходят
    снаружи — это следующий шаг («Взгляд»).
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
MARKER = "# TREYDER_ZHIV_V1 - marker"
BAK = ".bak_treyder_zhiv"

# ── стежок 1: бары через общий источник ──────────────────────
STAROE_KRAN = '''    from mt5_feed import _terminal, _fetch
    mt5 = _terminal()
    if mt5 is None:
        return {"ok": False, "error": "MetaTrader5 не установлен в Python",
                "narrative": "", "signal": {}, "diary_entry": {},
                "stats": _load_stats(), "market": {}, "table": table}

    bars, point = _fetch(mt5, symbol, timeframe, bars_count)
'''

NOVOE_KRAN = '''    # TREYDER_ZHIV_V1: бары берём ОБЩИМ источником, а не из терминала
    # напрямую. Тогда трейдер живёт по тому же крану РЕАЛ/ТЕСТЕР, что и
    # кадр, а его запрос идёт через исток и виден в гнезде Маяка.
    from feed_source import bars as _source_bars
    bars, point = _source_bars(symbol, timeframe, bars_count)
'''

# ── стежок 2: глаз в своё имя ────────────────────────────────
STAROE_GLAZ = "        chat = _glaz(chat, symbol, timeframe, _SLOT)\n"
NOVOE_GLAZ = ("        # TREYDER_ZHIV_V1: обёртка в СВОЁ имя. Присваивание в `chat`\n"
              "        # делало его местным на всю функцию — вызов падал всегда.\n"
              "        _chat_glazami = _glaz(chat, symbol, timeframe, _SLOT)\n")

STAROE_ZOV = "        response = chat(system=system_full, user=user_msg, knowledge=knowledge,\n"
NOVOE_ZOV = "        response = _chat_glazami(system=system_full, user=user_msg, knowledge=knowledge,\n"

STAROE_PAMYAT = """        if _zapros:
            response = chat(
                system=system_full,
"""
NOVOE_PAMYAT = """        if _zapros:
            response = _chat_glazami(
                system=system_full,
"""

STEZHKI = (
    ("бары через общий источник", STAROE_KRAN, NOVOE_KRAN),
    ("глаз в своё имя", STAROE_GLAZ, NOVOE_GLAZ),
    ("вызов через глаз", STAROE_ZOV, NOVOE_ZOV),
    ("второй заход через глаз", STAROE_PAMYAT, NOVOE_PAMYAT),
)


def proverit_python(tekst: str, imya: str) -> bool:
    """Синтаксис и компиляция. Не прошло — на диск не пишем."""
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"    ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vremenny = f.name
    try:
        py_compile.compile(vremenny, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"    ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vremenny).unlink(missing_ok=True)


def obrabotat(put: Path, suho: bool) -> str:
    """Один мозг. Возвращает: 'нет' | 'уже' | 'готово' | 'сбой'."""
    if not put.exists():
        print(f"  {put.parent.name}: мозга нет — вакансия, пропускаю")
        return "нет"

    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {put.parent.name}: уже накатано")
        return "уже"

    ne_nashlos = []
    for imya, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n == 0:
            ne_nashlos.append(imya)
            continue
        if n > 1:
            print(f"    ✗ {put.parent.name}: «{imya}» встречается {n} раз — "
                  f"якорь неточен, файл не трогаю")
            return "сбой"
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {imya} — заменено")

    if ne_nashlos:
        print(f"    ✗ {put.parent.name}: не нашёл якоря: "
              f"{', '.join(ne_nashlos)} — файл не трогаю")
        return "сбой"

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"

    if not proverit_python(tekst, put.parent.name):
        return "сбой"

    if suho:
        print(f"  {put.parent.name}: ✓ готов к накатке (сухой прогон)")
        return "готово"

    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {put.parent.name}: ✓ накатано (копия рядом: *{BAK})")
    return "готово"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true",
                    help="показать, но ничего не писать")
    a = ap.parse_args()

    if not SLOTY.exists():
        print("✗ не вижу слоты торгового_хаоса — запускай из КОРНЯ репо")
        return 1

    print("═" * 56)
    print("ОЖИВИТЬ ТРЕЙДЕРА" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 56)

    itogi = {}
    for slot in SLOTS:
        itogi[slot] = obrabotat(SLOTY / slot / "мозг.py", a.suho)

    print("─" * 56)
    sboi = [s for s, v in itogi.items() if v == "сбой"]
    if sboi:
        print(f"⚠ не тронуты: {', '.join(sboi)} — якоря разошлись, "
              f"покажи мне эти файлы")
        return 1
    if a.suho:
        print("Сухой прогон прошёл. Накатывать: "
              "python patch_treyder_ozhivit.py")
    else:
        print("Готово. Проверить, не зовя модель:")
        print("    python stol_pokazat.py EURUSD H1")
        print("Потом в кабинете жми РЫНОК — трейдер должен ответить "
              "словами, а не «не смог решить».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
