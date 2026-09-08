# -*- coding: utf-8 -*-
# PRISEDAYUSHCHIE_NA_KADRE_V1
"""
ЗАЧЕМ (08.09, слово Шефа): на кадре трейдера MFI нет вовсе. У Шефа в
терминале BW MFI отдельным окном внизу, а трейдер приседающий бар может
узнать только одним словом со стола — SQUAT/GREEN/FADE/FAKE, и только
про ПОСЛЕДНИЙ бар.

А по канону этого вечера смысл приседающему даёт МЕСТО, где он присел:
на дне после падения — упёрся в пол; на потолке после роста — толкают,
а не растёт; в середине хода — просто вдох. Одно и то же, три разных
вывода. Не видя, ГДЕ он стоит, трейдер этого правила выполнить не может.

Решение Шефа: не второе окно и не гистограмма объёма, а просто отметка —
«все просто красные кружки небольшие», строчкой внизу кадра.

ЧТО ДЕЛАЕТ ПАТЧ (Биржа/grafik.py, две функции):
  1. narisovat() принимает новый необязательный список приседающих и
     рисует строчку небольших красных кружков вдоль низа ценовой
     панели — по одному под каждым приседающим баром, ровно по его
     месту на оси. Совпадение с разворотником видно само: кружок
     окажется под тем же баром, где жёлтая стрелка.
  2. kadr() считает приседающие ЯДРОМ (detect_squat_bars) и передаёт
     их в narisovat.

ПОЧЕМУ ЯДРОМ, А НЕ СВОИМ СЧЁТОМ. В williams_core уже есть
detect_squat_bars(bars, point) — каноническая формула BWMFI
(MFI = (H−L)/point/volume): объём вырос, MFI упал. Считать то же самое
второй раз в рисовалке значит завести вторую правду о той же сущности —
на этом город уже обжигался. Зовём готовое.

Объём в барах есть: терминал кладёт tick_volume в поле "volume"
(mt5_feed._fetch), CSV — тем же полем (williams_core.read_mt5_csv).

ЧЕГО ПАТЧ НЕ ТРОГАЕТ: ни ядро, ни стол, ни промпт, ни поведение
трейдера. Только картинка. Ни одного нового числа в решении.

Запускать из корня репозитория:
    python postavit_prisedayushchie_na_kadr.py

Идемпотентен — смотрит маркер PRISEDAYUSHCHIE_NA_KADRE_V1 внутри
самого grafik.py. Второй раз ничего не тронет. Рядом кладёт .bak.
"""
from __future__ import annotations
from pathlib import Path

FAYL = "Биржа/grafik.py"
MARKER = "PRISEDAYUSHCHIE_NA_KADRE_V1"

