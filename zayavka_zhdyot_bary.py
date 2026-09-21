# -*- coding: utf-8 -*-
# zayavka_zhdyot_bary.py — заявка ждёт БАРЫ, а не вызовы; отчёт не врёт.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python zayavka_zhdyot_bary.py
#
# ═══ ЧТО НАШЛОСЬ ═══
#
# Шеф заметил в отчёте: есть вход и прибыль, вход и стоп, а есть вход
# «в работе» — и таких не один.
#
# Разобрали место 33 (2024.02.13 16:00, LONG @ 1.07275). В логе:
#
#     [ОРДЕР] 🚫 BRUT LONG @ 1.07275 ОТМЕНЁН — не пробит за 10 баров
#
# А по барам:
#
#     13.02 16:00  заявка выставлена
#     14.02 12:00  отменена — прошло ПЯТЬ баров, не десять
#     14.02 16:00  H 1.07347 — цена ДОШЛА до заявки. На бар позже.
#
# ═══ ПОЛОМКА ПЕРВАЯ — ТОРГОВАЯ ═══
#
# Счётчик «ждёт баров» прибавлял единицу НА КАЖДЫЙ ВЫЗОВ проверки
# заявок, а не на каждый бар:
#
#     zhdyot = pos.get("_ждёт_баров", 0) + 1
#
# Прогон зовёт рыночный шаг из двух мест — на баре места и на
# молчаливом шаге между местами. На части баров он срабатывает
# дважды, и заявка стареет вдвое быстрее. «Десять баров» оказывались
# пятью — и заявку снимали за шаг до того, как цена к ней приходила.
#
# ЭТО ПОТЕРЯННЫЕ СДЕЛКИ. Вход был правильный, рынок пошёл куда надо,
# а заявки уже не было.
#
# Починка: прибавлять, только когда СМЕНИЛСЯ БАР. Сколько бы раз ни
# звали на одном баре — счёт один.
#
# ═══ ПОЛОМКА ВТОРАЯ — В ОТЧЁТЕ ═══
#
# «В работе» ставил отчёт, когда не находил в журнале закрытия с той
# же ценой входа. А у отменённой заявки закрытия нет вовсе — она не
# открывалась. Значит под «в работе» прятались отменённые.
#
# Починка: писать честно — «не сработала или ещё открыта». Отличить
# одно от другого отчёт по журналу закрытий не может: отмена туда не
# пишется.
#
# БЕЗОПАСНО. Правит два файла, пишет только если сошлись оба. Рядом
# кладёт копии. Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "ZAYAVKA_ZHDYOT_BARY_V1"

H_STAROE = (
    '        # не сработал — считаем, сколько ждёт\n'
    '        zhdyot = pos.get("_ждёт_баров", 0) + 1\n'
    '        pos["_ждёт_баров"] = zhdyot\n'
    '        dirty = True\n'
)
H_NOVOE = (
    '        # не сработал — считаем, сколько ждёт.\n'
    '        # ZAYAVKA_ZHDYOT_BARY_V1: считаем БАРЫ, а не вызовы. Прогон\n'
    '        # зовёт рыночный шаг из двух мест, и на части баров он\n'
    '        # срабатывает дважды — заявка старела вдвое быстрее.\n'
    '        # «Десять баров» оказывались пятью: место 33 (13.02.2024)\n'
    '        # сняли на пятом баре, а цена дошла до заявки на шестом.\n'
    '        # Теперь прибавляем, только когда сменился бар.\n'
    '        if pos.get("_ждёт_бар_время") != bar_time:\n'
    '            zhdyot = pos.get("_ждёт_баров", 0) + 1\n'
    '            pos["_ждёт_баров"] = zhdyot\n'
    '            pos["_ждёт_бар_время"] = bar_time\n'
    '        else:\n'
    '            zhdyot = pos.get("_ждёт_баров", 0)\n'
    '        dirty = True\n'
)

O_STAROE = '        return None, "в работе"\n'
O_NOVOE = (
    '        # ZAYAVKA_ZHDYOT_BARY_V1: было «в работе». А у ОТМЕНЁННОЙ\n'
    '        # заявки закрытия нет вовсе — она не открывалась, — и под\n'
    '        # «в работе» прятались отменённые. Отличить по журналу\n'
    '        # закрытий нельзя: отмена туда не пишется.\n'
    '        return None, "не сработала или ещё открыта"\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti(imya):
    prosto = KOREN / "Биржа" / imya
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nash = [p for p in KOREN.rglob(imya)
            if not any(m in str(p) for m in musor)]
    if len(nash) == 1:
        return nash[0]
    if len(nash) > 1:
        print(f"Нашёл несколько {imya}:")
        for n, p in enumerate(nash, 1):
            print(f"  {n}. {p}")
        o = input("Какой правим? номер: ").strip()
        if o.isdigit() and 1 <= int(o) <= len(nash):
            return nash[int(o) - 1]
    return None


def main():
    hk = nayti("hooks.py")
    uo = nayti("ui_otchyot.py")
    if not (hk and uo):
        print("✗ не нашёл hooks.py или ui_otchyot.py — запускай из корня")
        return 1

    th = hk.read_text(encoding="utf-8")
    to = uo.read_text(encoding="utf-8")
    if MARKER in th and MARKER in to:
        print("· уже сделано")
        return 0

    nh = no = None
    if MARKER not in th:
        if th.count(H_STAROE) != 1:
            print(f"✗ hooks.py: нашёл {th.count(H_STAROE)} мест вместо одного.")
            print("  Ничего не тронул ни в одном файле.")
            return 1
        nh = th.replace(H_STAROE, H_NOVOE, 1)
        try:
            ast.parse(nh)
        except SyntaxError as e:
            print(f"✗ hooks.py поломался бы (строка {e.lineno})")
            return 1
    if MARKER not in to:
        if to.count(O_STAROE) != 1:
            print(f"✗ ui_otchyot.py: нашёл {to.count(O_STAROE)} мест вместо одного.")
            print("  Ничего не тронул ни в одном файле.")
            return 1
        no = to.replace(O_STAROE, O_NOVOE, 1)
        try:
            ast.parse(no)
        except SyntaxError as e:
            print(f"✗ ui_otchyot.py поломался бы (строка {e.lineno})")
            return 1

    for put, novyy in ((hk, nh), (uo, no)):
        if novyy is None:
            continue
        kopiya = put.with_suffix(put.suffix + ".bak_zhdyot")
        if not kopiya.exists():
            shutil.copy2(put, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        put.write_text(novyy, encoding="utf-8")

    print("✓ починено:")
    print("    · заявка ждёт БАРЫ, а не вызовы — десять баров снова десять")
    print("    · в отчёте вместо «в работе» — «не сработала или ещё открыта»")
    print()
    print("Перезапусти Кабинет (main.py) и прогони тот же отрезок.")
    print("Отменённых заявок должно стать меньше, а входов — больше:")
    print("часть снятых раньше срока теперь доживёт до пробоя.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
