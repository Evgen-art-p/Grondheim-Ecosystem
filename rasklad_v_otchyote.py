# -*- coding: utf-8 -*-
# rasklad_v_otchyote.py — расклад по прогону в каждом отчёте.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python rasklad_v_otchyote.py
#
# ═══ ЗАЧЕМ ═══
#
# Шеф считал расклад по «места.jsonl» руками. Теперь он будет
# выходить сам, в отчёт каждого прогона, сразу под шапкой.
#
# ЧТО СЧИТАЕТ:
#   · активность — мест, входов, отказов, конверсия в процентах
#   · по каждой сделке — направление, риск в пунктах, это 1R
#   · перенос стопа — на сколько подвинут и какой это R гарантии
#   · сбои записи — места без слов и без вердикта
#   · места, где вердикт «отказ», а в собственных словах трейдера
#     стоит признак сошедшихся условий
#
# КАК ОПРЕДЕЛЯЕТСЯ НАПРАВЛЕНИЕ. Не из текста, а из стопа: стоп ниже
# входа — LONG, выше — SHORT. Слова могут соврать, стоп не может.
#
# ЧЕГО СЧИТАТЬ НЕЛЬЗЯ — и отчёт скажет это прямо. В «места.jsonl»
# НЕТ выходов: ни цены закрытия, ни причины, ни результата. Без них
# прибыль, winrate и просадка не считаются в принципе. Отчёт не
# станет делать вид, что считает: он назовёт, чего не хватает.
#
# ═══ ОДНА ОГОВОРКА, ВАЖНАЯ ═══
#
# В шапке otchyot.py стоит твой закон: «Отчёт ЗАПИСЫВАЕТ, а не судит.
# Никаких "вход был хорош" и "стоило войти" — судит Шеф».
#
# Строчка про сошедшиеся условия ходит у самой этой черты. Поэтому
# она сделана НЕ приговором: отчёт не пишет «надо было входить». Он
# пишет факт — вот место, вот вердикт «отказ», вот собственные слова
# трейдера с этим признаком. Вывод по-прежнему твой.
#
# Если и так близко к черте — скажи, уберу одной правкой.
#
# БЕЗОПАСНО. Собирает новый текст в памяти, проверяет ast.parse и
# только потом пишет. Рядом кладёт otchyot.py.bak_rasklad.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "RASKLAD_PROGONA_V1"

YAKOR_METODA = "    def _svodka(self) -> str:\n"
YAKOR_VSTAVKI = (
    "        # кто сколько\n"
    "        po_lyudyam: dict = {}\n"
)

