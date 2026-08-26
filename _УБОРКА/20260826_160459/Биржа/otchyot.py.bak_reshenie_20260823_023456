# -*- coding: utf-8 -*-
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

        # VOLNA_NA_STOLE_V1: даты. Шаги наблюдения подписывались датой
        # КАНДИДАТА — в прогоне 20.08 места 10, 11 и 12 вышли с одной
        # датой 2025.11.21 12:00, хотя это три разных бара (видно по
        # дневнику самой Нины: там стоит 2025.11.27 04:00).
        # Берём бар, на котором трейдера спросили НА САМОМ ДЕЛЕ; дату
        # места оставляем отдельно, она тоже нужна.
        _nastoyashchiy_bar = ""
        try:
            from hooks import load_trading_state as _lts
            _nastoyashchiy_bar = str(
                ((_lts() or {}).get("рынок") or {}).get("бар") or "")
        except Exception:
            pass
        self.mesta.append({
            "когда_на_рынке": _nastoyashchiy_bar or k.get("дата", ""),
            "место_найдено_на": k.get("дата", ""),
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
                "\n".join(json.dumps(m, ensure_ascii=False)
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
        return "\n".join(s)


# OTCHYOT_PROGONA_V1 - marker

# VOLNA_NA_STOLE_V1 - marker
