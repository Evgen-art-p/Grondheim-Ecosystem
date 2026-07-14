# patch_slepok_ispolnitelya.py
# ─────────────────────────────────────────────────────────────
# SLEPOK_ISPOLNITELYA_V1 — ПОСЛЕДНИЙ МЕТР ТРУБЫ.
#
# БОЛЕЗНЬ (лог Шефа, 13.07 — на КАЖДОЙ закрытой сделке):
#   [МАЯК] судья сенсоров вызван: pnl_r=-0.7705, trader=BRUT
#   [МАЯК] стол_входа: {}                       ← ПУСТО
#   [МАЯК] ⛔ ВЫХОД: слепка нет или pnl_r=None   ← СУДЬЯ ВЫХОДИТ
#
# Судья сенсоров молча выходит на КАЖДОЙ сделке. Черновиков нет.
# Метка не родится НИКОГДА. Труба построена, вода идёт, а кран на
# выходе перекрыт.
#
# ⚠ ДИАГНОЗ: ПОЗИЦИИ ПИШУТ ДВОЕ. СЛЕПОК — ТОЛЬКО У МЁРТВОГО.
#
#   hooks.py:644 (_persist_trading_state)     → позиция СО СЛЕПКОМ ✓
#   исполнитель/мозг.py:278                   → позиция БЕЗ СЛЕПКА ✗
#
#   А _persist_trading_state зовётся ТОЛЬКО из on_after_agent —
#   которого council.py НЕ ВЫЗЫВАЕТ ВООБЩЕ.
#   ⇒ hooks-версия МЕРТВА. Живой писатель — мозг Сергея.
#
# Слепок чинили (SLEPOK_IZ_CHAIN_V1, комментарий в hooks прямо
# говорит: «судья молча выходил на 28 сделках подряд») — и починили
# НЕ ТУ КОПИЮ. Классика: два писателя одного, лечим одного.
# Тот же класс, что пять копий магика (§5г БИРЖА.md).
#
# ── ПОЧЕМУ СЛЕПОК ВООБЩЕ НУЖЕН ──
# Стол перетирается КАЖДЫЙ БАР. Сделка живёт десятки баров. Судить
# сенсора по чужому бару — КЛЕВЕТА: Морж на баре входа сказал
# «резинка вялая, жду», а на баре закрытия скажет что-то другое.
# Судить надо по тому, что он сказал В МОМЕНТ ВХОДА.
#
# ── ГДЕ БРАТЬ ПОКАЗАНИЯ (проверено на живом trading_state) ──
# Сенсоры сами пишут себя в состояние, каждый на своём баре:
#   iskra: {t1_status, zero_point_price, ...}
#   morj:  {morj_status, wave_1_validated, tension_peak, ...}
#   panic: {panic_phase, crowd_sentiment, ...}
#   hans:  {fractal_valid, fractal_side, fractal_price, ...}
# Исполнитель ходит ПОСЛЕДНИМ (после всех сенсоров и трейдеров) —
# значит в момент открытия в tstate лежат показания ИМЕННО ЭТОГО
# бара. Свежие. Их и снимаем.
#
# ── ЧТО КЛАДЁМ (ровно то, что ищет судья, hooks.py:795) ──
# Формат — БАЙТ В БАЙТ как в мёртвой hooks-версии (строка 668),
# чтобы sudit_sensora() и _zval() читали привычные ключи:
#   iskra: t1_status · zero_point_price · trend_direction (компас!)
#   morj:  morj_status · wave_1_validated
#   panic: panic_phase
#   hans:  fractal_valid · fractal_side · fractal_price
#
# Компас (trend_direction) критичен: без него не понять, звала ли
# Вера В СТОРОНУ сделки. BULL зовёт в LONG, но НЕ зовёт в SHORT.
#
# ИДЕМПОТЕНТЕН. BACKUP: мозг.py.bak_slepok
# Запуск из корня репо:  python patch_slepok_ispolnitelya.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ISP  = (ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
        / "слоты" / "исполнитель" / "мозг.py")
MARK = "SLEPOK_ISPOLNITELYA_V1"


