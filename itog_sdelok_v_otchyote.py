# -*- coding: utf-8 -*-
# itog_sdelok_v_otchyote.py — отчёт узнаёт, чем кончились сделки.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python itog_sdelok_v_otchyote.py
#
# ВАЖНО: идёт после rasklad_v_otchyote.py.
#
# ═══ ЧТО ОКАЗАЛОСЬ ═══
#
# Брат сперва решил, что город не пишет выходы. Это было НЕВЕРНО.
#
# Город считает закрытие полностью: цену выхода, причину (STOP_LOSS,
# EXIT_BELL, MANUAL_CLOSE), pnl в цене и pnl_r — результат в R от
# ПЕРВОНАЧАЛЬНОГО риска, а не от подвинутого трейлингом стопа. Всё
# это ложится в журнал trading_pnl.jsonl, в Атлас и в дневник самого
# трейдера.
#
# Дыра была не в расчётах, а в несоединённой трубе: отчёт прогона
# писал только «места» — пробуды — и в журнал закрытий ни разу не
# заглядывал.
#
# ═══ ЧТО СТАВИМ ═══
#
# Отчёт рождается — запоминает, сколько строк в журнале. Закрывается —
# берёт всё, что прибавилось, и считает: winrate, сумму и среднее в R,
# profit factor, худшую просадку по счёту, разбивку по причинам
# выхода и таблицу сделок.
#
# ПОЧЕМУ ПО ДЛИНЕ, А НЕ ПО ВРЕМЕНИ. В журнале лежит closed_at — это
# бар РЫНКА, а не момент работы. Прогоны ходят по истории: утром
# февраль, днём январь. По времени бара записи разных прогонов
# перемешаются. Длина журнала честнее: что прибавилось между
# рождением отчёта и его закрытием — то и случилось в этом прогоне.
#
# ЧЕГО ЭТОТ СПОСОБ НЕ УМЕЕТ. Если запустить два прогона ОДНОВРЕМЕННО,
# они поделят прибавку и каждый припишет себе чужое. Стол один и
# кнопка одна, так что этого не бывает; но знать надо.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт otchyot.py.bak_itog.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "ITOG_SDELOK_V1"
NUZHEN = "RASKLAD_PROGONA_V1"

# ── 1. при рождении отчёта запоминаем длину журнала ──
YAKOR_INIT = (
    "        try:\n"
    "            self.kadry.mkdir(parents=True, exist_ok=True)\n"
    "        except Exception as e:\n"
    '            print(f"[ОТЧЁТ] папку не завести: {e}")\n'
)
NOVYY_INIT = YAKOR_INIT + (
    "        # ITOG_SDELOK_V1: сколько строк было в журнале закрытий на\n"
    "        # старте. Всё, что прибавится, — сделки ЭТОГО прогона.\n"
    "        # По времени отбирать нельзя: в журнале бар рынка, а\n"
    "        # прогоны ходят по истории вразнобой.\n"
    "        self.zhurnal_bylo = self._dlina_zhurnala()\n"
)

# ── 2. вместо «посчитать нельзя» — настоящий итог ──
YAKOR_NELZYA = (
    "        # ── чего посчитать нельзя ──\n"
    '        s.append("### Чего посчитать нельзя")\n'
    '        s.append("")\n'
    '        s.append("В записях нет ни одного выхода: ни цены закрытия, ни "\n'
    '                 "причины, ни результата. Поэтому прибыль, winrate, "\n'
    '                 "ожидание в R и просадка не считаются — не из чего.")\n'
    '        s.append("")\n'
    '        s.append("Чтобы считались, в запись места должны попадать: цена "\n'
    '                 "и время выхода, причина выхода (стоп / цель / вручную), "\n'
    '                 "и общий номер сделки, чтобы вход и ведение связывались "\n'
    '                 "не по цене, а прямо.")\n'
    '        s.append("")\n'
)
NOVYY_NELZYA = "        s += self._itog_sdelok()\n"

# ── 3. сам счёт ──
YAKOR_METODA = "    def _rasklad(self) -> list:\n"

