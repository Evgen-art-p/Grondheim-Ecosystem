# -*- coding: utf-8 -*-
# KADR_BEZ_ALLIGATORA_V1
"""
АЛЛИГАТОР УХОДИТ С КАДРА ТРЕЙДЕРА

ТРИ ПОПЫТКИ БУМАГОЙ НЕ ПОМОГЛИ. Убирали из взгляда, возвращали
компасом, закрывали список условий — и каждый раз он возвращался.
Прогон 11.09: восемь отказов из восьми, в шести главный довод —
Аллигатор. «Ниже всех линий», «переплетён», и прямое нарушение
канона: «разворотный бар не оторван от Аллигатора» (отрыв уже внутри
формулы, глазами его не проверяют).

Слово Шефа: линии не должны быть у него перед глазами.

ЧТО ДЕЛАЕТ ПАТЧ. Кадр трейдера рисуется БЕЗ трёх линий. Нечего
вплетать, если нечего видеть. Остаются свечи, AO, приседающие,
фракталы, стрелки разворотных — ровно то, чем он работает.

НАПРАВЛЕНИЕ ОН НЕ ТЕРЯЕТ: оно приходит строкой на столе, фактом —
цена выше линий или ниже. Считает его по-прежнему ядро, по тем же
линиям; меняется только то, что их не видно на картинке.

КАДР ШЕФА НЕ МЕНЯЕТСЯ. Рисовалка получает выключатель, а решает
зовущий: кабинет рисует с линиями, трейдеру уходит без. Один и тот
же код, разные кадры для разных глаз — и это честно: Шеф смотрит
как хозяин, трейдер как работник своего уровня.

Дорастёт до масштаба, где пасть и ангуляция читаются, — включим
обратно одной строкой.

БЕЗОПАСНОСТЬ: .bak_bezalli, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python ubrat_alligatora_s_kadra.py --suho
    python ubrat_alligatora_s_kadra.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "KADR_BEZ_ALLIGATORA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
GRAFIK = _REPO / "Биржа" / "grafik.py"
RUKI = _REPO / "Биржа" / "ruki_treydera.py"

# 1. рисовалка получает выключатель
STAROE_SIG = '''def narisovat(bars: list, alligator: dict, ao_series: list,
              symbol: str = "", timeframe: str = "",
              kuda: Optional[Path] = None,
              barov: int = BAROV_V_KADRE,
              fraktaly: Optional[dict] = None,
              prisedayushchie: Optional[list] = None) -> Optional[Path]:'''
NOVOE_SIG = '''def narisovat(bars: list, alligator: dict, ao_series: list,
              symbol: str = "", timeframe: str = "",
              kuda: Optional[Path] = None,
              barov: int = BAROV_V_KADRE,
              fraktaly: Optional[dict] = None,
              prisedayushchie: Optional[list] = None,
              linii: bool = True) -> Optional[Path]:'''

STAROE_RIS = '''    # Аллигатор — толсто, это главные линии кадра
    for ryad, cvet, imya in ((jaw, C_JAW, "Челюсть"),
                             (teeth, C_TEETH, "Зубы"),
                             (lips, C_LIPS, "Губы")):'''
NOVOE_RIS = '''    # Аллигатор — толсто, это главные линии кадра.
    # KADR_BEZ_ALLIGATORA_V1: но трейдеру первого уровня они не
    # рисуются вовсе. Три попытки запретить их бумагой провалились —
    # он возвращался к ним в каждом отказе. Нечего вплетать, если
    # нечего видеть. Направление он берёт строкой со стола.
    for ryad, cvet, imya in (() if not linii else
                             ((jaw, C_JAW, "Челюсть"),
                              (teeth, C_TEETH, "Зубы"),
                              (lips, C_LIPS, "Губы"))):'''

# 2. kadr() пробрасывает выключатель
STAROE_KADR = '''def kadr(symbol: str, timeframe: str, kuda: Optional[Path] = None,
         barov: int = BAROV_V_KADRE) -> Optional[Path]:'''
NOVOE_KADR = '''def kadr(symbol: str, timeframe: str, kuda: Optional[Path] = None,
         barov: int = BAROV_V_KADRE,
         linii: bool = True) -> Optional[Path]:'''

STAROE_VYZOV = '''    return narisovat(bs, al, ao, symbol, timeframe, kuda=kuda, barov=barov,
                     fraktaly=fr, prisedayushchie=_sq)'''
NOVOE_VYZOV = '''    return narisovat(bs, al, ao, symbol, timeframe, kuda=kuda, barov=barov,
                     fraktaly=fr, prisedayushchie=_sq,
                     linii=linii)          # KADR_BEZ_ALLIGATORA_V1'''

# 3. руки трейдера просят кадр без линий
PRAVKI_RUK = [
    ('''                put = grafik.kadr(symbol, tf)''',
     '''                # KADR_BEZ_ALLIGATORA_V1: трейдеру — без линий
                put = grafik.kadr(symbol, tf, linii=False)'''),
    ('''            put = grafik.kadr(symbol, tf)''',
     '''            # KADR_BEZ_ALLIGATORA_V1: трейдеру — без линий
            put = grafik.kadr(symbol, tf, linii=False)'''),
]


def main():
    print()
    print("КАДР БЕЗ АЛЛИГАТОРА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()

    vsego = 0

    print("1. РИСОВАЛКА — выключатель линий:")
    if not GRAFIK.exists():
        print("  grafik.py: файла нет")
    else:
        txt = GRAFIK.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  grafik.py: уже стоит")
        else:
            novy, ok = txt, True
            for imya, st, nv in (("сигнатура", STAROE_SIG, NOVOE_SIG),
                                 ("рисование", STAROE_RIS, NOVOE_RIS),
                                 ("kadr()", STAROE_KADR, NOVOE_KADR),
                                 ("вызов", STAROE_VYZOV, NOVOE_VYZOV)):
                if novy.count(st) != 1:
                    print(f"  grafik.py: ОТКАЗ на «{imya}» — "
                          f"{novy.count(st)} совпадений")
                    ok = False
                    break
                novy = novy.replace(st, nv, 1)
            if ok:
                try:
                    ast.parse(novy)
                    if not SUHO:
                        shutil.copy2(GRAFIK,
                                     GRAFIK.with_suffix(".py.bak_bezalli"))
                        GRAFIK.write_text(novy, encoding="utf-8")
                    print(f"  grafik.py: {'готов' if SUHO else 'поправлен'}")
                    vsego += 1
                except SyntaxError as e:
                    print(f"  grafik.py: ОТКАЗ — синтаксис сломан ({e})")

    print()
    print("2. РУКИ ТРЕЙДЕРА — просят кадр без линий:")
    if not RUKI.exists():
        print("  ruki_treydera.py: файла нет")
    else:
        txt = RUKI.read_text(encoding="utf-8")
        if MARKER in txt:
            print("  ruki_treydera.py: уже стоит")
        else:
            novy, n = txt, 0
            for st, nv in PRAVKI_RUK:
                if novy.count(st) >= 1:
                    novy = novy.replace(st, nv)
                    n += 1
            if not n:
                print("  ruki_treydera.py: ОТКАЗ — вызовов kadr не нашёл")
            else:
                try:
                    ast.parse(novy)
                    if not SUHO:
                        shutil.copy2(RUKI, RUKI.with_suffix(".py.bak_bezalli"))
                        RUKI.write_text(novy, encoding="utf-8")
                    print(f"  ruki_treydera.py: "
                          f"{'готов' if SUHO else 'поправлен'} ({n} мест)")
                    vsego += 1
                except SyntaxError as e:
                    print(f"  ruki_treydera.py: ОТКАЗ — синтаксис ({e})")

    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_bezalli")
    print("Кадр Шефа не изменился. У трейдера линий больше нет.")
    print()


if __name__ == "__main__":
    main()
