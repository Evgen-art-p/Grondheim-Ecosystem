# -*- coding: utf-8 -*-
"""
postavit_ruku_uchebnika.py · MARKER: UCHEBNIK_V_RUKE_V1

СЛОВА ШЕФА
──────────
    «Есть же в Академии архив с картинками, ну и накидать по темам — и
    пусть по запросу получит в работе. Она там с глазами.»

ЧТО ЛЕЖИТ И ЧЕГО НЕ ХВАТАЛО
───────────────────────────
В Академии 41 картинка из книги «Торговый Хаос», разложенная по главам:

    глава 3 — логика хаоса (4)      глава 6 — бар, объём, MFI (13)
    глава 4 — структура (1)         глава 7 — волны и осциллятор (22)

И при них ОПИСЬ с подписями, вырезанными из авторского текста:
«приседающий бар и зелёный бар», «Альпинисты 3-1, 2-1 и 3-2»,
«техника для установки уровня убытков»…

То есть темы придумывать не надо — они уже в подписях книги.

А на рабочем столе картинок Академии не было НИ ОДНОЙ. Учили её
рисунками, глаза ей мы дали, — а дороги между ними не было.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Рука `uchebnik(о_чём)`: трейдер просит картинку из книги словами —
«приседающий бар», «фрактал», «волны AO» — и ВИДИТ её. Не описание,
не пересказ: сам рисунок, тем же приёмом, что кадр растяжки.

Ищем по описи и по названиям глав. Ничего не выдумываем: подписи
настоящие, авторские. Не нашлось — так и говорим, и показываем, какие
темы вообще есть.

ПОЧЕМУ ЭТО НЕ ПРОСТО «ЕЩЁ ОДНА РУКА»
────────────────────────────────────
Шеф заметил 05.08, и это записано в БИРЖА.md: «в память ложится не
картинка, а СОБСТВЕННЫЙ ТЕКСТ ученика о ней — завтра он помнит свои
слова, а не то, что видел». У Нины в памяти ровно 4 записи вида «я
узнала, что график gl07_str11_1 показывает окончания волн 1, …» — её
пересказ, а не рисунок.

Теперь она может СНОВА ПОСМОТРЕТЬ на то, на чём училась, стоя перед
живым графиком. Насмотренность перестаёт быть воспоминанием о словах.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_ruku_uchebnika.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "UCHEBNIK_V_RUKE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ruki_treydera.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


UCHEBNIK_PY = '''# -*- coding: utf-8 -*-
# UCHEBNIK_V_RUKE_V1
"""
УЧЕБНИК — картинки из книги, по которой учили.

СЛОВА ШЕФА
    «Есть же в Академии архив с картинками, накидать по темам — и
    пусть по запросу получит в работе. Она там с глазами.»

ЗАКОН ЭТОГО ФАЙЛА
    Ищем ПО АВТОРСКИМ ПОДПИСЯМ из описи и по названиям глав. Своих
    тем не выдумываем и картинок не толкуем: показали — дальше её
    дело. Не нашлось — так и говорим, а не подсовываем похожее.

ЗАЧЕМ
    Учили рисунками, а в память ложился её ПЕРЕСКАЗ рисунка. Завтра
    она помнит свои слова, а не то, что видела. Теперь может
    посмотреть снова — стоя перед живым графиком.