METOD = '''    # ── ITOG_SDELOK_V1: чем кончились сделки ──
    # Город всё считает сам и кладёт в trading_pnl.jsonl: цену выхода,
    # причину, pnl_r от ПЕРВОНАЧАЛЬНОГО риска. Отчёту оставалось
    # только заглянуть в журнал — раньше он этого не делал.

    @staticmethod
    def _zhurnal_put():
        try:
            from hooks import PNL_PATH
            return Path(PNL_PATH)
        except Exception:
            return None

    @staticmethod
    def _dlina_zhurnala() -> int:
        p = Otchyot._zhurnal_put()
        if not p or not p.exists():
            return 0
        try:
            with open(p, encoding="utf-8") as f:
                return sum(1 for stroka in f if stroka.strip())
        except Exception:
            return 0

    def _zakrytiya(self) -> list:
        """Сделки, закрывшиеся за ЭТОТ прогон — прибавка к журналу."""
        p = self._zhurnal_put()
        if not p or not p.exists():
            return []
        try:
            with open(p, encoding="utf-8") as f:
                stroki = [x for x in f if x.strip()]
        except Exception as e:
            print(f"[ОТЧЁТ] журнал закрытий не прочитался: {e}")
            return []
        out = []
        for x in stroki[int(getattr(self, "zhurnal_bylo", 0) or 0):]:
            try:
                out.append(json.loads(x))
            except Exception:
                pass
        return out

    def _itog_sdelok(self) -> list:
        zakr = self._zakrytiya()

        if not zakr:
            return [
                "### Чем кончилось", "",
                "За этот прогон ни одна сделка не закрылась. Либо входов "
                "не было, либо открытые дожили до конца отрезка — тогда "
                "их результат появится в следующем прогоне, когда рынок "
                "до них дойдёт.", "",
                "Считать winrate и просадку не из чего: закрытий ноль.",
                "",
            ]

        # pnl_r может быть None (трейлинг увёл риск в ноль) — такие
        # в счёт R не берём, но из списка не прячем.
        r = [x.get("pnl_r") for x in zakr]
        r_est = [float(v) for v in r if isinstance(v, (int, float))]
        plyusy = [v for v in r_est if v > 0]
        minusy = [v for v in r_est if v < 0]

        s = ["### Чем кончилось", ""]
        s.append("| что | сколько |")
        s.append("|---|---|")
        s.append(f"| сделок закрыто | {len(zakr)} |")
        if r_est:
            s.append(f"| в плюс | {len(plyusy)} |")
            s.append(f"| в минус | {len(minusy)} |")
            s.append(f"| доля прибыльных | "
                     f"{len(plyusy) / len(r_est) * 100:.0f}% |")
            s.append(f"| итог в R | {sum(r_est):+.2f}R |")
            s.append(f"| в среднем на сделку | "
                     f"{sum(r_est) / len(r_est):+.2f}R |")
            if minusy:
                pf = sum(plyusy) / abs(sum(minusy))
                s.append(f"| на рубль потерь заработано | {pf:.2f} |")
            elif plyusy:
                s.append("| на рубль потерь заработано | потерь не было |")
            # худшая просадка: самый глубокий провал кривой счёта
            pik = 0.0
            schyot = 0.0
            prosadka = 0.0
            for v in r_est:
                schyot += v
                pik = max(pik, schyot)
                prosadka = min(prosadka, schyot - pik)
            s.append(f"| худшая просадка | {prosadka:.2f}R |")
        if len(r_est) != len(zakr):
            s.append(f"| без R (риск ушёл в ноль) | "
                     f"{len(zakr) - len(r_est)} |")
        s.append("")

        # чем именно закрывались
        prichiny: dict = {}
        for x in zakr:
            p = str(x.get("close_reason") or "?")
            prichiny[p] = prichiny.get(p, 0) + 1
        po_russki = {"STOP_LOSS": "выбил стоп",
                     "EXIT_BELL": "колокол на выход",
                     "MANUAL_CLOSE": "закрыл сам"}
        s.append("Чем закрывались: " + ", ".join(
            f"{po_russki.get(k, k)} — {v}"
            for k, v in sorted(prichiny.items(), key=lambda x: -x[1])))
        s.append("")

        # таблица
        s.append("| # | закрыта | пара | кто | вход | выход | чем | R |")
        s.append("|---|---|---|---|---|---|---|---|")
        for i, x in enumerate(zakr, 1):
            rv = x.get("pnl_r")
            rs = f"{float(rv):+.2f}" if isinstance(rv, (int, float)) else "—"
            s.append(f"| {i} | {x.get('closed_at', '—')} | "
                     f"{x.get('symbol', '—')} {x.get('timeframe', '')} | "
                     f"{x.get('trader', '—')} | {x.get('entry', '—')} | "
                     f"{x.get('exit', '—')} | "
                     f"{po_russki.get(str(x.get('close_reason')), '?')} | "
                     f"{rs} |")
        s.append("")
        s.append("R считается от риска НА ВХОДЕ — от первого стопа, а не "
                 "от подвинутого трейлингом. Иначе перенос стопа сам себе "
                 "рисовал бы результат.")
        s.append("")
        return s

'''


def podozhdat():
    """Чтобы окно не захлопнулось при запуске двойным кликом."""
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti():
    """Ищет отчёт сам. Руками путь прописывать не надо."""
    prosto = KOREN / "Биржа" / "otchyot.py"
    if prosto.exists():
        return prosto
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak", ".bylo")
    nashlos = [p for p in KOREN.rglob("otchyot.py")
               if not any(m in str(p) for m in musor)]
    if len(nashlos) == 1:
        print(f"Нашёл: {nashlos[0]}")
        return nashlos[0]
    if len(nashlos) > 1:
        print("Нашёл несколько:")
        for nomer, put in enumerate(nashlos, 1):
            print(f"  {nomer}. {put}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def main():
    put = nayti()
    if put is None:
        print("✗ не нашёл Биржа/otchyot.py — запускай из корня репозитория")
        return 1

    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("· уже сделано")
        return 0

    if NUZHEN not in tekst:
        print("✗ сперва накати rasklad_v_otchyote.py — этот идёт следом.")
        print("  Ничего не тронул.")
        return 1

    pravki = [(YAKOR_INIT, NOVYY_INIT),
              (YAKOR_NELZYA, NOVYY_NELZYA),
              (YAKOR_METODA, METOD + YAKOR_METODA)]

    for nomer, (staroe, _) in enumerate(pravki, 1):
        if tekst.count(staroe) != 1:
            print(f"✗ правка {nomer}: нашёл {tekst.count(staroe)} мест "
                  f"вместо одного. Ничего не тронул.")
            print("  Скажи Брату, поправим по месту.")
            return 1

    novyy = tekst
    for staroe, novoe in pravki:
        novyy = novyy.replace(staroe, novoe, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_itog")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ отчёт узнал, чем кончились сделки:")
    print("    · доля прибыльных, итог и среднее в R")
    print("    · на рубль потерь заработано, худшая просадка")
    print("    · чем закрывались — стоп, колокол, вручную")
    print("    · таблица закрытых сделок")
    print()
    print("Перезапусти Кабинет (main.py). Раздел «Чем кончилось»")
    print("появится в отчёт.md каждого нового прогона.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
