# -*- coding: utf-8 -*-
# MARKER: ZAPUSK_V_KONEC_V1
"""
ЧИНИТ ПОРЯДОК В stol.py — ОКОНЧАТЕЛЬНО.

В файле строка запуска (`if __name__ == "__main__":`) стояла ВЫШЕ
нескольких функций, которые она зовёт через slovami() — «_razbros_linij»,
«_volna_1_syro», «_uroven_sloma», «_urovni_zayavki», «_proshlye_popytki»
и другие лежат в файле НИЖЕ неё. Питон читает файл сверху вниз: когда
доходит до запуска, эти функции ещё не объявлены — и падает.

Это было в файле ДО всех сегодняшних патчей — просто раньше стол почти
не запускали напрямую (`py stol.py ...`), и никто на это не натыкался.

ЧТО ДЕЛАЕТ СКРИПТ
    Переставляет саму строку запуска в САМЫЙ КОНЕЦ файла — после ВСЕХ
    функций, какие бы там ни были. Тогда неважно, сколько ещё функций
    туда допишут в будущем: запуск всегда будет последним.

    Больше ничего не трогает. Смысл кода не меняется — только то, в
    каком порядке лежат куски файла.

Идемпотентен. .bak3 кладёт рядом с файлом. Путь ищет сам.

Проверить после:
    py stol.py EURUSD H4
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "ZAPUSK_V_KONEC_V1"


def _nayti_birzhu() -> Path:
    primety = ("stol.py",)
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
        s = input("папка (перетащи сюда Биржа): ").strip().strip('"')
        p = Path(s)
        if (p / "stol.py").exists():
            return p
        raise SystemExit("не та папка — там нет stol.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    n = int((input("которая? ").strip() or "1"))
    return nashli[n - 1]


ZAPUSK = ('if __name__ == "__main__":\n'
          '    # Проверка без модели и без денег: python stol.py EURUSD H1\n'
          '    s = sys.argv[1] if len(sys.argv) > 1 else "EURUSD"\n'
          '    tf = sys.argv[2] if len(sys.argv) > 2 else "H1"\n'
          '    print(f"Стол {s} {tf}:\\n")\n'
          '    print(slovami(nakryt(s, tf)))')


def main():
    b = _nayti_birzhu()
    s = b / "stol.py"
    text = s.read_text(encoding="utf-8")

    if MARKER in text:
        print("  . stol.py: уже поправлен, пропускаю")
        return

    if text.count(ZAPUSK) != 1:
        raise SystemExit(
            f"Не нашёл (или нашёл не один раз) строку запуска — "
            f"совпадений: {text.count(ZAPUSK)}. Ничего не трогаю.\n"
            f"Файл, похоже, уже другой — зови Брата смотреть руками.")

    # убираем блок запуска с текущего места (оставляем одну пустую
    # строку вместо него, чтобы не слипались соседние куски)
    novyy = text.replace(ZAPUSK, "", 1)
    # переносим его в самый конец, после ВСЕХ функций файла
    novyy = novyy.rstrip() + "\n\n\n" + ZAPUSK + "\n\n# " + MARKER + " - marker\n"

    ast.parse(novyy)
    shutil.copy2(s, s.with_suffix(".py.bak3"))
    s.write_text(novyy, encoding="utf-8")
    print("  + stol.py: запуск перенесён в конец файла (.bak3 рядом)")
    print("\nПроверить:")
    print("    py stol.py EURUSD H4")


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
