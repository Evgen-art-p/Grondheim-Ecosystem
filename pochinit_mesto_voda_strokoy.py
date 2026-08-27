# -*- coding: utf-8 -*-
# MARKER: VODA_STROKOY_MESTO_V1
"""
ЧИНИТ ПОРЯДОК В stol.py — функция строки воды стояла ПОСЛЕ того места,
где стол запускается напрямую (py stol.py ...), и питон падал с
NameError: _voda_strokoy ещё не объявлена. Переносит функцию ВЫШЕ,
перед строкой запуска. Ничего в смысле не меняет — только порядок.

Идемпотентен. .bak кладёт рядом с файлом. Путь ищет сам.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "VODA_STROKOY_MESTO_V1"


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


OLD_IF = '''if __name__ == "__main__":
    # Проверка без модели и без денег: python stol.py EURUSD H1
    s = sys.argv[1] if len(sys.argv) > 1 else "EURUSD"
    tf = sys.argv[2] if len(sys.argv) > 2 else "H1"
    print(f"Стол {s} {tf}:\\n")
    print(slovami(nakryt(s, tf)))
'''

FUNC_BLOCK = "\n\n# ══════════════════════════════════════════════════════════════\n# VODA_NA_STOLE_V1 — вода отдельной строкой\n# ══════════════════════════════════════════════════════════════\n\ndef _voda_strokoy(p: dict) -> str:\n    # Вода на столе: сторона, оба этажа, и чем её нет, если её нет.\n    # Слово Шефа: вода не разрешает и не запрещает. Она лежит рядом с\n    # сигналом, и трейдер решает сам — в том числе войти против неё, со\n    # своим стопом. Поэтому здесь нет ни «можно», ни «нельзя»: только\n    # куда смотрит структура старших этажей.\n    v = (p or {}).get(\"вода\")\n    etazhi = (p or {}).get(\"вода_этажи\") or \"\"\n    pochemu = (p or {}).get(\"вода_почему\") or \"\"\n    svoy = (p or {}).get(\"направление_рабочего\")\n    hvost = (f\"   направление рабочего: {svoy}\" if svoy else \"\")\n    hvost += f\"   этаж: {(p or {}).get(\'этаж\') or \'—\'}\"\n    golova = f\"ВОДА: {v}\" if v in (\"BULL\", \"BEAR\") else \"ВОДА: НЕТ НА СТОЛЕ\"\n    if pochemu:\n        golova += f\"   ({pochemu})\"\n    golova += hvost\n    if etazhi:\n        golova += f\"\\n     этажи: {etazhi}\"\n    return golova\n"
   # страховка от опечатки при вставке


def main():
    b = _nayti_birzhu()
    s = b / "stol.py"
    text = s.read_text(encoding="utf-8")

    if MARKER in text:
        print("  . stol.py: уже поправлен, пропускаю")
        return

    tail_variant = FUNC_BLOCK + "\n# VODA_NA_STOLE_V1 - marker\n"
    if tail_variant not in text:
        raise SystemExit(
            "Не нашёл функцию _voda_strokoy в ожидаемом виде в конце файла — "
            "похоже, файл уже другой. Ничего не трогаю, зови Брата смотреть руками.")
    if text.count(OLD_IF) != 1:
        raise SystemExit(
            f"Не нашёл (или нашёл не один раз) строку запуска — "
            f"совпадений: {text.count(OLD_IF)}. Ничего не трогаю.")

    # убираем функцию из конца (маркер-строку оставляем)
    novyy = text.replace(tail_variant, "\n# VODA_NA_STOLE_V1 - marker\n")
    # вставляем функцию ПЕРЕД запуском
    novyy = novyy.replace(OLD_IF, FUNC_BLOCK.strip("\n") + "\n\n\n" + OLD_IF)

    novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
    ast.parse(novyy)
    shutil.copy2(s, s.with_suffix(".py.bak2"))
    s.write_text(novyy, encoding="utf-8")
    print("  + stol.py: функция воды перенесена выше запуска (.bak2 рядом)")
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
