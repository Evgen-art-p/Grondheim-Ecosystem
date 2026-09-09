# -*- coding: utf-8 -*-
# EDINYY_VYBOR_V1
"""
ЕДИНЫЙ ВЫБОР, шаг первый: заводим одно место и сажаем на него
трейдера и вахту.

═══ ЗАЧЕМ (вечер 09.09) ═══

Этаж жил в трёх местах сразу, и все три говорили правду:
  · полка кабинета — что выбрал Шеф;
  · метки жителя — рабочий этаж трейдера (а если не выбрал, тихо
    подставлялся H4 «от комфорта»);
  · вахта — что она запомнила в миг нажатия.

Отсюда весь вечер: Шеф спрашивал про H1, трейдер отвечал про H4;
вахта звонила по часовику, а будить решала по H4; некрон на часовике
для города не существовал. Доказано логом: «сейчас 12:00» при новой
свече 17:00 — это последний закрытый H4.

Слово Шефа: выбор ОДИН, он не чей-то. Кто последний выбрал — тот и
переписал. Экран показывает его, трейдер по нему работает, вахта его
сторожит.

═══ ЧЕСТНО: ЭТО РАЗВОРОТ ПРЕЖНЕГО РЕШЕНИЯ ═══

06.08 патчем UBRAT_CHETVERTOGO_V1 общая пара кабинета была УБРАНА —
и правильно: тогда она была ЧЕТВЁРТОЙ при трёх личных, ничьей, и
работали по ней все. Сейчас она возвращается, но не четвёртой, а
ЕДИНСТВЕННОЙ: личных больше нет. Это другое решение, а не откат к
старой болезни. Записано, чтобы через месяц никто не решил, будто мы
ходим по кругу.

═══ ЧТО ДЕЛАЕТ ЭТОТ ПАТЧ (шаг 1 из 3) ═══

  1. Кладёт новый файл `Биржа/ekran.py` — одно место, где живёт
     выбор: инструмент, этаж, кто поставил, когда и почему.
     Хранится на диске, переживает перезапуск города. Пусто — берётся
     последнее, что стояло (его же и храним).
  2. `vybor.rabota_dlya` — трейдер работает ПО ЭКРАНУ. Личные метки
     этажа больше не источник; тихой подстановки H4 «от комфорта»
     больше нет.
  3. Вахта сторожит экран: каждый тик перечитывает его заново.
     Переехал выбор — вахта переехала следом, перезаводить не нужно.

Шаг 2 (кадр сам выходит на экран при выборе руками, спуск рисуется)
и шаг 3 (рука на вход) — отдельными патчами, после того как этот
устоится.

═══ ЧЕГО НЕ ДЕЛАЕТ ═══

Не трогает тестер: у него своё время и своя пара, в общий выбор он не
пишет. Не трогает знания, промпт и задачу трейдера.

Запускать из корня репозитория:
    python postavit_edinyy_vybor.py

Идемпотентен (маркер EDINYY_VYBOR_V1). Рядом .bak. Есть --suho.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

MARKER = "EDINYY_VYBOR_V1"
SUHO = "--suho" in sys.argv

BIRZHA = Path("Биржа")

# ══════════════════════════════════════════════════════════════
# НОВЫЙ ФАЙЛ: Биржа/ekran.py
# ══════════════════════════════════════════════════════════════

EKRAN = '''# -*- coding: utf-8 -*-
# EDINYY_VYBOR_V1
"""ЭКРАН — единственное место, где живёт выбор города.

Один выбор на всех: инструмент и этаж. Кто последний выбрал — тот и
переписал. Экран показывает его, трейдер по нему работает, вахта его
сторожит, кадр по нему рисуется.

Своих копий больше никто не держит — в этом весь смысл. Если этаж
снова заведётся в двух местах, они разойдутся, и оба будут правы
(вечер 09.09, проверено дорого).

Лежит на диске: переживает перезапуск. Пусто бывает ровно один раз —
до первого выбора.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

_FAYL = Path(__file__).resolve().parent / "данные" / "vybor_ekrana.json"

_PUSTO = {"инструмент": "", "этаж": "", "кто": "", "когда": "",
          "почему": ""}