ZAMENY = [
    # ── 1) цвет строчки — рядом с остальными цветами кадра ──────────
    (
        'C_AO_UP = "#2ea043"\n'
        'C_AO_DOWN = "#d92626"',

        'C_AO_UP = "#2ea043"\n'
        'C_AO_DOWN = "#d92626"\n'
        '# PRISEDAYUSHCHIE_NA_KADRE_V1: строчка приседающих внизу кадра.\n'
        '# Красный — как в терминале Шефа (BW MFI, красный столбик).\n'
        'C_SQUAT = "#d92626"',
    ),

    # ── 2) сигнатура narisovat — новый необязательный список ─────────
    (
        "def narisovat(bars: list, alligator: dict, ao_series: list,\n"
        '              symbol: str = "", timeframe: str = "",\n'
        "              kuda: Optional[Path] = None,\n"
        "              barov: int = BAROV_V_KADRE,\n"
        "              fraktaly: Optional[dict] = None) -> Optional[Path]:",

        "def narisovat(bars: list, alligator: dict, ao_series: list,\n"
        '              symbol: str = "", timeframe: str = "",\n'
        "              kuda: Optional[Path] = None,\n"
        "              barov: int = BAROV_V_KADRE,\n"
        "              fraktaly: Optional[dict] = None,\n"
        "              prisedayushchie: Optional[list] = None) -> Optional[Path]:",
    ),

    # ── 3) сама строчка — после разворотников, до оформления осей ────
    (
        "    except Exception as _e_rb:\n"
        '        print(f"[КАДР] разворотники не нарисовались: {_e_rb}")\n'
        "\n"
        "    ax.set_facecolor(C_FON)",

        "    except Exception as _e_rb:\n"
        '        print(f"[КАДР] разворотники не нарисовались: {_e_rb}")\n'
        "\n"
        "    # PRISEDAYUSHCHIE_NA_KADRE_V1: строчка приседающих вдоль низа.\n"
        "    # Не второе окно и не гистограмма объёма — просто отметка, ГДЕ\n"
        "    # рынок присел. Смысл ей придаёт место: на дне после падения —\n"
        "    # упёрся в пол, на потолке — толкают, а не растёт, в середине\n"
        "    # хода — вдох. Кадр кладёт факт, вывод делает смотрящий.\n"
        "    # Совпадение с разворотником отмечать отдельно не нужно: кружок\n"
        "    # окажется под тем же баром, где жёлтая стрелка.\n"
        "    if prisedayushchie:\n"
        "        try:\n"
        "            _sdvig_sq = len(bars) - n\n"
        "            _nizy = [x['low'] for x in b]\n"
        "            _razmah_sq = max(x['high'] for x in b) - min(_nizy)\n"
        "            _stroka_y = min(_nizy) - _razmah_sq * 0.045\n"
        "            _xs_sq = []\n"
        "            for _s in prisedayushchie:\n"
        "                _i = _s.get('bar_index')\n"
        "                if _i is None:\n"
        "                    continue\n"
        "                _k = _i - _sdvig_sq\n"
        "                if 0 <= _k < n:\n"
        "                    _xs_sq.append(_k)\n"
        "            if _xs_sq:\n"
        "                ax.plot(_xs_sq, [_stroka_y] * len(_xs_sq),\n"
        "                        linestyle='none', marker='o',\n"
        "                        markerfacecolor=C_SQUAT,\n"
        "                        markeredgecolor=C_SQUAT,\n"
        "                        markersize=4.5, zorder=5,\n"
        "                        label='приседающий')\n"
        "        except Exception as _e_sq:\n"
        '            print(f"[КАДР] приседающие не нарисовались: {_e_sq}")\n'
        "\n"
        "    ax.set_facecolor(C_FON)",
    ),

    # ── 4) kadr(): импорт ядра + счёт приседающих + передача ─────────
    (
        "    from feed_source import bars as source_bars\n"
        "    from williams_core import (compute_alligator, compute_ao_series,\n"
        "                               detect_fractals)",

        "    from feed_source import bars as source_bars\n"
        "    from williams_core import (compute_alligator, compute_ao_series,\n"
        "                               detect_fractals, detect_squat_bars)",
    ),
    (
        "    al = compute_alligator(highs, lows, point=point)\n"
        "    ao = compute_ao_series(highs, lows)\n"
        "    fr = detect_fractals(bs)\n"
        "    return narisovat(bs, al, ao, symbol, timeframe, kuda=kuda, barov=barov,\n"
        "                     fraktaly=fr)",

        "    al = compute_alligator(highs, lows, point=point)\n"
        "    ao = compute_ao_series(highs, lows)\n"
        "    fr = detect_fractals(bs)\n"
        "    # PRISEDAYUSHCHIE_NA_KADRE_V1: считаем ЯДРОМ, не своей формулой.\n"
        "    # detect_squat_bars — канон BWMFI: объём вырос, MFI упал.\n"
        "    # Второй счёт той же сущности в рисовалке = вторая правда.\n"
        "    try:\n"
        "        _sq = detect_squat_bars(bs, point=point).get('all') or []\n"
        "    except Exception as _e_sq:\n"
        '        print(f"[КАДР] приседающие не посчитались: {_e_sq}")\n'
        "        _sq = []\n"
        "    return narisovat(bs, al, ao, symbol, timeframe, kuda=kuda, barov=barov,\n"
        "                     fraktaly=fr, prisedayushchie=_sq)",
    ),
]


def main() -> None:
    root = Path(__file__).resolve().parent
    path = root / FAYL
    if not path.exists():
        print(f"НЕ НАШЁЛ: {path}")
        print("Запускать из корня репозитория (там, где лежит main.py).")
        return

    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        print("уже накачен — маркер на месте, ничего не трогаю")
        return

    # сверяем ВСЕ куски заранее: либо ложится целиком, либо ничего
    ne_nashel = []
    for i, (old, _new) in enumerate(ZAMENY, start=1):
        cnt = text.count(old)
        if cnt != 1:
            ne_nashel.append((i, cnt))

    if ne_nashel:
        print("⚠ Файл на диске отличается от ожидаемого — ничего не меняю:")
        for i, cnt in ne_nashel:
            print(f"   правка {i}: совпадений {cnt} (нужно ровно 1)")
        print("Пришли Брату свой Биржа/grafik.py — доведу под него.")
        return

    bak = path.with_suffix(path.suffix + ".bak_prisedayushchie")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")

    for i, (old, new) in enumerate(ZAMENY, start=1):
        text = text.replace(old, new, 1)
        print(f"правка {i}/{len(ZAMENY)} применена")

    text = text.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    path.write_text(text, encoding="utf-8")

    # проверка синтаксиса — чтобы не отдать сломанный файл
    try:
        import ast
        ast.parse(text)
        print("\nсинтаксис после правки — цел")
    except SyntaxError as e:
        print(f"\n⚠ СИНТАКСИС СЛОМАН: {e}")
        print(f"Верни из бэкапа: {bak.name}")
        return

    print(f"Готово: {FAYL} обновлён, {len(ZAMENY)} правок легли, маркер стоит.")
    print("Бэкап рядом:", bak.name)
    print("\nПроверить: нажми «👁 Взгляд» в кабинете — внизу кадра")
    print("должна появиться строчка небольших красных кружков.")


if __name__ == "__main__":
    main()
