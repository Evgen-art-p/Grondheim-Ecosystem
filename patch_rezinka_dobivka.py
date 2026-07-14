# patch_rezinka_dobivka.py
# ─────────────────────────────────────────────────────────────
# REZINKA_DOBIVKA_V1 — МОЯ ОШИБКА. ВТОРОЙ ЧИТАТЕЛЬ ОСТАЛСЯ СЛЕПЫМ.
#
# ⚠ ЭТО НЕ НОВАЯ БОЛЕЗНЬ. ЭТО НЕДОДЕЛАННЫЙ ПАТЧ РЕЗИНКИ.
#
# СИМПТОМ (лог Шефа, 14.07 — девять кандидатов подряд):
#   кандидат 2/454 (BEAR): спуск не нашёл точку (компас=BEAR)
#   кандидат 3/454 (BEAR): спуск не нашёл точку (компас=BEAR)
#   кандидат 6/454 (BEAR): спуск не нашёл точку (компас=BEAR)
#   ...
#   Вера: прогонов 148 · нашла 19 · ПОДТВЕРДИЛОСЬ 0
#
# КОМПАС ЕСТЬ — а спуск всё равно пустой. Значит дело НЕ в компасе
# (я успел ляпнуть, что «резинка сломала Искру» — это была ДОГАДКА,
# и она неверна). Дело в bdb_dir.
#
# ── ПРИЧИНА (найдена чтением кода, не гаданием) ──
# У detect_divergent_bar ДВА ЧИТАТЕЛЯ:
#
#   1. build_market_data (williams_core:979)
#      → REZINKA_DZHASTIN_V1 научил его передавать lips_series ✓
#      → резинка считается → bdb_strong работает → 454 кандидата
#
#   2. read_ao_wave_form (williams_core:848)   ← Я ЕГО ПРОПУСТИЛ
#      → зовёт detect_divergent_bar БЕЗ lips_series ✗
#      → lips_series=None → compute_rubber_band не считает
#      → is_peak=False ВСЕГДА → bdb_strong=False ВСЕГДА
#      → bdb_dir=None ВСЕГДА
#
# А спуск Искры (A01/мозг.py:_descend) смотрит именно на bdb_dir:
#       bdb_dir = form.get("bdb_dir")
#       if bdb_dir == compass:  return {"found": True, ...}
#
# ⇒ Сито 1 говорит «есть точка» (по резинке через build_market_data),
#   а спуск Искры смотрит через read_ao_wave_form и НЕ ВИДИТ НИЧЕГО.
#   Два органа разошлись. Я починил одного читателя и забыл второго.
#
# ТОТ ЖЕ КЛАСС, ЧТО ПЯТЬ КОПИЙ МАГИКА И ДВА ПИСАТЕЛЯ ПОЗИЦИЙ:
# одна сущность — несколько читателей, лечим одного.
# За сутки это ТРЕТИЙ раз. Урок в §10а БИРЖА.md написан — и я на нём
# же поскользнулся.
#
# ── ЛЕЧЕНИЕ (одна строка) ──
# read_ao_wave_form сам считает Аллигатор? Нет — он принимает
# teeth_series снаружи. Значит и lips_series надо принять снаружи,
# тем же путём. Правим ОБА конца: сигнатуру и всех, кто зовёт.
#
# ИДЕМПОТЕНТЕН. BACKUP: williams_core.py.bak_dobivka
# Запуск из корня репо:  python patch_rezinka_dobivka.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "Биржа" / "williams_core.py"
MARK = "REZINKA_DOBIVKA_V1"


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ДОБИВКА РЕЗИНКИ — второй читатель остался слепым" + " " * 18 + "║")
    print("║  REZINKA_DOBIVKA_V1 · моя ошибка, чиню" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    if not CORE.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    src = CORE.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ уже пропатчен — пропускаю (идемпотентно)")
        print()
        return

    if "REZINKA_DZHASTIN_V1" not in src:
        print("  ⚠ сначала patch_rezinka_dzhastin.py — этот встаёт поверх")
        sys.exit(1)

    bak = CORE.with_suffix(".py.bak_dobivka")
    if not bak.exists():
        shutil.copy2(CORE, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── 1. Сигнатура read_ao_wave_form: принять Губы ────────────
    staraya = ("def read_ao_wave_form(\n"
               "    bars:         list,\n"
               "    ao_series:    list,\n"
               "    teeth_series: Optional[list],")
    novaya = ("def read_ao_wave_form(\n"
              "    bars:         list,\n"
              "    ao_series:    list,\n"
              "    teeth_series: Optional[list],\n"
              "    lips_series:  Optional[list] = None,   # REZINKA_DOBIVKA_V1")
    if staraya not in src:
        print("  ⚠ не нашёл сигнатуру read_ao_wave_form. СТОП.")
        sys.exit(1)
    src = src.replace(staraya, novaya, 1)
    print("  ✓ read_ao_wave_form принимает lips_series")

    # ── 2. Нарезка окна для Губ (как для Зубов) ─────────────────
    # ищем, где режется teeth_w, и режем lips_w рядом
    m = re.search(r"^(\s*)teeth_w\s*=\s*(.+)$", src, re.M)
    if not m:
        print("  ⚠ не нашёл нарезку teeth_w. СТОП.")
        sys.exit(1)
    otstup, vyrazhenie = m.group(1), m.group(2)
    lips_w = (f"{m.group(0)}\n"
              f"{otstup}# REZINKA_DOBIVKA_V1: Губы режем тем же окном, что Зубы —\n"
              f"{otstup}# без них резинка не считается и bdb_strong ВСЕГДА False\n"
              f"{otstup}lips_w = {vyrazhenie.replace('teeth_series', 'lips_series')}")
    src = src.replace(m.group(0), lips_w, 1)
    print(f"  ✓ lips_w режется тем же окном ({vyrazhenie[:40]}...)")

    # ── 3. Передать Губы в detect_divergent_bar ─────────────────
    staryi_vyzov = ("        db = detect_divergent_bar(bars_w, ao_w, teeth_w, "
                    "point=point)")
    novyi_vyzov = ("        # REZINKA_DOBIVKA_V1: ВОТ ОНА, ДЫРА. Без lips_series\n"
                   "        # резинка не считалась → is_peak=False ВСЕГДА →\n"
                   "        # bdb_strong=False ВСЕГДА → bdb_dir=None ВСЕГДА →\n"
                   "        # спуск Искры (_descend ищет bdb_dir == compass)\n"
                   "        # не находил НИЧЕГО. 454 кандидата, 0 подтверждений.\n"
                   "        db = detect_divergent_bar(bars_w, ao_w, teeth_w,\n"
                   "                                  point=point,\n"
                   "                                  lips_series=lips_w)")
    if staryi_vyzov not in src:
        # запасной матчер — вызов мог быть в одну строку иначе
        m2 = re.search(r"^(\s*)db\s*=\s*detect_divergent_bar\((.+?)\)\s*(#.*)?$",
                       src, re.M)
        if not m2:
            print("  ⚠ не нашёл вызов detect_divergent_bar в wave_form. СТОП.")
            sys.exit(1)
        src = src.replace(
            m2.group(0),
            f"{m2.group(1)}# REZINKA_DOBIVKA_V1: без Губ резинка не считается\n"
            f"{m2.group(1)}db = detect_divergent_bar({m2.group(2)}, "
            f"lips_series=lips_w)", 1)
    else:
        src = src.replace(staryi_vyzov, novyi_vyzov, 1)
    print("  ✓ detect_divergent_bar в wave_form получил Губы")

    # ── 4. Все, кто зовёт read_ao_wave_form — передать Губы ─────
    n = 0
    for m3 in list(re.finditer(
            r"read_ao_wave_form\(bars[^)]*?teeth_series[^)]*?\)", src)):
        vyzov = m3.group(0)
        if "lips_series" in vyzov:
            continue
        novyi = vyzov[:-1] + ", lips_series=_lips_series)"
        src = src.replace(vyzov, novyi, 1)
        n += 1
    print(f"  ✓ вызовов read_ao_wave_form обновлено: {n}")

    src = src.replace(
        "# `шесть·проверено·до·корня`",
        f"# {MARK}: read_ao_wave_form получил Губы. Без них резинка не\n"
        "#   считалась и bdb_dir был None ВСЕГДА — спуск Искры слеп.\n"
        "# `шесть·проверено·до·корня`", 1)

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    # ── СТОП-КРАН: проверяем ФАКТ ───────────────────────────────
    if "lips_series=lips_w" not in src:
        print("  ⚠ ГУБЫ НЕ ДОШЛИ ДО detect_divergent_bar. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    CORE.write_text(src, encoding="utf-8")

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО — спуск прозрел" + " " * 44 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ЧТО БЫЛО НЕ ТАК (МОЯ ОШИБКА):")
    print("    detect_divergent_bar читают ДВОЕ:")
    print("      build_market_data   → Губы передавал ✓ (454 кандидата)")
    print("      read_ao_wave_form   → Губы НЕ передавал ✗ (bdb_dir=None)")
    print("    Сито говорило «точка есть», спуск Искры её НЕ ВИДЕЛ.")
    print("    Я пропатчил одного читателя из двух.")
    print()
    print("  ТОТ ЖЕ КЛАСС, ЧТО ПЯТЬ МАГИКОВ И ДВА ПИСАТЕЛЯ ПОЗИЦИЙ.")
    print("  За сутки — третий раз. Урок записан в §10а, и я же на нём")
    print("  поскользнулся. Лечишь сущность — найди ВСЕХ, кто её читает.")
    print()
    print("  ПРОВЕРКА ФАКТА — гони тестер, в логе должно появиться:")
    print("    ···: кандидат N/454 ... спуск НАШЁЛ точку")
    print("    [ISKRA] 🪜 Спуск: компас=BEAR найдено=ДА")
    print("    🎯 ИСКРА: DETECTED  ← Совет просыпается")
    print()


if __name__ == "__main__":
    main()
