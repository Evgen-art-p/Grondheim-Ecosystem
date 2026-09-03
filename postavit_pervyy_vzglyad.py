# -*- coding: utf-8 -*-
# MARKER: PERVYY_VZGLYAD_V1
"""
ПЕРВЫЙ ВЗГЛЯД — КАДР, А НЕ ТРИДЦАТЬ СТРОК ЧИСЕЛ.

СЛОВО ШЕФА (03.09)
    «Я открываю график и смотрю. Не считаю, а смотрю. Просто вижу
    структуру, которая есть... Если понравилось, то уже смотрю
    глубже». И про этажи: «проснулся, смотрит свой этаж, выше,
    дневку, может и недельку... три-четыре кадра последовательно ПО
    ЗАПРОСУ. Нравится — не нравится».

ЧТО БЫЛО НЕ ТАК
───────────────
Трейдеру в одном сообщении приходил кадр И весь стол сразу: Аллигатор
числами, AO, фракталы, резинка, точка ноль, волна, масштаб, глубина
отката, уровни заявки, слом, попытки. Тридцать строк цифр рядом с
одной картинкой — глаз в такой стопке не первый, он последний.

Плюс лесенка ВРАЛА: заголовок обещал «три рабочих этажа» и объяснял,
что старший даёт направление, а младший точность, — а список этажей
давно схлопнут в один. Трейдер читал про то, чего ему не давали.

ЧТО ДЕЛАЕТСЯ
────────────
    · стол числами уходит из первого сообщения;
    · вместо него — честная строка: вот твой инструмент, вот твой
      этаж, кадр нарисован по нему, а числа и другие этажи — рукой,
      если после взгляда они тебе понадобились;
    · в JSON остаётся только то, без чего нельзя назвать цену: своя
      открытая позиция и текущий бар (OHLC + тик);
    · резинка тоже уходит в руку — это число, а не картина.

Руки, которыми он берёт всё остальное, у него УЖЕ ЕСТЬ и ничего в них
не меняется: stol_na_etazhe, pokazat_etazh, rastyanut_volnu,
izmerit_volnu, krayniye_tochki, moya_kartina, moy_dnevnik, uchebnik.
Патч не добавляет возможностей — он убирает подсказку вперёд глаза.

ЧТО НЕ ТРОГАЕТСЯ
────────────────
Сам стол (`stol.py`) считается как считался — он нужен рукам, кабинету
и прогону. Кадр, знания, личность, события, порядок ответа, НАБЛЮДАЮ,
формат JSON — как были.

Правится три мозга: A06, A07, A08. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "PERVYY_VZGLYAD_V1"
SLOTY = ("A06", "A07", "A08")


def _nayti_sloty() -> Path:
    """Папка .../торговый_хаос/слоты — ищем сами, от скрипта и от cwd."""
    hvost = Path("GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты")
    nashli = []
    korni = []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        for p in (koren / hvost, koren):
            if all((p / s / "мозг.py").exists() for s in SLOTY):
                if p not in nashli:
                    nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл слоты A06/A07/A08.")
        s = input("Перетащи сюда папку «слоты» и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "A06" / "мозг.py").exists():
            return p
        raise SystemExit("не та папка — там нет A06/мозг.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


# ─────────────── 1. ЛЕСЕНКА: правда вместо трёх этажей ───────────────

LESENKA_STAR = '''    def _lesenka_slovami() -> str:
        try:
            import stol as _s2
        except Exception:
            return ""
        L = ["=== ЛЕСЕНКА · три рабочих этажа этого инструмента ===",
             f"Инструмент {symbol} назначен Шефом. Этажи — твои."]
        for _tf in _RABOCHIE_ETAZHI:
            try:
                _t2 = _s2.nakryt(symbol, _tf, self_key=_SELF_KEY)
                _tekst = _s2.slovami(_t2)
            except Exception as _e2:
                _tekst = f"этаж не накрылся: {_e2}"
            _metka = "   ← на нём кадр перед тобой" if _tf == timeframe else ""
            L.append(f"\\n-- {_tf}{_metka} --\\n{_tekst}")
        L.append(
            "\\nСтарший этаж говорит о направлении, рабочий — о входе, "
            "младший — о точности. Спускаться или нет, и на каком "
            "работать сегодня — решаешь ты. Скажи это в narrative "
            "прямо: «работаю по H4», «спускаюсь на H1, там видно "
            "приседающий». Кадр нарисован по этажу с полки; если "
            "смотришь на другой — суди по числам, они честные.\\n")
        return "\\n".join(L) + "\\n"
'''

LESENKA_NOV = '''    def _lesenka_slovami() -> str:
        # PERVYY_VZGLYAD_V1: здесь выкладывался ВЕСЬ стол числами —
        # тридцать строк рядом с одной картинкой. Глаз в такой стопке
        # не первый. Теперь тут только правда о том, что перед тобой,
        # и напоминание, что числа можно ПОПРОСИТЬ.
        return (
            "=== ГДЕ ТЫ СТОИШЬ ===\\n"
            f"Инструмент {symbol}, рабочий этаж {timeframe}. Кадр перед "
            f"тобой нарисован по нему.\\n"
            "Чисел рядом нет НАРОЧНО: сперва глаз, приборы потом. Если "
            "после взгляда они тебе нужны — попроси рукой, это твоё "
            "право:\\n"
            "  · stol_na_etazhe — показания этажа: Аллигатор, AO, "
            "фракталы, разворотный бар, натяжение, точка, волна, откат;\\n"
            "  · pokazat_etazh — КАРТИНКА другого этажа: посмотреть "
            "старший (куда идёт рынок вообще) или нырнуть ниже;\\n"
            "  · rastyanut_volnu — растянуть кусок так, чтобы он занял "
            "100-140 баров, и разглядеть его целиком;\\n"
            "  · izmerit_volnu, krayniye_tochki, moya_kartina, "
            "moy_dnevnik, uchebnik.\\n"
            "Смотри столько кадров, сколько нужно, чтобы понять, что "
            "происходит. Не понял — это законный ответ: не работаешь.\\n\\n")
'''

# ─────────── 2. Стол числами уходит из первого сообщения ───────────

def _stol_star(imya: str) -> str:
    return ('        + "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\\n"\n'
            f'        f"{{json.dumps({imya}, ensure_ascii=False, indent=2)}}\\n\\n"\n')


def _stol_nov(imya: str) -> str:
    return ('        # PERVYY_VZGLYAD_V1: раскладка момента ушла в руку\n'
            '        # stol_na_etazhe. Здесь остаётся только то, без чего\n'
            '        # нельзя НАЗВАТЬ цену: своя позиция и текущий бар.\n'
            '        + "=== ЧТО У ТЕБЯ НА РУКАХ ===\\n"\n'
            '        f"{json.dumps({\'position\': '
            f'{imya}.get(\'position\'),\n'
            '                       \'бар\': '
            f'({imya}.get(\'market\') or {{}}).get(\'price\'),\n'
            '                       \'тик\': '
            f'({imya}.get(\'market\') or {{}}).get(\'point\')}},\n'
            '                     ensure_ascii=False, indent=2)}\\n\\n"\n')


# ─────────────── 3. Резинка — тоже число, тоже в руку ───────────────

REZINKA_STAR = '        f"РЕЗИНКА (натяжение от Губ): {_rez}\\n"\n'
REZINKA_NOV = ('        # PERVYY_VZGLYAD_V1: резинка — число, а не картина.\n'
               '        # Она есть в руке stol_na_etazhe, если понадобится.\n'
               '        + ""\n')


def _pochinit(f: Path, imya_stola: str) -> str:
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже накачено"

    star_stol = _stol_star(imya_stola)
    if LESENKA_STAR not in src:
        return "! не нашёл прежнюю лесенку — файл правили, не трогаю"
    if star_stol not in src:
        return "! не нашёл выкладку стола — файл правили, не трогаю"
    if REZINKA_STAR not in src:
        return "! не нашёл строку резинки — файл правили, не трогаю"

    novyy = src.replace(LESENKA_STAR, LESENKA_NOV)
    novyy = novyy.replace(star_stol, _stol_nov(imya_stola))
    novyy = novyy.replace(REZINKA_STAR, REZINKA_NOV)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    ast.parse(novyy)      # на диск не кладём то, что не разбирается
    shutil.copy2(f, f.with_suffix(".py.bak_vzglyad"))
    f.write_text(novyy, encoding="utf-8")
    return "кадр первым, числа по просьбе (.bak_vzglyad рядом)"


def main():
    koren = _nayti_sloty()
    print(f"\nСлоты: {koren}\n")
    imena = {"A06": "table_for_brut",
             "A07": "table_for_avan",
             "A08": "table_for_cons"}
    for slot in SLOTY:
        f = koren / slot / "мозг.py"
        try:
            itog = _pochinit(f, imena[slot])
        except SyntaxError as e:
            itog = f"! после правки не разбирается ({e}) — файл НЕ тронут"
        print(f"  {slot}: {itog}")
    print("\nГотово. Первым идёт кадр, числа трейдер просит сам.")
    print("Стол считается как считался — он нужен рукам и кабинету.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
