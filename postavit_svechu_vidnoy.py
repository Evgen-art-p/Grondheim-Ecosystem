# -*- coding: utf-8 -*-
# SVECHA_VIDNA_V1
"""
РАСТУЩАЯ СВЕЧА БЫЛА НЕВИДИМА. И КОНТРОЛЬНАЯ МЕТКА — ЧТОБЫ ЗАКРЫТЬ СПОР.

═══ ЧАСТЬ 1: почему ВСЕ модели врали про график ═══

Цвета кадра до этого патча:

    фон              #fdf6e3   кремовый, почти белый
    растущая свеча   #f2f2f2   ПОЧТИ БЕЛЫЙ — на кремовом фоне
    падающая свеча   #3a3a3a   тёмно-серый

Контраст к фону, посчитанный по яркости:

    растущая свеча   1.04 : 1   ← единица означает «неотличимо»
    падающая свеча  10.54 : 1

Растущая свеча была видна ТОЛЬКО по волосяному контуру толщиной 0.9.
Провайдеры уменьшают картинку перед показом модели — контур
смазывается, и вместе с ним пропадает вся свеча.

Что при этом видит модель: на падающих участках плотную тёмную массу,
на растущих — пустое поле с редкими палочками теней. Направление
читается рельефом, а рельеф выбит ровно наполовину. Отсюда «последние
две свечи чёрные» про две растущие и путаница вверх-вниз.

Одно объяснение на все три модели — Haiku, Gemini, Sonnet. И на то,
почему те же модели верно читают числа: числа целы, выбита картинка.

═══ ПОЧЕМУ ПОЛУМЕРЫ НЕ ГОДЯТСЯ (проверено счётом) ═══

Просто затемнить фон мало: белая свеча на светло-сером даёт 1.43 —
всё ещё почти невидимка при падающей 9.87. Перекос всемеро.

Сделать обе свечи тёмными тоже нельзя: к фону они видны, но КОНТРАСТ
МЕЖДУ НИМИ падает до 1.1-2.0 — направление снова не прочесть.

Одна свеча должна быть светлой, другая тёмной. А для этого фон обязан
быть ТЁМНЫМ. То есть ровно так, как в терминале Шефа, который он сам
читает без труда.

    фон              #0e1218
    растущая         #f5f5f5   к фону 17.2 : 1
    падающая         #cf3b2c   к фону  3.9 : 1
    между собой                       4.5 : 1   ← это и есть направление

Линии Аллигатора светлеют под тёмный фон (челюсть синяя, зубы красные,
губы зелёные — канон сохраняется), сетка и подписи тоже. Контур свечи
и доджи-полоска утолщаются, чтобы пережить уменьшение.

═══ ЧАСТЬ 2: контрольная метка ═══

Шеф сомневается: а вдруг они вообще не видят картинку и врут?
Спор решается меткой, которую НЕЛЬЗЯ угадать.

В левый верхний угол кадра ставится код из двух букв и двух цифр,
новый при каждой отрисовке. Его нет ни на столе, ни в промпте, ни в
знаниях — только на картинке. Он же печатается в консоль.

    Спроси трейдера: «какой код в левом верхнем углу кадра?»

    Назвал верно  → картинку ВИДИТ, и всё прежнее враньё было из-за
                    невидимой свечи (Часть 1).
    Не назвал     → НЕ ВИДИТ вовсе, цвета ни при чём, копать надо
                    маршрут до модели.

Одна фраза — и гадать больше не придётся ни про одну модель.

═══ ЧЕГО ПАТЧ НЕ ТРОГАЕТ ═══
Ни ядро, ни стол, ни промпт, ни знания, ни решение трейдера. Только
как выглядит картинка.

Запускать из корня репозитория:
    python postavit_svechu_vidnoy.py

Идемпотентен (маркер SVECHA_VIDNA_V1). Сверяет все куски заранее:
либо ложится целиком, либо не трогает ничего. Рядом .bak.
Совместим с postavit_prisedayushchie_na_kadr.py в любом порядке.
"""
from __future__ import annotations
from pathlib import Path

FAYL = "Биржа/grafik.py"
MARKER = "SVECHA_VIDNA_V1"

