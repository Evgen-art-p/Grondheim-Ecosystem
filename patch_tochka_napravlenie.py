#!/usr/bin/env python3
# patch_tochka_napravlenie.py
# ─────────────────────────────────────────────────────────────
# TOCHKA_NAPRAVLENIE_V1 · 20.07
#
# Наблюдение Шефа (картинка c→1→2 — всё внутри ОДНОЙ волны 1):
# станции цепочки должны быть СИНХРОННЫ по направлению, не просто
# "точка жива + любой фрактал/палец сработал". proverit_tochku()
# знает направление точки (trend_direction), но не отдавала его
# наружу — вызывающий код не мог сверить, совпадает ли пробой
# фрактала/Большой палец с тем же направлением, что и живая точка.
#
# ПАТЧ: добавляет "direction" в КАЖДЫЙ возврат proverit_tochku()
# (даже когда alive=False — там direction=None). Ничего не меняет
# в логике жизни/смерти точки, только раскрывает то, что функция
# и так уже знает.
#
# ЗАВИСИМОСТЬ: применить ПОСЛЕ patch_tochka_zhiva.py.
#
# ИДЕМПОТЕНТНОСТЬ: маркер TOCHKA_NAPRAVLENIE_V1 в файле — патч не
# накладывается повторно.
# ─────────────────────────────────────────────────────────────

import ast
import shutil
import py_compile
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Биржа" / "hooks.py"
MARKER = "TOCHKA_NAPRAVLENIE_V1"


PAIRS = [
    ('return {"alive": False, "reason": "точки нет", "changed": False}',
     'return {"alive": False, "reason": "точки нет", "changed": False, '
     '"direction": None}   # ' + MARKER),

    ('            return {"alive": True,\n'
     '                    "reason": f"подпитка {mfi_type}: точка обновлена → {novaya_zp}",\n'
     '                    "changed": True}',
     '            return {"alive": True,\n'
     '                    "reason": f"подпитка {mfi_type}: точка обновлена → {novaya_zp}",\n'
     '                    "changed": True, "direction": napr}   # ' + MARKER),

    ('        return {"alive": False,\n'
     '                "reason": f"структурный слом: цена пробила {zp}",\n'
     '                "changed": True}',
     '        return {"alive": False,\n'
     '                "reason": f"структурный слом: цена пробила {zp}",\n'
     '                "changed": True, "direction": napr}   # ' + MARKER),

    ('        return {"alive": False,\n'
     '                "reason": "TWR нейтрален — ритм угас во флэте",\n'
     '                "changed": True}',
     '        return {"alive": False,\n'
     '                "reason": "TWR нейтрален — ритм угас во флэте",\n'
     '                "changed": True, "direction": napr}   # ' + MARKER),

    ('    return {"alive": True, "reason": "жива", "changed": False}',
     '    return {"alive": True, "reason": "жива", "changed": False, '
     '"direction": napr}   # ' + MARKER),
]


def main():
    if not TARGET.exists():
        raise SystemExit(f"❌ не найден: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже применён — пропуск (идемпотентно).")
        return

    for anchor, _ in PAIRS:
        if anchor not in src:
            raise SystemExit(f"❌ якорь не найден (наложен ли уже "
                              f"patch_tochka_zhiva.py?) — патч НЕ применён:\n{anchor[:80]}...")

    for anchor, repl in PAIRS:
        src = src.replace(anchor, repl, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"❌ патч ломает синтаксис: {e} — файл НЕ тронут")

    backup = TARGET.with_suffix(".py.bak_napravlenie")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ записано: {TARGET}")
    print(f"✓ бэкап:    {backup}")

    py_compile.compile(str(TARGET), doraise=True)
    print(f"✓ py_compile прошёл")
    print(f"✓ {MARKER} применён")


if __name__ == "__main__":
    main()
