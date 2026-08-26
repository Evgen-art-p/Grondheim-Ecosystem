# -*- coding: utf-8 -*-
"""
postavit_otchyot_progona.py · MARKER: OTCHYOT_PROGONA_V1

ЗАЧЕМ
─────
Слова Шефа после первого прогона: «как-то нужно мне анализ высасывать
из всего, где что находится? где искать картинки? нет результатов
статистики».

Справедливо. Прогон говорил в чат — и растворялся. Ответы были, следа
не было: ни пересчитать, ни сравнить два прогона, ни найти кадр к
конкретному месту (все кадры валятся в общую папку `Биржа/кадры`
вперемешку с теми, что ты смотрел руками).

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Каждый прогон заводит свою папку:

    GRONDHEIM_CITY/Биржа/цеха/{цех}/прогоны/{дата_время}/
        отчёт.md        — таблица для глаз плюс итог
        места.jsonl     — то же машиной, строка на место
        кадры/          — картинка КАЖДОГО места, рядом со строкой

В таблице по каждому месту: когда, кто, инструмент, этаж, длина волны
в барах, компас, вердикт, причина ЕГО СЛОВАМИ и имя кадра.

В итоге — то, чего не хватало для анализа:

    · сколько мест прошли, сколько входов, сколько отказов;
    · СКОЛЬКО МЕСТ ПОПАЛО В ОКНО 100-140 — по первому прогону это
      было 6 из 30, то есть трейдеров звали смотреть на масштаб, где
      их структура не читается;
    · разброс длин волн: самая короткая, самая длинная, середина;
    · частые причины отказа, сгруппированные.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не трогает решения трейдеров и не подсказывает им. Отчёт только
записывает то, что было. Судить по нему — Шефу.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_otchyot_progona.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "OTCHYOT_PROGONA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists() and (p / "main.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


OTCHYOT_PY = '''# -*- coding: utf-8 -*-
# OTCHYOT_PROGONA_V1
"""
ОТЧЁТ ПРОГОНА — след, по которому можно судить.

ЗАЧЕМ
    Прогон говорил в чат и растворялся. Нельзя было ни пересчитать, ни
    сравнить два прогона, ни найти кадр к конкретному месту: все кадры
    валились в общую папку вперемешку.

ЗАКОН ЭТОГО ФАЙЛА
    Отчёт ЗАПИСЫВАЕТ, а не судит. Никаких «вход был хорош» и «стоило
    войти». Числа, слова трейдера и картинка — судит Шеф.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

OKNO = (100, 140)      # канон Шефа: столько баров держит волну читаемой