ZAMENY = [
    # ── 1) палитра: тёмный кадр, как в терминале ────────────────────
    (
        '# ── Цвета. Аллигатор канонический: челюсть синяя, зубы красные,\n'
        '# губы зелёные. Свечи — не «красное/зелёное» в тон линиям, иначе\n'
        '# сливается: тёмная и светлая.\n'
        'C_UP = "#f2f2f2"\n'
        'C_DOWN = "#3a3a3a"\n'
        'C_KRAY = "#1a1a1a"\n'
        'C_JAW = "#1f6feb"\n'
        'C_TEETH = "#d92626"\n'
        'C_LIPS = "#2ea043"\n'
        'C_FON = "#fdf6e3"\n'
        'C_AO_UP = "#2ea043"\n'
        'C_AO_DOWN = "#d92626"',

        '# ── Цвета. Аллигатор канонический: челюсть синяя, зубы красные,\n'
        '# губы зелёные.\n'
        '#\n'
        '# SVECHA_VIDNA_V1 — БЫЛО СЛОМАНО, И ЭТО ЛОМАЛО ВСЁ ОСТАЛЬНОЕ.\n'
        '# Фон был #fdf6e3 (кремовый), растущая свеча #f2f2f2 (почти\n'
        '# белая). Контраст растущей к фону — 1.04 к 1, то есть\n'
        '# НЕОТЛИЧИМО; падающей — 10.5 к 1. Растущую свечу держал только\n'
        '# волосяной контур, а провайдеры уменьшают кадр перед показом\n'
        '# модели, и контур смазывался. Модель видела тёмную массу на\n'
        '# падениях и пустоту на росте — и путала направление. Так было\n'
        '# у ВСЕХ моделей сразу: Haiku, Gemini, Sonnet.\n'
        '#\n'
        '# Почему именно тёмный фон. Одна свеча обязана быть светлой,\n'
        '# другая тёмной — иначе не отличить рост от падения. Светлая\n'
        '# свеча требует тёмного фона. Это ровно то, как устроен\n'
        '# терминал Шефа, который он читает без труда.\n'
        '#   растущая к фону 17.2:1 · падающая 3.9:1 · между собой 4.5:1\n'
        'C_UP = "#f5f5f5"      # растущая — светлая\n'
        'C_DOWN = "#cf3b2c"    # падающая — красная\n'
        'C_KRAY = "#0a0d11"    # контур: тёмный, отделяет свечу от свечи\n'
        'C_JAW = "#4d9bff"     # челюсть синяя — светлее под тёмный фон\n'
        'C_TEETH = "#ff5c5c"   # зубы красные\n'
        'C_LIPS = "#3ddc6b"    # губы зелёные\n'
        'C_FON = "#0e1218"     # было #fdf6e3 — см. выше\n'
        'C_AO_UP = "#3ddc6b"\n'
        'C_AO_DOWN = "#ff5c5c"\n'
        '# SVECHA_VIDNA_V1: сетка, подписи и рамки — под тёмный фон.\n'
        'C_SETKA = "#ffffff1f"\n'
        'C_TEKST = "#e6edf3"\n'
        'C_RAMKA = "#ffffff40"',
    ),

    # ── 2) контур толще: переживает уменьшение картинки ──────────────
    (
        "        telo = abs(c - o)\n"
        "        if telo < (h - l) * 0.02:\n"
        "            ax.plot([i - shirina / 2, i + shirina / 2], [c, c],\n"
        "                    color=C_KRAY, linewidth=1.4, zorder=3)\n"
        "        else:\n"
        "            ax.add_patch(plt.Rectangle(\n"
        "                (i - shirina / 2, min(o, c)), shirina, telo,\n"
        "                facecolor=C_UP if rastet else C_DOWN,\n"
        "                edgecolor=C_KRAY, linewidth=0.9, zorder=3))",

        "        telo = abs(c - o)\n"
        "        # SVECHA_VIDNA_V1: линии толще. Волосяная линия не\n"
        "        # переживает уменьшение кадра на стороне провайдера —\n"
        "        # смазывается в фон вместе со всей свечой. Доджи рисуем\n"
        "        # светлым, иначе на тёмном фоне бар пропадает совсем.\n"
        "        if telo < (h - l) * 0.02:\n"
        "            ax.plot([i - shirina / 2, i + shirina / 2], [c, c],\n"
        "                    color=C_UP, linewidth=2.2, zorder=3)\n"
        "        else:\n"
        "            ax.add_patch(plt.Rectangle(\n"
        "                (i - shirina / 2, min(o, c)), shirina, telo,\n"
        "                facecolor=C_UP if rastet else C_DOWN,\n"
        "                edgecolor=C_KRAY, linewidth=1.6, zorder=3))",
    ),

    # ── 3) тень свечи — светлой, иначе тонет в тёмном фоне ───────────
    (
        '        ax.plot([i, i], [l, h], color=C_KRAY, linewidth=1.1, zorder=2)',
        '        # SVECHA_VIDNA_V1: тень светлая — на тёмном фоне тёмная\n'
        '        # тень пропадала вместе с размахом бара.\n'
        '        ax.plot([i, i], [l, h], color="#9fb0c0", linewidth=1.3,\n'
        '                zorder=2)',
    ),

    # ── 4) оформление ценовой панели под тёмный фон ──────────────────
    (
        '    ax.set_facecolor(C_FON)\n'
        '    ax.grid(True, color="#00000012", linewidth=0.8)',
        '    ax.set_facecolor(C_FON)\n'
        '    ax.grid(True, color=C_SETKA, linewidth=0.8)   # SVECHA_VIDNA_V1',
    ),
    (
        '        ax.set_title(zag, fontsize=15, loc="left", color="#222")',
        '        ax.set_title(zag, fontsize=15, loc="left", color=C_TEKST)',
    ),
    (
        '    ax.tick_params(labelsize=10)\n'
        '    for s in ax.spines.values():\n'
        '        s.set_color("#00000030")',
        '    ax.tick_params(labelsize=10, colors=C_TEKST)   # SVECHA_VIDNA_V1\n'
        '    for s in ax.spines.values():\n'
        '        s.set_color(C_RAMKA)',
    ),

    # ── 5) оформление панели AO под тёмный фон ───────────────────────
    (
        '    axo.axhline(0, color="#00000055", linewidth=1.1, zorder=2)\n'
        '    axo.set_facecolor(C_FON)\n'
        '    axo.grid(True, color="#00000012", linewidth=0.8)\n'
        '    axo.set_ylabel("AO", fontsize=11)\n'
        '    axo.tick_params(labelsize=9)\n'
        '    for s in axo.spines.values():\n'
        '        s.set_color("#00000030")',
        '    # SVECHA_VIDNA_V1: нулевая линия и подписи — под тёмный фон.\n'
        '    axo.axhline(0, color="#ffffff66", linewidth=1.3, zorder=2)\n'
        '    axo.set_facecolor(C_FON)\n'
        '    axo.grid(True, color=C_SETKA, linewidth=0.8)\n'
        '    axo.set_ylabel("AO", fontsize=11, color=C_TEKST)\n'
        '    axo.tick_params(labelsize=9, colors=C_TEKST)\n'
        '    for s in axo.spines.values():\n'
        '        s.set_color(C_RAMKA)',
    ),

    # ── 6) контрольная метка + печать в консоль ──────────────────────
    (
        "    kuda = Path(kuda)\n"
        "    kuda.parent.mkdir(parents=True, exist_ok=True)\n"
        '    fig.savefig(kuda, facecolor=C_FON, bbox_inches="tight")\n'
        "    plt.close(fig)\n"
        "    return kuda",

        "    # SVECHA_VIDNA_V1: КОНТРОЛЬНАЯ МЕТКА. Код из двух букв и двух\n"
        "    # цифр, новый при каждой отрисовке. Его нет ни на столе, ни в\n"
        "    # промпте, ни в знаниях — ТОЛЬКО на картинке. Спроси трейдера\n"
        "    # «какой код в левом верхнем углу кадра?»: назвал — видит,\n"
        "    # не назвал — не видит, и никакие цвета этого не объяснят.\n"
        "    try:\n"
        "        import random as _rnd\n"
        "        _bukvy = 'ABCDEFGHJKLMNPQRSTUVWXYZ'\n"
        "        _kod = (_rnd.choice(_bukvy) + _rnd.choice(_bukvy)\n"
        "                + f'{_rnd.randint(10, 99)}')\n"
        "        fig.text(0.012, 0.985, _kod, ha='left', va='top',\n"
        "                 fontsize=18, color='#ffd866', family='monospace',\n"
        "                 fontweight='bold', zorder=20)\n"
        "        print(f'[КАДР] контрольная метка: {_kod}')\n"
        "    except Exception as _e_kod:\n"
        "        print(f'[КАДР] метка не встала: {_e_kod}')\n"
        "\n"
        "    kuda = Path(kuda)\n"
        "    kuda.parent.mkdir(parents=True, exist_ok=True)\n"
        '    fig.savefig(kuda, facecolor=C_FON, bbox_inches="tight")\n'
        "    plt.close(fig)\n"
        "    return kuda",
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

    bracket = []
    for i, (old, _new) in enumerate(ZAMENY, start=1):
        cnt = text.count(old)
        if cnt != 1:
            bracket.append((i, cnt))

    if bracket:
        print("⚠ Файл на диске отличается от ожидаемого — НИЧЕГО не меняю:")
        for i, cnt in bracket:
            print(f"   правка {i}: совпадений {cnt} (нужно ровно 1)")
        print("Пришли Брату свой Биржа/grafik.py — доведу под него.")
        return

    bak = path.with_suffix(path.suffix + ".bak_svecha")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")

    for i, (old, new) in enumerate(ZAMENY, start=1):
        text = text.replace(old, new, 1)
        print(f"правка {i}/{len(ZAMENY)} применена")

    text = text.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        import ast
        ast.parse(text)
    except SyntaxError as e:
        print(f"\n⚠ СИНТАКСИС СЛОМАН: {e} — НЕ сохраняю")
        return

    path.write_text(text, encoding="utf-8")
    print("\nсинтаксис цел, файл сохранён. Бэкап рядом:", bak.name)
    print("\n══ ЧТО УВИДИШЬ ══")
    print("  Кадр станет тёмным, как твой терминал: светлые свечи —")
    print("  растущие, красные — падающие, линии Аллигатора ярче.")
    print("\n══ КАК ПРОВЕРИТЬ, ВИДИТ ЛИ ОН ВООБЩЕ ══")
    print("  1. Жмёшь «👁 Взгляд» — в консоли появится")
    print("     [КАДР] контрольная метка: XY42")
    print("  2. Спрашиваешь трейдера: «какой код в левом верхнем углу?»")
    print("  3. Назвал верно  → ВИДИТ. Значит прежнее враньё было")
    print("        из-за невидимой растущей свечи.")
    print("     Не назвал     → НЕ ВИДИТ, и копать надо маршрут.")


if __name__ == "__main__":
    main()
