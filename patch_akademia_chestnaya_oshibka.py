# -*- coding: utf-8 -*-
# AKADEMIA_CHESTNAYA_OSHIBKA_V1
"""
НАСТОЯЩАЯ ОШИБКА ПЕРЕСТАЁТ ПРЯТАТЬСЯ.

ЧТО БЫЛО СЛОМАНО (старый баг, не от последнего патча)
    _sprosit_uchenika() в норме возвращает ПАРУ: ответ и пометку про
    просев. А в трёх аварийных случаях — одну голую строку:
        паспорт не читается
        нет ключа OPENROUTER_API_KEY
        запрос к модели упал
    Вызывающий код всегда распаковывает пару. Строку он распаковать не
    может и падает с «too many values to unpack (expected 2)».

    В итоге на экран выходит эта бессмыслица, а НАСТОЯЩАЯ причина —
    что именно ответил OpenRouter — не доходит никогда. Три года можно
    чинить не то.

ЧТО СТАНОВИТСЯ
    Все три случая возвращают пару, как и успешный путь. На экране
    появляется живое сообщение: код ответа, текст ошибки, чего не
    хватает. Чинить станет что видно.

    Ошибка модели вдобавок укорачивается до 400 символов — иначе
    простыня JSON распирает окно чата и читать её невозможно.

ЗАПУСК из корня репо:
    python patch_akademia_chestnaya_oshibka.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "AKADEMIA_CHESTNAYA_OSHIBKA_V1"
TARGET = Path("Академия") / "ui_akademia.py"
BAK = Path("Академия") / "ui_akademia.py.bak_chestnaya_oshibka"

A1_OLD = '''        p = _read_json(dom / "passport.json", {}) or {}
        if not p:
            return "⚠ паспорт не читается — не могу собрать личность."
'''
A1_NEW = '''        p = _read_json(dom / "passport.json", {}) or {}
        if not p:
            # AKADEMIA_CHESTNAYA_OSHIBKA_V1: пара, а не строка — иначе
            # вызывающий падает на распаковке и прячет эту причину.
            return "⚠ паспорт не читается — не могу собрать личность.", ""
'''

A2_OLD = '''        _key = os.getenv("OPENROUTER_API_KEY", "")
        if not _key:
            return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
'''
A2_NEW = '''        _key = os.getenv("OPENROUTER_API_KEY", "")
        if not _key:
            # AKADEMIA_CHESTNAYA_OSHIBKA_V1: пара, а не строка.
            return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env.", ""
'''

A3_OLD = '''        except Exception as e:
            return f"⚠ не отозвался(лась): {e}"
'''
A3_NEW = '''        except Exception as e:
            # AKADEMIA_CHESTNAYA_OSHIBKA_V1: пара, а не строка. И текст
            # ошибки укорачиваем — иначе JSON-простыня распирает чат.
            _tekst = str(e)
            _telo = getattr(getattr(e, "response", None), "text", "")
            if _telo:
                _tekst = f"{_tekst} | ответ сервера: {_telo}"
            return f"⚠ не отозвался(лась): {_tekst[:400]}", ""
'''

PRAVKI = [
    ("паспорт не читается", A1_OLD, A1_NEW),
    ("нет ключа", A2_OLD, A2_NEW),
    ("запрос упал — показываем ответ сервера", A3_OLD, A3_NEW),
]


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

    novyy = src
    for imya, old, new in PRAVKI:
        n = novyy.count(old)
        if n != 1:
            print(f"✗ якорь «{imya}»: найден {n} раз (нужно 1). "
                  f"Файл изменился — патч НЕ применён, оригинал цел.")
            return 1
        novyy = novyy.replace(old, new, 1)
        print(f"  · {imya} — ок")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK.name}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print("\n  Спроси Нину ещё раз — теперь на экран выйдет НАСТОЯЩАЯ")
    print("  причина вместо «too many values to unpack».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