class Otchyot:
    """Одна папка на один прогон: отчёт.md, места.jsonl, кадры/."""

    def __init__(self, koren: Path, ceh: str):
        self.kogda = datetime.now()
        self.papka = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh
                      / "прогоны" / self.kogda.strftime("%Y%m%d_%H%M%S"))
        self.kadry = self.papka / "кадры"
        self.ceh = ceh
        self.mesta: list = []
        try:
            self.kadry.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ОТЧЁТ] папку не завести: {e}")

    # ── одно место ──
    def zapisat(self, k: dict, slot: str, imya: str, symbol: str,
                etazh: str, otvet: dict, kadr_put=None):
        signal = (otvet or {}).get("signal") or {}
        verdikt = ""
        prichina = ""
        for kl, zn in signal.items():
            if kl.endswith("_verdict") and zn:
                verdikt = str(zn)
            if kl.endswith("_reason") and zn:
                prichina = str(zn)
        skazal = ((otvet or {}).get("narrative") or "").strip()
        if not prichina:
            prichina = skazal[:200]

        imya_kadra = ""
        if kadr_put:
            try:
                p = Path(kadr_put)
                if p.exists():
                    imya_kadra = f"{len(self.mesta) + 1:02d}_{imya}_{p.name}"
                    shutil.copy2(p, self.kadry / imya_kadra)
            except Exception as e:
                print(f"[ОТЧЁТ] кадр не лёг: {e}")

        self.mesta.append({
            "когда_на_рынке": k.get("дата", ""),
            "кто": imya, "слот": slot,
            "инструмент": symbol, "этаж": etazh,
            "разворотный": k.get("разворотный"),
            "цена_разворотного": k.get("цена_разворотного"),
            "длина_волны": k.get("длина_волны"),
            "в_окне_100_140": bool(
                k.get("длина_волны")
                and OKNO[0] <= k["длина_волны"] <= OKNO[1]),
            "компас": k.get("компас"),
            "вердикт": verdikt or ("промолчал" if not skazal else "без вердикта"),
            "причина": prichina,
            "сказал": skazal,
            "кадр": imya_kadra,
        })

    # ── итог ──
    def zakryt(self) -> Path | None:
        if not self.mesta:
            return None
        try:
            (self.papka / "места.jsonl").write_text(
                "\\n".join(json.dumps(m, ensure_ascii=False)
                          for m in self.mesta), encoding="utf-8")
            (self.papka / "отчёт.md").write_text(self._svodka(),
                                                 encoding="utf-8")
        except Exception as e:
            print(f"[ОТЧЁТ] не записался: {e}")
            return None
        return self.papka

    def _svodka(self) -> str:
        n = len(self.mesta)
        dliny = [m["длина_волны"] for m in self.mesta if m["длина_волны"]]
        v_okne = sum(1 for m in self.mesta if m["в_окне_100_140"])
        vhody = [m for m in self.mesta
                 if str(m["вердикт"]).upper() in ("APPROVED", "ENTER", "OK")]
        otkazy = [m for m in self.mesta
                  if str(m["вердикт"]).upper() in ("REJECTED", "WAIT")]

        s = [f"# Прогон {self.kogda:%Y-%m-%d %H:%M} · цех {self.ceh}", ""]
        s.append(f"Мест пройдено: **{n}** · входов: **{len(vhody)}** · "
                 f"отказов: **{len(otkazy)}**")
        if dliny:
            dliny_s = sorted(dliny)
            s.append(f"Длина волны: от {dliny_s[0]} до {dliny_s[-1]} баров, "
                     f"середина {dliny_s[len(dliny_s) // 2]}")
            s.append(f"В окне 100-140: **{v_okne} из {n}** — на остальных "
                     f"масштаб не тот, и трейдер это видит.")
        s.append("")

        # кто сколько
        po_lyudyam: dict = {}
        for m in self.mesta:
            d = po_lyudyam.setdefault(m["кто"], {"всего": 0, "входы": 0})
            d["всего"] += 1
            if m in vhody:
                d["входы"] += 1
        s.append("| кто | мест | входов |")
        s.append("|---|---|---|")
        for kto, d in sorted(po_lyudyam.items()):
            s.append(f"| {kto} | {d['всего']} | {d['входы']} |")
        s.append("")

        # таблица мест
        s.append("## Места")
        s.append("")
        s.append("| # | когда | кто | пара | волна | окно | компас | "
                 "вердикт | кадр |")
        s.append("|---|---|---|---|---|---|---|---|---|")
        for i, m in enumerate(self.mesta, 1):
            s.append(f"| {i} | {m['когда_на_рынке']} | {m['кто']} | "
                     f"{m['инструмент']} {m['этаж']} | "
                     f"{m['длина_волны'] or '—'} | "
                     f"{'✓' if m['в_окне_100_140'] else '·'} | "
                     f"{m['компас'] or '—'} | {m['вердикт']} | "
                     f"{m['кадр'] or '—'} |")
        s.append("")

        # частые причины
        prichiny: dict = {}
        for m in self.mesta:
            p = (m["причина"] or "").strip()
            if p:
                prichiny[p[:90]] = prichiny.get(p[:90], 0) + 1
        if prichiny:
            s.append("## Что говорили чаще всего")
            s.append("")
            for p, skolko in sorted(prichiny.items(), key=lambda x: -x[1])[:10]:
                s.append(f"- **{skolko}×** {p}")
            s.append("")

        s.append("## Словами")
        s.append("")
        for i, m in enumerate(self.mesta, 1):
            if m["сказал"]:
                s.append(f"**{i}. {m['кто']} · {m['когда_на_рынке']} · "
                         f"{m['инструмент']} {m['этаж']}**")
                s.append("")
                s.append(m["сказал"])
                s.append("")
        return "\\n".join(s)


