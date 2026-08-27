# -*- coding: utf-8 -*-
# MARKER: AC_VON_V1
"""
AC УХОДИТ ИЗ ГОРОДА.

СЛОВО ШЕФА (27.08)
    «Не лечи AC — в современных рынках скорость не нужна, его вычищай».

ЧТО УБИРАЕТСЯ
─────────────
    · сам расчёт AC в ядре (williams_core: compute_ac_series и всё,
      что от него кормилось)
    · AC со стола трейдера (приборы и строка вывода)
    · ЗОНА (зелёная/красная/серая) — она по определению AO+AC
      (iZone.mq4: AO растёт И AC растёт → зелёная). Без AC зоны не
      существует, и оставлять её половинкой было бы враньём: прибор
      показывал бы цвет, посчитанный неизвестно из чего.
    · строка отладки AC в hooks

ЧТО ОСТАЁТСЯ НЕТРОНУТЫМ
───────────────────────
AO — на месте целиком: значение, прошлое, переход нуля, направление,
пивоты, дивергенция. Аллигатор, фракталы, объём, натяжение, точка,
волна, откат, вода — всё как было. Убирается ТОЛЬКО ускорение.

ЕСЛИ ПОСЛЕ ЭТОГО ЧТО-ТО СПРОСИТ AC
──────────────────────────────────
Все места, что видел Брат, вычищены. Но если какой-то слот в городе
читал AC напрямую своим текстом — он получит пусто. Это не поломка:
скажи Брату, поправит и там.

Идемпотентен. .bak рядом. Пути ищет сам.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "AC_VON_V1"


def _nayti_birzhu() -> Path:
    primety = ("williams_core.py", "stol.py", "hooks.py")
    nashli = []
    korni = []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        mesta = [koren]
        try:
            mesta += [x for x in koren.iterdir() if x.is_dir()]
        except OSError:
            pass
        for p in mesta:
            if all((p / f).exists() for f in primety) and p not in nashli:
                nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл папку Биржа рядом со скриптом.")
        s = input("Перетащи сюда папку Биржа и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "williams_core.py").exists():
            return p
        raise SystemExit("не та папка — там нет williams_core.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


Y1_ST = '    ac_series  = compute_ac_series(ao_series)\n'
Y1_NO = ''
Y2_ST = '    ac_cur  = ac_series[-1]\n    ac_prev = next((v for v in reversed(ac_series[:-1]) if v is not None), None)\n'
Y2_NO = ''
Y3_ST = '    ac_direction = None\n    if ac_cur is not None and ac_prev is not None:\n        ac_direction = "UP" if ac_cur > ac_prev else "DOWN"\n'
Y3_NO = ''
Y4_ST = '        "ac": {\n            "value":      round(ac_cur,  8) if ac_cur  is not None else None,\n            "prev_value": round(ac_prev, 8) if ac_prev is not None else None,\n            "direction":  ac_direction,\n        },\n\n'
Y4_NO = ''
Y5_ST = 'def compute_ac_series(ao_series: list[Optional[float]]) -> list[Optional[float]]:\n    """\n    Accelerator Oscillator:\n      AC[i] = AO[i] - SMA(AO, 5)[i]\n    """\n    result: list[Optional[float]] = [None] * len(ao_series)\n    for i in range(len(ao_series)):\n        window = ao_series[max(0, i-4):i+1]\n        valid  = [v for v in window if v is not None]\n        if len(valid) < 5:\n            continue\n        cur = ao_series[i]\n        if cur is None:\n            continue  # WILLIAMS_CORE_TYPING_V2: структурно недостижимо\n            # (window включает cur; valid==5 доказывает cur не None) —\n            # запись существующего инварианта, не новая ветка поведения\n        result[i] = cur - sum(valid[-5:]) / 5\n    return result\n'
Y5_NO = '# AC_VON_V1: Accelerator Oscillator убран по слову Шефа (27.08):\n# «в современных рынках скорость не нужна, его вычищай». Формула была\n# AC = AO - SMA(AO,5); считался верно, но городу больше не нужен.\n# Вместе с ним ушла ЗОНА (AO+AC) — без AC её не существует.\n# AO остался целиком и работает как прежде.\n'
S1_ST = '        "зона": _zona(md),\n        "ac": {\n            "значение": (md.get("ac") or {}).get("value"),\n            "прошлое": (md.get("ac") or {}).get("prev_value"),\n            "растёт": (md.get("ac") or {}).get("direction"),\n        },\n'
S1_NO = '        # AC_VON_V1: AC и ЗОНА (AO+AC) убраны — скорость городу не нужна\n'
S2_ST = '\ndef _zona(md: dict) -> str:\n    """ЗЕЛЁНАЯ / КРАСНАЯ / СЕРАЯ — и ни слова о том, что с этим делать.\n\n    PRIBORY_NA_STOL_V1, по iZone.mq4 из Profitunity_MT4:\n        AO растёт И AC растёт  → зелёная\n        AO падает И AC падает  → красная\n        иначе                  → серая\n    """\n    ao_d = ((md or {}).get("ao") or {}).get("direction")\n    ac_d = ((md or {}).get("ac") or {}).get("direction")\n    if not ao_d or not ac_d:\n        return "—"\n    if ao_d == "UP" and ac_d == "UP":\n        return "ЗЕЛЁНАЯ"\n    if ao_d == "DOWN" and ac_d == "DOWN":\n        return "КРАСНАЯ"\n    return "СЕРАЯ"\n\n\n'
S2_NO = '\n# AC_VON_V1: функция зоны убрана вместе с AC. Зона по определению\n# считалась из AO+AC (iZone.mq4): оба растут — зелёная, оба падают —\n# красная. Без AC её посчитать нечем, а показывать цвет, собранный\n# из половины прибора, — врать трейдеру.\n\n\n'
S3_ST = '        f"зона (AO+AC): {p.get(\'зона\') or \'—\'}   "\n        f"AC: {(p.get(\'ac\') or {}).get(\'значение\')} "\n        f"({(p.get(\'ac\') or {}).get(\'растёт\') or \'—\'})",\n'
S3_NO = ''
H1_ST = '    ac = md["ac"]\n    print(f"  AC:       {ac[\'value\']} dir={ac[\'direction\']}")\n'
H1_NO = '    # AC_VON_V1: AC убран из города — печатать нечего\n'

YADRO = [
    ("расчёт ряда AC", Y1_ST, Y1_NO),
    ("текущий и прошлый AC", Y2_ST, Y2_NO),
    ("направление AC", Y3_ST, Y3_NO),
    ("AC в market_data", Y4_ST, Y4_NO),
    ("сама формула AC", Y5_ST, Y5_NO),
]

STOL = [
    ("AC и зона в приборах", S1_ST, S1_NO),
    ("функция зоны", S2_ST, S2_NO),
    ("строка вывода", S3_ST, S3_NO),
]

HOOKS = [
    ("отладочная печать AC", H1_ST, H1_NO),
]


def _pravka(path: Path, pary: list) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"  . {path.name}: уже вычищен, пропускаю")
        return
    novyy = text
    for nazv, staroe, novoe in pary:
        if novyy.count(staroe) != 1:
            raise SystemExit(
                f"  X {path.name}: кусок «{nazv}» не найден или не один "
                f"({novyy.count(staroe)}). Файл НЕ ТРОНУТ.")
        novyy = novyy.replace(staroe, novoe)
    novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
    ast.parse(novyy)
    shutil.copy2(path, path.with_suffix(path.suffix + ".bak_ac"))
    path.write_text(novyy, encoding="utf-8")
    print(f"  + {path.name}: AC убран (.bak_ac рядом)")


def main():
    b = _nayti_birzhu()
    print(f"\nБиржа: {b}\n")
    _pravka(b / "williams_core.py", YADRO)
    _pravka(b / "stol.py", STOL)
    _pravka(b / "hooks.py", HOOKS)
    print("\nГотово. AC больше не считается и на стол не ложится.")
    print("Заодно ушла ЗОНА — она была AO+AC, без AC её не бывает.")
    print("\nПроверить: py stol.py EURUSD H4  (из папки Биржа)")
    print("В выводе не должно остаться ни AC, ни строки «зона».")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
