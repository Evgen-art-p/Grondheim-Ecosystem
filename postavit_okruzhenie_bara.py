# -*- coding: utf-8 -*-
# OKRUZHENIE_BARA_V1
"""
КРАЯ БАРА И СПРЕД — ГОТОВЫМИ ЧИСЛАМИ

Слово Шефа 12.09: «окружать нужно вместе с тенями. Сверху два
спреда, снизу спред — не важно, заявка это или стоп-лосс».

ПОЧЕМУ ЭТО ВАЖНО. В прогонах трейдер называл цену и стоп «на глаз»:
заявка 1.04205, стоп 1.04164 — сорок пунктов, взятых ниоткуда. Края
разворотного бара он не знал: ему их никто не давал, а формула
некрона отдаёт только ОДИН край — тот, по которому бар опознан.

ПРАВИЛО, по слову Шефа, — про сторону ЦЕНЫ, а не про сторону сделки:

    что СВЕРХУ бара — на ДВА спреда выше high
    что СНИЗУ бара  — на ОДИН спред ниже low

Отсюда:
    LONG : заявка = high + 2 спреда   стоп = low − 1 спред
    SHORT: заявка = low  − 1 спред    стоп = high + 2 спреда

Сверху платишь спред дважды (покупка идёт по Ask), снизу — один раз.

ЧТО ДЕЛАЕТ ПАТЧ. В первое сообщение трейдера кладётся блок с
готовыми числами: края бара и обе цены для каждой стороны. Считать
ему больше нечего — он выбирает сторону и называет цифры.

СПРЕД — 2 пункта, как в подготовке данных (`--spread 2.0` при точке
0.00001). Одно число на все инструменты: на золоте и евро он разный,
но пока гоняем по одной паре — сойдёт, поправим по факту.

КУДА КЛАСТЬ ЭТОТ ФАЙЛ: в корень репы, рядом с main.py.

БЕЗОПАСНОСТЬ: .bak_okruzh, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_okruzhenie_bara.py --suho
    python postavit_okruzhenie_bara.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "OKRUZHENIE_BARA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

TELO = '''

# ── OKRUZHENIE_BARA_V1: края бара и спред ─────────────────────
# Трейдер называл цену «на глаз»: заявка и стоп в сорока пунктах друг
# от друга, взятых ниоткуда. Краёв разворотного бара он не знал —
# формула некрона отдаёт только ОДИН край, тот, по которому бар
# опознан. Теперь даём оба и сразу считаем, куда встают ордера.
#
# Правило Шефа — про сторону ЦЕНЫ, не про сторону сделки:
#   сверху бара — на ДВА спреда выше high  (покупка идёт по Ask)
#   снизу бара  — на ОДИН спред ниже low

SPRED_PUNKTOV = 2.0        # как при подготовке данных: --spread 2.0


def _okruzhenie_blok(md: dict) -> str:
    try:
        _bary = (md or {}).get("bars") or []
        if not _bary:
            return ""
        b = _bary[-1]
        hi, lo = b.get("high"), b.get("low")
        if hi is None or lo is None:
            return ""
        _p = (md or {}).get("point") or 0.00001
        _sp = SPRED_PUNKTOV * _p
        _okr = lambda x: round(x, 6)
        long_zayavka = _okr(hi + 2 * _sp)
        long_stop = _okr(lo - _sp)
        short_zayavka = _okr(lo - _sp)
        short_stop = _okr(hi + 2 * _sp)
        return (
            "=== КРАЯ ТВОЕГО БАРА (окружать по ним) ===\\n"
            f"верх (high): {_okr(hi)}   низ (low): {_okr(lo)}\\n"
            f"спред {SPRED_PUNKTOV:g} пункта. Сверху бара платим ДВА "
            f"спреда, снизу — ОДИН.\\n"
            f"  LONG : заявка {long_zayavka}, стоп {long_stop}\\n"
            f"  SHORT: заявка {short_zayavka}, стоп {short_stop}\\n"
            "Окружают по ТЕНЯМ, не по телу. Считать тебе нечего — "
            "выбери сторону и назови эти числа в приказе.\\n\\n")
    except Exception as _e:
        print(f"[ОКРУЖЕНИЕ] края не посчитались ({_e})")
        return ""
'''

STAROE_VYZOV = '''        + _svoyo_blok()           # NE_ZAYDI_DVAZHDY_V1'''
NOVOE_VYZOV = '''        + _svoyo_blok()           # NE_ZAYDI_DVAZHDY_V1
        + _okruzhenie_blok(md)    # OKRUZHENIE_BARA_V1'''

STAROE_TELO_YAKOR = '''def _povod_blok(povod: str) -> str:'''


def _pravka(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0
    if txt.count(STAROE_VYZOV) != 1:
        print(f"  {slot}: ОТКАЗ — не нашёл, куда вставить "
              f"({txt.count(STAROE_VYZOV)} совпадений). "
              f"Сперва postavit_ne_zaydi_dvazhdy.py")
        return 0
    if txt.count(STAROE_TELO_YAKOR) != 1:
        print(f"  {slot}: ОТКАЗ — не нашёл места для тела")
        return 0

    novy = txt.replace(STAROE_VYZOV, NOVOE_VYZOV, 1)
    novy = novy.replace(STAROE_TELO_YAKOR,
                        TELO.strip("\n") + "\n\n" + STAROE_TELO_YAKOR, 1)
    novy = novy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_okruzh"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("ОКРУЖЕНИЕ БАРА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
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
        print(f"Тронуто мозгов: {vsego}. Бэкапы — .bak_okruzh")
    print("Сверху два спреда, снизу один. По теням, не по телу.")
    print()


if __name__ == "__main__":
    main()
