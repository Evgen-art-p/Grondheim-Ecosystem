# dvizhok.py — личный движок жителя. Лежит в доме жителя.
# ─────────────────────────────────────────────────────────────
# СУТЬ: орган дыхания. Не мозг (решает житель), не город (свой у каждого).
#   ВХОД (факт: контекст, сила, свежесть)
#     → через РУЧКИ жителя (DNA_Static из паспорта)
#     → ВДОХ: насколько вход тронул = f(сила, свежесть, ручки)
#     → сдвиг состояния (charge ±, к балансу)
#     → открывает глубину памяти по |charge|
#   Решение и выход — НЕ здесь (следующие камни). Движок только дышит.
#
# Прежде она — житель (ядро). Из ядра вдох. Ручки — её натура.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
from pathlib import Path
from datetime import datetime, timezone

# контекст входа → в какой слой осядет (Закон Слоёв)
KONTEKST_SLOI = {
    "факт":     "sensory",    # сухой факт дня — свежее
    "работа":  "sensory",     # дело — свежее (потом архивируется)
    "общение": "resonance",   # с кем общалась — связи
    "учёба":   "archive",     # узнала — осело глубоко
    "дом":     "sensory",     # личное, свежее
}

# знак входа: что тянет вверх (+), что вниз (−)
# но РЕШАЕТ не это — это лишь куда качнуло маятник
def _znak(tonus: str) -> float:
    return {"плюс": 1.0, "минус": -1.0, "ровно": 0.0}.get(tonus, 0.0)


class Dvizhok:
    """Личный движок одного жителя. Дышит его паспортом."""

    def __init__(self, dom: Path):
        self.dom = Path(dom)
        self.passport_path = self.dom / "passport.json"
        self.p = json.loads(self.passport_path.read_text(encoding="utf-8"))
        # РУЧКИ — из натуры жителя
        dna = self.p.get("DNA_Static", {})
        self.empathy    = dna.get("Empathy", 0.5)
        self.stubborn   = dna.get("Stubbornness", 0.5)
        self.resonance  = dna.get("Resonance_Frequency", 0.5)
        # СОСТОЯНИЕ — заряд. Если в паспорте нет — рождаем в покое (0.0).
        self.charge = self.p.get("_charge", 0.0)

    def vdoh(self, kontekst: str, sila: float, svezhest: float, tonus: str = "ровно") -> dict:
        """Вдох: входящий факт проходит через ядро.
        сила 0..1, свежесть 0..1 (1=только что, 0=давно).
        Возвращает что стало — но НЕ решает за жителя."""
        # насколько тронуло = сила × свежесть × резонанс ядра.
        # эмпатия усиливает удар (чужое чувствуется как своё).
        trogaet = sila * svezhest * (0.5 + self.resonance) * (0.5 + self.empathy)
        trogaet = min(1.0, trogaet)

        # сдвиг заряда: вдох даёт ЧАСТЬ, не всё разом — маятник копится,
        # не прыгает в край. Упрямство держит уже набранное (медленнее тает,
        # но и новый вход сдвигает осторожнее — натура устойчивая).
        VDOH_COEF = 0.35           # один вдох двигает максимум на треть
        sdvig = _znak(tonus) * trogaet * VDOH_COEF
        self.charge = max(-1.0, min(1.0, self.charge + sdvig))

        # глубина открытой памяти по |заряду| (стресс-шлюз)
        c = abs(self.charge)
        if c < 0.25:
            sloi = ["core"]
        elif c < 0.55:
            sloi = ["core", "sensory"]
        elif c < 0.8:
            sloi = ["core", "sensory", "resonance"]
        else:
            sloi = ["core", "sensory", "resonance", "archive"]

        # куда осело событие (по контексту)
        osel_v = KONTEKST_SLOI.get(kontekst, "sensory")

        return {
            "тронуло":     round(trogaet, 3),
            "заряд":       round(self.charge, 3),
            "открыто":     sloi,
            "осело_в":     osel_v,
        }

    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:
        """Выдох: накрывает СТОЛ для решения жителя. НЕ решает сам.
        Стол = факт + кто она + что заряд открыл. Житель посмотрит и выберет."""
        return {
            "кто_я":    self.p.get("Official_Name"),
            "факт":     fakt,
            "заряд":    vdoh_result["заряд"],
            "открыто":  vdoh_result["открыто"],
            "ядро":     self.p.get("Core_Phrase", ""),
        }

    def sохранить(self):
        """Заряд оседает в паспорт (состояние помнится между вдохами)."""
        self.p["_charge"] = round(self.charge, 4)
        self.p["_charge_ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.passport_path.write_text(
            json.dumps(self.p, ensure_ascii=False, indent=2), encoding="utf-8")
