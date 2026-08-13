#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# INSTRUMENT_NAZNACHIT_ILI_SAM_V1
"""
ИНСТРУМЕНТ — можно назначить, можно оставить на выбор.

    python patch_instrument_treydera.py            посмотреть
    python patch_instrument_treydera.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).

СЛОВО ШЕФА

    «Не пришитый один свой, а на выбор: можно задать инструмент
    трейдеру, или он сам выберет».

КАК УСТРОЕНО

    Так же, как с местом входа. НАЗНАЧЕНИЕ — свойство МЕСТА: лежит в
    бланке должности, пишет его Шеф. ВЫБОР — свойство ЧЕЛОВЕКА: лежит
    меткой в его доме, объявляет его он сам.

    Старшинство:
      1. назначено в бланке места — работает по нему, это задание;
      2. не назначено, но взял свой — работает по своему;
      3. ни того ни другого — работает по кабинетному, и его просят
         выбрать. Не захочет — это тоже честно.

    Берёт он его словом, как и место входа:

        ИНСТРУМЕНТ: GBPUSD

    Кабинет ловит строку и кладёт метку ему в дом. Передумал — сказал
    ещё раз, старая остаётся в истории.

ГДЕ НАЗНАЧАТЬ

    Страница Работы → место → поле «Инструмент (пусто — выберет сам)».
    Оставил пустым — человек сам себе хозяин.

ЧТО ЭТО МЕНЯЕТ В РАБОТЕ

    Кабинет по-прежнему открывает Совет на том, что выбрано на полке.
    Но трейдер со своим инструментом работает по СВОЕМУ: накрывает
    свой стол, спускается по своим этажам, называет свои цены. В
    чёрном окне это видно строкой «инструмент такой-то вместо
    кабинетного такого-то».
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
VYBOR = KOREN / "Биржа" / "vybor.py"
RABOTA = KOREN / "ГОРОД" / "rabota.py"
STRANICA = KOREN / "ГОРОД" / "ui_rabota.py"
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
MARKER = "# INSTRUMENT_NAZNACHIT_ILI_SAM_V1 - marker"
BAK = ".bak_instrument"

DOBAVKA = '\n\n# ══════════════════════════════════════════════════════════════\n# ИНСТРУМЕНТ (INSTRUMENT_NAZNACHIT_ILI_SAM_V1)\n# ══════════════════════════════════════════════════════════════\n# Слово Шефа: не приколоченный, а на выбор — можно задать трейдеру\n# инструмент, а можно оставить пустым, и тогда он выберет сам.\n#\n# Устройство то же, что с местом входа: НАЗНАЧЕНИЕ — свойство МЕСТА\n# (лежит в бланке должности, его пишет Шеф), ВЫБОР — свойство\n# ЧЕЛОВЕКА (лежит меткой в его доме, его объявляет он).\n#\n# Порядок старшинства:\n#   1. назначено в бланке места  → работает по нему, это задание;\n#   2. не назначено, но выбрал сам → работает по своему выбору;\n#   3. ни того ни другого → работает по тому, что дал кабинет,\n#      и его просят выбрать.\nPATTERN_INSTR = "выбор_инструмента"\nSLOVO_INSTR = "ИНСТРУМЕНТ:"\n\n\ndef instrument_mesta(ceh: str, slot: str) -> str:\n    """Что назначено месту в бланке должности. Пусто — не назначено."""\n    try:\n        import sys as _s\n        from pathlib import Path as _P\n        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")\n        if _g not in _s.path:\n            _s.path.insert(0, _g)\n        import rabota as _rab\n        for m in _rab.mesta():\n            if m.get("цех") == ceh and m.get("слот") == slot:\n                d = _rab.chitat(m["id"]) or {}\n                return (d.get("инструмент") or "").strip().upper()\n    except Exception:\n        pass\n    return ""\n\n\ndef instrument_zhitelya(ceh: str, slot: str) -> dict:\n    """Что выбрал сам житель. Нет метки — пустой словарь."""\n    d, _ = _dvizhok_zhitelya(ceh, slot)\n    if d is None:\n        return {}\n    try:\n        moi = [m for m in d.metki() if m.get("паттерн") == PATTERN_INSTR]\n    except Exception:\n        return {}\n    if not moi:\n        return {}\n    moi.sort(key=lambda x: str(x.get("когда", "")))\n    return moi[-1]\n\n\ndef instrument_dlya(ceh: str, slot: str, zapasnoy: str = "") -> tuple:\n    """(инструмент, откуда) — по старшинству: место → человек → кабинет."""\n    naznachen = instrument_mesta(ceh, slot)\n    if naznachen:\n        return naznachen, "назначен"\n    svoy = (instrument_zhitelya(ceh, slot).get("текст") or "").strip().upper()\n    if svoy:\n        return svoy, "выбрал сам"\n    return (zapasnoy or "").strip().upper(), "с полки кабинета"\n\n\ndef zapisat_instrument(ceh: str, slot: str, tekst: str) -> tuple:\n    """Объявленный инструмент — меткой в дом человека."""\n    tekst = (tekst or "").strip().upper()\n    if not tekst:\n        return False, "пустой инструмент"\n    if instrument_mesta(ceh, slot):\n        return False, ("инструмент этому месту назначен Шефом — "\n                       "выбирать нечего")\n    d, n = _dvizhok_zhitelya(ceh, slot)\n    if d is None:\n        return False, "на месте никого"\n    prezhniy = (instrument_zhitelya(ceh, slot).get("текст") or "").strip()\n    if prezhniy.upper() == tekst:\n        return True, "тот же инструмент, что и был"\n    try:\n        from datetime import datetime\n        metki = d.metki()\n        metki.append({"текст": tekst, "паттерн": PATTERN_INSTR,\n                      "откуда": "решение",\n                      "когда": datetime.now().isoformat(timespec="seconds"),\n                      "раз": 1})\n        d._pisat_etazh(d._metki_path(), metki)\n    except Exception as e:\n        return False, str(e)\n    kto = (n or {}).get("имя", "житель")\n    return True, f"{kto} взял(а) инструмент: {tekst}"\n\n\ndef poymat_instrument(ceh: str, slot: str, otvet: str) -> tuple:\n    """Строка «ИНСТРУМЕНТ: EURUSD» в ответе — записываем меткой."""\n    for stroka in (otvet or "").splitlines():\n        s = stroka.strip()\n        if s.upper().startswith(SLOVO_INSTR):\n            return zapisat_instrument(ceh, slot, s[len(SLOVO_INSTR):])\n    return False, ""\n\n\ndef blok_instrumenta(ceh: str, slot: str, dostupnye=None,\n                     zapasnoy: str = "") -> str:\n    """Кусок в промпт: чем работаем и откуда это взялось."""\n    instr, otkuda = instrument_dlya(ceh, slot, zapasnoy)\n    if otkuda == "назначен":\n        return ("\\n\\n=== ТВОЙ ИНСТРУМЕНТ ===\\n"\n                f"{instr} — назначен тебе Шефом. Это задание, не выбор: "\n                "работаешь по нему.\\n")\n    if otkuda == "выбрал сам":\n        return ("\\n\\n=== ТВОЙ ИНСТРУМЕНТ ===\\n"\n                f"{instr} — ты выбрал(а) его сам(а). Место тебе ничего не "\n                "навязывало.\\nПередумал(а) — скажи строкой "\n                "«ИНСТРУМЕНТ: <тикер>», и это запишется как перемена.\\n")\n    spisok = ""\n    if dostupnye:\n        spisok = ("Что сейчас доступно в городе: "\n                  + ", ".join(sorted(set(dostupnye))[:24]) + ".\\n")\n    return ("\\n\\n=== ТВОЙ ИНСТРУМЕНТ ===\\n"\n            f"Тебе никто ничего не назначил, и своего ты пока не брал(а). "\n            f"Сейчас работаешь по тому, что открыл кабинет: {instr}.\\n"\n            + spisok +\n            "Хочешь свой — возьми: скажи строкой «ИНСТРУМЕНТ: <тикер>». "\n            "Бери тот, который знаешь и чувствуешь, а не тот, где сегодня "\n            "громче. Не хочешь выбирать — работай по кабинетному, это "\n            "тоже честно.\\n")\n'
MOZG_STEZHKI = (
    ("инструмент до стола", '    try:\n        import stol as _stol\n        table = _stol.nakryt(symbol, timeframe, self_key=_SELF_KEY)\n', '    # INSTRUMENT_NAZNACHIT_ILI_SAM_V1: чем работаем. Назначено месту —\n    # работаем по назначению; не назначено, но человек взял свой —\n    # по его; ни того ни другого — по кабинетному, и его просят выбрать.\n    _instr_blok = ""\n    try:\n        from vybor import instrument_dlya as _instr_dlya\n        from vybor import blok_instrumenta as _instr_blok_f\n        _svoy, _otkuda = _instr_dlya(_CEH, _SLOT, symbol)\n        if _svoy and _svoy != symbol:\n            print(f"[{_SLOT}] 🎯 инструмент {_svoy} ({_otkuda}) "\n                  f"вместо кабинетного {symbol}")\n            symbol = _svoy\n        _instr_blok = _instr_blok_f(_CEH, _SLOT, None, symbol)\n    except Exception:\n        pass\n\n    try:\n        import stol as _stol\n        table = _stol.nakryt(symbol, timeframe, self_key=_SELF_KEY)\n'),
    ("инструмент в промпт", '        + _lesenka_slovami()\n', '        + _instr_blok\n        + _lesenka_slovami()\n'),
)
RABOTA_STEZHKI = (
    ("поле бланка", 'POLYA_BLANKA = ("название", "локация", "где", "квартал", "цех", "слот",\n                "чем_занят", "обязанности", "судья", "требования",\n                "условия", "движок")\n', 'POLYA_BLANKA = ("название", "локация", "где", "квартал", "цех", "слот",\n                "чем_занят", "инструмент", "обязанности", "судья",\n                "требования", "условия", "движок")\n'),
    ("пустое поле у новых", '        "чем_занят": "",\n', '        "чем_занят": "",\n        # INSTRUMENT_NAZNACHIT_ILI_SAM_V1: пусто — работник выберет сам\n        "инструмент": "",\n'),
)
UI_STEZHKI = (("поле на виду", 'POLYA = [\n    ("название", "Название должности"),\n    ("чем_занят", "Чем занят — одной строкой"),\n]\n', 'POLYA = [\n    ("название", "Название должности"),\n    ("чем_занят", "Чем занят — одной строкой"),\n    # INSTRUMENT_NAZNACHIT_ILI_SAM_V1: пусто — работник выберет сам\n    ("инструмент", "Инструмент (пусто — выберет сам)"),\n]\n'),)


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


def pravit(put: Path, stezhki, suho: bool, imya: str, dobavka: str = "") -> bool:
    if not put.exists():
        print(f"  x нет {imya}")
        return False
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {imya}: уже накатано")
        return True
    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x {imya}: якорь «{nazv}» найден {n} раз — не трогаю")
            return False
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv}")
    if dobavka:
        tekst = tekst.rstrip("\n") + "\n" + dobavka
        print("    · руки для инструмента")
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, imya):
        return False
    if suho:
        print(f"  {imya}: + готов")
        return True
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {imya}: + накатано")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 62)
    print("ИНСТРУМЕНТ · назначить или на выбор" +
          ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    ok = True
    print("\nмеханизм выбора:")
    ok &= pravit(VYBOR, (), suho, "vybor.py", DOBAVKA)

    print("\nбланк должности:")
    ok &= pravit(RABOTA, RABOTA_STEZHKI, suho, "rabota.py")

    print("\nстраница работы:")
    ok &= pravit(STRANICA, UI_STEZHKI, suho, "ui_rabota.py")

    print("\nтрейдеры:")
    # лесенка может быть ещё не накатана — тогда цепляемся за стол
    ZAPAS_S = '        + "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\\n"\n'
    ZAPAS_N = ('        + _instr_blok\n'
               '        + "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\\n"\n')
    for slot in ("A06", "A07", "A08"):
        put = SLOTY / slot / "мозг.py"
        stezhki = MOZG_STEZHKI
        if put.exists() and "_lesenka_slovami()" not in put.read_text(
                encoding="utf-8"):
            stezhki = (MOZG_STEZHKI[0],
                       ("инструмент в промпт (без лесенки)",
                        ZAPAS_S, ZAPAS_N))
        ok &= pravit(put, stezhki, suho, slot)

    print("-" * 62)
    if not ok:
        return 1
    if suho:
        print("Это был показ. Накатывать: "
              "python patch_instrument_treydera.py --sdelat")
        return 0
    print("Хочешь назначить — Страница Работы, место, поле «Инструмент».")
    print("Хочешь отдать на выбор — оставь пустым и спроси его самого:")
    print("«какой инструмент возьмёшь и почему».")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