# OTCHYOT_PROGONA_V1 - marker
'''


# ── правки в прогоне ──
ST_START = '''        skolko = int(state.get("bars_to_live") or 1)
        state["tester_running"] = True'''
NOV_START = '''        skolko = int(state.get("bars_to_live") or 1)
        # OTCHYOT_PROGONA_V1: заводим папку прогона — туда лягут
        # таблица, строки машиной и кадр КАЖДОГО места.
        try:
            import otchyot as _ot
            _otchyot = _ot.Otchyot(Path(__file__).resolve().parent.parent,
                                   tseh_id)
        except Exception as _e:
            _otchyot = None
            print(f"[ОТЧЁТ] не завёлся ({_e}) — прогон пойдёт без записи")
        state["tester_running"] = True'''

ST_ZAPIS = '''                r = (itog.get("results") or {}).get(_sl) or {}
                skazal = (r.get("narrative") or "").strip()
                if not skazal and r.get("error"):
                    skazal = f"(промолчал: {r['error']})"'''
NOV_ZAPIS = '''                r = (itog.get("results") or {}).get(_sl) or {}
                skazal = (r.get("narrative") or "").strip()
                if not skazal and r.get("error"):
                    skazal = f"(промолчал: {r['error']})"
                # OTCHYOT_PROGONA_V1: кадр этого места — в папку прогона,
                # рядом со строкой. Раньше все кадры валились в общую
                # кучу, и найти картинку к месту было нельзя.
                if _otchyot is not None:
                    _kadr = None
                    try:
                        import grafik as _gr
                        _kadr = _gr.kadr(_sym, _tf)
                    except Exception:
                        pass
                    try:
                        _otchyot.zapisat(k, _sl, imya, _sym, _tf, r, _kadr)
                    except Exception as _e:
                        print(f"[ОТЧЁТ] место не записалось: {_e}")'''

ST_KONEC = '''        state["chat_history"].append({
            "role": "system",
            "content": f"✓ прогон окончен · пройдено мест: {proydeno}"})
        update_chat_display()
        ui.notify(f"✓ прогон окончен · {proydeno} мест", type="positive")'''
NOV_KONEC = '''        # OTCHYOT_PROGONA_V1: закрываем отчёт и говорим, где он лёг.
        _gde = None
        if _otchyot is not None:
            try:
                _gde = _otchyot.zakryt()
            except Exception as _e:
                print(f"[ОТЧЁТ] не закрылся: {_e}")
        _hvost = ""
        if _gde:
            try:
                _otn = _gde.relative_to(Path(__file__).resolve().parent.parent)
            except Exception:
                _otn = _gde
            _hvost = f" · отчёт: {_otn}"
            print(f"[ОТЧЁТ] 📄 {_gde}")
        state["chat_history"].append({
            "role": "system",
            "content": f"✓ прогон окончен · пройдено мест: {proydeno}{_hvost}"})
        update_chat_display()
        ui.notify(f"✓ прогон окончен · {proydeno} мест", type="positive")'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    otchyot = koren / "Биржа" / "otchyot.py"
    ui_torg = koren / "Биржа" / "ui_torg.py"

    print("\n1. Отчёт — Биржа/otchyot.py")
    if otchyot.exists() and MARKER in otchyot.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        try:
            ast.parse(OTCHYOT_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if not SUHO:
            otchyot.write_text(OTCHYOT_PY, encoding="utf-8")
        print("  ✓ положен")

    print("\n2. Прогон пишет отчёт")
    t = ui_torg.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        if "ODNA_KNOPKA_V1" not in t:
            print("  ✗ нет прогона — накати сперва ubrat_pult.py")
            return 1
        pary = [("начало", ST_START, NOV_START),
                ("запись места", ST_ZAPIS, NOV_ZAPIS),
                ("конец", ST_KONEC, NOV_KONEC)]
        beda = [imya for imya, st, _ in pary if t.count(st) != 1]
        if beda:
            print(f"  ✗ якоря не найдены: {', '.join(beda)}")
            return 1
        novyy = t
        for _, st, nov in pary:
            novyy = novyy.replace(st, nov, 1)
        if "\nfrom pathlib import Path" not in novyy and \
                "\nimport pathlib" not in novyy:
            novyy = novyy.replace("\nfrom nicegui import",
                                  "\nfrom pathlib import Path"
                                  "\nfrom nicegui import", 1)
        novyy += f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(ui_torg, ui_torg.with_suffix(
                f".py.bak_otchyot_{datetime.now():%Y%m%d_%H%M%S}"))
            ui_torg.write_text(novyy, encoding="utf-8")
            print("  ✓ пишет")

    if not SUHO:
        import py_compile
        for f in (otchyot, ui_torg):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nПосле прогона в чате будет путь, а на диске:")
        print("  GRONDHEIM_CITY/Биржа/цеха/{цех}/прогоны/{дата}/")
        print("      отчёт.md      таблица + итог + слова трейдеров")
        print("      места.jsonl   то же машиной")
        print("      кадры/        картинка каждого места")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