SNIMOK = '''
def _snyat_stol_vhoda() -> dict:
    """SLEPOK_ISPOLNITELYA_V1 — СЛЕПОК СТОЛА на баре ВХОДА.

    Позиция уносит с собой показания всех четырёх сенсоров — те, что
    они дали ИМЕННО НА ЭТОМ БАРЕ. Стол перетирается каждый бар, а
    сделка живёт десятки баров: судить Моржа по чужому бару — клевета.

    Исполнитель ходит ПОСЛЕДНИМ (после сенсоров и трейдеров), значит
    в tstate сейчас лежат показания этого самого бара. Свежие.

    Формат — байт в байт как ждёт судья (hooks._sudit_sensorov):
    он читает pos["стол_входа"][key], где key ∈ iskra/morj/panic/hans.
    Пустой слепок = судья молча выходит и ЧЕРНОВИК НЕ РОЖДАЕТСЯ.
    """
    try:
        from hooks import load_trading_state
        t = load_trading_state()
    except Exception as e:
        print(f"[СЛЕПОК] ⚠️  не снял стол: {e}")
        return {}

    isk = t.get("iskra", {}) or {}
    mrj = t.get("morj",  {}) or {}
    pnk = t.get("panic", {}) or {}
    hns = t.get("hans",  {}) or {}

    # компас: без него не понять, звала ли Вера В СТОРОНУ сделки —
    # BULL зовёт в LONG, но НЕ зовёт в SHORT
    kompas = (isk.get("trend_direction")
              or mrj.get("inherited_dir")
              or isk.get("global_bias"))

    stol = {
        "iskra": {
            "t1_status":        isk.get("t1_status"),
            "zero_point_price": isk.get("zero_point_price"),
            "trend_direction":  kompas,
        },
        "morj": {
            "morj_status":      mrj.get("morj_status"),
            "wave_1_validated": mrj.get("wave_1_validated"),
            "tension_peak":     mrj.get("tension_peak"),
        },
        "panic": {
            "panic_phase":      pnk.get("panic_phase"),
        },
        "hans": {
            "fractal_valid":    hns.get("fractal_valid"),
            "fractal_side":     hns.get("fractal_side"),
            "fractal_price":    hns.get("fractal_price"),
        },
    }
    print(f"[СЛЕПОК] 📸 стол снят: искра={stol['iskra']['t1_status']} "
          f"морж={stol['morj']['morj_status']} "
          f"паник={stol['panic']['panic_phase']} "
          f"ганс={stol['hans']['fractal_valid']} компас={kompas}")
    return stol

'''


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  СЛЕПОК СТОЛА — последний метр трубы" + " " * 31 + "║")
    print("║  SLEPOK_ISPOLNITELYA_V1 · идемпотентен" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    if not ISP.exists():
        print(f"⚠ не нашёл {ISP}")
        print("  запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    src = ISP.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ уже пропатчен — пропускаю (идемпотентно)")
        print()
        return

    bak = ISP.with_suffix(".py.bak_slepok")
    if not bak.exists():
        shutil.copy2(ISP, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── 1. Функция снятия слепка — перед _open_positions_from_table ──
    ank = "def _open_positions_from_table("
    if ank not in src:
        print("  ⚠ не нашёл _open_positions_from_table. СТОП.")
        sys.exit(1)
    src = src.replace(ank, SNIMOK.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ _snyat_stol_vhoda() — снимает показания 4 сенсоров")

    # ── 2. Слепок в позицию ──────────────────────────────────────
    staroe = ('            "iskra_zero_point": _iskra_zero_for_judgement(),\n'
              '        }')
    novoe = ('            "iskra_zero_point": _iskra_zero_for_judgement(),\n'
             '            # SLEPOK_ISPOLNITELYA_V1: позиция уносит С СОБОЙ показания\n'
             '            # сенсоров на баре ВХОДА. Без этого судья сенсоров молча\n'
             '            # выходит на КАЖДОЙ сделке → черновик не рождается →\n'
             '            # МЕТКА НЕ РОДИТСЯ НИКОГДА. Это был последний перекрытый\n'
             '            # кран: труба построена, вода шла, а на выходе — ничего.\n'
             '            "стол_входа": _snyat_stol_vhoda(),\n'
             '        }')
    if staroe not in src:
        print("  ⚠ не нашёл тело позиции. СТОП.")
        sys.exit(1)
    src = src.replace(staroe, novoe, 1)
    print("  ✓ позиция уносит стол_входа с собой")

    # ── СТОП-КРАН: проверяем ФАКТ, не намерение ──────────────────
    if '"стол_входа": _snyat_stol_vhoda()' not in src:
        print("  ⚠ СЛЕПОК НЕ ЛЁГ В ПОЗИЦИЮ. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    # и что он ВНУТРИ pos = {...}, а не где попало
    i_pos = src.find("        pos = {")
    i_sl  = src.find('"стол_входа": _snyat_stol_vhoda()')
    i_end = src.find("        tstate[\"positions\"].append(pos)")
    if not (0 < i_pos < i_sl < i_end):
        print("  ⚠ слепок НЕ В ТЕЛЕ позиции. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    src = src.replace(
        "# `шесть·проверено·до·корня`",
        f"# {MARK}: позиция уносит слепок стола. Судья сенсоров ожил.\n"
        "# `шесть·проверено·до·корня`", 1)
    if MARK not in src:
        src = f"# {MARK}\n" + src

    try:
        ast.parse(src)
    except SyntaxError as ex:
        print(f"  ⚠ СИНТАКСИС СЛОМАН: {ex}. НЕ ПИШУ ФАЙЛ.")
        sys.exit(1)

    ISP.write_text(src, encoding="utf-8")

    print("  ✓ проверено фактом: слепок В ТЕЛЕ pos, до append")
    print("  ✓ синтаксис цел")
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО — кран открыт" + " " * 46 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ЧТО БЫЛО НЕ ТАК:")
    print("    Позиции пишут ДВОЕ. Слепок был только у МЁРТВОГО:")
    print("      hooks.py:644  — со слепком, но НЕ ВЫЗЫВАЕТСЯ")
    print("                      (council.py не зовёт on_after_agent)")
    print("      мозг Сергея   — БЕЗ слепка, и он ЖИВОЙ")
    print("    Слепок чинили однажды — и починили НЕ ТУ КОПИЮ.")
    print()
    print("  ПРОВЕРКА ФАКТА (не галочки) — гони тестер и ищи в логе:")
    print("    [СЛЕПОК] 📸 стол снят: искра=... морж=... компас=...")
    print("    [МАЯК] стол_входа: {'iskra': {...}, 'morj': {...}}  ← НЕ {}")
    print("    [МАЯК] A02 morj: показание=... звал=... вывод=ЕСТЬ")
    print("    [МОСТ] 📝 черновик   ← ВОТ ОНО. Первый вывод в истории города.")
    print()
    print("  Если стол_входа снова {} — значит сенсоры не успели записаться")
    print("  до Исполнителя. Скажи — посмотрю порядок хода.")
    print()


if __name__ == "__main__":
    main()
