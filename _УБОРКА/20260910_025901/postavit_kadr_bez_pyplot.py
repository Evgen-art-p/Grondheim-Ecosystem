# -*- coding: utf-8 -*-
# KADR_BEZ_PYPLOT_V1
"""
Кадр перестаёт валить сервер: рисование больше не идёт через общий
pyplot.

═══ ЧТО ЗА БОЛЕЗНЬ ═══

`Биржа/grafik.py` рисовал через `matplotlib.pyplot` — а pyplot держит
ОДИН общий склад картинок на весь процесс и не рассчитан на то, что
в него лезут из двух потоков сразу.

А лезут именно из двух. Кнопка «Взгляд» рисует кадр Шефа в отдельном
потоке (`run_in_executor`). Трейдер, отвечая на вопрос, рисует свой
кадр руками — в другом потоке, в тот же самый общий склад. Совпали по
времени — склад путается: в лучшем случае кадр выходит битым, в
худшем поток застревает и сервер перестаёт отвечать. Браузер это
видит как «Connection lost», страница перезагружается, разговор
теряется.

Ровно это и случилось 09.09: Шеф задал вопрос, пока рисовался кадр
по его же выбору.

═══ ЧТО ПАТЧ ДЕЛАЕТ ═══

Убирает общий склад. Картинка создаётся своим объектом (`Figure` +
`FigureCanvasAgg`), живёт только внутри своего вызова и никому не
мешает. Два потока теперь рисуют каждый своё, не встречаясь.

Четыре точечные правки в одном файле:
  1. вместо `pyplot` берём `Figure`, `FigureCanvasAgg`, `Rectangle`;
  2. картинка создаётся объектом, а не через общий склад;
  3. прямоугольник свечи — из `patches`, не из `plt`;
  4. `plt.close()` больше не нужен — картинка уходит сама.

Побочная польза: пропадает старая утечка. Раньше каждый забытый
`close` оставлял картинку в общем складе навсегда — за долгий день
их там накапливались сотни.

Вид кадра НЕ меняется: те же размеры, те же пропорции, те же цвета,
та же контрольная метка. Меняется только способ, которым он
изготавливается.

═══ ЧЕГО ПАТЧ НЕ ДЕЛАЕТ ═══

Не трогает кабинет, живой кадр, кнопку «Взгляд», руки трейдера и
данные. Только `Биржа/grafik.py`.

Запускать из корня репозитория:
    python postavit_kadr_bez_pyplot.py

Идемпотентен (маркер KADR_BEZ_PYPLOT_V1). Рядом .bak. Есть --suho.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

MARKER = "KADR_BEZ_PYPLOT_V1"
SUHO = "--suho" in sys.argv

PRAVKI = [
    (
        "импорт: берём объект картинки вместо общего склада",
        '''        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import MaxNLocator''',
        '''        import matplotlib
        matplotlib.use("Agg")
        # KADR_BEZ_PYPLOT_V1: НЕ pyplot. Общий склад картинок один на
        # весь процесс и не переживает, когда в него лезут из двух
        # потоков разом (кнопка Шефа и рука трейдера). Берём объект.
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.patches import Rectangle
        from matplotlib.ticker import MaxNLocator''',
    ),
    (
        "создание картинки своим объектом",
        '''    fig, (ax, axo) = plt.subplots(
        2, 1, figsize=(16, 9), dpi=110, sharex=True,
        gridspec_kw={"height_ratios": [7, 3], "hspace": 0.06})''',
        '''    # KADR_BEZ_PYPLOT_V1: своя картинка, не из общего склада.
    fig = Figure(figsize=(16, 9), dpi=110)
    FigureCanvasAgg(fig)
    ax, axo = fig.subplots(
        2, 1, sharex=True,
        gridspec_kw={"height_ratios": [7, 3], "hspace": 0.06})''',
    ),
    (
        "прямоугольник свечи — из patches",
        "            ax.add_patch(plt.Rectangle(",
        "            ax.add_patch(Rectangle(",
    ),
    (
        "закрывать нечего — картинка уходит сама",
        '''    fig.savefig(kuda, facecolor=C_FON, bbox_inches="tight")
    plt.close(fig)''',
        '''    fig.savefig(kuda, facecolor=C_FON, bbox_inches="tight")
    # KADR_BEZ_PYPLOT_V1: закрывать нечего — картинка нигде не
    # зарегистрирована и уходит сама, как только кончится вызов.''',
    ),
]

FAYL = Path("Биржа") / "grafik.py"


def nayti_koren() -> Path:
    kandidat = Path(__file__).resolve().parent
    for papka in [kandidat, *kandidat.parents]:
        if (papka / FAYL).is_file():
            return papka
    print("Не нашёл Биржа/grafik.py рядом со скриптом.")
    print("Положи скрипт в корень репозитория и запусти оттуда.")
    input("Enter — закрыть...")
    sys.exit(1)


def main() -> None:
    koren = nayti_koren()
    p = koren / FAYL
    tekst = p.read_text(encoding="utf-8")
    print(f"Файл: {p}")

    if MARKER in tekst:
        print("уже накачен — маркер на месте, ничего не трогаю")
        input("Enter — закрыть...")
        return

    # сперва проверяем ВСЕ якоря, потом правим — чтобы не оставить
    # файл наполовину переделанным
    for imya, staroe, _ in PRAVKI:
        skolko = tekst.count(staroe)
        if skolko != 1:
            print(f"⚠ «{imya}»: совпадений {skolko}, нужно ровно 1.")
            print("НИЧЕГО не меняю. Пришли Брату свой grafik.py.")
            input("Enter — закрыть...")
            return

    novyy = tekst
    for imya, staroe, novoe in PRAVKI:
        novyy = novyy.replace(staroe, novoe, 1)
        print(f"  ✔ {imya}")

    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"⚠ СИНТАКСИС СЛОМАН: {e} — НЕ сохраняю")
        input("Enter — закрыть...")
        return

    if SUHO:
        print("\nсухой прогон — ничего не записано")
        input("Enter — закрыть...")
        return

    bak = p.with_suffix(p.suffix + ".bak_bez_pyplot")
    if not bak.exists():
        bak.write_text(tekst, encoding="utf-8")
    p.write_text(novyy, encoding="utf-8")

    print("\n✔ готово, кадр больше не делит общий склад с соседом")
    print("  Бэкап рядом:", bak.name)
    print("\nКак проверить: нажми «Взгляд» и, пока рисуется, задай")
    print("трейдеру вопрос. Раньше на этом рвалась связь.")
    input("Enter — закрыть...")


if __name__ == "__main__":
    main()
