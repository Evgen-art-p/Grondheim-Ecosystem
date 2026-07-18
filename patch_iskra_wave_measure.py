# -*- coding: utf-8 -*-
"""
ПАТЧ: ISKRA_WAVE_MEASURE_V1 — измерение волны + строгая проверка
структуры, как факты в wave_form (не фильтр).

ПРОВЕРЕНО РЕГРЕССИЕЙ ДО ПРИМЕНЕНИЯ (18.07): та же функция, что здесь
вживляется, прогнана на всех шести живых прогонах сессии (XAU/EUR ×
H4/H1/M30) и дала ЧИСЛО-В-ЧИСЛО те же результаты, что и стоячие
скрипты сессии (izmerit_ot_nulya_ao.py + proverit_strukturu.py):
  XAU H4: 47/130   EUR H4: 57/189
  XAU H1: 142/452  EUR H1: 177/522
  XAU M30: 152/446 EUR M30: 69/236
Все шесть совпали. Патчить раньше этой проверки было рано — не патчили.

ЧТО ДОБАВЛЯЕТ (в williams_core.py, ДО read_ao_wave_form):
  _ao_predydushchee_peresechenie, _ao_nachalo_okna,
  _ao_peresecheniya_v_okne, sudit_volnovuyu_strukturu,
  izmerit_volnovuyu_strukturu — новые функции, ничего существующего
  не трогают (аддитивно).

ЧТО МЕНЯЕТ (внутри read_ao_wave_form и _empty_wave_form):
  В wave_form добавляются поля:
    dlina                 — баров от начала окна (4 ноля AO назад) до
                             бара-кандидата, или None (не хватило истории)
    struktura_chitaetsya  — bool, читается ли пятёрка строго
    struktura_prichina    — текст причины (успех тоже объясняется)
  Ничего из существующих полей (bdb_dir, divergence_dir, anchor_ao_*
  и т.д.) НЕ убрано и НЕ изменено. Окно 100-140 НЕ используется как
  порог — только сами факты кладутся на стол (закон сессии 18.07:
  окно слабо коррелирует со структурой на XAU (+15 п.п.) и почти
  никак на EUR (+5 п.п.) — недостаточно для ворот).

ЗАПУСК: из корня репо
    python patch_iskra_wave_measure.py

Идемпотентно. Бэкап рядом (.bak).
"""
import ast
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "williams_core.py"
MARKER = "ISKRA_WAVE_MEASURE_V1"

ANCHOR_BEFORE = "def read_ao_wave_form("

