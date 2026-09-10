# -*- coding: utf-8 -*-
# ISTORIYA_OT_SLEDA_V1 — дневник пишет то, что случилось
"""
ДНЕВНИК ОТ СЛЕДА, А НЕ ОТ РАССКАЗА

Слово Шефа: «дневник пишет то, что случилось, а не то, что житель
про себя подумал. Без руки история — из слов».

ГДЕ СЕГОДНЯ ДЫРА. В событие дневника ложатся цифры решения (они уже
с руки — после SLOVO_NE_PRIKAZ_V1) и рядом два поля голоса: `input`
и `action` — то, что трейдер САМ про себя написал. И всё. По записи
нельзя ответить на три вопроса, ради которых история и ведётся:

  · был ли вообще рычаг, или это только слова;
  · что именно приказано — вход, стоп, долив, закрытие;
  · зачем — своими словами, из самого приказа, а не из рассказа.

ЧТО ДЕЛАЕТ ПАТЧ. Одна вставка в `_append_diary` каждого из трёх
мозгов. В событие добавляются четыре поля:

    "что"    — действие приказа (ENTER / MOVE_STOP / ADD / CLOSE …)
    "почему" — причина, которую трейдер назвал В ПРИКАЗЕ
    "рычаг"  — правда или ложь: приказ был отдан рукой
    "ключ"   — ключ жителя, чтобы запись искалась по ключу, а не
               только по имени

Голос НЕ выбрасывается: `input` и `action` остаются и стоят рядом.
Разница в том, что теперь видно, где факт, а где рассказ о факте.

Поле `рычаг` — самое важное из четырёх. Пока его нет, «промолчал» и
«говорил, но не сделал» в истории выглядят одинаково, а по весам
это совсем разные жители.

ТРЕБУЕТ: SLOVO_NE_PRIKAZ_V1 (иначе в signal лежит текст, и «рычаг»
врал бы). Патч это проверяет.

БЕЗОПАСНОСТЬ: .bak_istoriya, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_istoriyu_ot_sleda.py --suho
    python postavit_istoriyu_ot_sleda.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "ISTORIYA_OT_SLEDA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

PREF = {"A06": "brut_", "A07": "avan_", "A08": "cons_"}

VSTAVKA = '''        # ISTORIYA_OT_SLEDA_V1: дневник пишет ФАКТ, не рассказ.
        # Ниже — то, что доказано рычагом: был ли приказ, что
        # приказано и зачем. input/action остаются голосом трейдера
        # и стоят РЯДОМ, а не вместо: видно, где факт, где слова.
        "что":       signal.get("{PREF}action"),
        "почему":    signal.get("{PREF}reason"),
        "рычаг":     bool(signal),
        "ключ":      _klyuch_svoy(),
'''

TELO = '''

# ── ISTORIYA_OT_SLEDA_V1: свой ключ для записи ────────────────
# Запись подписана именем (YASHCHIK_STOLA_V1) — это для глаз. Ключ
# нужен, чтобы её нашли ПОПЕРЁК города: имя может повториться,
# печать — нет. Нет модуля или нет жителя — пустая строка, и запись
# просто остаётся с одним именем, как была.

def _klyuch_svoy() -> str:
    try:
        import sys as _s
        from pathlib import Path as _P
        # ищем папку ГОРОД вверх по дереву, а не считаем уровни:
        # счёт уровней ломается от любой перестановки папок
        _g = None
        for _up in _P(__file__).resolve().parents:
            if (_up / "ГОРОД" / "klyuch.py").exists():
                _g = str(_up / "ГОРОД")
                break
        if _g is None:
            return ""
        if _g not in _s.path:
            _s.path.insert(0, _g)
        import klyuch
        return klyuch.klyuch_zhitelya(_kto_ya() or "")
    except Exception:
        return ""


# ISTORIYA_OT_SLEDA_V1 - marker
'''


def _pravka(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}/мозг.py: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}/мозг.py: уже стоит")
        return 0
    if "SLOVO_NE_PRIKAZ_V1" not in txt:
        print(f"  {slot}/мозг.py: ОТКАЗ — сперва postavit_slovo_ne_prikaz.py")
        return -1

    pref = PREF[slot]
    yakor = f'        "lot":       signal.get("{pref}lot"),\n'
    if txt.count(yakor) != 1:
        print(f"  {slot}/мозг.py: ОТКАЗ — якорь встречается "
              f"{txt.count(yakor)} раз(а)")
        return 0

    novy = txt.replace(yakor, yakor + VSTAVKA.replace("{PREF}", pref), 1)
    novy = novy.rstrip("\n") + "\n" + TELO

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}/мозг.py: ОТКАЗ — синтаксис сломан ({e})")
        return 0

    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_istoriya"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}/мозг.py: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("ДНЕВНИК ОТ СЛЕДА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    if not SLOTY.exists():
        print("!! слотов нет — запускать из корня репы")
        return

    vsego = 0
    for slot in ("A06", "A07", "A08"):
        r = _pravka(slot)
        if r < 0:
            return
        vsego += r

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_istoriya")
    print("Теперь по записи видно: был рычаг или только слова.")
    print()


if __name__ == "__main__":
    main()
