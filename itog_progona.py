# -*- coding: utf-8 -*-
# ITOG_V_R_V1
"""
ИТОГ ПРОГОНА — ПЯТЬ СТРОК, ПО КОТОРЫМ ВИДНО, РАБОЧАЯ СИСТЕМА ИЛИ НЕТ.

СЛОВО ШЕФА (27.08)
    «Не количество успешных входов считать нужно, а результат на
    депозите. Пусть из 10 сделок 7 в минус, но если в результате ты в
    плюсе — это рабочая система».

ЗАЧЕМ
    Прогон в конце говорит «мест 23 · входов 3 · отказов 19». По этим
    числам НЕЛЬЗЯ понять, работает система или нет — они про то, часто
    ли трейдеры соглашаются входить, а не про деньги.

    Этот счёт отвечает на настоящий вопрос: что осталось в сумме.

ЧТО СЧИТАЕТ
    · СУММА В R — главное число. Плюс или минус, и насколько.
    · средний плюс против среднего минуса — та самая асимметрия,
      ради которой семь минусов из десяти не страшны
    · сколько сделок, сколько плюсовых, сколько минусовых
    · худшая просадка подряд — сколько придётся высидеть
    · во что обошёлся спред и сколько сделок вышло не по стопу

    Всё в R (риск на входе = 1R), а не в долларах: тогда результат не
    зависит от размера счёта, и разные прогоны честно сравниваются
    между собой.

ОТКУДА БЕРЁТ
    Из журнала сделок города — trading_pnl.jsonl. Город пишет туда
    каждую закрытую сделку сам, с готовым pnl_r. Ничего нового
    считать не надо и ничего в городе трогать не надо.

НИЧЕГО НЕ МЕНЯЕТ
    Только читает и печатает. Денег не тратит, модель не зовёт,
    файлы города не пишет. Запускать можно хоть после каждого прогона.

Запуск:  py itog_progona.py
         py itog_progona.py --с 2025.02.01 --по 2026.02.01
"""
import json
import sys
from pathlib import Path


def _nayti_zhurnaly() -> list:
    """Журналы сделок — ищем сами по всему городу."""
    zdes = Path(__file__).resolve().parent
    korni = [zdes, Path.cwd().resolve()] + list(zdes.parents)[:3]
    nashli = []
    for k in korni:
        try:
            for f in k.rglob("trading_pnl.jsonl"):
                if f not in nashli:
                    nashli.append(f)
        except OSError:
            pass
        if nashli:
            break
    return nashli


def _chitat(fayly: list, s_daty: str = "", po_datu: str = "") -> list:
    sdelki = []
    for f in fayly:
        try:
            for stroka in f.read_text(encoding="utf-8").splitlines():
                stroka = stroka.strip()
                if not stroka:
                    continue
                try:
                    z = json.loads(stroka)
                except Exception:
                    continue
                if z.get("pnl_r") is None:
                    continue
                kogda = str(z.get("opened_at") or z.get("closed_at") or "")
                if s_daty and kogda and kogda < s_daty:
                    continue
                if po_datu and kogda and kogda > po_datu:
                    continue
                sdelki.append(z)
        except OSError as e:
            print(f"  . {f.name}: не прочитан ({e})")
    return sdelki


def _prosadka(r_ryad: list) -> float:
    """Худшая просадка подряд — сколько высидеть в минусе от пика."""
    pik = 0.0
    summa = 0.0
    hudshaya = 0.0
    for r in r_ryad:
        summa += r
        pik = max(pik, summa)
        hudshaya = min(hudshaya, summa - pik)
    return hudshaya


def main():
    a = sys.argv[1:]
    s_daty = po_datu = ""
    for i, x in enumerate(a):
        if x in ("--с", "--c", "--from") and i + 1 < len(a):
            s_daty = a[i + 1]
        if x in ("--по", "--po", "--to") and i + 1 < len(a):
            po_datu = a[i + 1]

    fayly = _nayti_zhurnaly()
    if not fayly:
        print("Журналов сделок не нашёл (trading_pnl.jsonl).")
        print("Запусти скрипт из корня города — рядом с папкой GRONDHEIM_CITY.")
        return

    print(f"\nЖурналов найдено: {len(fayly)}")
    for f in fayly:
        print(f"   {f.parent.name}/{f.name}")

    sdelki = _chitat(fayly, s_daty, po_datu)
    if not sdelki:
        print("\nЗакрытых сделок с результатом нет — считать нечего.")
        return

    r = [float(z["pnl_r"]) for z in sdelki]
    plyus = [x for x in r if x > 0]
    minus = [x for x in r if x <= 0]
    summa = sum(r)
    sredniy_plyus = (sum(plyus) / len(plyus)) if plyus else 0.0
    sredniy_minus = (sum(minus) / len(minus)) if minus else 0.0

    print("\n" + "═" * 58)
    print("  ИТОГ ПРОГОНА")
    if s_daty or po_datu:
        print(f"  отрезок: {s_daty or 'с начала'} → {po_datu or 'до конца'}")
    print("═" * 58)

    znak = "🟢" if summa > 0 else ("🔴" if summa < 0 else "⚪")
    print(f"\n  СУММА:  {summa:+.2f}R   {znak}")
    print("          (плюс — система заработала, минус — отдала)")

    print(f"\n  сделок:        {len(r)}")
    print(f"  в плюс:        {len(plyus)}"
          + (f"   ({len(plyus)/len(r):.0%})" if r else ""))
    print(f"  в минус:       {len(minus)}"
          + (f"   ({len(minus)/len(r):.0%})" if r else ""))

    print(f"\n  средний плюс:  {sredniy_plyus:+.2f}R")
    print(f"  средний минус: {sredniy_minus:+.2f}R")
    if sredniy_minus:
        otnoshenie = abs(sredniy_plyus / sredniy_minus)
        print(f"  асимметрия:    плюс в {otnoshenie:.1f} раза "
              f"{'больше' if otnoshenie >= 1 else 'МЕНЬШЕ'} минуса")
        print("                 (вот ради чего 7 минусов из 10 не страшны —")
        print("                  но только если это число больше единицы)")

    print(f"\n  худшая просадка подряд: {_prosadka(r):.2f}R")
    print("                 (столько придётся высидеть, не бросив)")

    prichiny = {}
    for z in sdelki:
        p = z.get("close_reason") or "?"
        prichiny[p] = prichiny.get(p, 0) + 1
    print("\n  чем закрывались:")
    for p, n in sorted(prichiny.items(), key=lambda x: -x[1]):
        print(f"      {p:<16} {n}")

    dolivki = sum(1 for z in sdelki if (z.get("dolivok") or 0) > 0)
    if dolivki:
        print(f"\n  сделок с доливом (пирамида): {dolivki}")

    print("\n" + "─" * 58)
    if summa > 0:
        print("  Система в плюсе на этом отрезке.")
        print("  Доля стопов роли не играет — играет сумма.")
    elif summa < 0:
        print("  Система в минусе на этом отрезке.")
        if len(r) < 20:
            print(f"  НО сделок всего {len(r)} — это не выборка. По такому")
            print("  числу судить рано: даже рабочая система легко даёт")
            print("  полосу минусов подряд. Нужен отрезок подлиннее.")
        elif sredniy_minus and abs(sredniy_plyus / sredniy_minus) < 1:
            print("  Смотри на асимметрию: средний плюс МЕНЬШЕ среднего")
            print("  минуса. Даже угадывая чаще, так не выйти в плюс —")
            print("  дело не в числе входов, а в том, что прибыли рубят")
            print("  раньше убытков.")
    print("─" * 58 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
