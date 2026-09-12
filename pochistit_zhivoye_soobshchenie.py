# -*- coding: utf-8 -*-
# ZHIVOYE_SOOBSHCHENIE_CHISTO_V1
"""
ЖИВОЕ СООБЩЕНИЕ — ПОД ПЕРВЫЙ УРОВЕНЬ

Слово Шефа 12.09: «а у них же там стол, и промпт динамический».

И правда. Бумагу я переписал, а мозг на каждый вопрос собирает ещё
одно сообщение — и в нём осталось то, что новой бумаге прямо
противоречит:

 · «Отвечай ключами brut_action (HOLD / MOVE_STOP / ADD / CLOSE) и
   brut_reason» — старый путь через json, отменённый ещё 10.09:
   решение отдаётся РУКОЙ;
 · «Не входишь — verdict REJECTED» — то же самое, вердикт в тексте;
 · «всё, что ниже про поиск входа и ТРИ МЕСТА» — три места входа мы
   убрали, место одно: конец хода;
 · в перечне рук стол описан через «точка, волна, откат» — это
   второй уровень, он их не знает.

Получалось как всегда: одно и то же в двух местах, и второе врёт.
Трейдер читает оба и делает по тому, что ближе к глазам.

ЧТО ДЕЛАЕТ ПАТЧ. Чистит эти четыре места в мозгах A06/A07/A08.
Ничего не добавляет — только приводит живое сообщение в согласие с
бумагой.

КУДА КЛАСТЬ ЭТОТ ФАЙЛ: в корень репы, рядом с main.py.

БЕЗОПАСНОСТЬ: .bak_zhivoe, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python pochistit_zhivoye_soobshchenie.py --suho
    python pochistit_zhivoye_soobshchenie.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "ZHIVOYE_SOOBSHCHENIE_CHISTO_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

import re

# Одни и те же места у A06/A07/A08 записаны своими словами (brut_,
# avan_, cons_). Ловим их ОБРАЗЦОМ, а не буквой: так патч не зависит
# от приставки слота и не промахнётся.

OBRAZCY = [
    # Меняем ТОЛЬКО СЛОВА, кавычки и переносы не трогаем: первая
    # попытка правила ловила закрывающую кавычку и ломала строку —
    # патч отказался сам, и хорошо, что отказался.
    ("ведение — приказ рукой",
     re.compile(r'Отвечай ключами \w+_action \(HOLD / MOVE_STOP / ADD / '),
     'Отдай приказ рукой otdat_prikaz: HOLD / MOVE_STOP / ADD / '),

    ("ведение — без ключей ответа",
     re.compile(r'CLOSE\) и \w+_reason\.'),
     'CLOSE. Словами решение не считается.'),

    ("вход — не вердикт, а WAIT",
     re.compile(r'Не входишь — verdict'),
     'Не работаешь — отдай'),

    ("вход — WAIT рукой",
     re.compile(r'REJECTED\. Никто не подложит'),
     'WAIT рукой. Никто не подложит'),

    ("стол без волн и откатов",
     re.compile(r'натяжение, точка, волна, откат;'),
     'приседающие, натяжение;'),

    ("растяжка — без волны",
     re.compile(r'100-140 баров, и разглядеть его целиком;'),
     'чтобы ход было видно целиком;'),
]


def _pravka(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0

    novy, sdelano = txt, []
    for imya, obrazec, zamena in OBRAZCY:
        novy, skolko = obrazec.subn(zamena, novy, count=1)
        if skolko:
            sdelano.append(imya)

    if not sdelano:
        return 0
    novy = novy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_zhivoe"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'} — "
          f"{len(sdelano)} из {len(OBRAZCY)}")
    return 1


def main():
    print()
    print("ЖИВОЕ СООБЩЕНИЕ ПОД ПЕРВЫЙ УРОВЕНЬ"
          + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    if not SLOTY.exists():
        print("!! слотов нет — запускать из корня репы")
        return
    vsego = sum(_pravka(s) for s in ("A06", "A07", "A08"))
    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто мозгов: {vsego}. Бэкапы — .bak_zhivoe")
    print("Бумага и живое сообщение больше не спорят.")
    print()


if __name__ == "__main__":
    main()
