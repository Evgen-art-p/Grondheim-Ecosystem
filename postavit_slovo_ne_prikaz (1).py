# -*- coding: utf-8 -*-
# SLOVO_NE_PRIKAZ_V1 — запасной ход закрыт
"""
СЛОВО БОЛЬШЕ НЕ ПРИКАЗ

Рука `otdat_prikaz` доказала себя живьём 10.09 — приказ прошёл,
исполнитель принял. Значит запасной ход больше не нужен: пока он
есть, «сказал и не вошёл» опять неотличимо от «вошёл».

ЗАКОН РЫЧАГА, до конца: утверждение без рычага — не утверждение.

ЧТО ДЕЛАЕТ ПАТЧ, две правки в трёх слотах каждая.

 1. МОЗГИ A06/A07/A08. Решение больше НЕ достаётся из текста.
    Оно берётся с табло — то есть только то, что трейдер положил
    туда рукой на ЭТОМ баре. Разбор текста остаётся жив ради голоса
    и дневника, но его поля решения выбрасываются.

    Не позвал руку — решения нет вовсе, и дальше всё работает как
    при «не работаю»: город никого не открывает. Сказал словами и
    не позвал — в консоли встанет честная строка про это, чтобы
    было видно, а не гадалось.

    Режем ВСЁ, не только вход: ведение (передвинуть стоп, долить,
    закрыть) тоже уходит из текста. Полумера оставила бы ту же щель,
    просто в другом месте.

 2. БУМАГА (промпт.md). Из формата ответа убирается блок `signal` —
    иначе бумага учит тому, чего код уже не читает. Ровно эта
    болезнь дала «три места входа»: строку убрали из знаний, а в
    промпте забыли, и трейдер честно читал написанное. Вместо
    блока встаёт короткое правило: решение отдаётся рукой.

ЧЕГО НЕ ТРОГАЕТ: голос (`narrative`), дневник (`diary_entry`),
исполнителя, брокера. Дневник от следа приказа — следующий шаг,
отдельно.

ТРЕБУЕТ: RUKA_PRIKAZA_V1 (иначе трейдеру нечем будет решать вовсе —
патч это проверяет и откажется).

БЕЗОПАСНОСТЬ: .bak_slovo рядом с каждым файлом, идемпотентен,
синтаксис проверяется до записи, `--suho` не трогает диск.

    python postavit_slovo_ne_prikaz.py --suho
    python postavit_slovo_ne_prikaz.py

`шесть·проверено·до·корня`
"""
import ast
import re
import shutil
import sys
from pathlib import Path

MARKER = "SLOVO_NE_PRIKAZ_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# слот → (имя разборщика, ключ табло, приставка полей)
SLOTY_KARTA = {
    "A06": ("_parse_brut", "brut", "brut_"),
    "A07": ("_parse_avan", "avan", "avan_"),
    "A08": ("_parse_cons", "cons", "cons_"),
}

TELO = '''

# ── SLOVO_NE_PRIKAZ_V1: решение приходит с руки, не из текста ──
# Раньше цифры входа вылавливались из ответа модели. Сергей-исполнитель
# читал табло и был чист — врала середина: приказ рождался у разбора,
# а не у трейдера. Отсюда «сказал и не вошёл» = «вошёл».
#
# Теперь решение берётся ТОЛЬКО с табло и только то, что положено
# рукой otdat_prikaz на этом самом баре. Текст остаётся голосом.

_TABLO_KEY_{PREF_UP} = "{TABLO}"
_PRIKAZ_POLYA = ("action", "verdict", "reason", "direction", "entry",
                 "stop", "lot", "new_stop", "add_lot")


def _signal_ot_ruki(bar_time=None, slova: dict = None) -> dict:
    """Решение трейдера — с табло, куда он положил его рукой.

    Пусто, если: руку не звал; приказ с другого бара (протух);
    табло не открылось. Пустое решение означает ровно то же, что
    «не работаю» — город никого не откроет.
    """
    try:
        from hooks import load_trading_state
        t = load_trading_state()
    except Exception as _e:
        print(f"[РЕШЕНИЕ] табло не открылось ({_e}) — решения нет")
        return {}

    v = dict((t.get(_TABLO_KEY_{PREF_UP}) or {}))
    otdan = bool(v.get("отдан_рукой"))
    bar_v = str(v.get("бар") or "")

    if otdan and bar_time and bar_v and bar_v != str(bar_time):
        print("[РЕШЕНИЕ] приказ с прошлого бара — не беру")
        otdan = False

    if not otdan:
        if slova:
            print("[СЛОВО] в ответе есть поля решения, но рукой приказ "
                  "не отдан — решения нет. Слово приказом не считается.")
        return {}

    out = {}
    for pole in _PRIKAZ_POLYA:
        if v.get(pole) is not None:
            out["{PREF}" + pole] = v[pole]
    print(f"[РЕШЕНИЕ] с руки: {out.get('{PREF}action')} "
          f"{out.get('{PREF}direction') or ''}".rstrip())
    return out


# SLOVO_NE_PRIKAZ_V1 - marker
'''

