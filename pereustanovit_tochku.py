# -*- coding: utf-8 -*-
"""
pereustanovit_tochku.py

ЗАЧЕМ
─────
Патчи идемпотентны: увидели свой маркер — пропустили. Это правильно и
спасает от двойной накатки. Но у него есть обратная сторона: если ты
поставил РАННЮЮ версию патча, а потом я его поправил, свежая версия
уже не сядет — маркер стоит, и она честно уходит ни с чем.

Ровно это и случилось: в коде лежит ранняя точка ноль (и, возможно,
ранний ключ), а исправления — рождение только в зоне конца волны,
полка точек по парам, честная подпись «структура позади», пробуждение
один раз вместо каждого бара — до диска не доехали.

ЧТО ДЕЛАЕТ
──────────
1. Находит копии, которые патчи оставили ПЕРЕД собой:
       Биржа/hooks.py.bak_tochka_*
       Биржа/stol.py.bak_tochka_*
       Биржа/council.py.bak_klyuch_*
2. Убеждается, что в копии маркера нет — то есть это действительно
   состояние ДО патча, а не чья-то поздняя копия.
3. Возвращает файлы из этих копий (сами копии не удаляет).
4. Тут же ставит свежие версии обоих патчей — по порядку, точка первой.

Итог: один двойной щелчок, на диске свежая версия, старые копии целы.

ЕСЛИ ЧТО-ТО НЕ ТАК
──────────────────
Скрипт ничего не удаляет и при первом же сомнении останавливается,
ничего не тронув. Свежие патчи должны лежать рядом, в том же корне:
postavit_tochku_nol.py и postavit_klyuch_probuzhdeniya.py.

Запуск: py pereustanovit_tochku.py
"""
import importlib.util
import shutil
import sys
from pathlib import Path

TOCHKA = "TOCHKA_ROZHDAETSYA_V1"
KLYUCH = "KLYUCH_PROBUZHDENIYA_V1"


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "council.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    put = input("Не нашёл корень. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


def _vernut(fayl: Path, shablon: str, marker: str) -> str:
    """Вернуть файл из копии, снятой перед патчем. Возвращает отчёт."""
    if not fayl.exists():
        return f"✗ нет файла {fayl.name}"
    tekst = fayl.read_text(encoding="utf-8")
    if marker not in tekst:
        return f"· {fayl.name}: патча нет, возвращать нечего"

    kopii = sorted(fayl.parent.glob(shablon))
    if not kopii:
        return (f"✗ {fayl.name}: маркер стоит, а копии {shablon} нет — "
                f"сам ничего не трону")
    # самая ранняя копия и есть состояние ДО патча
    do = kopii[0]
    if marker in do.read_text(encoding="utf-8"):
        return (f"✗ {fayl.name}: в копии {do.name} маркер уже есть — "
                f"это не «до патча», останавливаюсь")
    shutil.copy2(do, fayl)
    return f"✓ {fayl.name}: вернул из {do.name}"


def _pustit(koren: Path, imya: str) -> int:
    """Запустить соседний патч, не открывая второго окна."""
    put = koren / imya
    if not put.exists():
        print(f"✗ рядом нет {imya} — положи его в корень и позови снова")
        return 1
    spec = importlib.util.spec_from_file_location(f"_patch_{imya}", put)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main()


def main() -> int:
    koren = nayti_koren()
    print(f"Город: {koren}\n")

    otchyot = [
        _vernut(koren / "Биржа" / "hooks.py", "hooks.py.bak_tochka_*", TOCHKA),
        _vernut(koren / "Биржа" / "stol.py", "stol.py.bak_tochka_*", TOCHKA),
        _vernut(koren / "Биржа" / "council.py", "council.py.bak_klyuch_*",
                KLYUCH),
    ]
    for s in otchyot:
        print("  " + s)
    if any(s.startswith("✗") for s in otchyot):
        print("\n⚠️  Что-то не сошлось. Ничего дальше не делаю — покажи мне")
        print("   этот вывод, разберёмся без спешки.")
        return 1

    print("\n── ставлю свежую точку ──")
    if _pustit(koren, "postavit_tochku_nol.py"):
        return 1
    print("\n── ставлю свежий ключ ──")
    if _pustit(koren, "postavit_klyuch_probuzhdeniya.py"):
        return 1

    print("\n✓ на диске свежая версия. Старые копии не тронуты.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
