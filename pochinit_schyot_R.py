# -*- coding: utf-8 -*-
# pochinit_schyot_R.py — R снова считается от риска НА ВХОДЕ.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python pochinit_schyot_R.py
#
# ═══ ЧТО НАШЛОСЬ ═══
#
# Прогон 19.09 с включённым трейлингом: 30 закрытий, 28 в минус,
# итог −26.54R. Выглядело так, будто трейлинг всё испортил.
#
# А в деньгах убытки РАЗНЫЕ — и очень мелкие:
#
#     pnl −0.005130  →  R −1.0
#     pnl −0.000498  →  R −1.0     ← это пять пунктов
#     pnl −0.000282  →  R −1.0     ← это три пункта
#
# Разница в деньгах в восемнадцать раз, а R у всех ровно −1.0. Так
# быть не может: −1R значит «потерял весь риск, взятый на входе».
#
# ═══ ПРИЧИНА ═══
#
# Счёт делает так:
#
#     stop_r = pos.get("stop_initial", stop)   # ← поля НЕТ → текущий
#
# А в списке ключей закрытой позиции (его печатает [МАЯК]) поля
# stop_initial НЕТ ВООБЩЕ. Значит риск берётся от ПОДТЯНУТОГО стопа.
#
# Трейлинг подвинул стоп к цене — риск стал три пункта — стоп
# сработал — записано −1.0R. То есть ЧЕМ ЛУЧШЕ СРАБОТАЛ ТРЕЙЛИНГ,
# ТЕМ ХУЖЕ ВЫГЛЯДИТ РЕЗУЛЬТАТ. Он спасал деньги, а отчёт писал
# полный убыток.
#
# Из-за этого все наши замеры последнего прогона были неверны, и
# трейлинг едва не признали вредным.
#
# ═══ ЧТО СТАВИМ ═══
#
# Две защиты, обе простые и обе в правильных местах:
#
# 1. ПРИ АКТИВАЦИИ заявки — запомнить стоп как первоначальный, если
#    его ещё не записали. В миг входа текущий стоп И ЕСТЬ
#    первоначальный, тут ошибиться нельзя.
#
# 2. ПЕРЕД ПОДТЯЖКОЙ в трейлинге — то же самое, на случай позиции,
#    открытой раньше. Первый же трейлинг запомнит стоп до того, как
#    его сдвинет.
#
# Обе через setdefault: если поле уже есть, НЕ трогаем.
#
# Старые позиции, открытые до патча, так и останутся без поля — их
# R будет врать до закрытия. Новые считаются верно.
#
# БЕЗОПАСНО. Проверяет ast.parse. Рядом кладёт hooks.py.bak_schyot_R.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "POCHINIT_SCHYOT_R_V1"

# ── 1. при активации ──
STAROE_1 = (
    '            pos["status"] = "OPEN"\n'
    '            pos["opened_at"] = bar_time      # ВРЕМЯ РЕАЛЬНОГО ВХОДА\n'
)
NOVOE_1 = (
    '            pos["status"] = "OPEN"\n'
    '            pos["opened_at"] = bar_time      # ВРЕМЯ РЕАЛЬНОГО ВХОДА\n'
    '            # POCHINIT_SCHYOT_R_V1: запоминаем риск НА ВХОДЕ.\n'
    '            # Без этого поля счёт брал ТЕКУЩИЙ стоп — и после\n'
    '            # трейлинга любой стоп-аут писался как −1.0R, хотя\n'
    '            # реально терялось три пункта вместо восьмидесяти.\n'
    '            # В миг входа текущий стоп И ЕСТЬ первоначальный.\n'
    '            if pos.get("stop") is not None:\n'
    '                pos.setdefault("stop_initial", pos["stop"])\n'
)

# ── 2. перед подтяжкой ──
STAROE_2 = (
    '        direction = (pos.get("direction") or "").upper()\n'
    '        old = pos.get("stop")\n'
    '        entry = pos.get("entry")\n'
    '        if old is None or entry is None:\n'
    '            continue\n'
)
NOVOE_2 = (
    '        direction = (pos.get("direction") or "").upper()\n'
    '        old = pos.get("stop")\n'
    '        entry = pos.get("entry")\n'
    '        if old is None or entry is None:\n'
    '            continue\n'
    '        # POCHINIT_SCHYOT_R_V1: вторая защита — для позиций,\n'
    '        # открытых раньше патча. Запоминаем стоп ДО того, как\n'
    '        # сдвинем его: потом восстановить будет неоткуда.\n'
    '        pos.setdefault("stop_initial", old)\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    prosto = KOREN / "Биржа" / "hooks.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nash = [p for p in KOREN.rglob("hooks.py")
            if not any(m in str(p) for m in musor)]
    if len(nash) == 1:
        print(f"Нашёл: {nash[0]}")
        return nash[0]
    if len(nash) > 1:
        print("Нашёл несколько hooks.py:")
        for n, p in enumerate(nash, 1):
            print(f"  {n}. {p}")
        o = input("Какой правим? номер: ").strip()
        if o.isdigit() and 1 <= int(o) <= len(nash):
            return nash[int(o) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/hooks.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("· уже сделано")
        return 0

    pravki = [(STAROE_1, NOVOE_1), (STAROE_2, NOVOE_2)]
    for n, (s, _) in enumerate(pravki, 1):
        if tekst.count(s) != 1:
            print(f"✗ правка {n}: нашёл {tekst.count(s)} мест вместо одного.")
            print("  Ничего не тронул. Скажи Брату, поправим по месту.")
            return 1

    novyy = tekst
    for s, nn in pravki:
        novyy = novyy.replace(s, nn, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno})")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_schyot_R")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ счёт R починен:")
    print("    · первоначальный стоп запоминается при активации")
    print("    · и перед первой подтяжкой — для старых позиций")
    print("    · уже записанное поле не трогается")
    print()
    print("Перезапусти Кабинет (main.py) и прогони ЗАНОВО.")
    print("Проверка: у стоп-аутов R должен стать РАЗНЫМ. Сплошные −1.0")
    print("при разных pnl означают, что поле снова теряется.")
    print()
    print("ВАЖНО: прошлые замеры с трейлингом были неверны — он")
    print("спасал деньги, а отчёт писал полный убыток.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