def _prochitat() -> dict:
    try:
        if _FAYL.is_file():
            d = json.loads(_FAYL.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                out = dict(_PUSTO)
                out.update({k: v for k, v in d.items() if k in out})
                return out
    except Exception as e:
        print(f"[ЭКРАН] не прочитался ({e}) — считаю пустым")
    return dict(_PUSTO)


def vzyat() -> dict:
    """Что сейчас выбрано. Всегда словарь, пустой — значит не выбрано."""
    return _prochitat()


def para() -> tuple:
    """(инструмент, этаж) — коротко, для тех, кому нужна только пара."""
    v = _prochitat()
    return v["инструмент"], v["этаж"]


def est() -> bool:
    v = _prochitat()
    return bool(v["инструмент"] and v["этаж"])


def postavit(instrument: str, etazh: str, kto: str = "",
             pochemu: str = "") -> tuple:
    """Поставить выбор. Возвращает (получилось, что сказать вслух).

    Закон Рычага: у смены выбора есть след — кто повернул, когда и
    зачем. Переезд двигает вахту, значит меняет, когда человека вообще
    будут будить; такое решение должно быть видно и разбираемо.
    """
    instrument = (instrument or "").strip().upper()
    etazh = (etazh or "").strip().upper()
    if not instrument or not etazh:
        return False, "выбор пустой — нужен и инструмент, и этаж"

    bylo = _prochitat()
    if bylo["инструмент"] == instrument and bylo["этаж"] == etazh:
        return True, "тот же выбор, что и был"

    novyy = {"инструмент": instrument, "этаж": etazh,
             "кто": (kto or "").strip(),
             "когда": datetime.now().isoformat(timespec="seconds"),
             "почему": (pochemu or "").strip()}
    try:
        _FAYL.parent.mkdir(parents=True, exist_ok=True)
        vremenno = _FAYL.with_suffix(".json.tmp")
        vremenno.write_text(
            json.dumps(novyy, ensure_ascii=False, indent=2),
            encoding="utf-8")
        vremenno.replace(_FAYL)
    except Exception as e:
        return False, f"выбор не записался: {e}"

    otkuda = f" ({novyy['кто']})" if novyy["кто"] else ""
    prichina = f" — {novyy['почему']}" if novyy["почему"] else ""
    print(f"[ЭКРАН] ▣ выбор: {instrument} {etazh}{otkuda}{prichina}")
    return True, f"выбор: {instrument} {etazh}"


def slovami() -> str:
    """Строка для человека: что стоит и с чьей руки."""
    v = _prochitat()
    if not (v["инструмент"] and v["этаж"]):
        return "выбор не поставлен"
    kto = f" · поставил {v['кто']}" if v["кто"] else ""
    return f"{v['инструмент']} {v['этаж']}{kto}"
'''

# ══════════════════════════════════════════════════════════════
# ПРАВКА 1: vybor.py — трейдер работает по экрану
# ══════════════════════════════════════════════════════════════

VYBOR_OLD = """    instr, otk_i = instrument_dlya(ceh, slot)
    etazh, otk_e = "", \"\""""

VYBOR_NEW = """    # EDINYY_VYBOR_V1: сперва ЭКРАН. Выбор в городе один, и трейдер
    # работает по нему — не по своей копии. Раньше инструмент брался
    # из поста или личных меток, а этаж без выбора тихо подставлялся
    # H4 «от комфорта»; из-за этого Шеф смотрел H1, трейдер работал
    # H4, вахта звонила по одному, а будила по другому.
    try:
        import ekran as _ekr
        _i, _e = _ekr.para()
        if _i and _e:
            if not kto_sidit(ceh, slot):
                return {"инструмент": _i, "этаж": _e, "паттерн": "",
                        "откуда_инструмент": "с экрана",
                        "откуда_этаж": "с экрана", "готов": False}
            return {"инструмент": _i, "этаж": _e, "паттерн": "",
                    "откуда_инструмент": "с экрана",
                    "откуда_этаж": "с экрана", "готов": True}
    except Exception as _e_ekr:
        print(f"[ВЫБОР] экран не прочитался ({_e_ekr}) — иду по-старому")

    instr, otk_i = instrument_dlya(ceh, slot)
    etazh, otk_e = "", \"\""""

# ══════════════════════════════════════════════════════════════
# ПРАВКА 2: ui_torg.py — вахта сторожит экран
# ══════════════════════════════════════════════════════════════

VAHTA_OLD = """    sym, tf = _VAHTA["инструмент"], _VAHTA["этаж"]"""

VAHTA_NEW = """    # EDINYY_VYBOR_V1: сторожим ЭКРАН, а не то, что вахта запомнила
    # при нажатии. Переехал выбор — вахта переехала следом, снимать и
    # заводить заново не нужно. Экран пуст — держимся прежнего.
    sym, tf = _VAHTA["инструмент"], _VAHTA["этаж"]
    try:
        import ekran as _ekr
        _i, _e = _ekr.para()
        if _i and _e and (_i, _e) != (sym, tf):
            print(f"[ВАХТА] ▣ выбор переехал: {sym} {tf} → {_i} {_e}")
            sym, tf = _i, _e
            _VAHTA.update({"инструмент": _i, "этаж": _e, "бар": ""})
            return          # новый пост — этот тик только запоминаем
    except Exception:
        pass"""

# ══════════════════════════════════════════════════════════════
# ПРАВКА 3: ui_torg.py — встал на вахту = поставил выбор
# ══════════════════════════════════════════════════════════════

KNOPKA_OLD = """        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,
                       "бар": "", "цех": tseh_id})"""

KNOPKA_NEW = """        # EDINYY_VYBOR_V1: встать на вахту — это и есть выбор.
        # Пишем в экран, чтобы трейдер и кадр поехали туда же.
        try:
            import ekran as _ekr
            _ekr.postavit(_s, _t, kto="Шеф", pochemu="встал на вахту")
        except Exception as _e_ekr:
            print(f"[ВАХТА] экран не записался ({_e_ekr})")
        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,
                       "бар": "", "цех": tseh_id})"""


def nayti_koren() -> Path:
    kandidat = Path(__file__).resolve().parent
    for papka in [kandidat, *kandidat.parents]:
        if (papka / BIRZHA / "vybor.py").is_file():
            return papka
    print("Не нашёл Биржа/vybor.py рядом со скриптом.")
    print("Положи скрипт в корень репозитория и запусти оттуда.")
    input("Enter — закрыть...")
    sys.exit(1)


def pravka(p: Path, pary: list, imya: str) -> bool:
    """Все правки одного файла разом. Ни одна не легла — не пишем."""
    tekst = p.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  · {imya}: уже сделано")
        return True

    for kak, staroe, _ in pary:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  ⚠ {imya} / «{kak}»: совпадений {n}, нужно 1 — "
                  "файл НЕ тронут")
            return False

    novyy = tekst
    for kak, staroe, novoe in pary:
        novyy = novyy.replace(staroe, novoe, 1)
        print(f"  ✔ {imya}: {kak}")

    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ⚠ {imya}: синтаксис сломан ({e}) — НЕ сохраняю")
        return False

    if SUHO:
        return True

    bak = p.with_suffix(p.suffix + ".bak_vybor")
    if not bak.exists():
        bak.write_text(tekst, encoding="utf-8")
    p.write_text(novyy, encoding="utf-8")
    return True


def main() -> None:
    koren = nayti_koren()
    print(f"Корень: {koren}\n")

    # 1. новый файл
    ekran_p = koren / BIRZHA / "ekran.py"
    if ekran_p.exists():
        print("  · Биржа/ekran.py: уже лежит")
    elif SUHO:
        print("  ✔ Биржа/ekran.py: положил бы (сухой прогон)")
    else:
        ekran_p.write_text(EKRAN, encoding="utf-8")
        print("  ✔ Биржа/ekran.py: положен")

    # 2. vybor.py
    pravka(koren / BIRZHA / "vybor.py",
           [("трейдер работает по экрану", VYBOR_OLD, VYBOR_NEW)],
           "Биржа/vybor.py")

    # 3. ui_torg.py — обе правки вместе
    pravka(koren / BIRZHA / "ui_torg.py",
           [("вахта сторожит экран", VAHTA_OLD, VAHTA_NEW),
            ("встал на вахту — поставил выбор", KNOPKA_OLD, KNOPKA_NEW)],
           "Биржа/ui_torg.py")

    print("\nКак проверить: встань на вахту по часовику и спроси")
    print("трейдера, где он работает. Должен ответить H1, а не H4.")
    input("\nEnter — закрыть...")


if __name__ == "__main__":
    main()