NEW_FUNCTIONS = '''_WAVE_MEASURE_N_NULEY = 4   # ISKRA_WAVE_MEASURE_V1: канон 18.07, полный цикл 1-5


def _ao_predydushchee_peresechenie(ao_series: list, i: int) -> Optional[int]:
    """Индекс бара, где AO последний раз сменил знак, идя назад от i.
    Возвращает индекс ПЕРВОГО бара нового знака, или None (история
    кончилась/дыра в данных раньше)."""
    if i < 0 or i >= len(ao_series):
        return None
    cur = ao_series[i]
    if cur is None or cur == 0:
        return None
    znak = 1 if cur > 0 else -1
    j = i - 1
    while j >= 0:
        v = ao_series[j]
        if v is None:
            return None
        if (znak > 0 and v < 0) or (znak < 0 and v > 0):
            return j + 1
        j -= 1
    return None


def _ao_nachalo_okna(ao_series: list, i: int, n_nuley: int) -> Optional[int]:
    """Индекс начала окна — N пересечений нуля AO назад от бара i.
    None — истории не хватило отмотать N раз (не ошибка, честный факт)."""
    idx = i
    for _ in range(n_nuley):
        p = _ao_predydushchee_peresechenie(ao_series, idx)
        if p is None:
            return None
        idx = p - 1
    return idx


def _ao_peresecheniya_v_okne(ao_series: list, a: int, b: int) -> list:
    res = []
    for j in range(a + 1, b + 1):
        v, p = ao_series[j], ao_series[j - 1]
        if v is None or p is None:
            continue
        if (p < 0 <= v) or (p > 0 >= v):
            res.append(j)
    return res


def sudit_volnovuyu_strukturu(ao_series: list, start: int, kand: int,
                              storona: str) -> tuple:
    """
    ISKRA_WAVE_MEASURE_V1: строгий суд структуры горб-3 → ноль-4 →
    дивер-5 внутри окна [start, kand]. Протокол Шефа 18.07, починка
    той же даты (горб ищется ДО последнего ноля в окне, не как
    глобальный экстремум — иначе часто попадает в волну 5).

    Возвращает (читается: bool, причина: str) — причина всегда, даже
    при успехе (для прозрачности отчёта, не только для отладки брака).
    """
    seg = ao_series[start:kand + 1]
    if any(v is None for v in seg):
        return False, "дыры в AO"

    per = _ao_peresecheniya_v_okne(ao_series, start, kand)
    if not per:
        return False, "нет пересечений в окне"
    nol_i = per[-1]                      # ноль-4 = ПОСЛЕДНЕЕ пересечение

    if nol_i <= start + 1:
        return False, "ноль слишком рано"
    if storona == "BULL":
        gorb_i = min(range(start, nol_i), key=lambda j: ao_series[j])
    else:
        gorb_i = max(range(start, nol_i), key=lambda j: ao_series[j])
    gorb_v = ao_series[gorb_i]

    if nol_i >= kand:
        return False, "ноль на самом кандидате"
    if storona == "BULL":
        div_i = min(range(nol_i, kand + 1), key=lambda j: ao_series[j])
    else:
        div_i = max(range(nol_i, kand + 1), key=lambda j: ao_series[j])
    div_v = ao_series[div_i]

    if not (start <= gorb_i < nol_i <= div_i <= kand):
        return False, "порядок нарушен"

    if storona == "BULL":
        if not (div_v > gorb_v):
            return False, "волна 5 глубже волны 3"
    else:
        if not (div_v < gorb_v):
            return False, "волна 5 выше волны 3"

    n_per = len(per)
    if n_per > 5:
        return False, f"шум: {n_per} пересечений"
    if n_per < 2:
        return False, f"мало пересечений: {n_per}"

    return True, f"ОК ({n_per} перес.)"


def izmerit_volnovuyu_strukturu(bars: list, ao_series: list, storona,
                                n_nuley: int = _WAVE_MEASURE_N_NULEY,
                                i: Optional[int] = None) -> dict:
    """
    ISKRA_WAVE_MEASURE_V1 (18.07). ФАКТЫ структуры на стол, НЕ фильтр.
    Меряет длину движения от N-го пересечения нуля AO назад (по
    умолчанию 4 — канон Шефа, полный цикл 1-5) до бара-кандидата, и
    строго судит, читается ли внутри пятёрка (горб-3→ноль-4→дивер-5,
    правило Эллиотта). bars нужен только для длины истории — сама
    проверка идёт по ao_series.

    i=None → последний бар истории (обычный live-случай).
    storona — направление кандидата (BULL/BEAR), обычно form["bdb_dir"].

    Возвращает:
      {"dlina": int|None, "struktura_chitaetsya": bool,
       "struktura_prichina": str, "n_nuley": int}
    dlina=None — истории не хватило отмотать N нулей назад (честный
    факт короткой истории, не ошибка).
    """
    if storona not in ("BULL", "BEAR"):
        return {"dlina": None, "struktura_chitaetsya": False,
                "struktura_prichina": "нет направления кандидата",
                "n_nuley": n_nuley}
    if i is None:
        i = len(ao_series) - 1
    start = _ao_nachalo_okna(ao_series, i, n_nuley)
    if start is None:
        return {"dlina": None, "struktura_chitaetsya": False,
                "struktura_prichina": f"истории не хватило на {n_nuley} нулей назад",
                "n_nuley": n_nuley}
    dlina = i - start
    ok, why = sudit_volnovuyu_strukturu(ao_series, start, i, storona)
    return {"dlina": dlina, "struktura_chitaetsya": ok,
            "struktura_prichina": why, "n_nuley": n_nuley}


def read_ao_wave_form('''

