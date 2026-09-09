# -*- coding: utf-8 -*-
"""
Убирает из промптов трейдеров строку полки «входы — три места входа».

Зачем: файл VHODY.md переехал в знания/ведение/, а промпт всё ещё
называет его среди того, что лежит на полке, и всё ещё обещает ТРИ
места входа — хотя ниже в том же промпте сказано «место одно, конец
хода». Трейдеру есть откуда пересказывать три входа: ему это прямо
написано.

Что делает:
  · ищет корень репозитория сам (от папки скрипта вверх);
  · обходит все слоты цеха торговый_хаос;
  · в каждом промпт.md убирает строку списка, начинающуюся с
    «- **входы**», и ставит маркер;
  · рядом кладёт .bak_tri_vhoda;
  · идемпотентен — второй запуск скажет «уже сделано».

Ключ --suho: только показать, ничего не писать.
"""

import sys
from pathlib import Path

MARKER = "<!-- POLKA_BEZ_TRYOH_VHODOV_V1 -->"
SUHO = "--suho" in sys.argv


def nayti_koren() -> Path:
    """Корень репы — папка, где лежит GRONDHEIM_CITY."""
    kandidat = Path(__file__).resolve().parent
    for papka in [kandidat, *kandidat.parents]:
        if (papka / "GRONDHEIM_CITY").is_dir():
            return papka
    print("Не нашёл GRONDHEIM_CITY рядом со скриптом.")
    print("Положи скрипт в корень репозитория и запусти оттуда.")
    input("Enter — закрыть...")
    sys.exit(1)


def main() -> None:
    koren = nayti_koren()
    sloty = koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"
    if not sloty.is_dir():
        print(f"Нет папки слотов: {sloty}")
        input("Enter — закрыть...")
        sys.exit(1)

    print(f"Корень: {koren}")
    tronuto = 0
    propushcheno = 0

    for promt in sorted(sloty.glob("*/промпт.md")):
        tekst = promt.read_text(encoding="utf-8")
        imya = f"{promt.parent.name}/промпт.md"

        if MARKER in tekst:
            print(f"  · {imya} — уже сделано")
            propushcheno += 1
            continue

        stroki = tekst.split("\n")
        ostavshiesya = [s for s in stroki if not s.lstrip().startswith("- **входы**")]

        if len(ostavshiesya) == len(stroki):
            print(f"  · {imya} — строки про входы нет, только маркер")
        else:
            ubrano = len(stroki) - len(ostavshiesya)
            print(f"  ✔ {imya} — убрано строк: {ubrano}")
            # список должен закрыться точкой, а не точкой с запятой
            for i in range(len(ostavshiesya) - 1, -1, -1):
                if ostavshiesya[i].lstrip().startswith("- **"):
                    if ostavshiesya[i].rstrip().endswith(";"):
                        ostavshiesya[i] = ostavshiesya[i].rstrip()[:-1] + "."
                    break

        novyy = "\n".join(ostavshiesya).rstrip("\n") + "\n\n" + MARKER + "\n"

        if SUHO:
            tronuto += 1
            continue

        promt.with_suffix(".md.bak_tri_vhoda").write_text(tekst, encoding="utf-8")
        promt.write_text(novyy, encoding="utf-8")
        tronuto += 1

    print()
    print(f"Итого: тронуто {tronuto}, пропущено {propushcheno}"
          + (" (сухой прогон, ничего не записано)" if SUHO else ""))
    input("Enter — закрыть...")


if __name__ == "__main__":
    main()