"""
from __future__ import annotations

import re
from pathlib import Path

_KOREN = Path(__file__).resolve().parent.parent
_KARTINKI = (_KOREN / "GRONDHEIM_CITY" / "Академия" / "дисциплины"
             / "финансы" / "торговый_хаос" / "уроки" / "картинки")
_OPIS = _KARTINKI / "ОПИСЬ.md"


def _razobrat_opis() -> list:
    """[(файл, глава, подпись)] — из авторской описи."""
    if not _OPIS.exists():
        return []
    out, glava = [], ""
    for s in _OPIS.read_text(encoding="utf-8", errors="replace").splitlines():
        s = s.strip()
        if s.startswith("## "):
            glava = s[3:].strip()
            continue
        m = re.match(r"^-\\s+`([^`]+)`\\s*(?:\\([^)]*\\))?\\s*—?\\s*(.*)$", s)
        if m:
            out.append((m.group(1).strip(), glava, m.group(2).strip()))
    return out


def _nayti_fayl(imya: str):
    for p in _KARTINKI.rglob(imya):
        return p
    return None


def temy() -> str:
    """Какие главы вообще есть — чтобы было видно, о чём спрашивать."""
    opis = _razobrat_opis()
    if not opis:
        return "описи учебника нет"
    po_glavam = {}
    for _f, g, _p in opis:
        po_glavam[g] = po_glavam.get(g, 0) + 1
    return "\\n".join(f"  · {g} — {n} рисунк(ов)"
                      for g, n in po_glavam.items() if g)


def nayti(o_chyom: str, skolko: int = 1) -> list:
    """[(путь, глава, подпись)] по словам запроса.

    Считаем совпадения слов запроса в подписи и в названии главы.
    Ничего не толкуем — просто ищем текстом.
    """
    zapros = (o_chyom or "").strip().lower()
    if not zapros:
        return []
    slova = [w for w in re.split(r"[^\\wа-яё]+", zapros) if len(w) > 3]
    if not slova:
        slova = [zapros]
    ocenki = []
    for fayl, glava, podpis in _razobrat_opis():
        seno = (podpis + " " + glava + " " + fayl).lower()
        ochki = sum(1 for w in slova if w in seno)
        # слово целиком в подписи весит больше, чем в имени файла
        ochki += sum(1 for w in slova if w in podpis.lower())
        if ochki:
            ocenki.append((ochki, fayl, glava, podpis))
    ocenki.sort(key=lambda x: -x[0])
    out = []
    for _o, fayl, glava, podpis in ocenki[:skolko]:
        p = _nayti_fayl(fayl)
        if p:
            out.append((p, glava, podpis))
    return out


# UCHEBNIK_V_RUKE_V1 - marker
'''


ST_SHEMA = '''        {"type": "function", "function": {
            "name": "moy_dnevnik",'''

NOV_SHEMA = '''        # UCHEBNIK_V_RUKE_V1: картинки из книги, по которой учили.
        # В памяти у неё лежит ПЕРЕСКАЗ рисунка, а не рисунок — можно
        # посмотреть заново, стоя перед живым графиком.
        {"type": "function", "function": {
            "name": "uchebnik",
            "description": (
                "ПОКАЗАТЬ картинку из книги «Торговый Хаос», по которой тебя "
                "учили: «приседающий бар», «фрактал», «волны AO», «окно "
                "объёма». Ты УВИДИШЬ сам рисунок и авторскую подпись к нему. "
                "Полезно, когда сомневаешься, как выглядит паттерн в "
                "учебнике — сравни с тем, что на графике сейчас."),
            "parameters": {"type": "object", "properties": {
                "о_чём": {"type": "string",
                          "description": "тема словами, например «приседающий бар»"}},
                "required": ["о_чём"]}}},
        {"type": "function", "function": {
            "name": "moy_dnevnik",'''

ST_RUKI = '''    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,'''

NOV_RUKI = '''    def _uchebnik(args: dict) -> str:
        """UCHEBNIK_V_RUKE_V1: показать рисунок из книги."""
        o = str(args.get("о_чём", "")).strip()
        try:
            import uchebnik as _u
            nashlos = _u.nayti(o, skolko=1)
        except Exception as e:
            return f"учебник не открылся: {e}"
        if not nashlos:
            try:
                import uchebnik as _u
                spisok = _u.temy()
            except Exception:
                spisok = ""
            return (f"по «{o}» в учебнике рисунка не нашёл. Что есть:\\n"
                    f"{spisok}")
        p, glava, podpis = nashlos[0]
        return (f"[КАДР: {p}] учебник · {glava} · {p.name}\\n"
                f"подпись автора: {podpis}")

    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,
            "uchebnik": _uchebnik,          # UCHEBNIK_V_RUKE_V1'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    uchebnik = koren / "Биржа" / "uchebnik.py"
    ruki = koren / "Биржа" / "ruki_treydera.py"

    opis = (koren / "GRONDHEIM_CITY" / "Академия" / "дисциплины" / "финансы"
            / "торговый_хаос" / "уроки" / "картинки" / "ОПИСЬ.md")
    if not opis.exists():
        print(f"✗ Нет описи картинок: {opis}")
        return 1

    print("\n1. Учебник — Биржа/uchebnik.py")
    if uchebnik.exists() and MARKER in uchebnik.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        try:
            ast.parse(UCHEBNIK_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if not SUHO:
            uchebnik.write_text(UCHEBNIK_PY, encoding="utf-8")
        print("  ✓ положен (ищет по авторской описи)")

    print("\n2. Рука учебника у трейдера")
    t = ruki.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        if "RASTYAZHKA_V1" not in t:
            print("  ✗ нет руки растяжки — картинку показать нечем.")
            print("    Накати сперва postavit_ruku_rastyazhki.py")
            return 1
        pary = [("схема", ST_SHEMA, NOV_SHEMA), ("руки", ST_RUKI, NOV_RUKI)]
        beda = [imya for imya, st, _ in pary if t.count(st) != 1]
        if beda:
            print(f"  ✗ якоря не найдены: {', '.join(beda)}")
            return 1
        novyy = t
        for _, st, nov in pary:
            novyy = novyy.replace(st, nov, 1)
        novyy += f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(ruki, ruki.with_suffix(
                f".py.bak_uchebnik_{datetime.now():%Y%m%d_%H%M%S}"))
            ruki.write_text(novyy, encoding="utf-8")
            print("  ✓ встала")

    if not SUHO:
        import py_compile
        for f in (uchebnik, ruki):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь она может сказать «покажи приседающий бар из")
        print("учебника» — и УВИДЕТЬ рисунок с авторской подписью,")
        print("стоя перед живым графиком.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
