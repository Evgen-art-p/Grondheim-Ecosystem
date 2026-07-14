# patch_tik_dobivka.py
# ─────────────────────────────────────────────────────────────
# SUTOCHNY_TIK_STOL_V1 — ДОБИВКА. Промпт видит ЧЕСТНЫЙ заряд.
#
# ⚠ МОЯ ОШИБКА, ПОЙМАННАЯ НА ВЫВОДЕ ШЕФА (13.07).
#   patch_sutochny_tik.py отчитался ТРЕМЯ пунктами вместо четырёх:
#   строки «✓ nakryt_stol_chisto(): промпт видит честный заряд» в выводе
#   НЕ БЫЛО. Матчер не нашёл метод (его переписал TRI_ETAZHA_V1, отступы
#   съехали) — и ПРОМОЛЧАЛ. Ровно та галочка, от которой я сам же
#   ставил стоп-кран в patch_dver_v_metki.py — а здесь не поставил.
#   «Пластик прячется в галочках» (§10 БИРЖА.md). Поймал Шеф, читая вывод.
#
# ЧЕМ ЭТО ПЛОХО ЖИВЬЁМ:
#   tik.py остужает на ДИСКЕ. Но nakryt_stol_chisto() — читающий конец,
#   он зовётся НА КАЖДОМ БАРЕ и берёт _charge из паспорта КАК ЕСТЬ.
#   Между тиками промпт видит ОКАМЕНЕВШИЙ заряд. Неделю не жал тик —
#   Илья всю неделю торгует с зарядом прошлого понедельника.
#   Дыра ровно в том месте, ради которого весь тик и делался.
#
# ЛЕЧЕНИЕ:
#   nakryt_stol_chisto() зовёт ostyt_po_vremeni() ПЕРЕД чтением.
#   Остужает В ПАМЯТИ — на диск НЕ пишет (контракт метода: «чтение
#   личности БЕЗ побочки», он на каждом баре, писать туда нельзя).
#   Осядет при следующем настоящем вдохе или тике. Честно.
#
# ПАТЧ ПАДАЕТ, ЕСЛИ НЕ ПОПАЛ. Больше никаких молчаливых галочек.
#
# ИДЕМПОТЕНТЕН. BACKUP: dvizhok.py.bak_stol
# Запуск из корня репо:  python patch_tik_dobivka.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DVIZHOK = ROOT / "жители" / "dvizhok.py"
MARK = "SUTOCHNY_TIK_STOL_V1"

VSTAVKA = '''        # SUTOCHNY_TIK_STOL_V1: промпт должен видеть ЧЕСТНЫЙ заряд, а не
        # окаменевший с прошлого тика. Этот метод зовётся НА КАЖДОМ БАРЕ —
        # значит он и есть главный читатель состояния. Остужаем В ПАМЯТИ:
        # на диск НЕ пишем (контракт метода — чтение БЕЗ побочки). Осадка
        # придёт со следующим настоящим вдохом или с tik.py.
        self.ostyt_po_vremeni()

'''


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ДОБИВКА ТИКА — промпт видит честный заряд" + " " * 25 + "║")
    print("║  SUTOCHNY_TIK_STOL_V1 · падает, если не попал" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    if not DVIZHOK.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    src = DVIZHOK.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ уже пропатчен — пропускаю (идемпотентно)")
        print()
        return

    if "def ostyt_po_vremeni" not in src:
        print("  ⚠ нет ostyt_po_vremeni — сначала patch_sutochny_tik.py")
        sys.exit(1)

    # ── находим тело nakryt_stol_chisto ────────────────────────
    i = src.find("    def nakryt_stol_chisto(self)")
    if i < 0:
        print("  ⚠ не нашёл nakryt_stol_chisto — движок изменился. СТОП.")
        print("    Смотри глазами: grep -n 'nakryt_stol_chisto' жители/dvizhok.py")
        sys.exit(1)

    # конец докстринга метода (он там точно есть — три кавычки дважды)
    d1 = src.find('"""', i)
    d2 = src.find('"""', d1 + 3)
    if d1 < 0 or d2 < 0:
        print("  ⚠ не нашёл докстринг nakryt_stol_chisto — СТОП")
        sys.exit(1)

    # вставляем СРАЗУ после докстринга, до return
    konec_doc = src.find("\n", d2) + 1

    # проверка: между докстрингом и return не должно быть уже нашего вызова
    hvost = src[konec_doc:konec_doc + 400]
    if "ostyt_po_vremeni" in hvost:
        print("  ✓ остывание уже зовётся — нечего делать")
        return

    bak = DVIZHOK.with_suffix(".py.bak_stol")
    if not bak.exists():
        shutil.copy2(DVIZHOK, bak)
        print(f"  ✓ бэкап: {bak.name}")

    novy = src[:konec_doc] + VSTAVKA + src[konec_doc:]

    # ── СТОП-КРАН: проверяем ФАКТ, а не намерение ──────────────
    # вырезаем тело метода заново из НОВОГО текста и смотрим глазами кода
    j = novy.find("    def nakryt_stol_chisto(self)")
    k = novy.find("\n    def ", j + 10)
    telo = novy[j:k if k > 0 else len(novy)]

    if "self.ostyt_po_vremeni()" not in telo:
        print("  ⚠ ВСТАВКА НЕ ПОПАЛА В ТЕЛО МЕТОДА. НЕ ПИШУ ФАЙЛ.")
        print("    Лучше стоп, чем отчёт «готово» при недоделанной работе.")
        sys.exit(1)

    # и что она ПЕРЕД return, а не после
    poz_ostyv = telo.find("self.ostyt_po_vremeni()")
    poz_return = telo.find("return {")
    if poz_return < 0 or poz_ostyv > poz_return:
        print("  ⚠ остывание НЕ ПЕРЕД return — бесполезно. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    # синтаксис — последняя проверка перед диском
    try:
        import ast
        ast.parse(novy)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    novy = novy.replace(
        "# `шесть·проверено·до·корня`",
        f"# {MARK}: nakryt_stol_chisto остужает ПЕРЕД чтением — промпт\n"
        "#   на каждом баре видит честный заряд, не окаменевший с тика.\n"
        "# `шесть·проверено·до·корня`", 1)

    DVIZHOK.write_text(novy, encoding="utf-8")

    print("  ✓ nakryt_stol_chisto(): остужает ПЕРЕД чтением")
    print("  ✓ проверено фактом: вызов В ТЕЛЕ метода, ДО return")
    print("  ✓ синтаксис цел")
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО — дыра закрыта" + " " * 45 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ЧТО БЫЛО НЕ ТАК:")
    print("    tik.py остужал на ДИСКЕ, а промпт на каждом баре читал")
    print("    заряд ИЗ ПАСПОРТА как есть. Неделю не жал тик — Илья всю")
    print("    неделю торговал с зарядом прошлого понедельника.")
    print()
    print("  ПРОВЕРКА ФАКТА (не галочки):")
    print("      python tik.py")
    print("    прогони ДВАЖДЫ подряд. Второй раз должен показать 0.0д")
    print("    тишины и не двинуть цифры — значит стол и диск сошлись.")
    print()


if __name__ == "__main__":
    main()
