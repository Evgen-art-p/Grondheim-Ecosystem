#!/usr/bin/env python3
# patch_tochka_log.py
# ─────────────────────────────────────────────────────────────
# TOCHKA_LOG_V1 · 20.07
#
# Вопрос Шефа после первого настоящего живого прогона: "совет прошёл,
# работал только авантюрист, а до следующей Искры прошло много баров
# и никто не проснулся — это баг или так и должно быть?"
#
# Честный ответ: не видно ни в консоли, ни в логе. proverit_tochku()
# сейчас работает МОЛЧА — состояние точки (жива/умерла/подпиталась)
# меняется на диске (trading_state.json), но ни строчки в вывод не
# идёт. Значит нельзя отличить "точка честно умерла (структурный
# слом/TWR угас — нормально)" от "точка ни разу не проверилась как
# надо (баг)".
#
# Заодно замечено подозрительное: в стол_входа закрытой сделки лежит
# trend_direction=BEAR, а сама Искра ГОЛОСОМ сказала "направление
# BULL" (и вошли в LONG). Если это не разовая ошибка модели, а
# системная (LLM не всегда пишет trend_direction=направление точки,
# как требует канон KOMPAS_DOSTAVKA_TREYDERAM_V1, а иногда путает с
# компасом) — proverit_tochku будет искать пробой НЕ в ту сторону.
# Этот патч не чинит это (нечего чинить кодом — если дело в LLM,
# нужно смотреть промпт), а даёт УВИДЕТЬ, происходит ли это.
#
# ПАТЧ: печатает строку в консоль/отчёт КАЖДЫЙ раз, когда состояние
# точки меняется (changed=True) — с причиной и текущим направлением.
# Чисто диагностика, логику не трогает.
#
# ЗАВИСИМОСТЬ: применить ПОСЛЕ patch_sito_sliyanie.py.
#
# ИДЕМПОТЕНТНОСТЬ: маркер TOCHKA_LOG_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Биржа" / "tester_express.py"
MARKER = "TOCHKA_LOG_V1"


ANCHOR = '''            _cheap_trigger = None
            _tochka = proverit_tochku(md)
            if _tochka.get("alive"):'''

REPLACEMENT = '''            _cheap_trigger = None
            _tochka = proverit_tochku(md)
            if _tochka.get("changed"):   # ''' + MARKER + ''': видно, когда точка родилась/умерла/подпиталась
                _bd_log = bars_all[i].get("date", "?")
                print(f"[ТОЧКА] бар {i} ({_bd_log}): "
                      f"{'жива' if _tochka.get('alive') else 'МЕРТВА'} — "
                      f"{_tochka.get('reason','?')}")
            if _tochka.get("alive"):'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    if ANCHOR not in src:
        raise SystemExit("❌ якорь не найден (наложен ли patch_sito_sliyanie.py?) "
                          "— патч НЕ применён")

    src = src.replace(ANCHOR, REPLACEMENT, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_tochkalog")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