# ── бумага ───────────────────────────────────────────────────
NOVOE_PRAVILO = '''```json
{
  "narrative": "Одно-три предложения. Твой голос. То, что ты думаешь сейчас.",
  "diary_entry": {
    "input": "что было перед тобой: рынок и каким ты был сегодня",
    "action": "что ты сделал и почему — честно",
    "result": null
  }
}
```

РЕШЕНИЕ В ЭТОТ ОТВЕТ НЕ ПИШЕТСЯ. Войти, передвинуть стоп, долить или
закрыть можно только рукой `otdat_prikaz` — она и есть приказ
исполнителю. Не позвал руку — ничего не произошло, сколько ни
рассказывай: слов исполнитель не слышит. Назвал цену в тексте и не
позвал руку — это не вход, а разговор о входе.

`diary_entry.result` всегда `null`: чем кончилось, допишет жизнь.'''


def _pravka_mozga(slot: str) -> int:
    imya, tablo, pref = SLOTY_KARTA[slot]
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}/мозг.py: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}/мозг.py: уже стоит")
        return 0
    # руки живут в Биржа/ruki_treydera.py в КОРНЕ репы. Раньше здесь
    # считались уровни от папки слотов и получался путь внутри
    # GRONDHEIM_CITY — файла там нет, и патч обрывался с ошибкой,
    # ничего не тронув. Ищем файл, а не считаем этажи.
    _ruki = None
    for _kandidat in (_REPO / "Биржа" / "ruki_treydera.py",
                      _REPO / "GRONDHEIM_CITY" / "Биржа" / "ruki_treydera.py"):
        if _kandidat.exists():
            _ruki = _kandidat
            break
    if _ruki is None:
        print("  ОТКАЗ: не нашёл ruki_treydera.py — запускать из корня репы")
        return -1
    if "RUKA_PRIKAZA_V1" not in _ruki.read_text(encoding="utf-8",
                                                errors="ignore"):
        print("  ОТКАЗ: руки приказа нет — сперва postavit_ruku_prikaza.py")
        return -1

    staroe = f"    narrative, signal, diary_entry = {imya}(response)"
    if txt.count(staroe) != 1:
        print(f"  {slot}/мозг.py: ОТКАЗ — якорь встречается "
              f"{txt.count(staroe)} раз(а)")
        return 0

    novoe = (f"    narrative, _slova, diary_entry = {imya}(response)\n"
             f"    # SLOVO_NE_PRIKAZ_V1: решение — только с руки\n"
             f"    signal = _signal_ot_ruki(md.get(\"bar_time\"), _slova)")

    novy = txt.replace(staroe, novoe, 1)
    novy = novy.rstrip("\n") + "\n" + TELO.replace(
        "{PREF_UP}", pref.strip("_").upper()).replace(
        "{TABLO}", tablo).replace("{PREF}", pref)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}/мозг.py: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_slovo"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}/мозг.py: {'готов' if SUHO else 'поправлен'}")
    return 1


def _pravka_bumagi(slot: str) -> int:
    p = SLOTY / slot / "промпт.md"
    if not p.exists():
        print(f"  {slot}/промпт.md: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}/промпт.md: уже стоит")
        return 0

    bloki = re.findall(r"```json\n.*?\n```", txt, re.S)
    if len(bloki) != 1 or "signal" not in bloki[0]:
        print(f"  {slot}/промпт.md: ОТКАЗ — блоков json {len(bloki)}, "
              f"не рискую")
        return 0

    novy = txt.replace(bloki[0], NOVOE_PRAVILO, 1)

    # старый абзац про входишь/null — он теперь про несуществующие поля
    novy = re.sub(r"\n\nВходишь — .*?допишет жизнь\.", "", novy, count=1,
                  flags=re.S)

    if MARKER not in novy:
        novy = novy.rstrip("\n") + f"\n\n<!-- {MARKER} -->\n"

    if not SUHO:
        shutil.copy2(p, p.with_suffix(".md.bak_slovo"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}/промпт.md: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("СЛОВО НЕ ПРИКАЗ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    if not SLOTY.exists():
        print("!! слотов нет — запускать из корня репы")
        return

    print("1. МОЗГИ — решение только с руки:")
    vsego = 0
    for slot in ("A06", "A07", "A08"):
        r = _pravka_mozga(slot)
        if r < 0:
            return
        vsego += r

    print()
    print("2. БУМАГА — формат ответа без решения:")
    for slot in ("A06", "A07", "A08"):
        vsego += _pravka_bumagi(slot)

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_slovo")
    print("Теперь войти можно только рукой. Слово осталось голосом.")
    print()


if __name__ == "__main__":
    main()