METOD = '''    # ── RASKLAD_PROGONA_V1: расклад по прогону ──
    # Шеф считал это руками по места.jsonl. Теперь выходит само.
    # Закон файла соблюдён: отчёт кладёт ЧИСЛА и СЛОВА трейдера,
    # приговоров не выносит.

    _PRIZNAKI_SHODYATSYA = (
        "все три условия", "три условия сход", "условия сход",
        "условия сошлись", "всё сходится", "все сходится",
        "все совпад", "картина сложил",
    )

    @staticmethod
    def _punkt(cena: float) -> float:
        """Размер пункта по величине цены. Отчёт скажет, какой взял."""
        c = abs(float(cena))
        if c < 20:          # EURUSD, GBPUSD и прочие пятизнаки
            return 0.00001
        if c < 500:         # иеновые пары
            return 0.001
        return 0.01         # золото и индексы

    def _sdelki(self) -> list:
        """Собирает сделки: вход и всё, что к нему прицепилось."""
        sdelki = []
        otkrytye = {}
        for nomer, m in enumerate(self.mesta, 1):
            d = str(m.get("действие") or "").upper()
            v = str(m.get("вердикт") or "").upper()
            para = f"{m.get('инструмент')} {m.get('этаж')}"
            vh = m.get("цена_входа")
            st = m.get("стоп_входа")

            vhod = (d == "ENTER") or (v in ("APPROVED", "ENTER", "OK")
                                      and d not in ("MOVE_STOP", "HOLD",
                                                    "ADD", "CLOSE"))
            if vhod and vh and st:
                s = {"номер": nomer, "когда": m.get("когда_на_рынке", ""),
                     "пара": para, "вход": float(vh), "стоп": float(st),
                     "перенос": None, "перенос_когда": "",
                     "закрыт": False}
                sdelki.append(s)
                otkrytye[para] = s
                continue

            if d == "MOVE_STOP" and st and para in otkrytye:
                otkrytye[para]["перенос"] = float(st)
                otkrytye[para]["перенос_когда"] = m.get("когда_на_рынке", "")
            if d == "CLOSE" and para in otkrytye:
                otkrytye[para]["закрыт"] = True
                otkrytye.pop(para, None)
        return sdelki

    def _rasklad(self) -> list:
        n = len(self.mesta)
        if not n:
            return []

        vhody = [m for m in self.mesta
                 if str(m.get("действие") or "").upper() == "ENTER"
                 or str(m.get("вердикт") or "").upper() in ("APPROVED",
                                                            "ENTER", "OK")]
        otkazy = [m for m in self.mesta
                  if str(m.get("вердикт") or "").upper() in ("REJECTED",
                                                             "WAIT")]
        sboi = [i for i, m in enumerate(self.mesta, 1)
                if not (m.get("сказал") or "").strip()
                or str(m.get("вердикт") or "") in ("промолчал",
                                                   "ОТВЕТ НЕ РАЗОБРАН")]
        sdelki = self._sdelki()

        s = ["## Расклад", ""]
        s.append("| что | сколько |")
        s.append("|---|---|")
        s.append(f"| мест пройдено | {n} |")
        s.append(f"| входов | {len(sdelki)} |")
        s.append(f"| отказов (WAIT / REJECTED) | {len(otkazy)} |")
        s.append(f"| конверсия мест во входы | "
                 f"{len(sdelki) / n * 100:.1f}% |")
        s.append(f"| сделок закрыто | "
                 f"{sum(1 for x in sdelki if x['закрыт'])} |")
        if sboi:
            s.append(f"| мест без слов (сбой записи) | {len(sboi)} |")
        s.append("")

        if len(vhody) != len(sdelki):
            s.append(f"> Мест с вердиктом входа: {len(vhody)}, а сделок "
                     f"собралось {len(sdelki)} — у остальных нет цены "
                     f"или стопа.")
            s.append("")

        # ── риск по сделкам ──
        if sdelki:
            s.append("### Риск по сделкам")
            s.append("")
            for nomer, x in enumerate(sdelki, 1):
                p = self._punkt(x["вход"])
                dlinnaya = x["стоп"] < x["вход"]
                storona = "LONG" if dlinnaya else "SHORT"
                risk = abs(x["вход"] - x["стоп"])
                risk_p = risk / p
                s.append(f"**Сделка {nomer} — {storona}, {x['пара']}, "
                         f"{x['когда']}**")
                s.append("")
                s.append(f"- вход {x['вход']}, стоп {x['стоп']} → риск "
                         f"**{risk_p:.0f} п. = 1R**")
                if x["перенос"] is not None and risk:
                    ns = x["перенос"]
                    hod = (ns - x["вход"]) if dlinnaya else (x["вход"] - ns)
                    s.append(f"- {x['перенос_когда']} стоп перенесён на "
                             f"{ns} → **{hod / risk:+.2f}R** "
                             f"гарантии, если стоп сработает")
                if not x["закрыт"]:
                    s.append("- выхода в записях нет — чем кончилось, "
                             "неизвестно")
                s.append("")
            s.append(f"Пункт взят как {self._punkt(sdelki[0]['вход'])} — "
                     f"по величине цены. Направление — из положения стопа, "
                     f"не из слов.")
            s.append("")

        # ── чего посчитать нельзя ──
        s.append("### Чего посчитать нельзя")
        s.append("")
        s.append("В записях нет ни одного выхода: ни цены закрытия, ни "
                 "причины, ни результата. Поэтому прибыль, winrate, "
                 "ожидание в R и просадка не считаются — не из чего.")
        s.append("")
        s.append("Чтобы считались, в запись места должны попадать: цена "
                 "и время выхода, причина выхода (стоп / цель / вручную), "
                 "и общий номер сделки, чтобы вход и ведение связывались "
                 "не по цене, а прямо.")
        s.append("")

        # ── отказ при сошедшихся условиях ──
        spornye = []
        for i, m in enumerate(self.mesta, 1):
            if str(m.get("вердикт") or "").upper() not in ("REJECTED",
                                                           "WAIT"):
                continue
            slova = ((m.get("сказал") or "") + " "
                     + (m.get("причина") or "")).lower()
            if any(pr in slova for pr in self._PRIZNAKI_SHODYATSYA):
                spornye.append((i, m))
        if spornye:
            s.append("### Отказ при сошедшихся условиях")
            s.append("")
            s.append(f"Мест, где вердикт — отказ, а в собственных словах "
                     f"трейдера есть признак сошедшихся условий: "
                     f"**{len(spornye)}**.")
            s.append("")
            s.append("Отчёт не судит, входить было надо или нет. Он кладёт "
                     "рядом вердикт и слова — смотри сам.")
            s.append("")
            for i, m in spornye[:15]:
                slova = (m.get("сказал") or m.get("причина") or "").strip()
                s.append(f"- **{i}. {m.get('когда_на_рынке')}** · "
                         f"{m.get('вердикт')} — {slova[:160]}")
            if len(spornye) > 15:
                s.append(f"- … ещё {len(spornye) - 15} (все — в места.jsonl)")
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

    if tekst.count(YAKOR_METODA) != 1 or tekst.count(YAKOR_VSTAVKI) != 1:
        print("✗ не нашёл ожидаемое место — отчёт мог измениться.")
        print("  Ничего не тронул. Скажи Брату, поправим по месту.")
        return 1

    novyy = tekst.replace(YAKOR_METODA, METOD + YAKOR_METODA, 1)
    novyy = novyy.replace(
        YAKOR_VSTAVKI, "        s += self._rasklad()\n\n" + YAKOR_VSTAVKI, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        print(f"✗ после правки файл поломался (строка {beda.lineno}): {beda.msg}")
        print("  Ничего не записал, оригинал цел.")
        return 1

    kopiya = put.with_suffix(put.suffix + ".bak_rasklad")
    if not kopiya.exists():
        shutil.copy2(put, kopiya)
        print(f"  (копия старого: {kopiya.name})")
    put.write_text(novyy, encoding="utf-8")

    print("✓ расклад встал в отчёт:")
    print("    · активность, конверсия, сбои записи")
    print("    · риск в пунктах и R по каждой сделке")
    print("    · перенос стопа — сколько гарантии в R")
    print("    · отказы при сошедшихся условиях — фактом, без приговора")
    print("    · прямо сказано, чего посчитать нельзя и почему")
    print()
    print("Перезапусти Кабинет (main.py). Расклад появится в отчёт.md")
    print("каждого нового прогона, сразу под шапкой.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
