# -*- coding: utf-8 -*-
# GDE_VHODYAT_V1
"""
ГДЕ ОНИ ВХОДЯТ — И ЧТО КАЖДОЕ МЕСТО ПРИНОСИТ.

ВОПРОС
    Итог прогона показал: 19 стопов на 1 выход по колоколу, сумма
    -17.84R. Асимметрия почти ровная (1.2), значит платить за стопы
    нечем. Но НЕ ВИДНО главного: в каком месте они входили.

    Три места входа по канону:
        1) на развороте            — самое дорогое, без подтверждения
        2) по первой волне         — дороже среднего
        3) конец первого отката    — дешевле всех по риску

    Если почти все входы в первом месте — дело не в стопах и не в
    коде, а в том, КУДА они садятся.

ЧТО ДЕЛАЕТ
    Берёт сделки из журнала (trading_pnl.jsonl) и отчёты прогонов
    (папка прогоны/), связывает каждую сделку с событием, на котором
    трейдера будили, и считает по каждому месту: сколько сделок и
    сколько в сумме R.

    Ничего не меняет. Только читает и печатает.

ЧЕСТНАЯ ОГОВОРКА
    Событие входа в журнале НЕ хранится — оно берётся из отчёта по
    времени: последнее событие до момента входа. Это восстановление,
    а не запись. Если отчётов не осталось, скрипт так и скажет.

Запуск:  py gde_vhodyat.py
"""
import json
import re
import sys
from pathlib import Path


def _nayti(imya: str, papka: bool = False) -> list:
    zdes = Path(__file__).resolve().parent
    out = []
    for k in (zdes, Path.cwd().resolve()):
        try:
            for f in k.rglob(imya):
                if f not in out:
                    out.append(f)
        except OSError:
            pass
        if out:
            break
    return out


def _sdelki() -> list:
    out = []
    for f in _nayti("trading_pnl.jsonl"):
        for s in f.read_text(encoding="utf-8").splitlines():
            s = s.strip()
            if not s:
                continue
            try:
                z = json.loads(s)
            except Exception:
                continue
            if z.get("pnl_r") is not None and z.get("opened_at"):
                out.append(z)
    return out


# «📍 2025.02.24 08:00 · точка родилась: BEAR @ 1.05283 → спрашиваю Илья»
METKA = re.compile(r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})\s*·\s*([^→\n]+?)\s*→")


def _sobytiya() -> list:
    """Все метки из отчётов прогонов: (время, что случилось)."""
    out = []
    fayly = []
    for shablon in ("*.md", "*.txt", "*.log"):
        for f in _nayti(shablon):
            if "прогон" in str(f).lower() or "отчёт" in str(f).lower() \
                    or "otchet" in str(f).lower():
                fayly.append(f)
    for f in fayly:
        try:
            tekst = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in METKA.finditer(tekst):
            out.append((m.group(1), m.group(2).strip()))
    out.sort(key=lambda x: x[0])
    return out


def _mesto(sobytie: str) -> str:
    """Какое из трёх мест канона."""
    s = (sobytie or "").lower()
    if "точка родилась" in s:
        return "1. на развороте (точка ноль)"
    if "волна 1" in s and "кончилась" in s:
        return "2. по первой волне"
    if "откат кончился" in s:
        return "3. конец отката  ← дешевле всех"
    if "вершина" in s and "сдвинул" in s:
        return "переезд вершины (шум)"
    if "pending" in s or "заявка" in s:
        return "висела заявка"
    if "сделка закрылась" in s or "вошёл" in s:
        return "ведение позиции"
    return "прочее"


def main():
    sd = _sdelki()
    if not sd:
        print("Сделок в журнале нет — считать нечего.")
        return
    sob = _sobytiya()
    print(f"\nСделок в журнале: {len(sd)}")
    print(f"Меток в отчётах:  {len(sob)}")

    if not sob:
        print("\nОтчётов прогонов не нашёл — восстановить место входа")
        print("не из чего. Отчёты лежат в GRONDHEIM_CITY/.../прогоны/.")
        print("Если они есть, положи скрипт в корень города и запусти оттуда.")
        return

    itog = {}
    ne_nashli = 0
    for z in sd:
        kogda = str(z["opened_at"])
        # последнее событие ДО входа (или ровно в тот же миг)
        bylo = [s for s in sob if s[0] <= kogda]
        if not bylo:
            ne_nashli += 1
            continue
        mesto = _mesto(bylo[-1][1])
        b = itog.setdefault(mesto, {"n": 0, "r": 0.0, "plyus": 0})
        b["n"] += 1
        b["r"] += float(z["pnl_r"])
        if float(z["pnl_r"]) > 0:
            b["plyus"] += 1

    print("\n" + "═" * 62)
    print("  ГДЕ ВХОДИЛИ И ЧТО ЭТО ПРИНЕСЛО")
    print("═" * 62)
    if not itog:
        print("\n  Связать сделки с событиями не вышло — время не сошлось.")
        return

    for mesto, b in sorted(itog.items(), key=lambda x: -x[1]["n"]):
        znak = "🟢" if b["r"] > 0 else "🔴"
        print(f"\n  {mesto}")
        print(f"      сделок: {b['n']}   в плюс: {b['plyus']}   "
              f"сумма: {b['r']:+.2f}R  {znak}")

    if ne_nashli:
        print(f"\n  (для {ne_nashli} сделок событие не нашлось)")

    # вывод словами
    vsego = sum(b["n"] for b in itog.values())
    pervoe = itog.get("1. на развороте (точка ноль)", {}).get("n", 0)
    tretye = itog.get("3. конец отката  ← дешевле всех", {}).get("n", 0)
    print("\n" + "─" * 62)
    if vsego and pervoe / vsego > 0.5:
        print(f"  {pervoe} из {vsego} входов — В ПЕРВОМ МЕСТЕ, на развороте.")
        print("  Это самое дорогое место канона: вход без подтверждения,")
        print("  стоп широкий, движение ещё не доказано. Стопы здесь —")
        print("  не поломка системы, а цена этого места.")
        if tretye < pervoe:
            print(f"\n  А в третьем месте (конец отката) — всего {tretye}.")
            print("  Именно оно дешевле всех по риску, и именно до него")
            print("  они чаще всего не доходят.")
    elif tretye >= pervoe and tretye:
        print("  Входят в основном в третьем месте — как и задумано.")
        print("  Значит дело не в выборе места, ищем причину дальше.")
    print("─" * 62 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