OLD_RETURN = '''    return {
        "anchor_ao_max":        round(amax_v, 4) if amax_v is not None else None,
        "anchor_ao_min":        round(amin_v, 4) if amin_v is not None else None,
        "zero_cross_after_max": bool(zc_max),
        "zero_cross_after_min": bool(zc_min),
        "divergence_dir":       div_dir,
        "bdb_dir":              bdb_dir,
        "bdb_price":            bdb_price,
        "bar_date":             bars_w[-1]["date"] if bars_w else None,
        "window":               w,
    }'''

NEW_RETURN = '''    # ISKRA_WAVE_MEASURE_V1: факты структуры, НЕ фильтр. Меряется по
    # ПОЛНОМУ (не windowed) ao_series/bars — окно read_ao_wave_form
    # (100-150 баров) короче того, что нужно для 4 нулей AO назад
    # (медианы 94-116, хвост до 300+). Кандидат — последний бар общей
    # истории, он же последний бар окна (bars_w[-1] is bars[-1]).
    _wave = izmerit_volnovuyu_strukturu(bars, ao_series, bdb_dir)

    return {
        "anchor_ao_max":        round(amax_v, 4) if amax_v is not None else None,
        "anchor_ao_min":        round(amin_v, 4) if amin_v is not None else None,
        "zero_cross_after_max": bool(zc_max),
        "zero_cross_after_min": bool(zc_min),
        "divergence_dir":       div_dir,
        "bdb_dir":              bdb_dir,
        "bdb_price":            bdb_price,
        "bar_date":             bars_w[-1]["date"] if bars_w else None,
        "window":               w,
        "dlina":                _wave["dlina"],
        "struktura_chitaetsya": _wave["struktura_chitaetsya"],
        "struktura_prichina":   _wave["struktura_prichina"],
    }'''

OLD_EMPTY = '''def _empty_wave_form() -> dict:
    return {
        "anchor_ao_max": None, "anchor_ao_min": None,
        "zero_cross_after_max": False, "zero_cross_after_min": False,
        "divergence_dir": None, "bdb_dir": None, "bdb_price": None,
        "bar_date": None, "window": 0,
    }'''

NEW_EMPTY = '''def _empty_wave_form() -> dict:
    return {
        "anchor_ao_max": None, "anchor_ao_min": None,
        "zero_cross_after_max": False, "zero_cross_after_min": False,
        "divergence_dir": None, "bdb_dir": None, "bdb_price": None,
        "bar_date": None, "window": 0,
        # ISKRA_WAVE_MEASURE_V1: те же поля и в пустом слепке — иначе
        # читатель словит KeyError на холодном старте (тот же урок,
        # что REZINKA_DOBIVKA_V1 уже преподал этому файлу).
        "dlina": None, "struktura_chitaetsya": False,
        "struktura_prichina": "пустой слепок",
    }'''


def main():
    if not TARGET.exists():
        print(f"[ПАТЧ] ✗ не найден: {TARGET}")
        print("[ПАТЧ]   запускать из КОРНЯ репо Grondheim-Ecosystem")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — ничего не делаю")
        return 0

    for anchor, label in ((ANCHOR_BEFORE, "вставка функций"),
                          (OLD_RETURN, "return read_ao_wave_form"),
                          (OLD_EMPTY, "_empty_wave_form")):
        if anchor not in src:
            print(f"[ПАТЧ] ✗ якорь «{label}» не найден — файл уже другой")
            return 1

    src = src.replace(ANCHOR_BEFORE, NEW_FUNCTIONS, 1)
    src = src.replace(OLD_RETURN, NEW_RETURN, 1)
    src = src.replace(OLD_EMPTY, NEW_EMPTY, 1)
    src += f"\n# {MARKER} - marker\n"

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ результат не парсится: {e}")
        return 1

    shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] ✓ {MARKER} применён")
    print("[ПАТЧ]   wave_form теперь несёт dlina / struktura_chitaetsya /")
    print("[ПАТЧ]   struktura_prichina — факты, не фильтр")
    print("[ПАТЧ]   проверено регрессией на 6 датасетах ДО применения")
    return 0


if __name__ == "__main__":
    sys.exit(main())
